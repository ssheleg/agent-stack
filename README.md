# agent-stack

[![validate](https://github.com/ssheleg/agent-stack/actions/workflows/validate.yml/badge.svg)](https://github.com/ssheleg/agent-stack/actions/workflows/validate.yml)
[![npm](https://img.shields.io/npm/v/%40ssheleg%2Fagent-stack)](https://www.npmjs.com/package/@ssheleg/agent-stack)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![site](https://img.shields.io/badge/docs-skills.sshlg.me-8ab0ff)](https://skills.sshlg.me/skills/agent-stack/)

**Build agent loops, harnesses, evals and protocol boundaries that stay inspectable under production failure.**

```bash
npx skills add ssheleg/agent-stack
```

Ask: `Design a resumable orchestrator with parallel collection and one convergence checker.`

**[Detailed docs →](https://skills.sshlg.me/skills/agent-stack/)**

**[Docs, and every skill →](https://skills.sshlg.me/)** · [this skill's page](https://skills.sshlg.me/skills/agent-stack/) · [follow @sshlg93 on X](https://x.com/intent/follow?screen_name=sshlg93)

Loads in **DeepSeek Harness** (`dsh`) with **no plugin to write**: it reads the
Agent Skills standard directly, scanning `~/.agents/skills` — where `npx skills
add` puts this pack — at rank 500.

Production patterns for building AI agent orchestrators — and for billing the
LLM access they burn.

Part of the [ssheleg skill family](https://github.com/ssheleg/sshlg-skills).

---

## What is in here

Four skills — `agent-orchestrator` for wiring the loop, `agent-evals` for proving it
behaves, `agent-interop` for everything it talks to outside its own process,
`agent-harness` for what it is **told** — and twenty references they load on demand,
plus one scanner.

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
- **the shape of the work, decided before the work**: an edge that carries no data is
  no edge, a plan that declares `depends_on` is executed in dependency layers rather
  than in list order, and a parallel layer gets a checker before the node that
  consumes it

**The evals skill** (`agent-evals/SKILL.md`) — how you know any of it works. An
agent's behaviour is not in its source, so the artifact under test is the
execution record: three primitives (run, trace, thread) crossed with three
granularities (single-step, full-turn, multi-turn), the offline/online/ad-hoc
timing axis, pass-fail rubrics instead of scalar scores that name no fix, cheap
code checks before model judges, judges calibrated against human labels before
they are trusted, and a corpus grown from production failures rather than
authored up front — where every fixed failure stays a fixture permanently.

**The interop skill** (`agent-interop/SKILL.md`) — the protocols an agent speaks
outside its own process, and the one rule that governs all of them: a protocol claim
without a date is a guess. Every one of these specifications moved in the last twelve
months in a way that silently breaks older code — MCP replaced the `initialize`
handshake with `server/discover` and went **stateless**, deprecated **sampling, roots
and logging**; A2A renamed its wire surface between v0.x and 1.0; agentgateway
deprecated `binds` while its own overview page still teaches it. So every reference
carries a `**Spec pinned:** … · read <date>` line, and the validator fails the build
without one. Six references: `mcp.md` (the wire and the full deprecation register),
`mcp-scale.md` (progressive discovery, code mode, and the prompt-cache interaction that
undoes both), `mcp-ship.md` (mounting, and the 404 that is really a double path),
`registry.md` (`server.json`, namespace proof, the registry's three refusals),
`a2a.md` (cards, task states, three bindings), `gateway.md` (what a gateway must do that
an API gateway does not). Plus a link map, and a verdict on each neighbouring standard —
ACP, AGNTCY, AP2, Agent Skills — so an agent stops guessing.

**The harness skill** (`agent-harness/SKILL.md`) — the layer between the loop and the
model, and the one where most agent bugs actually live: *the biggest performance
improvements often come from clearly explaining tool usage in the system prompt*, and *even
small refinements to tool descriptions can yield dramatic improvements*. Before adding a
retry or a sub-agent, it asks four questions about the text. Seven references —
`system-prompt.md` (right altitude, enumerated vocabulary, and the three things reasoning
models changed — starting with **do not add chain-of-thought**), `tools.md` (the
agent–computer interface, with a worked before/after and poka-yoke), `techniques.md`
(fifteen techniques, a verdict each **for production** rather than a benchmark),
`layers.md` (which layer you are building at, and why permission boundaries are usually the
environment's job), `audit.md` (seven tracks, evidence tiers, a plan instead of a score) —
plus **`pi.md` and `pi-sdk.md`, the doctrine as a worked implementation**: Pi read end to
end, each mechanism matched to the rule it instantiates, its divergences named, and the
eight extension seams where a permission gate or a context rewrite can actually live.

It runs in both directions: **building a harness and auditing somebody else's are one
checklist read forwards and backwards.** `scripts/audit_agent.py` is the mechanical half —
seven conservative detectors, and it always prints what it *cannot* see plus a denominator,
so its silence is never read as a pass.

**`references/graph-engineering.md`** — deciding the shape of the work before
doing it: node and edge, the fake-edge test, the diamond and the two ways it
fails silently, the checker node and what it costs, static versus dynamic with
auditability as the hard rule, when a graph is not worth building, and what a
host actually executes when it fans out — with the version evidence, because the
keyword the source named was renamed six weeks after it was published.

**`references/context-engineering.md`** — what the loop gives up when the window
runs out: the five-rung compaction ladder and why to re-measure between rungs,
the tool-pair boundary invariant, typed carryover blocks copied across the
boundary rather than summarized, tool-output offload to a file, token estimation
and the direction it errs, the compaction circuit breaker, sub-agent context
isolation, and how to choose constants for your own window.

**`references/runtime.md`** — what keeps an agent alive between requests, which
most orchestrators assume rather than specify: checkpointing every iteration and
not just the stages a human reviews, one interrupt/resume contract instead of two
mechanisms for one idea, the four double-texting policies, streaming a dropped
connection can rejoin, forking a past checkpoint to debug through the real loop,
stateful versus stateless schedules, and the seven cross-cutting concerns pulled
out of the loop into ordered interceptors — where order is semantics.

**`references/governance.md`** — permission rather than cost. The four boundaries
an agent crosses (model, tool, external server, agent-to-agent), each with its own
control set; the guardrail taxonomy and its honest limit — every content check is
probabilistic, so anything consequential gets a deterministic limit or a human;
why an audit row without a policy version cannot prove a control was applied;
cost attribution as a hierarchy; failover that must land somewhere approved rather
than merely available; fail-open versus fail-closed as a per-workload decision;
and blast radius — a sandbox protects the host, not the sandbox.

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

**npm installer** — copies both skills into `~/.claude/skills/`:

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

`agent-orchestrator`: building an agent system, an orchestrator, an LLM-powered
tool, a chatbot with tool use, or an AI pipeline. Also the money side — metering
usage, per-tenant keys, spend tracking, budget limits, loop detection — and the
permission side: what a tool may reach, what leaves the boundary, and what an
audit row has to carry to prove a control was on.

`agent-evals`: measuring whether the result behaves. Building a suite, judging a
trajectory rather than a final answer, turning a production failure into a
permanent fixture, calibrating a judge, gating a release on offline evals.

`agent-harness`: writing or fixing a system prompt, shaping tools so the model picks the
right one, choosing between ReAct, reflection, planning and voting — or auditing an agent
system somebody else built. Not the loop's plumbing, its evals, or its protocols.

`agent-interop`: building or consuming an MCP server, exposing or calling another
agent over A2A, publishing to the MCP Registry, or putting a gateway in front of
agent traffic. Not for designing one server's tool set — that is a design problem,
and Anthropic's `mcp-server-dev` plugin is built for it — and not for a skill's own
construction, which is `make-skill`. That boundary runs both ways: `make-skill` keeps
what changes *because you are writing a skill*, and the protocol itself is described
here and nowhere else in the family.

None of the four triggers for a single LLM call in a script or for prompt wording —
that is not an orchestrator, and pulling this much doctrine for it is how a skill
teaches you to route around it.

---

## Verify

<!-- commands-run-in: a clone -->
These run **in a clone of this repository**. The published npm package ships no
`test/` directory, so from an install they are names, not commands.

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
