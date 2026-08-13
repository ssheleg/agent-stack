# Brief — `agent-interop`: the protocol layer between agents

**Run:** 2026-08-13 · **Repos:** `ssheleg/agent-stack` (primary), `ssheleg/make-skill`
(boundary), `ssheleg/sshlg-skills` (umbrella pin) · **Artifact root:** `docs/evidence/`
(no `artifacts.root` in a `pipeline.json`; this repo has none, so the default applies)

---

## Scope

The family builds agents (`agent-orchestrator`), proves they behave (`agent-evals`),
and governs what they may reach (`governance.md`). It has no home for **how an agent
talks to anything that is not its own process** — the protocol layer. This run adds
one, and settles the boundary against the skill that had been carrying half of it.

Out of scope, said out loud: no code is written against these protocols in any product
repository; no MCP server is built or published; `agent-orchestrator` and `agent-evals`
keep their front matter untouched (both sit at ~91% of the 1024-char description budget,
measured, which is why a third skill exists at all).

---

## Phase-1 source ledger

| Source | What it says about this task | Freshness |
|---|---|---|
| `~/DATA/agent-stack` @ `04e8e76`, `main` | v0.6.0, 2 skills, 5 references, 1121 reference lines. No protocol doctrine | current — `git rev-list --count HEAD..@{u}` = 0 |
| `agent-orchestrator/references/governance.md:33-34` | names "external server call (MCP and similar)" and "agent-to-agent" as **boundaries to control**, never as protocols to speak | current |
| `agent-orchestrator/SKILL.md:169-177` | `has_mcp` → `QUERY_MCP`: MCP appears as a capability flag, not a contract | current |
| `make-skill/references/mcp.md` (137 ln) | **the collision, and it is stale** — pinned to spec revision `2025-11-25`; line 49 calls MCP "a **stateful** protocol"; lines 52-57 describe the `initialize` → `notifications/initialized` handshake | **stale** — see *Divergences* |
| `make-skill/references/a2a.md` (153 ln) | A2A 1.0.0, Agent Card, task lifecycle, v0.x drift warning | current |
| `make-skill/references/mcp-ship.md` (275 ln) | mounting a server, the `/mcp/mcp` 404, `server.json`, publishing to the registry | current |
| Family sweep, 8 members | `make-skill` is the **only** other home. `sheleg-design`, `super-ux`, `seo-aeo-audit`, `sheleg-dev`, `task-pipeline` name specific MCP servers as tools they consume — consumers, not doctrine | current |
| Wiki `projects/agent-stack/agent-stack.md` | says v0.1.0, "one skill", 2 references | **stale** — stage 9 |
| Family board `sshlg-skills/docs/evidence/backlog.md` | B-30 (this repo has no verification ledger), B-32 (pin two commits behind), B-24 (graph stale family-wide), B-26/B-27 (release gates and plants) | 2026-08-13 |
| Family retro, 8 standing instructions | **#6 binds directly**: a plant anchored on prose stopped planting and turned *this repository's* CI red for a validator that was fine | in force |
| `graphify-out/` | absent in this repo — no reach analysis available | n/a |
| `docs/`, `CLAUDE.md`, `docs/adr/`, `.task-pipeline/` | absent — first pipeline run here | n/a |

### Divergences found during the grill

1. **`make-skill/references/mcp.md` describes a protocol MCP no longer is.**
   `https://modelcontextprotocol.io/specification/latest` now serves revision
   **2026-07-28**, whose *Key Details → Base Protocol* reads "Stateless,
   self-contained requests. Per-request capability negotiation." The file says
   stateful, with an `initialize` handshake. Its own header — *"Read from the spec
   on 2026-07-28"* — shows it was read that day and left pinned to the older
   revision. Resolved by the operator: **one home**, `agent-interop` takes the
   protocol, `make-skill` keeps the skill-author delta and points at it.
2. **The wiki page is two minor versions and one whole skill behind.** Logged for
   stage 9, not fixed during the grill.

---

## Locked decisions

| # | Decision | Why, and what it rules out |
|---|---|---|
| D-1 | A **third skill**, `agent-interop`, in the existing `agent-stack` plugin — not a reference under `agent-orchestrator` | Measured: `agent-orchestrator` description is 914/1024 chars, `agent-evals` 911/1024. The triggers this work needs ("MCP server", "A2A", "agent card", "MCP registry", "agentgateway") do not fit in 110 characters, and a reference only loads once its parent skill has already triggered — which "write me an MCP server" would not do. Precedent: `agent-evals` was added the same way in v0.6.0 |
| D-2 | Four protocols in depth, neighbours as a **map with a verdict each** | Operator's call. A named boundary is the family's standard; an unnamed one is treated as a defect. Deep: MCP 2026-07-28, the MCP Registry, A2A 1.0, the gateway layer. Mapped: Agent Skills, AP2, AGNTCY/ACP, OpenAI Apps SDK, plus an explicit *deliberately not covered* |
| D-3 | **One home for the protocol.** `agent-interop` owns the wire; `make-skill`'s three references shrink to what is true only for a *skill author* and point at it | Operator's call, taken after the collision surfaced. Rules out the cheaper option of leaving two descriptions of one protocol to diverge again |
| D-4 | The run goes **outward to the end**: PR → merge → tag → npm → umbrella pin → local installs refreshed | Operator's explicit authorization, recorded here as the specific standing authorization the stage-7 floor requires. Named targets: `@ssheleg/agent-stack` v0.7.0 and `@ssheleg/make-skill` v0.18.0 on npm; `ssheleg/sshlg-skills` pin + `skills.json`; `npx --yes sshlg-skills@latest update` on this machine |
| D-5 | **Every wire-level claim carries its revision stamp and an instruction to re-verify.** Doctrine is written version-agnostic; field and method names are stamped | Convention call, taken from what this run measured about itself: a model whose training ended before 2026-07-28 confidently writes `initialize` and `sampling`. A skill that hardcodes today's names without a stamp becomes the same trap it exists to prevent. Reversible; recorded rather than assumed |
| D-6 | Minimal wire-accurate skeletons only (`server.json`, an Agent Card, the `_meta` envelope) — **no tutorials** | The operator asked for links "куда идти для изучения". Tutorials are what the links are for; what an agent cannot reconstruct from memory is the exact shape of a document |
| D-7 | Run mode `run.loop`: **off** | One module, not a platform. Recorded so it is not re-asked |

No ADR written: D-1 and D-3 are reversible inside one repository at the cost of one
release each, so the third ADR criterion (a genuinely hard-to-reverse call) is not met.

---

## REQ table — frozen

Adding is free; removing or narrowing needs the operator, recorded in the carry-over ledger.

| ID | Requirement | How it is verified | Status |
|---|---|---|---|
| REQ-001 | A third skill `agent-interop` ships in the `agent-stack` plugin and conforms to the Agent Skills standard | `python3 test/validate.py` prints `3 skill(s)`; `claude plugin validate . --strict` exits 0 | open |
| REQ-002 | MCP doctrine is pinned to revision `2026-07-28` and names every part of the wire surface that changed since `2025-11-25` | `grep` in `references/mcp.md` for `server/discover`, `_meta`, stateless, `subscriptions/listen`, sampling-deprecated, Tasks extension | open |
| REQ-003 | A2A doctrine at 1.0: Agent Card, task lifecycle, transports, and the A2A-vs-MCP decision rule | `grep` in `references/a2a.md`; the decision rule is a table | open |
| REQ-004 | The MCP Registry: `server.json`, reverse-DNS namespaces and their verification, preview status, and its three refusals (no private servers, not for direct host consumption, not self-hostable) | `grep` in `references/registry.md` | open |
| REQ-005 | The gateway layer stated vendor-neutrally — what agent traffic needs that an API gateway does not give it — with agentgateway as the named reference implementation | `references/gateway.md` separates "what a gateway must do" from "how agentgateway does it" | open |
| REQ-006 | A link map: every canonical doc URL an agent should read, each row saying **when** to read it | table in `SKILL.md`; every URL resolves (checked, not assumed) | open |
| REQ-007 | The neighbours' map, one verdict per entry, plus an explicit *deliberately not covered* list | section in `SKILL.md` | open |
| REQ-008 | The boundary against `make-skill` is stated **in both skills**, and neither repeats the other's protocol text | `grep` both; the two statements agree | open |
| REQ-009 | `make-skill`'s stale MCP claims are corrected and its protocol references reduced to the skill-author delta | no `initialize`-handshake or "stateful protocol" claim survives; `make-skill`'s own validator green | open |
| REQ-010 | Every reference under `agent-interop/references/` carries a spec-revision stamp, enforced **mechanically** | `test/validate.py` gains the check and fails without it | open |
| REQ-011 | A negative self-test proves REQ-010's check can fail — structurally anchored, asserting it planted something (retro #6) | the CI step is watched failing against a planted defect, output quoted | open |
| REQ-012 | Released and installed: `@ssheleg/agent-stack` v0.7.0 and `@ssheleg/make-skill` v0.18.0 on npm; umbrella `skills.json` + both pins updated; local copies refreshed | `npm view <pkg> version`; `git submodule status` with no `+`; installed plugin version read back | open |

---

## Autonomy sweep

| Stage | Settled |
|---|---|
| run-wide model | the session's model, confirmed once, used throughout |
| run-wide pacing | `run.loop` off (D-7) |
| run-wide escalation | decide alone inside these repositories; the only outward acts are those D-4 names, and they are authorized |
| 0 harvest | this repo, `make-skill`, the family board and retro, the wiki. Stage 9 may write the wiki and this repo's docs; `sshlg-skills` gets a commit for the pin, which D-4 authorizes |
| 0 duplicates | the shipped copy is `plugins/agent-stack/skills/` — named by `marketplace.json` `source` and by `test/validate.py:130`, quoted rather than inferred. `bin/agent-stack.js:78-82` **enumerates the directory** rather than naming skills, so a third skill needs no installer change; the CI functional test at `.github/workflows/validate.yml:129-131` does name files and must be checked |
| 0 fixtures | nothing persists between runs; CI installs into a throwaway `HOME=/tmp/fakehome` |
| 0 source | `git rev-list --count HEAD..@{u}` = 0 on `agent-stack`; re-checked on `make-skill` before its first edit |
| 0 work-list | family board — `grep -n '^| B-' ~/DATA/sshlg-skills/docs/evidence/backlog.md`. This repo gets its own ledgers seeded, which closes B-30's instance here |
| 0 setup audit | declined — no documentation exists to audit; this run creates the first |
| 0 docs regime | decision home: this brief and `docs/evidence/`. No lease mechanism (`.claude/agent-sync.json` absent) → **ungated**. Gate: `python3 test/validate.py`, ratchet = its printed check count |
| 1 docs | the operator's 17 URLs, plus `specification/latest` and `llms.txt`. No private docs |
| 2 decompose | one module, not a platform. Deploy once at the end |
| 2–3 spec | **no UI.** `super-ux` declined: a `SKILL.md` is read by an agent runtime, not by a product user, so there is no scenario to trace. `copywriting` declined: README and CHANGELOG are developer docs, explicitly outside its boundary. `sheleg-design` not applicable. All three declines recorded here rather than left silent |
| 3 design surface | n/a — no visual layer |
| 4–5 dev | base `main`; branch `feat/agent-interop` in each repo; `main` is not edited directly; conventional commits; PR per repo; tracker = the family board |
| 5 integration | PR → merge to `main` (D-4). No parallel fan-out — one module |
| 6 tests | `python3 test/validate.py` plus every negative self-test in `.github/workflows/validate.yml`, run locally before the push. Green = validator exits 0 **and** every plant is watched failing. No known-red baseline |
| 7 lint+deploy | no separate linter; `claude plugin validate --strict` is the conformance gate. Deploy = tag → `release.yml` → npm. Authorized by D-4 |
| 8 post-deploy | `npm view` for the published version; the packed tarball inspected for the new skill's files; the local install read back |
| 9 docs+wiki | README, CHANGELOG, the wiki page (stale, listed above). **Code graph: not refreshed** — no `graphify-out/` in this repo, and B-24 records that the tool cannot run on this machine for want of an API key. Stated, not implied |
| 10 acceptance | the operator signs off; deferred rows go to the family board with ids |

## Done criteria

Every REQ row verified by the check its own row names, with the evidence quoted; both
packages published and read back; both pins moved and the umbrella clean; the carry-over
ledger empty of `open` rows or every survivor carrying a board id.

## Open assumptions

- That `release.yml` in `make-skill` behaves as `agent-stack`'s does. **Unverified at
  freeze time** — checked before stage 7, not assumed.
- That the four "neighbour" standards still exist under the names this run gives them.
  Each is fetched at stage 1; any that does not resolve is dropped from the map with a
  line saying so, rather than described from memory.
