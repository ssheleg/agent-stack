# Verification ledger — agent-stack

One row per shipped requirement, with the command that confirmed it and what that
command printed. A row sits at `never` until somebody has watched its check pass on the
shipped artifact — not on a branch, not in a plan.

This file exists because its absence read as zero exposure. `sshlg-skills` board row
**B-30** measured three members returning 0 REQ rows and named the reading it produces:
*"an absent ledger and a clean one are indistinguishable from the number alone."*

---

## Run 2026-08-19 (second) — a node says who owns it and what closes it (AG-02, unreleased)

Row: `sshlg-skills/docs/evidence/manifesto-conformance.md` **AG-02**, manifesto requirement
**M-22** (`~/DATA/pod-manifesto/manifesto.md:157`, under the heading *A node has one job* at
`:156`). Local board: `docs/evidence/backlog.md`. **No release**: the version stays `0.11.1`
and the CHANGELOG is untouched, so every row below is measured on the working tree rather
than on a published artifact.

| REQ | Verified by | Result | Status |
|---|---|---|---|
| 001 | confirmed the audit's reading before changing anything | Confirmed. `graph-engineering.md:52` (before) read *"**A node is one unit of work.** One input, one output, one job"* — three of the manifesto's five fields. `grep -i owner` and `grep -i 'completion test'` over the file each exited **1**: neither field appeared anywhere, not in §1 and not elsewhere. What made the omission conspicuous rather than incidental is also confirmed: both texts then give the same justification in nearly the same words — *nodes wearing one name* (`:53` vs `manifesto.md:157`) and the retry/cache/review/replace list (`:54-55` vs `:157`). The audit's reading was correct | **verified** |
| 002 | the two substitutes the audit traced, measured at the commit it read (`2b3d45e^`) | Both confirmed. §4's first rule at `:121-122` — *"no shared mutable state. Two 'independent' workers writing one file are one node with a race in it"* — and §9's primitive table at `:252`, *"the only safe way to fan out writers"*. So the file did answer *how* to fan writers out and never *whose output wins*; and no per-node completion check existed at all | **verified** |
| 003 | read `graph-engineering.md:52-100` after | Five fields declared in the lead sentence (`:52-53`), then `one owner` (`:64`) and `its own completion test` (`:81`) each written out. `grep -c -i owner` → **8**, `grep -c -i 'completion test'` → **4**, from 0 and 0 | **verified** |
| 004 | read `:69-79` — the substantive half of this row | Ownership and worktree isolation are stated as **complementary, not alternatives**, and the distinction is named: isolation answers **when** (two writers cannot corrupt one file, neither can see the other's copy while it runs), ownership answers **whose** (which node's version is authoritative once the branches return). The consequence is written out — isolation without ownership loses nothing during the run and moves the loss to the merge, *"the quieter place for it, because a convergence that silently takes one side is indistinguishable from a convergence that only ever had one answer"* — and §4's rule is recast as the *detection* half against ownership's *assignment* half. §9's table is **cited, not restated**, so the host fact keeps one home | **verified** |
| 005 | read `:93-100` | A completion test is distinguished from §6's checker node, in the direction that matters: the checker judges *arriving siblings from outside*, including the two things no node can establish about itself — whether it contradicts a neighbour, and whether it answered the question the layer was asked. Both are needed, and the text says what dropping either costs. Without this paragraph a reader could read AG-01's checker as the completion test M-22 asks for, which it is not | **verified** |
| 006 | TP-01 alignment, read from `task-pipeline` at the commits that carry it | **Matched, and their work had landed before mine was written.** `8b7de18` *"feat(graph): a node says how it will be closed…"* and `d17ae27` add `check` to `graph.schema.json` — one string, `minLength: 1`, no newlines, required by an `allOf` branch on every node whose `status` is not `parked`. Their `references/work-graph.md:72` states *"**One node, one completion test.** `check` is a string rather than a list… one input, one job, one output, one owner, one completion test… one gate made of two commands is `a && b`, which is still one gate."* I shipped the same field name, the same one-string rule, the same `a && b` line and the same `parked` exemption (`graph-engineering.md:86-92`). **No third vocabulary was invented** | **verified** |
| 007 | `python3 test/validate.py` | `OK: agent-stack structurally valid (12 checks, 4 skill(s), v0.11.1)` — 11 before; the new one is `check_node_contract_keeps_its_five_fields`. It is **AG-01's mechanism reused, not a second one**: a `<!-- node-contract: … -->` declaration beside the prose, a **floor of 5** as a ratchet, `owner` and `check` required by name, every declared field required to appear in the prose **with comments stripped first**, and the spelled count required to match. It adds two requirements AG-01's did not need — the backticked field name `` `check` `` and the pack that defines it — because the M-44 defect is a family holding two names for one field, and doctrine that states only *"its own completion test"* leaves the next implementer to name it themselves. **One home, not two**: this list is stated once (the only match for *"one input"* under `plugins/` is that line), so the check compares a declaration against its own prose rather than against a mirror, and no second home was created to police. Said so in the comment | **verified** |
| 008 | three new negative self-tests in `validate.yml`, run locally from the YAML | Each was watched refusing, and `plant_guard.py verify` confirmed all three plants landed: **shrink** (drop the last declared field, whatever it is called) → *"declares 4 fields, floor is 5"*; **`owner` dropped by key** → *"no longer declares 'owner'"*; **spelled count** → *"the contract has 5 fields and the prose never says 'five'"*. The third plant is **computed, not prose-anchored**: it reads the declaration, derives the number word from its length and removes that word from §1 only, so adding a sixth field re-aims it without an edit | **verified** |
| 009 | the whole negative suite, extracted from `validate.yml` and executed | **20 of 20** executable steps passed, 17 pre-existing + 3 new; runner exit **0**. Three steps were skipped as out of scope locally (global `npm install -g`, `pip install`, a fake `HOME`) and are named rather than counted as green. Four further plants were run by hand and also refused: the declaration comment deleted whole, the lead sentence reverted verbatim to *"One input, one output, one job"*, the backticked `` `check` `` removed from the prose, and `task-pipeline` removed as the field's defining pack | **verified** |
| 010 | `npm test`; `python3 test/validate.py`; `audit_agent.py --self-test`; `yaml.safe_load` on the workflow | exit **0** / **0** / **0** / **0** — `PASS: plant_guard — 9 cases`, `self-test: 11/11 passed`, `workflow parses OK` | **verified** |
| 011 | the duplication check, before and after | Repo maximum unchanged at **12** shared twelve-word runs (`agent-harness/SKILL.md` ↔ the graph reference), against the floor of 20. The file grew **356 → 401** lines and added no new overlap: the manifesto is paraphrased and `task-pipeline` is cited by field name rather than quoted at length | **verified** |

**11 of 11 verified. 0 at `never`.**

### What the checks did not cover

- **The product hypothesis is unobserved, as on every run of this ledger.** Nothing above
  shows a graph in which naming an owner prevented a merge from silently taking one side, or
  a per-node `check` catching an output its author would have passed. The pack ships prose;
  the first graph built with five fields instead of three is the evidence this ledger cannot
  supply, and it does not exist yet.
- **Ownership is stated as a discipline, and nothing here can enforce it.** The check proves
  the *field is declared and described*; it cannot prove any node in any real graph has an
  owner. Unlike `task-pipeline`, this pack ships no schema a node is validated against — so
  on this side M-22 is doctrine with a documentation gate, not a mechanism.
- **The alignment with TP-01 is a reading of their text, not a shared artifact.** Two
  repositories now use `check` with the same stated meaning because I read their schema and
  matched it. Nothing computes that the two definitions still agree, and either can be
  edited without the other noticing — the M-44 defect is *narrowed* here, not closed. A
  cross-repository check would be the mechanism, and it is not built.
- **The `owner` semantics were not reconciled with `agent-sync`.** That pack answers *who is
  holding this file right now* for agents editing a repository; M-22's owner is about a node
  in a graph being built. The two are different questions and the text does not say so,
  because saying it well needs the boundary written in both packs and this row owns only one.
- **Nothing here ran in CI.** The three new steps were executed locally by extracting them
  from `validate.yml`; GitHub has not run them, and no artifact was published.
- **`agent-orchestrator/SKILL.md` was deliberately not touched**, for the reason AG-01 gave:
  its body was already at 4728 tokens against the 4750 it set itself, so a summary of the
  node contract there would buy a second home for the list and break the budget in one edit.
  §1's five fields are reachable from the reference the SKILL.md already links (`:377`).

## Run 2026-08-19 — the checker asks what a branch can show, not how sure it is (AG-01, unreleased)

Row: `sshlg-skills/docs/evidence/manifesto-conformance.md` **AG-01**, manifesto requirement
**M-25** (`~/DATA/pod-manifesto/manifesto.md:186`). Local board: `docs/evidence/backlog.md`.
**No release**: the version stays `0.11.1` and the CHANGELOG is untouched, so every row below
is measured on the working tree rather than on a published artifact.

| REQ | Verified by | Result | Status |
|---|---|---|---|
| 001 | read the audit's two citations before changing anything | Confirmed. `graph-engineering.md:154-161` (before) named *empty-or-null, mutually-contradictory, off-topic, **under-confident**, malformed* and called the list "the contract"; `manifesto.md:186` requires *arrived / matches its contract / **carries its evidence** / does not contradict a sibling*. contract↔malformed and sibling↔contradictory map; **"carries its evidence" had no item at all** and the confidence signal sat in its place — against this pack's own `agent-evals/SKILL.md:154` and `governance.md:53-55`. The audit's reading was correct | **verified** |
| 002 | read `graph-engineering.md:154-190` after | Six mandatory items, `**Unevidenced**` third (line 167): *"an assertion with no receipt: no citation, no tool result, no file and line, nothing a later reader could re-check"*, and explicitly distinguished from *wrong* | **verified** |
| 003 | read `graph-engineering.md:181-190` | The confidence signal is kept and demoted in one paragraph that cites the repo's **own** two arguments — *"an uncalibrated judge is an opinion with a number attached"* (`agent-evals` §5) and *"never a classifier's confidence"* (`governance.md`) — and ends *"low confidence flags, absent evidence blocks"*. No new argument was invented for it | **verified** |
| 004 | read item 1, `graph-engineering.md:159-165` | *Arrived* is now a **count**: the fan-out is fixed when the layer is built, the checker is handed the number to expect and compares it with what it holds. The old incidental catch is named as such — a nulled slot is item 2 "by luck rather than by design" — and §9's primitive table is **cited, not restated**, so the host fact keeps one home | **verified** |
| 005 | the duplication check, before and after | The mirror is declared (DOCMAP 2026-08-15 D-1: the graph reference is the home, `agent-evals` states the eval half and points back), so the two are worded differently on purpose. Shared twelve-word runs between them: **7 → 8**, against the floor of 20. Repo maximum unchanged at **12** (`agent-harness/SKILL.md` ↔ the graph reference). No second home was created | **verified** |
| 006 | `python3 test/validate.py` | `OK: agent-stack structurally valid (11 checks, 4 skill(s), v0.11.1)` — 10 checks before; the new one is `check_checker_contract_is_one_list_in_two_documents`. It compares the two `<!-- checker-contract: … -->` declarations for equality, holds a **floor of 6** as a ratchet, requires `missing` and `unevidenced` by name, refuses `under-confident` as mandatory, requires every declared key (optional included) to be named in the prose **with comments stripped first**, and requires the home's numbered list and its spelled count to match the declaration | **verified** |
| 007 | three new negative self-tests in `validate.yml`, run locally from the YAML | Each plants structurally and each was watched refusing: **shrink** (delete the last numbered item, whatever it says) → *"lists 5 numbered items but the contract declares 6"*; **evidence dropped from both declarations** → *"declares 5 mandatory items, floor is 6"* + *"no longer requires 'unevidenced'"*; **mirror diverged on one side** → *"declare different checker contracts"*. `plant_guard.py verify` confirmed all three plants landed | **verified** |
| 008 | the whole negative suite, extracted from `validate.yml` and executed | **12 of 12** steps printed their `OK:` line, 9 pre-existing + 3 new; runner exit **0**. Three further plants were run by hand and also refused: `under-confident` promoted to mandatory, the declaration comment deleted, and the optional item removed from the prose while left in the declaration | **verified** |
| 009 | `npm test`; `python3 test/validate.py`; `audit_agent.py --self-test`; `yaml.safe_load` on the workflow | exit **0** / **0** / **0** — `PASS: plant_guard — 9 cases`, `self-test: 11/11 passed`, `workflow parses OK` | **verified** |

**9 of 9 verified. 0 at `never`.**

### What the checks did not cover

- **The product hypothesis is unobserved, as on every run of this ledger.** Nothing above
  shows a checker in a real graph refusing an unevidenced branch, or an arrival count
  catching a branch that vanished. The pack ships prose; the first system that gates a
  convergence on the evidence item is the evidence this ledger cannot supply.
- **"A receipt a reader could re-check" is stated, not implemented.** Whether it is
  decidable by code in a given system — a citation that resolves, a tool result that is
  present — is the reader's measurement, and this repository ships no checker library to
  make it one.
- **The arrival count assumes the fan-out is known.** That holds for a static layer, which
  is what §7 already tells you to prefer; a layer that grows its own branches has no such
  number, and the text does not solve that case.
- **The mirror check compares declarations, not meaning.** Two documents can name the same
  six keys and describe them differently; the shingle check deliberately cannot look at
  wording this close, so agreement of *sense* between the two rests on reading them.
- **Nothing here ran in CI.** The three new steps were executed locally by extracting them
  from `validate.yml`; GitHub has not run them, and no artifact was published.
- **`agent-orchestrator/SKILL.md` was deliberately not touched.** Its body measured 4728
  tokens against the 4750 it set itself, so a summary of the new items there would have
  bought a third home for the list and broken the budget in one edit. §13 still describes
  the checker as *usable / not usable* and points at the reference, which stays true.

## Run 2026-08-16 — the body under its budget, and one home per fact, v0.11.0

Brief: `sshlg-skills/docs/evidence/briefs/2026-08-15-graph-backlog.md` (modules M7, M8).

| REQ | Verified by | Result | Status |
|---|---|---|---|
| 001 | `cl100k_base` count of `agent-orchestrator/SKILL.md`, before and after | **5670 → 4728 tokens** against the 4750 budget — under it for the first time. Three layers moved: `references/pipeline.md` (new), observability into `runtime.md`, retry and the learning cycles into `patterns.md` | **verified** |
| 002 | the duplication check, watched firing twice | Measured first: the largest overlap in the pack was **50 shared twelve-word runs** between `agent-harness/SKILL.md` and the graph reference — my own table in two homes. After removing it the honest maximum was 12, so the floor is 20. Then it **caught its own author**: moving two sections left one rule duplicated, 29 runs, refused at the gate | **verified** |
| 003 | a planted restated section | 356 words of §6 copied into a sibling → `share 349 runs of 12 words — that is a restated section, not a citation` | **verified** |
| 004 | `audit_agent.py --self-test`, and two real repositories | `9/9` → **`11/11`** with `declared-deps-ignored`, its plant and its clean fixture. **0 findings** of the new class on `sshlg-skills` and on an unrelated repo, so it is silent on real code as well as on its fixture | **verified** |
| 005 | `python3 test/validate.py` | `OK: agent-stack structurally valid (10 checks, 4 skill(s), v0.11.0)` — the new reference is linked in both directions | **verified** |

**5 of 5 verified. 0 at `never`.**

### What the checks did not cover

- **The split is measured in tokens, not in whether a reader finds things faster.** The
  budget is a proxy for that and it is the only half that can be counted.
- **The duplication floor is 20 because 12 was the measured maximum after one cleanup.**
  A different pack would need its own measurement; the number is not a constant, and the
  comment beside it says which day it was taken.

## Run 2026-08-15 (second) — graph engineering, v0.10.0 → v0.10.1

Brief: `sshlg-skills/docs/evidence/briefs/2026-08-15-graph-engineering.md`.
Spec: `sshlg-skills/docs/evidence/specs/2026-08-15-graph-engineering-design.md`.

| REQ | Verified by | Result | Status |
|---|---|---|---|
| 001 | the file exists; `grep -c 'x.com/Mahaximus_'`; the stamp inside the first 15 lines | `references/graph-engineering.md` present, source URL and publication date carried, `**Spec pinned:** … · read 2026-08-15` on **line 8** | **verified** |
| 002 | read each Claude Code claim against `anthropics/claude-code` `CHANGELOG.md` | five claims, five version entries — v2.1.154, v2.1.160, v2.1.178, v2.1.219, v2.1.229 — each quoted from the changelog and each resolving in it | **verified** |
| 003 | read §9 and *Where this file disagrees with its source* | the source's `workflow` keyword is stated, the v2.1.160 rename is stated beside it, and the correction is framed as a dated fact rather than an error by the author | **verified** |
| 004 | `python3 test/validate.py` | `OK: agent-stack structurally valid (10 checks, 4 skill(s), v0.10.0)`. The orphan branch was **watched failing** first: with the reference written and `SKILL.md` not yet linking it, the validator printed *"exists but SKILL.md never links it"* | **verified** |
| 005 | read `SKILL.md` §5 | the component line says *dependency layers*, the checkpoint loop iterates `plan.layers()`, a layer of more than one is gated on the checker, and `ExecutionPlan.layers()` is in `patterns.md` | **verified** |
| 006 | `grep -nE 'gpt-4\|gpt-3\|claude-3-\|claude-sonnet-4' references/patterns.md` | 6 matching lines before, **no output (exit 1) after**. A widened sweep across all of `plugins/` then found two more illustrative ids — `SKILL.md:62` and `llm-proxy-billing.md:251` — and both went with it | **verified** |
| 007 | read `agent-harness/SKILL.md`; front-matter measured | *Static or dynamic* present with six rows and the audit rule; `description` **807 → 884** chars against the 1024 limit. The orchestrator's own went to **996** and tripped the repo-gate hook at 1048 on the way — the limit is enforced at edit time here, which is how the overshoot was caught in the same minute it was written | **verified** |
| 008 | `audit_agent.py --self-test`, watched both ways | with the plants and no detector: `FAIL unguarded-fanout (asyncio)` and `(promise)`, `7/9`. With the detector: **`self-test: 9/9 passed`**. Run against two real repositories: 0 `unguarded-fanout` findings, so the new detector is silent on real code as well as on its clean fixture | **verified** |
| 009 | read `agent-evals/SKILL.md` §5a | the position in the graph, the five catches split 3 code / 2 judge, and the three consequences — planted refusal, verdicts as scores with a source, zero rejections as a finding | **verified** |
| 010 | `npm pack @ssheleg/agent-stack@0.10.1`, extracted, **and the scanner run from the tarball** | the published package carries `references/graph-engineering.md` with the three-source stamp; `audit_agent.py --self-test` from the extracted package prints `9/9 passed`; `grep` for a vendor model id across the published orchestrator text returns nothing. `docs/evidence/` is not in the package, so this ledger can be corrected without a release | **verified** |

**10 of 10 verified. 0 at `never`.** The registry was read for the content, not only for
the version — a workflow that says `success` and a package that carries the file are two
different claims, and only the second is what an operator installs.

### What the checks did not cover

- **The methodichka has not been used to design a real graph yet.** Everything above
  confirms the text says what it should; none of it confirms the model changes a decision.
  The first orchestrator built with it is the evidence this ledger cannot supply.
- **`unguarded-fanout` has two shapes and a language does not have two.** Python and
  JavaScript are covered; a `Task.WhenAll` or an `errgroup` is the same defect and this pass
  is blind to both. Recorded as a known floor, not a survey.
- **The token budget went the wrong way and the number is stated rather than smoothed.**
  `agent-orchestrator/SKILL.md` is 502 lines / **5670 tokens** against a 4750 working
  budget, up from 5009 — measured with `cl100k_base`, not estimated. Two duplicated
  sections were compressed to offset it and did not. The next addition to that body should
  split rather than absorb.
- **The four diagrams are described, never reproduced.** Whether the descriptions carry the
  same information as the images is a judgement, and it is the author's own.

## Run 2026-08-15 — Pi as the worked implementation, v0.9.0

Brief: `docs/evidence/specs/2026-08-15-pi-reference-brief.md`.
Released: `@ssheleg/agent-stack@0.9.0`, tag `v0.9.0`, `main` at `d97a17d`, CI run `31878521750`,
release run `31878555766` (selected **by tag**, not by recency).

| REQ | Verified by | Result | Status |
|---|---|---|---|
| 001 | `validate.py`; stamp audit | `OK: … (10 checks, 4 skill(s), v0.9.0)`; 7 of 7 references carry `**Spec pinned:**` | **verified** |
| 002 | read both files | sessions→`runtime.md`, compaction→the ladder, trust→`layers.md`, seams→`governance.md`/`tools.md` — each stated in the text, not implied | **verified** |
| 003 | read `pi-sdk.md` | `createAgentSession`, `ModelRuntime`, `SessionManager`, `defineTool`, `DefaultResourceLoader`, RPC command groups + lifecycle, JSON delta-only, `ExtensionAPI`, custom providers | **verified** |
| 004 | table in `pi-sdk.md` | 8 seams, each with the doctrine it implements; `tool_call` called out as the audit's most important | **verified** |
| 005 | *Where Pi and this pack's doctrine differ* | 4 divergences named: no iteration guard, no sub-agents, skill-name leniency, one-rung compaction | **verified** |
| 006 | `curl -o /dev/null -w '%{http_code}' -L` per page | **16 of 16 → `200`**. The only non-2xx are `api.my-llm.com` and `proxy.example.com` — deliberate placeholders inside custom-provider examples, recorded rather than rounded away | **verified** |
| 007 | `ls ~/.agents/skills` + front-matter check | 72 entries; `agent-harness`, `agent-orchestrator`, `agent-evals`, `agent-interop`, `make-skill`, `task-pipeline` all present, `name` and `description` present | **verified, with its limit written into the reference** |
| 008 | token/char count | body 150 ln / ~2235 tok (limits 500 / 4750); description 807/1024 (canon ≤970) | **verified** |
| 009 | local plants | 3 watched failing: stamp removal in `pi.md`, in `pi-sdk.md`, and a dangling link | **verified** |
| 010 | `npm view`; `npm pack` + `tar tzf`; `installed_plugins.json`; hub listing | npm `0.9.0`; tarball carries both files with stamps intact; installed plugin `v0.9.0` with all 7 references; **the same 7 present in `~/.agents/skills`, the directory Pi reads**; shadow check clean | **verified** |

**10 of 10 verified. 0 at `never`.**

### What the checks did *not* cover

- **Pi was never run.** Everything here is read from its documentation and its published
  package layout. The `~/.agents/skills` claim is about a path and front matter, not an
  observed load, and the reference says so in its own text.
- **The doctrine-mapping is an argument, not a measurement.** That Pi's session tree
  *implements* time-travel-and-forking is a reading; it is labelled as one.
- **Pi moves.** The stamp is `2026-08-15`; the mechanical guard proves a date is present,
  never that the prose still matches.
- **One process error, recorded:** `git add -A` in the umbrella swept in a neighbouring
  session's uncommitted brief (`docs/evidence/briefs/2026-08-15-graph-engineering.md`).
  Caught on reading the commit's own file list, removed with `git rm --cached` and
  `--amend` before merge; the file returned to untracked, intact, 85 lines. The commit that
  merged touches 3 files.

---

## Run 2026-08-14 (second) — `agent-harness`, v0.8.0

Brief: `docs/evidence/specs/2026-08-14-agent-harness-brief.md`.
Released: `@ssheleg/agent-stack@0.8.0`, tag `v0.8.0`, `main` at `078dcb6`, CI run `31810634053`.

| REQ | Verified by | Result | Status |
|---|---|---|---|
| 001 | `validate.py`; `claude plugin validate --strict` ×2 | `OK: … (10 checks, 4 skill(s), v0.8.0)`; both `✔ Validation passed` | **verified** |
| 002 | read `references/system-prompt.md` | altitude, vocabulary enumeration, injected context, flexible-vs-strict, and the three reasoning-model changes all present | **verified** |
| 003 | read `references/tools.md` | five ACI principles + worked before/after + poka-yoke + the error-that-teaches contrast | **verified** |
| 004 | count of verdict cells in `references/techniques.md` | 15 techniques, each with a production verdict | **verified** |
| 005 | table in `SKILL.md` | workflow-vs-agent criteria + the five workflow patterns, with the routing/orchestration boundary named | **verified** |
| 006 | read `references/layers.md` | three layers, what a harness owns, what it delegates | **verified** |
| 007 | read `references/audit.md` | 7 tracks, 3 evidence tiers, computed priority, report shape | **verified** |
| 008 | `audit_agent.py --self-test`; runs on 3 real repositories | `self-test: 6/6 passed`; blind-spot list and denominator printed every run | **verified** |
| 009 | `grep SKILL.md` | boundaries stated against all three siblings, plus an explicit not-covered list | **verified** |
| 010 | `PROTOCOL_PINNED` extended; gate | 5 of 5 references stamped `· read 2026-08-14`; validator counts 10 checks | **verified** |
| 011 | local plants + CI | 3 plants watched failing against the NEW skill (missing stamp, dangling link, orphan); CI printed `self-test: 6/6 passed` and `OK: scanner discloses its blind spots and its denominator` | **verified** |
| 012 | `npm view`; `npm pack` + `tar tzf`; **ran the scanner from the extracted tarball** | npm `0.8.0`; tarball carries SKILL.md, 5 references and the script; the published script's self-test prints `6/6 passed` | **verified** |

**12 of 12 verified. 0 at `never`.**

### What the checks did *not* cover

- **No agent system has been audited with this skill end to end.** The scanner ran against
  three real repositories and the seven tracks have not been walked on a live target. The
  first real audit is the evidence this ledger cannot supply.
- **The scanner's five detectors are a floor, not a survey.** Its own blind-spot list is
  longer than its findings list, by design and permanently.
- **The technique verdicts are judgement over documented sources**, not measurements taken
  here. They are labelled as verdicts for that reason.
- **Two false-positive classes were found by running it on real code, not by review** —
  a virtualenv named `myenv/`, and a denominator that made `read: 1` unreadable. Both were
  fixed; the class *"what else only shows up on real code"* stays open.

---

## Run 2026-08-14 — `agent-interop`, v0.7.0

Brief: `docs/evidence/specs/2026-08-13-agent-interop-brief.md`.
Released: `@ssheleg/agent-stack@0.7.0` (npm), tag `v0.7.0`, `main` at `dd46e3e`.
Companion: `@ssheleg/make-skill@0.18.0`, umbrella `sshlg-skills@0.48.0`.

| REQ | Requirement | Verified by | Result | Status |
|---|---|---|---|---|
| 001 | A third skill `agent-interop` ships and conforms | `python3 test/validate.py`; `claude plugin validate . --strict` and `plugins/agent-stack --strict` in CI run `31750367175` | `OK: agent-stack structurally valid (9 checks, 3 skill(s), v0.7.0)`; both `✔ Validation passed` | **verified** |
| 002 | MCP pinned to `2026-07-28`, names the surface that changed since `2025-11-25` | `grep -c` over `references/mcp.md` | `server/discover` 5, `_meta` 5, `Stateless` 1, `subscriptions/listen` 3, `Sampling` 2, `Roots` 1, `Logging` 1, `Dynamic Client Registration` 1, `Tasks` 1, `isError` 2 | **verified** |
| 003 | A2A 1.0 — card, lifecycle, bindings, decision rule | `grep -c` over `references/a2a.md` | `TASK_STATE_COMPLETED` 2, `agent-card.json` 1, `SendMessage` 2, `JSON-RPC` 4, `gRPC` 2, `HTTP+JSON` 1, `contextId` 4, `signatures` 3 | **verified** |
| 004 | Registry — `server.json`, namespaces, proof of ownership, the three refusals | `grep -ci` over `references/registry.md` | `server.json` 7, `reverse-DNS` 1, `mcpName` 2, `mcp-publisher` 8, `Ed25519` 4, and one hit each for the three refusals | **verified** |
| 005 | Gateway stated vendor-neutrally **before** the named implementation | `grep -n '^## ' references/gateway.md` | *What a gateway must do* at line 39; *agentgateway, concretely* at line 115 — the required order | **verified** |
| 006 | Link map, every URL resolving | `curl -s -o /dev/null -w '%{http_code}' -L` over each of 21 extracted URLs plus the 3 written with an ellipsis | **24 of 24 → `200`**, `non-2xx/3xx: 0` | **verified** |
| 007 | Neighbours mapped, one verdict each | `grep -oE '^\| \*\*(…)' SKILL.md` | 6 rows: Agent Skills, ACP, AGNTCY, AP2, "ChatGPT apps", MCP extensions | **verified** |
| 008 | Boundary stated in both skills, wire described in only one | `grep` both `SKILL.md`s; `grep -cE` for method names across all of `make-skill`'s skill files | Both state it. Method names in `make-skill`: **1 hit**, at `references/mcp.md:7`, inside the sentence pointing *at* `agent-interop` — a signpost, not a description. Recorded as-is rather than rounded to zero | **verified, with the one hit named** |
| 009 | `make-skill`'s stale MCP claims gone | `grep -rn -E "stateful protocol\|\`initialize\`\|notifications/initialized\|2025-11-25\|resources/subscribe\|sampling/createMessage\|roots/list"` over `plugins/` and `README.md` in `make-skill` | `NONE — clean`; `make-skill` validator `PASS` | **verified** |
| 010 | Every `agent-interop` reference carries a revision stamp, enforced mechanically | `PROTOCOL_PINNED` in `test/validate.py`; stamps read back from the **installed** plugin | 6 of 6 references stamped, each `· read 2026-08-13`; validator counts the check | **verified** |
| 011 | The stamp check is watched failing | local harness, 9 plants; CI run `31750367175`, 8 negative self-tests | `passed=9 failed=0` locally; CI printed `OK: validator requires a revision stamp…` and `OK: validator rejects a stamp date that never existed`. Also proved: the narrowed link regex still catches a dangling link **inside the new skill** | **verified** |
| 012 | Released and installed | `npm view`; `npm pack` + `tar tzf`; `installed_plugins.json` read back after `npx sshlg-skills@latest update` | npm: agent-stack `0.7.0`, make-skill `0.18.0`, sshlg-skills `0.48.0`. Tarball carries all 6 `agent-interop` references; make-skill tarball carries 10 references and no `mcp-ship.md`. Installed: `agent-stack@agent-stack v0.7.0 skills=['agent-evals','agent-interop','agent-orchestrator']`; shadow check clean | **verified** |

**12 of 12 verified. 0 at `never`.**

### What the checks did *not* cover, said plainly

- **No agent has yet been observed using the skill to build something.** Every row above
  measures the artifact, not the outcome. The first real MCP server written with
  `agent-interop` loaded is the evidence this ledger cannot supply, and it has not
  happened yet.
- **The revision stamps prove a date was written, not that the prose matches the spec on
  that date.** The stamp makes staleness *visible*; it cannot make the reading correct.
  Content accuracy rests on the 17 documents fetched during stage 1, listed in the brief.
- **`gateway.md`'s config example is minimal by choice.** agentgateway's own overview
  still teaches the deprecated `binds`; a longer example copied today would be the trap
  this skill warns about.
