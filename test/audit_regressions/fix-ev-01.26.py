#!/usr/bin/env python3
"""FIX-EV-01.26 — the outcome corpus for agent-orchestrator (sherlock audit,
parent FIX-EV-01; depends on the family harness of FIX-EV-01.01).

The corpus (evals/cases/agent-orchestrator.json) is anchored to the audit's own
findings: a greenfield first release must carry happy + adversarial +
failure/retry trials and an empty corpus closes no gate (AS-06); an
order-sensitivity rubric must fail a swapped confirm/charge while passing
swapped reads, negative example kept beside it (AS-07); boundary n=1/n=3
statistics carry no zero-width intervals (AS-08, a no-op case — the skill
reports, redesigns nothing); a regrade of an old trace is labelled and a
mutated candidate must flip the gate (AS-10); plus negative routing — judged
on ARTIFACTS through the family's outcome-case contract, so agent-orchestrator can
no longer pass an eval by its name being picked.

Checked here, stdlib only.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASES = os.path.join(ROOT, "evals", "cases", "agent-orchestrator.json")
HARNESS = os.path.expanduser("~/DATA/sshlg-skills/test/outcome_harness.py")

failures = []
not_run = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def manifest():
    with open(CASES, encoding="utf-8") as fh:
        return json.load(fh)


def t_cases_are_structurally_valid():
    m = manifest()
    ids = [c["id"] for c in m["cases"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 5
    for c in m["cases"]:
        assert c["schema_version"] == "outcome-case/1"
        assert c["skill"] == "agent-orchestrator"
        assert c["environment"]["case_digest"] == \
            hashlib.sha256(c["prompt"]["text"].encode()).hexdigest(), \
            f"{c['id']}: case_digest does not pin the frozen prompt"
        assert c["checks"]["outcome"], \
            f"{c['id']}: no outcome checks — the name-picking eval again"


def t_saga_case_keeps_unknown_pending():
    c = next(x for x in manifest()["cases"] if "saga-not-2pc" in x["id"])
    p = c["prompt"]["text"]
    assert "UNKNOWN HTTP outcome stays PENDING" in p, "unknown is not kept pending (AS-01)"
    assert "AT MOST ONE external effect per operation_id" in p, "no idempotency bound (AS-01)"


def t_negative_refuses_to_load():
    neg = next(c for c in manifest()["cases"] if "negative" in c["id"])
    assert "agent-orchestrator" in neg["checks"]["load_trace"]["expect_not_loaded"]


def t_baseline_and_memory():
    m = manifest()
    base = next(c for c in m["cases"] if "zero-baseline" in c["id"])
    assert "uninitialized" in base["prompt"]["text"] and "initialized(0)" in base["prompt"]["text"], \
        "the zero-vs-missing baseline is not pinned (AS-02)"
    mem = next(c for c in m["cases"] if "lexical-similarity" in c["id"])
    p = mem["prompt"]["text"]
    assert "no silent merge" in p and "wins ONLY in its own scope" in p, \
        "contradiction handling is not pinned (AS-03)"


def t_noop_and_manifest_rules():
    m = manifest()
    noop = next(c for c in m["cases"] if "fake-edge" in c["id"])
    p = noop["prompt"]["text"]
    for edge in ("backup->migration", "approval->charge", "lease->edit"):
        assert edge in p, f"the {edge} edge is not preserved (AS-04)"
    assert "Do NOT redesign" in p, "the no-op case now mutates"
    flat = " ".join(json.dumps(m, ensure_ascii=False).split())
    for needle in ("actual output oracle", "raw result", "with/without-skill",
                   "grader convenience"):
        assert needle in flat, f"the manifest no longer records {needle!r}"


def t_family_harness_validates_each_case_where_present():
    if not os.path.isfile(HARNESS):
        not_run.append("family harness absent — case validation NOT_RUN (never PASS)")
        return
    for c in manifest()["cases"]:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(c, fh)
            path = fh.name
        try:
            r = subprocess.run([sys.executable, HARNESS, path],
                               capture_output=True, text=True, timeout=60)
            assert r.returncode == 0, \
                f"{c['id']} rejected by the family harness:\n{r.stdout}"
        finally:
            os.unlink(path)


def main():
    case("every case is structurally valid, none is name-picking",
         t_cases_are_structurally_valid)
    case("the saga case keeps an unknown outcome pending (AS-01)",
         t_saga_case_keeps_unknown_pending)
    case("the negative case refuses to load the skill", t_negative_refuses_to_load)
    case("zero baseline is not missing; opposites do not merge (AS-02, AS-03)",
         t_baseline_and_memory)
    case("the fake-edge no-op preserves control/state edges (AS-04)",
         t_noop_and_manifest_rules)
    case("the family harness validates each case (where present)",
         t_family_harness_validates_each_case_where_present)
    for n in not_run:
        print(f"  NOT_RUN  {n}")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
