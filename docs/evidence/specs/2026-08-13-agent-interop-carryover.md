# Carry-over ledger — `agent-interop`, 2026-08-13

Append-only. Written by every stage the moment something is deferred, dropped or
half-done; read in full at stage 10. **Deferred out loud is forgotten** — a row here
is the only thing that survives the run.

| # | Stage | What was deferred / dropped / left half-done | Why | Home | Status |
|---|---|---|---|---|---|
| C-01 | 0 | The wiki page `projects/agent-stack/agent-stack.md` claims v0.1.0, one skill and two references; the repository is at v0.6.0 with two skills and five references | Found during the harvest; fixing it mid-grill would have edited a source the run was still reading | stage 9 | open |
| C-02 | 0 | The code graph is not refreshed for this repository | No `graphify-out/` here, and B-24 records that `graphify . --update` cannot run on this machine for want of an API key. A narrower graph presented as a refreshed one is worse than no graph | family board B-24 | open |
| C-03 | 0 | B-26 — this repository's `release.yml` publishes without running the negative self-tests, which live in `validate.yml` | Real, pre-existing, and outside this run's scope. REQ-011 adds a plant; it will sit in the workflow that the release does not run | family board B-26 | open |
| C-04 | 0 | `.github/workflows/validate.yml:129-131` asserts specific installed files by name for `agent-orchestrator` only | Noticed while checking whether a third skill needs an installer change (it does not — `bin/agent-stack.js:78-82` enumerates). Whether the functional test should assert the new skill too is a stage-5 call | stage 5 | open |
