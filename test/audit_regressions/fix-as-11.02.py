#!/usr/bin/env python3
"""FIX-AS-11.02 — threat-model limits: the trifecta is not full security
(sherlock audit, AS-11 leaf 2, on FIX-AS-11.01).

The rule under test: the audit treats the lethal trifecta as a SPECIFIC
exfiltration pattern, not a complete threat model; it evaluates capabilities
and effects SEPARATELY, so a session missing one trifecta leg is NOT a PASS
for an unrelated destructive effect. Documented in audit.md, and the
capability/effect separation is run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-harness",
                   "references", "audit.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_limit():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("The lethal trifecta is a specific EXFILTRATION pattern, not a full\nthreat\n  "
                   "model".replace("\n  ", " ").replace("\n", " "),
                   "a session MISSING one leg is not thereby\n  \"safe\"".replace("\n  ", " ").replace("\n", " "),
                   "Audit **capabilities and effects SEPARATELY**",
                   "is an unrelated destructive\n  effect".replace("\n  ", " ").replace("\n", " "),
                   "\"Only two of the three, therefore a PASS\" is the mistake"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"


# ---------------- the capability/effect audit, executed


def exfiltration_risk(caps):
    return {"private_data", "untrusted_content", "external_comms"} <= set(caps)


def destructive_effect_risk(caps):
    """A damaging action does not need private data: untrusted content + a write
    capability is enough."""
    return "untrusted_content" in caps and "write" in caps


def audit_session(caps):
    """Findings are the UNION of separately-evaluated risks — a clean
    exfiltration axis does not clear the destructive-effect axis."""
    findings = []
    if exfiltration_risk(caps):
        findings.append("exfiltration")
    if destructive_effect_risk(caps):
        findings.append("destructive-effect")
    return findings


def t_missing_leg_is_not_a_pass_for_a_destructive_effect():
    # untrusted content + write, NO private data → not the exfiltration triangle,
    # but still a destructive-effect finding.
    caps = {"untrusted_content", "write"}
    assert not exfiltration_risk(caps), "this set is not the exfiltration triangle"
    findings = audit_session(caps)
    assert "destructive-effect" in findings, \
        "a missing trifecta leg PASSed a session with an unrelated destructive "\
        "effect — the finding itself"
    assert "exfiltration" not in findings


def t_full_trifecta_is_an_exfiltration_finding():
    caps = {"private_data", "untrusted_content", "external_comms"}
    assert "exfiltration" in audit_session(caps)


def t_axes_are_independent():
    # a session can be clean on one axis and flagged on the other
    only_exfil = {"private_data", "untrusted_content", "external_comms"}
    assert audit_session(only_exfil) == ["exfiltration"]
    both = {"private_data", "untrusted_content", "external_comms", "write"}
    assert set(audit_session(both)) == {"exfiltration", "destructive-effect"}, \
        "the two risk axes were not evaluated separately"


def t_a_safe_session_has_neither():
    assert audit_session({"private_data"}) == []
    assert audit_session({"read", "external_comms"}) == []


def main():
    case("the doctrine states the trifecta's limit", t_doctrine_states_the_limit)
    case("a missing leg is not a PASS for a destructive effect",
         t_missing_leg_is_not_a_pass_for_a_destructive_effect)
    case("the full trifecta is an exfiltration finding",
         t_full_trifecta_is_an_exfiltration_finding)
    case("the capability and effect axes are independent", t_axes_are_independent)
    case("a genuinely safe session has neither finding", t_a_safe_session_has_neither)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
