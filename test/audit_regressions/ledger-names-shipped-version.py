#!/usr/bin/env python3
"""The verification ledger names the version this tree ships.

docs/evidence/verification.md's first `## Release candidate: vX.Y.Z` heading must equal
package.json's version. The sshlg-skills hub refuses to pin a member whose ledger describes an
older version than it ships (its member-ledger ratchet); v0.33.0 shipped without its row on
2026-11-18 and needed v0.33.1, a release for one line. This check moves that refusal into the
member's own gate, before the tag. Stdlib only.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def first_candidate(text):
    m = re.search(r"^## Release candidate: v(\d+\.\d+\.\d+)\b", text, re.M)
    return m.group(1) if m else None


def check(root):
    with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
        version = json.load(fh)["version"]
    with open(os.path.join(root, "docs", "evidence", "verification.md"), encoding="utf-8") as fh:
        head = first_candidate(fh.read())
    if head != version:
        return f"verification.md heads with v{head}, package.json ships {version}: add the v{version} candidate row"
    return None


def self_test():
    assert first_candidate("x\n## Release candidate: v1.2.3 (2026-01-01)\n## Release candidate: v1.2.2\n") == "1.2.3"
    assert first_candidate("## Release candidate: v1.2.2\n") != "1.2.3", "a stale head must not pass"
    assert first_candidate("no rows") is None


self_test()
err = check(ROOT)
if err:
    print(f"FAIL  ledger names the shipped version: {err}")
    sys.exit(1)
print("  ok  ledger names the shipped version")
