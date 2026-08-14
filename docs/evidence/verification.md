# Verification ledger — agent-stack

One row per shipped requirement, with the command that confirmed it and what that
command printed. A row sits at `never` until somebody has watched its check pass on the
shipped artifact — not on a branch, not in a plan.

This file exists because its absence read as zero exposure. `sshlg-skills` board row
**B-30** measured three members returning 0 REQ rows and named the reading it produces:
*"an absent ledger and a clean one are indistinguishable from the number alone."*

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
