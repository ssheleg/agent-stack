<sub>ssheleg skills — task-pipeline · evidence-docs · agent-sync</sub>

# Bounded restart correction after0.28.1

## Objective and ownership

Preserve the operator's autonomous continuation intent without making a stopped
lane permission to cancel active siblings, duplicate an uncertain outward effect
or retry forever. Baseline is published `cd6421b8ca7d9440bc87e366ebd8a96bb38b69b8`.
The isolated branch owns agent-orchestrator's body/runtime reference, its focused
text regression, current README/handoff/verification and this packet. Task
`RESTART-BOUNDS-1013` uses an advisory local lease; guarded verification resource
was separately acquired. No foreign tree or installed profile is changed.

The independent parent-hub receipt is committed as `5f71ec2` on
`docs/eval-results-1013`, under `docs/evidence/completion-1013/agent-stack-0281-peer.md`.
It verified all44 npm files against baseline Git and all four release jobs at
https://github.com/ssheleg/agent-stack/actions/runs/38355706771.
Publication success did not certify the new doctrine's recovery semantics.

## Frozen counterexamples and intended correction

| Scenario | Baseline instruction path | Corrected boundary |
|---|---|---|
| A hits quota while B awaits an outward response | “stop the workflow” can stop B too | Resume owned stopped A only; whole-workflow recovery needs sibling/in-flight reconciliation and authority. |
| Provider accepted an effect but response/checkpoint is missing | Same run ID/arguments are presented as sufficient recovery | Unknown outcome stays unknown; reconcile attempt/provider receipt or idempotency key before replay. |
| Fixed quota never clears | Backoff continues every15 minutes without a terminal rule | Finite recorded cap/deadline includes host attempts; exhaustion records partial and next step. |
| Retry-After or known reset is later than the suggested next attempt | “restart at once” ignores eligibility | Provider timing is a lower bound unless newer supported evidence changes it; deadline may end the series. |
| Task is cancelled or another worker takes ownership between attempts | Resume-by-ID alone can continue stale work | Recheck current task authority/ownership before each attempt; revoked/exhausted work stops. |
| Stream is quiet while a host request or command remains active | Silence is treated as a restart trigger | Inspect host liveness; no second active owner; ambiguous state gets a watcher. |
| Spend/credit failure or human sign-in required | Existing billing exception is correct | Preserve billing stop and human-only gates; no account/key switching or cap bypass. |
| A stopped transient worker is eligible and authorized | Autonomous continuation is desired | Supported bounded resume proceeds without a new approval question; independent work continues meanwhile. |

These are manual semantic instruction counterexamples, not executed provider or
agent traces. The change supplies doctrine, not a scheduler implementation.
Cache/resume claims are now conditional on the actual host contract; no invented
universal `resume` API or cache guarantee remains. The prior changelog stays an
immutable description of0.28.1; a successor release must explicitly describe the
correction rather than rewrite the old entry.

## Checks actually run

- New `python3 -B test/audit_regressions/restart-boundaries.py` on baseline source:
  exit1 with12 diagnostic clauses. This counts textual omissions/reintroduced
  unsafe claims, not12 independent production defects. Initial exploratory
  checker also demanded a new spelling for the already-present billing exception;
  that redundant assertion was removed before recording this baseline.
- The same checker on corrected source: exit0, candidate contract plus11
  in-memory plants/controls. It removes admission/timing/authority clauses,
  restores unsafe old commands, checks body admission and accepts an unrelated
  wording edit. No temporary tree or provider call. It cannot prove arbitrary
  English semantics or actual model adherence.
- `python3 -B test/validate.py`: exit0,17 structural checks at0.28.1. It explicitly
  reports strict frontmatter cross-reader unlooked in this isolated checkout;
  separate strict native manifest results are recorded below.
- Direct `tiktoken` cl100k_base body measurement:4400 tokens for agent-orchestrator,
  below the4750 working bound. The description is unchanged.
- `claude plugin validate plugins/agent-stack --strict` and
  `claude plugin validate . --strict`: both exit0.

- `npm pack --dry-run --json`: exit0,44 files; runtime reference included and
  docs/test/private coordination paths absent. `git diff --check`: exit0.

Owner aggregate and model replay are **NOT_RUN**; no duplicate broad suite while
the coordinator's serial slot is occupied. Release version remains0.28.1 in this
pre-review correction branch; no successor publication claim yet.

## Exact next task

Independent reviewer reads the body/reference delta against the frozen scenarios
and challenges the text checker with a missing boundary or restored unsafe
command. On acceptance, synchronize a successor patch version in all metadata
homes and add its changelog correction, run the single coordinated owner aggregate
and normal required CI, then release under existing policy and compare the whole
published payload. Parent may advance the hub pin only after that separate
acceptance. Keep the two historical tags unchanged.

---
**Made with [ssheleg skills](https://github.com/ssheleg/sshlg-skills)**:
task-pipeline for bounded delivery; evidence-docs for proof boundaries;
agent-sync for local ownership.
