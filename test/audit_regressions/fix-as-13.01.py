#!/usr/bin/env python3
"""FIX-AS-13.01 — "long-running" no longer routes to A2A by itself (sherlock
audit, AS-13).

The finding: the interop skill's "tell" said that inventing a task lifecycle,
a progress channel and a resumable handle on top of tools/call means "you
wanted A2A" — while the same skill's mcp.md correctly documents MCP Tasks as
exactly that durable handle. Duration was deciding the protocol.

The fix under test (agent-interop SKILL.md + references/mcp.md):
* the PRIMARY dispatch criterion is capability/tool execution (MCP) vs
  autonomous peer outcome (A2A); duration is a SECOND question about the
  Tasks capability, not a protocol choice;
* the routing set: long-running fixed export → MCP Tasks when negotiated;
  autonomous outsourced negotiation → A2A; Tasks unsupported → an explicit
  fallback, not A2A;
* actually-negotiated client/SDK extensions are checked before building;
* no case in the routing set is decided by the word "long-running" alone.

Standard library only.
"""
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-interop", "SKILL.md")
MCP = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-interop",
                   "references", "mcp.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def flat(path):
    with open(path, encoding="utf-8") as fh:
        return " ".join(fh.read().split())


def t_primary_criterion_is_what_not_how_long():
    d = flat(SKILL)
    assert "The dispatch criterion is WHAT the other side is, not how long it runs." in d
    assert "Duration is a SECOND question, and it is about a Tasks CAPABILITY, not a protocol." in d


def t_old_tell_is_gone():
    d = flat(SKILL)
    assert "a resumable handle on top of `tools/call`, you wanted A2A" not in d, \
        "the old tell still routes a task lifecycle to A2A"


def t_routing_set_covers_all_three():
    d = flat(SKILL)
    assert "long-running FIXED export → **MCP Tasks, when the client/SDK negotiates that extension**" in d
    assert "autonomous outsourced negotiation → **A2A**" in d
    assert "**Tasks unsupported** by the reached client/SDK → an explicit fallback" in d
    assert "reaching for A2A because Tasks is absent is picking a protocol to dodge a missing extension" in d


def t_no_case_decided_by_the_word_alone():
    d = flat(SKILL)
    assert "never by the word *long-running*" in d
    assert "Check the client's ACTUALLY-negotiated extensions" in d


def t_mcp_md_agrees():
    d = flat(MCP)
    assert "Duration is a TASKS-capability question, never a reason to switch to A2A" in d
    assert "OPT-IN, NEGOTIATED extension" in d
    assert "not a protocol change" in d


def main():
    case("the primary criterion is WHAT, duration is a second question",
         t_primary_criterion_is_what_not_how_long)
    case("the old lifecycle→A2A tell is gone", t_old_tell_is_gone)
    case("the routing set covers Tasks / A2A / unsupported-fallback",
         t_routing_set_covers_all_three)
    case("no case is decided by the word long-running; negotiated support is checked",
         t_no_case_decided_by_the_word_alone)
    case("mcp.md carries the same rule at the Tasks bullet", t_mcp_md_agrees)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
