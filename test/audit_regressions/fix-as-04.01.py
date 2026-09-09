#!/usr/bin/env python3
"""FIX-AS-04.01 — the fake-edge test is typed (sherlock audit, AS-04).

The finding: "No payload, no edge" and the delete step did not distinguish
dataflow from control flow, approval, or shared state — so backup→migration,
approval→charge and lease→edit (all payload-free, all real) were deletable
by the doctrine's own rule.

The fix under test, run as the documented behaviour: an edge is typed
data/control/authorization/resource; deletion requires NONE of the four;
side-effect footprints and read/write sets are compared before fan-out, so
independent read-only reviews genuinely parallelise while two writers of one
resource serialise.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REFS = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-orchestrator")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_types_the_edge():
    ge = " ".join(open(os.path.join(REFS, "references", "graph-engineering.md"),
                       encoding="utf-8").read().split())
    for needle in ("**data** | A's output enters B",
                   "**control** | ordering only",
                   "**authorization** | a decision that permits B",
                   "**resource** | A and B touch one thing",
                   "type it, and write the rationale on the arrow",
                   "an empty payload cell justifies deletion only when there is "
                   "also no causal, permissive or resource constraint",
                   "compare the branches' side-effect footprints and read/write sets"):
        assert needle in ge, f"graph-engineering.md no longer states {needle!r}"
    assert "No payload named ⇒ delete the edge" not in ge, \
        "the untyped delete rule survived in the workflow defaults"
    sk = " ".join(open(os.path.join(REFS, "SKILL.md"), encoding="utf-8").read().split())
    assert "Type every edge: data, control, authorization or resource" in sk
    assert "No payload, no edge." not in sk, "the untyped rule survived in SKILL.md"


# ---------------- the documented test, executed


def edge(a, b, kind=None, rationale=None):
    return {"from": a, "to": b, "kind": kind, "rationale": rationale}


def keep(e):
    """Step 3-5 as documented: any of the four kinds keeps the edge."""
    return e["kind"] in ("data", "control", "authorization", "resource")


def fan_out_plan(nodes):
    """Step 6: read/write sets before fan-out. Writers of one resource
    serialise (a resource edge is drawn); read-only branches parallelise."""
    edges = []
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            shared = set(a["writes"]) & (set(b["writes"]) | set(b["reads"]))
            shared |= set(b["writes"]) & set(a["reads"])
            if shared:
                edges.append(edge(a["id"], b["id"], "resource",
                                  f"both touch {sorted(shared)}"))
    parallel = [n["id"] for n in nodes
                if not any(e for e in edges if n["id"] in (e["from"], e["to"]))]
    return edges, parallel


def t_payload_free_constraints_survive():
    for e in (edge("backup", "migration", "control", "migration is unsafe before backup"),
              edge("approval", "charge", "authorization", "the decision permits the money"),
              edge("lease", "edit", "authorization", "the lease permits the write")):
        assert keep(e), f"{e['from']}→{e['to']} was deleted — the finding itself"


def t_truly_fake_edge_still_dies():
    e = edge("review-A", "review-B")
    assert not keep(e), "an untyped, unconstrained edge was kept"


def t_two_writers_serialise_readers_parallelise():
    nodes = [
        {"id": "review-1", "reads": ["src/"], "writes": []},
        {"id": "review-2", "reads": ["src/"], "writes": []},
        {"id": "write-ledger-a", "reads": [], "writes": ["ledger.md"]},
        {"id": "write-ledger-b", "reads": [], "writes": ["ledger.md"]},
    ]
    edges, parallel = fan_out_plan(nodes)
    assert "review-1" in parallel and "review-2" in parallel, \
        "independent read-only reviews were serialised without cause"
    assert any(e["kind"] == "resource" and "ledger.md" in e["rationale"]
               for e in edges), \
        "two writers of one ledger fanned out unserialised — the lost-write race"


def t_reader_of_a_writers_target_is_an_edge_too():
    nodes = [{"id": "writer", "reads": [], "writes": ["state.json"]},
             {"id": "reader", "reads": ["state.json"], "writes": []}]
    edges, parallel = fan_out_plan(nodes)
    assert edges and not parallel, \
        "a reader raced the writer of its own input"


def main():
    case("the doctrine types the edge and drops the untyped delete rule",
         t_doctrine_types_the_edge)
    case("backup→migration, approval→charge, lease→edit survive",
         t_payload_free_constraints_survive)
    case("a truly fake edge still dies", t_truly_fake_edge_still_dies)
    case("two writers serialise; read-only reviews parallelise",
         t_two_writers_serialise_readers_parallelise)
    case("a reader of a writer's target is an edge too",
         t_reader_of_a_writers_target_is_an_edge_too)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
