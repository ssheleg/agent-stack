# Runtime — what keeps an agent alive between requests

**Load this when** the agent must survive things a single request does not: a crash
mid-run, a human who has to approve before it continues, a user who sends a second
message while the first is still working, a dropped connection, a schedule. The body's
loop is the *harness* — what the model is given to work with. This is the layer beneath
it, and most orchestrators assume it exists rather than specify it.

The split is worth keeping in mind while reading: **a good harness makes an agent
capable, a good runtime makes it deployable.** They fail differently, and a team that
has only built the first one discovers the second in production.

## Contents

- Durability, and where our own asymmetry was
- The interrupt/resume contract
- Double-texting: four policies
- Streaming that survives a dropped connection
- The tracker, concretely — what the feed above is made of
- Time travel and forking
- Scheduled and sleep-time work
- Middleware: the seven concerns, unwelded

## Durability, and where our own asymmetry was

**Checkpoint every iteration of the loop, not just the stages a human reviews.**

The body's multi-stage pipeline persists at each `stage.checkpoint` and can resume from
a `pipeline_run_id`. The simple tool-calling path persists nothing: a crash, a deploy or
a killed worker loses the entire run, including the tool calls that already cost money
and time. That asymmetry is a defect, not a design — the simple path is the one that
runs most often.

What a checkpoint holds: the message array, the iteration counter, accumulated token
usage, the carryover state (see `context-engineering.md`), and whatever the sub-agents
have returned so far. Keyed by a thread id that acts as a cursor into the run.

Two properties earn their cost:

- **Resume at the point of failure**, not at the last human review. The difference is
  whole minutes of re-executed tool calls.
- **A pause frees the worker.** An agent waiting for a human should hold no process. If
  waiting costs a worker, long approvals are quietly expensive and teams stop using them.

## The interrupt/resume contract

The body has two mechanisms for one idea: `ask_user` raises a clarification error, and a
pipeline checkpoint returns a paused result. **They should be one contract.**

- **Interrupt** — the run stops at a named point, persists its state, and surfaces a
  payload describing what it needs: a question, a plan to approve, a destructive action
  to confirm.
- **Resume** — the caller returns a decision, and execution continues *from that point*
  with the decision in scope. Not a fresh run that re-derives its way back.

One contract means one persistence format, one place a UI has to understand, and one
answer to "what happens if nobody replies for a day".

**When an interrupt is mandatory** rather than optional: any action that is
hard to reverse or outward-facing. Content-level guardrails are probabilistic — see
`governance.md` — so consequential actions need a deterministic limit or a human, not a
classifier's opinion.

## Double-texting: four policies

A user sends a second message while the first is still running. This has four possible
answers, and a system that never chose one has chosen the worst by accident:

| Policy | Behaviour | Fits |
|---|---|---|
| **Enqueue** | finish the current run, then start the new one | a task where the first answer is still wanted |
| **Reject** | refuse the second message while busy | expensive or transactional runs |
| **Interrupt** | stop the current run, start the new one, keep what was produced | conversational agents — the usual default |
| **Rollback** | discard the current run *including its input*, start clean | the user is correcting themselves |

The difference between interrupt and rollback is what the transcript looks like
afterwards, and it is worth deciding deliberately: interrupt leaves a half-finished turn
in history that the next prompt will see.

## Streaming that survives a dropped connection

Four things are worth streaming, and they are not the same thing:

1. **State snapshots** after each step — for a UI that renders the whole picture.
2. **State deltas** — the same, cheaper.
3. **Tokens** — the typing effect.
4. **Custom events** — domain progress: "queried 3 of 7 sources".

The body's tracker emits an in-memory feed. Two properties turn it into something a
client can rely on:

- **Every event carries a monotonic id**, and a client reconnecting sends the last id it
  saw. The server replays from there. Without this, a dropped connection during a
  ninety-second run means the user watches nothing and then gets an answer from nowhere.
- **The feed is a view over the durable trace, not the record itself.** If the only copy
  of what happened is a stream nobody stored, evaluation is impossible — see the
  `agent-evals` skill, which cannot function without it.

## The tracker, concretely — what the feed above is made of

Real-time progress via `WorkflowTracker`:

```python
class WorkflowTracker:
    # In-memory event bus with asyncio.Queue subscribers
    async def begin(pipeline, context) -> workflow_id
    async def emit(wf_id, step, status, detail)
    async def end(wf_id, agent, status, detail)

    @asynccontextmanager
    async def step(wf_id, step_name, description):
        # Emits started/completed/failed with elapsed_ms

# Event types:
# pipeline_start/end, thinking, token (streaming), orchestrator:llm_call,
# orchestrator:sql_agent, orchestrator:llm_retry, orchestrator:warning
```

The final answer streams in chunks as `token` events on the same bus — a typing effect is
a chunked emit, not a second mechanism. What makes the feed reliable rather than decorative
is in `references/runtime.md`: a monotonic id per event so a reconnecting client can resume,
and the feed being a **view over the durable trace** rather than the record itself.

---

This moved out of `SKILL.md` on 2026-08-16. It was the concrete half of the section
two headings up, in a different file: *streaming that survives a dropped connection*
stated the two properties that matter and the body stated the API without them. One
home, and the properties now sit beside the thing they are properties of.

## Time travel and forking

Once every iteration is checkpointed, one capability follows nearly free: **pick a past
checkpoint, modify the state, and resume from it.** The original history stays; the
modified run forks.

This is the debugging tool the loop otherwise lacks. "Why did it call that tool?" is
answerable by rewinding to the step before, changing one thing, and running forward
again — through the real loop, with real model calls and real tools, rather than a
reconstruction that may not share the bug.

It is also how a failed production run becomes a regression fixture: fork at the failure
point, minimise, save the state as the fixture's input.

## Scheduled and sleep-time work

Not all agent work starts with a user. Two shapes, and the distinction matters:

- **Stateful schedule** — each run appends to an existing thread, so the agent remembers
  the previous ones. A daily briefing that should not repeat itself.
- **Stateless schedule** — each run starts a fresh thread. A monitor that must not drift
  on yesterday's context.

Scheduled runs need the same retry and tracing as interactive ones, and one extra rule:
**a schedule that fails silently is worse than no schedule.** Failures must reach a human
through something other than the absence of a result.

**Sleep-time compute** is the useful pattern on top: work done between conversations —
consolidating memory, refreshing an index, pre-computing what tomorrow's first question
will need. It is also where memory consolidation belongs when the hot path is too busy
for it.

## Middleware: the seven concerns, unwelded

The body's loop hand-codes seven cross-cutting concerns inside itself: retry, provider
fallback, summarisation, human-in-the-loop, tool-call limits, redaction, and moderation.
Each is correct and none is separable — changing the retry policy means editing the loop.

The alternative is ordered interceptors at four points:

| Hook | Runs | Typical use |
|---|---|---|
| `before_model` | before the request is built | inject context, redact, enforce a budget |
| `wrap_model_call` | around the call | retry, fallback, timing, cost accounting |
| `wrap_tool_call` | around each tool | authorisation, rate limits, argument validation |
| `after_model` | on the response | moderation, structured-output repair, guardrails |

The hook names are borrowed vocabulary; the shape is generic. What it buys is
composition — a tool-call limit is one interceptor, not a counter threaded through three
functions — and testability: an interceptor is a unit, the loop is not.

The trap: **order is semantics.** Redaction after summarisation redacts a summary that
already leaked. Write the order down where the list is defined, not in the head of
whoever wrote it.
