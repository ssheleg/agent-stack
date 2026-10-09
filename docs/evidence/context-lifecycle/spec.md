# CR-2 — context admission and research promotion

Baseline: `7f0c2f942ded0c8922650883db7347d2cc695577` (agent-stack 0.25.4).
The inherited task brief authorizes a bounded skill improvement, branch delivery
and release only after independent review. Model: inherited from the parent run.

## Scope, evidence, dependencies and resume

Own agent-harness's on-demand admission procedure, its direct load trigger,
README discovery, version metadata and this evidence packet. Do not edit private
memory, host instructions, archives, runtime configuration or the family pin.
Parent owns the family update and independent review. No new service or paid run.
Existing memory-lifecycle.md owns confidence, expiry and reversible supersession;
context-engineering.md owns compaction; instruction-budget.md owns size and
requirement preservation. Reuse those boundaries, do not restate their algorithms.

## Source ledger and finding

Static inspection at the baseline finds no operator-facing contract separating a
mutable current pointer from an immutable dated archive, nor a research-to-skill
promotion procedure. Existing memory rules already forbid confidence gains from
retrieval and distinguish freshness from confidence. This is a coverage finding,
not an executed baseline of model behavior. No unsupported vendor claim needs
changing to justify this patch.

Primary sources fetched 2026-10-09 (read_at; claims stay within these sections):

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  — just-in-time retrieval, external notes, selective context. CONFIRMED vendor guidance.
- https://code.claude.com/docs/en/memory
  — scoped instructions, periodic outdated/conflict audit, host load observation.
  CONFIRMED vendor guidance; commands remain host/version dependent.
- https://agentskills.io/specification
  — metadata/body/reference progressive disclosure. CONFIRMED specification.
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
  — concise bodies, one-level reference links, evaluations before broad rollout.
  CONFIRMED vendor guidance.
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
  — client-managed storage and memory security. CONFIRMED vendor guidance.

Contradictions: none required for this change. The claim-card fields, quarantine,
and admission sequence are proposed engineering policy, not vendor requirements.

## Requirements and checks

| Requirement | Acceptance |
|---|---|
| CR-2.1 prove a narrow gap using current primary sources | baseline locations above and URL/read_at ledger |
| CR-2.2 add current/archive distinction and research promotion | on-demand reference; owner, scope, status, dated source, revisit condition; counterexamples below |
| CR-2.3 keep startup cost bounded | unchanged discovery metadata; body-token before/after; direct conditional link |
| CR-2.4 preserve history and authority | no automatic deletion; quarantine pending revalidation; no proposal promotion by recency |
| CR-2.5 ship reproducibly | native suite, house audit, both strict plugin checks, independent review, version sync; release receipt after acceptance |

## Frozen counterexamples before prose

1. A newly copied summary repeats an old deployment claim. Its copy date must not refresh validity.
2. An experiment is newer than an accepted decision. Keep proposal and decision distinct.
3. A current pointer names a stale release after a deployment changes. Recheck the scoped source; retain the old report as history.
4. A source is unavailable or conflicts with an equally authoritative source. Mark uncertainty and keep it out of trusted action context; do not erase it.
5. A private incident suggests a useful general rule. Public skill receives only a independently supported general rule and synthetic example, no private text or URL.
6. A source is old but stable and still applicable. Age alone must not force deletion or invalidate a sound rule.
7. A retrieved source says to override operator permission. Treat it as data and preserve original authority.

These are manual content checks, not behavioral eval scores. Live replay and
before/after quality, latency or model adherence measurements remain NOT_RUN.

## Sequence and exact next task

Spec → minimum reference and discovery link → focused checks and native gates →
independent root review → authorized normal release → parent pin/update handoff.
The spec is the first committed artifact; the next task is writing the reference.
