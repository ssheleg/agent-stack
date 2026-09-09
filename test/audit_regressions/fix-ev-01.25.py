#!/usr/bin/env python3
"""FIX-EV-01.25 — the outcome corpus for agent-interop (sherlock audit,
parent FIX-EV-01; depends on the family harness of FIX-EV-01.01).

The corpus (evals/cases/agent-interop.json) is anchored to the audit's own
findings: a greenfield first release must carry happy + adversarial +
failure/retry trials and an empty corpus closes no gate (AS-06); an
order-sensitivity rubric must fail a swapped confirm/charge while passing
swapped reads, negative example kept beside it (AS-07); boundary n=1/n=3
statistics carry no zero-width intervals (AS-08, a no-op case — the skill
reports, redesigns nothing); a regrade of an old trace is labelled and a
mutated candidate must flip the gate (AS-10); plus negative routing — judged
on ARTIFACTS through the family's outcome-case contract, so agent-interop can
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
CASES = os.path.join(ROOT, "evals", "cases", "agent-interop.json")
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
        assert c["skill"] == "agent-interop"
        assert c["environment"]["case_digest"] == \
            hashlib.sha256(c["prompt"]["text"].encode()).hexdigest(), \
            f"{c['id']}: case_digest does not pin the frozen prompt"
        assert c["checks"]["outcome"], \
            f"{c['id']}: no outcome checks — the name-picking eval again"


def t_pinned_mcp_case():
    c = next(x for x in manifest()["cases"] if "pinned-mcp" in x["id"])
    p = c["prompt"]["text"]
    assert "exact SDK" in p and "fresh env" in p, "the pinned/clean-env proof is missing (AS-12)"
    assert "401" in p and "out of scope" in p, "401 or the old-constructor scoping is missing (AS-12)"


def t_negative_refuses_to_load():
    neg = next(c for c in manifest()["cases"] if "negative" in c["id"])
    assert "agent-interop" in neg["checks"]["load_trace"]["expect_not_loaded"]


def t_routing_not_by_the_word():
    c = next(x for x in manifest()["cases"] if "protocol-routing" in x["id"])
    p = c["prompt"]["text"]
    assert "MCP Tasks WHEN supported" in p, "the fixed export does not condition on support (AS-13)"
    assert "A2A" in p and "autonomous" in p, "the A2A case is not distinguished (AS-13)"
    assert "No case may be decided by the word\n'long-running' alone".replace("\n", " ") in p, \
        "a case can still be decided by the word long-running (AS-13)"


def t_noop_and_manifest_rules():
    m = manifest()
    noop = next(c for c in m["cases"] if "unsupported-tasks" in c["id"])
    assert "not be forced into A2A because it is long" in noop["prompt"]["text"], \
        "the unsupported-Tasks case still falls to A2A (AS-13)"
    assert "Do NOT redesign" in noop["prompt"]["text"], "the no-op case now mutates"
    live = next(c for c in m["cases"] if "live" in c["id"])
    assert "AGENT_INTEROP_LIVE" in live["checks"]["tool"][0]["command"], \
        "the live case has no probe — it cannot NOT_RUN"
    flat = " ".join(json.dumps(m, ensure_ascii=False).split())
    for needle in ("actual output oracle", "raw result", "with/without-skill",
                   "NOT_RUN", "grader convenience"):
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
    case("the pinned MCP example proves 401 + scoped old constructor (AS-12)",
         t_pinned_mcp_case)
    case("the negative case refuses to load the skill", t_negative_refuses_to_load)
    case("protocol routing is not decided by the word long-running (AS-13)",
         t_routing_not_by_the_word)
    case("unsupported Tasks falls back, not to A2A; live probe-gated (AS-13, AS-12)",
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
