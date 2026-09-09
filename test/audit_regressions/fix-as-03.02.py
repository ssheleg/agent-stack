#!/usr/bin/env python3
"""FIX-AS-03.02 — the temporal evidence lifecycle (sherlock audit, second
leaf of AS-03, on FIX-AS-03.01's contradiction gate).

The rules under test, run as the documented lifecycle: retrieval is not a
lifecycle event (repeated retrieval raises nothing); supersession is a
reversible annotation — the new dated fact keeps the replacement history,
the chain is walkable, restoring is clearing two fields; and a volatile
fact past its freshness window leaves default retrieval at ANY confidence,
verified included.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator",
                   "references", "memory-lifecycle.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_lifecycle():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("Retrieval is not a lifecycle event",
                   "Supersession is an annotation, and it is reversible",
                   "clearing two fields, not resurrecting a deleted row",
                   "`verified` is about confidence, never about time",
                   "nothing exempts a fact about the present from the present",
                   "The temporal evidence lifecycle"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"


# --------------- the documented lifecycle, executed


class Store:
    def __init__(self):
        self.rows = {}
        self.n = 0

    def add(self, value, observed_at, provenance, volatile=False,
            fresh_until=None, confidence=0.6, verified=False):
        self.n += 1
        self.rows[self.n] = {
            "id": self.n, "value": value, "observed_at": observed_at,
            "provenance": [provenance], "volatile": volatile,
            "fresh_until": fresh_until, "confidence": confidence,
            "verified": verified, "is_active": True, "superseded_by": None}
        return self.n

    def retrieve(self, rid):
        return dict(self.rows[rid])                    # a READ. Nothing moves.

    def corroborate(self, rid, provenance):
        r = self.rows[rid]
        if provenance in r["provenance"]:
            return False                               # self-repeat: no event
        r["confidence"] = min(1.0, r["confidence"] + 0.1)
        r["provenance"].append(provenance)
        return True

    def supersede(self, old_id, value, observed_at, provenance):
        new_id = self.add(value, observed_at, provenance)
        self.rows[old_id]["is_active"] = False
        self.rows[old_id]["superseded_by"] = new_id
        return new_id

    def restore(self, old_id):
        self.rows[old_id]["is_active"] = True
        self.rows[old_id]["superseded_by"] = None

    def default_retrieval(self, now):
        return [r["id"] for r in self.rows.values()
                if r["is_active"]
                and not (r["volatile"] and r["fresh_until"] is not None
                         and now > r["fresh_until"])]

    def history(self, rid):
        chain = [rid]
        while self.rows[chain[-1]]["superseded_by"]:
            chain.append(self.rows[chain[-1]]["superseded_by"])
        return chain


def t_repeated_retrieval_raises_nothing():
    s = Store()
    rid = s.add("timeout=30s", 100, "s1")
    before = s.rows[rid]["confidence"]
    for _ in range(50):
        s.retrieve(rid)
    assert s.rows[rid]["confidence"] == before, \
        "fifty retrievals raised confidence — the finding itself"
    assert s.corroborate(rid, "s1") is False and s.rows[rid]["confidence"] == before, \
        "a same-provenance repeat counted as corroboration"
    assert s.corroborate(rid, "s2") is True, "independent corroboration was refused"


def t_supersession_keeps_history_and_reverses():
    s = Store()
    a = s.add("plan=basic", 100, "s1")
    b = s.supersede(a, "plan=pro", 200, "s2")
    assert s.rows[a]["is_active"] is False and s.rows[a]["superseded_by"] == b
    assert a in s.rows and s.rows[a]["value"] == "plan=basic", \
        "the old dated fact left the store — history lost"
    assert s.history(a) == [a, b], "the replacement chain is not walkable"
    assert s.default_retrieval(300) == [b], \
        "default retrieval still serves the superseded value"
    s.restore(a)
    assert s.rows[a]["is_active"] and s.rows[a]["superseded_by"] is None, \
        "restoring was more than clearing two fields"


def t_volatile_verified_fact_expires():
    s = Store()
    rid = s.add("quota=1000/day", 100, "verified-check", volatile=True,
                fresh_until=500, confidence=1.0, verified=True)
    assert s.default_retrieval(400) == [rid], "a fresh volatile fact was hidden"
    assert s.default_retrieval(600) == [], \
        "a stale volatile fact was served at confidence 1.0 because verified"
    stable = s.add("company founded 2019", 100, "s1")
    assert stable in s.default_retrieval(10_000), \
        "a stable fact was expired — freshness applies to volatile facts only"


def main():
    case("the doctrine states the lifecycle", t_doctrine_states_the_lifecycle)
    case("repeated retrieval raises nothing; independence corroborates",
         t_repeated_retrieval_raises_nothing)
    case("supersession keeps the dated history and reverses cleanly",
         t_supersession_keeps_history_and_reverses)
    case("a volatile verified fact still expires; a stable one does not",
         t_volatile_verified_fact_expires)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
