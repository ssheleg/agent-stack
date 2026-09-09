#!/usr/bin/env python3
"""FIX-AS-07.01 — the order ban keeps the mandatory happens-before (sherlock
audit, AS-07).

The finding: the advice to avoid a brittle exact tool-order assertion had
hardened into a BAN on order — "as a set and a forbidden list, never as an
order" — which throws out the semantically mandatory happens-before
(authorization before effect, fresh read before write, commit before
publish).

The fix under test: forbid only the redundant EXACT GLOBAL sequence; assert
the mandatory edges as a PARTIAL order — reordering two independent reads
passes, reordering confirm/charge or acquire/write fails; and keep a
negative example beside the rubric. Documented in SKILL.md, and the
partial-order matcher is run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-evals", "SKILL.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_carves_out_partial_order():
    flat = " ".join(open(SKILL, encoding="utf-8").read().split())
    for needle in ("What is forbidden is the redundant **exact global sequence**, "
                   "not order as such",
                   "A few **happens-before** edges are semantically mandatory",
                   "authorization\nprecedes its effect".replace("\n", " "),
                   "a fresh read precedes the write depending on it",
                   "reordering two independent reads must\npass".replace("\n", " "),
                   "reordering confirm/charge or acquire/write must fail",
                   "keep the\nnegative example (a confirm-after-charge trace)".replace("\n", " ")):
        assert needle in flat, f"the doctrine no longer states {needle!r}"
    assert "as a **set and a forbidden list**, never as an order" not in flat, \
        "the total ban on order survived"


# ---------------- the partial-order matcher, executed


def satisfies_partial_order(trace, edges):
    """Every (a, b) edge means a must appear before b in the trace. Independent
    calls not named in any edge may appear in any order."""
    pos = {}
    for i, call in enumerate(trace):
        pos.setdefault(call, i)
    for a, b in edges:
        if a in pos and b in pos and pos[a] > pos[b]:
            return False
    return True


MANDATORY = [("authorize", "charge"), ("read_fresh", "write"), ("commit", "publish")]


def t_independent_reads_reorder_freely():
    edges = [("read_fresh", "write")]
    assert satisfies_partial_order(["read_a", "read_b", "read_fresh", "write"], edges)
    assert satisfies_partial_order(["read_b", "read_a", "read_fresh", "write"], edges), \
        "reordering two independent reads was rejected — the order ban's over-reach"


def t_confirm_after_charge_fails():
    assert satisfies_partial_order(["authorize", "charge"], [("authorize", "charge")])
    assert not satisfies_partial_order(["charge", "authorize"], [("authorize", "charge")]), \
        "confirm/charge reordering passed — a mandatory happens-before was not enforced"


def t_acquire_after_write_fails():
    edges = [("acquire", "write")]
    assert satisfies_partial_order(["acquire", "write"], edges)
    assert not satisfies_partial_order(["write", "acquire"], edges), \
        "write-before-acquire passed — the lease-before-edit edge was not enforced"


def t_partial_order_is_not_a_total_order():
    # a total-order assertion would reject a valid reordering of unrelated calls;
    # the partial order must not.
    edges = [("authorize", "charge")]
    assert satisfies_partial_order(
        ["log", "authorize", "metric", "charge", "notify"], edges), \
        "unrelated calls around a mandatory edge were rejected"


def main():
    case("the doctrine carves out the mandatory partial order",
         t_doctrine_carves_out_partial_order)
    case("two independent reads reorder freely", t_independent_reads_reorder_freely)
    case("confirm-after-charge fails", t_confirm_after_charge_fails)
    case("acquire-after-write fails", t_acquire_after_write_fails)
    case("the partial order is not a total order", t_partial_order_is_not_a_total_order)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
