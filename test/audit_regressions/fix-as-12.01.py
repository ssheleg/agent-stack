#!/usr/bin/env python3
"""FIX-AS-12.01 — the MCP shipping example pins its SDK (sherlock audit, AS-12).

The finding: the wire revision was pinned but not the SDK's distribution,
version or import — the example used FastMCP with transport settings in the
constructor, while the standalone `fastmcp` 2.x renamed the class and moved
those args. A reader could install either distribution and get a 404 the doc
itself warns about.

The fix under test (mcp-ship.md):
* the two distributions are distinguished; the official import is named and
  the standalone import explicitly refused;
* a pinned requirements block ties the snippets to the verified version and
  its date, re-pinned only with a re-run;
* v1/standalone is explicitly out of scope (or its own fixture);
* the lifecycle names the verified registration order (health BEFORE auth);
* proof is a localhost protocol call (health 200, unauth 401, initialize /
  tools/list / tools/call), never a string in markdown — asserted here as
  the doc's contract, and the acceptance list is machine-checked.

Standard library only.
"""
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-interop",
                   "references", "mcp-ship.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def raw():
    with open(DOC, encoding="utf-8") as fh:
        return fh.read()


def flat():
    return " ".join(raw().split())


def t_distributions_distinguished():
    d = flat()
    assert "TWO distributions" in d
    assert "from mcp.server.fastmcp import FastMCP" in d, "the official import is not named"
    assert "NOT `from fastmcp import FastMCP`" in d, "the standalone import is not refused"


def t_pin_is_the_identity():
    d = flat()
    assert re.search(r"mcp==\d+\.\d+\.\d+", d), "no exact SDK pin"
    assert "the pin IS the example's identity" in d
    assert "re-pin only together with a re-run" in d or "re-pin only with a re-run" in d.lower()
    assert "verified against (2026-08-13)" in d, "the tested date is not tied to the pin"


def t_v1_out_of_scope_and_lifecycle_order():
    d = flat()
    assert "explicitly **out of scope**" in d or "explicitly out of scope" in d
    assert "its OWN fixture verified against its own pin" in d
    assert "The health route registers BEFORE the auth wrap" in d or \
           "health route registers BEFORE the auth" in d, "the verified order is missing"


def t_proof_is_a_protocol_call():
    d = flat()
    assert "localhost protocol call, never a string in markdown" in d
    for probe in ("`GET /health` → 200", "unauthenticated `/mcp` → 401",
                  "`tools/list`", "`tools/call`"):
        assert probe in d, f"the acceptance list lost {probe!r}"


def t_snippets_consistent_with_the_named_import():
    # every python snippet constructing FastMCP must be the official-SDK shape
    blocks = re.findall(r"```python\n(.*?)```", raw(), re.S)
    ctors = [b for b in blocks if "FastMCP(" in b]
    assert ctors, "no FastMCP snippet found — the doc moved"
    for b in ctors:
        assert "from fastmcp import" not in b, "a snippet imports the standalone distribution"


def main():
    case("the two distributions are distinguished; imports named/refused",
         t_distributions_distinguished)
    case("the pin is the example's identity, dated", t_pin_is_the_identity)
    case("v1/standalone out of scope; lifecycle order verified",
         t_v1_out_of_scope_and_lifecycle_order)
    case("proof is a localhost protocol call with the 200/401/list/call set",
         t_proof_is_a_protocol_call)
    case("every FastMCP snippet matches the named distribution",
         t_snippets_consistent_with_the_named_import)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
