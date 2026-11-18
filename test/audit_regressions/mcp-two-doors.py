#!/usr/bin/env python3
"""The two-door rule for MCP servers we build (operator, 2026-11-18).

`agent-interop/references/mcp-two-doors.md` owns the rule: `tools/list` of a server the
estate builds or runs answers `search` and `execute`, at most three measured exceptions,
old tool names alias for one release. What this file holds the pack to:

  * the reference exists, carries its load line and pin, and states the contract parts
    (the two tool names, the catalogue fields, the typed refusals, the exception cap, the
    migration release, the snapshot, the conformance list);
  * agent-interop's body states the rule and indexes the reference; agent-harness's tool
    advice and the agent-surface snapshot row point at it, so no other file teaches a
    many-tool server as the default;
  * no em dash in the new prose.

Stdlib only.
"""
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILLS = os.path.join(ROOT, "plugins", "agent-stack", "skills")
DOORS = os.path.join(SKILLS, "agent-interop", "references", "mcp-two-doors.md")
INTEROP = os.path.join(SKILLS, "agent-interop", "SKILL.md")
SURFACE = os.path.join(SKILLS, "agent-interop", "references", "agent-surface.md")
MCP = os.path.join(SKILLS, "agent-interop", "references", "mcp.md")
TOOLS = os.path.join(SKILLS, "agent-harness", "references", "tools.md")
EM_DASH = chr(0x2014)

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def t_reference_states_the_contract():
    text = read(DOORS)
    assert text.startswith("# Two doors"), "title"
    assert "**Load this when:**" in text, "no load line"
    assert re.search(r"^\*\*Spec pinned:\*\*.+· read \d{4}-\d{2}-\d{2}\s*$", text, re.M), "no pin"
    for part in ("`search`", "`execute`", '"inputSchema"', '"gate"', '"effect"', '"example"',
                 "`unknown-operation`", "`invalid-arguments`", "`idempotency-required`",
                 "at most three", "One release of aliases", "## The contract snapshot",
                 "## Conformance tests", "fabric.job.get"):
        assert part in text, f"missing {part}"


def t_interop_states_and_indexes_the_rule():
    text = read(INTEROP)
    assert "## Rule one: every MCP server we build has two doors" in text, "no rule one"
    assert "[`references/mcp-two-doors.md`](references/mcp-two-doors.md)" in text, "not indexed"
    assert "| What tools does my server list? |" in text, "no dispatch row"


def t_neighbours_point_at_the_rule():
    assert "mcp-two-doors.md" in read(TOOLS), "agent-harness tools.md does not point at it"
    assert "mcp-two-doors.md" in read(MCP), "mcp.md does not point at it"
    surface = read(SURFACE)
    assert "the whole `search` catalogue" in surface, "snapshot row lacks the catalogue"
    assert "owes a tool." not in surface, "AN-3 still says a capability owes a tool"


def t_no_em_dash_in_new_prose():
    assert EM_DASH not in read(DOORS), "em dash in mcp-two-doors.md"
    block = read(INTEROP).split("## Rule one:", 1)[1].split("\n---\n", 1)[0]
    assert EM_DASH not in block, "em dash in rule one"


case("reference states the contract", t_reference_states_the_contract)
case("agent-interop states and indexes the rule", t_interop_states_and_indexes_the_rule)
case("neighbours point at the rule", t_neighbours_point_at_the_rule)
case("no em dash in the new prose", t_no_em_dash_in_new_prose)

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nmcp-two-doors: all cases pass")
