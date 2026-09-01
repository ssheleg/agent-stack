# OpenTelemetry GenAI — the wire format for §7, and what it does not carry

**Load this when instrumenting an agent for someone else to read**: choosing span names and
attributes, deciding what of a prompt reaches a backend, wiring token usage into a bill, or
judging what an "OpenTelemetry-based" tool actually gives you.

§7 says *what* to instrument in four bullets. This is the format that carries it — and the
three places it will not carry what this skill requires.

## Contents

- [Read this before encoding any of it](#read-this-before-encoding-any-of-it)
- [Span names are formulas, and the operation list is closed](#span-names-are-formulas-and-the-operation-list-is-closed)
- [The evaluation event, missing the field §7 requires](#the-evaluation-event-missing-the-field-7-requires)
- [Content: three tiers, and a hook that runs when nothing else does](#content-three-tiers-and-a-hook-that-runs-when-nothing-else-does)
- [Tokens are eleven numbers and money is none of them](#tokens-are-eleven-numbers-and-money-is-none-of-them)
- ["OpenTelemetry-based" is not one vocabulary](#opentelemetry-based-is-not-one-vocabulary)
- [Replay is three different guarantees](#replay-is-three-different-guarantees)

---

## Read this before encoding any of it

**The conventions moved.** They no longer live in the main `semantic-conventions` repository
— that page now says only that they have moved and is no longer maintained. They have their
own repository, whose README lists **Schema URL: `TODO`**.

**Nothing in them is stable.** Every document is marked `Status: Development`. On the
inference span the only attributes marked `Stable` are the ones borrowed from core semconv —
`error.type`, `server.address`, `server.port`, `exception.*`. **Every single `gen_ai.*`
attribute is `Development`.**

So: adopt it, because a moving standard beats a private vocabulary that will never be read
by anyone else's tooling — and **pin the version you adopted and expect to migrate**. Treat
any code that branches on a `gen_ai.*` attribute as code with an expiry date, and re-read
the spec before quoting a field name from this file.

## Span names are formulas, and the operation list is closed

Span names are computed, not free text:

| Span | Name | Kind |
|---|---|---|
| inference | `{gen_ai.operation.name} {gen_ai.request.model}` | `CLIENT` |
| tool call | `execute_tool {gen_ai.tool.name}` | `INTERNAL` |
| agent invocation | `invoke_agent {gen_ai.agent.name}` | `CLIENT` |
| planning | `plan {gen_ai.agent.name}` | `INTERNAL` |
| agent creation | `create_agent {gen_ai.agent.name}` | — |
| MCP | `{mcp.method.name} {target}`, target being the tool or prompt name | — |

`gen_ai.operation.name` is a **closed 17-value enum** — `chat`, `text_completion`,
`generate_content`, `embeddings`, `retrieval`, `fetch_response`, `execute_tool`,
`create_agent`, `invoke_agent`, `plan` and the rest. A value outside it is not an extension,
it is a name a backend cannot group by.

**Only two attributes are Required on an inference span.** Everything else that matters —
the model that actually answered, token counts, finish reasons — is Recommended or
Conditionally Required. A conformant instrumentation can therefore be almost empty, which is
the reason to specify what *you* need rather than to trust conformance as a floor.

One behaviour worth knowing before you count spans: **automatic retries collapse into one
span.** A span is one logical operation, not one HTTP request, so a retry storm is invisible
at this layer and has to be measured somewhere else.

## The evaluation event, missing the field §7 requires

The spec defines `gen_ai.evaluation.result`, parented to the span being evaluated — or
carrying `gen_ai.response.id` when the span id is not available — with:

- `gen_ai.evaluation.name` (**Required**)
- `gen_ai.evaluation.score.value`
- `gen_ai.evaluation.score.label` — low-cardinality: `pass`, `fail`, `relevant`, …
- `gen_ai.evaluation.explanation`

**There is no attribute for who or what produced the score.**

That is precisely the field this skill requires: §7 says a score binds to a run with a
`source` of `human` | `llm_judge` | `code_check`, *because a score with no source cannot be
calibrated, audited, or trusted differently from its neighbours*. The standard omits it.

OpenInference has it, under a different name: **`annotation.annotator_kind`** — `HUMAN`,
`LLM`, `CODE`, or custom — with `evaluation.annotator_kind` beside it. The three values are
our three values.

**So carry it yourself.** Add the attribute under your own namespace and document that it is
an extension; do not drop the requirement because the schema has no slot for it. A judge
score and a human label that are indistinguishable on the wire will be averaged by somebody
downstream, and that average is the thing §5's calibration exists to prevent.

## Content: three tiers, and a hook that runs when nothing else does

Prompt and completion content is governed by three named patterns, chosen by environment:

1. **Record nothing** — the default.
2. **Record on span attributes** — *"best suited for … pre-production environments"*.
3. **Store externally, record a reference on the span** — *"recommended in production
   environments where telemetry volume is a concern or sensitive data needs to be handled
   securely. Using external storage enables separate access controls."*

**The spec's own default is to capture nothing**, and it says instrumentations SHOULD NOT
capture content by default. Verify that in your stack rather than assuming it: the most
widely used `gen_ai.*` implementation ships the opposite. OpenLLMetry's
`is_content_tracing_enabled()` reads

```python
return (os.getenv("TRACELOOP_TRACE_CONTENT") or "true").lower() == "true"
```

— an unset variable is **true**, so prompts are captured unless you turn them off. Measured
2026-08-31 against `traceloop-sdk/traceloop/sdk/config/__init__.py`. An agent's trace carries
prompts, prompts carry secrets, and the default here works against you.

**The upload hook is the last scrubbing point, and it runs where nothing else does.** Two
properties make it the mechanism rather than a convenience: it *"SHOULD operate independently
of the opt-in flags"*, and instrumentations *"SHOULD invoke it regardless of the span sampling
decision"*. It therefore fires on spans nobody will ever look at — which is right, because
the content has already left the process by then, and wrong to reason about as *"we only keep
sampled traces"*.

**A masking hook cannot change the span name.** Span names are built from tool names and MCP
targets, so a redaction design that scrubs attributes and leaves the name is a design that
leaks through the one field it never inspected. Decide naming and redaction together.

## Tokens are eleven numbers and money is none of them

**There is no cost attribute anywhere in the GenAI semantic conventions.** The spec
standardises tokens and never money, so cost is always a join against a price table living
outside the trace — and that join is where the number goes wrong.

Because usage is not one number. It is eleven: `gen_ai.usage.input_tokens`, `output_tokens`,
`reasoning.output_tokens`, `cache_read.input_tokens`, `cache_write.input_tokens`, and
per-modality `text.*` / `image.*` / `audio.*` splits including
`image.cache_read.input_tokens`.

**A cost computed from `input_tokens + output_tokens` alone is wrong in both directions.** It
bills cache reads at full price — they are the cheap ones — and it misses reasoning tokens and
cache writes entirely. `references/kv-cache.md` in `agent-orchestrator` is the other half of
this: the cache read is the case worth getting right, because at scale it is most of the
traffic.

And `gen_ai.client.token.usage` carries a hard **MUST NOT report** when the counts are not
obtainable. A zero is a claim; absence is the honest value. That is the same rule
`agent-harness/references/audit.md` states for cost attribution — *missing attribution beats
wrong attribution, and absence is a named state rather than a fabricated zero*.

## "OpenTelemetry-based" is not one vocabulary

Two widely used tools both describe themselves as OpenTelemetry-based and emit **disjoint**
attribute sets:

| | Emits |
|---|---|
| **Phoenix** | OpenInference — `openinference.span.kind` (required; `LLM`, `CHAIN`, `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`, `EMBEDDING`), plus `llm.*`, `input.value`, `input.mime_type`, `document.*`, `annotation.*` |
| **OpenLLMetry** | `gen_ai.*` plus `traceloop.*` |

**Neither set is a subset of the other, and neither is a superset of the GenAI
conventions.** A backend query written against one returns nothing against the other, and a
trace assembled from two services using each is **two disconnected halves under one trace
id** — which reads as a gap in the system rather than a gap in the vocabulary.

So *"we use OpenTelemetry"* answers a transport question and no semantic one. Ask which
attribute set, and pick one per system rather than per service.

## Replay is three different guarantees

The word appears in three products in this space and means three incompatible things. Our
own `agent-harness/references/audit.md` asks *"can a past run be replayed"* without saying
which:

| Sense | What re-runs | Cost | Answers |
|---|---|---|---|
| **Durable execution** (Temporal) | nothing — recorded results are replayed and only the failed step retries | free, deterministic | can I resume without redoing 20 web searches |
| **Trace playground** (Phoenix) | the model call, against the live provider, with an edited prompt | a real call | would a different prompt have done better |
| **Fixture replay** (this skill, §2 single-step) | an assertion over a stored run | free | did the decision at this point change |

They are not interchangeable, and a runbook that says *"replay the run"* has not said what it
means. Name the sense.
