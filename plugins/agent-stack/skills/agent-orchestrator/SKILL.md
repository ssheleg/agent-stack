---
name: agent-orchestrator
description: >-
  Use when building an agent system — an orchestrator, an LLM-powered tool, a chatbot with tool
  use, an AI pipeline — or metering and billing the LLM access it burns. Covers tool-calling
  loops, pipelines with human checkpoints, provider routing with fallback/retry, memory
  architecture, retrieval and decay, context budgets, sub-agent coordination, error hierarchies; the
  work as a graph — parallel layers, fake edges, a checker before convergence; for resale:
  tiered wallets, one markup boundary, two-phase commit across database and provider API,
  spend-delta polling, budget and loop guards, per-tenant keys. Triggers - "agent",
  "orchestrator", "tool calling", "sub-agent", "LLM router", "fallback chain", "human in the
  loop", "memory layer", "LLM billing", "token wallet", "checker node", "агент", "оркестратор",
  "суб-агент", "роутер моделей", "человек в цикле", "слой памяти", "биллинг LLM", "граф задач".
  Not for a single LLM call in a script, or prompt wording.
---

# Agent Orchestrator — Production Best Practices

Patterns from a production multi-agent system. **The body is decisions; the mechanisms are
one file away**, and it is held under a 4750-token budget — a body that grows absorbs the
layer that should have been split, and this one did until 2026-08-16.

## Architecture Overview

```
User Question
    ↓
OrchestratorAgent.run(AgentContext)
    ├─ Shape check → one loop, or a planned path (§5, references/pipeline.md)
    ├─ Context loading (a parallel layer: staleness, sources, KB — §13)
    ├─ History trimming, then context budget allocation
    ├─ System prompt built from the live capabilities (§10)
    └─ Execute:
        ├─ SIMPLE: LLM → tools → sub-agents → results → LLM → … → answer   (§2)
        └─ PLANNED: plan → dependency layers → checker → checkpoints → done (§5)
```

## 1. The Orchestrator Pattern

### Shared Context Object

Pass a single immutable-ish context object to all sub-agents:

```python
@dataclass
class AgentContext:
    project_id: str
    user_question: str
    chat_history: list[Message]
    llm_router: LLMRouter           # provider abstraction with retry/fallback
    tracker: WorkflowTracker        # SSE event emitter for real-time UI
    workflow_id: str                 # unique ID for this request
    connection_config: ... | None   # external resource config
    user_id: str | None
    preferred_provider: str | None  # e.g. "openrouter"
    model: str | None               # e.g. "<provider>/<model-id>"
    extra: dict[str, Any]           # pipeline_action, flags, overrides
```

**Key principles:**
- Sub-agents never modify context — they return typed results
- Provider/model preferences flow down from user → project defaults → app defaults
- `extra` dict carries pipeline state, flags like `_skip_complexity`, session IDs

### Sub-Agent Protocol

Every sub-agent extends a base class:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, context: AgentContext, **kwargs) -> AgentResult: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @staticmethod
    def accum_usage(total, usage): ...  # merge token counters
```

Typed result subclasses per agent (e.g. `SQLAgentResult` with `query`, `results`, `attempts`).

---

## 2. Tool-Calling Loop (Simple Path)

The core agent loop pattern:

```python
max_iter = settings.max_orchestrator_iterations  # e.g. 10
for iteration in range(max_iter):
    # 1. Context pressure management
    messages, did_trim = trim_loop_messages(messages, context_window)
    if should_wrap_up(messages, context_window):
        messages.append(Message(role="system",
            content="IMPORTANT: Stop making tool calls. Compose final answer now."))

    # 2. LLM call with retry
    llm_resp = await llm_call_with_retry(messages, tools, provider, model)

    # 3. No tool calls = final answer
    if not llm_resp.tool_calls:
        final_text = llm_resp.content
        break

    # 4. Dispatch tool calls
    messages.append(Message(role="assistant", content=llm_resp.content,
                            tool_calls=llm_resp.tool_calls))

    # 5. Parallel execution (except sequential-only tools)
    if len(llm_resp.tool_calls) > 1 and not has_sequential_tool:
        results = await asyncio.gather(
            *(handle_tool(tc, context) for tc in llm_resp.tool_calls),
            return_exceptions=True)
    else:
        results = [await handle_tool(tc, context) for tc in llm_resp.tool_calls]

    # 6. Append tool results
    for tc, (text, sub_result) in zip(llm_resp.tool_calls, results):
        messages.append(Message(role="tool", content=text,
                                tool_call_id=tc.id, name=tc.name))
else:
    # Max iterations reached — compose partial answer from gathered data
    final_text = "I reached maximum analysis steps. Here is what I found..."
```

**Critical details:**
- **Parallel tool dispatch**: Use `asyncio.gather` for independent tools, sequential for stateful ones (e.g. data processing that depends on prior query results)
- **Wrap-up injection**: At ~70% context capacity, inject a system message telling the LLM to stop making tools calls and give a final answer
- **In-loop trimming**: At ~80% capacity, collapse older assistant+tool pairs into one-liner summaries
- **Token limit recovery**: On `LLMTokenLimitError`, compress to 60% and retry once. If still fails, return partial answer
- **Max iterations guard**: Always have a hard limit. On exhaustion, compose best-effort answer from data gathered so far
- **Iteration refund**: a recoverable provider error is not charged to that guard

---

## 3. Meta-Tools (Orchestrator-Level)

The orchestrator's tools **delegate to sub-agents** rather than execute:
`query_database` takes a question in natural language and the SQL agent behind it owns
generation, validation and execution. One parameter, one responsibility, and the caller
never learns the sub-agent exists.

```python
def get_tools(*, has_db=False, has_kb=False, has_mcp=False) -> list[Tool]:
    """Assembled per request from the same capability flags that build the prompt (§10)."""
    tools = []
    if has_db:  tools.extend([QUERY_DB, PROCESS_DATA, MANAGE_RULES, ASK_USER])
    if has_kb:  tools.append(SEARCH_CODEBASE)
    if has_mcp: tools.append(QUERY_MCP)
    return tools
```

Two rules that are this layer's and not the prompt's: **a capability the request does not
have contributes no tool**, and every enum a tool accepts is closed at the schema
(`ask_user`'s `question_type` is `yes_no | multiple_choice | free_text`, never free
prose). How to *describe* a tool so the model picks the right one — the sentence naming
when to use it, and the neighbour it is confused with — is
`agent-harness/references/tools.md`.

---

## 4. Sub-Agent Retry and Validation

Wrap every sub-agent call in retry **and** validation, and keep the two apart: a call that
threw and a call that returned something unusable need different answers. Retry the first,
re-prompt or fail the second.

Three decisions the rest follows from:

- **Split errors into retryable and fatal at the type level**, not at the call site. A bad
  credential and an overloaded provider are both exceptions and only one is worth a second
  attempt.
- **Validate the result before it reaches the user**, against the shape the caller
  expects — rows present, columns named, a citation attached. A confident wrong answer
  passes every check that only looks for an exception.
- **Cap the attempts and return the best partial**, because the alternative to a partial
  answer is not a better answer, it is no answer and a spent budget.

The hierarchy, the loop and the per-domain validators:
[`references/patterns.md`](references/patterns.md).

## 5. Multi-Stage Pipeline (Complex Path)

When one loop is not the shape — several data steps that depend on each other, a person
who has to approve something in the middle, a run that must survive the gap between two
messages — the orchestrator plans first and executes stages instead of tools.

Three decisions belong here; the mechanism is
[`references/pipeline.md`](references/pipeline.md).

- **Detect complexity in two tiers**, cheap first: a keyword heuristic, then one small
  model call only where the heuristic is unsure. Paying a model to classify every question
  is a tax on the common case.
- **Execute in dependency layers, never in list order** (§13). A plan that declares
  `depends_on` and is then walked down the list has serialised itself, and a layer of more
  than one stage gets a checker before anything consumes it.
- **A checkpoint is a pause that frees the worker.** If waiting for a human costs a
  process, long approvals get quietly designed out — which is how a human-in-the-loop
  system stops having one.

## 6. LLM Provider Routing

A router in front of the providers, not a provider client in front of the app:
attempt in order, fall through on failure, and surface one error hierarchy
upward so the caller cannot tell which vendor answered.

Read `references/llm-proxy-billing.md` → **Model routing and fallbacks** for the
fallback chain and per-provider retry with exponential backoff, and its
**Guardrails** section for budgets, loop detection and auto-pause.

**Three traps that cost real money:**

- **A retry loop and a fallback chain multiply.** Three providers with three
  retries each is nine calls for one prompt; cap the total attempts, not the
  per-provider ones.
- **Health checks that only run on failure never recover.** A provider marked
  unhealthy needs a scheduled probe, or the chain permanently runs one provider
  short and nobody sees it — the requests still succeed.
- **Model selection has three levels** — the request, the tenant, the system
  default — and a tenant override that silently loses to a request parameter is
  how a cheap model ends up billed at a premium one's rate.
## 7. Multi-Layer Memory System

Four layers, each with a different lifetime and a different reason to exist:

| Layer | Scope | Lives | Holds |
|---|---|---|---|
| 1 Chat history | per session | minutes | the turns, trimmed to a token budget |
| 2 Working memory | per resource | days | what this task has established so far |
| 3 Long-term learnings | per resource | months | what worked, with a confidence score |
| 4 Insights | per project | permanent | conclusions that outlived their resource |

What enters layers 3 and 4 is decided by `references/patterns.md` — **Confidence
Management**, **Learning Extraction Heuristics**, **Fuzzy Deduplication**, **Conflict
Resolution**.

**These four are lifetimes, and lifetime is not the taxonomy.** Layers 3 and 4 are
*experiential*; **nothing here is a factual store**, and a stale fact about the USER makes
the agent rude while one about the ENVIRONMENT makes it wrong. Retrieval is absent here and
is four decisions, the first of which — whether to retrieve at all — fails as a confident
answer built from nothing, in no error log.

**Design a memory layer from
[`references/memory-architecture.md`](references/memory-architecture.md)**, not from this
table — it also carries the context-budget trap, layer 0 carryover and workspace scale.
The write path is [`references/memory-lifecycle.md`](references/memory-lifecycle.md);
what to build on and measure with is
[`references/memory-landscape.md`](references/memory-landscape.md).
## 8. Self-Learning Feedback Loops

Three cycles feed the memory layers, and they differ by what supplies the signal: a failed
attempt that was then fixed, a user's verdict, and time.

**The rule the whole section exists for:** a learning is written from a **contrast** — the
attempt that failed beside the attempt that worked — never from a single successful run. A
system that learns from its successes learns its own habits.

The extractors, the confidence arithmetic and the promotion query:
[`references/patterns.md`](references/patterns.md).

## 9. Observability

One bus, an event per step, and the answer streamed as chunks on the same bus. Two
properties decide whether it is a feed or a decoration: every event carries a **monotonic
id**, so a reconnecting client resumes rather than missing the run, and the feed is a
**view over a durable trace**, never the record itself — a stream nobody stored is a run
`agent-evals` cannot evaluate. The tracker's shape:
[`references/runtime.md`](references/runtime.md).

## 10. Dynamic System Prompts

**Assemble the prompt from the capabilities that are actually present**, in the same pass
that assembles the tools (§3): one section naming each live capability, the resource map
if there is one, the current learnings, then the guidelines. A prompt that describes a
tool the agent was not given is how a model spends a turn calling something that is not
there.

What belongs in that text, at what altitude, and how to enumerate the vocabulary so the
agent stops inventing status values is the **`agent-harness`** skill's
`agent-harness/references/system-prompt.md` — one home, and it is not this one. What is *this* skill's
is the wiring: the prompt is rebuilt per request from the same capability flags the tool
list is built from, so the two can never disagree.

**Data Verification Protocol** (inject when DB connected):
- First-time metrics: ask user "Do these numbers match expectations?"
- Financial figures: mention units (cents vs dollars), ask for confirmation
- Anomalies: proactively explain and ask user to verify
- Rejected data: investigate discrepancy, record finding as learning

---

## 11. Clarification Requests (ask_user)

Stopping to ask is the same suspend-and-resume as a checkpoint with a different caller —
one contract, not two ([`references/pipeline.md`](references/pipeline.md)).

## 12. Context Engineering

**Compaction is a ladder, not a call.** Clear old tool results, collapse
oversized blocks, condense messages, and only then pay a summarizer —
re-measuring between rungs. Most pressure resolves before the first call.

**Never orphan a `tool_use`.** Every truncation point lands *between* an
assistant+tool pair, or the next request is a 400 in the middle of a task.

**Carry state across the boundary as typed blocks, not prose** — goal,
artifacts, verified work, restrictive mode. A summarizer keeps the discussion
and drops the state, including the flag that said not to write anything.

**Offload a large tool result to a file, keep the path.** Trimming history
cannot save a window one tool output already filled.

**A sub-agent's value is its own window**: it returns a typed summary, not a
transcript.

---

## 13. The Work as a Graph

Before the loop, the pipeline or the sub-agents: **decide the shape.** A node is one unit
of work; an edge is a dependency, and an edge carries data. The full model, the source it
comes from, and what this host actually executes are in
[`references/graph-engineering.md`](references/graph-engineering.md).

Four rules, and these are the ones that change code:

- **Label every edge with what crosses it. No payload, no edge.** Run the fake-edge test
  over any chain you inherited: write the steps as boxes, ask of each arrow whether data
  from A actually enters B, and delete the arrows that only encode the order somebody
  typed. Two or three per workflow is the normal yield.
- **`depends_on` is a claim, so execute by layer.** §5's executor walked `plan.stages` in
  list order beside a model that declared its dependencies — which serialises a plan that
  went to the trouble of saying it need not be. Kahn the graph; a cycle fails the plan
  rather than deadlocking the run.
- **A parallel layer needs a checker before its convergence.** Three branches run, one
  returns a hallucination, and the synthesis node cannot tell: it combines all three and
  answers confidently. The checker decides *usable / not usable* and nothing else, and
  the convergence depends on **the checker**, never directly on a branch.
- **Static unless you can name what forces dynamic.** A graph that picks its own next
  nodes cannot be audited afterwards, because the shape that ran is not the shape anyone
  drew. Where a run has to be explainable, that settles it.

---

## Checklist — Building a New Orchestrator

The sections above are the map. These are the items a reader **cannot** derive from a
heading — the ones that were learned by getting them wrong:

- [ ] In-loop trimming at ~80% of the window, wrap-up injected at ~70%, and a max-iteration
      guard that composes a partial answer rather than returning nothing
- [ ] A recoverable provider error **refunds** its iteration; a misconfiguration must not
      spend the budget that exists to stop a runaway
- [ ] Retries and fallbacks are capped **in total** — three providers × three retries is
      nine calls for one prompt
- [ ] A provider marked unhealthy is probed on a schedule; a health check that only runs on
      failure never recovers, and the chain runs one short with nobody seeing it
- [ ] Chat history has a **floor** — a session that trims it to fit old learnings has chosen
      generalities over what the user said a minute ago
- [ ] Every declared dependency names the data it carries; plans execute in layers, and a
      layer of more than one gets a checker before anything consumes it (§13)
- [ ] That checker has been watched refusing a planted bad input, and its verdicts are
      stored as scores — one that has never rejected anything is a finding
- [ ] Sub-agents return **distilled summaries**, not transcripts; a return value proportional
      to the input is a function call wearing a costume
- [ ] Model, window and price are resolved at one boundary from configuration or the
      provider — never from a table of vendor ids in source
- [ ] An observable before the implementation, an eval before the prompt is tuned, or the
      tuning is folklore — only the corpus waits for production

## References

Each file opens with its own **Load this when** line — the authoritative trigger lives
there, so this table stays an index and the two cannot drift apart.

| File | Read it when |
|---|---|
| [`references/graph-engineering.md`](references/graph-engineering.md) | you are deciding the **shape of the work** — the fake-edge test, the diamond, the checker node, static versus dynamic, and what the host actually runs |
| [`references/pipeline.md`](references/pipeline.md) | one loop is **not the shape** — the planned path, its checkpoints, resume, and the interrupt that asks a person |
| [`references/patterns.md`](references/patterns.md) | you need the **data models and algorithms** under the body |
| [`references/context-engineering.md`](references/context-engineering.md) | the loop is **running out of window** |
| [`references/runtime.md`](references/runtime.md) | the agent must **survive a crash, a pause, a second message or a schedule** |
| [`references/governance.md`](references/governance.md) | the question is **permission, not cost** — what it may do, and how you prove it |
| [`references/llm-proxy-billing.md`](references/llm-proxy-billing.md) | the product **resells LLM access** |
| [`references/provider-lifecycle.md`](references/provider-lifecycle.md) | the question is the **workforce, not the loop** — where providers come from, produced-once/bound-many, knowledge packs, canary trust, workspace lifecycle, fleet budgets |
