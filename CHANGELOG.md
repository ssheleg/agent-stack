# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.4.0] — 2026-08-12

### Added

- **`references/context-engineering.md`** — what the loop gives up when the window
  runs out, which the skill named a threshold for and never answered. The five-rung
  compaction ladder, cheapest first, with a re-measure between rungs so a small
  overage never buys a model call; the rung that exists only for the case where the
  compaction request itself does not fit; the **tool-pair invariant** — one boundary
  finder used by every rung, because a truncation that orphans a `tool_use` fails the
  *next* request with a 400 in the middle of a task; **typed carryover blocks** copied
  across the boundary rather than summarized, since a summarizer keeps the discussion
  and drops the state, including the flag that said not to write; **tool-output
  offload** to a file with the path left in context, because trimming history cannot
  save a window one result already filled; token estimation and the direction it errs;
  the compaction circuit breaker; sub-agent context isolation; the filesystem as
  context; and how to pick constants for your own window.

  Ladder structure and the attachment taxonomy are adapted from
  [HKUDS/OpenHarness](https://github.com/HKUDS/OpenHarness) (MIT),
  `services/compact/__init__.py` and `services/tool_outputs.py`. The constants are
  deliberately ours — and deliberately absent, with anchors for choosing them, because
  a threshold copied without its window is a number nobody can defend.

### Changed

- **§12 Context Engineering** in the body: five traps an agent cannot know to look up,
  because it does not know they exist. **§7 gains Layer 0 — carryover state**, the one
  memory layer whose survival is deterministic rather than a model's choice. §2 gains
  the iteration refund. Body lands at 486 lines / ~4985 tokens against the 500 / 5000
  budget — every insertion was cut twice to fit, and the depth is in the reference
  where it belongs.

## [0.3.0] — 2026-08-12

### Changed

- **The description now opens with `Use when …` and carries paired Russian triggers.**
  That has been the family canon since `super-ux` v0.20.0; this repository was created
  after it and never adopted it, so the skill did not match a request written in
  Russian — and a skill that does not match is a skill that is not there. 923/1024
  chars, inside the 970 working limit that v0.2.0 had already brought it under.

## [0.2.0] — 2026-08-11

### Changed

- **The body went 604 lines / 5361 tokens to 459 / 4146** — the caps are 500
  and 5000, and it was the only skill in the family over both. Measured with
  `cl100k`.

  Sections 6 (provider routing) and 7 (memory layers) were carrying depth that
  `references/llm-proxy-billing.md` and `references/patterns.md` already hold —
  fallback chains and retry/backoff in the first, confidence management,
  extraction heuristics, fuzzy deduplication and conflict resolution in the
  second. The body keeps the shape of each (the four-layer table, the router's
  contract) plus the traps, and points at the depth.

  The traps stay inline because an agent cannot know to open a file about a
  trap it does not know exists: a retry loop and a fallback chain **multiply**,
  a health check that only runs on failure never recovers, model selection has
  three levels and a silent precedence bug bills a cheap model at a premium
  rate, and every memory layer competes for one context window — give layer 1 a
  floor or old generalities crowd out what the user said a minute ago.

- `references/patterns.md` gains the `## Contents` list the canon requires of a
  reference over 100 lines: a partial read is what agents actually do, and
  without the list it returns an arbitrary slice.

- The description trimmed 975 → 937 chars, inside the 970 headroom, by dropping
  two trigger phrases already covered by their neighbours.

## [0.1.0] — 2026-08-06

First release. The skill is a port: it was written and used inside Cursor
against a production multi-agent system, and this repository is where it
becomes installable, versioned and checked.

### Added

- **`agent-orchestrator` skill** (618 lines) — the orchestrator pattern with a
  shared context object and a sub-agent protocol; a tool-calling loop with
  in-loop trimming, wrap-up injection at ~70% of the window and a max-iteration
  guard that still composes a partial answer; meta-tools that delegate rather
  than execute; sub-agent retry split into retryable and fatal; a multi-stage
  pipeline with complexity detection, human-in-the-loop checkpoints and resume;
  multi-provider routing with fallback, exponential backoff and health checks;
  a four-layer memory system (chat history, working memory, long-term learnings,
  insights) with confidence lifecycles, fuzzy dedup, conflict resolution and
  decay; context budget allocation; self-learning feedback loops.
- **`references/patterns.md`** (351 lines) — the data models and algorithms
  behind the above: message and result protocols, pipeline models, the SQL
  validation loop, context-window sizes and token estimation, learning
  extraction heuristics, confidence management, the fuzzy-dedup and
  conflict-resolution patterns, cross-resource transfer, and a suggestion engine
  that costs no LLM calls.
- **`references/llm-proxy-billing.md`** (255 lines) — the wallet side of
  reselling LLM access, generalized from an OpenRouter Management API
  integration: tiered balances and the single boundary where markup applies,
  two-phase commit against a provider API with compensating transactions,
  transaction-scoped advisory locking, optimistic concurrency for reclaims,
  spend-delta polling and the three cases it must distinguish, budget/loop/
  auto-pause guardrails converging on one pause function with per-cause
  timestamps, per-tenant key lifecycle and healing, the refund waterfall, and
  model routing precedence.
- Structural validator (`test/validate.py`) enforcing one version across four
  files, Agent Skills front-matter limits, and reference links in **both**
  directions — the source this skill came from shipped a `reference.md` that
  nothing referenced, and that is now a failing check.
- Installer CLI, `install.sh`, Cursor rule channel, plugin + marketplace
  manifests, CI with negative self-tests.

### Notes

The `references/patterns.md` file was `reference.md` in the source and was
renamed on the way in: it is loaded by name from `SKILL.md`, and the validator
now requires that link to resolve.
