<sub>ssheleg skills — agent-harness · make-skill · task-pipeline · agent-sync</sub>

# ECC → ssheleg harness: selective adoption ledger

Research date: 2026-09-21. Owner: agent-stack / agent-harness. Task packet:
[bounded brief](../specs/2026-09-21-ecc-harness-brief.md).

## Source boundary

ECC was cloned read-only from `https://github.com/affaan-m/ECC` at
[`2b6e839771e53096d8451a213d40dc64ec8acac0`](https://github.com/affaan-m/ECC/tree/2b6e839771e53096d8451a213d40dc64ec8acac0).
Its package declares 2.2.2. The source ledger below names exact files and SHA-256
values. Source observations are **static inspection**, not execution results.
No ECC installer, hook, test, package installation or background observer ran.
The wider repository was inventoried by paths; it was not audited in full.

ECC root LICENSE: MIT, Copyright (c) 2026 Affaan Mustafa. The selected files show
no separate license headers overriding it. This change adapts methods in newly
written prose; no implementation, schema, command text or substantial upstream
text is copied. Do not infer the same review for uninspected assets/subtrees.

Local baseline: agent-stack
[`c681ef3af6157d13becf53250373b418cca6c919`](https://github.com/ssheleg/agent-stack/tree/c681ef3af6157d13becf53250373b418cca6c919).
Family comparison: sshlg-skills
[`564d1f42a895abb8f0f53417695414b74dbf91a5`](https://github.com/ssheleg/sshlg-skills/tree/564d1f42a895abb8f0f53417695414b74dbf91a5),
README and `lib/lifecycle.js` read. This is a selected-contract comparison, not a
whole-project audit or a benchmark between the two projects.

## Narrative recommendation

**The ssheleg harness is an operating layer for agent work.** It routes work to
specialist skills, carries tasks through explicit contracts, preserves evidence
and resume context, and exposes what is installed and actually loaded. The skill
family is its expertise layer. Project Observatory can be its optional observation
component once its own readiness and privacy checks pass.

The host owns model execution and tool permissions. The harness does not promise
sandboxing, universal hook support or complete leak prevention. Observatory's
credential requirements and private state are separate from the skills' runtime
requirements. Avoid calling this a replacement for Claude Code, Codex or other
agent hosts. Avoid publishing vendor leak counts without reviewed evidence.

## Borrow / adapt / reject

| Method | Verdict and reason | Family owner / destination | Evidence |
|---|---|---|---|
| Explicit managed install state, preservation of unowned files | **Adapt.** A skipped write must not grant uninstall ownership. Keep user changes visible. | Installer owner + make-skill; contract in new reference | ECC ownership guard; lifecycle inspection |
| Installed versus loaded status | **Retain existing family contract.** ECC doctor diagnoses managed files; family already distinguishes disk and reload receipts. No second store. | sshlg-skills lifecycle | ECC doctor; local `lib/lifecycle.js` |
| Hook profiles and per-hook disable | **Adapt.** Make effective capabilities, effects and failure behavior inspectable. | Host adapter; contract in agent-harness | ECC hook-flags |
| Input caps and subprocess timeout | **Adapt with stronger bounds.** Input bytes alone do not bound stream duration; subprocess timeout does not bound in-process awaits. | Host adapter | ECC hook-input; run-with-flags lines 249–287 |
| Fail-open generic hook exception | **Reject as a universal policy.** A required gate must not silently pass when its check failed. This is a design assessment, not an exploit claim. | Host adapter | run-with-flags lines 267–270 and 303–306 |
| Evidence-bearing save/resume | **Adapt content, retain local format.** Confirmed work, failures and next task are useful; a new global session store would duplicate task-pipeline. | task-pipeline existing handoff | save-session and resume-session |
| Hash-bound eval receipts and fixture-only replay | **Adapt contract.** Bind candidate, taskset and checker; integrity is distinct from correctness. | agent-evals / existing result envelopes | eval-harness receipt, capsule and architecture |
| Arbitrary candidate execution | **Do not import.** ECC itself disables it without verified OS containment. Keep that limitation explicit. | Host/environment security boundary | eval-harness gate opening contract |
| Instinct learning/background observer | **Defer.** Scope, consent, retention, cost and proven improvement need evaluation; do not auto-promote session content globally. | agent-orchestrator memory owner | continuous-learning-v2 SKILL |
| Entire ECC installer, hook bundle and host configs | **Reject wholesale import.** Adds parallel orchestration and unreviewed dependency closure. | Existing family routers remain entry points | Inventory plus bounded task scope |

ECC observations above are grounded in the source files below. Family policy
choices (adapt/reject) are author judgment and await parent review; they are not
measured performance findings. No claim of superiority or outcome improvement.

## Implemented delta and dependency closure

- [Workbench contracts](../../../plugins/agent-stack/skills/agent-harness/references/workbench-contracts.md):
  new on-demand doctrine and nine review cases.
- [Harness entry point](../../../plugins/agent-stack/skills/agent-harness/SKILL.md):
  reference routing and kernel/workbench checklist distinction.
- [Layer reference](../../../plugins/agent-stack/skills/agent-harness/references/layers.md):
  explicit broader workbench meaning, preserving kernel responsibilities.
- README, skill card and synchronized 0.25.0 manifests/changelog.

Runtime additions: none. No new packages, interpreters, services, credentials,
telemetry, foreign scripts, schema stores or automatic downloads. Existing
agent-stack audit script still needs Python as before. Research files are Git
artifacts; only the reference ships inside the skill package.

## Verification limits and next work

Repository tests establish structural/reference/installer regressions. Strict
plugin validation checks manifest conformance. Package inspection confirms the
new reference is included and research/private machine state are not. These do
not measure agent behavior. The nine adapter review cases are design acceptance
criteria; no new adapter is implemented by this prose change.

Before a future runtime transfer: implement in the existing owning module,
freeze representative baseline tasks, exercise no-op/conflict/unsupported-host
and tampered-evidence paths, and record real outcomes under agent-evals. Parent
review and release evidence are recorded in the adjacent handoff.

## Source digest ledger

`sha256(file bytes)` at the pinned ECC commit; line references above resolve there.
Sources marked “selected sections” were not semantically audited end to end.

| Source | SHA-256 | Read scope |
|---|---|---|
| [LICENSE](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/LICENSE) | `326146379f01bb137c0a5d3c54770c1aa31076705c8b88a7f6b26a460f6221b2` | full |
| [package.json](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/package.json) | `650eaa8de580a3c8eadbc658aa5ffe3f8d50ba2be075dd327a62e1d70e1d7a69` | selected sections |
| [scripts/lib/install/ownership-guard.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/install/ownership-guard.js) | `000d8de192edceb32169b8725a797f908256f5a7e124c1803c29328eb07a36cc` | selected sections |
| [scripts/lib/install-lifecycle.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/install-lifecycle.js) | `4814affb0f3ffd3648e62a4987ce21d3a5318f6c8d4f5e2069b01e5ecbe5dfe5` | selected sections |
| [scripts/doctor.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/doctor.js) | `4ec5a1c7fe9124ebeea5d3d939270a16b0974b789558a8a9cc313cf73ec70b6e` | selected sections |
| [scripts/lib/hook-flags.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/hook-flags.js) | `1f5fbf2d2ebd0ab07a3e54406db18c2932ae7bf965513ec12c521da1be54425d` | full |
| [scripts/hooks/hook-input.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/hooks/hook-input.js) | `edae519f794befa4cf1dcbfb3c985d0db6f589342b7036ffb7ace61a9c3868b0` | full |
| [scripts/hooks/run-with-flags.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/hooks/run-with-flags.js) | `a5b3c3f4ed27f1d9d9c607d6819aab9985ad446239ea7d2825d4b040d2d8d87e` | selected sections |
| [commands/save-session.md](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/commands/save-session.md) | `a9488a8819d6c65fe4777f07ea72de6b0c4ee94f90c6bb33b3b8841916222db4` | selected sections |
| [commands/resume-session.md](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/commands/resume-session.md) | `b09bcb22feb10adbba50accd5dd97d09b60897aa94d05c6c12b6e579cb69cbac` | full |
| [scripts/lib/eval-harness/receipt.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/eval-harness/receipt.js) | `eacacccf8a6d06f38e83c8cee1bb3a6c608e9125115a989fd7f8a7f7e371d5e7` | selected sections |
| [scripts/lib/eval-harness/capsule.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/eval-harness/capsule.js) | `fd0bbbde8f383226fbcb093210e0f16594acd9f6ea0ae209e47a37cc39834b0c` | selected sections |
| [scripts/lib/eval-harness/gate.js](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/eval-harness/gate.js) | `76d6613aa7aacb9863c61859d20e554826c6f08e71c10221f0b6fea4d04e3c4f` | selected sections |
| [docs/architecture/eval-harness-frameworks.md](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/docs/architecture/eval-harness-frameworks.md) | `eec9ad255f71f68feb4d5e2ee9b2ececef6cd4dc4d1b246d015f3cc047406a61` | selected sections |
| [skills/continuous-learning-v2/SKILL.md](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/skills/continuous-learning-v2/SKILL.md) | `ddad12451a0d582c6ef1b197b7be193bef613cbc74eba4117fcb74fc7a4ecd00` | selected sections |

---

**Made with [ssheleg skills](https://github.com/ssheleg/sshlg-skills)**

- [`agent-harness`](https://github.com/ssheleg/agent-stack) — workbench contracts and ECC comparison
- [`make-skill`](https://github.com/ssheleg/make-skill) — attribution and package checks
- [`task-pipeline`](https://github.com/ssheleg/task-pipeline) — bounded brief and handoff
- [`agent-sync`](https://github.com/ssheleg/agent-sync) — local claims for shared metadata
