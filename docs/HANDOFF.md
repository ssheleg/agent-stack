## 0.30.2 released and pinned (2026-10-22)

- **State.** agent-stack 0.30.2 is tagged, on npm and pinned by sshlg-skills 1.73.2; installed on the operator machine.
- **Next task.** B-156: give the per-reply `degraded` / `human_steps` envelope a contract home.

## v0.30.2: the ledger records the shipped version (2026-10-22)

- **Objective.** Record the shipped version in the verification ledger (the sshlg-skills validator reads it).
- **Done.** Ledger entry v0.30.2.
- **Next task.** After merge: tag `v0.30.2`, watch the release run, then the sshlg-skills pin bump.

## v0.30.1: no citations into a private repository (2026-10-22)

- **Objective.** Remove citations into a private repository from shipped doctrine (operator, 2026-10-22).
- **Done.** `gateway.md` names the authority record without its private path; version 0.30.1.
- **Next task.** After merge: tag `v0.30.1`, watch the release run, then the sshlg-skills pin bump.

# Short descriptions: v0.30.0, 2026-10-20

Branch `desc-budget-1020`. The four descriptions went from 929 to 939 characters to
368 to 458 (3,742 to 1,693 in total), because the operator's skill listing was full and
81 skills showed no description. Removed trigger phrases live verbatim under
`## Triggers` in each SKILL.md. `test/validate.py` ratchet 940 to 500, plus a
"Not for" check. Gate: `npm test` alone, exit 0.

Next: none here; the hub re-pins 0.30.0 in its own change.

---

# FEED-SEO-1019 wave 6: v0.29.0, 2026-10-19

Objective: an agent-safety incident checklist with primary sources, the eval
solvability rule, and owed fixture rows that have a primary source.
Done on `feat/feed-1019`: the incident checklist in
`agent-orchestrator/references/governance.md` (six rows), the solvability rule
and checklist line in `agent-evals/SKILL.md` §6, the "Goal met through a
prohibited effect" seed case in `agent-evals/references/multi-agent.md`, and
`check_sourced_safety_rows_keep_their_sources` in `test/validate.py`.
Evidence: the v0.29.0 section of [verification.md](evidence/verification.md).
Decisions: claims without a vendor or researcher primary source stayed out (a
visa-application count known only from news reports, a paywall bypass the vendor
post does not describe, a screen-only long-run fixture with no primary source).
Open: the long-horizon recovery fixture still has no primary source; the seeded
cases are text, not executed trials.
Next: release v0.29.0 (PR, merge, annotated tag, release run, npm readback, hub pin).

---

# Current source acceptance — 2026-10-13

B-159's named SEO source gaps are closed by accepted SEO main1e86edf and its
complete gate; [closure evidence](evidence/runs/2026-10-13-fw01-referral-closure.md)
preserves every original row and the limits. This owner scanner correction
merged atb332a92 through [normal checks](evidence/runs/2026-10-13-fw01-discovery/normal-integration.json).
Published package0.28.2 bytes remain unchanged; source-test acceptance does not
claim new installed behavior.

Next: coordinator integrates this docs-only reconciliation after peer and
genuine checks, then continues the existing native/runtime and family-wave
prerequisites. Earlier entries below are dated history, not current instructions.

---

# FW01 source discovery correction — 2026-10-13

The [source packet and receipt](evidence/runs/2026-10-13-fw01-discovery/README.md)
records actual healthy/readable/unreadable baseline evidence and the bounded
permission-error fix. New focused controls pass; source payload and version stay
unchanged. Next: independent review, serialized owner aggregate and genuine normal
PR admission. No full-scan/runtime completeness, publication or installation claim.

---

# FW00 referral dispositions — 2026-10-13

[Current packet](evidence/runs/2026-10-13-fw00-referrals.md) closes only B-160's
accepted source-lint port and retains B-159 as partial/open. Next: accept SEO's
remaining scanner through its owner, then reconcile B-159 with source evidence.
This docs-only change requires focused checks, peer review and normal PR admission.

---

# Current work — agent-stack 0.28.2 published

The bounded restart correction is published from accepted source
[`2b3d769775e368d0a1e6d0f20ea095ae24fbbd54`](https://github.com/ssheleg/agent-stack/commit/2b3d769775e368d0a1e6d0f20ea095ae24fbbd54)
as annotated tag `v0.28.2`. The [publication receipt](evidence/runs/2026-10-13-release-0.28.2.md#published-readback)
records exact candidate and accepted-main local full checks, genuine PR checks,
all four successful release jobs, registry integrity and 44 matching payload files.
Historical v0.28.0 and v0.28.1 tags remain unchanged.

The [restart correction packet](evidence/runs/2026-10-13-restart-boundaries.md)
and [independent source review](https://github.com/ssheleg/sshlg-skills/blob/82310a56309932f5d51b40e3dcdd2801db99a296/docs/evidence/completion-1013/agent-stack-restart-peer.json)
own the doctrine boundary. Text/structural checks and publication do not prove a
native agent followed the instruction or that provider timing/cache outcomes occurred.

Next: the hub coordinator updates its accepted member pin and performs separately
recorded installed readback. This owner task made no machine apply. Remaining owner
board/runtime prerequisites remain open; publication alone does not close them.
Earlier 0.27.2 evidence remains in its [release packet](evidence/runs/2026-10-13-release-0.27.2.md#published-readback).
