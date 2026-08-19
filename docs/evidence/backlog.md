# Board — agent-stack

What this repository knows it owes, in one place. The companion file is
`docs/evidence/verification.md`: this board says what is outstanding, the ledger says what
shipped and what confirmed it. A row leaves this board only when a ledger row can point at
the command that closed it.

**Priority is computed, not felt** — `P = blast × (1 + age_runs) / effort`, with *blast* 3
for a user of the pack, 2 for the operator of this machine, 1 for a future run of this
repository; *age_runs* in distinct days carrying a run stamp; *effort* 1 under an hour, 2 a
session, 3 its own run. The method's home is the umbrella board
(`sshlg-skills/docs/evidence/backlog.md`), which also carries why age counts days rather
than stamps and why `waived` is a state rather than a flavour of open. Not restated here.

**Ids.** `B-NN` rows are this repository's own debt. `AG-NN` rows come from the
cross-repository manifesto-conformance program, whose *program* state (which agent, which
wave) lives in `sshlg-skills/docs/evidence/manifesto-conformance.md` — that file is the
single home for the program, this one for the member's debt, cross-referenced by id. One
row per line, appended, so two runs closing two rows do not land on the same line.

| id | What | Source | Blast | Age | Effort | P | Status |
|---|---|---|---|---|---|---|---|
| AG-01 | **The checker contract asked a branch how sure it was and never what it could show.** Manifesto requirement M-25 (`pod-manifesto/manifesto.md:186`) states the checker's contract as *arrived / matches its contract / **carries its evidence** / does not contradict a sibling*. The reference implementation named five items — empty-or-null, mutually-contradictory, off-topic, **under-confident**, malformed — with the confidence signal standing where the evidence item should be, in the pack whose own text says *"an uncalibrated judge is an opinion with a number attached"* (`agent-evals/SKILL.md:154`) and *"never a classifier's confidence"* (`agent-orchestrator/references/governance.md:53-55`). *Arrived* was half-covered too: no arrival count, so a branch that never returned was caught only when the host happened to resolve its slot to `null`. | 2026-08-18 manifesto-conformance audit, row AG-01 (M-25) | 3 | 0 | 2 | **1.5** | **closed 2026-08-19** — contract now six mandatory items with `unevidenced` third and `missing` first (an arrival count); the confidence signal is kept and demoted, with the pack's own two arguments cited rather than a new one invented. Both homes declare the list machine-readably and `test/validate.py` compares them; three negative self-tests in `validate.yml` were watched refusing a shrunk list, a dropped evidence item and a diverged mirror, each with `plant_guard.py verify` confirming the plant landed. `npm test`, `test/validate.py` and `audit_agent.py --self-test` all exit 0. |
