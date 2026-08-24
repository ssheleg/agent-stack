# Auditing an agent system

**Load this when:** reviewing an agent system you did not build — a due-diligence pass, an
inherited codebase, or a "why is this unreliable" investigation.

**Spec pinned:** the tracks below are this pack's synthesis of Anthropic agent guidance, `promptingguide.ai` and the sibling skills · read 2026-08-14

## Contents

- What this audit produces
- Run the scanner first
- Seven tracks
- Evidence tiers
- Priority — four axes, and no scalar
- The report
- Traps

## What this audit produces

**A prioritized change plan, with an observation behind every finding.** Not a score.

A number compresses away the only useful information — *what to change on Monday* — and
invites arguing about the number. This is the same rule `agent-evals` applies to eval
rubrics and `seo-aeo-audit` applies to sites, and it is the family's position rather than a
preference: **pass/fail with a named failure condition beats a scalar that names no fix.**

## Run the scanner first

```bash
python3 scripts/audit_agent.py <path>          # human-readable
python3 scripts/audit_agent.py <path> --json   # machine-readable
```

It finds only what is mechanically visible, and **it prints the list of what it cannot see.**
Read that list: it is the agenda for the manual half. A scanner that goes quiet is reporting
its own blindness, and an audit that stops there has audited the scanner.

## Seven tracks

Walk them in order. Later tracks assume earlier ones.

### 1 — Prompt

- Is there a system prompt under version control, or is it a string literal edited in place?
- **Altitude**: hardcoded branches (brittle) or vague hope (useless)? See `system-prompt.md`.
- Are the values the agent must emit **enumerated**, or invented per run?
- Is volatile context — the date above all — **injected**?
- Is tool *policy* in the prompt, or only tool *schema*?
- Has it been pruned, or only appended to since the first incident?

### 2 — Tools

- How many? Can the team say, without hesitating, which applies to a borderline case?
- Are descriptions written **for a model choosing under uncertainty**, or for a human reading docs?
- Do responses return **meaning or identifiers**?
- Is there a default limit on response size, or only an optional one?
- Do errors **name the next action**?
- Are destructive tools guarded by shape (`confirm: true`, absolute paths, enums) rather than by instruction?

### 3 — Control flow

- **Workflow or agent — and was that decided, or defaulted?** An agent where a chain would do is the most expensive finding on this list.
- Is there a **bounded iteration guard**, and what happens at the bound — a partial answer, or nothing?
- Are retries and fallbacks **multiplied**? Three providers × three retries is nine calls for one prompt.
- Is there loop detection, or does a repeated near-identical tool call run until the budget does?
- Do sub-agents return **distilled summaries** or transcripts?

### 4 — Context

- Does anything measure window usage **before** a request fails?
- Is there a compaction strategy, and does it preserve **decisions and open questions** rather than the discussion?
- Can a large tool result be **offloaded** and referenced, or does it land in the window whole?
- Is memory a design, or the conversation history by default?

### 5 — Failure

- What happens when a tool errors — is it distinguished from a tool returning nothing?
- Under MCP, is `isError: true` handled, or does a 200 read as success?
- Is there a timeout on every external call?
- Is degradation **honest** — does the user learn the answer is partial?
- Is there a path where the agent silently does nothing and reports success?

### 6 — Permission

- **Which layer owns the boundary?** If the harness delegates it (`layers.md`), audit the surroundings instead of filing a finding.
- Is tool access differentiated per caller, or is one credential shared by every path?
- Is tool output treated as **untrusted input**?
- Can an audit row prove a control was applied — does it carry the **policy version**?
- Is there a deterministic limit anywhere consequential, or only probabilistic content checks?

### 7 — Evidence

- **Are there evals?** If not, this is finding number one and everything else is unfalsifiable.
- Do they judge the **trajectory**, or only the final answer?
- Has any production failure become a permanent fixture?
- Is a judge calibrated against human labels, or trusted because it is a judge?
- Can a past run be replayed — is the execution record durable?

## Evidence tiers

Every finding carries one, and the tier is part of the finding:

| Tier | Means | Example |
|---|---|---|
| **Measured** | observed here, in this system, with the observation attached | "`agent.py:212` — the `while` has no bound; a repeated call ran 47 times in the log at `logs/2026-08-02`" |
| **Documented** | the upstream source says so, and this system contradicts it | "descriptions restate the name; Anthropic's tool guidance calls this the highest-leverage fix" |
| **Judgement** | experience, no measurement available here | "two tools look interchangeable to us" |

**Never present judgement as measured.** A finding whose tier is honest survives the meeting
where it is challenged; one that is inflated loses the whole report.

## Priority — four axes, and no scalar

`P = blast × confidence / effort` used to sit here, and it contradicted the two sections
above it. "Not a score" and *pass/fail with a named failure condition beats a scalar that
names no fix* cannot share a file with a number the plan is then ordered by.

**And the number does not do what it claimed to do.** The section said the ranking "can be
argued with on its inputs", but multiplication destroys them: `3 × 1 / 3` and `1 × 1 / 1`
both print **1**, so *harms a user, judgement-tier, its own project* and *annoys a future
maintainer, judgement-tier, an hour* arrive at one priority and nobody reading the output
can tell which is which. A product is a one-way function on the very inputs the argument
needs.

<!-- priority-axes: impact, irreversibility, uncertainty, coordination -->

So the inputs are published and the arithmetic is not. The axes are the manifesto's four
(`manifesto` → *"How many agents, repositories, services, and owners meet at the
change"*, under *"These axes are not a fake numerical score"*), and two of them were absent here entirely while `effort` — a **cost**,
not a risk axis — had been substituted into their place:

| Axis | Question | High · Medium · Low |
|---|---|---|
| **Impact** | What is harmed if the finding is right? | a user of the system · the operator · a future maintainer |
| **Irreversibility** | How hard is the harm to undo once it lands? | unrecoverable · recoverable with work · trivially reversible |
| **Uncertainty** | How much of the behaviour cannot be checked deterministically? | unmeasurable here · measurable but unmeasured · measured |
| **Coordination** | How many agents, repositories, services and owners meet at the fix? | many · two · one |

**Ordering rule: the first axis that separates two findings decides, in that order.**
Impact, then Irreversibility, then Uncertainty, then Coordination. It is inspectable in the
direction the old formula was not — a reader who disagrees with the order of two findings
can point at the axis that decided it and argue about that axis alone.

**Effort keeps its job and loses its rank.** It is recorded per finding — under an hour · a
session · its own project — and it never moves a finding up or down. It sizes the *first
three items of the plan* so they can start immediately, which is the only decision it was
ever good for. A cost that divides a risk is how "too expensive to fix" becomes "not
important".

**Uncertainty is not the old `confidence` renamed.** `confidence` graded the auditor's
evidence; the axis grades what the *system* cannot be made to prove. The evidence grade
still exists and is still required — it is the tier on every finding, one section up — and
a finding whose tier is `judgement` says so there rather than being quietly discounted here.

## The report

1. **One paragraph** — what the system is, which layer, and the single most important thing.
2. **The scanner output**, including its blind-spot list, verbatim.
3. **Findings by track**, each with observation, tier, the four axes and its effort.
4. **The plan** — ordered by the axes above, first separating axis wins, with the first
   three items sized by effort so they can start immediately.
5. **What was not looked at**, and why. An audit that does not say where it stopped is read
   as complete.

## Traps

- **Auditing the code and not the prompt.** The prompt is the largest behavioural surface and
  is often not in the repository at all — ask where it lives before concluding it is fine.
- **Filing "no permission model" against a harness that delegates by design.** Check the
  layer first (`layers.md`).
- **Grading instead of planning.** A score ends the conversation the audit was meant to
  start — including a score assembled from honest axes. Publish the axes; do not multiply
  them.
- **Confusing "no evals" with "not measured yet."** It is the root finding; put it first,
  because every other conclusion inherits it.
- **Reading a silent scanner as a clean system.** It is silent about what it can see.
