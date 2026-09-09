#!/usr/bin/env python3
"""FIX-AS-10.01 — a regrade of an old output is not a check of the candidate
(sherlock audit, AS-10).

The finding: "fixture replay" was described as a free assertion over a stored
run that answers "did the decision at this point change" — but an old output
does not change when the new prompt/model/tool schema changes. That operation
is a deterministic REGRADE, not a new agent trial.

The fix under test:
* otel-genai.md splits the senses: regrade of a stored output (free,
  deterministic, explicitly NOT a candidate check) vs candidate execution over
  a frozen fixture (a real stochastic call, costed) vs durable-execution
  replay; candidate version/output/score are their own records;
* the SKILL labels a regrade as regrade;
* the gate rule run as behaviour: mutating the candidate to a knowingly wrong
  tool CHANGES the candidate-execution gate and CANNOT change a regrade —
  which is precisely why the regrade may not wear the candidate label.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OTEL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-evals",
                    "references", "otel-genai.md")
SKILL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-evals", "SKILL.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def flat(p):
    with open(p, encoding="utf-8") as fh:
        return " ".join(fh.read().split())


def t_replay_senses_are_split():
    d = flat(OTEL)
    assert "Regrade of a stored output" in d
    assert "Candidate execution over a frozen fixture" in d
    assert "explicitly NOT a check of the candidate" in d
    assert "an assertion over a stored run | free | did the decision at this point change" not in d, \
        "the free-answers-decision-change row survived — the finding itself"
    assert "a real model call, stochastic" in d, "cost/stochasticity is not reflected"


def t_candidate_records_are_separate():
    d = flat(OTEL)
    assert "stored as their own records, never overwriting the old trace" in d
    s = flat(SKILL)
    assert "labelled regrade" in s, "the SKILL does not label a regrade as regrade"
    assert "stochastic call, costed in the receipt" in s


def t_mutation_must_move_the_gate():
    d = flat(OTEL)
    assert "mutate the candidate to a knowingly wrong tool, and the gate's result MUST change" in d
    assert "a regrade wearing the wrong label" in d


# ---------------- the gate rule, run as behaviour


OLD_TRACE_OUTPUT = {"tool": "search", "result": "ok"}


def regrade(rubric, candidate):
    # marks the OLD output; the candidate never runs
    return rubric(OLD_TRACE_OUTPUT)


def execute_candidate(rubric, candidate):
    # runs the CANDIDATE against the frozen fixture inputs
    out = {"tool": candidate["tool"], "result": "ok" if candidate["tool"] == "search" else "wrong"}
    return rubric(out)


def t_gate_behaviour():
    rubric = lambda out: out["tool"] == "search" and out["result"] == "ok"
    good = {"tool": "search"}
    bad = {"tool": "delete_everything"}          # knowingly wrong tool
    # candidate execution: the mutation MUST change the gate
    assert execute_candidate(rubric, good) is True
    assert execute_candidate(rubric, bad) is False, \
        "mutating the candidate did not move the candidate-execution gate"
    # regrade: the mutation CANNOT change it — the label must say so
    assert regrade(rubric, good) == regrade(rubric, bad) == True, \
        "the model no longer shows why a regrade cannot check a candidate"


def main():
    case("the replay senses are split, cost/stochasticity reflected",
         t_replay_senses_are_split)
    case("candidate records separate; regrade labelled regrade",
         t_candidate_records_are_separate)
    case("the mutation-must-move-the-gate rule is stated", t_mutation_must_move_the_gate)
    case("the gate rule run as behaviour (mutation moves execution, not regrade)",
         t_gate_behaviour)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
