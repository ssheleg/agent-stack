# Context engineering — what survives the window, and how

**Load this when** the loop is running out of window: choosing a compaction strategy,
deciding what crosses the boundary, bounding a tool result that will not fit, or
splitting message history without breaking the next request.

`SKILL.md` §2 gives the loop and its two thresholds — trim at ~80% of the window,
inject the wrap-up at ~70%. This file is what happens *at* those thresholds. The
difference matters: §2 decides **when** to act, this decides **what to give up**.

Ladder structure and the attachment taxonomy are adapted from
[HKUDS/OpenHarness](https://github.com/HKUDS/OpenHarness) (MIT),
`src/openharness/services/compact/__init__.py` and `services/tool_outputs.py`. The
constants below are ours; theirs are tuned for a different window and a different tool
mix, and a threshold copied without its context is a number nobody can defend.

## Contents

- The ladder — five rungs, cheapest first
- Re-measure between rungs
- The tool-pair invariant
- Carryover attachments — what crosses the boundary
- Tool-output offload
- Estimating what you have left
- The circuit breaker
- Sub-agent context isolation
- The filesystem as context
- Choosing your own constants

## The ladder — five rungs, cheapest first

Compaction is not one call. It is an ordered set of strategies, and the expensive one
is last. A loop that summarizes at the first sign of pressure pays a model call and a
round-trip for what a string operation would have solved.

| Rung | What it does | Cost | Cache | Loses |
|---|---|---|---|---|
| 1. Microcompact | Replace old tool results with a tombstone: `[tool result cleared]`. Keep the N most recent. | free | invalidates from the oldest replacement | old observations, kept recent ones |
| 2. Head/tail collapse | For an oversized text block, keep a head and a tail, elide the middle with a marker | free | invalidates from that block | the middle of long outputs |
| 3. Session condensation | Collapse each older message to a one-line summary, capped in total | free | invalidates from the first collapsed message | phrasing, keeps the thread of events |
| 4. LLM compaction | One model call summarizes the transcript into a structured brief | a call + latency | invalidates the whole trajectory | anything the summarizer does not think to keep |
| 5. Prompt-round truncation | Drop the oldest whole prompt rounds, boundary-aligned | free | invalidates from the first dropped round | the earliest history entirely |

Rung 5 exists for one case: **the compaction request itself does not fit.** When rung 4
fails because the transcript it must summarize is over the limit, summarizing harder is
not available — you drop oldest rounds and retry, bounded by a small retry count.

**Eligibility, not just age.** A tool result becomes a rung-1 candidate by size as well
as position: anything past a few thousand characters, and every result from an external
tool server, whose outputs are the usual window hog and the least likely to be re-read.

**"Free" is a compute column, and none of these rungs is free in cache.** Every one edits
history, and an edit invalidates the prefix from the replacement point onward — so the
frequency of compaction is itself a cost decision: **compact in batch at a threshold, never
every round.** A per-round compactor pays a full re-prefill each round to save tokens it had
already paid for once. `references/kv-cache.md` carries the economics and the arithmetic.

## Re-measure between rungs

After every rung, measure again and stop if you are under the threshold. Two failure
modes hide here:

- **Running the whole ladder every time** turns a 200-character overage into a model
  call. Rung 1 usually settles it.
- **Trusting a rung that did nothing.** Head/tail collapse on a transcript with no
  oversized blocks changes nothing. If the estimate did not drop, reject the result and
  escalate rather than recording a compaction that never happened.

## The tool-pair invariant

**A tool call and its result are one unit. Never split them.**

Every provider rejects a request where an assistant message announces a tool call whose
result is missing, or a tool result with no matching call. It is not a soft error — the
next request fails, mid-task, with a 400 that names nothing useful.

This makes every boundary computation in this file conditional: a truncation point, a
collapse range, a dropped round must all land **between** pairs. Write the boundary
finder once, use it from every rung, and give it a test that plants an orphan and
requires rejection.

The same invariant governs parallel dispatch: if one tool in a batch raises, its result
block must still be emitted — as an error result. A sibling's crash is not a reason to
send a malformed request.

## Carryover attachments — what crosses the boundary

A summarizer keeps prose and drops state. Ask one to compress a transcript and it will
faithfully preserve the discussion while losing the fact that you are in a read-only
mode, the path of the file you verified, and what the user actually asked for.

So state does not go through the summarizer. It is accumulated during normal execution
and re-attached after compaction as **typed blocks**:

| Block | Carries | Why it is lost otherwise |
|---|---|---|
| `task_focus` | the goal, recent sub-goals, active artifacts, verified state, next step | the summarizer rewrites the goal into its own words and drifts |
| `recent_files` | paths read or written, most recent first | the agent re-reads what it already has |
| `verified_work` | what was checked and how it was checked | re-verification, or worse, a claim of verification that was never re-run |
| `plan` | the active plan and any mode that restricts what may be done | **a safety mode forgotten across a boundary is how a read-only run starts writing** |
| `invoked_skills` | which doctrine is already loaded | re-loading a large file that is already in effect |
| `work_log` | one line per significant action | the agent repeats a step it already completed |

Accumulate them in bounded buckets during the loop — a small cap per bucket, oldest
evicted — so the attachment cost is known in advance and does not itself grow into a
context problem. Cap the number of attached blocks too.

The property that matters: this is **deterministic**. Structured state survives because
it is copied, not because a model chose to keep it.

## Tool-output offload

One large tool result poisons a window before any history trimming is relevant. Trimming
the conversation does not help when the problem is a single 200 KB response sitting in
the current turn.

The rule: **above an inline limit, write the full output to a file and put a preview
plus the path into the context.** The model reads the preview, and when it needs the
rest it reads the file with the tools it already has.

- **Inline limit** — the size above which offload happens.
- **Preview size** — enough to decide whether the rest is needed; head, or head and tail
  when the tail carries the verdict (test runs, build logs).
- **Path** — stable and unique per call, so two calls to the same tool do not collide.
- **Location** — a scratch directory scoped to the run, not the project tree; artifacts
  of a loop are not deliverables and must never arrive in a diff.

Both limits belong in configuration. The right value depends on the window and the tool
mix, and the only way to find it is to measure a real run.

## Estimating what you have left

Every threshold in this file depends on an estimate, and estimates are optimistic in the
direction that hurts:

- **Character-based estimation runs low.** A divisor calibrated on prose under-counts
  code, JSON and non-Latin text. Apply a padding factor, and prefer being early over
  being right.
- **Non-text content costs more than its representation suggests.** An image is worth
  hundreds to thousands of tokens depending on its dimensions; a reference to a file is
  worth nothing until it is read.
- **Reserve the output.** The threshold is not "the window" — it is the window minus the
  space the answer needs, minus a buffer for the next tool result. Express the trigger
  as a floor in absolute tokens, not only as a percentage: at a small window a
  percentage silently reserves too little.

## The circuit breaker

Compaction can fail — the summarizer errors, the provider is down, the result does not
shrink. **After a small number of consecutive failures, disable compaction for the run
and degrade deliberately**: stop adding to the context, compose the best answer
available, and say that compaction is unavailable.

Without this, a failing compaction is retried at the top of every iteration, and the
loop spends its remaining budget on the one operation that is not working.

**Related: refund the iteration.** When an iteration ends in a recoverable provider
error — a token limit that can be clamped and retried, a rate limit — do not charge it
to the max-iteration guard. A misconfiguration should not consume the budget that exists
to stop a runaway agent.

## Sub-agent context isolation

A sub-agent's value is not that it is a different prompt. **It is that it has its own
window.**

The contract: the sub-agent receives a task and the context it needs, works in a window
the parent never sees, and returns a typed result — a summary, not a transcript. The
parent's window grows by the size of the result, not by the size of the work.

This makes delegation the strongest context tool available: a search across forty files
costs the parent one paragraph. It also sets the design rule — if a sub-agent's return
value is proportional to its input rather than its conclusion, it is a function call
wearing a costume, and it will fill the parent's window anyway.

## The filesystem as context

Anything durable belongs in a file, not in the transcript:

- **It survives the boundary.** Compaction cannot delete what was never in the window.
- **It survives the process.** A crash loses the conversation and keeps the work.
- **It is shared.** Two agents on one task coordinate through files; a transcript is
  private to one loop.
- **It is addressable.** A path is a few tokens; the content it names can be any size.

The pattern is the same in each case: do the work, write the artifact, keep the path.
Where the runtime offers no real filesystem, the same contract works over any keyed
store — what matters is that the address is cheap and the content is retrievable, not
that it is POSIX.

## Choosing your own constants

Every number in this file is deliberately absent, because the useful value depends on
the window, the tool mix and the cost of a summarizer call in your stack. Pick them
against these anchors:

1. **Reserve output before you reserve anything else.** Start from window minus expected
   answer minus one worst-case tool result.
2. **Rung 1's keep-count** is the smallest number of recent tool results the loop
   actually re-reads. Measure it; the intuition is always too high.
3. **The inline limit for offload** should be crossed only by outputs that are genuinely
   large — if half of all tool calls offload, the limit is too low and the model is
   reading files instead of working.
4. **The circuit-breaker count** is small. Three consecutive failures is a pattern, not
   a coincidence.
5. **Write them down where the loop reads them**, not inline at the call site. A
   threshold nobody can find is a threshold nobody will tune.
