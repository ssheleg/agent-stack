#!/usr/bin/env python3
"""FIX-AS-14.01 — "no evals" no longer makes the whole audit unfalsifiable
(sherlock audit, AS-14).

The finding: the doctrine prescribed "no evals → finding number one and
everything else is unfalsifiable", and "most agent bugs are prompt bugs" was
stated as measured reality. But a deterministic race, a hardcoded secret or a
miswired timeout are provable without a behavioural eval suite, and the
prompt-bug share was never measured.

The fix under test (agent-harness SKILL.md + references/audit.md):
* three proof classes separated — source-level invariant proof, deterministic
  reproduction, behavioural estimate; only the third inherits "no evals";
* no evals = a finding about UNKNOWN RELIABILITY; a proven concrete harm keeps
  its own priority and is never masked by the general finding;
* prompt-first survives as a diagnostic heuristic WITH exceptions — a broken
  unit invariant is not treated by rewording;
* the synthetic no-evals + double-charge repo, run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-harness", "SKILL.md")
AUDIT = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-harness",
                     "references", "audit.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def flat(path):
    with open(path, encoding="utf-8") as fh:
        return " ".join(fh.read().split())


def t_proof_classes_separated():
    d = flat(AUDIT)
    for cls in ("**source-level invariant proof**", "**deterministic reproduction**",
                "**behavioural estimate**"):
        assert cls in d, f"proof class {cls} missing"
    assert "survive a system with no evals untouched" in d
    assert "inherits the no-evals finding until one exists" in d


def t_no_evals_is_unknown_reliability():
    s = flat(SKILL)
    assert "a finding about UNKNOWN RELIABILITY" in s
    assert "Everything downstream is then unfalsifiable — including this audit." not in s, \
        "the everything-is-unfalsifiable claim survived in SKILL.md"
    assert 'a general "no evals" never masks a specific proven harm' in s
    d = flat(AUDIT)
    assert "everything else is unfalsifiable" not in d, \
        "the everything-else claim survived in audit.md"
    assert "prioritized by their concrete harm" in d


def t_prompt_first_is_a_heuristic_with_exceptions():
    s = flat(SKILL)
    assert "a diagnostic heuristic, with exceptions" in s
    assert "not a measured share of defects" in s
    assert "no rewording treats them" in s
    assert "most agent bugs are prompt bugs wearing a stack trace" not in s, \
        "the unmeasured universal claim survived as a heading"
    assert "The measured reality" not in s, \
        "vendor guidance is still presented as measured reality"


def t_traps_updated():
    d = flat(AUDIT)
    assert "does NOT inherit it" in d
    assert "the one finding with a victim gets deprioritized" in d
    assert "Treating a broken unit invariant with a prompt change." in d


# ---- the rule as behaviour: the synthetic no-evals repo with a double charge


def audit(findings, has_evals):
    """Each finding: {harm, proof}. Returns the kept findings with dispositions."""
    out = []
    if not has_evals:
        out.append({"id": "no-evals", "kind": "unknown-reliability",
                    "priority_from": "concrete harm of what it blocks"})
    for f in findings:
        if f["proof"] in ("source-invariant", "deterministic-repro"):
            out.append({**f, "falsifiable": True,
                        "priority_from": f["harm"]})
        else:
            out.append({**f, "falsifiable": has_evals,
                        "priority_from": f["harm"] if has_evals else "inherits no-evals"})
    return out


def t_double_charge_survives_no_evals():
    kept = audit([
        {"id": "double-charge", "harm": "a user is charged twice",
         "proof": "deterministic-repro"},
        {"id": "usually-recovers", "harm": "operator time",
         "proof": "behavioural-estimate"},
    ], has_evals=False)
    ids = [f["id"] for f in kept]
    assert "no-evals" in ids and "double-charge" in ids, \
        "one of the two findings was dropped"
    dc = next(f for f in kept if f["id"] == "double-charge")
    assert dc["falsifiable"] is True and dc["priority_from"] == "a user is charged twice", \
        "the proven double charge was masked by the general no-evals finding"
    est = next(f for f in kept if f["id"] == "usually-recovers")
    assert est["falsifiable"] is False, \
        "a behavioural estimate claimed falsifiability without evals"


def t_unit_invariant_not_fixed_by_prompt():
    remedy = {"source-invariant": "fix the code",
              "behavioural-estimate": "check the prompt first"}
    assert remedy["source-invariant"] == "fix the code"
    s = flat(SKILL)
    assert "source-level invariant violations are code bugs" in s


def main():
    case("the three proof classes are separated", t_proof_classes_separated)
    case("no evals = unknown reliability; proven harm never masked",
         t_no_evals_is_unknown_reliability)
    case("prompt-first is a heuristic with named exceptions",
         t_prompt_first_is_a_heuristic_with_exceptions)
    case("the traps carry both new rules", t_traps_updated)
    case("fixture: the no-evals repo keeps BOTH findings, double charge unmasked",
         t_double_charge_survives_no_evals)
    case("a broken unit invariant is not treated by rewording",
         t_unit_invariant_not_fixed_by_prompt)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
