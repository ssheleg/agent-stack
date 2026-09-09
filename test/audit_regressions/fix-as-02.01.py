#!/usr/bin/env python3
"""FIX-AS-02.01 — zero baseline is not an absent baseline (sherlock audit).

The finding: the spend-discovery rule tested `lastRecordedUsage == 0` to mean
"never watched" — so a key genuinely watched from zero had its FIRST real
spend eaten as baseline seeding. And any decrease was guessed as "key
recreated" and silently resynced, forgiving real discrepancies forever.

The fix under test: baseline_initialized / observed_at /
provider_key_generation live beside the sum; zero is a valid value; a
decrease on the SAME generation is an anomaly for reconciliation, never a
guessed resync.

Acceptance sequences, each with its predetermined ledger record and state:
uninitialized→5 (seed, no record), initialized(0)→5 (record 5 — the first
real spend counts), 5→8 (record 3), 8→2 same generation (anomaly, no
record), generation change (resync; the new key's first spend counted).

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator",
                   "references", "llm-proxy-billing.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_split():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("Zero is a value, not an absence",
                   "`baseline_initialized`, `observed_at`",
                   "provider_key_generation",
                   "decided by the flags, never by the sum",
                   "including the very first delta of a key whose baseline is a genuine 0",
                   "same generation** → **ANOMALY",
                   "A guessed resync here quietly forgives the difference forever"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"
    assert "lastRecordedUsage == 0 && currentUsage > 0" not in flat, \
        "the zero-means-absent test survived"


# ------------------- the documented state machine, run over the sequences


class Tracker:
    def __init__(self):
        self.initialized = False
        self.baseline = 0
        self.generation = None
        self.observed_at = None
        self.ledger = []
        self.state = "ok"

    def poll(self, usage, generation, at):
        if not self.initialized:
            self.initialized = True
            self.baseline, self.generation, self.observed_at = usage, generation, at
            return ("seeded", None)
        if generation != self.generation:
            self.baseline, self.generation, self.observed_at = usage, generation, at
            return ("resynced-new-generation", None)
        if usage > self.baseline:
            delta = usage - self.baseline
            self.baseline, self.observed_at = usage, at
            self.ledger.append(delta)
            return ("recorded", delta)
        if usage < self.baseline:
            self.state = "anomaly"
            return ("anomaly", None)
        self.observed_at = at
        return ("unchanged", None)


def t_acceptance_sequences():
    tr = Tracker()
    assert tr.poll(5, "gen-1", 1) == ("seeded", None), "uninitialized→5 must seed"
    assert tr.ledger == [], "seeding recorded spend"

    tr2 = Tracker()
    tr2.poll(0, "gen-1", 1)                      # initialized at a GENUINE zero
    verdict = tr2.poll(5, "gen-1", 2)
    assert verdict == ("recorded", 5), \
        f"the first real spend of a watched-from-zero key was eaten: {verdict}"
    assert tr2.ledger == [5]

    assert tr2.poll(8, "gen-1", 3) == ("recorded", 3)
    assert tr2.ledger == [5, 3]

    verdict = tr2.poll(2, "gen-1", 4)            # decrease, SAME generation
    assert verdict == ("anomaly", None), f"a same-key decrease was explained away: {verdict}"
    assert tr2.state == "anomaly" and tr2.ledger == [5, 3], \
        "the anomaly wrote or resynced anyway"

    tr3 = Tracker()
    tr3.poll(8, "gen-1", 1)
    assert tr3.poll(2, "gen-2", 2) == ("resynced-new-generation", None), \
        "a generation change was not resynced"
    assert tr3.poll(6, "gen-2", 3) == ("recorded", 4), \
        "the new key's first spend was not counted"
    assert tr3.ledger == [4]


def t_zero_then_zero_stays_clean():
    tr = Tracker()
    tr.poll(0, "g", 1)
    assert tr.poll(0, "g", 2) == ("unchanged", None)
    assert tr.state == "ok" and tr.ledger == []


def main():
    case("the doctrine splits zero from absent", t_doctrine_states_the_split)
    case("all five acceptance sequences produce their predetermined records",
         t_acceptance_sequences)
    case("zero then zero is unchanged, not an event", t_zero_then_zero_stays_clean)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
