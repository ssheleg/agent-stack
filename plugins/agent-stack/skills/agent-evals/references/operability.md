# Operability: proving an agent completes a product's stories through its tools

**Load this when** a product exposes capabilities to agents (MCP, an HTTP API, a CLI) and you
must prove that an agent completes its users' stories through that surface: the deterministic
release gate, the cold-agent judgment, gated steps inside a test, and what a pipeline reads.

This is the mechanics of canon rule **AN-9** (index and the surface rules AN-3, AN-7, AN-8:
`agent-interop/references/agent-surface.md`). The pipeline that runs it, and when, is
task-pipeline's `references/agent-surface.md`. Proof has two levels and they never stand in
for each other.

## Level 1: the gate (deterministic, blocks a release)

**The proving call**, through a real client: a local stdio build where nothing is deployed, the
deployed target after a deploy.

- [ ] Discovery answers (`server/discover`, the OpenAPI document, or `--help --json`).
- [ ] The advertised tool list equals the committed snapshot.
- [ ] One read-only call returns the documented shape.
- [ ] One deliberate bad call returns the documented typed error.

**Contract tests**, one set per capability (`CAP-NN`), run against a test tenant:

| Test | Passes when |
|---|---|
| schema | invalid input is refused before any effect; output validates against `outputSchema` |
| typed errors | each documented error code is reachable and carries its `code` |
| idempotent retry | the same write twice with one key leaves one effect and two equal answers |
| scope refusal | a grant narrower than the capability's role is refused, and no effect row exists |
| gate refusal | a gated call returns the gate and `human_steps`, and no effect row exists |
| gate completion | after the fixture performs the gate, the repeated call causes the effect exactly once |
| emits | each declared `Emits` event arrives at a test subscriber |

Assert the **state change** in the tenant, never the response text (SKILL.md §2, *Full-turn*).
Authorization before effect is a mandatory happens-before edge (SKILL.md §5): assert it as a
partial order, with the negative example (an effect row written before the refusal) kept
beside the test.

## Level 2: the judgment (a cold agent, `pass^k`)

- [ ] **Tasks:** one per agent-channel scenario (`Channel: agent | both`) of every `must` story.
  The prompt states the user's goal, never tool names.
- [ ] **Cold:** the agent gets only what is published (`AGENTS.md`, discovery) and its
  persona's credentials; no repository, no earlier transcript.
- [ ] **Personas** from the product's `docs/ux/agent-panel.md`: a full-grant agent, a narrowly
  delegated agent, an automation with no conversation, a cheap model, an adversarial agent fed
  injected content. The full-grant persona is the judgment; the cheap and adversarial ones are
  advisory, and the adversarial one is owed on a `public` surface.
- [ ] **Model:** the verification model named by the project's model policy; record its id.
- [ ] **Reliability:** `pass^k` with **k = 3** by default, measured directly
  (`references/statistics.md`, *pass@k and pass^k are different questions*); report `n`, `k`
  and the reducer.
- [ ] **Solvable first:** each task has a reference call sequence that passes its graders
  before any agent is scored (SKILL.md §6).
- [ ] **Sandbox gate fixtures** close gated steps without a person: an approver identity that
  approves through the product's own approval surface in the test tenant, the payment
  provider's test mode, a magic-link or one-time-code sink. Never mock the server's gate
  check: that proves nothing about the gate.
- [ ] **Credentials** for the test tenant come from the secret store at run time, never a file.
- [ ] **Transcripts are fixtures:** every run's trace is stored by id; a failure is minimised
  into a permanent case (SKILL.md §6).
- [ ] **Spend cited:** the run names its budget source and reports what it spent; it stops at
  the cap.

**Per-step checks** (the names the task-pipeline `agent-tester` reports in `agent-review/1`):

| Check | Measured by |
|---|---|
| `discoverable` | the agent found the right tool from discovery and descriptions alone |
| `schema_valid` | every call's arguments validated on the first or a corrected second try |
| `typed_error` | each error the agent met carried a code it could act on |
| `idempotent_retry` | a retried write left one effect |
| `auth_denied` | a call beyond the persona's grant was refused before any effect |
| `gate_handoff` | at a gate the agent handed over `human_steps` and resumed after the fixture |
| `outcome_read_back` | the agent confirmed the outcome by a read, not by its own claim |
| `notified` | the declared `Emits` event reached the agent |

Code checks decide every row they can; an LLM grader, where one is needed, is calibrated first
(SKILL.md §5).

## How a pipeline consumes it

| Level | Verdict | Blocks |
|---|---|---|
| 1, proving call and contract tests | pass or fail | always: a red gate stops the release |
| 2, cold agent | `pass^k` per task and persona, with the failing check names and transcript ids | where the pipeline owes it (task-pipeline decides: breaking-contract and `public` nodes); there, a task below `pass^3` fails the node |

Level 1 runs in the pipeline's local test gate and on the scheduled full run; level 2 runs once
per owed node and on the scheduled run, never on every push. The receipt names the product build, the
snapshot digest, the model, `k`, the spend and the transcript ids.

## Traps

- **A cold agent that can read the repository.** It reads the code instead of the docs, and the
  docs' gaps stay hidden.
- **`pass@k` reported as reliability.** One success in three is a ceiling, not a floor.
- **Grading the agent's final message.** "Refund issued" with no refund row is a fail.
- **A gate closed by a mock.** The test passes and the real gate is untested.
- **A judgment run per push.** Cost grows with every commit and the signal does not.
