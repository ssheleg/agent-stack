# Agent Orchestrator — Reference Guide

Extended patterns, data models, and implementation details.

## Contents

- [Data Models](#data-models)
- [Pipeline Data Models](#pipeline-data-models)
- [Validation Loop (SQL Execution)](#validation-loop-sql-execution)
- [Context Window Sizes](#context-window-sizes)
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

@dataclass
class StageResult:
    stage_id: str
    status: str = "success"    # success | error | skipped
    query: str | None = None
    query_result: QueryResult | None = None
    answer: str | None = None
    error: str | None = None
```

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

```python
MODEL_CONTEXT_WINDOWS = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "claude-sonnet-4-20250514": 200_000,
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-haiku-20240307": 200_000,
    "claude-3-opus-20240229": 200_000,
}
DEFAULT_CONTEXT_WINDOW = 16_000

# Token estimation: tiktoken for OpenAI models, ~4 chars/token fallback
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
