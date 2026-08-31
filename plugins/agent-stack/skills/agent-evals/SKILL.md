---
name: agent-evals
description: >-
  Use when measuring whether an agent actually works — building an eval suite, judging a
  trajectory rather than a final answer, turning production traces into regression
  fixtures, calibrating an LLM judge against human labels, or gating a release on offline
  evals. Covers the three observability primitives (run, trace, thread) crossed with three
  eval granularities (single-step, full-turn, multi-turn), the offline/online/ad-hoc
  timing axis, pass-fail rubrics over scalar scores, cheap code checks before model
  judges, the checker node as an evaluator inside the graph, simulated users with adversarial
  personas, annotation queues, and what to instrument for any of it. Triggers - "agent eval", "eval suite", "LLM judge", "regression fixture",
  "trajectory eval", "checker node", "is the agent getting better", "эвалы агента",
  "оценка агента", "LLM-судья", "регрессионный набор", "как проверить агента". Not for
  unit tests of ordinary code, or benchmarking a model.
license: MIT
---

# Agent evals — proving the thing behaves

An agent's behaviour does not exist in its source. The code says what it is *allowed* to
do; only a run says what it *did*. So the artifact under test is the execution record,
and the suite runs on **two clocks**: the *observable* is authored up front, before the
implementation exists, and the *corpus* it runs against is grown from production (§6).

Three claims follow, and they are what makes this different from testing ordinary code:

- **You are testing reasoning, not code paths**, so one granularity is never enough.
- **Every natural-language input is unique**, so the edge cases cannot be enumerated
  offline. Production is not only where you catch what you missed — it is where you
  discover what to test for.
- **Traces become test cases.** The corpus grows from what actually happened; the
  criterion it is measured against does not.

---

## 1. Three primitives

| Primitive | Is | Carries |
|---|---|---|
| **Run** | one model call | the complete prompt — instructions, tools, context — and what came back |
| **Trace** | one full execution | every run, every tool call with arguments and results, nested to show how steps relate |
| **Thread** | many traces in one session | multi-turn context in order, **state evolution** (memory, files, artifacts), and elapsed time |

The thread level is the one most systems lack, and it is where a whole class of defect
lives: a bad memory write at turn 6 surfaces as a wrong answer at turn 11, and neither
the run nor the trace view can localise it.

**Precondition for all of this: traces are durable and queryable.** A live event stream
renders a progress bar and evaporates. If you cannot fetch last week's low-scoring runs
by id, nothing below is available to you — see §7.

---

## 2. Three granularities

Each primitive gets its own kind of assertion.

### Single-step — validates a run

Fixture is a serialized run: prompt, tool schemas, context. Assert the decision at that
point — tool name, argument shape.

> "Schedule a meeting with Harrison tomorrow morning", with `find_meeting_times`,
> `schedule_meeting` and `send_email` available, must call `find_meeting_times` first.

Cheap, deterministic, CI-blocking. **Precondition: a stable agent architecture.** These
break on a graph refactor, and a suite that fails on every refactor gets deleted.

### Full-turn — validates a trace

Assert on three axes at once, with three different mechanisms:

| Axis | Assert | With |
|---|---|---|
| Trajectory | tool-call sequence — `read_file` → `edit_file` → `run_tests` | set/subset/order matchers |
| Final response | quality, tone, policy compliance | rubric or judge |
| **State change** | the memory row exists, the file was written, the artifact is there | direct inspection of the side effect |

The third axis is the one people forget. **Assert on side effects, not only on prose** —
an agent that says it saved the preference and did not is a pass on two axes out of three.

Easiest inputs to generate, hardest outputs to validate automatically.

### Multi-turn — validates a thread

A scripted turn sequence with a **checkpoint after every turn and fail-fast on
deviation**. Without that, turn 3 goes off the rails and turns 4–10 assert nothing while
still reporting a result.

> Turn 1: "I prefer Python over JavaScript." Turn 3's output must still be Python.

Hardest to implement well. Start here only for behaviour that is genuinely about memory
across turns.

**Production suites combine all three.** One vendor reports about half of theirs sitting
at single-step — recorded as their observation, not as a target to hit.

---

## 3. Offline, online, ad-hoc

| When | Reference | Blocks a release? | Answers |
|---|---|---|---|
| **Offline** | a dataset, ground truth optional | **yes** — this is the gate | did my change break what used to work |
| **Online** | none — **definitionally reference-free** | no | is production drifting |
| **Ad-hoc** | none | no | what is actually happening out there |

**Offline is necessary and not sufficient.** A green suite proves you did not regress the
cases you already know about. It cannot prove the agent handles what nobody thought of,
because that input is not in the dataset — which is what the online tier is for.

Online evaluators fire on trace ingestion and check what needs no expected answer:
trajectory anomalies, step-count and latency trends, judge scores, error rates. Route
them over all traces, a sample, or a filtered subset; the sampling rate is a cost
decision, not a correctness one.

Ad-hoc is exploratory analysis over stored traces — clustering to surface failure modes
nobody predefined. A dashboard tracks metrics you chose in advance; this finds the ones
you did not.

---

## 4. Rubrics beat scores

Generic metrics — helpfulness, naturalness, completeness — produce numbers and no
decision. A 3.4 out of 5 on "helpfulness" tells you nothing about what to change.

**Write narrow, behaviour-specific pass/fail rubrics, and write them with the people who
own the behaviour.** Each failure must point at one thing: a prompt, a tool description,
a workflow step, a missing capability.

A rubric that works, in full:

> **Escalation.** On a request for a human: push back once, escalate on the repeat.
> **Fails if** it escalates immediately · refuses after the second request · escalates
> before providing information it already had · continues several turns past the point it
> is clearly not helping.

Note the shape: one behaviour, an explicit pass condition, and an enumerated failure list.
That is what makes a judge reproducible and a disagreement resolvable.

---

## 5. Judges

**Cheap checks first.** Schema validation, exact match, format conformity, business-rule
assertions, tool-call correctness — all deterministic, all faster and cheaper than a model
call. Send to a judge only what cannot be decided by code.

**Judge the trajectory, not just the answer.** Right tools, right order, right arguments.
An agent that reaches a correct answer through three wrong tool calls is a latent outage.

**Calibrate the judge before trusting it.** Collect human labels on the same traces,
measure agreement, iterate the judge prompt until agreement is high — *then* let it score
unattended. An uncalibrated judge is an opinion with a number attached, and shipping on it
is exactly the failure of grading instead of measuring.

**Some things a judge cannot do.** Plausible-but-wrong domain output — an invented legal
citation, a subtly wrong SQL join — reads as correct to a general judge. Route those to a
domain expert and accept that this tier stays human.

---

## 5a. The checker node — an evaluator that runs inside the graph

Everything above evaluates a run *afterwards*. One evaluator runs **during** it, and it is
the one most systems are missing: a **checker node** sitting between a parallel layer and
the node that consumes it. Its only job is *usable / not usable*, and the convergence
depends on **it** rather than on the branches — otherwise the gate has a bypass.

**That split is measured practice, not only this pack's position.** Anthropic's
harness-design guidance (`anthropic.com/engineering/harness-design-long-running-apps`,
read 2026-08-30) reports that *tuning a standalone evaluator to be skeptical is more
tractable than making a generator self-critical* — the same reason the verdict belongs to
a separate node rather than to the branches grading themselves. Dated and cited so a
reader can tell doctrine that converged with the field from doctrine invented here.

It matters here because it is the same machinery as §5, positioned differently:

<!-- checker-contract: missing, empty, unevidenced, malformed, contradictory, off-topic | optional: under-confident -->

| It catches | Decided by |
|---|---|
| a **missing** branch — the arrival count falls short of the fan-out promised | a code check |
| an **empty** or null result | a code check |
| an **unevidenced** claim — nothing attached that a reader could re-check | a code check |
| a **malformed** shape the consuming node cannot parse | a code check |
| **contradictory** siblings, including two that paraphrased one shared assumption | a judge |
| an **off-topic** answer to something nobody asked | a judge |

Four of six are free. Run them first — §5's *cheap checks first*, applied to a position
in the graph rather than to a suite.

**An under-confident branch is a hint, not a row: its own confidence number is optional
and deliberately not one of the six.** §5 above is the reason: a score from an
uncalibrated source is an opinion, so it may order retries and it may not open a gate.
The gate asks for the third row instead — a receipt — which is the same reason this pack
ranks evidence over confidence everywhere else. The contract's home, with the argument in
full, is `agent-orchestrator/references/graph-engineering.md` §6.

**A checker is a node, so it can be wrong, and its failure mode is silent approval.** A
model checker that has never been shown a bad input passes everything, and a graph with a
checker that always says yes is **worse** than one with none: the missing checkpoint has
been replaced by a false one that everything downstream now trusts. Three consequences,
and they are eval work rather than orchestration work:

- **Watch it refuse a planted bad output** before trusting it, exactly as §5 requires of
  any judge before it scores unattended.
- **Record every verdict as a score bound to the run**, with `source: code_check` or
  `llm_judge` (§7). A checker whose verdicts are not stored cannot be asked afterwards how
  often it fired, which means it cannot be calibrated.
- **A checker that has never rejected anything is a finding, not a reassurance.** Put the
  rejection rate on the same dashboard as the pass rate; a rate of zero is either a
  perfect upstream or a broken gate, and only the stored verdicts can tell you which.

Where the checker sits in the shape, and why the convergence needs one at all:
`agent-orchestrator/references/graph-engineering.md`.

## 6. Two clocks — the observable up front, the corpus from production

Two different objects get called *the eval*, and they are written at opposite ends of the
work. Naming them apart is what stops either rule from reading as the other's exception.

<!-- eval-tiers: observable, corpus -->

| Tier | Is | Written | Because |
|---|---|---|---|
| **Observable** | the criterion that would show one requirement was met — a pass/fail rubric (§4), a trajectory or state-change assertion (§2) | **before the implementation exists** | a requirement with no observable is unfinished: attach one afterwards and you are inventing the test having already seen the code, so the output has decided what counts as success |
| **Corpus** | the inputs those criteria run against — fixtures, datasets, minimised production failures | **from production, never up front** | every natural-language input is unique, so the edge cases cannot be enumerated offline; inputs invented in advance test your imagination |

**Neither rule softens the other, because they govern different objects.** An observable is
a *criterion* — what would count as success. A corpus is a *sample* — which inputs you
happen to have. The criterion costs nothing to write early and can only be written honestly
early; the sample written early is green on inputs no user sends. Both therefore hold at
full strength: **a requirement that ships without an observable is unfinished, and a corpus
with no production in it is imagination.** The requirement itself gets its id and its
definition of done from `task-pipeline`'s REQ spine — what this pack owns is the
observable's *form*, not the register it hangs on.

**The first release has no production, so its offline gate is observables only** (§3). That
is not the corpus rule suspended for a special case: the corpus is empty because nothing has
run yet, and it fills from the first real traces. Inventing *inputs* to fill it sooner would
still be imagination.

**Never author the suite up front** — the *corpus*, that is: the inputs. Every production
failure and every thumbs-down becomes a fixture:

1. Capture the state at the failure point.
2. Minimise it to the smallest input that still reproduces.
3. Add it to the tier that isolates it — step, turn or thread.
4. **It stays in the suite permanently.** A fixed bug that silently returns is the defect
   this rule exists to prevent.

Two dataset shapes come out of review:

- **Ground truth** — the reviewer writes the correct output; the suite asserts equality.
- **Criteria-based** — for open-ended work, the reviewer labels dimensions (relevance,
  completeness, tone) instead of an exact answer.

**The annotation queue** is what feeds both: filters route a subset of traces to humans —
low automated score, thumbs-down, a feature area, a cluster. Two reviewer roles, and
mixing them wastes both: generalists judge surface quality, domain experts judge
correctness only they can see.

**Simulated users, if you generate inputs.** A model playing a customer is articulate,
patient and cooperative, and inflates every pass rate. Fine-tune it on real user
transcripts and add adversarial personas — the refund-seeker, the AI-sceptic, the one who
wants a human immediately. Making the simulated user worse makes the offline result
predictive.

---

## 7. What to instrument first

None of the above runs without these, and they are the part people skip:

- **A durable trace store, queryable by id, filterable by score and time.** The live
  stream is a view over it, never the record itself.
- **Scores as first-class records bound to a run**: `run_id`, key, value, and a `source`
  of `human` | `llm_judge` | `code_check`. A score with no source cannot be calibrated,
  audited, or trusted differently from its neighbours.
- **Whole prompts, not just messages** — instructions, tool schemas and context as they
  were sent. A fixture cannot be replayed from a summary.
- **State snapshots at turn boundaries**, so a thread test can assert what carried.

---

## Checklist

- [ ] Traces durable and queryable by id, not only streamed
- [ ] Scores bound to runs, each with a source
- [ ] Single-step fixtures for the decisions that must not drift
- [ ] Full-turn assertions on trajectory **and** final response **and** state change
- [ ] Multi-turn scripts with a checkpoint after every turn, failing fast
- [ ] Offline suite as the release gate; online evaluators reference-free and non-blocking
- [ ] Pass/fail rubrics with enumerated failure conditions, written with behaviour owners
- [ ] Code checks before model judges
- [ ] Judge calibrated against human labels before it is trusted
- [ ] Every checker node watched refusing a planted output, its verdicts stored as scores,
      and its rejection rate on the dashboard — a checker at zero rejections is a finding
- [ ] Domain-expert review for output a general judge cannot grade
- [ ] Every requirement carries an **observable** written before the implementation — the
      corpus waits for production, the criterion does not
- [ ] Every production failure minimised into a permanent fixture
- [ ] Annotation queue with filters, and the two reviewer roles kept separate
- [ ] Simulated users trained on real transcripts, with adversarial personas

---

## Related

Building the agent this measures is the **`agent-orchestrator`** skill, shipped in the
same plugin — named rather than linked, because a packager may ship either directory
alone. Its context-engineering reference covers the context-pressure behaviour that
trajectory assertions most often catch drifting.
