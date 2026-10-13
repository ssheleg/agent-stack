# Current work — bounded restart correction after published0.28.1

Agent-stack0.28.1 source `cd6421b8ca7d9440bc87e366ebd8a96bb38b69b8` is published,
but independent review found the restart instruction overbroad. The current
[restart correction packet](evidence/runs/2026-10-13-restart-boundaries.md) owns
scope, counterexamples, checks, remaining gates and the exact next action.

Next: independent review of this bounded doctrine diff and its instruction-only
checks. Then coordinate one owner aggregate, normal integration and a successor
patch release; do not change either existing0.28.0 or0.28.1 tag. Hub keeps its
accepted0.27.2 pin until the correction is accepted and published. No native retry
mechanism or model behavior is claimed by these documentation tests.

Earlier0.27.2 source/publication evidence remains in the
[release packet](evidence/runs/2026-10-13-release-0.27.2.md#published-readback).
