# Changelog

## v0.7.2 — the plants say whether they landed, and two of them were not

Eight negative self-tests asserted inline, in Python, that their edit had happened —
which works, and is the **fifth** careful copy of an idea this family already scripted.
`plant_guard.py`'s own docstring was written against exactly that shape: five hand-written
variants produced five different bugs, one of which reached a pull request.

Adopting the shared implementation found two plants that were doing nothing at all.

### Fixed

- **`cp -R . /tmp/x` into an existing `/tmp/x` nests the tree instead of replacing it.**
  The plant then edits a file left by the previous run, and `touch` on a file that already
  exists changes neither content nor mode — so *a reference nobody links* and *stray
  SKILL.md* both planted nothing, the validator honestly passed, and the step would have
  reported a healthy guard as broken. CI is always fresh, so this was invisible there and
  only ever bit the machine the plants were written on. Every copy is now `rm -rf`'d first.

### Added

- **`test/plant_guard.py` and its nine fixtures**, shared with `make-skill`, the umbrella
  and `seo-aeo-audit`. It compares content **and permission bits**, because the variant
  that shipped compared bytes against a plant whose whole effect was `chmod`.
- **Every plant wrapped in `snap` / `verify`**, the description being the step's own name,
  so a refusal names which plant died.
- **A negative for the guard itself**: an unchanged copy must be reported, not passed.

All eight plants were then watched landing on the machine they were written on.

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2026-08-14

A red `validate` could not stop a publish anywhere in this family, and one member
proved it: on 2026-08-12 `sheleg-dev` tagged v0.4.1 while its own validate run for that
exact tag **failed**, and npm served 0.4.1 four minutes later.

### Fixed

- **The release now runs the whole validate suite before anything is published.**
  `validate.yml` gained a `workflow_call` trigger and `release.yml` calls it with
  `needs: validate` — the release runs *after* the real suite rather than beside a copy
  of it. **Not one plant is duplicated:** each still has exactly one home.
- **A guard keeps the connection there.** It fails when the trigger, the call, or the
  `needs` goes missing — calling the suite without depending on it lets the jobs run in
  parallel, which looks gated and is not. Watched failing against the planted removal.

Proven end to end on `sheleg-dev` v0.4.3 before it reached here: the release run shows
`validate / validate` completing first, then `release`, then `publish`.

## [0.7.0] — 2026-08-14

### Added

- **`agent-interop`, a third skill — the protocol layer between processes.** The pack
  could build an agent (`agent-orchestrator`) and prove it behaved (`agent-evals`), and
  said nothing about how either talks to anything outside its own process. Six references:
  MCP's wire surface, running many servers at once, shipping a server so a client can
  actually reach it, the registry, A2A, and the gateway layer. It is its own skill rather
  than a reference under `agent-orchestrator` because both existing descriptions sit at
  ~91% of the 1024-character budget — measured, not estimated — and "write me an MCP
  server" matches neither of their triggers.

- **`references/mcp.md`** — MCP pinned at revision `2026-07-28`, written around the part
  that breaks code written from memory: the protocol is now **stateless**, the `initialize`
  handshake is gone in favour of `server/discover`, and version plus capabilities ride in
  `_meta` on every request. The full deprecation register with migration paths —
  **sampling, roots, logging and dynamic client registration are all on the way out**,
  which is precisely the set an older model reaches for first. Plus notifications as opt-in
  `subscriptions/listen` streams, `ttlMs` / `cacheScope` caching, and the fact that a
  failed tool arrives as `isError: true` inside a 200.

- **`references/mcp-scale.md`** — the two distinct costs of many servers and the pattern
  for each: progressive discovery for *when* definitions enter context (with the published
  1–5% threshold), programmatic tool calling for *how* tools are invoked. Includes the
  interaction that turns a clever discovery scheme into a regression — most providers cache
  the prompt prefix **including the `tools` array**, so mutating it mid-conversation can
  cost more than the definitions it removed.

- **`references/mcp-ship.md`** — mounting a server inside an existing app, transport-level
  auth, client config in both forms, and the 404 that is really FastMCP's double path.
  Relocated from `make-skill`, where it had been describing a protocol rather than a skill.

- **`references/a2a.md`** — A2A 1.0 under the Linux Foundation: agent cards and the
  `/.well-known/agent-card.json` path, the full `TASK_STATE_*` enum with terminal states
  marked, three protocol bindings with their REST method mapping, and the v0.x→1.0 rename
  spelled out so inherited code is recognisable on sight.

- **`references/registry.md`** — `server.json`, reverse-DNS namespaces and the Ed25519
  DNS/HTTP challenge that proves one, the publish flow with its three named failure modes,
  and the registry's three refusals: no private servers, not for direct host consumption,
  not designed for self-hosting.

- **`references/gateway.md`** — what a gateway must do that an API gateway does not, stated
  vendor-neutrally, with agentgateway as the named reference implementation. Includes the
  federation trap that bites later: `prefixMode: conditional` renames every tool the day a
  second target is added.

### Changed

- **The validator now enforces a revision stamp on protocol references** (`PROTOCOL_PINNED`
  in `test/validate.py`). Prose about somebody else's specification ages silently — a
  reader cannot tell last year's handshake from this year's, and a model writing code from
  it is confidently wrong with no signal anywhere on the page. Every file under
  `agent-interop/references/` must open with `**Spec pinned:** … · read YYYY-MM-DD`, and
  the date must be a real one. Two negative self-tests, both anchored on the stamp's shape
  and both asserting they planted something.

- **`test/validate.py` no longer reads `other-skill/references/x.md` as a link of its own.**
  A bare `references/x.md` means this skill's file; a path-qualified one is prose about a
  sibling. Without the lookbehind, stating a boundary against another skill — which
  `agent-interop` must do — failed the build over a file it never claimed. The existing
  dangling-link plant proves the narrowed pattern still catches the real case, and a second
  plant proves it inside the new skill.

- **The installer functional test asserts every shipped skill installs**, by enumerating the
  skills directory rather than naming files. `bin/agent-stack.js` already enumerated;
  nothing proved it kept doing so.

## v0.6.1 — 2026-08-13

Two CI fixes that had been sitting on `main` unreleased ship here, and the half of
standing instruction #6 that was missing arrives with them.

### Fixed

- **Two plants used `sed -i` and were no-ops on macOS.** BSD sed requires an argument to
  `-i`, so they errored and changed nothing; they could only ever be exercised in CI.
  Converted to Python — the rule `task-pipeline` has enforced on itself for months.
- **Every plant now asserts that it changed the file.** The 2026-08-13 commit
  *anchor the description plant on the file's shape, not its wording* applied one half of
  instruction #6; this applies the corollary to the rest, so a plant that stops landing
  says `PLANT DID NOT LAND: <why>` rather than reporting a healthy guard as broken.
- Also shipping, previously merged and unreleased: *one CHANGELOG-extraction pattern for
  the whole family* (B-11), which is why this release can be cut at all.

All six plants verified by running them locally: each lands, and each makes the
validator fail.

## [0.6.0] — 2026-08-12

### Added

- **`references/runtime.md`** — the layer most orchestrators assume rather than
  specify, and the one this skill was quietly missing. **Checkpoint every iteration,
  not just the stages a human reviews**: the multi-stage path persisted and could
  resume, the simple tool-calling path persisted nothing, so a crash lost the run that
  executes most often — an asymmetry, not a design. Then one interrupt/resume contract
  instead of the two mechanisms the body had for one idea (`ask_user` and a stage
  checkpoint); the four double-texting policies and why interrupt and rollback differ
  in what the transcript looks like afterwards; streaming with event ids so a dropped
  connection rejoins instead of watching nothing for ninety seconds; forking a past
  checkpoint, which debugs through the real loop rather than a reconstruction that may
  not share the bug; stateful versus stateless schedules; and the seven cross-cutting
  concerns welded into the loop pulled out as ordered interceptors — where **order is
  semantics**, because redaction after summarisation redacts a summary that already
  leaked.

- **`references/governance.md`** — permission, where `llm-proxy-billing.md` is cost.
  **The greatest risk is usually not what the model says but what the agent can do**,
  so the four boundaries get four control sets: model call, tool call, external server,
  and agent-to-agent — the last being the one designs miss, since a sub-agent
  inheriting its caller's authority silently widens every permission. The guardrail
  taxonomy in order of reliability, and its honest limit: every content check is
  probabilistic, so anything consequential takes a deterministic limit or a human, never
  a classifier's confidence. Why an audit row without a **policy version** cannot prove
  a control was applied. Cost attribution as a hierarchy, because "which team's agent
  did this" is unanswerable from a flat tenant id. Failover that must be
  policy-equivalent rather than merely available — a chain that silently fails into
  another jurisdiction does it precisely when nobody is reading logs. Fail-open versus
  fail-closed per workload. And blast radius: a sandbox protects the host, not the
  sandbox, and credentials never enter it.

### Changed

- **The References table is an index again.** Each reference now opens with its own
  `Load this when` line, so the trigger has exactly one home and the table cannot drift
  from the files it points at. Compressing it returned ~100 tokens of body budget, which
  is what paid for two new rows: the body sits at 489 lines / ~4883 tokens against
  500 / 5000.
- README describes two skills and five references, and its trigger section covers the
  evals skill and the permission surface, not only the orchestrator and the wallet.

## [0.5.0] — 2026-08-12

### Added

- **A second skill: `agent-evals`** — how you know the thing built by
  `agent-orchestrator` actually behaves. There was no evaluation doctrine anywhere in
  this family; `grep -ril "llm-as-judge\|eval dataset\|regression fixture\|trace id"`
  across four plugins returned nothing.

  An agent's behaviour is not in its source — the code says what it is allowed to do,
  only a run says what it did — so the artifact under test is the execution record.
  Three primitives (run, trace, thread) crossed with three granularities (single-step,
  full-turn, multi-turn), each with its own fixture shape and its own precondition:
  step assertions need a stable architecture or they die at the next refactor; turn
  assertions cover trajectory **and** response **and** state change, because an agent
  that says it saved the preference and did not passes two axes out of three; thread
  scripts checkpoint after every turn and fail fast, or turn 3 derails and turns 4–10
  assert nothing while still reporting a result.

  Then the parts that decide whether any of it is trustworthy: the offline/online/ad-hoc
  timing axis and why offline is necessary and not sufficient; pass-fail rubrics with
  enumerated failure conditions instead of scalar scores that name no fix; code checks
  before model judges; judging the trajectory, not just the answer; **calibrating a judge
  against human labels before trusting it**, because an uncalibrated judge is an opinion
  with a number attached; the classes of output no general judge can grade; a corpus
  grown from production failures where every fixed failure stays a fixture permanently;
  annotation queues with the two reviewer roles kept apart; and simulated users made
  deliberately worse so offline results predict production.

  Body 214 lines / ~2500 tokens; description 911/1024 with paired RU triggers.

### Changed

- **Both installers iterate over `skills/` instead of naming one skill.** `install.sh`
  and `bin/agent-stack.js` each hardcoded `agent-orchestrator`, so a second skill would
  have shipped in the package and reached nobody. Verified by running both against a
  clean `HOME` and listing what arrived. The CI smoke test now asserts both skills.
- README and both manifests describe two skills; the marketplace entry's description is
  the manifest's, rather than a second one drifting beside it.

## [0.4.0] — 2026-08-12

### Added

- **`references/context-engineering.md`** — what the loop gives up when the window
  runs out, which the skill named a threshold for and never answered. The five-rung
  compaction ladder, cheapest first, with a re-measure between rungs so a small
  overage never buys a model call; the rung that exists only for the case where the
  compaction request itself does not fit; the **tool-pair invariant** — one boundary
  finder used by every rung, because a truncation that orphans a `tool_use` fails the
  *next* request with a 400 in the middle of a task; **typed carryover blocks** copied
  across the boundary rather than summarized, since a summarizer keeps the discussion
  and drops the state, including the flag that said not to write; **tool-output
  offload** to a file with the path left in context, because trimming history cannot
  save a window one result already filled; token estimation and the direction it errs;
  the compaction circuit breaker; sub-agent context isolation; the filesystem as
  context; and how to pick constants for your own window.

  Ladder structure and the attachment taxonomy are adapted from
  [HKUDS/OpenHarness](https://github.com/HKUDS/OpenHarness) (MIT),
  `services/compact/__init__.py` and `services/tool_outputs.py`. The constants are
  deliberately ours — and deliberately absent, with anchors for choosing them, because
  a threshold copied without its window is a number nobody can defend.

### Changed

- **§12 Context Engineering** in the body: five traps an agent cannot know to look up,
  because it does not know they exist. **§7 gains Layer 0 — carryover state**, the one
  memory layer whose survival is deterministic rather than a model's choice. §2 gains
  the iteration refund. Body lands at 486 lines / ~4985 tokens against the 500 / 5000
  budget — every insertion was cut twice to fit, and the depth is in the reference
  where it belongs.

## [0.3.0] — 2026-08-12

### Changed

- **The description now opens with `Use when …` and carries paired Russian triggers.**
  That has been the family canon since `super-ux` v0.20.0; this repository was created
  after it and never adopted it, so the skill did not match a request written in
  Russian — and a skill that does not match is a skill that is not there. 923/1024
  chars, inside the 970 working limit that v0.2.0 had already brought it under.

## [0.2.0] — 2026-08-11

### Changed

- **The body went 604 lines / 5361 tokens to 459 / 4146** — the caps are 500
  and 5000, and it was the only skill in the family over both. Measured with
  `cl100k`.

  Sections 6 (provider routing) and 7 (memory layers) were carrying depth that
  `references/llm-proxy-billing.md` and `references/patterns.md` already hold —
  fallback chains and retry/backoff in the first, confidence management,
  extraction heuristics, fuzzy deduplication and conflict resolution in the
  second. The body keeps the shape of each (the four-layer table, the router's
  contract) plus the traps, and points at the depth.

  The traps stay inline because an agent cannot know to open a file about a
  trap it does not know exists: a retry loop and a fallback chain **multiply**,
  a health check that only runs on failure never recovers, model selection has
  three levels and a silent precedence bug bills a cheap model at a premium
  rate, and every memory layer competes for one context window — give layer 1 a
  floor or old generalities crowd out what the user said a minute ago.

- `references/patterns.md` gains the `## Contents` list the canon requires of a
  reference over 100 lines: a partial read is what agents actually do, and
  without the list it returns an arbitrary slice.

- The description trimmed 975 → 937 chars, inside the 970 headroom, by dropping
  two trigger phrases already covered by their neighbours.

## [0.1.0] — 2026-08-06

First release. The skill is a port: it was written and used inside Cursor
against a production multi-agent system, and this repository is where it
becomes installable, versioned and checked.

### Added

- **`agent-orchestrator` skill** (618 lines) — the orchestrator pattern with a
  shared context object and a sub-agent protocol; a tool-calling loop with
  in-loop trimming, wrap-up injection at ~70% of the window and a max-iteration
  guard that still composes a partial answer; meta-tools that delegate rather
  than execute; sub-agent retry split into retryable and fatal; a multi-stage
  pipeline with complexity detection, human-in-the-loop checkpoints and resume;
  multi-provider routing with fallback, exponential backoff and health checks;
  a four-layer memory system (chat history, working memory, long-term learnings,
  insights) with confidence lifecycles, fuzzy dedup, conflict resolution and
  decay; context budget allocation; self-learning feedback loops.
- **`references/patterns.md`** (351 lines) — the data models and algorithms
  behind the above: message and result protocols, pipeline models, the SQL
  validation loop, context-window sizes and token estimation, learning
  extraction heuristics, confidence management, the fuzzy-dedup and
  conflict-resolution patterns, cross-resource transfer, and a suggestion engine
  that costs no LLM calls.
- **`references/llm-proxy-billing.md`** (255 lines) — the wallet side of
  reselling LLM access, generalized from an OpenRouter Management API
  integration: tiered balances and the single boundary where markup applies,
  two-phase commit against a provider API with compensating transactions,
  transaction-scoped advisory locking, optimistic concurrency for reclaims,
  spend-delta polling and the three cases it must distinguish, budget/loop/
  auto-pause guardrails converging on one pause function with per-cause
  timestamps, per-tenant key lifecycle and healing, the refund waterfall, and
  model routing precedence.
- Structural validator (`test/validate.py`) enforcing one version across four
  files, Agent Skills front-matter limits, and reference links in **both**
  directions — the source this skill came from shipped a `reference.md` that
  nothing referenced, and that is now a failing check.
- Installer CLI, `install.sh`, Cursor rule channel, plugin + marketplace
  manifests, CI with negative self-tests.

### Notes

The `references/patterns.md` file was `reference.md` in the source and was
renamed on the way in: it is loaded by name from `SKILL.md`, and the validator
now requires that link to resolve.
