---
name: agent-orchestrator
description: >-
  Use when building an agent system — an orchestrator, an LLM-powered tool, a chatbot with tool
  use, an AI pipeline — or when metering and billing the LLM access it burns. Covers tool-
  calling loops, multi-stage pipelines with human checkpoints, provider routing with fallback
  and retry, four-layer memory with confidence decay, context budgets, sub-agent coordination
  and error hierarchies; the work as a graph — parallel layers, fake edges, a checker before
  a convergence; for resale: tiered wallets, the single markup boundary, two-phase commit
  across a database and a provider API, spend-delta polling, budget and loop guardrails,
  per-tenant key lifecycle. Triggers - "agent", "orchestrator", "tool calling", "sub-agent",
  "LLM router", "fallback chain", "human in the loop", "memory layer", "LLM billing", "token
  wallet", "checker node", "агент", "оркестратор", "суб-агент", "роутер моделей", "человек в
  цикле", "слой памяти", "биллинг LLM", "граф задач". Not for a single LLM call in a script,
  or for prompt wording.
---

# Agent Orchestrator — Production Best Practices

Battle-tested patterns from a production multi-agent system. Apply these when building any agent
orchestrator, LLM-powered tool system, or agentic workflow.

## Architecture Overview

```
User Question
    ↓
ConversationalAgent (thin wrapper, backward-compat)
    ↓
OrchestratorAgent.run(AgentContext)
    ├─ Complexity check → simple (tool loop) or complex (pipeline)
    ├─ Context loading (parallel: staleness, MCP sources, KB check)
    ├─ History trimming
    ├─ Context budget allocation
    ├─ System prompt construction (dynamic, capability-aware)
    └─ Execution:
        ├─ SIMPLE: iterative LLM tool-calling loop
        │    LLM → tool calls → sub-agent dispatch → results → LLM → ... → final text
        └─ COMPLEX: multi-stage pipeline
             QueryPlanner → ExecutionPlan → StageExecutor → checkpoints → final
```

---

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

Wrap every sub-agent call in retry + validation:

```python
MAX_SUB_AGENT_RETRIES = 2

for attempt in range(MAX_SUB_AGENT_RETRIES + 1):
    try:
        result = await sub_agent.run(context, question=q)
        validation = validator.validate(result)
        if validation.passed or attempt == MAX_SUB_AGENT_RETRIES:
            return format_for_llm(result, validation.warnings), result
        continue  # retry on validation failure
    except AgentRetryableError:
        if attempt < MAX_SUB_AGENT_RETRIES: continue
        return "Failed after retries", None
    except AgentFatalError as e:
        return f"Fatal: {e}", None  # no retry
```

**Error hierarchy:**
```
AgentError (base)
├── AgentRetryableError    → orchestrator retries with adjusted context
├── AgentFatalError        → unrecoverable (bad config, auth failure)
├── AgentTimeoutError      → retry with smaller context
└── AgentValidationError   → sub-agent result failed quality checks
```

**Result validation** (check before returning to user):
- SQL: query present? execution error? zero rows (warn)? slow query >30s (warn)?
- Viz: valid chart type? appropriate for data shape? (pie with 100 slices → bar)
- Knowledge: non-empty answer? source citations present?

---

## 5. Multi-Stage Pipeline (Complex Path)

For complex queries requiring multiple data steps:

### Complexity Detection

Two-tier: fast heuristic + optional LLM check.

```python
COMPLEXITY_KEYWORDS = ["summary table", "pivot", "cross-reference", "compare",
                       "for each", "step 1", "first find", "then"]

def detect_complexity(question, history) -> bool:
    return any(kw in question.lower() for kw in COMPLEXITY_KEYWORDS)

async def detect_complexity_adaptive(question, llm, history) -> bool:
    # Lightweight LLM call: "Is this simple or complex? Reply 'simple' or 'complex'."
    resp = await llm.complete([...], max_tokens=10)
    return "complex" in resp.content.lower()
```

### Pipeline Components

```
QueryPlanner   → (single LLM call) → ExecutionPlan (stages + their depends_on)
StageExecutor  → runs stages in DEPENDENCY LAYERS with validation + retry (§13)
StageValidator → checks data shape, row bounds, cross-stage consistency
StageContext   → in-memory state (plan, results per stage, user feedback)
PipelineRun    → DB-persisted state for resume/retry across requests
```

### Checkpoint Pattern (Human-in-the-Loop)

```python
for layer in plan.layers():                       # Kahn over depends_on — never list order
    results = await run_layer(layer, context)     # execute_with_retries per stage, together

    for i, (stage, result) in enumerate(zip(layer, results)):
        validation = validator.validate(stage, result, stage_ctx)
        if not validation.passed:
            results[i] = await retry_failed_validation(stage, context, validation)
            if results[i] is None:
                return StageFailedResult(stage, validation)   # ask user

    if len(layer) > 1:                            # cheap per-stage checks ran first; this
        verdict = checker.check(results)          # one is the cross-item gate (§13)
        if not verdict.passed:
            return StageFailedResult(layer, verdict)  # nothing converges on a flagged output

    for stage, result in zip(layer, results):
        stage_ctx.set_result(stage.id, result)

    if any(s.checkpoint for s in layer):
        persist_to_db(pipeline_run_id, stage_ctx)
        return CheckpointResult(layer, results)   # pause for user review
        # User responds: "continue" | "modify" | "retry"
```

### Pipeline Resume

```python
async def resume_pipeline(resume_info, context):
    pipeline_run = load_from_db(resume_info["pipeline_run_id"])
    plan = ExecutionPlan.from_json(pipeline_run.plan_json)
    stage_ctx = StageContext.from_persistence(...)

    resume_from = current_idx + 1 if action == "continue" else current_idx
    return await executor.execute(plan, context, resume_from=resume_from, stage_ctx=stage_ctx)
```

---

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

Read `references/patterns.md` for the data models, **Confidence Management**
(how a learning decays and when it is retired), **Learning Extraction
Heuristics**, **Fuzzy Deduplication** and **Conflict Resolution** — the four
mechanisms that decide what actually enters layers 3 and 4.

**The trap is the budget, not the storage.** Every layer competes for the same
context window, so allocation has to be decided per call rather than per layer:
a session that trims chat history to fit a large set of learnings has quietly
chosen old generalities over what the user said sixty seconds ago. Give layer 1
a floor.

**Layer 0 — carryover state.** Goal, artifacts, verified work and restrictive
mode cross a compaction boundary as copied typed blocks, not prose (§12).
## 8. Self-Learning Feedback Loops

Three cycles feed layers 3 and 4, and they differ by what supplies the signal:

| Cycle | Signal | Produces |
|---|---|---|
| **Validation** | the attempt sequence of a call that failed and was then fixed | a learning, extracted by heuristic — the wrong table, a renamed column, a unit divisor, a soft-delete filter, a missing `LIMIT`. Deep LLM analysis only past 3 attempts, on a cooldown |
| **User feedback** | a thumbs-down, or a data verdict of confirmed / approximate / rejected | a benchmark, a session note with the deviation, or a learning plus a flag on the now-stale benchmark |
| **Lifecycle** | time, and contradiction | decay, conflict resolution by negation flip, and promotion of a pattern seen on two independent resources |

The extractors, the exact confidence arithmetic and the promotion query live in
`references/patterns.md` — **Learning Extraction Heuristics**, **Confidence Management**
and **Cross-Resource Learning Transfer** — and not here, because a decay rate is a
constant to tune and a constant with two homes is one that will disagree with itself.

**The rule the whole section exists for:** a learning is written from a **contrast** — the
attempt that failed beside the attempt that worked — never from a single successful run.
A system that learns from its successes learns its own habits.

---

## 9. Observability (SSE Event Streaming)

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

Interrupt the tool loop to ask the user:

```python
async def handle_ask_user(tc, context, wf_id):
    payload = {"question": ..., "question_type": "multiple_choice",
               "options": [...], "context": "why I'm asking"}
    raise _ClarificationRequestError(json.dumps(payload))
    # Caught in orchestrator.run() → returns AgentResponse(response_type="clarification_request")
    # Frontend renders special UI, user responds, next message continues flow
```

---

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

- [ ] Shared `AgentContext` dataclass with all sub-agents
- [ ] `BaseAgent` protocol with typed results + `accum_usage()`
- [ ] Tool-calling loop with max iterations guard
- [ ] In-loop context trimming (80% compress, 70% wrap-up)
- [ ] Parallel tool dispatch where independent, sequential where stateful
- [ ] Sub-agent retry with validation (retryable vs fatal errors)
- [ ] Multi-provider LLM router with fallback chain + health checks
- [ ] Per-provider retry with exponential backoff (respect `retry_after`)
- [ ] Unified LLM error hierarchy with `user_message` property
- [ ] Context budget manager (priority-based allocation)
- [ ] Dynamic system prompt (capability-aware, learning-injected)
- [ ] Chat history trimming (tool condensing, LLM summarization)
- [ ] Working memory (session notes, fuzzy dedup, confidence decay)
- [ ] Long-term learnings (heuristic extraction, conflict resolution, global patterns)
- [ ] Insight memory (lifecycle, trust scoring, decay)
- [ ] Feedback pipeline (thumbs, data validation → learnings/notes/benchmarks)
- [ ] SSE event streaming for real-time progress
- [ ] Complexity detection (heuristic + adaptive LLM)
- [ ] Multi-stage pipeline with checkpoints and resume
- [ ] `ask_user` clarification mechanism
- [ ] Graceful degradation (partial answers on context overflow or max iterations)
- [ ] Compaction ladder, tool-pair-safe boundaries, typed carryover, output offload
- [ ] Every declared dependency names the data it carries — the fake-edge test run once
- [ ] Plans executed in dependency layers, not in the order the stages were listed
- [ ] A checker between every parallel layer and the node that consumes it, and that
      checker watched refusing a planted bad input at least once

---

## References

The checklist above is the map, these are the territory. Each file opens with its
own **Load this when** line — the authoritative trigger lives there, so this table
stays an index and the two cannot drift apart.

| File | Read it when |
|---|---|
| [`references/graph-engineering.md`](references/graph-engineering.md) | you are deciding the **shape of the work** — the fake-edge test, the diamond, the checker node, static versus dynamic, and what the host actually runs |
| [`references/patterns.md`](references/patterns.md) | you need the **data models and algorithms** under the body |
| [`references/context-engineering.md`](references/context-engineering.md) | the loop is **running out of window** |
| [`references/runtime.md`](references/runtime.md) | the agent must **survive a crash, a pause, a second message or a schedule** |
| [`references/governance.md`](references/governance.md) | the question is **permission, not cost** — what it may do, and how you prove it |
| [`references/llm-proxy-billing.md`](references/llm-proxy-billing.md) | the product **resells LLM access** |
