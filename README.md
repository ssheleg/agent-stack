# agent-stack

Production patterns for building AI agent orchestrators — and for billing the
LLM access they burn.

Part of the [ssheleg skill family](https://github.com/ssheleg/sshlg-skills).

---

## What is in here

One skill, `agent-orchestrator`, and two references it loads on demand.

**The orchestrator** (`SKILL.md`) — what the agent reads first:

- a shared context object and a sub-agent protocol with typed results
- a tool-calling loop that survives its own context pressure: in-loop trimming
  at ~80% of the window, a wrap-up instruction at ~70%, a max-iteration guard
  that still composes a partial answer instead of returning nothing
- meta-tools that **delegate to sub-agents** rather than execute directly
- sub-agent retry split into retryable and fatal, with validation between tries
- a multi-stage pipeline for complex work: complexity detection, checkpoints
  where a human approves, and resume after they do
- multi-provider LLM routing with a fallback chain, per-provider exponential
  backoff that respects `retry_after`, health checks and one error hierarchy
- a four-layer memory system — chat history, working memory, long-term
  learnings, insights — each with its own lifetime, confidence lifecycle and
  decay, plus conflict resolution when a new learning contradicts an old one
- context budget allocation by priority
- self-learning feedback loops

**`references/patterns.md`** — the data models and algorithms underneath:
message and result protocols, pipeline models, the SQL validation loop,
context-window sizes and token estimation, learning-extraction heuristics,
confidence management, fuzzy deduplication, conflict resolution, cross-resource
learning transfer, and a suggestion engine that costs no LLM calls.

**`references/llm-proxy-billing.md`** — for when the product resells LLM access:
tiered wallets and the single boundary where markup applies, two-phase commit
across a database and a provider API with compensating transactions,
transaction-scoped advisory locking, optimistic concurrency for reclaims,
spend-delta polling and the three cases it must tell apart, budget / loop /
auto-pause guardrails, per-tenant key lifecycle and healing, the refund
waterfall, and model-routing precedence.

---

## Install

**Claude Code plugin** (recommended):

```bash
/plugin marketplace add ssheleg/agent-stack
/plugin install agent-stack@agent-stack
```

**npm installer** — copies the skill into `~/.claude/skills/`:

```bash
npx @ssheleg/agent-stack
```

**Any of 70+ agents:**

```bash
npx skills add ssheleg/agent-stack
```

**Whole family at once:**

```bash
npx --yes sshlg-skills@latest update
```

Restart your agent afterwards — skills load at session start.

---

## When it triggers

Building an agent system, an orchestrator, an LLM-powered tool, a chatbot with
tool use, or an AI pipeline. Also when the work is the money side: metering
usage, per-tenant keys, spend tracking, budget limits, loop detection.

It does **not** trigger for a single LLM call in a script, or for prompt
wording — that is not an orchestrator, and pulling 1200 lines of doctrine for it
is how a skill teaches you to route around it.

---

## Verify

```bash
python3 test/validate.py
```

Checks one version across `package.json`, `plugin.json`, `marketplace.json` and
the top `CHANGELOG` entry; front matter inside the Agent Skills limits (over-long
front matter does not error — hosts truncate it silently, which is worse); and
that `SKILL.md` and `references/` agree in **both** directions, so neither a
dangling link nor a file nobody loads can ship.

---

## License

MIT © ssheleg
