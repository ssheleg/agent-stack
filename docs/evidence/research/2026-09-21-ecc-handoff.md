# Agent-stack ECC transfer — handoff

Objective: improve the agent-engineering component of the ssheleg harness with
selective ECC methods, keeping existing family contracts and runtime boundaries.

Entry point: [research and transfer matrix](2026-09-21-ecc-harness.md).
Task packet: [scope, dependencies and checks](../specs/2026-09-21-ecc-harness-brief.md).

## Completed

Implementation commit:
[`3456965577a19ee3b44816b593304a8c8a0970cc`](https://github.com/ssheleg/agent-stack/commit/3456965577a19ee3b44816b593304a8c8a0970cc).
Branch: `codex/ecc-harness-contracts`. Prepared version: **0.25.0**.
The commit link becomes remotely accessible only after the parent pushes it.

- New workbench contract reference with install ownership, hook bounds and
  failure semantics, durable handoff, artifact-bound eval evidence and observation
  limits; linked from the skill and layers reference.
- README positions this pack within the ssheleg agent harness; all release version
  surfaces synchronized, including the skill card and changelog.
- ECC pinned with 15 file digests, selected-read scope, attribution and a
  borrow/adapt/reject matrix. No ECC executable code or runtime dependency added.

## Checks actually run

| Check | Observed result |
|---|---|
| `npm test` | EXIT=0: structural checks, plant guard 9 cases, installer 11 cases, audit regressions green |
| `python3 test/validate.py` after final reference TOC correction | EXIT=0, 15 checks, v0.25.0 |
| `claude plugin validate . --strict` | EXIT=0, marketplace passed |
| `claude plugin validate ./plugins/agent-stack --strict` | EXIT=0, plugin passed |
| make-skill `audit_skill.py plugins/agent-stack/skills/agent-harness --house --quiet` | First run reported missing reference TOC; corrected; final 0 GAP, 19 PASS |
| `npm pack --dry-run --json` | 40 files; new reference included; research, `.env`, `.agent-sync` and `.git` absent |
| SHA-256 ledger comparison | All 15 pinned source hashes matched |
| Relative-link inspection of brief/research | All Markdown relative links resolved |
| `git diff --check` | EXIT=0 |

The repository validator reports one unavailable check: strict family front-matter
reader is not found above this standalone checkout. The make-skill house auditor
ran separately. No behavioral model evaluation was run; structural checks do not
prove improved outcomes. The nine review cases are contract criteria, not executed
new-adapter tests. No deployment or npm publication has occurred in this packet.

## Decisions and open work

- Reuse task-pipeline packets, agent-sync coordination and family lifecycle
  receipts; do not create another session store or global observer.
- Distinguish kernel and workbench harness meanings. Host capabilities and
  missing enforcement stay visible.
- Observatory remains an optional integration proposal here. Its open-source
  readiness, actual features and publication belong to the parent program.
- Parent owns independent semantic/security review, push/integration policy,
  version release, installed-skill refresh, website edits and umbrella pin.

**Exact next task:** independently review the new workbench reference and transfer
matrix against the pinned sources, then push/integrate the reviewed branch under
repository policy. Release 0.25.0 only after that review; update the umbrella pin
and verify the installed/loaded version separately. The prepared change does not
claim those follow-up operations have happened.

Local-only residue: a read-only temporary ECC clone and package inventory JSON
used for research remain outside Git. No credential or private project inventory
was read for this packet. Local advisory coordination claims are released when
this subtask hands back; the pre-existing foreign expired lease is left untouched.

## Release correction

Parent independently reviewed the new reference and authorized publication. PR
#33 checks passed at 331f7eb. The initial merge method was rejected by GitHub,
but a shell command sequence incorrectly continued and tagged the old c681ef3
commit as v0.25.0. The queued release run 35584412545 was cancelled before
publication. Repository rules refused deletion; no rules were bypassed and no
force push was used. The immutable incorrect tag is preserved. Publication now
targets **0.25.1** with the same reviewed content and this explicit correction.
Future merge, head verification, tag creation and tag push are separate checked
operations; a failed step cannot continue to the next mutation.

## Published verification — supersedes pending release notes above

Published **@ssheleg/agent-stack 0.25.1**, through
[PR #33](https://github.com/ssheleg/agent-stack/pull/33), squash merged at
[`0b76d1afc19c778db0228b1c0f383c2c1d6a9949`](https://github.com/ssheleg/agent-stack/commit/0b76d1afc19c778db0228b1c0f383c2c1d6a9949).
[Release workflow 35584641319](https://github.com/ssheleg/agent-stack/actions/runs/35584641319)
completed with validate, house audit, release and publish all successful.
[GitHub release](https://github.com/ssheleg/agent-stack/releases/tag/v0.25.1).

Observed 2026-09-21:

- Remote annotated tag v0.25.1 peels to the exact merged SHA above.
- Fresh GitHub checkout at that SHA: `npm test` passed; pack inventory contains
  40 files, the new reference, no research ledger or private machine state.
- `npm view @ssheleg/agent-stack@0.25.1 version gitHead dist.integrity --json`
  reports version 0.25.1 and the exact merged SHA.
- Registry tarball downloaded with `npm pack @ssheleg/agent-stack@0.25.1`:
  every one of its 40 regular files matches the fresh checkout byte-for-byte.
- Registry integrity:
  `sha512-FeGZO3AGoRhu0DaHgwNKp8DHf4tT7u3lMS+n/hVc2bWdbP0f6i7prSI7Rzgo8r9WU66FnytUv93UfFEipFAggA==`.
- **v0.25.0 is unreleased.** `npm view @ssheleg/agent-stack@0.25.0 version`
  returns E404; its cancelled workflow has release and publish cancelled. The
  incorrect protected tag remains at c681ef3; do not install from that tag.

Exact next task for the parent program: set the umbrella's agent-stack version
and submodule pin to 0.25.1 / 0b76d1a, then refresh installed skills and separately
check the host's loaded receipt. Those operations belong to the parent and are
not implied by this member publication. The tested research/reference contract
has no new runtime or behavioral-model evaluation result.
