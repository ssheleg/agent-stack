# Brief — Pi as the harness doctrine's worked implementation

**Run:** 2026-08-15 · **Repo:** `ssheleg/agent-stack` (+ umbrella pin) · **Artifact root:** `docs/evidence/`

## Scope

`agent-harness` states rules. Nothing in the family shows those rules **implemented** by a
real harness. Pi is small enough to read and complete enough to have made each decision in
public, so this run adds it as the worked example — and, per the operator's call, as
*mechanism ↔ rule* rather than as a second copy of `pi.dev`.

Out of scope: `agent-orchestrator` (body still over budget, C-01 from the previous run);
`seo-aeo-audit`'s lagging pin (this run never executed its gate).

## Source ledger

| Source | Freshness |
|---|---|
| `pi.dev/docs/latest` — quickstart, usage, providers, security, containerization, settings, sessions, compaction, extensions, skills, prompt-templates, packages, custom-provider, sdk, rpc, json, session-format | read 2026-08-15, **all 16 verified `200`** |
| `github.com/earendil-works/pi/tree/main/packages/coding-agent` | read 2026-08-15 |
| `agent-harness` v0.8.0 — 5 references, `layers.md` already named Pi | current |
| `~/.agents/skills/` — 72 entries, family skills present with required front matter | measured 2026-08-15 |

## Locked decisions

| # | Decision | Why |
|---|---|---|
| D-1 | **Mechanism ↔ rule**, not documentation | Operator's call. A retelling of `pi.dev` is stale on arrival and adds nothing a reader could not get from the source |
| D-2 | **Two references**, `pi.md` (harness) and `pi-sdk.md` (programmable) | 16 pages of material; one file would be unreadable and would mix "what it is" with "how to build on it" |
| D-3 | Release to the end: npm, umbrella pin, local installs | Operator's call; the umbrella was measured calm first (no drift, no leases held) |
| D-4 | Divergences from this pack's doctrine are **named, not smoothed** | A worked example that hides where it disagrees teaches the wrong lesson |

## REQ table

| ID | Requirement | Verified by |
|---|---|---|
| REQ-001 | Two references ship, stamped, gate green | `validate.py` → 10 checks / 4 skills; 7 of 7 references stamped |
| REQ-002 | Each Pi mechanism names the rule it implements | sessions→runtime, compaction→ladder, trust→layers, seams→governance/tools |
| REQ-003 | The programmable surface: SDK, RPC, JSON, ExtensionAPI, custom providers | `pi-sdk.md` |
| REQ-004 | The eight seams named, with what each implements | table in `pi-sdk.md` |
| REQ-005 | Divergences from the pack stated | *Where Pi and this pack's doctrine differ* in `pi.md` |
| REQ-006 | Every named doc page resolves | 16 of 16 → `200`; the 2 non-resolving URLs are placeholders inside examples, stated as such |
| REQ-007 | The `~/.agents/skills` claim carries its limit | recorded as a fact about path + front matter, **not** an observed load; Pi not installed here |
| REQ-008 | Budgets held | body 150 ln / ~2235 tok; description 807/1024 |
| REQ-009 | Negative self-tests against the new files | 3 plants watched failing |
| REQ-010 | Released and pinned | npm 0.9.0; umbrella pin, `skills.json`, README; local install read back |
