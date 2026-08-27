# Memory architecture — deciding what the agent remembers before deciding where to put it

**Load this when** an agent is being given memory for the first time, when an existing
memory layer is being extended, or when memory is present and behaving badly — recall that
misses, a store that grows without bound, an agent confidently answering from nothing.

**Spec pinned:** *Memory in the Age of AI Agents: A Survey — Forms, Functions and
Dynamics*, Hu et al., `https://arxiv.org/abs/2512.13564` (arXiv:2512.13564v2, 13 Jan 2026;
NUS / RUC / Fudan / PKU / NTU and others) · read 2026-08-27. Paper list:
`https://github.com/Shichun-Liu/Agent-Memory-Paper-List`.

`SKILL.md` §7 owns the four **layers** and their lifetimes, and §8 the loops that feed
them. Both answer *how long does this live*. **This file is upstream of that**: it decides
what kind of memory is being built at all, and lifetime is one property of the answer
rather than the taxonomy. The survey's own position, and the reason this file exists:
*"traditional taxonomies such as long/short-term memory have proven insufficient to capture
the diversity and dynamics of contemporary agent memory systems."*

## Contents

- [The source, and what this file adds](#the-source-and-what-this-file-adds)
- [1. Three axes, and lifetime is not one of them](#1-three-axes-and-lifetime-is-not-one-of-them)
- [2. Form — what physically carries it](#2-form--what-physically-carries-it)
- [3. Function — what it is for](#3-function--what-it-is-for)
- [4. Dynamics — formation, evolution, retrieval](#4-dynamics--formation-evolution-retrieval)
- [5. Retrieval is four decisions, not one](#5-retrieval-is-four-decisions-not-one)
- [5.5 The budget, layer 0, and workspace scale](#55-the-budget-layer-0-and-workspace-scale)
- [6. Forgetting, and the long-tail trap](#6-forgetting-and-the-long-tail-trap)
- [7. Shared memory when there is more than one agent](#7-shared-memory-when-there-is-more-than-one-agent)
- [8. Trustworthy memory](#8-trustworthy-memory)
- [9. What this pack does NOT claim](#9-what-this-pack-does-not-claim)
- [10. The checklist](#10-the-checklist)

## The source, and what this file adds

The survey is a map of published work, not a build guide: it classifies roughly two
hundred systems and states open problems. What is taken from it here is the **taxonomy and
the named failure modes**, because those are what an architect needs before writing a
schema. What is added is the decision order — form, then function, then dynamics — and the
wiring to what this pack already owns: §7's layers, §8's learning loops, `patterns.md`'s
confidence arithmetic, `context-engineering.md`'s budget, and `agent-evals` for judging
whether any of it helped.

**Where the survey and this pack disagree, the pack says so rather than quietly adopting.**
§7's four layers are a *deployment* shape that has survived contact with real systems; the
survey's three functions are an *analytical* shape. They are not rivals — the mapping is in
§3 below — and a schema built from either alone is missing what the other sees.

## 1. Three axes, and lifetime is not one of them

Every memory decision is three independent questions. Answer them in this order; answering
the third first is how a vector store arrives before anyone has said what it holds.

| Axis | The question | Answered in |
|---|---|---|
| **Form** | what physically carries it | §2 |
| **Function** | what it is FOR | §3 |
| **Dynamics** | how it is formed, evolved and retrieved | §4, §5, §6 |

Long-term and short-term are **not** a fourth axis. They are a consequence: the survey's
formulation is that short- and long-term effects *"emerge not from discrete architectural
modules but from the temporal patterns with which formation, evolution and retrieval are
engaged."* A single store read once per task behaves as short-term; the same store read
across tasks behaves as long-term. Design the patterns, and the lifetimes follow.

## 2. Form — what physically carries it

Three realizations. Most agent work uses the first and never learns the other two exist,
which is fine until the first one's costs bite.

| Form | What it is | Reach for it when | What it costs |
|---|---|---|---|
| **Token-level** | text, key-value, documents, graphs — anything the model reads as tokens | almost always; it is legible, auditable and editable by hand | every read spends context, and the store competes with the task for the window |
| **Parametric** | the knowledge is in weights — fine-tuning, model editing, adapters | a behaviour must hold with no retrieval step and no context cost, and it changes rarely | not auditable, not selectively deletable, and **wrong entries are expensive to remove** — which collides with §8's right to be forgotten |
| **Latent** | compressed internal states — KV reuse, latent tokens | throughput or privacy dominates and the content need not be read by a person | opaque: nobody can inspect what it holds, so a defect in it is invisible until behaviour is wrong |

Token-level splits further by structure — flat (1D), planar/tabular (2D), hierarchical or
graph (3D). Structure is a **retrieval** decision, not a storage one: a graph is worth its
cost when queries are multi-hop, and is overhead when they are lookups.

**The default, stated so it is a choice and not an accident:** token-level, flat, until a
measured retrieval failure justifies structure. Structure added before that is a schema
maintained for a query nobody runs.

## 3. Function — what it is for

Three pillars. The name matters because **the update rule and the trust level differ per
pillar**, and a store that mixes them applies one rule to all three.

| Function | Answers | Subtypes | Update rule |
|---|---|---|---|
| **Factual** | *what does the agent know* | **user** facts (identity, stable preferences, task constraints, commitments) · **environment** facts (document state, resource availability, what other agents can do) | corrected on contradiction; the newest assertion usually wins |
| **Experiential** | *how does the agent improve* | case-based (whole solutions and trajectories) · strategy-based (insights, workflows, patterns) · skill-based (functions, code, tools it wrote) | earned from a **contrast** — see §8 of `SKILL.md`; never from a single success |
| **Working** | *what is it thinking about now* | single-turn (input condensation, observation abstraction) · multi-turn (state consolidation, hierarchical folding) | discarded at the task boundary unless promoted |

**The split this pack was missing, and why it matters.** §7's layers do not separate *user*
facts from *environment* facts, and the two have opposite failure modes. A user fact that
goes stale makes the agent **rude** — it addresses a person by a preference they abandoned.
An environment fact that goes stale makes the agent **wrong** — it acts on a file that
moved, a budget that was spent, a tool that was removed. So environment facts need a
freshness policy and a re-check on use; user facts need a correction path and a way for the
person to see and edit what is held about them. One TTL for both is wrong twice.

**Mapping to §7's layers**, so the two shapes can be held at once:

| §7 layer | Function it actually serves |
|---|---|
| 1 Chat history | working, multi-turn |
| 2 Working memory (per resource) | working promoted to factual-about-this-task |
| 3 Long-term learnings | experiential — strategy-based |
| 4 Insights | experiential — strategy-based, cross-resource |
| *(missing)* | **factual: user and environment** — add it as its own store, not as a learning |

## 4. Dynamics — formation, evolution, retrieval

Three operators, and a system is defined by which of them it runs and how often.

- **Formation** — what becomes a memory candidate at all. Selective, never the whole
  transcript: *"extracting information with potential future utility rather than storing
  the entire interaction history verbatim."* Owned here by §8 and
  `patterns.md` → **Learning Extraction Heuristics**.
- **Evolution** — consolidation, updating, forgetting. Owned by `patterns.md` →
  **Confidence Management**, **Fuzzy Deduplication**, **Conflict Resolution**. Forgetting is
  under-specified there; §6 below closes it.
- **Retrieval** — this pack had almost nothing on it. §5 is the whole of it.

## 5. Retrieval is four decisions, not one

*"Memory retrieval is not a static search operation but a dynamic cognitive process."* Four
stages, in execution order. A system that implements only the third — the usual case — is
running one of four.

### 5.1 Timing and intent — whether to retrieve at all, and from which store

**The failure this stage exists to prevent has a name and it is silent.** When an agent
overestimates its own knowledge and does not retrieve, there is no error, no empty result
and no latency spike — there is a confident answer built from nothing. It is invisible to
every health check that watches for failures.

- **Always-on retrieval** is the safe default and it is not free: it spends context on
  every turn and injects noise into questions that needed none.
- **Model-decided** retrieval is cheaper and introduces exactly the silent mode above.
- **Fast–slow** is the compromise worth the wiring: answer, self-assess, and retrieve
  deeper only when the first answer is judged insufficient.

**Instrument it or do not ship it.** Log retrieval decisions including the negatives —
*asked, decided not to retrieve* — and give `agent-evals` a fixture where the answer is
only obtainable from memory. A memory that is never queried scores the same as a memory
that is empty, and only the log tells them apart.

### 5.2 Query construction — what to retrieve with

The user's words are not a good query against your index, and this stage is the one most
often skipped entirely. Two techniques, and they compose:

- **Decomposition** — break a compound question into sub-queries, retrieve per part.
  Use when the question spans several facts that no single entry holds.
- **Rewriting** — restate the query in the index's own language, or generate a hypothetical
  answer and search with *that* (HyDE). Use when user phrasing and stored phrasing diverge
  — which is most of the time for a store written by the agent itself.

### 5.3 Strategy — how the search runs

| Strategy | Strong at | Weak at |
|---|---|---|
| **Lexical** (BM25, TF-IDF) | exact identifiers, tool names, error strings, precision | paraphrase, synonyms |
| **Semantic** (embeddings) | paraphrase, fuzzy match — the usual default | drift and forced top-K, which return *something* however irrelevant |
| **Graph** | multi-hop, relational, temporal constraints | cost, and a schema to maintain |
| **Hybrid** | lexical precision plus semantic reach | two systems to tune |

**Semantic-only retrieval always returns K results.** There is no "nothing matched" unless
a similarity floor is set, so an empty store and an irrelevant store look identical to the
model. Set the floor, and make "nothing relevant" a value the caller can act on.

### 5.4 Post-retrieval — what actually reaches the prompt

Raw hits are redundant, stale and mutually contradictory. Two operations:

- **Re-rank and filter** — drop low-relevance and expired items. Temporal validity is a
  filter, not a tiebreak: a fact with a validity window that has closed is wrong, not
  merely old.
- **Aggregate and compress** — merge duplicates and reconstruct one coherent context.

This is where `context-engineering.md`'s budget applies. §7's warning holds at every stage:
every layer competes for one window, so give working memory a floor or a large set of old
generalities will quietly evict what the user said a minute ago.

## 5.5 The budget, layer 0, and workspace scale

Moved here from `SKILL.md` §7 when that file reached its body budget: these are memory
*architecture*, and this is the file about it.

**The trap is the budget, not the storage.** Every layer competes for the same context
window, so allocation is decided per call rather than per layer. A session that trims chat
history to fit a large set of learnings has quietly chosen old generalities over what the
user said sixty seconds ago. **Give layer 1 a floor.** This is the same window
`context-engineering.md` governs, and §5.4's post-retrieval stage is where a retrieval
that ignores it does its damage.

**Layer 0 — carryover state.** Goal, artifacts, verified work and restrictive mode cross a
compaction boundary as copied typed blocks, not prose (`SKILL.md` §12). It is a memory
layer whose whole job is surviving one specific event.

**Workspace scale.** Managing persistent workspaces rather than sessions shifts the scopes
— run, workspace, global, doctrine — and adds the journal-spine rules:
`patterns.md` → **Workspace-scale memory**.

## 6. Forgetting, and the long-tail trap

Three policies, and they are orthogonal — a system usually needs more than one:

- **Time-based decay** — natural aging. `patterns.md` → Confidence Management.
- **Frequency-based** — LRU/LFU, evict what is not read.
- **Importance-driven** — score on temporal, frequency and semantic signals together, and
  increasingly let a model judge salience rather than a counter.

**The trap, stated because frequency-based forgetting is the easy one to reach for:**
LRU-style eviction *"may eliminate long-tail knowledge, which is seldom accessed but
essential for correct decision-making."* The rarely-read entry is often the one that
prevents a rare and expensive mistake — the incident, the exception, the one customer whose
setup differs. **When storage is not the binding constraint, do not delete: demote.** Move
it out of the default retrieval path and keep it reachable by explicit query.

Deletion is also a **correctness** operation, not only a capacity one — see §8.

## 7. Shared memory when there is more than one agent

The progression, and both ends are wrong:

- **Isolated memories with message passing** — no interference, but redundancy, fragmented
  context and communication overhead that grows with team size.
- **A naive global store** — every agent reads and writes one space. This buys joint
  attention and costs **memory clutter, write contention, and no role- or permission-aware
  access control**.

**What this pack already has, and what it is not.** `agent-sync` gives leases, race-free id
reservation and a run journal: it decides *who may write this file right now*. That is
coordination, and it is not shared memory — it says nothing about what an agent should be
allowed to *read*, or whose experiential memory is trustworthy enough to act on. An agent
system that needs both needs both.

**The design rule:** make shared writes **attributed and scoped**. An entry carries who
wrote it and under what role, and a reader may weigh it accordingly. Unattributed shared
memory means one agent's wrong conclusion becomes every agent's premise, with nothing in
the record to trace it back.

## 8. Trustworthy memory

Three pillars, and the survey's position is that these stop being features and become
requirements once an agent is deployed and persistent.

**Privacy.** Agent memory holds user-specific, persistent and potentially sensitive content
— a different risk class from a document index. Memory modules have been shown to **leak
private data through indirect prompt injection**: text the agent read becomes text the
agent stored becomes text the agent will repeat. Three controls: do not store what the task
does not need (the same rule `error-tracking` applies before events reach a third party),
scope reads, and make **verifiable forgetting** possible — which is exactly what parametric
memory (§2) cannot offer, and the strongest argument for keeping deletable knowledge in
token-level form.

**Explainability.** *"Users and developers still lack tools to trace which memory items
were retrieved, how they influenced generation, or whether they were misused."* Minimum
bar, and it is cheap if built in from the start: every retrieval is logged with the ids it
returned, and every answer that used memory can name the entries it used. Retrofitted, it
is a rewrite.

**Hallucination robustness.** The point of memory is fewer invented answers, and a memory
layer can add them: a confidently retrieved stale entry is worse than an empty store,
because it carries authority. **Abstention under low-confidence retrieval** — say *"I do not
have this"* rather than answer from the best of a bad set — is the single highest-value
behaviour here, and it needs the similarity floor from §5.3 to be expressible at all.

## 9. What this pack does NOT claim

Named so a reader does not take this file for more than it is:

- **No benchmark numbers are reproduced here.** The survey tabulates benchmarks (LoCoMo,
  LongMemEval, MemBench, StreamBench and others, §6.1); which of them fits a given system
  is an `agent-evals` question and none of them is quoted as a result.
- **The frontier sections are frontiers.** RL-trained memory management, latent/generative
  memory, and offline consolidation are stated in the survey as open directions, not
  settled practice. They are in §2 as forms with costs, and nothing here recommends
  building on them.
- **This file was written from the survey, not from running these systems.** Where the pack
  has its own measured experience — §7's layers, `patterns.md`'s confidence arithmetic —
  that is marked as the pack's and is not attributed to the paper.

## 10. The checklist

Before an agent gets memory, answer these. An unanswered row is a decision that will be
made by accident:

1. **Which functions does it need?** Factual-user, factual-environment, experiential,
   working — name each one you are building. Not all four are always needed; the ones you
   skip should be skipped on purpose.
2. **What form carries each?** Default token-level and flat. Any other answer names the
   cost it is paying for (§2).
3. **What forms a memory?** The contrast rule for experiential (§8 of `SKILL.md`); an
   explicit write path for factual. Never "log the transcript".
4. **When is it retrieved, and is that decision logged — including the negatives?** (§5.1)
5. **What is the query?** Raw user text is the answer only if you have checked it works.
   (§5.2)
6. **Is there a relevance floor, so "nothing relevant" is expressible?** (§5.3)
7. **What expires, what decays, what is demoted rather than deleted?** (§6)
8. **If more than one agent writes it: who wrote this entry, under what role?** (§7)
9. **Can a person see, correct and delete what is held about them?** (§8)
10. **What eval fails if memory is silently disabled?** If none, the memory layer is
    unmeasured and its value is a belief. (`agent-evals`)
