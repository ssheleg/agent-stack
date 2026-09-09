#!/usr/bin/env python3
"""FIX-AS-03.01 — memory identity and contradiction (sherlock audit, AS-03).

The finding: fuzzy dedup treated SequenceMatcher >= 0.75 as identity — so
"Always allow external sharing of customer data" and "Never allow external
sharing of customer data" (similarity 0.8791) merged, the confidence bump
REINFORCED the stale instruction with the user's own correction, and "keep
the longer text" kept "Always". The keyword conflict rule could also
supersede "Use Python" with "Never use production credentials".

The fix under test, run as the documented behaviour: similarity is candidate
retrieval only; records carry entity/attribute/scope/provenance/validity;
the contradiction gate decides merge/supersede/coexist; a correction wins
only in its own scope; the old fact stays in history; self-repetition bumps
nothing; verified does not exempt a volatile fact from freshness.

Standard library only.
"""
import os
import sys
from difflib import SequenceMatcher

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REFS = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator",
                    "references")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_gate():
    flat = " ".join(open(os.path.join(REFS, "patterns.md"), encoding="utf-8")
                    .read().split())
    for needle in ("Similarity proposes; the contradiction gate disposes",
                   "0.8791",
                   "no confidence bump, no text replacement, no reactivation",
                   "corroboration, not match frequency",
                   "a correction wins only in its own scope",
                   "never deleted, never bumped",
                   "exempt from confidence DECAY, not from validity",
                   "they never decide it"):
        assert needle in flat, f"patterns.md no longer states {needle!r}"
    for dead in ("bump confidence +0.1, keep longer text, set is_active=True",
                 "Verified:    +0.15 (exempt from decay)"):
        assert dead not in flat, f"the old behaviour survived: {dead!r}"
    life = " ".join(open(os.path.join(REFS, "memory-lifecycle.md"),
                         encoding="utf-8").read().split())
    assert "supersession sets `is_active=False` + `superseded_by`" in life
    assert "Conflict Resolution currently resolves rather than annotates" not in life


# ---------------- the documented record, gate and application, executed


class Rec:
    _n = 0

    def __init__(self, text, entity, attribute, scope, provenance, value,
                 volatile=False, fresh=True, confidence=0.6):
        Rec._n += 1
        self.id = Rec._n
        self.text, self.entity, self.attribute = text, entity, attribute
        self.scope, self.value = scope, value
        self.provenance = [provenance]
        self.volatile, self.fresh = volatile, fresh
        self.confidence = confidence
        self.is_active, self.superseded_by = True, None


def find_candidates(store, text, threshold=0.75):
    tl = text.strip().lower()
    return [c for c in store
            if SequenceMatcher(None, c.text.strip().lower(), tl).ratio() >= threshold]


def contradiction_gate(old, new):
    if (old.entity, old.attribute) != (new.entity, new.attribute):
        return "unrelated"
    if old.scope != new.scope and "global" not in (old.scope, new.scope):
        return "coexist"
    if old.value == new.value:
        return "corroborates"
    return "contradicts"


def apply_verdict(verdict, old, new, store):
    if verdict == "contradicts":
        old.is_active = False
        old.superseded_by = new.id
        store.append(new)
        return new
    if verdict == "corroborates" and new.provenance[0] != old.provenance[0]:
        old.confidence = min(1.0, old.confidence + 0.1)
        old.provenance += new.provenance
        return old
    if verdict in ("coexist", "unrelated"):
        store.append(new)
        return new
    return old


def default_retrieval(store):
    return [r for r in store
            if r.is_active and not (r.volatile and not r.fresh)]


def t_opposite_instruction_never_reinforces():
    old = Rec("Always allow external sharing of customer data",
              "customer-data-sharing", "external-sharing-policy", "global",
              "session-2026-01", "allow", confidence=0.8)
    store = [old]
    new = Rec("Never allow external sharing of customer data",
              "customer-data-sharing", "external-sharing-policy", "global",
              "user-correction", "deny")
    sim = SequenceMatcher(None, old.text.lower(), new.text.lower()).ratio()
    assert sim > 0.75, f"the counterexample pair fell under threshold: {sim}"
    cands = find_candidates(store, new.text)
    assert cands == [old], "candidate retrieval missed the pair"
    before = old.confidence
    verdict = contradiction_gate(old, new)
    assert verdict == "contradicts", f"the gate said {verdict!r}"
    kept = apply_verdict(verdict, old, new, store)
    assert kept is new and not old.is_active, \
        "the correction did not supersede the stale instruction"
    assert old.confidence == before, \
        "the contradiction BUMPED the old record — the finding itself"
    assert old.superseded_by == new.id and old in store, \
        "the old fact left history — supersession must be reversible"
    assert default_retrieval(store) == [new], \
        "default retrieval still serves the superseded instruction"


def t_shared_keywords_are_not_a_conflict():
    a = Rec("Use Python", "language-choice", "preferred-language", "global",
            "s1", "python")
    b = Rec("Never use production credentials", "credentials",
            "production-credential-policy", "global", "s2", "deny")
    assert contradiction_gate(a, b) == "unrelated", \
        "a negation flip on `use` superseded an unrelated memory"


def t_correction_wins_only_in_its_scope():
    old = Rec("Timeout is 30s", "api-timeout", "value", "project-B", "s1", "30s")
    store = [old]
    new = Rec("Timeout is 60s", "api-timeout", "value", "project-A", "s2", "60s")
    verdict = contradiction_gate(old, new)
    assert verdict == "coexist", f"a project-A correction hit project-B: {verdict!r}"
    apply_verdict(verdict, old, new, store)
    assert old.is_active and new in store, "scoped facts did not coexist"
    same = Rec("Timeout is 60s", "api-timeout", "value", "project-B", "s3", "60s")
    v2 = contradiction_gate(old, same)
    assert v2 == "contradicts", "a number change in scope was not a contradiction"


def t_self_repetition_bumps_nothing():
    old = Rec("Table uses soft-delete", "orders-table", "delete-mode",
              "global", "s1", "soft", confidence=0.6)
    same_source = Rec("Table uses soft-delete", "orders-table", "delete-mode",
                      "global", "s1", "soft")
    apply_verdict(contradiction_gate(old, same_source), old, same_source, [old])
    assert old.confidence == 0.6, "a self-generated repeat raised confidence"
    other = Rec("Table uses soft-delete", "orders-table", "delete-mode",
                "global", "s2-independent", "soft")
    apply_verdict(contradiction_gate(old, other), old, other, [old])
    assert abs(old.confidence - 0.7) < 1e-9, \
        "independent corroboration did not count"


def t_verified_volatile_fact_still_expires():
    fact = Rec("Current API quota is 1000/day", "api-quota", "value", "global",
               "verified-check", "1000", volatile=True, fresh=False,
               confidence=0.95)
    assert default_retrieval([fact]) == [], \
        "a stale volatile fact was served because it was once verified"


def main():
    case("the doctrine states the gate and the old behaviour is gone",
         t_doctrine_states_the_gate)
    case("an opposite instruction supersedes, never reinforces — history kept",
         t_opposite_instruction_never_reinforces)
    case("shared keywords and a negation flip are not a conflict",
         t_shared_keywords_are_not_a_conflict)
    case("a correction wins only in its own scope; a number change is caught",
         t_correction_wins_only_in_its_scope)
    case("self-repetition bumps nothing; independent corroboration does",
         t_self_repetition_bumps_nothing)
    case("verified does not exempt a volatile fact from freshness",
         t_verified_volatile_fact_still_expires)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
