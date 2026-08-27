# Memory landscape — what exists to build on, what to measure with, where it is going

**Load this when** deciding whether to build a memory layer or adopt one, choosing what to
evaluate it against, or judging whether a technique somebody is proposing is settled
practice or a research direction.

**Source:** the survey pinned in [`memory-architecture.md`](memory-architecture.md)
— §6 resources, §7 positions and frontiers. That file is its one home; repeating the citation here would give it two.

**Read the dates on everything here.** This is the fastest-moving part of the subject, and
a landscape file is stale the day after it is written. What does not go stale is the
*shape*: which axes the frameworks differ on, and which of the frontier ideas is a
direction rather than a practice.

## Contents

- [1. Build or adopt](#1-build-or-adopt)
- [2. Frameworks, by what actually separates them](#2-frameworks-by-what-actually-separates-them)
- [3. Evaluating a memory layer](#3-evaluating-a-memory-layer)
- [4. Frontiers — and which of them is not practice yet](#4-frontiers--and-which-of-them-is-not-practice-yet)
- [5. The one that changes how you build today](#5-the-one-that-changes-how-you-build-today)

## 1. Build or adopt

An ecosystem of open-source memory frameworks exists — the survey tabulates around
twenty-five, including MemGPT, Mem0, Memobase, MemoryOS, MemOS, Zep, LangMem, Cognee,
Memary, MIRIX, and vector stores used as memory (Pinecone, Chroma, Weaviate).

**What most of them give you** is storage plus retrieval: a vector or graph database, an
API, a short/long-term split. **What most of them leave to you** is the part that decides
whether the memory works — *"they often leave agent behavior and evaluation protocols to
the application."*

So the honest framing of the choice:

| | Adopting a framework | Building on your own store |
|---|---|---|
| You get | schema, indexing, retrieval, a short/long split | nothing you did not write |
| You still own | formation policy, what enters at all, forgetting policy, retrieval timing, **evals** | the same list |
| Argues for it | not writing an index; graph or temporal support you would not build | your entries are few and structured, and a table plus a query is genuinely enough |

**The decision is usually smaller than it looks.** The parts that go wrong — deciding what
becomes a memory, when to retrieve, what to abstain on, what to demote — are yours in both
columns. Adopt for the index, not for the judgement.

## 2. Frameworks, by what actually separates them

Rather than a list that expires, the axes that distinguish them — check a candidate on
these:

- **Does it model experiential memory, or only factual?** Several store facts well and have
  no notion of a strategy learned from a trajectory. If the agent is supposed to improve,
  this is the axis that matters.
- **What is the structure?** Hierarchical short/long-term, graph, temporal knowledge graph,
  flat vectors, profile-based. This decides which queries are cheap. (§3 of
  `memory-architecture.md`.)
- **Is temporal validity first-class?** A store that can express *"this was true until
  March"* supports soft updating; one that cannot will make you delete history to stay
  correct.
- **Does it report results on memory benchmarks at all?** Most do not. Absence is not
  failure, but a framework with published LoCoMo or LongMemEval numbers has at least been
  measured by someone.
- **Multimodal?** Most are text-only. The survey is explicit that **no system provides
  truly omnimodal support** yet.

## 3. Evaluating a memory layer

The survey groups benchmarks two ways, and the split is the useful part.

**Memory-oriented** — built to test memory directly. `LoCoMo` and `LongMemEval` are the two
most frequently reported and the closest thing to a common yardstick. `PersonaMem`,
`PrefEval`, `MemoryBank`, `PerLTQA`, `MPR` stress user modelling and preference tracking.
`StreamBench`, `LifelongAgentBench`, `MemoryAgentBench`, `Evo-Memory` test lifelong and
self-evolving behaviour — new information arriving while old information becomes obsolete
or conflicting. `HaluMem` targets memory-induced hallucination specifically.

**Long-horizon agent benchmarks that stress memory implicitly** — `SWE-Bench Verified`,
`GAIA`, `WebArena`, `ToolBench`, `ALFWorld`. Memory is not the measured target, but
performance depends on it.

**Which to use is not the first question.** The first question is the one `agent-evals`
asks: **what fails if memory is silently disabled?** A public benchmark measures a system
against a distribution that is not yours. A fixture built from your own traces, where the
answer is obtainable *only* from memory, catches the failure mode this whole subject is
about — the agent that skips retrieval and answers confidently from nothing
(`memory-architecture.md` §5.1). Build that fixture first; reach for a public benchmark
when you need to compare against somebody else's system.

**Instrument the negatives.** A memory never queried and a memory that is empty score
identically on every benchmark. Only the retrieval log separates them.

## 4. Frontiers — and which of them is not practice yet

Marked plainly, because the risk with a survey's frontier section is building on a
direction as though it were a technique.

| Frontier | State | What it would change |
|---|---|---|
| **Memory generation** (over retrieval) | direction | memory synthesized on demand for the current task rather than fetched and concatenated. Two shapes: *retrieve-then-generate*, which is buildable now and is essentially §5.4 post-retrieval taken seriously; and *direct generation* with no retrieval step, which is research |
| **Automated memory management** | early | the agent reasons about its own memory through **explicit tool calls** — add/update/delete/retrieve as actions in its loop rather than a module beside it. See §5 |
| **RL-driven memory** | research | the progression is RL-free → RL for selected operations (reranking, the write policy) → fully learned. Most production systems are and will remain RL-free |
| **Multimodal memory** | partial | vision is furthest along, audio underexplored, and **no omnimodal system exists** |
| **Shared memory for multi-agent** | early | from isolated stores with message passing, through naive global stores, toward **role- and trust-aware** access. `memory-architecture.md` §7 |
| **Trustworthy memory** | **requirement, not frontier** | privacy, explainability, hallucination robustness. `memory-architecture.md` §8 |
| **Offline consolidation** ("sleep") | direction | a dedicated interval to reorganize, prune and replay, away from latency constraints. The buildable half of it is the **dual-phase update** in `memory-lifecycle.md` §4 |

## 5. The one that changes how you build today

Of everything above, **automated memory management via explicit tool calls** is the item
worth acting on now, and it costs little.

Instead of a memory module that runs beside the agent — summarizing on a timer, evicting on
a policy, retrieving on every turn — expose memory operations as **tools the agent calls**:
`memory.search`, `memory.write`, `memory.update`, `memory.forget`. Three consequences, and
they are what make it worth doing rather than an aesthetic preference:

1. **The decisions become legible.** Every memory operation is a tool call in the trace,
   which means `agent-evals` can judge them and the retrieval log from
   `memory-architecture.md` §5.1 exists for free — including the negatives, because a turn
   with no `memory.search` call is visibly a turn that chose not to retrieve.
2. **The agent can reason about them** — retrieve, find it insufficient, decompose and
   retrieve again, which is the fast–slow pattern that the timing stage needs anyway.
3. **They inherit everything the tool layer already has** — descriptions the model can act
   on (`agent-harness`), error hierarchies, budgets and loop guards (`SKILL.md` §2).

**The cost, so it is a choice:** more model calls, and a model that can decline to use
memory at all. That second one is the silent failure mode again, which is why point 1
matters — with tool calls you can *see* it happen, and with a background module you cannot.
