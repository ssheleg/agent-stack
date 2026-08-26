# Changelog

## v0.13.5 — the shared seam is explicit

Both shared validators now state `diverges: none`, completing the umbrella
mechanism contract instead of leaving the constant seam implicit.

## v0.13.4 — shared guards identify their owner

The eval and social-preview validators now declare their umbrella-owned shared
mechanisms, so cross-repository drift is reported as one contract rather than
nine accidental copies.

## v0.13.3 — public contract, measurable before it is marketable

The repository now opens with one install path and one concrete request, carries a
reviewable `SKILL-CARD.md`, portable trigger and behavior evals, and a generated
1200×630 social preview. CI runs the pinned family skill audit, validates the eval
schema, watches its planted defect fail, and checks the preview. The eval suite is
authored, not presented as a model result.

## v0.13.2 — the residue scan stops answering for other runs

`test/residue.py` now tags every workspace with the process group that made it, and the
gate-wide scan reads only that tag. Scanning the shared `$TMPDIR` by prefix reported two
things that are not this run's leak: another session's trees — 37,301 entries under the
shared directory on 2026-08-24 turned a green suite red — and a tree a FAILING case in an
earlier run kept ON PURPOSE as its evidence, which poisoned every run after it. The split is
a pure function with fixtures for both directions, and what it excludes is printed rather
than dropped in silence.

The README told a reader to run commands the published package cannot run: it ships no
`test/` directory, so `python3 test/validate.py` resolves in a clone and nowhere else. Measured against the
published tarball on 2026-08-25. Shipping the suite does not fix it — the plants live in
`.github/workflows/`, which no packaging npm can express puts in a tarball — so the document
now names where the command runs instead of claiming it, beside a marker the umbrella's
validator reads. Naming a dead command is this family's own rule; claiming one is the defect.


## v0.13.1 — a citation into the manifesto is a phrase

Five references into the manifesto had rotted, and every rule they named was
intact — the worst shape a dead citation takes, because it still reads as a
receipt. `manifesto.md:419-422`, which this pack cited as the home of the four
priority axes, now holds *"The strongest is mechanical"*; the axes moved twenty
lines down when the document grew.

Converted to phrase anchors, each verified unique in the subject:
`:156` → *"one input, one job, one output, one owner, and its own completion
test"*, `:114` → *"you cannot connect it to the evidence graph later without
inventing the test"*, `:122` → *"The evidence graph says how the result will be
known"*, `:419-422` → *"How many agents, repositories, services, and owners meet
at the change"*, `:424` → *"These axes are not a fake numerical score"*.

`PRIORITY_AXES_SOURCE` was a constant holding one of the dead addresses; it holds
the phrase now.

Swept from the umbrella's conformance register in the same pass — R-003, run the
fix against its siblings rather than its instance. `seo-aeo-audit` got the four
axes this pack already had, in the other direction, on the same day.

## v0.13.0 — 2026-08-20 — the audit refused a score and computed one

`references/audit.md` said *"a prioritized change plan … **not** a score"* at `:20`, argued
at `:22-25` that *"a number compresses away the only useful information"*, and then computed
`P = blast × confidence / effort` at `:114` and ordered the plan by it at `:128`. The
manifesto backs the refusal in the same words (`manifesto.md:424` — *"these axes are not a
fake numerical score. They are a reason the team can inspect"*) and names **four** axes at
`:419-422`: impact, **irreversibility**, uncertainty, **coordination**. Two of them appeared
nowhere in the pack (`grep -ci irreversib` → 0, `grep -ci coordinat` → 0) and `effort` — a
cost, not a risk — had been substituted for both.

**Position taken: publish the axes, drop the arithmetic.** The number never did what its own
paragraph claimed — `3 × 1 / 3` and `1 × 1 / 1` both print 1, so two findings a reviewer
would rank very differently ranked identically.

Three more, each with its plant:

- **The ledger graded a tree, not an artifact.** Three sections said *unreleased* and
  *"the version stays 0.11.1 and the CHANGELOG is untouched"* over 35 rows reading
  `verified` — while v0.12.0 was tagged and published — against this file's own rule that a
  row sits at `never` until its check has been watched passing **on the shipped artifact**.
  Re-run against `git archive v0.12.0`, both commands exit 0.
- **Three of four skill descriptions were past the house working limit**, one with five
  characters of headroom before the platform's hard 1024. 1019 / 986 / 983 → **964 / 963 /
  970**, every trigger intact (19→19, 12→12, 14→14), and 970 is a gate now.
- **`test/plant_guard_test.py` leaked eight nameless temp trees per run and the gate said
  nothing.** `test/residue.py` is **ported** from `make-skill`, not rewritten; the shared
  pile went from growing to flat (2568 → 2576 measured, 0 growth from this suite).

**Three guards were wrong first, and watching them fail is the only reason that is known:**
the scalar check refused the paragraph that records the formula's removal; the ledger check
read its own citation as a claim; and its `shipped in vX` pattern was **lowercase-only**
while every real claim is capitalised — so it reported green over a file it had never read.

Also corrected: `checks = 9 + len(skill_dirs)` was a hand-bumped literal that five ledger
rows quote as evidence a guard was added. The true count at v0.12.0 was **10**, not 13.

Negative self-tests 19 → **26**.


## v0.12.0 — 2026-08-19

Three places where this pack's own doctrine disagreed with the Proof of Done manifesto it
is built on. Each was confirmed from *inside* the pack before anything was changed.

### The gate before every convergence asked how sure a branch was, never what it could show

The manifesto's checker contract is *arrived · matches its contract · **carries its
evidence** · does not contradict a sibling*. This pack named five things and substituted
**under-confident — a confidence signal below the bar** for the evidence item. In a family
whose first value is Evidence over confidence, and whose own text says "an uncalibrated
judge is an opinion with a number attached", the gate guarding every convergence never
asked what a branch could show.

Six mandatory items now, in run order, with `unevidenced` as item 3 — an assertion with no
receipt, explicitly distinguished from *wrong*. **Arrival is a count**, not an accident: a
never-returning branch is caught because it is missing, not because the host happened to
null it. The confidence signal is kept and demoted to a hint: **low confidence flags,
absent evidence blocks.**

### A node was defined by three of its five fields, and read as whole

`One input, one output, one job` — against the manifesto's five, which add **one owner** and
**its own completion test**. Both texts then gave the same justification in nearly the same
words, which is what let the abridged version read as complete.

Worktree isolation answers **when** — two writers cannot corrupt one file. Ownership answers
**whose** — which node's version is authoritative once the branches return. Isolation without
ownership loses nothing during the run and moves the loss to the merge, where a silently
one-sided merge is indistinguishable from a convergence that only ever had one answer. The
`check` field matches `task-pipeline`'s exactly — same name, same one-string rule, same
`parked` exemption — rather than inventing a second vocabulary for one idea.

### The suite that could never be authored up front had to gate the first release

`Never author the suite up front` read as an absolute because the pack had no word for the
other tier: `grep -ci observable` and `grep -ci requirement` both returned **0**. Taken as
written the rule made a first release ungateable — §3 names the offline suite "this is the
gate", and a suite that may never be authored up front cannot exist before there is
production to grow it from.

Two clocks now. The **observable** is a criterion, written before the implementation. The
**corpus** is a sample, grown from production. The original imperative survives word for
word and gains only its subject: *"Never author the suite up front — the corpus, that is:
the inputs."* Neither rule softens the other, because they govern different objects.

Each contract is declared machine-readably with a floor and named keys, so an item cannot
silently go missing again. Validator 10 → 13 checks; negative self-tests 15 → 19.

## v0.11.1 — 2026-08-16

**This pack was the one place nothing was looking.** The family umbrella's shared checker
had an early exit for a member carrying no routed triggers, and `agent-stack` is that
member — so when a sibling's front matter turned out to be invalid YAML (B-56: a
colon-space inside an unquoted scalar, which every regex-based gate in the family reads
happily and a real parser refuses), nothing here would have caught the same mistake.

`test/validate.py` now asks that checker, which no longer exits early: it validates the
shipped front matter of every skill first, and only then the routed triggers a member may
or may not have. The table it reads is not copied here, so there is nothing to drift.
Watched refusing a planted `Broken: now a nested mapping.` in `agent-orchestrator`'s
description, and green after restore.

## [0.11.0] — 2026-08-16

### Changed

- **`agent-orchestrator`'s body is under its own budget for the first time: 5670 →
  4728 tokens** against the 4750 the pack set itself, and by **splitting rather than
  trimming**. Three layers moved to where they belong instead of every section losing a
  sentence:

  - **`references/pipeline.md`** is new — the planned path and the interrupt that asks a
    person, which are one suspend-and-resume seen from two sides rather than two features.
  - **Observability folded into `references/runtime.md`**, beside the streaming contract it
    was the concrete half of. The body had the API and the reference had the two properties
    that decide whether it is a feed or a decoration; they are one thing now.
  - **Sub-agent retry and the learning cycles went to `references/patterns.md`**, whose
    mechanisms they were the surface of.

  The body keeps the decisions and the checklist keeps only what a heading cannot say. The
  v0.8.0 notes had already made this argument to justify a fourth skill and then the body
  absorbed a layer anyway; the budget is now stated in the file itself.

### Added

- **A check for one home per fact.** Every reference was checked for *existence* in both
  directions and nothing checked whether two of them **say the same thing**. On 2026-08-15
  the same six-row decision table was written into `agent-harness/SKILL.md` and into the
  graph-engineering reference in one afternoon — 50 shared twelve-word runs, found by
  measuring rather than by review. The floor is set above the legitimate maximum, measured
  after that duplication was removed: 12 runs is a skill quoting the rule it defers to, and
  20 leaves headroom for a longer citation while still catching a restated section.

  **It caught its own author within the minute.** Moving two sections into `patterns.md`
  left one rule in both homes; the gate refused, and the copy was deleted.

- **A seventh scanner detector, `declared-deps-ignored`.** A model with a `depends_on`
  field, and a loop over the collection in the order it happens to be stored: the plan says
  it need not be serialised, and then is. This pack shipped exactly that in its own
  reference until yesterday. Conservative — any sign of a topological pass anywhere in the
  file (`layers`, `kahn`, `toposort`, `in_degree`, a `ready` set) and it says nothing. Its
  entry in the blind-spot list is retired, because it is no longer blind.
  `self-test: 9/9` → **`11/11`** (eight plants, three clean fixtures).

- **`agent-harness` cites the static-versus-dynamic model instead of restating it.** The
  six-row table has one home, and it is the reference.

## [0.10.1] — 2026-08-15

### Changed

- **`graph-engineering.md`'s stamp names all three of its sources, and the two numbers that
  come from the third say so.** The file pins an article and Claude Code's changelog, and
  its execution section also states a concurrency cap and a lifetime agent cap that come
  from **neither** — they are the Workflow tool contract the host presents at runtime, a
  source with its own lifetime and no public changelog entry to check them against. A
  revision stamp that names two sources for a file carrying three is the exact defect the
  stamp exists to prevent, one level up. Both numbers now carry the instruction to read them
  back from the running host.

## [0.10.0] — 2026-08-15

### Added

- **`agent-orchestrator/references/graph-engineering.md` — deciding the shape of the work
  before doing it.** The pack could wire a loop, prove it behaved, connect it and tell it
  what to do, and had nothing to say about the question that comes before all four: *does
  this actually have to happen in a line?* Node and edge, the fake-edge test, the diamond,
  the two ways a diamond fails silently, the checker node, static versus dynamic, and the
  cost table that says when a graph is not worth building.

  Sourced from *Graph Engineering with Claude*
  (`https://x.com/Mahaximus_/status/2082442856417956173`, published 2026-07-29), and the
  link is kept so the original can be re-read rather than remembered through the summary.
  Four sections are **this pack's** and are marked as such in the file: what the host
  actually runs, the barrier distinction, what a checker costs, and auditability as a hard
  rule rather than a preference.

- **What Claude Code actually executes, with version evidence.** The source's one
  operational claim aged out six weeks after publication: the `workflow` keyword it names
  was renamed to `ultracode` in **v2.1.160**, and the YAML it shows is a way of describing
  a graph in a prompt rather than a syntax the host parses — the execution contract is a
  script whose primitives are `agent()`, `parallel()` (a barrier) and `pipeline()` (none).
  Every claim in that section carries the `v2.1.x` changelog entry that establishes it,
  which is why the correction reads as a dated fact rather than as an error by the author.

- **`agent-harness` — *Static or dynamic, the second question*.** The workflow-versus-agent
  table decided one thing and left the other open. Six rows, and one of them is hard: a run
  that has to be auditable is static, because a graph that picks its own next nodes produces
  a shape nobody drew, and then *"here is the design"* and *"here is what happened"* stop
  being the same document.

- **`agent-evals` §5a — the checker node as an evaluator that runs inside the graph.** Its
  five catches split three code checks and two judge calls, so §5's *cheap checks first*
  applies to a position in the graph rather than to a suite. And the part that makes it eval
  work: **a checker that has never rejected anything is a finding, not a reassurance** — its
  verdicts are scores with a source, and its rejection rate belongs on the same dashboard as
  its pass rate.

- **A sixth scanner detector, `unguarded-fanout`.** `asyncio.gather` with no
  `return_exceptions=True`, or `Promise.all` with no `allSettled` and no per-branch
  `.catch`: the first sibling to fail cancels the batch, the others' completed work is
  discarded, and the node consuming the results cannot tell a failed branch from an empty
  one. Conservative like the rest — the capturing form anywhere in the file silences it.

### Changed

- **The self-test proves silence as well as noise.** `PLANTS` and `CLEAN` replaced the
  single dict, because one detector now reads two languages and needed a plant in each, and
  because a detector that fires on the defect *and* on its fix has no discriminating power.
  A fan-out that **does** capture its branches is now a fixture the pass must stay silent
  on. `self-test: 6/6` → **`9/9`** (seven plants, two clean fixtures), counted by running it.

- **`agent-orchestrator` §5 no longer contradicts its own data model.** `PlanStage` declared
  `depends_on` and the executor beside it walked `plan.stages` in list order — a plan that
  went to the trouble of saying it need not be serialised, serialised. It now executes in
  dependency layers (Kahn), gates a layer of more than one on the checker before anything
  consumes it, and `ExecutionPlan` grows the `layers()` that makes the declaration mean
  something. A cycle fails the plan rather than deadlocking the run.

### Removed

- **The hardcoded context-window table.** `references/patterns.md` carried nine vendor model
  ids with their windows and a `DEFAULT_CONTEXT_WINDOW` of 16 000. Every number was correct
  when written and none survived: ids were renamed, long-context variants shipped under the
  same family name, and a system reading that table would size its budget for a window an
  order of magnitude smaller than the one it was given. Replaced by the resolution order —
  configuration, then the provider, then a conservative floor **with a loud log line** — and
  the check is mechanical: no vendor model id remains anywhere in the shipped skill text.
  Two illustrative ones in `SKILL.md` and `llm-proxy-billing.md` went with it, because a
  class fixed in one place and left in two others is not fixed.

- **Two duplicated homes.** §8's learning tables and §10's prompt-assembly snippet restated
  what `references/patterns.md` and `agent-harness/references/system-prompt.md` already own.
  Both now state the decision and point at the home. `SKILL.md` is **502 lines / 5670
  tokens** against a 4750 working budget — the number is counted, it is over, and the next
  addition to this body should split rather than absorb.

## [0.9.0] — 2026-08-15

### Added

- **`agent-harness/references/pi.md` and `pi-sdk.md` — the harness doctrine as a worked
  implementation.** Every other reference in that skill states a rule; **Pi** is small enough
  to read and complete enough to have made each of those decisions in public. So each section
  says what Pi does and then **which rule it is an instance of** — the second half is the
  point, and where Pi disagrees with this pack, that is said rather than smoothed over.

  Read from `pi.dev/docs/latest` on 2026-08-15: sixteen doc pages plus the package source.
  All sixteen verified reachable (`200`); the only non-resolving URLs in either file are the
  two deliberate placeholders inside custom-provider examples.

- **`pi.md`** — the four ways to run it; **sessions as a JSONL tree** (8-hex `id`, `parentId`,
  version 3, `BranchSummaryEntry`) matched to *time travel and forking* in
  `agent-orchestrator/references/runtime.md`; **compaction with the real numbers**
  (`contextTokens > contextWindow - reserveTokens`, defaults 16,384 and 20,000, tool results
  truncated to 2,000 chars while summarizing) matched to the compaction ladder, with what the
  ladder adds that Pi leaves to you; settings precedence that **merges rather than replaces**;
  skills, prompt templates and packages; and the trust model.

  Its sharpest section is **the deliberate absence of a sandbox**, quoted: *"prompt injection
  from repository files … is expected local-agent risk and cannot be reliably prevented by
  pi."* That is `layers.md`'s delegation thesis stated by the project itself — and for an
  audit it changes the finding, because "no permission model" here is a delegation, not a
  defect. Three containerization patterns are compared by **where credentials end up**, which
  is the question that actually decides between them.

- **`pi-sdk.md`** — `createAgentSession()`, `ModelRuntime`, `SessionManager`, `defineTool()`,
  `DefaultResourceLoader`; the RPC protocol with its command groups, its full event lifecycle
  and the **`\n`-only JSONL framing warning**; JSON mode's delta-only records and why;
  the `ExtensionAPI` surface; and **the eight seams** — `tool_call` (can block),
  `tool_result` (a middleware chain), `context`, `before_agent_start`, the three provider
  hooks, and the compaction pair — each matched to the doctrine it lets you implement.
  `tool_call` blocking is called out as the single most important one for an audit: it is
  where a per-tool, per-caller policy can actually live.

- Noted with its evidence and its limit: **Pi discovers skills from `~/.agents/skills/`**,
  which on this machine is the ssheleg hub — 72 entries, every family skill carrying the
  `name` and `description` front matter Pi requires. Stated as a fact about the path and the
  front matter, **not** as an observed load: Pi is not installed here. The reference also
  names Pi's documented divergence from the Agent Skills standard (a skill name may differ
  from its directory) and warns that `make-skill`'s validator enforces the strict rule.

### Changed

- `references/layers.md` points at the two new files as the worked example of the kernel
  layer it describes abstractly.
- `agent-harness`'s description gains the embedding triggers (`agent SDK`, `embed an agent`,
  `Pi harness`, `встроить агента`) — 807/1024, inside the family's 970 working budget. The
  repository's own front-matter gate caught a first draft at 1066 and refused the write.


## [0.8.0] — 2026-08-14

### Added

- **`agent-harness`, a fourth skill — the layer between the loop and the model.** The pack
  could wire an agent (`agent-orchestrator`), prove it behaved (`agent-evals`) and connect
  it to other processes (`agent-interop`), and said nothing about **what the agent is
  told**. Five references and a scanner. It runs in both directions: building a harness and
  auditing somebody else's are the same checklist read forwards and backwards, which is why
  the audit lives here rather than in a sixth skill.

  It is a fourth skill rather than a section because `agent-orchestrator`'s body is
  **489 lines / ~4761 tokens** — already past the 4750 working limit — and could not absorb
  a paragraph, let alone a layer.

- **`references/system-prompt.md`** — the right altitude (hardcoded branches on one side,
  vague hope on the other), what actually belongs in a system prompt in order of behaviour
  bought, **enumerating the vocabulary** so an agent stops inventing `pending` and `to-do` in
  the same run, injecting what the model cannot know, and flexible-while-learning versus
  strict-in-production. Plus the three things reasoning models changed: **do not add
  chain-of-thought** (it can degrade instruction-following), give goals rather than
  procedures, and treat reasoning effort as a per-stage dial.

- **`references/tools.md`** — the agent–computer interface. Fewer tools than instinct
  suggests, namespacing, and the description as the product: a worked before/after where the
  strong version names *when*, *what it costs*, *how to narrow*, and **the neighbouring tool
  it is confused with** — the highest-value sentence in a tool definition and the one almost
  nobody writes. Then meaning over identifiers, token efficiency as a correctness issue,
  errors that teach, and **poka-yoke** — changing the interface so the wrong call cannot be
  made.

- **`references/techniques.md`** — fifteen techniques with a **verdict each for a production
  loop**, not a benchmark score. ReAct is the agent loop and its under-quoted failure is that
  non-informative results derail it; reflection is strong exactly where a cheap objective
  signal exists and is a second opinion from the same source where it does not; Tree of
  Thoughts is almost never worth its combinatorics. Ends with an ordered five-question
  chooser.

- **`references/layers.md`** — the question that resolves most framework arguments (*which
  layer am I working at*), what a harness owns, and the design position that **permission
  boundaries usually belong to the environment**: a harness that also claims to be a sandbox
  is claiming a guarantee it cannot keep from inside the same process.

- **`references/audit.md`** — seven tracks, three evidence tiers (**measured / documented /
  judgement**, never inflated), computed priority, and a report shape that ends in a plan
  rather than a score. The finding that ends most audits early is stated first: no evals
  makes everything downstream unfalsifiable, including the audit.

- **`scripts/audit_agent.py`** — the mechanical half. Five conservative detectors
  (unbounded loop, empty tool description, swallowed error, missing timeout, duplicated
  model literal), each requiring the file to show **two** independent signs of an agent, each
  finding carrying `file:line`. It always prints **what it cannot see** and a **denominator**,
  because `read: 1` alone looks like a broken pass while `1 of 4261` is itself a finding.
  Virtualenvs are skipped by their `pyvenv.cfg` marker rather than by name — a real
  repository met during testing kept 4249 of its 4261 files in `myenv/`, and was excluded
  only because `site-packages` happened to be listed too.

### Changed

- **`PROTOCOL_PINNED` now covers `agent-harness`.** Its references document guidance that
  moves, so each carries `**Spec pinned:** … · read <date>` and the build fails without it.
- **CI runs the scanner's own self-test**, and asserts that a real-tree run discloses both
  its blind-spot list and its denominator — a scanner that could stop disclosing would be a
  scanner nobody could calibrate.


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
