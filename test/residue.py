#!/usr/bin/env python3
"""What did this run leave on disk? — one ledger, and it prints even when the answer is nothing.

**Ported from `make-skill/test/residue.py`, not reinvented.** That repository measured the
same defect first and shipped the answer; a second implementation of one ledger is how two
gates end up disagreeing about what a clean run leaves. The differences are the prefix, the
suite it accounts for, and this paragraph.

A run produces more than a diff. `test/plant_guard_test.py` built a small tree per case and
removed none of them, and — the part that matters — nothing said so. Measured here on
2026-08-20 with

    find "$TMPDIR" -maxdepth 4 -type f -path '*/copy/sub/b.sh' | wc -l

before and after one run of the fixture: **2568 → 2576, eight nameless `tmpXXXXXXXX` trees
per run**, and the gate printed nothing about any of them. The fixture that leaks them is
byte-identical (md5 `623a086d10a04940573c31cbebb93e31`) in `agent-stack` and
`seo-aeo-audit`; those 2576 trees are the accumulation of every sibling's runs, not this
one's, and they are reported rather than swept — see the board row.

A `TemporaryDirectory` around each one closes the leak. It does not close the defect,
because the defect is that a completed run said nothing about what it left, so the next
leak is invisible in exactly the same way. So every temp tree in this suite is taken
through `workspace()`, and every run ends with one line naming its residue — `nothing`
included. That line is the check: the next leak shows up in the gate's own output rather
than in somebody's `du`.

**A failing case keeps its tree, deliberately.** A plant is debugged by reading the copy
it landed in, and a cleanup that runs only on the pass path deletes the evidence exactly
when it is wanted. So a case that fails — or raises anything at all, including an error
that is not an assertion — keeps its workspace; the report names the path, names the case
that owns it, and prints the `rm -rf` that ends it. A clean case's tree goes at exit.

The prefix is part of the mechanism: `agent-stack-test-…` makes any future residue
attributable to this suite by name. The 2576 directories measured above are plain
`tmpXXXXXXXX` and are indistinguishable from every other program's — which is why they
have to be reported and left alone rather than swept.

    import residue
    residue.open_case(name)
    d = residue.workspace("plant-guard")  # removed iff the owning case passed
    residue.close_case(name)              # only on success — see above
    residue.report()                      # also wired to atexit, so it cannot be skipped

Zero dependencies, standard library only, like everything else here.
"""
import atexit
import os
import shutil
import sys
import tempfile

PREFIX = "agent-stack-test-"

_created = []        # [(path, owner)] every workspace this run made, in order
_incomplete = set()  # cases that did not finish clean; their workspaces are kept
_owner = None
_reported = False


def open_case(name):
    """Everything created from here on belongs to `name` until it closes."""
    global _owner
    _owner = name
    _incomplete.add(name)


def close_case(name, ok=True):
    """Call with ok=True only when the case passed — a kept tree is the evidence."""
    global _owner
    if ok:
        _incomplete.discard(name)
    _owner = None


def workspace(tag="tree"):
    """A temp directory this run owns and will account for at exit."""
    path = tempfile.mkdtemp(prefix=PREFIX, suffix="-" + tag)
    _created.append((path, _owner))
    return path


def _keep(owner):
    # An unowned workspace — created outside any case — is kept only when the run as a
    # whole is red, because nobody can say which case would want to read it.
    return bool(_incomplete) if owner is None else owner in _incomplete


def report(stream=None):
    """Remove what may go, keep what a failure may need, and say which — on every path.

    Returns (kept, removed) so a fixture can assert on the decision rather than on the
    wording. Idempotent: registered with `atexit` and safe to call by hand as well.
    """
    global _reported
    if _reported:
        return [], []
    _reported = True
    stream = stream or sys.stdout
    kept, removed = [], []
    for path, owner in _created:
        if _keep(owner):
            kept.append((path, owner))
            continue
        shutil.rmtree(path, ignore_errors=True)
        if os.path.exists(path):
            # Honest degradation: a tree that refused to go is residue, not a pass.
            kept.append((path, owner))
        else:
            removed.append(path)
    total = len(_created)
    if not kept:
        print("residue: this run left nothing — %d temp tree(s) created, %d removed"
              % (total, len(removed)), file=stream)
    else:
        print("residue: %d of %d temp tree(s) KEPT — the case did not pass and the copy "
              "is the evidence:" % (len(kept), total), file=stream)
        for path, owner in kept:
            print("    %s  <- %s" % (path, owner or "no case"), file=stream)
        print("  %d removed. When you are done reading them: rm -rf %s"
              % (len(removed), " ".join(p for p, _ in kept)), file=stream)
    stream.flush()
    return kept, removed


atexit.register(report)
