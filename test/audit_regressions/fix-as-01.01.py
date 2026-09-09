#!/usr/bin/env python3
"""FIX-AS-01.01 — saga state model (sherlock audit, finding AS-01).

The finding: the billing doctrine called its DB+HTTP pattern "two-phase
commit" and prescribed compensating an API failure unconditionally — but an
HTTP outcome can be AMBIGUOUS (timeout, reset after send, 5xx), and 2PC has no
vocabulary for that. Compensating on a guess restores a ledger the provider's
key no longer matches, in the direction nobody can see.

The fix under test: the doctrine names the pattern a saga, every provider
operation carries an operation_id and a state pending → applied | unknown |
compensated, a documented HTTP timeout lands in `unknown` — never
auto-compensated — and resolves only by reconciliation on evidence.

The state model is also run as behaviour: a transition table implementing
exactly the documented states, driven over the acceptance cases both ways.

Standard library only.
"""
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator",
                   "references", "llm-proxy-billing.md")
SKILL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator", "SKILL.md")

checks = 0
failures = []


def case(name, fn):
    global checks
    try:
        fn()
        checks += 1
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


# ------------------------------------------------------------------ the doctrine


def t_doctrine_names_the_saga_not_2pc():
    text = open(DOC, encoding="utf-8").read()
    assert "## The saga across a DB and an external API" in text, "the section lost its saga name"
    assert "not two-phase commit" in text, "the doctrine no longer says the pattern is not 2PC"
    for needle in ("operation_id", "pending → applied | unknown | compensated",
                   "marked `unknown` and is NOT compensated",
                   "resolves only by **reconciliation**",
                   "outbox entry, not a log line",
                   "idempotency key"):
        assert needle in text, f"the doctrine no longer states {needle!r}"
    # The old prescription must be gone: no unconditional compensate-on-API-failure.
    assert "On API failure: a compensating transaction" not in text, \
        "the unconditional compensation prescription survived the rewrite"
    # The term is corrected everywhere in the file, headings and prose alike.
    stale = [l for l in text.splitlines() if re.search(r"two-phase commit", l, re.I)
             and "not two-phase commit" not in l]
    assert not stale, f"the file still calls it 2PC: {stale[:2]}"
    skill = open(SKILL, encoding="utf-8").read()
    assert "two-phase commit" not in skill, "SKILL.md still advertises the pattern as 2PC"
    assert "saga across database and provider API" in skill, \
        "SKILL.md description lost the saga wording"


# ------------------------------- the documented state model, run as behaviour


STATES = {"pending", "applied", "unknown", "compensated"}
# outcome of the provider call → what the doctrine says happens
DEFINITE_FAILURE = "definite_failure"   # 4xx refusal: provably not applied
AMBIGUOUS = "ambiguous"                 # timeout / reset after send / 5xx
SUCCESS = "success"


class Saga:
    def __init__(self):
        self.state = "pending"
        self.compensations = 0
        self.audit = ["intent"]

    def outcome(self, kind):
        assert self.state == "pending", f"outcome on a {self.state} operation"
        if kind == SUCCESS:
            self.state = "applied"
        elif kind == DEFINITE_FAILURE:
            self.compensations += 1
            self.audit.append("compensation")
            self.state = "compensated"
        elif kind == AMBIGUOUS:
            self.state = "unknown"      # and nothing else: no compensation, no retry
            self.audit.append("unknown")
        return self.state

    def reconcile(self, provider_applied):
        assert self.state == "unknown", "reconciliation is for unknown outcomes"
        if provider_applied:
            self.state = "applied"
        else:
            self.compensations += 1
            self.audit.append("compensation")
            self.state = "compensated"
        return self.state

    def may_retry(self):
        """A retry of an unknown is how one top-up applies twice."""
        return self.state == "compensated"


def t_timeout_is_not_auto_compensated():
    s = Saga()
    assert s.outcome(AMBIGUOUS) == "unknown"
    assert s.compensations == 0, "a timeout was compensated on a guess"
    assert not s.may_retry(), "an unknown operation was offered for retry"


def t_definite_failure_compensates_once():
    s = Saga()
    assert s.outcome(DEFINITE_FAILURE) == "compensated"
    assert s.compensations == 1
    assert "compensation" in s.audit
    assert s.may_retry(), "a compensated operation must be retryable"


def t_unknown_resolves_only_by_evidence():
    applied = Saga()
    applied.outcome(AMBIGUOUS)
    assert applied.reconcile(provider_applied=True) == "applied"
    assert applied.compensations == 0, \
        "the provider had applied the change and the ledger was rolled back anyway"

    not_applied = Saga()
    not_applied.outcome(AMBIGUOUS)
    assert not_applied.reconcile(provider_applied=False) == "compensated"
    assert not_applied.compensations == 1


def t_success_path_stays_clean():
    s = Saga()
    assert s.outcome(SUCCESS) == "applied"
    assert s.compensations == 0
    assert s.audit == ["intent"]


def main():
    case("the doctrine names the saga, the states, and never 2PC",
         t_doctrine_names_the_saga_not_2pc)
    case("a documented HTTP timeout is unknown, never auto-compensated",
         t_timeout_is_not_auto_compensated)
    case("a definite failure compensates exactly once, with its audit row",
         t_definite_failure_compensates_once)
    case("unknown resolves only by reconciliation evidence", t_unknown_resolves_only_by_evidence)
    case("the success path stays clean", t_success_path_stays_clean)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"OK ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
