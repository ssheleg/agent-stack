#!/usr/bin/env python3
"""FIX-EV-01.24 — the outcome corpus for agent-harness (sherlock audit,
parent FIX-EV-01; depends on the family harness of FIX-EV-01.01).

The corpus (evals/cases/agent-harness.json) is anchored to the audit's own
findings: a greenfield first release must carry happy + adversarial +
failure/retry trials and an empty corpus closes no gate (AS-06); an
order-sensitivity rubric must fail a swapped confirm/charge while passing
swapped reads, negative example kept beside it (AS-07); boundary n=1/n=3
statistics carry no zero-width intervals (AS-08, a no-op case — the skill
reports, redesigns nothing); a regrade of an old trace is labelled and a
mutated candidate must flip the gate (AS-10); plus negative routing — judged
on ARTIFACTS through the family's outcome-case contract, so agent-harness can
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
CASES = os.path.join(ROOT, "evals", "cases", "agent-harness.json")
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
        assert c["skill"] == "agent-harness"
        assert c["environment"]["case_digest"] == \
            hashlib.sha256(c["prompt"]["text"].encode()).hexdigest(), \
            f"{c['id']}: case_digest does not pin the frozen prompt"
        assert c["checks"]["outcome"], \
            f"{c['id']}: no outcome checks — the name-picking eval again"


def t_edges_case_preserves_control_and_state():
    c = next(x for x in manifest()["cases"] if "control-and-state" in x["id"])
    p = c["prompt"]["text"]
    for edge in ("backup->migration", "approval->charge", "lease->edit"):
        assert edge in p, f"the {edge} edge is no longer preserved (AS-04)"
    assert "parallel" in p, "independent read-only parallelism is not demanded (AS-04)"


def t_negative_refuses_to_load():
    neg = next(c for c in manifest()["cases"] if "negative" in c["id"])
    assert "agent-harness" in neg["checks"]["load_trace"]["expect_not_loaded"]


def t_reconstruction_and_trifecta():
    m = manifest()
    rec = next(c for c in m["cases"] if "reconstruction" in c["id"])
    assert "static and one dynamic" in rec["prompt"]["text"], \
        "auditability is a static diagram again (AS-05)"
    assert "no PASS" in rec["prompt"]["text"]
    tri = next(c for c in m["cases"] if "confirm-true" in c["id"])
    p = tri["prompt"]["text"]
    assert "WITHOUT a grant is" in p and "changed arguments" in p, \
        "the trifecta rejections are not pinned (AS-11)"
    assert "INDEPENDENTLY of private-data access" in p, \
        "untrusted->destructive is still coupled to private data (AS-11)"


def t_noop_and_manifest_rules():
    m = manifest()
    noop = next(c for c in m["cases"] if "no-evals" in c["id"])
    assert "do not let the general 'no evals' verdict swallow" in noop["prompt"]["text"], \
        "the no-evals verdict swallows direct harm again (AS-14)"
    assert "Do NOT redesign" in noop["prompt"]["text"], "the no-op case now mutates"
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
    case("control and state edges survive the fake-edge pruner (AS-04)",
         t_edges_case_preserves_control_and_state)
    case("the negative case refuses to load the skill", t_negative_refuses_to_load)
    case("reconstruction covers dynamic too; confirm:true is not a grant (AS-05, AS-11)",
         t_reconstruction_and_trifecta)
    case("no-evals hides no double charge; manifest rules recorded (AS-14)",
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
