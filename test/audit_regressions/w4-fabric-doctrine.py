#!/usr/bin/env python3
"""W4 — the Fabric doctrine in agent-interop says what its sources say
(sshlg-skills plan R23 and R24, wave 4 fix round, 2026-10-12).

The finding: three blind readings of 0.27.0's first cut found the trust-tier block
contradicting the rule it cited. It made a token mandatory for any service taking
calls across the machine boundary (DL-26 forbids requiring one from a T0 or T1 caller,
per caller, not per service), said a present token was "for attribution only" (DL-26:
verified, refused when invalid, used for attribution AND narrowing), placed callers by
network rather than by origin (DL-25), listed three of five human gates, and kept two
pre-tier sentences (fail closed with no issuer; the descriptor token retired) that the
amended DL-8 and DL-12 scope to the machine boundary. mcp.md claimed a caller "works
unchanged" when Tasks is negotiated, omitted `output` and `scope` from the envelope,
never said how an input request is answered, and did not teach the well-known
`degraded` list the contract defines.

The fix under test: the sourced sentences are present, the unsourced ones are gone,
and the pins name the commit that carries DL-25 and DL-26 (`3cb03ab`).

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REFS = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-interop", "references")
GATEWAY = os.path.join(REFS, "gateway.md")
MCP = os.path.join(REFS, "mcp.md")

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


def t_token_rule_is_dl26():
    g = flat(GATEWAY)
    assert "MUST NOT require a delegation token, an `approval/1` or a grant record from a T0 or T1 caller" in g, \
        "DL-26's MUST NOT is missing"
    assert "still must not require a token from its T0 and T1 callers" in g, \
        "tiers per caller, not per service, is missing"
    assert "a present but invalid token is never ignored" in g
    assert "used for attribution and for narrowing" in g
    for stale in ("optional and used for attribution only",
                  "takes calls across the machine boundary, or from outside people, requires it",
                  "nobody can attribute a cost"):
        assert stale not in g, f"unsourced sentence survived: {stale!r}"


def t_tier_by_origin():
    g = flat(GATEWAY)
    assert "A tier is the caller's origin's, not its connection's" in g
    assert "is T2 unless the relay proves the origin's tier" in g
    assert "T0 is trusted because the operator gave the instruction, not because of the connection" in g
    assert "RM-21" in g and "no machine is T1 yet" in g, "T1 enrolment is not named as RM-21, still open"
    for stale in ("same network", "Enrolment is what moves a machine from T2 to T1"):
        assert stale not in g, f"unsourced sentence survived: {stale!r}"


def t_pre_tier_text_scoped():
    g = flat(GATEWAY)
    assert "with no issuer a call fails closed" not in g, "fail-closed is not scoped to T2 (DL-8)"
    assert "For a T2 caller the issuer must be up to mint" in g
    assert "**Across the machine boundary**, once callers can mint" in g, "DL-12 is not scoped"
    assert "8e49fbd" not in g, "the delegation pin predates DL-25/DL-26"
    assert g.count("3cb03ab") >= 2, "header and worked example must both pin 3cb03ab"
    assert "read 2026-10-12" in g


def t_gates_and_money():
    g = flat(GATEWAY)
    assert "a sign-in, a consent, a payment, a top-up, and a secret typed into a hidden prompt" in g, \
        "the five human gates are not all listed"
    assert "L0 — the estate's total across provider keys — the project's limit (L1) and each provider key's own ceiling" in g
    assert "`slotsRequireGrant: when-token`" in g and "`keyserverRequiresDelegation` is `off`" in g, \
        "token-less T0 metering is not named"
    assert "This is the T2 path" in g


def t_mcp_jobs_and_degraded():
    m = flat(MCP)
    assert "works unchanged when the server later negotiates Tasks" not in m, \
        "the unsourced forward-compatibility claim survived"
    assert "A caller that does not negotiate Tasks keeps receiving the job handle" in m
    assert "`done`, `proof`, `scope` and `notVerified` beside `output`" in m
    assert "`inputResponses`" in m and "`tasks/update`" in m
    assert "whose `degraded` list is always present: an empty list asserts full health" in m
    assert "`setup: true`" in m
    assert "estate convention with no contract home yet" in m


def main():
    case("the token rule is DL-26: per caller, verified, refused, narrowing", t_token_rule_is_dl26)
    case("a tier is placed by origin; T1 waits on RM-21", t_tier_by_origin)
    case("fail-closed and the descriptor token are scoped; pins carry DL-25/DL-26",
         t_pre_tier_text_scoped)
    case("five human gates, three money levels, token-less metering", t_gates_and_money)
    case("mcp.md: job handle, envelope, input responses, well-known degraded",
         t_mcp_jobs_and_degraded)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
