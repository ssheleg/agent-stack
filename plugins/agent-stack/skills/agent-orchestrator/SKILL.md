---
name: agent-orchestrator
description: >-
  Use when building an agent system — an orchestrator, an LLM-powered tool, a chatbot with tool
  use, an AI pipeline — or when metering and billing the LLM access it burns. Covers tool-
  calling loops, multi-stage pipelines with human checkpoints, provider routing with fallback
  and retry, four-layer memory with confidence decay, context budgets, sub-agent coordination
  and error hierarchies; for resale: tiered wallets, the single markup boundary, two-phase
  commit across a database and a provider API, spend-delta polling, budget and loop guardrails,
  per-tenant key lifecycle. Triggers - "agent", "orchestrator", "tool calling", "sub-agent",
  "LLM router", "fallback chain", "human in the loop", "memory layer", "LLM billing", "token
  wallet", "агент", "оркестратор", "суб-агент", "роутер моделей", "человек в цикле", "слой
  памяти", "биллинг LLM", "лимит бюджета". Not for a single LLM call in a script, or for prompt
  wording.
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
    model: str | None               # e.g. "openai/gpt-4o"
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

---

## 3. Meta-Tools (Orchestrator-Level)

Define tools that **delegate to sub-agents**, not execute directly:

```python
QUERY_DATABASE_TOOL = Tool(
    name="query_database",
    description="Query the connected database. Handles SQL generation, validation, execution.",
    parameters=[ToolParameter(name="question", type="string", description="Data question")]
)
ASK_USER_TOOL = Tool(
    name="ask_user",
    description="Ask the user a structured clarification question.",
    parameters=[
        ToolParameter(name="question", type="string", ...),
        ToolParameter(name="question_type", type="string",
                      enum=["yes_no", "multiple_choice", "free_text"]),
        ToolParameter(name="options", type="string", required=False),
    ]
)
```

**Assemble tools dynamically** based on available capabilities:

```python
def get_tools(*, has_db=False, has_kb=False, has_mcp=False) -> list[Tool]:
    tools = []
    if has_db:
        tools.extend([QUERY_DB, PROCESS_DATA, MANAGE_RULES, ASK_USER])
    if has_kb:
        tools.append(SEARCH_CODEBASE)
    if has_mcp:
        tools.append(QUERY_MCP)
    return tools
```

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
QueryPlanner   → (single LLM call) → ExecutionPlan (ordered stages)
StageExecutor  → runs stages sequentially with validation + retry
StageValidator → checks data shape, row bounds, cross-stage consistency
StageContext   → in-memory state (plan, results per stage, user feedback)
PipelineRun    → DB-persisted state for resume/retry across requests
```

### Checkpoint Pattern (Human-in-the-Loop)

```python
for idx, stage in enumerate(plan.stages):
    result = await execute_with_retries(stage, context)
    validation = validator.validate(stage, result, stage_ctx)

    if not validation.passed:
        retried = await retry_failed_validation(stage, context, validation)
        if retried is None:
            return StageFailedResult(stage, validation)  # ask user
        result = retried

    stage_ctx.set_result(stage.id, result)

    if stage.checkpoint:
        persist_to_db(pipeline_run_id, stage_ctx)
        return CheckpointResult(stage, result)  # pause for user review
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
## 8. Self-Learning Feedback Loops

### Cycle 1: Automatic (Validation Loop)

After every SQL execution cycle, heuristic extractors analyze the attempt sequence:

| Extractor | Detects | Creates |
|-----------|---------|---------|
| Table preference | Wrong table A fixed to B | "Use `B` instead of `A`" |
| Column correction | column_not_found → suggested col | "Use `full_name` not `user_name`" |
| Format discovery | Division by 100/1000 added | "Amounts in cents, divide by 100" |
| Schema gotcha | `deleted_at IS NULL` added | "Soft-delete: filter active records" |
| Performance hint | Timeout fixed by LIMIT/date filter | "Always add LIMIT to this table" |

LLM-based deep analysis (3+ attempts, 1hr cooldown) for cross-query patterns.

### Cycle 2: User Feedback

```python
# Thumbs down → analyze_negative_feedback() → learning
# Data validation:
#   confirmed  → store benchmark
#   approximate → benchmark + session note (deviation details)
#   rejected   → learning + note + flag stale benchmark
#     Categorize rejection: currency/format → data_format, filter → schema_gotcha,
#                           table → table_preference, join → schema_gotcha
```

### Cycle 3: Knowledge Lifecycle

- **Decay**: stale learnings -0.02/month, notes -0.1/60 days, insights -0.05/30 days
- **Conflict resolution**: negation flips deactivate old conflicting lessons
- **Global promotion**: patterns on 2+ resources promoted project-wide

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

Stream final answer text in chunks for typing effect:

```python
async def stream_tokens(wf_id, text, chunk_size=12):
    for i in range(0, len(text), chunk_size):
        await tracker.emit(wf_id, "token", "streaming", text[i:i+chunk_size])
```

---

## 10. Dynamic System Prompts

Build system prompts dynamically based on available capabilities:

```python
def build_system_prompt(*, project_name, db_type, has_connection, has_kb, table_map,
                        project_overview, recent_learnings):
    sections = [f"You are an AI data assistant for '{project_name}'."]
    sections.append("AVAILABLE CAPABILITIES:")
    if has_connection:
        sections.append("- query_database: ... SQL agent handles everything")
        sections.append("- process_data: ... enrich/aggregate/filter")
        sections.append("- manage_rules: ... CRUD project rules")
    if has_kb:
        sections.append("- search_codebase: ... RAG over indexed code")

    if table_map:
        sections.append(f"DATABASE TABLES: {table_map}")
    if recent_learnings:
        sections.append(recent_learnings)  # "AGENT LEARNINGS: ..."
    sections.append("GUIDELINES: ...")  # routing rules, verification protocol
    return "\n".join(sections)
```

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

---

## References

Load these when the task reaches them — the checklist above is the map, these
are the territory.

| File | Read it when |
|---|---|
| [`references/patterns.md`](references/patterns.md) | you need the **data models and algorithms**: message and result protocols, pipeline models, the SQL validation loop, context-window sizes and token estimation, learning-extraction heuristics, confidence lifecycle, fuzzy dedup, conflict resolution, cross-resource transfer, the no-LLM suggestion engine |
| [`references/llm-proxy-billing.md`](references/llm-proxy-billing.md) | the product **resells LLM access**: tiered wallets and where markup applies, two-phase commit against a provider API with compensating transactions, advisory locking, optimistic concurrency for reclaims, spend-delta polling and its three cases, budget/loop/auto-pause guardrails, per-tenant key lifecycle and healing, the refund waterfall, model routing |
