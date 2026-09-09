#!/usr/bin/env python3
"""FIX-AS-11.01 — the approval grant contract (sherlock audit, AS-11).

The finding: `confirm: true` was presented as protecting a destructive action,
but the MODEL can set the boolean itself — it is not user approval. And "any
two are safe" gave blanket safety to any pair of the lethal-trifecta
capabilities, when untrusted content + write causes damage with no private-data
access.

The fix under test: `confirm: true` is named a SYNTAX GUARD; real user approval
is a verifiable grant bound to principal/action/arguments/expiry (or an
existing authorization), and a stale grant does not authorize changed
arguments; the trifecta is a sufficient config for a specific exfiltration
risk, not a complete model. Documented in tools.md, and the grant/verification
rules are run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-harness",
                   "references", "tools.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_contract():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("`confirm: true` is a SYNTAX GUARD, not user approval",
                   "the MODEL can\nset the boolean itself".replace("\n", " "),
                   "verifiable grant from a trusted control plane, bound to\nthe principal, "
                   "action, exact arguments and an expiry".replace("\n", " "),
                   "a stale grant does NOT authorize changed arguments",
                   "a client-supplied\nboolean creates no authorization at all".replace("\n", " "),
                   "\"any two are safe\" over-claims",
                   "SUFFICIENT configuration for one SPECIFIC risk"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"
    assert "Any two are safe. All three in one session" not in flat, \
        "the 'any two are safe' claim survived"


# ---------------- the grant contract, executed


def is_authorized(grant, request):
    """A grant authorizes a request only if it is a trusted-plane grant bound to
    the same principal/action/arguments and not expired. A bare boolean is not a
    grant."""
    if grant is True or grant is None:
        return False                              # a boolean/absent grant authorizes nothing
    if grant.get("issuer") != "control-plane":
        return False
    if grant.get("principal") != request.get("principal"):
        return False
    if grant.get("action") != request.get("action"):
        return False
    if grant.get("arguments") != request.get("arguments"):
        return False                              # changed arguments ⇒ stale
    if request.get("now", 0) > grant.get("expiry", 0):
        return False
    return True


def t_client_boolean_is_not_authorization():
    req = {"principal": "u", "action": "delete", "arguments": {"id": 7}, "now": 10}
    assert is_authorized(True, req) is False, \
        "a client-supplied boolean authorized a destructive action — the finding itself"
    assert is_authorized({"confirm": True}, req) is False, \
        "a model-set confirm object authorized the action"


def t_valid_grant_authorizes_its_exact_request():
    req = {"principal": "u", "action": "delete", "arguments": {"id": 7}, "now": 10}
    grant = {"issuer": "control-plane", "principal": "u", "action": "delete",
             "arguments": {"id": 7}, "expiry": 100}
    assert is_authorized(grant, req) is True


def t_stale_grant_does_not_authorize_changed_arguments():
    grant = {"issuer": "control-plane", "principal": "u", "action": "delete",
             "arguments": {"id": 7}, "expiry": 100}
    changed = {"principal": "u", "action": "delete", "arguments": {"id": 999}, "now": 10}
    assert is_authorized(grant, changed) is False, \
        "a grant for id 7 authorized a delete of id 999 — arguments not bound"


def t_expired_grant_is_refused():
    grant = {"issuer": "control-plane", "principal": "u", "action": "delete",
             "arguments": {"id": 7}, "expiry": 100}
    late = {"principal": "u", "action": "delete", "arguments": {"id": 7}, "now": 200}
    assert is_authorized(grant, late) is False, "an expired grant still authorized"


def t_trifecta_pair_is_not_blanket_safe():
    # untrusted content + write, no private data: still a damage path
    caps = {"untrusted_content", "write"}
    exfiltration_possible = {"private_data", "untrusted_content", "external_comms"} <= caps
    assert not exfiltration_possible, "this pair is not the exfiltration triangle"
    # ...but it is not 'safe' — a damaging action is possible without private data
    damage_possible = "untrusted_content" in caps and "write" in caps
    assert damage_possible, "the write+untrusted damage path was treated as safe"


def main():
    case("the doctrine states the grant contract", t_doctrine_states_the_contract)
    case("a client boolean is not authorization", t_client_boolean_is_not_authorization)
    case("a valid grant authorizes its exact request",
         t_valid_grant_authorizes_its_exact_request)
    case("a stale grant does not authorize changed arguments",
         t_stale_grant_does_not_authorize_changed_arguments)
    case("an expired grant is refused", t_expired_grant_is_refused)
    case("a trifecta pair is not blanket safe", t_trifecta_pair_is_not_blanket_safe)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
