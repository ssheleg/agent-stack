# Provider lifecycle — where agents come from, and how one earns trust

**Load this when** the question is the workforce rather than the loop: an agent is being
produced, adapted from an existing project, registered, replaced or retired, or a fleet
of workspaces needs governing. The loop that *runs* a provider is the body; what a call
costs is `llm-proxy-billing.md`; whether an action is permitted is `governance.md`. This
file owns the axis none of them hold: a provider's life from intake to retirement.

*Distilled 2026-08-27 from the Passion Code fabric design review (its ADR-0015 and
agent-production design), generalised for any estate of agent workspaces.*

## Contents

- Produced once, bound many times
- The production pipeline, stage by stage
- Knowledge packs — how expertise transfers between projects
- Trust is earned by watched runs: the canary binding
- Two extension mechanisms, and only two
- Workspace lifecycle, and the dependency projection under retirement
- Fleet governance: hierarchical budgets and the run scheduler

## Produced once, bound many times

The distinction the whole file stands on:

| | **Provider** | **Binding** |
|---|---|---|
| Is | the agent as artifact: repo, manifest, capability schemas, service or instruction pack | one workspace's versioned decision to use that provider for a capability |
| Created by | a production run — rare, expensive, gated | a registry write — cheap, reversible |
| Versioned as | provider revisions; v2 goes through the same pipeline as v1 | immutable binding revisions; a run pins one |
| Retired by | archiving its home project | unbinding — history and schedules survive it |

Conflate the axes and every hire becomes a project: nineteen role types across N
workspaces is nineteen providers and N× bindings, never 19×N projects. Rollout of a new
provider version is *rebinding*, never mutation of a binding a running task already
pinned.

## The production pipeline, stage by stage

Producing an agent is an ordinary project whose route is data — a versioned stage list,
not code. The stages that survived review:

| Stage | Gate that closes it |
|---|---|
| **intake** | capability named in the controlled vocabulary; **a consumer named** — the workspace or schedule that will actually call it; workflow-or-agent decided (`agent-harness`: if every step can be named now, it is a workflow behind a capability, not an autonomous agent); transport chosen by the interop rule; money- and publication-adjacent effects declared per agent |
| **knowledge** | sources named and distilled into a knowledge pack (below); every claim in it cites its origin |
| **scaffold** | manifest + capability schemas + one safe fixture validate against the pinned contract revision |
| **instructions** | the instruction pack is a revision, content-hashed, carrying the enumerated vocabulary — status values, capability names — generated from the schema, never retyped |
| **build** | the ordinary delivery pipeline of the estate, run inside the agent's own workspace |
| **evals** | golden fixtures pass AND planted defects are rejected, *watched* — on the two clocks `agent-evals` §6 defines: the **observable** for each requirement written at intake, before the build; the corpus grown from production, where the source project's recorded failures count as production |
| **admission** | shape conformance → protocol negotiation → side-effect-free semantic probes → an immutable admission record |
| **canary binding** | bound under mandatory checking and a budget cap; unsupervised operation is a later, recorded promotion |

The sharpest gate is the first: **no agent without a named consumer.** A role catalogue
is not a production queue, and the cheapest agent to operate is the one you did not
build because nothing would have called it.

Two entry doors, one pipeline: **build** (greenfield) and **adapt** — an existing
project with a stable surface gets inspected without execution, wrapped behind a
capability, and enters at scaffold with its own docs as the knowledge source and its own
recorded failures as the first fixtures.

## Knowledge packs — how expertise transfers between projects

The object that makes "reuse the knowledge, not the code" mechanical rather than
aspirational:

```
knowledge_pack(id, revision, content_hash,
  sources[]:  what was read — repos, docs, audits, retros, with refs
  distilled:
    patterns[]   what works here, each citing file:line
    traps[]      the source's recorded failures and dead ends
    fixtures[]   ← traps, converted into planted-defect eval cases
    glossary[]   terms the new agent must use exactly as the source does
)
```

Three rules give it teeth:

- **A trap becomes a fixture.** The new agent is not admitted until it has been watched
  rejecting the exact defects its predecessor was burned by. Knowledge transfers as a
  check, not as prose an instruction pack hopes the model remembers.
- **A pack travels as an artifact, never as a memory write.** Workspace memory is
  isolated (see `patterns.md` → *Workspace-scale memory*); the pack is the legal vehicle
  between workspaces — explicit, attributable, revisioned.
- **A pack is an injection surface.** Text composed into a prompt from many sources is
  supply chain; a pack produced by an agent passes the same eval gate as code.

## Trust is earned by watched runs: the canary binding

Authorship is not evidence. A freshly produced provider — your own included — enters
under a **canary binding**: its output gates through a checker (the contract lives in
`graph-engineering.md` §6) and its spend is capped, regardless of who wrote it. Removing
the supervision is a **promotion**: a recorded decision citing eval results and run
history, with an author. The record matters more than the ceremony — a checker quietly
dropped is indistinguishable from one that never existed, and the promotion row is the
only thing that says which.

Store, per provider revision, the **production provenance**: source repo, the run that
produced it, its eval set, its admission. "Where did this agent come from" must be a
query, not an archaeology project.

## Two extension mechanisms, and only two

Everything that extends an agent estate is one of:

1. **a versioned registry entry** — a capability name, a skill, a pipeline, a template,
   an event kind;
2. **a provider behind a profile** — an agent, a connector, a checker.

The corollaries do real work: a *connector* is a deterministic provider of `collect.*`
capabilities (no separate plugin system to build); a *checker* is a provider of
`check.*` capabilities (so custom checkers ride the same production pipeline and
admission as any agent, and a checker may never be served by the same binding that
produced the work it checks). A feature that wants a third extension mechanism is a
design smell before it is a backlog item.

## Workspace lifecycle, and the dependency projection under retirement

A workspace moves `proposed → active → dormant → archived`, and two transitions carry
rules that prevent silent damage:

- **dormant pauses its schedules.** A sleeping workspace whose routines still tick burns
  quota and money invisibly — dormancy that does not stop the clock is a label, not a
  state.
- **archived requires the dependency projection to be empty for it**: no active binding
  in another workspace may still point at this workspace's providers. That projection —
  who consumes whose capabilities — is cheap to maintain and impossible to reconstruct
  during an incident; without it, retiring a workspace is a surprise delivered to its
  dependents at call time.

## Fleet governance: hierarchical budgets and the run scheduler

Per-call spend limits do not govern a fleet. Two objects do, and both are projections
over the run record rather than new subsystems:

- **A budget hierarchy** — estate → workspace → goal → task — where an exhausted level
  refuses *admission of new runs* rather than killing running ones, and approaching a
  cap is an attention signal. The money mechanics — wallets, reservations, reconciliation
  — are `llm-proxy-billing.md`; the multi-level attribution argument is
  `governance.md`. What this file adds: the cap must exist at every level, because
  sixty workspaces individually under budget is still one bill nobody approved.
- **A run scheduler** — a ceiling on concurrent runs per host, priority classes
  (incident > scheduled > backfill), and per-provider concurrency tied to the external
  quota records the collectors keep. A fleet without one discovers its capacity limit
  as a pile of half-finished runs on the busiest day of the year.

And one heartbeat rule: every scheduled worker writes an observation about itself; a
stale heartbeat is an attention row. A provider that is not watched is not operated —
the failure mode of every fleet is not the crash but the silence after it.
