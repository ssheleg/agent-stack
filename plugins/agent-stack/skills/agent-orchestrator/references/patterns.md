# Agent Orchestrator — Reference Guide

**Load this when** you need the data models and algorithms under the body: message
and result protocols, pipeline models, the SQL validation loop, context-window sizes
and token estimation, learning-extraction heuristics, the confidence lifecycle, fuzzy
deduplication, conflict resolution, cross-resource transfer, and the suggestion engine
that costs no LLM call.

## Contents

- [Data Models](#data-models)
- [Pipeline Data Models](#pipeline-data-models)
- [Validation Loop (SQL Execution)](#validation-loop-sql-execution)
- [Context Window Sizes](#context-window-sizes)
- [Sub-agent retry, and the error hierarchy under it](#sub-agent-retry-and-the-error-hierarchy-under-it)
- [The three learning cycles, and what each one consumes](#the-three-learning-cycles-and-what-each-one-consumes)
- [Learning Extraction Heuristics](#learning-extraction-heuristics)
- [Confidence Management](#confidence-management)
- [Fuzzy Deduplication Pattern](#fuzzy-deduplication-pattern)
- [Conflict Resolution Pattern](#conflict-resolution-pattern)
- [Cross-Resource Learning Transfer](#cross-resource-learning-transfer)
- [Suggestion Engine (No LLM Cost)](#suggestion-engine-no-llm-cost)


## Data Models

### Message Protocol

```python
@dataclass
class Message:
    role: str          # system | user | assistant | tool
    content: str
    tool_call_id: str | None = None   # for role="tool" responses
    name: str | None = None           # tool name
    tool_calls: list[ToolCall] | None = None  # for role="assistant" with tools

@dataclass
class ToolCall:
    id: str                    # unique ID per call
    name: str                  # tool function name
    arguments: dict[str, Any]  # parsed JSON arguments

@dataclass
class Tool:
    name: str
    description: str
    parameters: list[ToolParameter]

@dataclass
class ToolParameter:
    name: str
    type: str          # "string", "number", "boolean"
    description: str
    required: bool = True
    enum: list[str] | None = None

@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    provider: str = ""
    finish_reason: str = ""
```

### Agent Result Protocol

```python
@dataclass
class AgentResult:
    status: str = "success"    # success | error | no_result
    token_usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

# Typed subclass example:
@dataclass
class SQLAgentResult(AgentResult):
    query: str | None = None
    query_explanation: str | None = None
    results: QueryResult | None = None
    attempts: list[QueryAttempt] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)
```

### Orchestrator Response

```python
@dataclass
class AgentResponse:
    answer: str = ""
    query: str | None = None
    query_explanation: str | None = None
    results: QueryResult | None = None
    viz_type: str = "text"
    viz_config: dict = field(default_factory=dict)
    knowledge_sources: list[RAGSource] = field(default_factory=list)
    error: str | None = None
    workflow_id: str | None = None
    token_usage: dict = field(default_factory=dict)
    llm_provider: str = ""
    llm_model: str = ""
    response_type: str = "text"       # text|sql_result|knowledge|error
                                      # |clarification_request|stage_checkpoint
                                      # |stage_failed|pipeline_complete
    tool_call_log: list[dict] = field(default_factory=list)
    suggested_followups: list[str] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)
    context_usage_pct: int = 0
    staleness_warning: str | None = None
```

---

## Pipeline Data Models

```python
@dataclass
class PlanStage:
    stage_id: str              # unique ID
    description: str           # human-readable
    tool: str                  # "query_database" | "search_codebase" | "analyze_results"
    question: str              # sub-question for the stage
    depends_on: list[str]      # stage IDs this depends on
    checkpoint: bool = False   # pause for user review after this stage
    validation: StageValidation | None = None

@dataclass
class StageValidation:
    min_rows: int | None = None
    max_rows: int | None = None
    required_columns: list[str] = field(default_factory=list)

@dataclass
class ExecutionPlan:
    question: str
    stages: list[PlanStage]
    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, raw: str) -> ExecutionPlan: ...

    def layers(self) -> list[list[PlanStage]]:
        """Kahn's algorithm over `depends_on`. Each returned list may run concurrently."""
        ...

@dataclass
class StageResult:
    stage_id: str
    status: str = "success"    # success | error | skipped
    query: str | None = None
    query_result: QueryResult | None = None
    answer: str | None = None
    error: str | None = None
```

**`depends_on` is a claim the executor has to honour.** A plan that declares dependencies
and is then executed in list order has serialised itself: `stages[3]` waits for
`stages[2]` whether or not it consumes anything it produced. Execute by **layer** —
everything whose dependencies are satisfied goes together — and the declaration starts
paying for itself. Two rules come with it: a cycle is a plan defect and fails the plan
rather than deadlocking the run, and a layer of more than one stage needs the convergence
check in `graph-engineering.md` §6 before anything downstream consumes it.

---

## Validation Loop (SQL Execution)

The full SQL execution cycle with pre/post validation and repair:

```
for attempt in range(1, max_retries + 1):
    1. PRE-VALIDATE
       └─ Schema check: tables exist? columns exist? types compatible?
       └─ If fails → repair query via LLM → continue

    2. SAFETY CHECK
       └─ Read-only enforcement, DML blocking
       └─ If unsafe → fail immediately (no retry)

    3. EXPLAIN DRY-RUN (optional)
       └─ Run EXPLAIN, check for full table scans on huge tables
       └─ If problematic → repair query → continue

    4. EXECUTE
       └─ Run query against user's database
       └─ Classify errors: table_not_found, column_not_found, syntax_error,
          timeout, permission_denied, connection_error
       └─ If retryable error → enrich context + repair → continue
       └─ If fatal → fail

    5. POST-VALIDATE
       └─ Sanity checks on results
       └─ If fails → repair → continue

    6. SUCCESS → extract learnings from attempt history
```

---

## Context Window Sizes

**Do not ship a table of model ids.** This file carried one until 2026-08-15 — nine
vendor ids with their windows, and a `DEFAULT_CONTEXT_WINDOW` of 16 000. Every number in
it was correct when written and none of it survived a year: generations shipped, ids were
renamed, long-context variants appeared under the same family name, and a system reading
that table would have sized its budget for a window an order of magnitude smaller than
the one it was actually given. A lookup table of somebody else's identifiers is a cache
with no invalidation.

**Resolve the window at one boundary instead**, in this order, and let every caller ask
that boundary rather than a constant:

1. **Configuration** — an explicit per-model entry the operator set. It outranks
   everything, because it is the only source that can encode a limit you have chosen (a
   budget cap below the real window, a provider tier).
2. **The provider** — the model list or metadata endpoint most APIs expose. Fetched once
   per process, cached with a TTL, refreshed on a miss.
3. **A conservative floor** for a model nothing knows about, plus a **loud log line**
   naming the model. A silent default is how a new model runs at a fraction of its
   window for months with nobody noticing.

The floor is a number to be small about, not accurate about: being early to compact costs
one avoidable rung of the ladder, and being late costs the request.

```python
# Token estimation: a real tokenizer where one is available, ~4 chars/token otherwise.
# The fallback runs LOW on code, JSON and non-Latin text — see context-engineering.md
# → Estimating what you have left, and apply the padding factor described there.
def estimate_tokens(text):
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return max(1, len(text) // 4)
```

---

## Learning Extraction Heuristics

```python
class LearningAnalyzer:
    def _detect_table_preference(attempts, question):
        # For consecutive attempt pairs where attempt[i] failed and attempt[i+1] succeeded:
        # Compare tables used. If old_tables - new_tables and new_tables - old_tables:
        # → "Use `new_table` instead of `old_table` for {topic}"

    def _detect_column_correction(attempts):
        # If attempt[i] has column_not_found error with column name X
        # and attempt[i+1] no longer uses X:
        # → "Column `X` doesn't exist on `table`. Use `Y` instead."

    def _detect_format_discovery(attempts):
        # If fixed query adds "/ 100" or "/ 1000" that wasn't in failed query:
        # → "Column `amount` stores cents. Divide by 100."

    def _detect_schema_gotcha(attempts):
        # If fixed query adds "deleted_at IS NULL" or schema prefix:
        # → "Table uses soft-delete. Always filter active records."

    def _detect_performance_hint(attempts):
        # If timeout error fixed by adding LIMIT or date filter:
        # → "Table can timeout. Always add LIMIT and date filter."
```

---

## Confidence Management

```
LEARNING CONFIDENCE:
  Initial:     0.6
  Confirmed:   +0.1 (cap 1.0)
  Applied:     tracked (times_applied counter)
  Contradicted: -0.3
  Stale (30d): -0.02/month
  Deactivated: below 0.2

SESSION NOTE CONFIDENCE:
  Initial:     0.7
  Confirmed:   +0.1 (cap 1.0)
  Verified:    +0.15 (exempt from decay)
  Stale (60d): -0.1 per cycle
  Floor:       0.1

INSIGHT CONFIDENCE:
  Initial:     0.5
  Resurfaced:  +0.05
  Confirmed:   +0.15
  Dismissed:   -0.2
  Stale (30d): -0.05 per cycle
  Expired:     below 0.15
```

---

## Fuzzy Deduplication Pattern

Used across all memory layers:

```python
from difflib import SequenceMatcher

THRESHOLD = 0.75  # learnings/notes; 0.80 for insights

async def find_similar(session, connection_id, category, subject, text):
    candidates = await load_existing(session, connection_id, category, subject)
    text_lower = text.strip().lower()
    best_match, best_ratio = None, 0.0
    for c in candidates:
        ratio = SequenceMatcher(None, c.text.strip().lower(), text_lower).ratio()
        if ratio >= THRESHOLD and ratio > best_ratio:
            best_match, best_ratio = c, ratio
    return best_match

# On match: bump confidence +0.1, keep longer text, set is_active=True
# On no match: create new entry
```

---

## Conflict Resolution Pattern

Detect when new learning contradicts existing ones:

```python
CONFLICT_INDICATORS = {"use", "prefer", "always", "never", "should",
                       "instead", "not", "avoid", "correct", "wrong"}

def resolve_conflicts(existing_learnings, new_lesson, new_confidence):
    new_keywords = {w for w in new_lesson.lower().split() if w in CONFLICT_INDICATORS}
    for old in existing_learnings:
        old_keywords = {w for w in old.lesson.lower().split() if w in CONFLICT_INDICATORS}
        shared = new_keywords & old_keywords
        if not shared: continue

        has_negation_flip = (
            ("not" in new_keywords) != ("not" in old_keywords) or
            ("never" in new_keywords) != ("never" in old_keywords) or
            ("avoid" in new_keywords) != ("avoid" in old_keywords))

        if has_negation_flip and old.confidence <= new_confidence:
            old.is_active = False  # superseded
```

---

## Cross-Resource Learning Transfer

```python
async def get_cross_connection_learnings(session, connection_id, exclude_hashes):
    project_id = get_project_for_connection(connection_id)
    sibling_ids = get_sibling_connections(project_id, exclude=connection_id)
    # Only transfer schema_gotcha and performance_hint (universally applicable)
    transferable = await load_learnings(sibling_ids, categories={"schema_gotcha", "performance_hint"},
                                        min_confidence=0.6)
    return [f"- [from sibling] {l.lesson} [{int(l.confidence*100)}%]"
            for l in transferable if l.lesson_hash not in exclude_hashes][:8]

async def promote_global_patterns(session, connection_id):
    # Find learnings appearing on 2+ independent connections
    patterns = await query(
        SELECT lesson_hash, MAX(lesson), MAX(confidence), COUNT(DISTINCT connection_id)
        WHERE is_active AND confidence >= 0.7
        GROUP BY lesson_hash HAVING COUNT(DISTINCT connection_id) >= 2)
    # Exclude already-known patterns, format as prompt lines
    return [f"- [global, seen on {p.conn_count} DBs] {p.lesson}" for p in patterns][:5]
```

---

## Suggestion Engine (No LLM Cost)

Template-based follow-up suggestions:

```python
FOLLOWUP_TEMPLATES = [
    "Show this as a pie chart",
    "Break this down by month",
    "Compare with the previous period",
    "Show only the top 5 results",
    "What is the trend over time?",
]

def generate_followups(query, columns, row_count) -> list[str]:
    pool = list(FOLLOWUP_TEMPLATES)
    if has_aggregate_keywords(query):
        pool.extend(["Show percentage breakdown", "Average instead of count?"])
    if row_count > 1 and len(columns) >= 2:
        pool.append(f"Sort by {columns[-1]} descending")
    random.shuffle(pool)
    return pool[:3]
```

## Sub-agent retry, and the error hierarchy under it

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


## The three learning cycles, and what each one consumes

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


---


Both moved out of `SKILL.md` on 2026-08-16. The mechanisms they describe were already
in this file — the validation loop, the extractors, the confidence arithmetic — so the
body was holding a second copy of their surface. One home; the body keeps the decision.
