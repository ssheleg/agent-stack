# Carry-over ledger — `agent-interop`, 2026-08-13

Append-only. Written by every stage the moment something is deferred, dropped or
half-done; read in full at stage 10. **Deferred out loud is forgotten** — a row here
is the only thing that survives the run.

| # | Stage | What was deferred / dropped / left half-done | Why | Home | Status |
|---|---|---|---|---|---|
| C-01 | 0 | The wiki page `projects/agent-stack/agent-stack.md` claims v0.1.0, one skill and two references; the repository is at v0.6.0 with two skills and five references | Found during the harvest; fixing it mid-grill would have edited a source the run was still reading | stage 9 | open |
| C-02 | 0 | The code graph is not refreshed for this repository | No `graphify-out/` here, and B-24 records that `graphify . --update` cannot run on this machine for want of an API key. A narrower graph presented as a refreshed one is worse than no graph | family board B-24 | open |
| C-03 | 0 | B-26 — this repository's `release.yml` publishes without running the negative self-tests, which live in `validate.yml` | Real, pre-existing, and outside this run's scope. REQ-011 adds a plant; it will sit in the workflow that the release does not run | family board B-26 | open |
| C-04 | 0 | `.github/workflows/validate.yml:129-131` asserts specific installed files by name for `agent-orchestrator` only | Noticed while checking whether a third skill needs an installer change (it does not — `bin/agent-stack.js:78-82` enumerates). Whether the functional test should assert the new skill too is a stage-5 call | stage 5 | **closed at stage 5** — the test now loops over `ls plugins/agent-stack/skills` and asserts each one installs, so the enumeration itself is under test |
| C-05 | 5 | `make-skill`'s local checkout was **two commits behind `origin/main`** and at v0.16.0 while the umbrella pinned v0.17.0 | Caught by the stage-0 autonomy row *"is this checkout the one that ships"*, re-run before the first edit in the second repository. Editing there would have been undone by fast-forward with nothing complaining | — | **closed** — pulled to v0.17.1 before any edit |
| C-06 | 7 | `agent-stack` `main` moved to **v0.6.1** mid-run, conflicting on the same negative self-tests | Another session's PR #1 converted the plants to Python with landing asserts. Both sides kept | — | **closed** — merge `45e4eb1`; nine steps, 9/9 plants re-watched failing |
| C-07 | 10 | **`sheleg-dev` is pinned at 0.4.2 while npm serves 0.4.3** | Pre-existing, from another session, not this run's work. Deliberately not adopted: moving a pin to a release whose gate this run never executed is how *green* comes to read as *verified*. The submodule working tree was restored to the recorded pin so this run's commit carries only its own changes | family board | **open → board** |
| C-08 | 10 | `agent-stack` has no `plant_guard.py`; `make-skill` and the umbrella now ship one | This run's two new plants assert inline in Python, which achieves the same effect, but the family now has a shared implementation and this member does not use it | family board | **open → board** |
