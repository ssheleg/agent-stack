#!/usr/bin/env python3
"""Mechanical half of an agent-system audit.

Finds only what is visible WITHOUT understanding intent, and prints what it cannot see —
because a scanner that goes quiet is reporting its own blindness, and an audit that stops
at a silent scanner has audited the scanner.

    python3 audit_agent.py <path>            human-readable
    python3 audit_agent.py <path> --json     machine-readable
    python3 audit_agent.py --self-test       plant each defect, require each to be found

Zero dependencies. Python 3.9+.

Design rule, and the reason this file is short: every detector is CONSERVATIVE. A false
positive costs more than a miss here, because an audit report that cries wolf is discarded
whole — and the seven tracks in `references/audit.md` cover by hand everything this cannot
reach. Detectors therefore require corroboration (the file must look agent-related) and
each finding carries `file:line` so a human can disagree with it in one click.
"""

import argparse
import json
import os
import re
import sys

# A file is "agent-related" only if it shows two independent signs. One is a coincidence:
# plenty of code says "message" or "prompt" without being an agent loop.
AGENTISH = [
    re.compile(r"\btool[_ ]?call", re.I),
    re.compile(r"\btools\s*=|\"tools\"\s*:|'tools'\s*:"),
    re.compile(r"\bsystem[_ ]?prompt", re.I),
    re.compile(r"\b(anthropic|openai|litellm|langchain|langgraph|bedrock|mistral)\b", re.I),
    re.compile(r"\bfunction[_ ]?call", re.I),
    re.compile(r"\bmessages\s*=\s*\[|\"messages\"\s*:"),
]
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
             ".next", "target", "vendor", ".tox", "site-packages"}
MAX_BYTES = 400_000          # a generated bundle is not worth reading, and skews everything

# Model ids that are usually hardcoded by accident. Deliberately not exhaustive: this is a
# smell detector, and the finding says "pin it deliberately", not "this id is wrong".
MODEL_LITERAL = re.compile(
    r"[\"']((?:claude|gpt|gemini|llama|mistral|deepseek|qwen)[-\w.]*\d[\w.-]*)[\"']", re.I)

FINDINGS = []


def add(kind, path, line, detail, fix):
    FINDINGS.append({"check": kind, "file": path, "line": line, "detail": detail, "fix": fix})


def agentish(text):
    return sum(1 for p in AGENTISH if p.search(text)) >= 2


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip a virtualenv by its MARKER, not by its name. `venv`/`.venv` in SKIP_DIRS
        # only catches the conventional names; a real repository met during testing used
        # `myenv/`, holding 4249 of its 4261 code files, and was excluded only because
        # `site-packages` happened to be listed too. Right by accident is not right.
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")
                       and not os.path.exists(os.path.join(dirpath, d, "pyvenv.cfg"))]
        for fn in filenames:
            if os.path.splitext(fn)[1] not in CODE_EXT:
                continue
            full = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(full) > MAX_BYTES:
                    continue
                with open(full, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            yield os.path.relpath(full, root), text


# ------------------------------------------------------------------ detectors

def check_unbounded_loop(rel, text, lines):
    """`while True` in an agent file with no visible iteration bound.

    Conservative twice over: the file must be agent-related, AND the file must not mention
    any bound at all. A loop with `max_iter` somewhere else in the file is left alone.
    """
    if re.search(r"max[_ ]?iter|max[_ ]?steps|max[_ ]?turns|iteration_limit|for\s+\w+\s+in\s+range\(",
                 text, re.I):
        return
    for i, l in enumerate(lines, 1):
        if re.search(r"^\s*while\s+(True|true|1)\s*[:)]|^\s*while\s*\(\s*true\s*\)", l):
            add("unbounded-loop", rel, i,
                "`while True` in an agent file with no iteration bound anywhere in it",
                "Add a max-iteration guard that composes a partial answer at the bound, "
                "rather than returning nothing")


def check_tool_without_description(rel, text, lines):
    """A tool declared with an empty or missing description.

    Only fires on an explicit empty string — a missing key is too easy to get wrong across
    frameworks, and a wrong finding here is worse than a missed one.
    """
    for i, l in enumerate(lines, 1):
        if re.search(r"[\"']description[\"']\s*:\s*[\"']\s*[\"']", l) or \
           re.search(r"\bdescription\s*=\s*[\"']\s*[\"']", l):
            add("tool-no-description", rel, i,
                "a tool description is the empty string",
                "Describe WHEN and WHY to use it, and name the neighbouring tool it is "
                "confused with — the highest-leverage sentence in a tool definition")


def check_swallowed_error(rel, text, lines):
    """An exception caught and discarded inside an agent file."""
    for i, l in enumerate(lines, 1):
        nxt = lines[i] if i < len(lines) else ""
        if re.search(r"^\s*except[^\n]*:\s*$", l) and re.search(r"^\s*pass\s*$", nxt):
            add("swallowed-error", rel, i,
                "`except: pass` — the failure is invisible to the loop and to the model",
                "Return an error the agent can act on; a tool error is a turn in the "
                "conversation, not a silence")
        if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", l):
            add("swallowed-error", rel, i,
                "empty `catch` block — the failure is discarded",
                "Surface it to the loop; an error that teaches the next attempt costs "
                "nothing extra")


def check_no_timeout(rel, text, lines):
    """An outbound HTTP call with no timeout, in an agent file."""
    for i, l in enumerate(lines, 1):
        if re.search(r"\brequests\.(get|post|put|patch|delete)\s*\(", l) and "timeout" not in l:
            add("no-timeout", rel, i,
                "`requests` call with no `timeout=` — a hung provider hangs the agent",
                "Set an explicit timeout on every external call, and decide what the loop "
                "does when it fires")
        if re.search(r"\burllib\.request\.urlopen\s*\(", l) and "timeout" not in l:
            add("no-timeout", rel, i, "`urlopen` with no `timeout=`",
                "Set an explicit timeout on every external call")


def check_hardcoded_model(rel, text, lines):
    """A model id as a literal, in more than one place — the smell is duplication."""
    hits = []
    for i, l in enumerate(lines, 1):
        if l.lstrip().startswith(("#", "//", "*")):
            continue
        m = MODEL_LITERAL.search(l)
        if m:
            hits.append((i, m.group(1)))
    if len(hits) >= 2:
        i, name = hits[0]
        add("hardcoded-model", rel, i,
            f"model id {name!r} appears as a literal {len(hits)}× in this file",
            "Resolve the model from configuration at one boundary; three levels — request, "
            "tenant, system default — is the shape that bills correctly")


def check_unguarded_fanout(rel, text, lines):
    """A fan-out whose siblings' failures are not captured.

    `asyncio.gather` without `return_exceptions=True` cancels the whole batch on the first
    exception: every other branch's completed work is discarded, and the node that consumes
    the results cannot tell a branch that FAILED from one that returned nothing. `Promise.all`
    has the identical shape. That is the failure a checker node between a parallel layer and
    its convergence exists to stop, and it is invisible in a green test run because the happy
    path never exercises it.

    Conservative twice over, like every detector here: the file must already look
    agent-related, and the capturing form must be absent from the WHOLE file — one
    `return_exceptions` or `allSettled` anywhere is taken as evidence the author knows the
    distinction, and this pass says nothing.
    """
    if re.search(r"return_exceptions|allSettled", text):
        return
    for i, l in enumerate(lines, 1):
        if re.search(r"\basyncio\.gather\s*\(", l):
            add("unguarded-fanout", rel, i,
                "`asyncio.gather` with no `return_exceptions=True` — the first sibling to "
                "raise cancels the batch and throws away what the others already produced",
                "Capture each branch's outcome, then gate the convergence on a checker that "
                "can tell a failed branch from an empty one")
        if re.search(r"\bPromise\.all\s*\(", l) and ".catch" not in l:
            add("unguarded-fanout", rel, i,
                "`Promise.all` with no `allSettled` and no per-branch `.catch` — one "
                "rejection discards every other branch's completed result",
                "Use `Promise.allSettled` or catch per branch, then gate the convergence on "
                "a checker that can see which branch failed")


def check_declared_deps_ignored(rel, text, lines):
    """A plan that declares dependencies and is then walked in list order.

    A model with a `depends_on` (or `dependsOn`, or `depends`) field has gone to the trouble
    of saying which steps need which — and then a loop over the collection in the order it
    happens to be stored serialises the whole thing anyway. The declaration is not wrong and
    the loop is not wrong; together they are a plan that says it need not be serialised,
    serialised. This pack shipped exactly that in its own reference until 2026-08-15.

    Conservative: the file must declare a dependency field AND iterate the collection that
    holds it, and it must contain no sign of a topological pass anywhere — `layers`, `kahn`,
    `toposort`, `in_degree` or a `ready`/`runnable` set. Any of those and this says nothing.
    """
    if re.search(r"\b(layers?|kahn|toposort|topological|in_degree|indegree|runnable|ready_set)\b",
                 text, re.I):
        return
    if not re.search(r"\bdepends?(_on|On)?\b\s*[:=]", text):
        return
    for i, l in enumerate(lines, 1):
        m = re.search(r"for\s+\w+\s+in\s+(\w+)\.(stages|steps|nodes|tasks|plan)\b", l) or \
            re.search(r"for\s+\w+\s+in\s+(plan|stages|steps|nodes|tasks)\b", l)
        if m:
            add("declared-deps-ignored", rel, i,
                "a dependency field is declared and the collection is walked in list order — "
                "the plan says it need not be serialised, and then is",
                "Execute in dependency layers (Kahn over the declared edges); a cycle fails "
                "the plan rather than deadlocking the run, and a layer of more than one gets "
                "a checker before anything downstream consumes it")
            return


CHECKS = [check_unbounded_loop, check_tool_without_description, check_swallowed_error,
          check_no_timeout, check_hardcoded_model, check_unguarded_fanout,
          check_declared_deps_ignored]

# What no static pass can reach. Printed every run, never suppressed.
BLIND = [
    "whether the SYSTEM PROMPT is at the right altitude — or whether it is in this repo at all",
    "whether two tool descriptions actually distinguish themselves to a model",
    "whether the workflow/agent choice was made deliberately or defaulted to an agent",
    "whether a fan-out has a CHECKER between it and the node that consumes it — this pass "
    "sees an unguarded gather, never a missing gate",
    "whether retries and fallbacks MULTIPLY (three providers x three retries is nine calls)",
    "whether compaction preserves decisions and open questions, or keeps the discussion",
    "whether tool output is treated as untrusted input",
    "whether evals exist, judge trajectories, and are calibrated",
    "whether an audit row could prove a control was applied (policy version)",
    "everything in a language this pass does not read, and everything in configuration",
]


def scan(root):
    seen_files = considered = 0
    for rel, text in walk(root):
        considered += 1
        if not agentish(text):
            continue
        seen_files += 1
        lines = text.splitlines()
        for c in CHECKS:
            c(rel, text, lines)
    return seen_files, considered


def report_text(root, seen, considered):
    # The denominator is not decoration. "read: 1" alone looks like a broken pass; "1 of
    # 4261" says the repository is mostly not an agent, which is a finding in itself when
    # somebody called it one.
    out = [f"agent-audit: {root}",
           f"  code files considered: {considered}",
           f"  of those, agent-related: {seen}"]
    if not seen:
        out.append("  NOTHING READ — no file showed two independent signs of an agent loop.")
        out.append("  That is a fact about this pass, not about the system. Check the path,")
        out.append("  and whether the agent lives in a language or a config this cannot read.")
    out.append("")
    if FINDINGS:
        out.append(f"FINDINGS ({len(FINDINGS)}) — each is a smell with a location, not a verdict:")
        for f in FINDINGS:
            out.append(f"  {f['file']}:{f['line']}  [{f['check']}]")
            out.append(f"      {f['detail']}")
            out.append(f"      fix: {f['fix']}")
    else:
        out.append("FINDINGS (0) — nothing mechanically visible.")
    out.append("")
    out.append("THIS PASS CANNOT SEE — the manual half of the audit, and it is the larger half:")
    for b in BLIND:
        out.append(f"  - {b}")
    out.append("")
    out.append("Walk the seven tracks in references/audit.md. Silence above is not a pass.")
    return "\n".join(out)


PY_HEADER = ("import requests\n"
             "system_prompt = 'x'\n"
             "tools = [{'name': 't', 'description': 'does a thing'}]\n"
             "messages = []\n")
JS_HEADER = ("const system_prompt = 'x';\n"
             "const tools = [{name: 't', description: 'does a thing'}];\n"
             "const messages = [];\n")

# (label, the check that MUST fire, filename, body)
PLANTS = [
    ("unbounded-loop", "unbounded-loop", "agent.py",
     PY_HEADER + "while True:\n    pass\n"),
    ("tool-no-description", "tool-no-description", "agent.py",
     PY_HEADER + "T = [{'name': 'a', 'description': ''}]\n"),
    ("swallowed-error", "swallowed-error", "agent.py",
     PY_HEADER + "try:\n    x = 1\nexcept Exception:\n    pass\n"),
    ("no-timeout", "no-timeout", "agent.py",
     PY_HEADER + "r = requests.get('https://example.com')\n"),
    ("hardcoded-model", "hardcoded-model", "agent.py",
     PY_HEADER + "a = 'claude-opus-4'\nb = 'claude-opus-4'\n"),
    ("unguarded-fanout (asyncio)", "unguarded-fanout", "agent.py",
     PY_HEADER + "out = await asyncio.gather(*(run(t) for t in tasks))\n"),
    ("unguarded-fanout (promise)", "unguarded-fanout", "agent.js",
     JS_HEADER + "const out = await Promise.all(tasks.map(t => run(t)));\n"),
    ("declared-deps-ignored", "declared-deps-ignored", "agent.py",
     PY_HEADER + "class Stage:\n    depends_on = []\n"
     "for stage in plan.stages:\n    run(stage)\n"),
]

# A detector that fires on the defect AND on its fix has no discriminating power. Each
# clean fixture is the half of the evidence that says which one this is.
CLEAN = [
    ("the ordinary correct file", "agent.py",
     PY_HEADER + "for _ in range(10):\n    pass\n"
     "r = requests.get('https://example.com', timeout=5)\n"),
    ("a fan-out that DOES capture its branches", "agent.py",
     PY_HEADER + "for _ in range(10):\n    pass\n"
     "out = await asyncio.gather(*(run(t) for t in tasks), return_exceptions=True)\n"),
    ("a plan that DOES execute in dependency layers", "agent.py",
     PY_HEADER + "class Stage:\n    depends_on = []\n"
     "for layer in plan.layers():\n    run_layer(layer)\n"
     "r = requests.get('https://example.com', timeout=5)\n"),
]


def self_test():
    """Plant each defect and require the matching check to fire.

    A detector nobody has watched fire is not evidence that it works, and every plant
    asserts it changed something so a reworded fixture fails HERE rather than reporting a
    healthy checker as broken.

    Two things the shape of this function is deliberate about. A detector that reads two
    languages gets a plant in **each** — one passing shape is not evidence about the
    other. And every run also asserts silence on the CORRECT shape of the same defect,
    which is what separates a detector from a keyword search.
    """
    import tempfile
    failures = 0
    for label, kind, fname, body in PLANTS:
        FINDINGS.clear()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, fname), "w", encoding="utf-8") as fh:
                fh.write(body)
            assert agentish(body), f"PLANT DID NOT LAND: fixture for {label} is not agent-related"
            scan(d)
        got = {f["check"] for f in FINDINGS}
        if kind in got:
            print(f"  OK   {label}: detected")
        else:
            print(f"  FAIL {label}: NOT detected (found {sorted(got) or 'nothing'})")
            failures += 1
    for label, fname, body in CLEAN:
        FINDINGS.clear()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, fname), "w", encoding="utf-8") as fh:
                fh.write(body)
            assert agentish(body), f"CLEAN FIXTURE NOT READ: {label} is not agent-related"
            scan(d)
        if FINDINGS:
            print(f"  FAIL {label}: produced {len(FINDINGS)} finding(s): "
                  f"{[f['check'] for f in FINDINGS]}")
            failures += 1
        else:
            print(f"  OK   {label}: silent")
    total = len(PLANTS) + len(CLEAN)
    print(f"\nself-test: {total - failures}/{total} passed")
    return 1 if failures else 0


def main(argv):
    ap = argparse.ArgumentParser(description="Mechanical half of an agent-system audit.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    root = os.path.abspath(a.path)
    if not os.path.isdir(root):
        print(f"error: {a.path} is not a directory", file=sys.stderr)
        return 2
    seen, considered = scan(root)
    if a.json:
        print(json.dumps({"root": root, "files_considered": considered,
                          "files_agent_related": seen, "findings": FINDINGS,
                          "cannot_see": BLIND}, indent=2))
    else:
        print(report_text(root, seen, considered))
    # Findings are smells, not failures: exit 0 so this composes in a pipeline, and let the
    # human decide. A non-zero exit here would turn an audit into a gate it was never
    # calibrated to be.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
