#!/usr/bin/env python3
"""FIX-AS-01.02 — reconciliation and serialization (sherlock audit, AS-01,
second leaf; depends on FIX-AS-01.01's saga state model).

The contract under test: an unknown outcome is reconciled BY the operation's
own idempotency key (never by guessing from ambient state); the tenant's
ledger carries a revision and every resolve is a CAS — a late or concurrent
HTTP response that lost the race aborts and re-reads, never blind-writes; a
compensation reverses only its OWN confirmed operation; and repeated
reconciliation is idempotent — one-way edges, zero new writes the second time.

Acceptance, run as behaviour: a late response for operation A cannot
compensate over operation B's newer ledger state, and reconciling twice
changes nothing the second time.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator",
                   "references", "llm-proxy-billing.md")

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


def t_doctrine_states_the_three_rules():
    text = open(DOC, encoding="utf-8").read()
    flat = " ".join(text.split())
    for needle in ("## Reconciling an unknown",
                   "Ask by the operation's own idempotency key",
                   "only the key isolates yours",
                   "every resolve is a CAS",
                   "aborts and re-reads, it never blind-writes",
                   "Compensate only your own confirmed operation",
                   "never grounds to touch B's rows",
                   "Repeated reconciliation is idempotent",
                   "one-way edges"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"
    assert "[Reconciling an unknown](#reconciling-an-unknown)" in text, \
        "the Contents list does not route to the section"


# --------------------- the documented rules, run as behaviour


class Ledger:
    """A tenant ledger with a revision, exactly as the doctrine states it."""

    def __init__(self, balance=100):
        self.balance = balance
        self.revision = 0
        self.audit = []

    def read(self):
        return {"balance": self.balance, "revision": self.revision}

    def cas_write(self, expected_revision, delta, note):
        if expected_revision != self.revision:
            return False  # lost the race: abort and re-read, never blind-write
        self.balance += delta
        self.revision += 1
        self.audit.append(note)
        return True


class Provider:
    """The external API, queryable by idempotency key — never by guesswork."""

    def __init__(self):
        self.applied_ops = set()

    def apply(self, op_id):
        self.applied_ops.add(op_id)

    def did_apply(self, op_id):
        return op_id in self.applied_ops


class Op:
    def __init__(self, op_id, delta):
        self.op_id = op_id
        self.delta = delta
        self.state = "unknown"          # this leaf starts where FIX-AS-01.01 left off
        self.read_revision = None       # what the late response saw

    def reconcile(self, ledger, provider):
        """One-way edges; CAS on the revision read NOW; own delta only."""
        if self.state != "unknown":
            return self.state           # idempotent: nothing left to do
        snapshot = ledger.read()
        if provider.did_apply(self.op_id):
            self.state = "applied"
            return self.state
        # confirmed not applied: compensate exactly this operation's delta
        if not ledger.cas_write(snapshot["revision"], -self.delta,
                                f"compensation:{self.op_id}"):
            return "retry"              # the ledger moved: re-read, never blind-write
        self.state = "compensated"
        return self.state


def t_late_response_cannot_compensate_anothers_ledger():
    ledger, provider = Ledger(balance=100), Provider()
    op_a = Op("op-a", delta=15)
    ledger.cas_write(0, +15, "apply:op-a")          # A applied locally, outcome unknown

    stale_revision = ledger.read()["revision"]      # the late response's view of the world
    op_b = Op("op-b", delta=30)
    provider.apply("op-b")
    ledger.cas_write(1, +30, "apply:op-b")          # B lands and moves the revision

    # A's late compensation arrives holding the pre-B revision: a blind write here
    # would "restore" values B already superseded.
    ok = ledger.cas_write(stale_revision, -15, "compensation:op-a")
    assert not ok, "a stale revision blind-wrote over a newer ledger"
    assert ledger.balance == 145 and "compensation:op-a" not in ledger.audit

    # the honest path: re-read, then compensate ONLY op-a's delta
    verdict = op_a.reconcile(ledger, provider)
    assert verdict == "compensated"
    assert ledger.balance == 130, f"the compensation touched more than op-a's delta: {ledger.balance}"
    assert "apply:op-b" in ledger.audit and ledger.audit[-1] == "compensation:op-a"


def t_reconciliation_asks_by_key_not_by_guess():
    ledger, provider = Ledger(), Provider()
    provider.apply("op-x")
    op = Op("op-x", delta=10)
    assert op.reconcile(ledger, provider) == "applied"
    assert ledger.audit == [], "an applied operation was compensated anyway"

    other = Op("op-y", delta=10)                     # same delta, different key
    assert other.reconcile(ledger, provider) == "compensated", \
        "the reconciler credited op-y with op-x's application — it guessed by value"


def t_repeated_reconciliation_is_idempotent():
    ledger, provider = Ledger(), Provider()
    op = Op("op-z", delta=20)
    first = op.reconcile(ledger, provider)
    assert first == "compensated"
    audit_after_first = list(ledger.audit)
    revision_after_first = ledger.read()["revision"]
    for _ in range(3):
        assert op.reconcile(ledger, provider) == "compensated"
    assert ledger.audit == audit_after_first, "a repeat reconcile wrote new audit rows"
    assert ledger.read()["revision"] == revision_after_first, \
        "a repeat reconcile moved the revision"


def t_lost_cas_retries_and_lands_once():
    ledger, provider = Ledger(), Provider()
    op = Op("op-r", delta=5)
    # somebody moves the ledger between the reconciler's read and its write —
    # simulated by bumping the revision after the snapshot would be taken
    snapshot = ledger.read()
    ledger.cas_write(snapshot["revision"], +1, "interloper")
    assert not ledger.cas_write(snapshot["revision"], -5, "compensation:op-r"), \
        "the stale write went through"
    assert op.reconcile(ledger, provider) == "compensated"  # fresh read, lands once
    assert ledger.audit.count("compensation:op-r") == 1


def main():
    case("the doctrine states the three rules and the idempotence",
         t_doctrine_states_the_three_rules)
    case("a late response cannot compensate another's ledger",
         t_late_response_cannot_compensate_anothers_ledger)
    case("reconciliation asks by key, never by guess", t_reconciliation_asks_by_key_not_by_guess)
    case("repeated reconciliation is idempotent", t_repeated_reconciliation_is_idempotent)
    case("a lost CAS retries and lands exactly once", t_lost_cas_retries_and_lands_once)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"OK ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
