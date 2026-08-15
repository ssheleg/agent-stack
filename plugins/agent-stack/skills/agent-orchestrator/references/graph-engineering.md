# Graph engineering — deciding the shape of the work before doing it

**Load this when** a job has more than two steps and you are about to write them in a
line: choosing between a chain and a graph, finding the dependencies that are not real,
placing a check between a parallel layer and the node that consumes it, or deciding
whether the structure may be discovered while it runs.

**Spec pinned:** *Graph Engineering with Claude*, `https://x.com/Mahaximus_/status/2082442856417956173`
(published 2026-07-29); Claude Code `CHANGELOG.md` v2.1.154 – v2.1.229 · read 2026-08-15

`SKILL.md` §2 owns the tool-calling loop and §5 the multi-stage pipeline. Both assume
the shape is already decided. **This file is how it gets decided**, and it is upstream of
every constant in the rest of the pack: a threshold tuned inside the wrong shape is a
well-measured answer to the wrong question.

## Contents

- [The source, and what this file adds](#the-source-and-what-this-file-adds)
- [1. Node and edge](#1-node-and-edge)
- [2. Your loop is already a graph, and most of its edges are fake](#2-your-loop-is-already-a-graph-and-most-of-its-edges-are-fake)
- [3. The fake-edge test](#3-the-fake-edge-test)
- [4. The diamond](#4-the-diamond)
- [5. Two ways a diamond fails silently](#5-two-ways-a-diamond-fails-silently)
- [6. The checker node](#6-the-checker-node)
- [7. Static or dynamic](#7-static-or-dynamic)
- [8. When not to build a graph at all](#8-when-not-to-build-a-graph-at-all)
- [9. What Claude Code actually executes](#9-what-claude-code-actually-executes)
- [10. Barrier or no barrier](#10-barrier-or-no-barrier)
- [11. Project defaults, written once](#11-project-defaults-written-once)
- [12. The source's four diagrams, and what each one is for](#12-the-sources-four-diagrams-and-what-each-one-is-for)
- [Where this file disagrees with its source](#where-this-file-disagrees-with-its-source)

## The source, and what this file adds

The model below — node, edge, the fake-edge test, the diamond, the checker node, static
versus dynamic — is taken from the article pinned above. It is the clearest short
statement of the idea available, and the link is kept so the original can be re-read
rather than remembered through this summary.

Four things are **this pack's**, not the source's, and each is marked where it appears:

| Added here | Why the source could not carry it |
|---|---|
| §9 — what the host actually runs, with version evidence | the article's one operational claim aged out six weeks after publication (see §9) |
| §10 — the barrier distinction | the article's diamond has a barrier at every convergence; most convergences do not need one |
| §6 — what a checker costs, and when it is a rubber stamp | a check nobody measures is a node that always says yes |
| §7 — the auditability rule as a **hard** rule, not a preference | this pack's own doctrine is that a green nobody watched fail is not evidence |

## 1. Node and edge

**A node is one unit of work.** One input, one output, one job. Not *"research the topic,
summarise it, and check the sources"* — that is three nodes wearing one name. The
smaller and more defined the job, the more useful the node, because a node is also the
unit you retry, cache, review and replace.

**An edge is a dependency, and it carries data.** It exists when the second node
genuinely consumes what the first produced. Not when the second merely *happens after*
the first.

That distinction is the whole discipline. Write it on the edge and it stops being
abstract: `research --findings--> write --draft--> verify`. **An edge you cannot label
with what crosses it is not an edge.**

## 2. Your loop is already a graph, and most of its edges are fake

A prompt that says *"research this, then summarise, then draft"* is a graph — a single
unbranching chain in which every step waits for its predecessor. It is correct. It is
also the slowest possible arrangement of that work and the most brittle: one bad step
takes the whole chain, and nothing runs while any step is running.

The first move is therefore not to learn a new structure. It is to look at the one you
already have and ask which of its waits are real.

## 3. The fake-edge test

Five minutes, no tooling, and it is the highest-yield thing in this file.

1. Write every step as a box.
2. Draw an arrow between each pair of consecutive steps.
3. For each arrow ask: **does data from A actually enter B?** — not *"does B come after
   A"*.
4. Yes → keep it, and **write the payload on the arrow**.
5. No → delete it. That wait was free to give away and you were paying for it.
6. Everything with no incoming arrow starts immediately.
7. Everything with no outgoing arrow is a final output.

The tell that the test is being done honestly is step 4: if the payload cell is empty,
the edge is fake, and the person drawing it now has to say so out loud rather than
leaving the arrow in place because it looked orderly.

**Expect two or three fake edges in any workflow you have not run this against.** The
classic is *"review file A, then review file B"*: it reads as a sequence, and the review
of B never once looks at what A returned.

## 4. The diamond

One node fans out into several independent nodes; those all feed one node that combines
them. Drawn out, it is a diamond, and it is the shape that makes graphs worth the setup.

```
                 ┌──────────┐
                 │  SPLIT   │
                 └────┬─────┘
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼          ← parallel layer
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ source1 │   │ source2 │   │ source3 │
   └────┬────┘   └────┬────┘   └────┬────┘
        └─────────────┼─────────────┘
                      ▼
                 ┌──────────┐
                 │SYNTHESIZE│                  ← convergence
                 └──────────┘
```

The convergence waits for the slowest branch, not for the sum of all of them.

**Two rules, and both have to hold:**

1. **The parallel nodes are genuinely independent** — no fake edge dressed as a real one,
   and no shared mutable state. Two "independent" workers writing one file are one node
   with a race in it.
2. **The convergence genuinely needs all of them.** If it needs only the first to answer,
   the rest are paid-for waste and you wanted a race, not a diamond.

Once you look for it, the shape is everywhere there is a *gather-then-combine*: research,
multi-file review, market analysis, a fan of checks over one artifact.

## 5. Two ways a diamond fails silently

Both are failures **of the convergence**, which is why sequential chains do not have
them.

**A bad node goes undetected.** Three branches run, one returns a hallucination, an empty
result or a misread file, and that output arrives at the synthesis node beside two good
ones. The synthesis node does not know one of its inputs is wrong. It produces a
confident answer built partly on garbage. Parallelism bought the speed by deleting the
checkpoints where a human would have noticed.

**The error cascades and dilutes.** In a chain, a bad step produces a visibly bad output.
At a convergence, the bad output is *mixed* with good ones, so the damage is spread thin
and the trace back to its source is gone. By the time anything looks wrong, three nodes
have averaged it into plausibility.

Both are the same defect: **the convergence trusts its inputs because they arrived.**

## 6. The checker node

A node between the parallel layer and the convergence whose only job is to decide whether
each output may proceed. It synthesises nothing and writes nothing. It answers *is this
usable* and then passes, flags, retries or drops.

Five things it must catch — the list is the contract, and a checker that cannot say which
of the five it is asserting is not a checker:

1. **Empty or null** — the node returned nothing usable.
2. **Mutually contradictory** — two outputs that cannot both be true.
3. **Off-topic** — an output that answers a different question than the one asked.
4. **Under-confident** — a confidence signal below the bar for the downstream decision.
5. **Malformed** — a shape that will break the convergence node's parsing.

Three of the five are code checks (1, 4, 5) and cost nothing; only 2 and 3 need a model.
Run them in that order — this is `agent-evals` §5's *cheap checks first*, applied to a
position in the graph rather than to a test suite.

**What a checker costs, and how it turns into a rubber stamp — this pack's addition.** A
checker is a node, so it has the failure mode of every node: it can be wrong. A model
checker that has never been shown a bad input will pass everything, and a graph with a
checker that always says yes is strictly worse than one with no checker, because the
absent checkpoint has been replaced by a false one. So:

- **Give it a planted bad input at least once and watch it refuse.** Same rule as any
  other guard in this family.
- **Record its verdicts as scores with a source** (`agent-evals` §7), or you can never
  ask afterwards how often it fired.
- **A checker that has never rejected anything is a finding**, not a reassurance.

**Wire the convergence to the checker, not to the layer.** The synthesis node depends on
the checker; the checker depends on the branches. If synthesis also takes a direct edge
from a branch, the gate has a bypass and the shape is decoration.

## 7. Static or dynamic

A **static** graph has its nodes and edges decided before it runs. A **dynamic** graph
grows: a node finishes, looks at what it found, and decides what should come next.

| Reach for | When |
|---|---|
| **static** | the task repeats and the structure is the same each time |
| **static** | predictability and speed matter more than flexibility |
| **static** | **always first** — switch only after the static version hits a wall you can name |
| dynamic | the scope of the work depends on what is discovered along the way |
| dynamic | a node must choose its successors from its own output |
| **never dynamic** | **you will need to audit exactly what ran and why** |

The last row is a hard rule in this pack, not a preference. A dynamic graph's executed
shape is not the shape anybody drew, so *"here is the graph"* and *"here is what
happened"* stop being the same document — and every claim about the run becomes
unfalsifiable from the outside. That is the same failure `agent-evals` names when a
system has no durable trace.

**Most workflows that feel like they need a dynamic graph need a better static one.**
Dynamic is more powerful and much harder to control; it is the second reach, never the
first.

## 8. When not to build a graph at all

The honest cost table. A graph is not free, and for a one-off it usually loses:

| | Chain | Graph |
|---|---|---|
| Time to build | low | higher — the dependencies have to be worked out |
| Time to run | the sum of the steps | the longest path |
| Debugging | easy — one line to walk | harder — concurrent state, diluted errors |
| Mid-run failure | poor, but visible immediately | good **only if** there is a checker |
| A one-off task | right answer | overkill |
| Something you run weekly | works | better, and the setup amortises |
| Growth in task size | does not scale | scales |

**Build the graph when the work repeats, or when a mid-run error is expensive enough that
the checker pays for itself.** Otherwise write the chain and move on — this is
`agent-harness`'s *start at the simplest thing that works* applied to shape.

## 9. What Claude Code actually executes

**This section is the pack's, not the source's, and it exists because the source's one
operational claim has since changed.** The article tells the reader that Claude Code has
a `workflow` keyword which parses a YAML block of `nodes:` and `depends_on:` and
parallelises it. Two corrections, both from the vendor's own changelog:

| Version | Entry (quoted from `anthropics/claude-code` `CHANGELOG.md`) |
|---|---|
| v2.1.154 | "Introducing dynamic workflows: ask Claude to create a workflow and it orchestrates work across tens to hundreds of agents in the background" |
| v2.1.160 | "Renamed the dynamic-workflow trigger keyword from `workflow` to `ultracode`. The word 'workflow' no longer triggers a run; asking for one in your own words still works" |
| v2.1.178 | the keyword "trigger[s] only on explicit phrases like 'run a workflow' or 'workflow:', not on any mention of the word" |
| v2.1.219 | dynamic workflows "default to a medium size guideline (aim for fewer than 15 agents)"; settable via `workflowSizeGuideline` |
| v2.1.229 | fan-outs "stagger same-prefix sibling agents so subsequent agents read the cached prompt prefix instead of re-paying it" |

So the keyword named in the article stopped being the keyword in v2.1.160, and the
opt-in today is `ultracode` or an explicit phrase.

**And the YAML is not what runs.** The host does not parse `nodes:`/`depends_on:`. It
authors and executes a **script** whose primitives are the real contract:

| Primitive | Is | Note |
|---|---|---|
| `agent(prompt, opts)` | one subagent | `opts.schema` forces a validated object back, so downstream stages get data, not prose to parse |
| `parallel(thunks)` | concurrent, **with a barrier** | awaits all; a thrower resolves to `null` rather than rejecting the call |
| `pipeline(items, ...stages)` | each item through all stages, **no barrier** | item A can be in stage 3 while B is still in stage 1 |
| `phase(title)` | a progress grouping | display, not semantics |
| `isolation: "worktree"` | a private checkout per agent | the only safe way to fan out writers |

Concurrency is capped at `min(16, cores − 2)` per run, and a run's total agents at 1000.
Passing 100 items is fine — they queue.

**Why this matters for the model above:** the article's diamond is `parallel()`, and the
next section is the distinction it does not draw.

## 10. Barrier or no barrier

**This section is the pack's.** A convergence node is a barrier: nothing downstream of it
starts until every branch has finished. The article treats that as the definition of a
diamond. It is actually a *choice*, and the wrong default.

A barrier is correct only when the downstream stage needs **cross-item** context:

- deduplicating or merging across the whole result set before expensive work;
- an early exit that depends on the total ("zero findings → skip verification");
- a stage whose prompt genuinely compares one item against the others — **which is
  exactly what a checker node does**, and is why the checker is a legitimate barrier.

A barrier is **not** justified by:

- *"I need to flatten or filter the results first"* — do that inside a stage;
- *"the stages are conceptually separate"* — separate is not the same as synchronised;
- *"it reads more cleanly"* — the cost is real. With five branches where the slowest takes
  three times the fastest, a barrier idles the four fast ones for two thirds of the wait.

The rule: **pipeline by default; barrier when a stage names the cross-item fact it
needs.** If it cannot name one, it does not need one.

## 11. Project defaults, written once

Anything you run more than twice deserves its graph conventions recorded where the agent
reads them (`CLAUDE.md`, or the equivalent for the host), so they are not re-derived per
session:

```markdown
## Workflow defaults

- A node with no declared dependency starts immediately; do not serialise by habit.
- Every declared dependency names the data it carries. No payload named ⇒ delete the edge.
- A checker sits between any parallel layer and the node that consumes it, and the
  consumer depends on the checker rather than on the layer.
- A checker flags; it never silently passes an incomplete output.
- A node that fails pauses the run and reports; nothing downstream consumes a flagged output.
- Outputs are files with the node's name; the graph passes paths, not transcripts.
```

The last line is `context-engineering.md`'s *filesystem as context* stated as a graph
rule: an edge that carries a path costs a few tokens, and an edge that carries a
transcript costs the window.

## 12. The source's four diagrams, and what each one is for

The article carries four hand-drawn figures. They are not decoration — each one is doing
a specific job, and knowing which one saves re-reading the prose:

| Figure | What it shows | The job it does |
|---|---|---|
| **Cover — "Graph Engineering explained"** | `START` (define the task) → `SPLIT` (break into nodes) → a fan of three workers labelled *research / compare / check* → `CHECKER` (catch errors early) → `OUTPUT` (one clean answer) | The whole argument in one line, and the only figure in which the checker appears as a first-class stage rather than an afterthought |
| **Node / edge** | Three boxes — `Research` (in: topic, out: findings) → `Write` (in: findings, out: draft) → `Verify` (in: draft, out: final) — with `NODE` and `EDGE` labelled, and **the arrows themselves labelled with the data they carry** | Makes §1 concrete: the payload written on the arrow is what turns "comes after" into "depends on". This is the figure to copy when teaching the model |
| **The diamond** | One `RESEARCH` node fanning into `SOURCE 1/2/3` (bracketed *parallel layer*), all three converging on `SYNTHESIZE` | The ideal shape, drawn **before** the failure modes — deliberately without a checker, which is what §5 then attacks |
| **Workflow — how the code runs** | The same shape in code terms: `research_a/b/c` in a parallel layer, three arrows into `checker` annotated *waits for all three*, one arrow from `checker` into `compare` | The repaired shape. Its point is the single edge out of the checker: `compare` depends on the **gate**, not on the branches — §6's last paragraph, drawn |

## Where this file disagrees with its source

- **The keyword.** The source's `workflow` is `ultracode` since v2.1.160 (§9). Treated as
  a version-dated fact rather than a correction of the author: it was true when written.
- **The YAML.** The source presents `workflow:` / `nodes:` / `depends_on:` as a syntax the
  host parses. It is a way of *describing* a graph in a prompt, and it works for that; the
  execution contract is the script in §9.
- **The barrier.** The source's diamond always synchronises. This file makes the barrier a
  decision with a named justification (§10).
- **The checker's own reliability.** The source introduces the checker and stops. This
  file requires it to have been watched refusing a planted input, and treats a checker
  that has never rejected anything as a finding (§6).
