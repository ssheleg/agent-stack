# Verification ledger — agent-stack

One row per shipped requirement, with the command that confirmed it and what that
command printed. A row sits at `never` until somebody has watched its check pass on the
shipped artifact — not on a branch, not in a plan.

This file exists because its absence read as zero exposure. `sshlg-skills` board row
**B-30** measured three members returning 0 REQ rows and named the reading it produces:
*"an absent ledger and a clean one are indistinguishable from the number alone."*

---

## Run 2026-08-15 (second) — graph engineering, v0.10.0

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

**9 of 9 verified. 0 at `never`.**

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
