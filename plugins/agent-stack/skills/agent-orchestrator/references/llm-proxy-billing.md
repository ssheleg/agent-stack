# Reselling LLM access — metering, wallets and guardrails

**Load this when** the product resells LLM access: tiered wallets and the single
boundary where markup applies, the saga across a database and a provider API
with compensating transactions, advisory locking, optimistic concurrency for reclaims,
spend-delta polling and its three cases, budget / loop / auto-pause guardrails,
per-tenant key lifecycle and healing, the refund waterfall, and model-routing
precedence.

When your product gives users LLM access and bills for it, you are running a
proxy with a wallet behind it. The failure modes are not model failures: they
are **double-credited transfers**, **spend you discovered after it happened**,
and **a runaway loop that emptied a balance overnight**. This reference is the
provider-neutral shape of that problem, drawn from a production system built on
OpenRouter's Management API — the API calls are named where they are concrete,
the patterns hold for any upstream that issues per-tenant keys with limits.

## Contents

- [The tiered wallet](#the-tiered-wallet)
- [The saga across a DB and an external API](#the-saga-across-a-db-and-an-external-api)
- [Reconciling an unknown](#reconciling-an-unknown)
- [Serializing concurrent transfers](#serializing-concurrent-transfers)
- [Optimistic concurrency for reclaims](#optimistic-concurrency-for-reclaims)
- [Discovering spend you do not control](#discovering-spend-you-do-not-control)
- [Guardrails: budgets, loops, auto-pause](#guardrails-budgets-loops-auto-pause)
- [Key lifecycle and healing](#key-lifecycle-and-healing)
- [Refund the iteration, charge the money](#refund-the-iteration-charge-the-money)
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

## The saga across a DB and an external API

You have a database you can roll back and an HTTP API you cannot. That pair is
a **saga** — local transactions stitched together by compensations — and it is
not two-phase commit: 2PC needs a coordinator both participants obey, and the
provider's API never agreed to prepare/commit. Naming it 2PC is how the next
defect ships, because 2PC has no *unknown* outcome, and an HTTP call to a
system you do not control has one all the time.

Every operation that touches the provider carries an **`operation_id`**, minted
inside the DB transaction, and a state that moves
`pending → applied | unknown | compensated`:

1. Acquire the lock (below).
2. Read fresh balances **inside** the transaction — not before it.
3. Compute the transfer and apply the markup once.
4. Zero the source tier, increment the destination, write the intent row —
   `operation_id`, state `pending` — an outbox entry, not a log line.
5. Commit.
6. Call the provider to raise the key limit, idempotently where the API allows
   (send the `operation_id` as the idempotency key).
7. **On an outcome that proves the call did not apply** — a 4xx validation
   refusal, a "no such key" — a compensating transaction restores every DB
   value, writes a `compensation` audit row, and marks the operation
   `compensated`.
8. **On an AMBIGUOUS outcome — a timeout, a connection reset after send, a
   5xx — the operation is marked `unknown` and is NOT compensated.** The
   provider may have applied the change: compensating on a guess restores a
   ledger the key no longer matches, and the money drifts in the direction you
   cannot see. `unknown` resolves only by **reconciliation** — read the
   provider's actual state (the key's real limit), then mark `applied` or
   compensate on evidence. Until it resolves, the operation blocks retries of
   itself: a retry of an `unknown` is how one top-up applies twice.

The alternative — API first, DB second — leaves money on the key that your
ledger does not know about, and no amount of retrying finds it again. The
compensating transaction makes the *known* failure recoverable; the `unknown`
state is what keeps the ambiguous one honest.

Log the intent, the outcome and the compensation, keyed by `operation_id`. An
audit trail that records only successes cannot answer "where did the $35 go"
six weeks later — and one that cannot say "we do not know yet" answers it
wrongly.

## Reconciling an unknown

Three rules, and every one exists because a late HTTP response is a message
from the past:

- **Ask by the operation's own idempotency key.** Reconciliation queries the
  provider for what happened to THIS `operation_id` — never "read the limit
  and guess whose change it reflects". Ambient state is the sum of every
  operation that ever landed; only the key isolates yours.
- **The tenant's ledger carries a revision, and every resolve is a CAS.** A
  reconcile or compensation writes only if the revision it read is still
  current; a late or concurrent response that lost the race aborts and
  re-reads, it never blind-writes. Without this, the response to operation A —
  arriving after operation B moved the same tenant's ledger — "restores"
  values B already superseded, and the compensation itself becomes the
  corruption.
- **Compensate only your own confirmed operation.** A compensation names its
  `operation_id`, reverses exactly that operation's delta, and runs only after
  reconciliation confirmed THAT operation did not apply. A response for A is
  never grounds to touch B's rows — however tempting the arithmetic looks.

**Repeated reconciliation is idempotent.** `unknown → applied` and
`unknown → compensated` are one-way edges: resolving an already-resolved
operation reads its state and stops — zero new writes, zero new audit rows. A
reconciler that runs twice (and it will: cron plus a manual "Sync now" is the
normal case, not the weird one) must find nothing left to do the second time.

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

**Zero is a value, not an absence.** The baseline row carries three fields
BESIDE the sum — `baseline_initialized`, `observed_at`, and
`provider_key_generation` (the key's id or created-at, whatever the provider
lets you read) — because `lastRecordedUsage == 0` has two meanings that cost
money to conflate: "never watched" and "watched from zero". Testing the sum
for zero eats the first REAL spend of every key you watched from birth,
silently, as "seeding".

Four cases, decided by the flags, never by the sum:

- `!baseline_initialized` → **seed the baseline, record nothing**, set
  `baseline_initialized`, stamp `observed_at` and the generation. Recording
  here charges the tenant for everything spent before you started watching.
- initialized, `currentUsage > lastRecordedUsage` → record `delta` — including
  the very first delta of a key whose baseline is a genuine 0 — then
  immediately enforce budgets (below).
- initialized, `currentUsage < lastRecordedUsage`, **generation changed** →
  the key really was recreated: resync the baseline to the new generation,
  record nothing. The new key's next increase is recorded normally.
- initialized, `currentUsage < lastRecordedUsage`, **same generation** →
  **ANOMALY.** Do not resync, do not record, do not guess "recreated" — a
  counter that went backwards on the same key is the provider disagreeing
  with your ledger, and reconciliation (above) owns it. A guessed resync here
  quietly forgives the difference forever.

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

## Refund the iteration, charge the money

These are two axes and it is easy to ship one rule for both.

`agent-orchestrator`'s loop **refunds the iteration** on a recoverable provider error: a
502 should not consume one of the ten attempts the agent has to finish its work. That is
right, and it says nothing about money.

**The provider still billed the call.** A response that arrived and then failed to parse
was generated, metered and charged upstream; so was the one that arrived truncated, and the
one whose tool call was malformed. The tempting symmetry — *the attempt did not count, so
it did not cost* — is how a spend guard under-counts on exactly the runs that go worst.

The failure mode is specific and worth naming, because it hides where nobody looks:

> A harness charged `self.cost` on the **success path** of its `query()`. When parsing the
> response raised a format error, `query()` never returned, so the cost was never added —
> and the code compensated for it explicitly inside the exception handler. Where a cost
> ceiling is the *primary* bound — that harness ships `cost_limit = 3.0` with the step
> limit **off** — a leak in that accounting is a leak in the only guard there is.

The rule, in one line each:

- **Iteration:** refunded on a recoverable provider error, never on a misconfiguration.
- **Money:** charged whenever the provider generated tokens, including on every path that
  raises after the response arrived.
- **Therefore:** accounting belongs in a `finally`, or in the exception handler as well as
  the success path. If the only place your cost is added is the line after a successful
  parse, the guard is quietly optimistic.

A budget that under-counts is worse than one that over-counts: over-counting stops a run
early and is visible immediately; under-counting is invisible until the invoice, and it
biases toward the failing runs, which are the expensive ones.


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
toUpstreamModel(provider, model)   // "<public-name>" → "<provider>/<upstream-id>"
getDefaultModel(provider)          // when the caller names none
getFallbackModels(provider)        // ordered, tried on 5xx / overload
```

Three levels of model selection, in precedence order: the caller's explicit
choice → the tenant's configured default → the application default. Resolve them
in that order in one place, and log which level won — "why did it use that
model" is otherwise unanswerable.

See `patterns.md` for the retry, health-check and error-hierarchy patterns these
routing calls sit inside.

### What a trajectory cannot carry across a vendor

The routing above assumes the **request** is portable. Mid-run failover is a different
problem, because by then there is an accumulated history and not all of it can move.

- **Tool calls and results are portable.** They differ in structure between vendors and
  mean the same thing, so re-rendering them is enough.
- **Reasoning is not.** It is portable *text* plus a **non-portable credential** the vendor
  attaches to prove the reasoning is its own. Vendors disagree on what they demand: one end
  validates nothing, the other rejects any credential it did not issue.
- **The credential is not always attached to the reasoning.** It may sit on the *tool call*
  — which is why the apparently safe policy *"just strip all reasoning before failing
  over"* is exactly what fails at some vendors, and fails as a 400 rather than as
  degradation.

Design rules that follow:

- Store trajectories in a **neutral internal format**: keep the text, discard the
  credential, re-render per vendor at send time.
- Decide the failover boundary deliberately. **Between turns** is cheap and safe; **inside
  a turn**, after reasoning has been emitted, is where the credential problem lives.
- A fallback chain that has never been exercised **mid-trajectory** has not been tested.
  A green health probe answers a question about the endpoint, not about your history.

### Where the capability goes — not evenly

The intuitive allocation is to spend evenly across agents, or to give the strongest model
to whichever agent does the most work. Both are wrong for a planner–executor pair.

*Plan-and-Act* (arXiv:2503.09572) found the **planner is the bottleneck of the whole
system**: with good enough planning a relatively simple executor suffices, and with a wrong
decomposition every downstream executor is building on a false premise. Their 54% on
WebArena-Lite came from improving the **planner's** planning, not the executor's execution.

So: **give the strongest model and the most carefully written prompt to the manager**, and
let the executors be cheaper. It also sets where to look when a multi-agent system
underperforms — a weak plan is invisible in every executor's transcript, because each one
did its own step correctly.

### Budget awareness — steps the agent cannot see buy nothing

Raising a step budget does not by itself buy more work. Google's *Budget-Aware Tool-Use
Enables Effective Agent Scaling* reports that standard agents have **no budget awareness**,
so at **300 steps** they still conduct shallow searches and plateau at roughly what they
achieve at **30**.

Spending a larger budget requires telling the model where it is in that budget, so it can
shift strategy — broad exploration early, narrowing later. The multi-agent form is the
manager allocating step budget per sub-task rather than handing every executor the same cap.

A max-iteration guard that only composes a partial answer at exhaustion is the *floor* of
this, not the mechanism: it stops the spend, and it never changes the behaviour that led
there.
