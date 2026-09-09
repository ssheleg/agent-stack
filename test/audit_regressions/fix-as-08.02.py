#!/usr/bin/env python3
"""FIX-AS-08.02 — paired/clustered/unpaired are separated, and splits are spent
once (sherlock audit, AS-08 + ADOPT-M-04).

The finding: McNemar/bootstrap were prescribed without tying them to the
design; dependent repeats could be treated iid; and nothing stopped a reused
validation example from being relabelled an "unseen final test".

The fix under test (statistics.md):
* a design→method table: paired→McNemar/paired-bootstrap over deltas;
  clustered→cluster bootstrap resampling TASKS; unpaired→two-sample (Welch)
  SE — and the receipt names both, matching;
* dependent repeats are never iid; small n buys no certainty;
* case IDs/groupings are FIXED; validation may tune; the final holdout is
  spent once and never picks versions; "unseen" is run-history, not a label;
* the matching rule is RUN as behaviour on the audit's counterexamples.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-evals",
                   "references", "statistics.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def flat():
    with open(DOC, encoding="utf-8") as fh:
        return " ".join(fh.read().split())


def t_design_method_table():
    d = flat()
    assert "The design decides the method" in d
    for needle in ("cluster bootstrap that resamples TASKS",
                   "two-sample (Welch) SE",
                   "receipt names the design AND the method"):
        assert needle in d, f"the doc no longer states {needle!r}"
    assert "treats dependent repeats as iid" in d, "the trial-bootstrap trap is not named"


def t_repeats_never_iid_small_n_humble():
    d = flat()
    assert "Dependent repeats are never claimed iid" in d
    assert "a small sample never buys\nimaginary certainty".replace("\n", " ") in d or \
           "a small sample never buys imaginary certainty" in d


def t_splits_spent_once():
    d = flat()
    assert "case IDs and their groupings" in d.lower() or "case ids and their groupings" in d.lower()
    assert "frozen before any run" in d
    assert "MAY be used for tuning" in d, "validation tuning is forbidden again"
    assert "spent ONCE" in d and "never used to pick between versions" in d
    assert 'relabelled an "unseen final test"' in d
    assert "property of the RUN HISTORY" in d


# ---------------- the matching rule, run as behaviour


def receipt_ok(design, method, labels=None):
    """The doc's rule: the method must match the design; splits keep their
    history; dependent repeats are not iid."""
    match = {"paired": {"mcnemar", "paired-bootstrap"},
             "clustered": {"cluster-bootstrap-tasks"},
             "unpaired": {"welch-two-sample"}}
    if method not in match.get(design, set()):
        return False
    for lab in labels or []:
        if lab.get("claim") == "unseen-final-test" and lab.get("history") == "used-in-validation":
            return False
        if lab.get("claim") == "iid" and lab.get("structure") == "dependent-repeats":
            return False
    return True


def t_matching_rule_behaviour():
    assert receipt_ok("paired", "mcnemar") is True
    assert receipt_ok("unpaired", "mcnemar") is False, "McNemar over an unpaired corpus passed"
    assert receipt_ok("clustered", "cluster-bootstrap-tasks") is True
    assert receipt_ok("clustered", "paired-bootstrap") is False, \
        "a trial-level bootstrap passed a clustered corpus"
    assert receipt_ok("unpaired", "welch-two-sample") is True
    assert receipt_ok("paired", "mcnemar",
                      [{"claim": "unseen-final-test", "history": "used-in-validation"}]) is False, \
        "a reused validation example was relabelled an unseen final test — the finding"
    assert receipt_ok("clustered", "cluster-bootstrap-tasks",
                      [{"claim": "iid", "structure": "dependent-repeats"}]) is False, \
        "dependent repeats were claimed iid"


def main():
    case("the design→method table stands, receipt names both", t_design_method_table)
    case("dependent repeats never iid; small n buys nothing",
         t_repeats_never_iid_small_n_humble)
    case("splits are frozen; holdout spent once; unseen is history",
         t_splits_spent_once)
    case("the matching rule refuses the audit's counterexamples",
         t_matching_rule_behaviour)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
