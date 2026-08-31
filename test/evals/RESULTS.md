# Evaluation results

**Status: executed — first dated rows below (2026-08-31).** CI still proves only
that the files are shaped correctly; the rows are where behavioural claims live,
and each carries the method that produced it.

| Date | Version | Model | Trigger pass rate (train / validation) | Scenario lines passed | Installed alongside | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | superseded: "no run yet" row retired by the rows below |
| 2026-08-31 | 0.17.1 (tree at release candidate) | claude-haiku (Agent-tool `haiku`) | 5/6 train, 6/6 validation (11/12 overall) | s01 4/4 · s02 2/4 · s03 4/4 (10/12 lines) | ssheleg family: make-skill, task-pipeline (+evidence-docs, project-audit), super-ux (brand-voice, copywriting, ux-audit, ux-flows, ux-foundation, ux-scenarios, vision), sheleg-design, seo-aeo-audit, agent-sync, sheleg-dev (7 skills), telegram-dev (3 skills), agent-stack (4 skills) — 28 descriptions total | Miss: q09 ("Rewrite this one system prompt so it sounds friendlier") false-triggered `agent-harness`. All six positives hit the intended skill; q07/q08/q10/q11 routed to the correct sibling pack (task-pipeline, agent-sync, stripe-billing, task-pipeline), q12 answered `none`. |
| 2026-08-31 | 0.17.1 (tree at release candidate) | claude-sonnet (Agent-tool `sonnet`) | 6/6 train, 5/6 validation (11/12 overall) | s01 3/4 · s02 2/4 · s03 4/4 (9/12 lines) | same 28-skill family list as the haiku row | Miss: q04 ("проверь системный промпт и описания инструментов нашего агента") answered `none` instead of `agent-harness`. All other positives hit; negatives routed to the correct sibling or `none`. q07 was probed twice (a launch retry) — both runs answered task-pipeline. |

## Method (2026-08-31 rows)

Wave-3 eval protocol, executed from a Claude Code harness rather than a chat UI:

- **Triggers:** one FRESH general-purpose subagent per query per model (Agent
  tool, `model: haiku` / `model: sonnet`), no shared context between probes. The
  probe prompt was the query verbatim plus an instruction to read a file holding
  the family's 28 skill names-with-descriptions (built from the members'
  `SKILL.md` front matters) and answer with one skill name or `none`. Scoring: a
  positive passes only on the intended skill; a negative passes on `none` or any
  non-`agent-stack` skill.
- **Known limits, stated rather than hidden:** (1) each subagent's own system
  prompt also lists the machine's full installed-skill roster (family plus
  foreign packs), so the probe context is the real machine, not a clean room —
  sonnet probes mostly answered from that roster without opening the file
  (0 tool uses), haiku probes read the file first (1 tool use); answers in
  `plugin:skill` form were normalised to the skill name. (2) One probe per query
  per model, not the three repetitions `test/evals/README.md` asks for — cost
  bound; treat single-probe rates as coarse. (3) The suite names no models, so
  haiku and sonnet were chosen; opus was not probed.
- **Scenarios:** per scenario and model, one fresh subagent was given the
  scenario query and told to read the named skill file(s) first (simulating the
  skill being loaded), then answer. Each `expected_behavior` line was scored
  pass/fail by the coordinating agent reading the full answer — an LLM-judge
  grade with n=1, not a calibrated judge. A full interactive session (real skill
  auto-loading, multi-turn) is not reproducible from this harness; trigger rows
  above are the loading evidence, scenario rows are content evidence.
- **What the scenario failures name, so the next edit knows where to aim:** the
  one line that failed on BOTH models is s02's *"Records model, prompt and tool
  versions with results"* — neither answer surfaced version-recording, though
  `agent-evals` §7 states it; s02's judge-calibration line failed on sonnet and
  its adversarial-cases line on haiku; s01's *"Names provider failure and
  context-pressure behavior"* failed on sonnet. s03 passed 4/4 on both models.

