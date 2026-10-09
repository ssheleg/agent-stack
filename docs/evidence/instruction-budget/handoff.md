# Instruction budget candidate handoff

## Objective and result

Add reusable instruction cleanup guidance and a bounded measurement tool to
agent-harness. The baseline is agent-stack
`07d8fc8a6a0ac56ef389e96b093def101367e4f1` (0.25.3); this candidate is 0.25.4.
The [spec](spec.md) defines the contract before implementation.

The new reference is linked directly from the skill with a load trigger. The
body retains the eager-import gotcha. The checker reports Unicode code points,
bytes, lines, hashes, declared import edges and duplicate contents; its inputs
are explicit roots and an import allowlist. It never reads an unlisted import
or prints source bodies. MEASURED is an accounting result, not a host load or
semantic adherence claim. No private operational inputs are stored here.

## Validation actually run

- `python3 test/audit_regressions/instruction_budget.py`: 14 synthetic tests pass.
- `npm test`: exit 0, including structural checks, planted validator defects,
  installer fixtures, all discovered audit regressions and the new checker tests.
- `claude plugin validate . --strict`: PASS.
- `claude plugin validate plugins/agent-stack --strict`: PASS.
- make-skill `audit_skill.py` on agent-harness with `--house`: 0 GAP, 19 PASS;
  body 206 lines / 3052 cl100k_base tokens; description 961 characters.
- `git diff --check`: exit 0.

The first test run exposed an incorrect test expectation for macOS's /var
symlink; fixtures now compare canonical paths. The structural gate exposed a
forgotten SKILL-CARD version and Python import cache produced by the test; the
card is synchronized and the regression disables bytecode generation before
importing the shipped script. Both checks were rerun successfully.

## Boundaries and next task

Independent review and release are pending. Actual host-load observation,
behavioral requirement replay and model quality/latency comparisons are NOT_RUN
for this synthetic public package change. Local instruction cleanup belongs to
the operator's private records, not this repository.

The next task is independent review of this source and synthetic tests. Then run
normal PR/release policy, install the published package, verify its bytes and move
the umbrella pin in the same session. Do not claim a running session reloaded
from a filesystem checksum. Do not modify global routers or authentication state.
