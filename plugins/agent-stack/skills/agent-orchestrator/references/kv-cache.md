# The prompt cache — an architectural constraint, not an optimisation

**Load this before deciding what goes where in a request**: the system prompt's shape,
whether the tool list may change mid-run, how often to compact, whether to swap a role or
load a skill, whether few-shot examples may be selected per request.

It reads as a cost topic and is not. The cache decides **context layout before semantics
does**, because every other decision in this skill is cheap or ruinous depending on where
in the request it lands. A team that treats it as tuning discovers it as an incident.

## Contents

- [The split, and the one directional rule](#the-split-and-the-one-directional-rule)
- [What a miss costs, measured](#what-a-miss-costs-measured)
- [Every condition before the boundary doubles the keys](#every-condition-before-the-boundary-doubles-the-keys)
- [The named invalidators](#the-named-invalidators)
- [Three regions, never mixed](#three-regions-never-mixed)
- [Compaction is a cache decision](#compaction-is-a-cache-decision)
- [Four things that look like optimisations and are not](#four-things-that-look-like-optimisations-and-are-not)
- [Where this constrains the rest of the skill](#where-this-constrains-the-rest-of-the-skill)

---

## The split, and the one directional rule

Every request is two parts:

```
agent context = static prefix + trajectory
                ^^^^^^^^^^^^^   ^^^^^^^^^^
                system prompt   user messages, assistant messages,
                tool definitions   tool results — append-only
                few-shot examples
```

Caching operates on the **byte sequence of tokens**. A request hits the cache for as long
as its bytes are an exact prefix of a previous one, and stops hitting at the first
differing token.

> **The earlier a change lands, the more cache it invalidates.**

That single line is the whole discipline. It is why the append-only shape of a trajectory
is not a stylistic preference: appending changes nothing before the append point, so the
entire prior context stays a valid prefix. Editing an earlier message discards everything
after it.

**The structural fix follows from the rule and is worth stating as a rule of its own:** a
configuration change is **appended as a new message**, never applied by editing an earlier
one. Codex deliberately keeps the old prompt an exact prefix of the new one for this
reason — the agent loop is quadratic in JSON and linear in sampling *only while cache hits
hold*.

## What a miss costs, measured

A customer-service agent at **100,000 conversations/day** was healthy until an engineer
added `Current time: {{now}}` to the system prompt. Nothing else changed:

| | before | after |
|---|---|---|
| TTFT | **0.5 s** | **3–5 s** |
| monthly inference bill | baseline | **nearly doubled** |

The line sat near the front of the prefix, so every request differed from that token
onward and the whole remainder was recomputed and re-billed, every time, for every user.

A second measurement from the other direction: on one real user in one day, a harness that
treats prefix stability as a loop invariant moved **435M input tokens**, at a hit price
roughly **1/120** of a miss. At that ratio the cache is not a saving — it is the only
reason the workload is affordable at all.

**The general shape:** anything that varies per request and sits early in the prefix is a
permanent, silent, whole-fleet cost. A timestamp is the classic; a user id, a session
counter, a randomly ordered list and a freshly retrieved example are the same defect
wearing different clothes.

## Every condition before the boundary doubles the keys

Providers let you mark where the cacheable region ends. Content before the boundary can be
cached **across users and sessions**; content after it is user- or session-specific.

The arithmetic is unforgiving: **N binary runtime conditions in front of the boundary
produce 2^N distinct cache populations**, each of which must be warmed independently.

| conditions before the boundary | cache populations |
|---|---|
| 1 (e.g. OS) | 2 |
| 2 (+ debug mode) | 4 |
| 3 (+ locale) | **8** |
| 5 | 32 |

Three innocuous conditions — macOS/Linux × normal/debug × zh/en — and one warm cache
becomes eight cold ones. **Push every runtime condition after the boundary**, or accept
that the prefix is no longer shared.

## The named invalidators

Each of these changes the prefix and costs everything after it:

- **Changing the `tools` array mid-conversation** — adding, removing *or reordering* a
  definition. Tool definitions are hundreds of tokens each and sit in the prefix.
- **Changing the model.**
- **Changing sandbox configuration, approval mode, or working directory**, where those are
  rendered into the prompt.
- **Changing the thinking / reasoning budget.**
- **Hot-loading a plugin at runtime** — it changes the tools and prompt fragments the model
  sees, so a plugin's documentation owes the reader its impact on the KV cache, not only on
  behaviour.
- **Replacing the system prompt to switch a role** (`transfer_to_agent`-style). This is a
  real architectural trade, not a mistake: replacing the prompt makes an out-of-scope tool
  *absent* — a hard boundary — where loading a **skill** keeps the static prefix intact and
  gives the model an *instruction* it may ignore. Boundary versus instruction, paid for in
  cache. Decide it deliberately.

## Three regions, never mixed

The cleanest shape observed in a production harness partitions every request and never
lets the parts blend:

| Region | Holds | Lifetime |
|---|---|---|
| **Immutable prefix** | system prompt, tool specs, few-shot examples | computed once per session, pinned |
| **Append-only log** | `[assistant][tool][assistant]…` | every prior turn stays a prefix of the next |
| **Volatile scratch** | reasoning traces, transient state | reset each turn, **never sent upstream** |

The value is that the invariant becomes checkable: if anything ever writes into region one
after the session starts, that is a bug with a name, not a mystery in the bill.

## Compaction is a cache decision

Compression happens **between** API calls, not inside one, and it never touches the static
prefix — its target is tool results in the history. But every such edit invalidates the
cache **from the replacement point onward**.

So compression frequency is itself a cost decision: **compact in batch when the context
approaches the threshold, never every round.** A per-round compactor pays a full re-prefill
every round to save tokens it was already paying for once.

`references/context-engineering.md`'s ladder carries this now: four of its five rungs are
free in *compute* and none is free in *cache*, because each one edits history.

**A marker makes the operation idempotent** — a `[COMPRESSED]` tombstone tells the next
pass what it may skip, so a second compaction does not rewrite the same region and pay the
invalidation twice.

## Four things that look like optimisations and are not

- **Sorting tool definitions by usage frequency.** Invalidates from the first moved
  position onward — and the measurement is the useful half: **a fixed order has almost no
  effect on tool-selection accuracy.** The trade is not accuracy against cost. It is cost
  for nothing.
- **Retrieving "the most relevant few-shot example" per request.** Examples land early in
  the prefix, so once chosen they must be **byte-for-byte identical** across requests.
  Per-request selection is a RAG-flavoured instinct that guarantees a permanent miss.
- **Deferred tool loading, misread.** `defer_loading` controls *what enters the context
  window, not what you send* — every definition still ships in the `tools` array on every
  request. What it buys is real and specific: deferred tools are excluded from the
  **system-prompt prefix** and discovered ones are appended inline as `tool_reference`
  blocks, so the cached prefix is untouched. That makes it the platform's cache-safe path,
  which the three hand-rolled mitigations in `agent-interop/references/mcp-scale.md` were
  approximating. At least one tool must stay non-deferred — all-deferred is a 400.
- **"Manual message concatenation breaks the cache."** It does not. Caching is over bytes,
  so a hand-built `"USER: … ASSISTANT: …"` prefix that is byte-stable hits exactly like a
  templated one; it breaks only if the concatenation is unstable. The real cost of
  flattening is different and worse — an **out-of-distribution format**, since the model
  was trained on role-delimited dialogue. Fix the reason, not the myth.

**The pinning mechanism, because it is what makes discovery viable at all:** on the turn a
tool is discovered its schema is appended at the end of the context, and **from then on it
stays fixed at that position and becomes ordinary history**. It is never moved to the new
end again — doing so would force a re-prefill every turn and make the whole scheme
pointless.

## Where this constrains the rest of the skill

- **§3 (meta-tools) and §10 (dynamic system prompts)** tell you to assemble tools and
  prompt per request from the same capability flags, so the two can never disagree. That is
  right for correctness and silent about cost. The reconciliation: rebuilding is free while
  it is **byte-identical** — which it is whenever the capability set has not moved — and the
  moment capabilities genuinely change mid-session, append the change as a new message
  rather than rewriting the prefix, and take the one miss knowingly.
- **§2's loop** may not swap the model between iterations of one conversation without
  counting the miss.
- **`references/context-engineering.md`** owns the ladder; this file owns why its rungs are
  not free.
- **`agent-interop/references/mcp-scale.md`** owns the tools-array case in an MCP client.
  This file owns the general rule it is an instance of.
