# The pipeline path — planning, checkpoints, resume, and the human in the middle

**Load this when** one tool-calling loop is not the shape: the question needs several data
steps that depend on each other, a person has to approve something in the middle, or a run
must survive the gap between two of the user's messages.

**Spec pinned:** this pack's own patterns, from a production multi-agent system · read 2026-08-16

`SKILL.md` §2 owns the simple path — one loop, tools, an iteration guard — and §13 owns the
question that comes before both: what shape is this work. This file is the **complex**
path, and it was in the body until 2026-08-16, when the body went 920 tokens over the
budget this pack set itself and the honest fix was to split a layer rather than trim
sentences off every section.

Two things live here because they are one mechanism seen from two sides: a pipeline that
**pauses** at a checkpoint and a loop that **interrupts** to ask a question are the same
suspend-and-resume with different callers. `references/runtime.md` states that contract in
the abstract; this is what it looks like in the orchestrator.

## Contents

- The complex path, end to end
- Clarification requests — interrupting the loop to ask

## The complex path, end to end

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

## Clarification requests — interrupting the loop to ask

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
