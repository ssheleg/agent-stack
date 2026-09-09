#!/usr/bin/env python3
"""FIX-AS-08.01 — proportion intervals and trial units (sherlock audit, AS-08).

The finding: the Wald interval was given without n/p limits (zero width at
p=0/1 — certainty from a boundary); "dependence always widens the band" and
"p^k is a worst case" were stated as theorems though both need assumptions;
comparing independent averages was banned outright; repeated trials of one
task could be pooled as if they were independent tasks.

The fix under test (statistics.md):
* Wilson is the default (extracted from the doc and RUN): nonzero width at the
  boundary, (0,1) at n=0 — a zero/small sample is never a universal bound;
* the Wald helper states its validity limits;
* dependence-widens and p^k-baseline carry their assumptions;
* unpaired comparison is legitimate with the wider band; pairing preferred;
* pass@k/pass^k aggregate over TASK-level trials, never pooling repeats.

Standard library only.
"""
import os
import re
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


def doc():
    with open(DOC, encoding="utf-8") as fh:
        return fh.read()


def load_wilson():
    text = doc()
    for m in re.finditer(r"```python\n(.*?)```", text, re.S):
        if "def wilson" in m.group(1):
            ns = {}
            exec(compile(m.group(1), "statistics.md", "exec"), ns)
            return ns["wilson"], ns["band"]
    raise AssertionError("the wilson code block was not found in statistics.md")


def t_wilson_is_shipped_and_boundary_honest():
    wilson, band = load_wilson()
    lo, hi = wilson(0.0, 5)
    assert hi > 0.3, f"5 clean runs left almost no uncertainty: hi={hi}"
    lo1, hi1 = wilson(1.0, 3)
    assert lo1 < 0.75, f"3/3 passes claimed near-certainty: lo={lo1}"
    assert wilson(0.5, 0) == (0.0, 1.0), "n=0 is not total uncertainty"
    # the Wald defect, demonstrated: zero width at the boundary
    assert band(0.0, 5) == 0.0, "the doc's Wald no longer shows the boundary defect"


def t_wald_states_its_limits():
    d = " ".join(doc().split())
    assert "n*p >= 10 and n*(1-p) >= 10" in d, "the Wald validity limits are missing"
    assert "zero or tiny sample is not a universal bound" in d or \
           "a zero or tiny sample is not a universal bound" in d.lower(), \
        "small-sample humility is missing"


def t_assumptions_are_named():
    d = " ".join(doc().split())
    assert "POSITIVE intra-cluster correlation" in d, \
        "dependence-widens carries no assumption"
    assert "an assumption, not a theorem" in d.lower() or "assumption, not a theorem" in d, \
        "the widening claim is still a theorem"
    assert "INDEPENDENCE BASELINE, not a bound" in d, "p^k is still called a worst case"


def t_unpaired_is_legitimate_with_wider_band():
    d = " ".join(doc().split())
    assert "Never subtract two independent averages." not in d, \
        "the absolute ban on independent averages survived"
    assert "still legitimate when pairing is impossible" in d, \
        "unpaired comparison is still forbidden"
    assert "wider two-sample band" in d


def t_task_level_trials():
    d = " ".join(doc().split())
    assert "computed over TASK-LEVEL trials" in d, "task-level aggregation is missing"
    assert "trials are not independent tasks" in d, \
        "repeated trials can still be pooled as tasks"


# ---------------- the trial-unit rule, run as behaviour


def benchmark_pass_at_k(tasks, pooled):
    """tasks: {task: [trial results]}. Correct: mean over tasks of per-task
    any-success. Pooled (the defect): every trial counted as its own task."""
    if pooled:
        allt = [r for rs in tasks.values() for r in rs]
        return sum(allt) / len(allt)
    per_task = [1.0 if any(rs) else 0.0 for rs in tasks.values()]
    return sum(per_task) / len(per_task)


def t_pooled_trials_inflate():
    tasks = {"easy": [1, 1, 1, 1, 1], "hard": [0, 0, 0, 0, 1]}
    correct = benchmark_pass_at_k(tasks, pooled=False)
    pooled = benchmark_pass_at_k(tasks, pooled=True)
    assert correct == 1.0, "per-task any-success mis-modelled"
    assert pooled != correct, \
        "the model cannot show the pooling defect — the regression proves nothing"


def main():
    case("wilson ships, is boundary-honest, n=0 = total uncertainty",
         t_wilson_is_shipped_and_boundary_honest)
    case("the Wald helper states its validity limits", t_wald_states_its_limits)
    case("dependence-widens and p^k-baseline carry their assumptions",
         t_assumptions_are_named)
    case("unpaired comparison is legitimate with the wider band",
         t_unpaired_is_legitimate_with_wider_band)
    case("pass@k/pass^k aggregate over task-level trials", t_task_level_trials)
    case("pooling repeated trials as tasks visibly distorts the number",
         t_pooled_trials_inflate)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
