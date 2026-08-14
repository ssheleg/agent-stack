---
name: agent-harness
description: >-
  Use when the question is what the agent is TOLD rather than how its loop is wired — writing
  or fixing a system prompt, shaping tools so the model actually picks the right one,
  deciding whether a job wants a workflow or an agent, or choosing between ReAct, reflection,
  planning and voting. Also the audit direction: reviewing an agent system somebody else
  built, with tracks, evidence tiers and a prioritized plan instead of a score, plus a
  scanner for the defects that are mechanically visible. Triggers - "system prompt", "tool
  description", "the agent picks the wrong tool", "agent loops forever", "prompt engineering",
  "ReAct", "reflection", "workflow or agent", "audit this agent", "review our agent system",
  "системный промпт", "агент не вызывает тул", "аудит агента", "воркфлоу или агент". Not for
  the loop's plumbing, its evals, or the protocols it speaks — those are the sibling skills.
---

# Agent harness — what the agent is told, and how to audit what someone else told theirs

`agent-orchestrator` wires the loop. `agent-evals` proves it behaves. `agent-interop` gets
it talking to other processes. **This skill is the layer between them and the model: the
prompt, the tools, and the shape of the work.**

It runs in both directions. Building one and auditing one are the same checklist read
forwards and backwards, which is why they live together here.

---

## Rule zero — most agent bugs are prompt bugs wearing a stack trace

The instinct when an agent misbehaves is to change the code. The measured reality, in every
source this skill was built from, is that the largest behavioural changes come from the
text: **"the biggest performance improvements often come from clearly explaining tool usage
in the system prompt"**, and **"even small refinements to tool descriptions can yield
dramatic improvements."**

Before adding a retry, a router, or a sub-agent, check in this order:

1. **Does the tool description say when to use it, not just what it does?**
2. **Does the system prompt name the vocabulary?** An agent told to track status will invent
   `pending` and `to-do` and `done` and `completed` in the same run unless the allowed values
   are enumerated.
3. **Does the agent know today's date?** A model with a training cutoff will answer from
   memory rather than search unless the current date is injected.
4. **Is the instruction flexible where it should be strict?** *"Use the tools in the order
   that makes most sense to you"* is right while you are learning the task and wrong in
   production, where *"you MUST execute a web search for each task"* is what stops a step
   from being skipped.

Only then reach for architecture. Reaching for it first is how a prompt defect becomes a
permanent structural cost.

---

## Workflow or agent — decide this before anything else

An **agent** dynamically directs its own process. A **workflow** follows predefined code
paths. The choice is not about sophistication; it is about whether the number of steps is
knowable in advance.

| Build a workflow when | Build an agent when |
|---|---|
| requirements are clear and stable | the task is open-ended or exploratory |
| predictability and explicit control matter | flexibility outweighs predictability |
| debugging and cost control are priorities | adaptive reasoning across variables is needed |
| you can name every step now | step count is unpredictable and cannot be hardcoded |

**Start at the simplest thing that works, and stop there.** An agent adds latency, cost and
a class of failure a workflow does not have — it needs *trust in its own decisions*. Pay for
that only where a fixed path genuinely cannot be written.

### The five workflow patterns, before you reach for autonomy

| Pattern | Shape | Reach for it when |
|---|---|---|
| **Prompt chaining** | sequential calls, each on the last output, with programmatic checks between | the task decomposes into fixed steps — outline then draft, draft then translate |
| **Routing** | classify the input, send it to a specialist | categories are distinct and each wants its own prompt |
| **Parallelization** | *sectioning* (independent subtasks at once) or *voting* (same task N times) | subtasks are independent, or confidence needs more than one sample |
| **Orchestrator–workers** | a central model decomposes and delegates, then synthesizes | the subtasks **cannot be predefined** — this is the honest boundary with routing |
| **Evaluator–optimizer** | one model produces, another critiques, loop | clear evaluation criteria exist and iteration measurably helps |

**Orchestrator–workers versus routing is the distinction people get wrong.** Routing picks
from a known set. Orchestration invents the set per request. If you can enumerate the
branches, you wanted routing and it is cheaper.

---

## References

Each opens with its own **Load this when** line and a revision stamp — this material moves,
and `test/validate.py` fails the build on a reference that does not say when it was read.

| File | Read it when |
|---|---|
| [`references/system-prompt.md`](references/system-prompt.md) | you are **writing or fixing the prompt** — altitude, structure, vocabulary, dynamic context, and what changes for reasoning models |
| [`references/tools.md`](references/tools.md) | the model **picks the wrong tool, or none** — the agent–computer interface: how many, named how, described how, returning what |
| [`references/techniques.md`](references/techniques.md) | you are choosing between **ReAct, reflection, voting, planning** and the rest — every entry carries a verdict for production, not a benchmark score |
| [`references/layers.md`](references/layers.md) | deciding **what your harness owns** — kernel, workbench and product layers, and why permission boundaries are usually somebody else's job |
| [`references/audit.md`](references/audit.md) | reviewing **an agent system you did not build** — seven tracks, evidence tiers, and a prioritized plan |

**`scripts/audit_agent.py`** — the mechanical half of the audit. It finds what is visible
without understanding intent (an unbounded loop, a tool with no description, a swallowed
tool error, a hardcoded model, a missing timeout) and **prints the list of things it cannot
see**, so its silence is never read as a pass.

---

## Auditing an agent system — the short version

The long version is `references/audit.md`. The shape:

1. **Run the scanner first.** It is cheap, and its blind-spot list tells you what the rest of
   the audit must cover by hand.
2. **Walk the seven tracks** — prompt, tools, control flow, context, failure, permission,
   evidence — and record a finding only with an observation attached.
3. **Tier every recommendation** by what backs it: measured here, documented upstream, or
   judgement.
4. **Output a prioritized plan, not a score.** A number tells nobody what to change on
   Monday. This is the same rule `agent-evals` applies to eval rubrics and
   `seo-aeo-audit` to sites.

**The finding that ends most audits early:** the system has no evals. Everything downstream
is then unfalsifiable — including this audit. Say so first, and make it the first item.

---

## Boundaries

**Against `agent-orchestrator`.** That skill owns the loop's *plumbing*: iteration guards,
trimming, sub-agent dispatch, provider routing, memory layers, checkpoints. This one owns
what the model is *told*. They meet in one place:
`agent-orchestrator/references/context-engineering.md` covers **compaction** — what to drop
when the window fills — while this skill's `system-prompt.md` covers what to put there in
the first place. Filling and emptying, two files.

**Against `agent-evals`.** That skill measures whether an agent behaves, from execution
records. This one reviews how it was *built*, from its source and prompts. An audit that
finds no evals hands over to it; an eval suite that keeps failing on the same axis hands
back here.

**Against `agent-interop`.** MCP, A2A, the registry, gateways — the wire between processes.
Tool *descriptions* are here; tool *protocol* is there.

**Not covered:** model choice and pricing (see the `claude-api` skill for Anthropic's), the
wallet under resale (`agent-orchestrator/references/llm-proxy-billing.md`), and RAG
retrieval quality, which is a search problem this skill only touches where it enters the
prompt.

---

## Checklist — a harness worth shipping

- [ ] Workflow-versus-agent decided deliberately, and the simpler option was actually tried
- [ ] System prompt at the **right altitude** — heuristics, not hardcoded branches, not vague hope
- [ ] Every status, category and enum the agent must produce is **enumerated in the prompt**
- [ ] Today's date, and any other volatile context, injected rather than assumed
- [ ] Tools: a few high-impact ones, namespaced, each described as if to a new colleague
- [ ] Tool responses carry **meaning, not identifiers**, and are paginated or truncated by default
- [ ] Tool errors **teach the next attempt** instead of restating a stack trace
- [ ] One technique chosen per problem, with a reason — not ReAct because it was in a paper
- [ ] Sub-agents return **distilled summaries**, not transcripts
- [ ] The agent can be observed: which tool, which arguments, which observation, how many tokens
- [ ] An eval exists before the prompt is tuned, or the tuning is folklore
