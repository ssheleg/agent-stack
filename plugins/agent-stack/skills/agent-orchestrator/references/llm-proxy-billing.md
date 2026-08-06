# Reselling LLM access — metering, wallets and guardrails

When your product gives users LLM access and bills for it, you are running a
proxy with a wallet behind it. The failure modes are not model failures: they
are **double-credited transfers**, **spend you discovered after it happened**,
and **a runaway loop that emptied a balance overnight**. This reference is the
provider-neutral shape of that problem, drawn from a production system built on
OpenRouter's Management API — the API calls are named where they are concrete,
the patterns hold for any upstream that issues per-tenant keys with limits.

## Contents

- [The tiered wallet](#the-tiered-wallet)
- [Two-phase commit across a DB and an external API](#two-phase-commit-across-a-db-and-an-external-api)
- [Serializing concurrent transfers](#serializing-concurrent-transfers)
- [Optimistic concurrency for reclaims](#optimistic-concurrency-for-reclaims)
- [Discovering spend you do not control](#discovering-spend-you-do-not-control)
- [Guardrails: budgets, loops, auto-pause](#guardrails-budgets-loops-auto-pause)
- [Key lifecycle and healing](#key-lifecycle-and-healing)
- [The refund waterfall](#the-refund-waterfall)
- [Model routing and fallbacks](#model-routing-and-fallbacks)

---

## The tiered wallet

Money does not move in one hop. Model it as tiers, and be explicit about **which
boundary applies the markup** — this is the single most common source of
accounting drift.

| Tier | Holds | Denominated in |
|---|---|---|
| Account wallet | what the user paid you | user-facing USD |
| Tenant reserve | allocated to one bot / workspace / project | user-facing USD, 1:1 with the account |
| Upstream key limit | what the provider will actually let them spend | provider USD, after markup |

```
markup = 0.30                          // your cut, from config, never hardcoded

toKeyAmount(userUsd)  = userUsd * (1 - markup)   // $50 user → $35 on the key
toUserAmount(keyUsd)  = keyUsd  / (1 - markup)   // $35 key  → $50 shown back
```

**Apply markup at exactly one boundary** — reserve → key — and keep account ↔
reserve at 1:1. Two boundaries applying a cut is how a balance silently shrinks
every time a user moves money around without spending anything.

Keep the same two functions on the client. A UI that recomputes the conversion
with its own copy of the constant will disagree with the server the first time
the constant changes.

**Thresholds worth naming rather than inlining:**

| Constant | Typical | Purpose |
|---|---|---|
| `LOW_BALANCE_THRESHOLD` | $10 | trigger reserve → key transfer + notify |
| `CRITICAL_BALANCE_THRESHOLD` | $1 | permit auto-topup from the account wallet |
| `AUTO_TOPUP_AMOUNT` | $15 | ceiling pulled per auto-topup |

---

## Two-phase commit across a DB and an external API

You have a database you can roll back and an HTTP API you cannot. Order matters,
and so does what you do when step 2 fails.

**DB first, API second, compensate on failure:**

1. Acquire the lock (below).
2. Read fresh balances **inside** the transaction — not before it.
3. Compute the transfer and apply the markup once.
4. Zero the source tier, increment the destination, write an audit row.
5. Commit.
6. Call the provider to raise the key limit.
7. **On API failure: a compensating transaction restores every DB value and
   writes a `compensation` audit row.**

The alternative — API first, DB second — leaves money on the key that your
ledger does not know about, and no amount of retrying finds it again. The
compensating transaction is not optional politeness; it is the only thing that
makes step 6 recoverable.

Log both the intent and the compensation. An audit trail that records only
successes cannot answer "where did the $35 go" six weeks later.

---

## Serializing concurrent transfers

Two requests topping up the same tenant at the same time will both read the same
starting balance and both write their own total. Take a lock keyed on the tenant,
in the same transaction:

```sql
SELECT pg_advisory_xact_lock(hashtext(tenant_id || '_key'));
```

Transaction-scoped (`_xact_`) so it releases on commit **or** rollback — a
session-scoped lock survives a failed transaction and deadlocks the retry.

Every operation that moves this tenant's money takes the same lock: top-up,
reclaim, pull-back, refund. A single unlocked path makes the other five
pointless.

---

## Optimistic concurrency for reclaims

Locking protects concurrent writers in your database. It does not protect you
from a change the **provider** made while your transaction was open — a spend
that landed, a limit an operator edited in their dashboard.

For any operation that reads a provider value, acts, and writes back: snapshot
the value before the external call and re-read it after. If it moved, abort
rather than reconcile.

```
before = db.keyLimit
info   = await provider.getKey(hash)
if (info.limit !== before) throw new ConcurrentModification()   // do not guess
```

Aborting costs a retry. Guessing double-credits.

---

## Discovering spend you do not control

The provider deducts from the key as calls happen. Nothing notifies you. You
discover spend by **polling a cumulative counter and taking the delta**:

```
delta = currentUsage - lastRecordedUsage
```

Three cases, and only the first is obvious:

- `lastRecordedUsage == 0 && currentUsage > 0` → **seed the baseline, record
  nothing.** Recording it charges the tenant for everything spent before you
  started watching.
- `currentUsage > lastRecordedUsage` → record `delta`, then immediately enforce
  budgets (below).
- `currentUsage < lastRecordedUsage` → the key was recreated. **Resync the
  baseline, record nothing.** A negative delta treated as spend credits money
  that was never returned.

Sync your stored limit from the provider's authoritative value on the same pass —
under the lock, with a re-read, so the sync does not clobber a transfer that
landed mid-poll.

---

## Guardrails: budgets, loops, auto-pause

Three independent mechanisms, one shared action. Keep them separate in
configuration and unified in effect.

**Budget limits** — per-tenant daily and monthly caps with their own counters and
reset timestamps. `recordSpend()` increments and calls `enforceBudgetLimit()`
in the same breath; enforcement that runs on a schedule rather than on the write
is enforcement that arrives after the money is gone.

**Loop detection** — spend *velocity* over a rolling window against a
configurable multiplier of the tenant's normal rate. This is what catches an
agent that started calling itself; a daily cap will also catch it, tomorrow.

**Auto-pause** — an absolute per-tenant threshold, plus a user-level aggregate
across all their tenants. The aggregate exists because ten tenants each just
under their limit is a bill nobody approved.

All three converge on one function:

```
pauseBot(tenantId, cause, reason)
  1. set the pause timestamp for THAT cause (budgetPausedAt / loopPausedAt / …)
  2. disable the upstream key
  3. write an audit row naming the cause
  4. notify the user
```

Separate timestamps per cause, because resuming must know what paused it: a
daily budget reset should not un-pause a tenant that a loop detector stopped.
Reset jobs zero their own counters, clear **their own** timestamp, and re-enable
only if no other pause is still set.

---

## Key lifecycle and healing

Per-tenant keys go missing — deleted in a dashboard, orphaned by a failed
provision, expired. Treat the key as cache, not truth.

**Before every deploy**, validate and heal:

1. Check the key against the provider's own auth endpoint (the raw key, not the
   management hash).
2. Dead → create a fresh one with the same limit, update your stored key, hash
   and limit.
3. If the tenant was running, trigger a redeploy so the new key takes effect.

The polling job does the same when the Management API returns 404 for a hash it
holds.

**Management keys are not inference keys.** They do key CRUD and nothing else;
a management key sent to a completions endpoint fails in a way that reads like
an auth bug for an hour.

**The full key is returned exactly once, at creation.** Store it then or issue a
new one. Every provider does this and every integration learns it the same way.

Name keys after the tenant (`tenant:{id}:{name}`) — the provider dashboard is
where you will be debugging at 2am, and `sk-or-v1-…` tells you nothing.

Wire the lifecycle explicitly, one row per event: enabled → create + fund;
disabled → disable; subscription cancelled → disable + reclaim; deleted →
delete + reclaim; balance depleted → disable + notify; budget reset → re-enable.
A table like that in your own docs is what stops the eleventh event from being
handled three different ways.

---

## The refund waterfall

A payment refund has to come out of somewhere, and the money has usually moved.
Pull in a fixed priority, most-liquid first:

1. tenant reserve — purchased pool
2. tenant reserve — subscription pool
3. remaining balance on the upstream key (markup-adjusted, via the provider API)
4. account wallet

Any unrecoverable remainder is **logged for manual review**, not silently
forgiven and not left to make a balance negative. A tenant who spent the money
already is a business decision, not an arithmetic one.

---

## Model routing and fallbacks

Map your public model names to provider ids in **one** function, and give every
provider a default and a fallback:

```
toUpstreamModel(provider, model)   // "gpt-4o" → "openai/gpt-4o"
getDefaultModel(provider)          // when the caller names none
getFallbackModels(provider)        // ordered, tried on 5xx / overload
```

Three levels of model selection, in precedence order: the caller's explicit
choice → the tenant's configured default → the application default. Resolve them
in that order in one place, and log which level won — "why did it use that
model" is otherwise unanswerable.

See `patterns.md` for the retry, health-check and error-hierarchy patterns these
routing calls sit inside.
