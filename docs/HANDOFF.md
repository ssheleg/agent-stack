# Current work — published agent-stack 0.27.2

R30 owner-board and release-ancestry gates are merged and published as0.27.2,
source `792e3f6cb2e46517f0187066db55edc63ae7d12c`. All four release jobs passed,
and all44 npm payload files matched that source. The
[release packet](evidence/runs/2026-10-13-release-0.27.2.md#published-readback)
is the durable entry with exact sources, gates and limitations.

Exact next task: coordinator pins0.27.2 in the next family release and verifies
installed files. B-161 source/publication scope is closed; the family-wide R30
and native runtime remain distinct. Preserve foreign worktrees and old tags.
