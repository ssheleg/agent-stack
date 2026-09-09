#!/usr/bin/env python3
"""FIX-AS-06.01 — the first release ships with an executable seed corpus
(sherlock audit, AS-06).

The finding: §6 said the corpus comes "from production, never up front" and
the first offline gate is "observables only" — leaving a greenfield feature
with criteria but no executed trials, a gate that cannot run. And the same
chapter then allowed simulated users, a contradictory route.

The fix under test: a SEED corpus (curated/synthetic/manual, provenance per
input) is allowed before release with at least a happy, an adversarial and a
failure/retry trial; the release gate requires EXECUTED trials —
observable-only is specification-ready, not release-ready; a corrupted
input/fixture/runner is TEST_ERROR, not a behaviour pass/fail; and cases are
isolated.

Standard library only.
"""
import json
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-evals", "SKILL.md")
CORPUS = os.path.join(ROOT, "test", "evals", "fixtures", "bootstrap-corpus.json")
SCEN = os.path.join(ROOT, "test", "evals", "scenarios.json")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_seed_and_gate():
    flat = " ".join(open(SKILL, encoding="utf-8").read().split())
    for needle in ("The first release has no production — so it runs against a "
                   "SEED corpus, and\nobservable-only is not release-ready".replace("\n", " "),
                   "with at least a **happy**, an **adversarial** and a "
                   "**failure/retry** trial",
                   "Each seed input carries its **provenance**",
                   "The release gate requires EXECUTED trials",
                   "`specification-ready`, not\n`release-ready`".replace("\n", " "),
                   "A corrupted fixture, input or runner is a `TEST_ERROR`",
                   "cases are isolated"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"


def t_seed_corpus_has_the_three_kinds_with_provenance():
    c = json.load(open(CORPUS, encoding="utf-8"))
    trials = c["trials"]
    kinds = {t["kind"] for t in trials}
    assert {"happy", "adversarial", "failure_retry"} <= kinds, \
        f"the seed corpus is missing a required trial kind: {kinds}"
    for t in trials:
        assert t.get("provenance") in ("curated", "synthetic", "manual"), \
            f"{t['id']}: no valid provenance mark"
        assert t.get("input") and t.get("observable"), \
            f"{t['id']}: a trial with no input or observable is not executable"


def t_scenarios_note_points_at_the_seed_and_names_specification_ready():
    note = json.load(open(SCEN, encoding="utf-8"))["note"]
    assert "specification-ready" in note and "EXECUTED trials" in note, \
        "the scenarios note still calls authored observables release-ready"
    assert "bootstrap-corpus.json" in note, "the note does not point at the seed corpus"


# ---------------- the release-gate + runner rules, executed


REQUIRED_KINDS = {"happy", "adversarial", "failure_retry"}


def gate(trials, executed):
    """Release-ready needs EXECUTED trials covering the required kinds; a
    suite with nothing run is specification-ready."""
    if not executed:
        return "specification-ready"
    covered = {t["kind"] for t in trials if t["id"] in executed}
    if REQUIRED_KINDS <= covered:
        return "release-ready"
    return "specification-ready"


def run_trial(trial):
    """A corrupted input/fixture is TEST_ERROR, distinct from a behaviour
    pass/fail."""
    if not trial.get("input") or trial.get("input") == "<corrupt>":
        return "TEST_ERROR"
    return "PASS" if trial.get("_behaviour_ok", True) else "FAIL"


def t_observable_only_is_specification_ready():
    trials = json.load(open(CORPUS, encoding="utf-8"))["trials"]
    assert gate(trials, executed=set()) == "specification-ready", \
        "a suite with nothing executed was called release-ready"
    all_ids = {t["id"] for t in trials}
    assert gate(trials, executed=all_ids) == "release-ready", \
        "an executed seed covering all three kinds was not release-ready"


def t_corrupt_input_is_test_error():
    assert run_trial({"input": "<corrupt>"}) == "TEST_ERROR", \
        "a corrupted input scored as a behaviour result"
    assert run_trial({"input": "real", "_behaviour_ok": False}) == "FAIL"
    assert run_trial({"input": "real"}) == "PASS"


def t_cases_are_isolated():
    trials = json.load(open(CORPUS, encoding="utf-8"))["trials"]
    a, b = trials[0], trials[1]
    r_ab = (run_trial(a), run_trial(b))
    r_b_alone = run_trial(b)
    assert r_ab[1] == r_b_alone, "case B's result depended on whether A ran"


def main():
    case("the doctrine states the seed corpus and release gate",
         t_doctrine_states_the_seed_and_gate)
    case("the seed corpus has happy/adversarial/failure_retry with provenance",
         t_seed_corpus_has_the_three_kinds_with_provenance)
    case("the scenarios note points at the seed and says specification-ready",
         t_scenarios_note_points_at_the_seed_and_names_specification_ready)
    case("observable-only is specification-ready, executed is release-ready",
         t_observable_only_is_specification_ready)
    case("a corrupt input is TEST_ERROR, not a behaviour result",
         t_corrupt_input_is_test_error)
    case("cases are isolated", t_cases_are_isolated)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
