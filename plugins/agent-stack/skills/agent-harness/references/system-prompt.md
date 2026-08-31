# The system prompt — altitude, vocabulary, and what changes for reasoning models

**Load this when:** writing or fixing an agent's system prompt, or explaining why the same
prompt behaves differently across runs.

**Spec pinned:** Anthropic context-engineering and agent guidance; `promptingguide.ai` agents/* and guides/reasoning-llms · read 2026-08-14

## Contents

- The right altitude
- What actually belongs in there
- Enumerate the vocabulary
- Inject what the model cannot know
- Flexible while learning, strict in production
- Structure, examples, and the cost of formatting
- Reasoning models change three things
- Traps

## The right altitude

A system prompt fails in two directions and the middle is narrower than it looks.

**Too low** — hardcoded if-then branches for every case. It works on the cases you wrote and
is brittle everywhere else, and each new case costs another branch. You are writing a
program in prose, badly.

**Too high** — vague guidance that assumes a shared understanding the model does not have.
"Be helpful and use good judgement" tells it nothing it did not already believe.

The target: **specific enough to guide behaviour, flexible enough to give the model strong
heuristics.** A useful test — could a competent new colleague follow this without asking a
clarifying question, and without being insulted? If they would ask, it is too high. If they
would feel micromanaged into a corner where their judgement cannot help, it is too low.

## What actually belongs in there

In rough order of how much behaviour each buys:

1. **Tool usage instructions.** Not the tool schema — the *policy*. When to reach for which,
   what order usually makes sense, what to do when one fails. The largest measured gains come
   from here, and it is the part most teams leave to the schema alone.
2. **The role and its boundaries** — what this agent is for, and what it must hand off.
3. **The vocabulary** it must produce (below).
4. **Volatile context** it cannot know (below).
5. **Failure instructions** — what to do when a tool errors, when data is missing, when the
   task is impossible. Absent, the model invents a recovery, and inventions are not uniform.
6. **Output contract** — shape, not prose about shape.

## Enumerate the vocabulary

**Be explicit about allowed values.** An agent asked to track task status will produce
`pending` in one turn and `to-do` in the next, `completed` here and `done` there — and any
code reading those strings now has a bug that appears intermittently and reads as
flakiness.

This generalises past status: every category, label, severity, priority or state the agent
emits should appear as an enumerated set in the prompt, or in the tool's parameter `enum`,
or both. It is the cheapest determinism available.

## Inject what the model cannot know

**Today's date is the canonical example**, and its absence has a specific failure signature:
the agent answers from training data instead of searching, confidently and with no error.
Inject the date and the behaviour changes without another word of instruction.

The general rule: anything volatile that the model would otherwise fill from memory —
current date, environment, tenant, available capabilities, the user's locale — is injected,
not assumed. A capability-aware prompt that lists only the tools actually connected beats a
static prompt describing tools that may be absent.

**A worked injection, because the shape is the lesson.** A data-verification protocol added
only when a database is connected:

> - First-time metrics: ask the user *"Do these numbers match expectations?"*
> - Financial figures: mention units (cents vs dollars) and ask for confirmation
> - Anomalies: explain proactively and ask the user to verify
> - Rejected data: investigate the discrepancy, and record the finding as a learning

Note what makes it injectable rather than permanent: every line is conditional on a
capability the agent may or may not have. It arrived here from `agent-orchestrator`'s §10,
which owns the *wiring* that assembles a prompt and says in its own text that the content
belongs in this file — so a protocol sitting there contradicted the boundary its section
had drawn.

## Flexible while learning, strict in production

The same instruction should not survive the whole lifecycle.

- **While you are still learning what good looks like:** *"Use the tools in the order that
  makes most sense to you."* This surfaces what the model thinks the task is, which is the
  information you need.
- **Once the sequence is known and a skipped step is a defect:** *"You MUST execute a web
  search for each task."* Flexibility here buys nothing and costs a silently missing step.

Teams get stuck at the first form because it felt elegant, then debug an agent that
"sometimes forgets" — which is not forgetting, it is permission.

## Structure, examples, and the cost of formatting

**Structure inputs and outputs** with delimiters, XML tags or JSON. Clear segmentation
reduces the class of error where the model treats data as instruction.

**Examples are worth more than description**, and the mistake is quantity. Curate a few
**diverse, canonical** examples rather than an exhaustive list of edge cases — the latter
reads as a lookup table and the model generalises from it badly.

**But formatting has a cost.** Keep formats close to natural internet text where you can;
elaborate escaping, deeply nested structures and unusual syntaxes spend the model's
attention on parsing rather than the task. Ask whether a human writing this by hand would
choose the format. If not, it is overhead.

## Reasoning models change three things

Treating a reasoning model like a completion model is now a common and expensive mistake.

1. **Do not add chain-of-thought instructions.** Native reasoning already happens.
   Explicit step-by-step prompting is redundant and **can hurt instruction-following** —
   which is the opposite of what the person adding it intends.
2. **Give goals, not procedures.** Be explicit about the high-level outcome and let the
   model plan the route. Procedural micro-steps fight the thing you are paying for.
3. **Reasoning effort is a dial that did not exist before** — low/medium/high trades cost
   against accuracy per call, so it is a per-stage decision, not a global setting.

Two more, worth knowing before you architect around them: **few-shot is still useful, but
mainly for output *format***, not for teaching the task; and **tool-calling remains weaker
in most reasoning models**, which is why the common shape is a reasoning model for planning
and a different one for execution.

## Traps

- **Growing the prompt instead of fixing it.** Every incident adds a sentence; nothing is
  ever removed; a year later nobody can say which line does work. Prune on the same schedule
  you add.
- **Describing tools twice**, in the schema and in the prompt, with the two drifting. Put
  *policy* in the prompt and *contract* in the schema, and say which is which.
- **A prompt that assumes a tool exists.** Capability-aware assembly, or an explicit
  fallback; never a promise the runtime may not keep.
- **Tuning the prompt with no eval.** You are optimising against the last thing you noticed.
  See `agent-evals`.
- **One prompt for planning and execution.** Separation of concerns measurably improves
  reliability and lets a cheaper model take the mechanical half.
