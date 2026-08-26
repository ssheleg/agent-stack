# Skill Card — agent-stack

## Identity

| Field | Value |
|---|---|
| Pack | `agent-stack` |
| Version | `0.13.4` |
| Skills | `agent-orchestrator`, `agent-evals`, `agent-interop`, `agent-harness` |
| License | MIT |
| Source | https://github.com/ssheleg/agent-stack |

## Job and boundary

Build and evaluate agent systems: the orchestration loop, work graph, harness,
eval suite and outward protocols. It does not coordinate coding agents editing
this repository, wire product payments or redesign a user interface.

## Inputs and outputs

Inputs are an agent-system requirement, existing prompt/tool surface, protocol
boundary or evaluation target. Outputs are architecture and implementation
guidance, audit findings and evaluation artifacts in the user's repository.
The pack does not operate a hosted service or ship credentials.

## Runtime and trust

The skills are Markdown plus bundled references and deterministic fixtures.
Some workflows may ask the user's normal development tools to inspect or change
their repository. Protocol claims carry their specification revision. External
systems are contacted only when the user-authorized implementation itself needs
them.

## Distribution

Install from npm/GitHub through the repository installer, from the Agent Skills
CLI, or as the `agent-stack` Claude Code plugin. Manifests and package versions
are checked together before release.

## Verification

- Repository validator: `python3 test/validate.py`
- House audit: pinned `make-skill` auditor in `validate.yml`
- Behavioral data: `test/evals/`
- Evaluation status: designed and schema-validated; no model run is claimed in
  `test/evals/RESULTS.md`

## Known limits

The pack provides production patterns, not a provider-agnostic hosted runtime.
Protocol references age and must be rechecked against their pinned revision
before a compatibility claim is extended.

