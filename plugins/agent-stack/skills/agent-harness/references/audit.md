# Auditing an agent system

**Load this when:** reviewing an agent system you did not build — a due-diligence pass, an
inherited codebase, or a "why is this unreliable" investigation.

**Spec pinned:** the tracks below are this pack's synthesis of Anthropic agent guidance, `promptingguide.ai` and the sibling skills · read 2026-08-14

## Contents

- What this audit produces
- Run the scanner first
- Seven tracks
- Evidence tiers
- Priority, computed
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

## Priority, computed

`P = blast × confidence / effort`

- **blast** 3 = a user of the system is harmed · 2 = the operator · 1 = a future maintainer
- **confidence** 3 = measured · 2 = documented · 1 = judgement
- **effort** 1 = under an hour · 2 = a session · 3 = its own project

Computed, not felt — so a dramatic finding nobody can act on ranks below a boring one that
is fixed before lunch, and the ranking can be argued with on its inputs.

## The report

1. **One paragraph** — what the system is, which layer, and the single most important thing.
2. **The scanner output**, including its blind-spot list, verbatim.
3. **Findings by track**, each with observation, tier and priority.
4. **The plan** — ordered by P, with the first three items sized so they can start immediately.
5. **What was not looked at**, and why. An audit that does not say where it stopped is read
   as complete.

## Traps

- **Auditing the code and not the prompt.** The prompt is the largest behavioural surface and
  is often not in the repository at all — ask where it lives before concluding it is fine.
- **Filing "no permission model" against a harness that delegates by design.** Check the
  layer first (`layers.md`).
- **Grading instead of planning.** A score ends the conversation the audit was meant to start.
- **Confusing "no evals" with "not measured yet."** It is the root finding; put it first,
  because every other conclusion inherits it.
- **Reading a silent scanner as a clean system.** It is silent about what it can see.
