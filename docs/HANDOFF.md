# Current work — agent-stack 0.28.2 release candidate (not published)

Agent-stack0.28.1 source `cd6421b8ca7d9440bc87e366ebd8a96bb38b69b8` is published,
but independent review found the restart instruction overbroad. The current
[restart correction packet](evidence/runs/2026-10-13-restart-boundaries.md) owns
scope, counterexamples, checks, remaining gates and the exact next action.

Independent source review of the doctrine correction passed at
`ff797c6341fe6cdb4d9b0dd2e113f7ebb8f24f6f`, recorded in the hub's
[peer receipt](https://github.com/ssheleg/sshlg-skills/blob/82310a5/docs/evidence/completion-1013/agent-stack-restart-peer.json).
Version metadata now targets 0.28.2; this is not publication evidence.
The [release packet](evidence/runs/2026-10-13-release-0.28.2.md) owns pending gates.

Next: independent metadata review, one coordinated local owner aggregate, normal
exact-head PR checks and merge, then exact accepted-main local full chain before
the annotated tag and release/readback; do not change either existing0.28.0 or0.28.1 tag. Hub keeps its
accepted0.27.2 pin until the correction is accepted and published. No native retry
mechanism or model behavior is claimed by these documentation tests.

Earlier0.27.2 source/publication evidence remains in the
[release packet](evidence/runs/2026-10-13-release-0.27.2.md#published-readback).
