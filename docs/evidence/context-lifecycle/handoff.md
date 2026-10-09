<sub>ssheleg skills — task-pipeline · make-skill · agent-harness · agent-sync</sub>

# CR-2 — context lifecycle candidate

## Objective and completed scope

Baseline: `7f0c2f942ded0c8922650883db7347d2cc695577`, agent-stack 0.25.4.
Candidate branch: `codex/context-lifecycle-20261009`, version 0.25.5.
[Requirements, frozen cases and primary source receipts](spec.md) are the task
entry and shared contract. This bounded change adds one on-demand harness
reference and direct trigger. It admits scoped, dated evidence, separates current
pointers from immutable history, preserves uncertainty/authority in compact
packets and sets an evidence gate for research-to-skill promotion.

Existing orchestrator memory expiry, confidence, supersession and compaction
remain their own contracts. The same patch removes the harness's unscoped ARC
headline and unsupported ranking of prompt gains from active guidance. The
primary benchmark was found, scoped and preserved in the spec; old verification
rows are historical and were not rewritten. README and narrow prompt/tool
reference assertions follow the corrected scope.

## Checks actually run

- `npm test`: exit 0, native structural validator, planted-defect guard tests,
  installer fixtures and all discovered audit regressions. No new executable
  behavior was added; no mirrored prose assertions were added as tests.
- `claude plugin validate . --strict`: exit 0, Validation passed.
- `claude plugin validate plugins/agent-stack --strict`: exit 0, Validation passed.
- make-skill `audit_skill.py .../agent-harness --house`: 19 PASS, 0 GAP;
  its native counter reports 202 lines / 2958 cl100k_base tokens, down from
  206 / 3052 at baseline. Description remains 961 characters.
- An independent stripped-body counter reports 204→200 lines and 3050→2956
  cl100k_base tokens. The two-token/two-line difference is surrounding whitespace;
  both counters show a 94-token reduction. Metadata compared byte-for-byte equal.
- `npm pack --dry-run --json`: new reference appears in the publishable payload.
- `git diff --check`: exit 0. No private sources, paths or host configuration are
  included in the task-owned diff.
- Observatory local update check: no applicable update output for this worktree.
  No revision acknowledgement was claimed.
- agent-sync: local advisory CR-2 and per-file resource claims obtained before
  guarded edits. This is not cross-machine enforcement.

## Manual counterexamples and limits

These are content review outcomes, not executed model behavior:

| Input | Candidate instruction and observed review result |
|---|---|
| Copied old deployment summary | Dates/card and admission step 3 retain original observation date; covered |
| New experiment conflicts with accepted decision | Current/history section separates authority from observation; covered |
| Deployment changes under current pointer | Revisit triggers require scoped recheck and historical preservation; covered |
| Source inaccessible or contradictory | Admission step 4 retains uncertainty and missing resolution evidence; covered |
| Private incident becomes public rule | Promotion step 5 requires publishable support and synthetic examples; covered |
| Old stable fact remains applicable | Admission step 3 permits scoped stability; covered |
| Source text claims permission | Admission step 2 denies authority transfer; covered |
| Compact packet would drop owner veto or prerequisite | Packet section requires split/retrieval before dependent action; covered |
| Summary claims an observed effect | Packet section separates observed, inferred and proposed; covered |

Live behavioral replay, model quality/latency, host-load observation and archive
mutation are NOT_RUN. A stamped source date is not semantic enforcement. The
new reference is policy and a manual procedure, with explicit missing-source,
missing-host and no-memory-write-authority fallbacks.

## Open work and exact next task

Independent root review must ACCEPT this candidate before merge/tag/publication.
After review, use the existing trusted tag release, verify registry integrity and
record exact source SHA/version. Parent owns hub pin and family updater; do not
claim install/load acceptance from package publication. No outstanding runtime or
private-memory edits belong to this branch.

Incidental out-of-scope finding: CONTRIBUTING.md contains legacy SEO-oriented
examples and names `test/test_page_audit.py`, absent in this tree. Native checks
above come from package.json. A separate documentation cleanup should repair
that contributor entry; this task does not claim a whole-repository audit.

---

**Made with [ssheleg skills](https://github.com/ssheleg/sshlg-skills)**

- [`task-pipeline`](https://github.com/ssheleg/task-pipeline) — bounded requirements and acceptance
- [`make-skill`](https://github.com/ssheleg/make-skill) — skill structure budgets and release checks
- [`agent-harness`](https://github.com/ssheleg/agent-stack) — context admission procedure
- [`agent-sync`](https://github.com/ssheleg/agent-sync) — advisory local claims
