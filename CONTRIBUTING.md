# Contributing

This repository ships agent-orchestrator, agent-evals, agent-interop and
agent-harness: instructions, on-demand references, Python helpers and a Node
installer. Change the smallest contract that owns the behavior.

## Evidence and scope

Distinguish primary-source guidance, locally observed behavior, experiments and
proposals. A fact needs a resolving source or reproducible check; include its
observation/read date and applicable model, version or environment. An upstream
benchmark is not a measured improvement in this package. Preserve contradictory
evidence and report missing checks as NOT_RUN.

Keep historical evidence dated. Update current entry points when their underlying
state changes, linking predecessors instead of silently rewriting old reports.
Task evidence belongs under `docs/evidence/`; include scope, acceptance, checks
actually run, open work and an explicit next step. Update the relevant current
verification rows and README in the same change as the skill behavior.

## Setup and local checks

Use Python 3.9+ and Node 16+ for the local tools. The structural validator can
report token-budget measurement as unavailable when no tokenizer is installed;
that is weaker evidence, not a measured budget pass.

From the repository root:

```bash
npm test
```

`package.json` owns this command: structural validation, planted-defect guard
checks, installer fixtures and the discovered `test/audit_regressions/*.py` tests.
For a focused structural check:

```bash
python3 test/validate.py
```

When the Claude CLI is available, validate both manifests:

```bash
claude plugin validate . --strict
claude plugin validate plugins/agent-stack --strict
```

Those manifest checks do not establish model behavior. When changing executable
helpers, add meaningful positive and negative cases to the existing native tests.
For instruction changes, record frozen counterexamples and distinguish manual
content review from actual baseline/candidate agent replay. Do not add tests that
merely restate every sentence of the new guidance.

Before delivery, also run:

```bash
git diff --check
npm pack --dry-run
```

The pack listing shows what consumers receive; required references must ship and
private configuration or credentials must not. Existing hosted workflows govern
CI and publication. Local checks, hosted checks, registry publication and a
running host loading a skill are separate evidence.

## Where a change belongs

| Concern | Owner |
|---|---|
| Loop, memory storage/retrieval, provider routing | `plugins/agent-stack/skills/agent-orchestrator/` |
| Execution evidence and behavioral evaluation | `plugins/agent-stack/skills/agent-evals/` |
| MCP, A2A, registry and gateway contracts | `plugins/agent-stack/skills/agent-interop/` |
| Instructions, tool wording and harness audit | `plugins/agent-stack/skills/agent-harness/` |
| Installer | `bin/agent-stack.js` and `test/installer_test.js` |
| Structural guard | `test/validate.py` and its planted-defect coverage |
| Task receipts and handoff | `docs/evidence/` |

Add references inside their owning skill directory and link directly from its
`SKILL.md` with a load condition. Keep runtime metadata and bodies within the
house budgets checked by the validator. References in agent-harness and
agent-interop carry the `Spec pinned` revision stamp required by that validator.
A stamp establishes what date is claimed, not that the prose is correct.

## Coordination and release

Read [docs/AGENT_SYNC.md](docs/AGENT_SYNC.md) and the live
`.claude/agent-sync.json` before editing guarded files. Take the configured claim;
state honestly whether coordination is advisory or enforced. Preserve unrelated
work and use a separate branch/worktree for concurrent tasks.

Use conventional commits and a focused pull request. Before a release, synchronize
`package.json`, `.claude-plugin/marketplace.json`,
`plugins/agent-stack/.claude-plugin/plugin.json`, `SKILL-CARD.md` and the top
`CHANGELOG.md` version. Run the native and both strict plugin checks, obtain
independent review, then follow the existing repository integration policy.
The tag-triggered `.github/workflows/release.yml` owns trusted publication;
verify the published registry artifact instead of treating a pushed tag as done.

The [sshlg-skills family](https://github.com/ssheleg/sshlg-skills) pins this member.
Coordinate the member commit/version with its owner so the parent submodule,
manifest and advertised version move together. Family publication and supported
host updates have their own receipts; never claim a running session reloaded
from installed-file checks alone.

## Reporting problems and license

Open non-sensitive issues at
[ssheleg/agent-stack](https://github.com/ssheleg/agent-stack/issues), with the exact
source revision, failing behavior and available evidence. Follow
[SECURITY.md](SECURITY.md) for sensitive reports.

Contributions are licensed under [MIT](LICENSE).

The unrelated SEO contributor instructions replaced here remain available in the
[0.25.4 snapshot](https://github.com/ssheleg/agent-stack/blob/7f0c2f942ded0c8922650883db7347d2cc695577/CONTRIBUTING.md).
