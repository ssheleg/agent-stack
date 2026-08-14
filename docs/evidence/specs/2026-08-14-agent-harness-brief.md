# Brief — `agent-harness`: the prompt and harness layer, and auditing somebody else's

**Run:** 2026-08-14 · **Repo:** `ssheleg/agent-stack` (only) · **Artifact root:** `docs/evidence/`

## Scope

The pack can build an agent's *mechanics* (`agent-orchestrator`), prove it *behaves*
(`agent-evals`), and connect it to *other processes* (`agent-interop`). Nothing in it says
**what to write in the system prompt, how to shape a tool so the model uses it, which
named technique survives contact with production, or how to audit an agent system somebody
else built.** This run adds that layer.

Out of scope, said out loud: no change to `agent-orchestrator` — its body is **489 lines /
~4761 tokens**, already past the 4750 working limit, so it cannot absorb a paragraph, let
alone a section. The umbrella pin is **not** moved (D-3).

## Phase-1 source ledger

| Source | What it gives | Freshness |
|---|---|---|
| `promptingguide.ai` — agents/*, techniques/*, guides/reasoning-llms | technique catalogue, agent components, deep agents, reasoning-model differences | read 2026-08-14 |
| Anthropic *Building effective agents* | the five workflow patterns; simplicity, transparency, ACI, poka-yoke | read 2026-08-14 |
| Anthropic *Writing tools for agents* | five tool principles: few tools, namespacing, meaningful context, token efficiency, descriptions | read 2026-08-14 |
| Anthropic *Effective context engineering* | right altitude, just-in-time retrieval, compaction, structured note-taking, sub-agent 1–2k summaries | read 2026-08-14 |
| Gist `AIMOWAY/bd8007c8` | the layer question — kernel/harness vs workbench vs coding agent; permission boundaries delegated to the environment | read 2026-08-14 |
| `agent-orchestrator` + 5 references | loop mechanics, **compaction**, runtime, governance, memory models, billing — the prompt layer is 33 lines of code assembly in §10 | current |
| `agent-evals` (215 ln, 0 refs) | measures behaviour; does not audit construction | current |
| `agent-interop` (158 ln, 6 refs) | the wire between processes | current |
| Family board | 15 open rows; none blocks this | 2026-08-14 |

**Divergence found:** `agent-orchestrator`'s body is over the working budget. Recorded, not
fixed here — fixing it means evicting content, which is its own change.

## Locked decisions

| # | Decision | Why |
|---|---|---|
| D-1 | A **fourth skill** `agent-harness`, audit inside it | Measured: `agent-orchestrator` 489 ln / 4761 tok is past the working limit; all three descriptions sit at 911–930/1024. Audit and construction are two readings of one checklist — splitting them makes two homes for one fact |
| D-2 | Audit ships **doctrine + a mechanical scanner** that declares its own blind spots | Operator's call. A doc-only audit is a different audit each time it runs |
| D-3 | Release the **member only** — npm yes, umbrella pin no | Operator's call. A neighbouring session holds an uncommitted seven-pin sweep; instruction #5 says re-measure and say so rather than push into a moving sweep |
| D-4 | Technique catalogue is **broad, with a verdict each** | Convention, matching the operator's choice on the interop run. An unnamed neighbour is where an agent improvises |
| D-5 | Every reference carries `**Spec pinned:** … · read <date>` | `PROTOCOL_PINNED` already enforces this for `agent-interop`; this skill documents somebody else's fast-moving guidance, so it opts in too |

## REQ table — frozen

| ID | Requirement | Verified by | Status |
|---|---|---|---|
| REQ-001 | `agent-harness` ships as a fourth skill and conforms | `validate.py` prints `4 skill(s)`; `claude plugin validate --strict` | open |
| REQ-002 | The system-prompt layer: right altitude, what belongs, status vocabulary, dynamic context, flexible-vs-rigid, reasoning-model differences | `grep` `references/system-prompt.md` | open |
| REQ-003 | The tool layer (ACI): few tools, namespacing, descriptions, meaningful context, token efficiency, errors that teach, poka-yoke | `grep` `references/tools.md` | open |
| REQ-004 | Technique catalogue with a verdict each, production-first | `references/techniques.md` — every entry has a verdict cell | open |
| REQ-005 | Workflow-vs-agent decision and the five workflow patterns | table in `SKILL.md` | open |
| REQ-006 | Harness layering: what a harness owns, and what it delegates | `references/layers.md` | open |
| REQ-007 | Audit: tracks, evidence tiers, a prioritized plan — not a score | `references/audit.md` | open |
| REQ-008 | `scripts/audit_agent.py` finds mechanical defects **and prints what it cannot see** | run against a planted fixture; blind-spot list printed | open |
| REQ-009 | Boundaries stated against all three sibling skills | `grep` `SKILL.md` | open |
| REQ-010 | Every reference carries a revision stamp; the validator enforces it | `PROTOCOL_PINNED` gains `agent-harness`; gate green | open |
| REQ-011 | A negative self-test proves the scanner can fail | watched failing against a planted defect | open |
| REQ-012 | Released: `@ssheleg/agent-stack` v0.8.0 on npm, read back | `npm view`; `npm pack` + `tar tzf` | open |

## Autonomy sweep — what differs from the last run

Branch `feat/agent-harness` off `main` (v0.7.2); gate `python3 test/validate.py` + the
repo's negative self-tests; deploy = tag → `release.yml` → npm, authorized by D-3; **the
umbrella is not touched**; no UI, so `super-ux`, `copywriting` and `sheleg-design` are
declined as before; graph not refreshed (B-24, family-wide).

## Carry-over opened at stage 0

| # | What | Home |
|---|---|---|
| C-01 | `agent-orchestrator` body is past the working token budget (4761 / 4750) | board, after this run |
| C-02 | The umbrella pin for v0.8.0 is left to the neighbouring sweep | operator |
| C-03 | `agent-sync` collision from the previous run (my 1.10.1 vs their uncommitted 1.11.0) is unresolved | operator |
