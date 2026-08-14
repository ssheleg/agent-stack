# The technique catalogue, with a verdict on each

**Load this when:** choosing between ReAct, reflection, voting, planning and the rest — or
being asked why the system does not use one that appeared in a paper.

**Spec pinned:** `promptingguide.ai` techniques/* and guides/*; Anthropic agent guidance · read 2026-08-14

**How to read the verdicts.** Every technique here works somewhere; the column says whether
it earns its cost *in a production agent loop*, which is a narrower question than whether it
raised a benchmark. Costs are real: each of these multiplies calls, latency or context, and
several of them were measured on single-turn QA rather than a long-running agent.

## Contents

- The catalogue
- ReAct, in detail
- Reflection, in detail
- Voting and self-consistency
- What reasoning models made redundant
- Choosing one

## The catalogue

| Technique | What it is | Verdict for a production agent loop |
|---|---|---|
| **Zero-shot** | instruction alone | **Default.** Start here; everything below is a cost you must justify |
| **Few-shot** | input→output exemplars | **Yes, for format.** Curate a few diverse canonical examples. It teaches shape far better than it teaches judgement, and an exhaustive list makes the model brittle |
| **Chain-of-thought** | "think step by step" | **Legacy on reasoning models — actively harmful there** (it can degrade instruction-following). Still useful on non-reasoning models for arithmetic and multi-constraint tasks |
| **ReAct** | interleaved thought → action → observation | **Yes — this is the agent loop.** Most harnesses implement it without naming it. See below for what it does not fix |
| **Reflexion / self-critique** | actor, evaluator, self-reflection, with episodic memory | **Selectively.** Real gains where a *cheap objective signal* exists — tests pass, query runs, schema validates. Without one, the model grades its own homework |
| **Self-consistency** | sample N, take the majority | **Rarely.** N× cost and latency for a single answer; needs a well-defined answer to vote on. Use for a high-stakes classification, not for a whole trajectory |
| **Tree of Thoughts** | explore and prune a branching search | **Almost never in production.** Combinatorial cost, and the pruning heuristic is usually the hard part you have not solved. A planner plus a bounded retry gets most of the value |
| **ART** (automatic reasoning + tool use) | select exemplars and tools from a task library automatically | **Watch.** The idea — a library of trajectories rather than a hand-written prompt — is where prompt maintenance is heading; the tooling is not settled |
| **Prompt chaining** | fixed sequence with checks between | **Yes — and prefer it over an agent** wherever the steps are knowable |
| **Meta prompting** | prompt about the structure of the task, not its content | **Occasionally.** Useful for generating scaffolds; not a loop technique |
| **Generate-knowledge** | elicit facts first, then answer | **No.** Retrieval solves the same problem with grounding; this invents plausible knowledge |
| **RAG** | retrieve, then generate | **Yes, and it is a search problem.** Its quality lives outside this skill; what belongs here is *just-in-time* retrieval — see below |
| **Just-in-time retrieval** | hold lightweight identifiers (paths, queries, links); load at runtime via tools | **Yes.** The scalable default: it mirrors how people work, and keeps the window for reasoning rather than for data |
| **Structured note-taking** | write notes to durable memory outside the window, read them back | **Yes for long tasks.** Persistent memory at low overhead, and it survives compaction — which a summary of the discussion does not |
| **Sub-agents** | specialists returning distilled summaries | **Yes where the sub-task has its own context need.** The value is the *isolated window*; a sub-agent returns a 1–2k-token distilled summary, never a transcript |

## ReAct, in detail

**Thought → Action → Observation**, repeated. Reasoning traces and task actions generated in
an interleaved way, so the plan updates on what the world actually returned.

What it fixes: plain chain-of-thought is isolated from external information and therefore
suffers **fact hallucination and error propagation** — it reasons confidently past a wrong
premise. ReAct grounds each step in an observation.

**What it does not fix, and this is under-quoted:**

- It **constrains reasoning flexibility** compared with free-form CoT — the format itself is
  a cost.
- **Non-informative results derail it.** A search returning nothing useful leaves the model
  struggling to reformulate, and it will loop on near-identical queries. This is the failure
  your iteration guard exists for, and it is why tool errors must teach (`tools.md`).
- It is strongest **combined** with CoT and self-consistency rather than alone — which is
  the honest reading of the paper and rarely the reading in a blog post.

## Reflection, in detail

Three roles, and naming them separates the ones people conflate:

| Role | Does | In practice |
|---|---|---|
| **Actor** | generates text and actions, produces a trajectory | your existing loop |
| **Evaluator** | scores the trajectory | **the part that decides whether this works at all** |
| **Self-reflection** | turns the score into verbal guidance stored for next time | an extra call, plus memory |

**The evaluator is the whole question.** Where the signal is objective and cheap — the test
suite ran, the SQL executed, the JSON validated, the build passed — reflection is one of the
strongest available techniques. Where the evaluator is the same model judging its own
output with no ground truth, you have added cost and a confident second opinion.

Stated limitations worth carrying: it depends on **accurate self-evaluation**, its memory is
typically a **sliding window**, and it struggles where correctness is non-deterministic.

## Voting and self-consistency

Sample the same task several times and take the majority. It genuinely reduces variance —
and it multiplies cost and latency by N, needs a discrete answer to vote on, and does
nothing for a long trajectory where the runs diverge at step three.

Reach for it on a **single high-stakes decision** — a routing classification, a safety
judgement, an extraction that everything downstream depends on. Not on a whole agent run.

## What reasoning models made redundant

A live shift, and it invalidates a lot of otherwise-good advice:

- **Do not instruct step-by-step thinking.** It is native, and explicit CoT can hurt
  instruction-following.
- **Give high-level goals rather than procedures**, and let planning happen inside the model.
- **Reasoning effort** is now a per-call dial, which is a cheaper knob than most of the
  techniques above.
- But **tool-calling stays weaker** in most reasoning models — so the common production shape
  is a reasoning model that plans and a different model that executes tools. That is
  *separation of concerns*, and it also lets the cheap half be cheap.

## Choosing one

Ask in this order, and stop at the first yes:

1. **Are the steps knowable?** → prompt chaining, not an agent.
2. **Is there a cheap objective signal?** → evaluator–optimizer or reflection.
3. **Does the sub-task need its own window?** → a sub-agent returning a distilled summary.
4. **Is one decision disproportionately expensive to get wrong?** → voting, on that decision only.
5. **Otherwise** → a plain ReAct loop with a bounded iteration guard, and spend the effort on
   the tools and the prompt instead. That is where the measured gains are.

**The anti-pattern this section exists to prevent:** adopting a technique because it appears
in a paper, without naming the signal it consumes or the cost it adds. If you cannot say
what the evaluator measures, you are not doing reflection — you are paying for a second
opinion from the same source.
