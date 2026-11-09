#!/usr/bin/env python3
"""AI-native products, packet P-AS (sshlg-skills plan 2026-11-09-ai-native).

agent-interop gains `references/agent-surface.md` (canon index AN-1..AN-10; AN-3, AN-7,
AN-8) and agent-evals gains `references/operability.md` (AN-9 mechanics). What this file
holds them to:

  * the canon index lists all ten rules once, each with a home;
  * every `file:line` the two references cite resolves, and the load-bearing ones still
    point at the text they cite (a citation that drifted is a rule restated wrongly);
  * agent-interop's description is no longer than before the change (283 characters,
    the plan's budget) and hands tool shape to agent-harness, with no second owner left
    in the body (the `:6-7` vs `:142-144` contradiction, BN-21);
  * the outcome cases written before the prose exist, pin their prompts, and check
    artifacts;
  * no em dash in the new prose.

Stdlib only.
"""
import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILLS = os.path.join(ROOT, "plugins", "agent-stack", "skills")
SURFACE = os.path.join(SKILLS, "agent-interop", "references", "agent-surface.md")
OPERABILITY = os.path.join(SKILLS, "agent-evals", "references", "operability.md")
INTEROP_SKILL = os.path.join(SKILLS, "agent-interop", "SKILL.md")
DESC_BEFORE = 283          # agent-interop's description at v0.31.4, whitespace collapsed
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


def t_canon_index_lists_ten_rules_once():
    text = read(SURFACE)
    rows = re.findall(r"^\| (AN-\d+) \|", text, re.M)
    assert rows == [f"AN-{n}" for n in range(1, 11)], f"canon index rows are {rows}"
    assert "https://raw.githubusercontent.com/ssheleg/<repo>/main/" in text, "no raw base"
    for profile in ("`public`", "`internal`", "`library`"):
        assert f"| {profile} |" in text, f"profile {profile} has no row"


def t_surface_carries_its_rules():
    text = read(SURFACE)
    for needle in ("human_steps", "input_required", "io.modelcontextprotocol/tasks",
                   "Client ID Metadata Documents", "`iss`", "confirm: true",
                   "internal: <reason>", "--help --json", "not-enabled", "sunset",
                   "Idempotency key on every write", "pseudonymised"):
        assert needle in text, f"agent-surface.md lost {needle!r}"


CITE = re.compile(r"`([A-Za-z0-9_./-]+\.md):(\d+)(?:-(\d+))?`")


def resolve(ref, cited_from):
    """`skill/references/x.md` is from the skills root; a bare name is a sibling reference,
    else the one reference of that name in the pack (the file's header names its home)."""
    if "/" in ref:
        return os.path.join(SKILLS, ref)
    sibling = os.path.join(os.path.dirname(cited_from), ref)
    if os.path.isfile(sibling):
        return sibling
    found = [os.path.join(SKILLS, s, "references", ref) for s in sorted(os.listdir(SKILLS))
             if os.path.isfile(os.path.join(SKILLS, s, "references", ref))]
    assert len(found) == 1, f"bare {ref!r} resolves to {len(found)} references, not one"
    return found[0]


def t_citations_resolve():
    for src in (SURFACE, OPERABILITY):
        for m in CITE.finditer(read(src)):
            path = resolve(m.group(1), src)
            assert os.path.isfile(path), f"{os.path.basename(src)} cites missing {m.group(0)}"
            n = len(read(path).splitlines())
            end = int(m.group(3) or m.group(2))
            assert end <= n, f"{m.group(0)} runs past {m.group(1)}'s {n} lines"


ANCHORS = (
    # (file under skills/, first line, last line, text that must sit inside the range)
    ("agent-interop/references/gateway.md", 191, 191, "effect ceiling"),
    ("agent-interop/references/gateway.md", 131, 159, "| T2 |"),
    ("agent-interop/references/gateway.md", 240, 249, "digest"),
    ("agent-interop/references/gateway.md", 251, 255, "approval-required"),
    ("agent-interop/references/gateway.md", 231, 238, "naming the"),
    ("agent-interop/references/mcp.md", 155, 155, "Dynamic Client Registration"),
    ("agent-interop/references/mcp.md", 136, 141, "retries the original request"),
    ("agent-interop/references/mcp.md", 131, 134, "payment"),
    ("agent-interop/references/mcp.md", 108, 110, "isError"),
    ("agent-interop/references/mcp.md", 166, 191, "subscriptions/listen"),
    ("agent-interop/references/mcp.md", 216, 249, "Tasks"),
    ("agent-harness/references/tools.md", 127, 133, "confirm: true"),
    ("agent-harness/references/tools.md", 135, 153, "readOnlyHint"),
    ("agent-harness/references/tools.md", 155, 178, "lethal trifecta"),
    ("agent-orchestrator/references/governance.md", 115, 131, "The audit row"),
)


def t_load_bearing_citations_point_at_their_text():
    surface = read(SURFACE)
    for rel, a, b, needle in ANCHORS:
        cited = f"{os.path.basename(rel)}:{a}" + (f"-{b}" if b != a else "")
        assert cited in surface, f"agent-surface.md no longer cites {cited}; update ANCHORS"
        lines = read(os.path.join(SKILLS, rel)).splitlines()[a - 1:b]
        assert needle in "\n".join(lines), \
            f"{rel}:{a}-{b} no longer holds {needle!r}; the citation drifted"


def description(path):
    fm = read(path).split("---", 2)[1]
    m = re.search(r"description: >-\n((?:  .*\n)+)", fm)
    return " ".join(m.group(1).split())


def t_interop_description_and_ownership():
    d = description(INTEROP_SKILL)
    assert len(d) <= DESC_BEFORE, f"description is {len(d)} chars, past its {DESC_BEFORE} budget"
    assert "agent surface" in d, "the description does not name a product's agent surface"
    assert "Not for tool shape (agent-harness)" in d, "tool shape is not handed to agent-harness"
    body = read(INTEROP_SKILL)
    assert "mcp-server-dev` plugin is built for\nit" not in body and \
        "designing the tool set of one server" not in body, \
        "the body still names a second owner of one server's tool design"
    assert "agent-harness/references/tools.md" in body, "the body does not name the tool-shape home"
    for t in ("agent surface", "агентная поверхность", "AI-native", "API для агентов"):
        assert f'"{t}"' in body, f"## Triggers lost {t!r}"


def t_cases_written_before_the_prose():
    want = {
        "agent-interop": ("AI-OUT-006-product-billing-agent-surface",
                          "AI-OUT-007-gated-refund-human-steps",
                          "AI-OUT-008-cli-made-agent-ready"),
        "agent-evals": ("AE-OUT-006-operability-proving-call-and-pass-k",),
    }
    for skill, ids in want.items():
        cases = {c["id"]: c for c in
                 json.loads(read(os.path.join(ROOT, "evals", "cases", f"{skill}.json")))["cases"]}
        for cid in ids:
            assert cid in cases, f"{skill}: case {cid} is missing"
            c = cases[cid]
            assert c["skill"] == skill and c["schema_version"] == "outcome-case/1"
            assert c["environment"]["case_digest"] == \
                hashlib.sha256(c["prompt"]["text"].encode()).hexdigest(), f"{cid}: digest drifted"
            contains = [o for o in c["checks"]["outcome"] if o["kind"] == "artifact-contains"]
            assert len(contains) >= 3, f"{cid}: fewer than three artifact checks"
            for o in contains:
                assert o["expect"] not in c["prompt"]["text"], \
                    f"{cid}: the expected {o['expect']!r} is in the prompt, an answer key"


def t_no_em_dash_in_new_prose():
    for path in (SURFACE, OPERABILITY):
        for n, line in enumerate(read(path).splitlines(), 1):
            assert EM_DASH not in line, f"{os.path.basename(path)}:{n} carries an em dash"


def main():
    case("the canon index lists AN-1..AN-10 once, with the three profiles",
         t_canon_index_lists_ten_rules_once)
    case("agent-surface.md carries the gate, credential, CLI and deprecation rules",
         t_surface_carries_its_rules)
    case("every file:line in the two references resolves", t_citations_resolve)
    case("the load-bearing citations still point at their text",
         t_load_bearing_citations_point_at_their_text)
    case("agent-interop: description within budget, tool shape owned once",
         t_interop_description_and_ownership)
    case("the outcome cases pin their prompts and check artifacts",
         t_cases_written_before_the_prose)
    case("no em dash in the new references", t_no_em_dash_in_new_prose)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
