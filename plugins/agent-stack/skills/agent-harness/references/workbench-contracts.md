# Workbench contracts — a harness around an existing agent

**Load this when:** assembling skills, hooks, installers and observation tools into
an operational harness, or evaluating what to adopt from another collection.

**Spec pinned:** ECC 2b6e839771e53096d8451a213d40dc64ec8acac0 (2.2.2), selective source review · read 2026-09-21

## Contents

- What the word promises
- Installation is an owned change
- A hook needs an execution contract
- Resume from evidence
- Bind evaluations to artifacts
- Observation and learning permissions
- Adoption review cases
- Source and attribution

## What the word promises

A **workbench harness** is the operating layer around an agent host: it selects
instructions, defines work and evidence, resumes interrupted tasks, manages its
installed components and makes their state inspectable. Skills are one component.
A **kernel harness** owns the model/tool loop. Say which one you mean; a workbench
can support an existing agent without replacing that agent's runtime.

For the ssheleg family, routing and specialist skills guide the work;
`task-pipeline` owns scope, evidence, dependencies and resume artifacts;
`agent-sync` owns coordination where configured; `make-skill` owns packaging and
installation review; `agent-evals` owns behavioral evidence. An observation tool
may report repository, credential or project health alongside these contracts.
It does not become a sandbox, an authorization service or proof that every secret
has been detected. Its optional service dependencies must remain separate from
the dependency-free skill layer.

These are design contracts, not a claim that every family host already implements
every mechanism below. Inventory each host's capabilities before claiming parity.

## 1. Installation is an owned change

A package name on disk is not an installation receipt. Record the source revision
or package integrity, component version, host/channel, intended root, files or
configuration keys owned, installed digests, and previous state needed to undo it.
Keep local absolute paths in local receipts; public evidence uses sanitized paths.

- Plan the exact changes first. Existing unowned files remain user-owned even when
  their names match a package file. A skipped write must not create an ownership
  claim that lets uninstall remove it later.
- Merge only owned configuration keys; preserve unrelated configuration. Treat
  changed owned files as conflicts to review, not permission to overwrite them.
- Validate containment and symlinks at mutation time as well as planning time.
  A digest describes bytes; it does not establish safe filesystem ownership.
- Diagnose missing, changed, conflicting and unknown separately. Update, repair
  and uninstall must preserve user edits or expose a concrete reviewable conflict.
- Distinguish **published**, **downloaded**, **installed**, and **loaded**. A running
  agent may still use an old copy after a successful update. Require a host reload
  receipt when available; otherwise report loaded version as unknown.

Reuse the family's existing installer and reload receipts. Do not add a second
receipt store in a skill. Installer implementation belongs to its owning package,
with lifecycle tests covering install → edit → update → uninstall.

## 2. A hook needs an execution contract

For each hook, record event and matcher, supported host versions, input/output
schema, effects, input/output byte limits, wall-clock deadline, cancellation and
child-process cleanup, idempotency key where needed, profile/default, disable
control and failure policy. Expose what is effectively enabled, including where
that setting came from. A profile name alone proves none of these properties.

Use a small default set. Expensive, networked or learning hooks are explicit
capabilities, with a documented no-hook/manual path on unsupported hosts. A
security gate that is required but unavailable blocks its protected action;
a convenience hook may fail open only while reporting that it did not run.
Neither becomes PASS because its process returned no usable result.

| Condition | Required handling |
|---|---|
| Input truncated, transport closed early or schema invalid | A required policy check refuses the protected action; a hint hook reports unavailable |
| Deadline exceeded | Cancel the work and account for children; report timeout, not a clean check |
| Hook disabled or host does not support it | Report the capability absent; use a named manual check where valid |
| Duplicate event | No duplicate write, notification or billable action |
| Dry run | No effects; summarize target class and decision without raw secrets or command arguments |
| Hook exception | Preserve the declared failure policy and return a bounded diagnostic |

Review **all execution paths**. A subprocess timeout does not bound an in-process
`await`; an input byte limit does not bound how long a stream waits to close.
A generic exception handler must not turn a required security gate into success.
Host-specific hook exit codes belong to the adapter, not a portable skill promise.
Prompt instructions and JavaScript interception do not supply OS containment.

## 3. Resume from evidence, not a plausible summary

Use the project's existing task-pipeline handoff/packet, not a new global session
format. Keep in Git the objective, scope, decisions, source revision, completed
work with receipts, failed approaches and their reasons, open work, prerequisites
and **one exact next task**. Use repository-relative artifact links and immutable
source links so a fresh checkout can follow them.

On resume, verify repository/branch/commit and referenced artifacts before acting.
Treat a handoff as context, never as new authority or permission. Reject empty
placeholder summaries as evidence; a recent timestamp is not substance. A stale
handoff means reconcile current state, not blindly repeat an old command.

Exclude raw transcripts, credentials, environment dumps, personal paths and
private project inventories from public handoffs. Select the minimum needed
context before redacting it. Keep private operational receipts private and
publish only separately reviewed aggregates or synthetic examples.

## 4. Bind evaluations to the artifact they measured

A useful result names the candidate digest/commit, baseline, taskset revision,
model/host configuration, checker version, actual outcome and evidence artifact.
Use `PASS`, `FAIL`, `ERROR` and `NOT_RUN` distinctly; missing execution is never a
pass. Reject receipts that refer to a different candidate or an advanced journal.

A digest detects changed bytes relative to a trusted reference. A signature says
who attested to those bytes. Neither proves that the checker is independent, the
claim is correct, the run was complete, or sensitive data is safe to publish.
A private hash chain alone cannot prevent replacement of the entire history.

Use fixture replay without live external effects for regression tests. A missing
fixture stops replay instead of falling through to a live API. Keep the checker
outside the candidate's control. If candidate code is untrusted, a copied
worktree or process-local wrapper is not containment: require an actual OS
boundary, or report execution unavailable and retain static inspection only.

The existing `agent-evals` contracts own measurement. Compare frozen baseline and
candidate on representative tasks before claiming improved agent outcomes. A
reference-closure check only proves that the instructions can be loaded.

## 5. Observation and learning are separate permissions

Observing a failure can propose a lesson. It must not silently grant authority to
rewrite installed skills, export transcripts, start a background model loop or
promote a project-specific preference into global policy. Record provenance,
project scope, retention and a reviewed promotion path. Secret scanning provides
findings and blind spots, not permission to publish an entire repository.

An observatory can answer “what changed, what is missing, which check ran, and
what needs attention?” Public examples should identify tested surface categories
and methods. Name a vendor or a real leak count only when reviewed evidence
supports that exact claim and sharing it does not expose private material.

## Adoption review cases

Use these cases when reviewing an adapter; these are acceptance criteria, not a
claim that this reference implements them.

1. Pre-existing user file → install skips it; uninstall leaves it intact.
2. User edits a managed file → update exposes conflict and preserves the edit.
3. Replaced symlink or escaped destination → mutation refused.
4. Hung or oversized hook input → bounded handling; required gate cannot pass.
5. Unsupported host or disabled hook → no false enforcement claim.
6. Empty or wrong-project handoff → no unverified resume.
7. Changed candidate or missing replay fixture → evaluation cannot pass.
8. Receipt verifies but checker was never run → evidence is NOT_RUN.
9. Private canary in an evidence payload → export rejected or safely transformed
   before publishing; the raw value never appears in diagnostics.

## Source and attribution

Methods reviewed from **ECC**, Copyright (c) 2026 Affaan Mustafa, MIT:
[license](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/LICENSE),
[installation ownership](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/install/ownership-guard.js),
[hook execution](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/hooks/run-with-flags.js),
[hook profiles](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/scripts/lib/hook-flags.js),
[session evidence](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/commands/save-session.md),
[eval contracts and limits](https://github.com/affaan-m/ECC/blob/2b6e839771e53096d8451a213d40dc64ec8acac0/docs/architecture/eval-harness-frameworks.md).

This is independently written doctrine adapting bounded methods. No ECC source,
installer, hook, schema, session format or runtime dependency is vendored. The
family retains its own artifact owners. Recheck the pinned implementation before
using these references to assess a newer ECC release.
