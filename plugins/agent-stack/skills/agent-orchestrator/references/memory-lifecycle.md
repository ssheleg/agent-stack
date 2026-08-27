# Memory lifecycle — how an entry is made, changed and thrown away

**Load this when** writing the code that decides what becomes a memory, how a new entry
meets the ones already there, and what leaves. `memory-architecture.md` decides *what kind*
of memory is being built and owns retrieval; this file is the **write path**.

**Source:** the survey pinned in [`memory-architecture.md`](memory-architecture.md)
— §5.1 formation, §5.2 evolution. That file is its one home; repeating the citation here would give it two.

The three operators run at **different frequencies**, and that is the design. Formation can
run per turn, evolution per task boundary or offline, retrieval per call. Short- and
long-term behaviour is a consequence of those frequencies, not of separate boxes.

## Contents

- [1. Formation — five ways to turn experience into an entry](#1-formation--five-ways-to-turn-experience-into-an-entry)
- [2. Choosing among them](#2-choosing-among-them)
- [3. Evolution — consolidation](#3-evolution--consolidation)
- [4. Evolution — updating, and the stability–plasticity dilemma](#4-evolution--updating-and-the-stabilityplasticity-dilemma)
- [5. Evolution — forgetting](#5-evolution--forgetting)
- [6. What this pack already implements](#6-what-this-pack-already-implements)

## 1. Formation — five ways to turn experience into an entry

*"Instead of passively logging all interaction history, the memory system selectively
identifies information with long-term utility."* Five operations, and they compose — one
system commonly runs several.

| Operation | What it produces | Strength | The cost, stated |
|---|---|---|---|
| **Semantic summarization** | a compact narrative of a long stream | drastically shorter context; ideal for long dialogue | **lossy by design** — specific details and subtle cues get smoothed out, so it is wrong for evidence-critical tasks |
| **Knowledge distillation** | discrete reusable facts or strategies | fine-grained, function-specific | produces flat units with no relation between them |
| **Structured construction** | a graph or tree — entities, relations, hierarchy | explainability and multi-hop queries | **schema rigidity**; extraction and maintenance cost is high, and nuance that does not fit the schema is lost |
| **Latent representation** | vectors or KV states | high density, cross-modal, no decoding loss | **a black box** — cannot be inspected, edited or verified by a person |
| **Parametric internalization** | changed weights | zero retrieval cost, "instinctive" access | catastrophic forgetting, high update cost, and **cannot be precisely removed** |

### Summarization has two shapes and they fail differently

- **Incremental** — fuse each new chunk into the running summary. Supports streaming and
  avoids reprocessing the whole history. Fails by **semantic drift**: errors compound
  across iterations, because each summary is built from the last one.
- **Partitioned** — summarize segments independently, then aggregate. Finer-grained and
  parallelizable. Fails by **losing cross-partition dependencies**, and by cutting at
  arbitrary boundaries unless segments are chosen semantically rather than by length.

If you summarize by fixed window size, you have chosen partitioned summarization with the
worst possible partition rule.

### Distillation splits by what it is distilling

- **Factual** — dialogue turns into stated facts, user intent, environment state. Watch for
  *goal drift*: separate confirmed constraints from unresolved intents, or the agent starts
  treating a floated idea as a decision.
- **Experiential** — strategies from trajectories. **From contrast, not from success.** The
  survey's own split confirms what §8 of `SKILL.md` already requires: success-only
  distillation learns the agent's habits, and the systems that work compare successful and
  failed runs, or reflect against ground truth.

## 2. Choosing among them

The question is not which is best. It is **what the memory will be asked for later**:

| If the later question is… | Form it now with |
|---|---|
| "what happened, roughly" | semantic summarization |
| "what is true about X" | knowledge distillation, factual |
| "how do I do this kind of task" | knowledge distillation, experiential |
| "what connects to what" / multi-hop | structured construction |
| "match this to anything similar" at volume | latent |
| "behave this way, always, with no lookup" | parametric — and read §2 of `memory-architecture.md` on why this is rarely the answer |

**A schema chosen before this question has been asked is a guess.** The commonest and most
expensive version of that guess is a knowledge graph built because graphs sound thorough,
then maintained for multi-hop queries nobody runs.

## 3. Evolution — consolidation

Merging new entries with existing ones so learning is cumulative rather than a growing pile
of near-duplicates. Three granularities:

- **Local** — a new entry retrieves its top-K nearest and a model decides whether to merge.
  Cheapest, and the one to build first.
- **Cluster-level** — align a new cluster with similar existing clusters and fuse. Captures
  regularities across instances that local merging cannot see.
- **Global integration** — periodically distil system-level insight from the whole store.

**The cost of consolidation, which is the reason not to run it aggressively:**
*"it risks information smoothing, where outlier events or unique exceptions are lost during
the abstraction process."* The exception is often the entry worth keeping — see §5.

## 4. Evolution — updating, and the stability–plasticity dilemma

Updating resolves *conflict*; consolidation performs *abstraction*. They are different
operations and a system needs both.

**The trajectory the field took, and it is worth copying rather than rediscovering:**
early systems detected a conflict and **replaced or deleted** the old entry — destructive,
and it erased historical context and broke temporal continuity. The better pattern is
**temporal annotation**: mark the superseded fact with a validity window instead of
deleting it. Soft, time-aware updating keeps both semantic consistency and history.

**Dual-phase updating** is the shape that survives real load: a soft online update for
responsiveness, then an offline reflective pass that merges similar entries and resolves
conflicts properly. Eventual consistency, deliberately — because doing full reflective
consolidation inline puts a model call on the write path of every interaction.

**The dilemma has no general answer:** *"determining when to overwrite existing knowledge
versus when to treat new information as noise. Incorrect updates can overwrite critical
information."* What a system can do is make the decision **reversible** — which is the
argument for annotation over deletion, again.

## 5. Evolution — forgetting

Three policies on three different signals — creation time, access frequency, judged
importance. They are orthogonal and most systems need more than one.

| Policy | Signal | Watch for |
|---|---|---|
| **Time-based** | age | evicting on age alone drops stable facts that were simply written early |
| **Frequency-based** | reads | **the long-tail trap** — see below |
| **Importance-driven** | a composite, increasingly a model's judgement of salience | the judge becomes a dependency, and an unaudited judge silently sets policy |

**The long-tail trap, stated because frequency-based eviction is the easy one to reach
for:** *"heuristic forgetting mechanisms like LRU may eliminate long-tail knowledge, which
is seldom accessed but essential for correct decision-making."* The entry read twice a year
is often the incident, the exception, the one customer whose setup differs — precisely the
entry that prevents an expensive mistake.

**The rule:** where storage is not the binding constraint, **demote rather than delete**.
Move it out of the default retrieval path, keep it reachable by explicit query. The survey
reports this is what many systems do in practice: *"when storage cost is not a critical
constraint, many memory systems avoid directly deleting certain memories."*

Deletion remains a **correctness and privacy** operation — a person asking to be forgotten
is not a capacity decision, and `memory-architecture.md` §8 covers it.

## 6. What this pack already implements

Stated so this file is read as an extension and not as a replacement:

| Survey concept | Where it already lives here |
|---|---|
| Formation, experiential, from contrast | `SKILL.md` §8 · `patterns.md` → Learning Extraction Heuristics |
| Consolidation, local | `patterns.md` → Fuzzy Deduplication |
| Updating, conflict resolution | `patterns.md` → Conflict Resolution |
| Forgetting, time-based | `patterns.md` → Confidence Management |
| Global integration, cross-scope | `patterns.md` → Cross-Resource Learning Transfer |
| **Frequency-based forgetting** | **nowhere — and the long-tail trap above is why that is a deliberate omission rather than a gap to close carelessly** |
| **Temporal annotation instead of deletion** | **nowhere** — Conflict Resolution currently resolves rather than annotates |
| **Dual-phase updating** | **nowhere** — the pack updates inline |

The last three are named as absent rather than quietly added: each is a real change to a
mechanism that is in production, and this file's job is to say what the options are, not to
change `patterns.md` from a survey.
