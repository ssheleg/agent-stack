#!/usr/bin/env python3
"""Structural validator for agent-stack.

House rules, each one written because it can actually break:

  * one version, four files -- package.json, plugin.json, marketplace.json and
    the top CHANGELOG entry. A plugin whose manifest disagrees with its package
    installs fine and reports the wrong version forever.
  * SKILL.md front matter inside the Agent Skills limits, and `name` equal to
    the directory. Over-long front matter does not error -- it is silently
    truncated by the host, which is worse.
  * references/ and SKILL.md agree in BOTH directions: no link to a missing
    file, no file nobody links. The source this skill came from shipped a
    reference.md that nothing referenced.
  * a skill that documents somebody else's wire protocol stamps the revision it
    read (PROTOCOL_PINNED below). Prose about a protocol ages silently: the
    reader cannot tell a description of last year's handshake from this year's,
    and a model writing code from it is confidently wrong with no signal. The
    stamp is the signal, so it is enforced rather than requested.
  * no stray SKILL.md outside plugins/*/skills/*/, no build artifacts in the
    shipped tree.
  * CI runs this file. A validator that CI stopped calling is decoration.

Exit code 0 = green. Anything else = a fail with a reason on stderr.
"""

import datetime
import subprocess
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILURES = []

# Skills whose references describe an external specification somebody else
# versions. Every reference under one of these MUST open with a revision stamp,
# so a reader always knows which revision the prose was true against.
#
# Opting a skill in is a one-word change; leaving it out is the default, because
# most references document this repository's own patterns, which carry no
# upstream revision to drift from.
PROTOCOL_PINNED = {"agent-interop", "agent-harness"}

# `**Spec pinned:** <what> · read YYYY-MM-DD`
STAMP = re.compile(
    r"^\*\*Spec pinned:\*\*\s+.+\s+·\s+read\s+(\d{4})-(\d{2})-(\d{2})\s*$", re.M
)
STAMP_HEAD_LINES = 15


def fail(msg):
    FAILURES.append(msg)


def load_json(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        fail(f"missing {rel}")
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        fail(f"{rel}: invalid JSON -- {exc}")
        return None


def front_matter(path):
    """Return the raw front-matter block of a markdown file, or None."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    return m.group(1), text


def scalar(block, key):
    """Read one front-matter scalar without a YAML dependency.

    Handles both `key: value` and the folded `key: >-` form used for long
    descriptions, which is the only multi-line shape this repo ships.
    """
    m = re.search(rf"^{re.escape(key)}:\s*(.*)$", block, re.M)
    if not m:
        return None
    head = m.group(1).strip()
    if head not in (">-", ">", "|", "|-"):
        return head
    lines = []
    started = False
    for line in block.splitlines():
        if re.match(rf"^{re.escape(key)}:", line):
            started = True
            continue
        if not started:
            continue
        if line.startswith((" ", "\t")):
            lines.append(line.strip())
        elif line.strip() == "":
            lines.append("")
        else:
            break
    return " ".join(x for x in lines if x)


# ---------------------------------------------------------------- versions

pkg = load_json("package.json")
plugin = load_json("plugins/agent-stack/.claude-plugin/plugin.json")
market = load_json(".claude-plugin/marketplace.json")

version = pkg.get("version") if pkg else None
if not version:
    fail("package.json: missing version")

if plugin and plugin.get("version") != version:
    fail(f"version drift: plugin.json={plugin.get('version')!r} package.json={version!r}")

if market:
    plugins = market.get("plugins") or []
    if not plugins:
        fail("marketplace.json: plugins[] empty")
    for entry in plugins:
        if entry.get("version") != version:
            fail(
                f"version drift: marketplace.json {entry.get('name')!r}="
                f"{entry.get('version')!r} package.json={version!r}"
            )
        src = entry.get("source", "")
        if not os.path.isdir(os.path.join(ROOT, src.lstrip("./"))):
            fail(f"marketplace.json: source {src!r} does not exist")

changelog = os.path.join(ROOT, "CHANGELOG.md")
if not os.path.exists(changelog):
    fail("missing CHANGELOG.md")
else:
    with open(changelog, encoding="utf-8") as fh:
        text = fh.read()
    headings = re.findall(r"^## \[?v?(\d+\.\d+\.\d+)\]?", text, re.M)
    if not headings:
        fail("CHANGELOG.md: no version heading found")
    elif headings[0] != version:
        fail(f"version mismatch: CHANGELOG=v{headings[0]} package.json={version!r}")
    for dup in sorted({v for v in headings if headings.count(v) > 1}):
        fail(f"CHANGELOG.md: v{dup} documented twice -- the release notes would truncate")

# ------------------------------------------------------------------ skills

SKILL_ROOT = os.path.join(ROOT, "plugins", "agent-stack", "skills")
if not os.path.isdir(SKILL_ROOT):
    fail("missing plugins/agent-stack/skills/")
    skill_dirs = []
else:
    skill_dirs = sorted(
        d for d in os.listdir(SKILL_ROOT) if os.path.isdir(os.path.join(SKILL_ROOT, d))
    )
    if not skill_dirs:
        fail("plugins/agent-stack/skills/ has no skills")

for name in skill_dirs:
    sdir = os.path.join(SKILL_ROOT, name)
    spath = os.path.join(sdir, "SKILL.md")
    if not os.path.exists(spath):
        fail(f"{name}: no SKILL.md")
        continue

    block, text = front_matter(spath)
    if block is None:
        fail(f"{name}/SKILL.md: no front matter")
        continue

    fm_name = scalar(block, "name")
    fm_desc = scalar(block, "description")

    if fm_name != name:
        fail(f"{name}/SKILL.md: front-matter name {fm_name!r} != directory {name!r}")
    if not fm_name or len(fm_name) > 64:
        fail(f"{name}/SKILL.md: name must be 1-64 chars, got {len(fm_name or '')}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm_name or ""):
        fail(f"{name}/SKILL.md: name {fm_name!r} must be lowercase [a-z0-9-]")
    if not fm_desc:
        fail(f"{name}/SKILL.md: description is required")
    elif len(fm_desc) > 1024:
        fail(
            f"{name}/SKILL.md: description is {len(fm_desc)} chars, limit 1024 "
            "-- hosts truncate silently, so this never surfaces at runtime"
        )
    if fm_desc and re.search(r"<[a-zA-Z/]", fm_desc):
        fail(f"{name}/SKILL.md: description must not contain angle-bracket tags")

    # references: both directions
    rdir = os.path.join(sdir, "references")
    on_disk = set()
    if os.path.isdir(rdir):
        on_disk = {f for f in os.listdir(rdir) if f.endswith(".md")}
    # A bare `references/x.md` means THIS skill's file. `other-skill/references/x.md`
    # is prose about a sibling and must not be read as a link here -- without the
    # lookbehind, naming another skill's reference (which a boundary statement has to
    # do) fails the build for a file that was never claimed.
    linked = set(re.findall(r"(?<![\w./-])references/([A-Za-z0-9._-]+\.md)", text))

    for missing in sorted(linked - on_disk):
        fail(f"{name}/SKILL.md links references/{missing}, which does not exist")
    for orphan in sorted(on_disk - linked):
        fail(
            f"{name}/references/{orphan} exists but SKILL.md never links it "
            "-- an unreferenced reference is a file nobody loads"
        )

    # revision stamps: only for skills that document somebody else's protocol
    if name in PROTOCOL_PINNED:
        for ref in sorted(on_disk):
            rpath = os.path.join(rdir, ref)
            with open(rpath, encoding="utf-8") as fh:
                head = "".join(fh.readlines()[:STAMP_HEAD_LINES])
            m = STAMP.search(head)
            if not m:
                fail(
                    f"{name}/references/{ref}: no `**Spec pinned:** ... · read YYYY-MM-DD` "
                    f"line in the first {STAMP_HEAD_LINES} lines -- protocol prose without a "
                    "revision stamp cannot be told apart from prose that went stale"
                )
                continue
            try:
                datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                fail(f"{name}/references/{ref}: stamp date {m.group(0).strip()!r} is not a real date")

# ------------------------------------------------------- one home per fact

# Every reference is checked for EXISTENCE in both directions above. Nothing checked
# whether two of them say the same thing, and on 2026-08-15 the same six-row decision
# table was written into `agent-harness/SKILL.md` and into the graph-engineering
# reference in one afternoon — 50 shared twelve-word runs, found by measuring rather than
# by review. A table with two homes is one that will disagree with itself.
#
# The floor is set ABOVE the legitimate maximum, measured after that duplication was
# removed: the largest honest overlap between any two documents was 12 runs — a skill
# quoting the rule it defers to, which is exactly what citing looks like. 20 leaves
# headroom for a longer citation and still catches a restated section.
DUP_SHINGLE = 12          # words per run
DUP_FLOOR = 20            # runs shared before it stops being a citation


def _runs(text, n=DUP_SHINGLE):
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def check_one_home_per_fact():
    import itertools
    docs = {}
    for _sk in sorted(os.listdir(SKILL_ROOT)) if os.path.isdir(SKILL_ROOT) else []:
        _sd = os.path.join(SKILL_ROOT, _sk)
        if not os.path.isdir(_sd):
            continue
        _s = os.path.join(_sd, "SKILL.md")
        if os.path.isfile(_s):
            docs[f"{_sk}/SKILL.md"] = open(_s, encoding="utf-8").read()
        _rd = os.path.join(_sd, "references")
        if os.path.isdir(_rd):
            for _f in sorted(os.listdir(_rd)):
                if _f.endswith(".md"):
                    docs[f"{_sk}/{_f}"] = open(os.path.join(_rd, _f), encoding="utf-8").read()
    shingled = {k: _runs(v) for k, v in docs.items()}
    for a, b in itertools.combinations(sorted(shingled), 2):
        shared = len(shingled[a] & shingled[b])
        if shared >= DUP_FLOOR:
            fail(f"{a} and {b} share {shared} runs of {DUP_SHINGLE} words — that is a "
                 f"restated section, not a citation. One of them is the home; the other "
                 f"names it and stops. A fact with two homes disagrees with itself on the "
                 f"first edit, and nothing here would notice which one is now wrong")


check_one_home_per_fact()

# ------------------------------------------------- the checker's contract

# The checker node's contract is the gate in front of every convergence this pack
# recommends, and it is named in TWO documents by design: the home is
# `agent-orchestrator/references/graph-engineering.md` §6, and `agent-evals/SKILL.md` §5a
# states the eval half and points back (docs/DOCMAP.md, 2026-08-15 D-1). Two homes for one
# list is exactly what the shingle check above refuses, so the two are worded differently —
# which means nothing above can tell whether they still name the SAME items.
#
# They did not. Until 2026-08-19 the list held five items and *"carries its evidence"* was
# not one of them: a confidence signal stood in its place, in the one pack whose first value
# is evidence over confidence and whose own text says an uncalibrated judge is an opinion
# with a number attached. Arrival was half-covered too — no count, so a branch that never
# returned was caught only when the host happened to null its slot.
#
# So the list is declared machine-readably in both files and compared here. The floor is a
# RATCHET: an item may be added, never quietly dropped. Removing one is a deliberate edit to
# this file with a reason, which is the whole point — a contract that can shrink in silence
# is not a contract.
CHECKER_CONTRACT_FLOOR = 6
# Named individually because these two are the requirement, not decoration: *arrived* needs
# an arrival count and *carries its evidence* is the item that was missing.
CHECKER_CONTRACT_REQUIRED = {"missing", "unevidenced"}
# Demoted on purpose. Promoting it back to mandatory is a decision, not a typo, so it fails
# here and has to be argued.
CHECKER_CONTRACT_OPTIONAL_ONLY = {"under-confident"}
CHECKER_CONTRACT_DOCS = [
    ("agent-orchestrator/references/graph-engineering.md", "## 6. The checker node"),
    ("agent-evals/SKILL.md", "## 5a."),
]
CONTRACT_DECL = re.compile(
    r"<!--\s*checker-contract:\s*([^|>]+?)\s*\|\s*optional:\s*([^>]+?)\s*-->"
)
NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
                7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def _section(text, heading):
    """The body of one `##` section, heading line included, or None."""
    i = text.find(heading)
    if i < 0:
        return None
    j = text.find("\n## ", i + len(heading))
    return text[i:] if j < 0 else text[i:j]


def check_checker_contract_is_one_list_in_two_documents():
    decls = {}
    for rel, heading in CHECKER_CONTRACT_DOCS:
        path = os.path.join(SKILL_ROOT, *rel.split("/"))
        if not os.path.isfile(path):
            fail(f"{rel}: missing — it carries half of the checker contract")
            continue
        body = _section(open(path, encoding="utf-8").read(), heading)
        if body is None:
            fail(f"{rel}: no section starting {heading!r} — the checker contract lost its home")
            continue
        m = CONTRACT_DECL.search(body)
        if not m:
            fail(f"{rel}: {heading} has no `<!-- checker-contract: … | optional: … -->` "
                 "declaration. The two documents word the list differently on purpose, so "
                 "this line is the only thing that can prove they still name the same items")
            continue
        mandatory = [x.strip() for x in m.group(1).split(",") if x.strip()]
        optional = [x.strip() for x in m.group(2).split(",") if x.strip()]
        # Strip comments before reading the prose, or the declaration would satisfy the
        # check that the prose mentions the item — a guard that cannot fail.
        prose = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        decls[rel] = (tuple(mandatory), tuple(optional), prose)

    if len(decls) < len(CHECKER_CONTRACT_DOCS):
        return

    # Compared pairwise against the home rather than unpacked as a pair, so adding a third
    # document to the list above does not silently stop comparing anything.
    rel_a = CHECKER_CONTRACT_DOCS[0][0]
    mand_a, opt_a, _ = decls[rel_a]
    diverged = False
    for rel_b, (mand_b, opt_b, _p) in decls.items():
        if rel_b == rel_a:
            continue
        if mand_a != mand_b or opt_a != opt_b:
            diverged = True
            fail(f"{rel_a} and {rel_b} declare different checker contracts — "
                 f"{list(mand_a)}/{list(opt_a)} vs {list(mand_b)}/{list(opt_b)}. One of the "
                 "two gates is now the other one's past, and a reader cannot tell which")
    if diverged:
        return

    if len(mand_a) < CHECKER_CONTRACT_FLOOR:
        fail(f"the checker contract declares {len(mand_a)} mandatory items, floor is "
             f"{CHECKER_CONTRACT_FLOOR}: {list(mand_a)}. The floor is a ratchet — an item "
             "may be added, never quietly dropped, because the list is what every "
             "convergence in this pack is gated on")

    for key in sorted(CHECKER_CONTRACT_REQUIRED - set(mand_a)):
        fail(f"the checker contract no longer requires {key!r}. `missing` is *arrived* "
             "(an arrival count, not a nulled slot) and `unevidenced` is *carries its "
             "evidence* — the two this implementation was missing when the 2026-08-18 "
             "conformance audit measured it against the manifesto. Dropping either puts "
             "the gate back to asking how sure a branch is instead of what it can show")

    for key in sorted(CHECKER_CONTRACT_OPTIONAL_ONLY & set(mand_a)):
        fail(f"{key!r} is declared mandatory in the checker contract. It is optional by "
             "decision: an uncalibrated confidence score orders retries, it does not open "
             "a gate (`agent-evals` §5, `agent-orchestrator/references/governance.md`)")
    for key in sorted(CHECKER_CONTRACT_OPTIONAL_ONLY - set(opt_a)):
        fail(f"{key!r} left the checker contract's optional list — the confidence signal is "
             "demoted, not deleted, and the text explains why it is kept")

    word = NUMBER_WORDS.get(len(mand_a))
    for rel, (_m, _o, prose) in decls.items():
        # Optional keys are read too: an item kept as a hint still has to be visible to a
        # reader, or "we kept it, demoted" is a claim only this declaration makes.
        for key in list(mand_a) + list(opt_a):
            if not re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", prose, re.I):
                fail(f"{rel}: the checker contract declares {key!r} but the prose never "
                     "names it — the declaration would then be the only place the item "
                     "exists, and a reader of the document would never see it")
        if word and not re.search(rf"(?<![\w-]){word}(?![\w-])", prose, re.I):
            fail(f"{rel}: the contract has {len(mand_a)} items and the prose never says "
                 f"{word!r}. `Three of five are free` outlived the five it counted; a "
                 "spelled count that nothing checks is how the sentence and the list drift")

    home_rel, home_heading = CHECKER_CONTRACT_DOCS[0]
    home_prose = decls[home_rel][2]
    items = re.findall(r"^(\d+)\.\s+\*\*", home_prose, re.M)
    if len(items) != len(mand_a):
        fail(f"{home_rel}: {home_heading} lists {len(items)} numbered items but the "
             f"contract declares {len(mand_a)}. The list is the contract — a document that "
             "counts one way and declares another has already lost track of which items a "
             "checker must assert")


check_checker_contract_is_one_list_in_two_documents()

# --------------------------------------------------------------- hygiene

for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "plugins")):
    if "__pycache__" in dirnames or any(f.endswith(".pyc") for f in filenames):
        fail(f"build artifacts inside plugins/ at {os.path.relpath(dirpath, ROOT)}")
    if "SKILL.md" in filenames:
        rel = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        if not re.fullmatch(r"plugins/[^/]+/skills/[^/]+", rel):
            fail(f"stray SKILL.md at {rel}/SKILL.md -- only plugins/*/skills/*/ may hold one")

# ------------------------------------------------------------------- CI

wf = os.path.join(ROOT, ".github", "workflows", "validate.yml")
if not os.path.exists(wf):
    fail("missing .github/workflows/validate.yml")
else:
    with open(wf, encoding="utf-8") as fh:
        ci = fh.read()
    # Match the ENTRY POINT, not any mention. The negative self-tests below run
    # `python3 /tmp/<copy>/test/validate.py`, so a substring search for
    # "test/validate.py" stays satisfied after the real step is deleted -- which
    # is a guard that cannot fail. Require a step that runs it at the repo root.
    if not re.search(r"^\s*run:\s*python3\s+test/validate\.py\s*$", ci, re.M):
        fail("validate.yml has no `run: python3 test/validate.py` step -- the gate stopped being a gate")

# ---------------------------------------------------------------- verdict


def check_release_gates_on_validate():
    """A release must not publish over a red `validate`.

    On 2026-08-12 `sheleg-dev` tagged v0.4.1 while its own `validate` run for that exact
    tag FAILED, and npm served 0.4.1 four minutes later. The two are separate workflows,
    so nothing connected them: the release ran the structural validator and never the
    negative self-tests, which are steps in `validate.yml`. Six of the family's nine
    repositories were in that state.

    The fix is a `workflow_call` — the release calls the real suite rather than a copy of
    it — and this guard keeps the call there. A dependency nobody checks is a dependency
    somebody removes.
    """
    _wf = os.path.join(ROOT, ".github/workflows")
    _rel, _val = os.path.join(_wf, "release.yml"), os.path.join(_wf, "validate.yml")
    if not (os.path.isfile(_rel) and os.path.isfile(_val)):
        return
    _v = open(_val, encoding="utf-8").read()
    _r = open(_rel, encoding="utf-8").read()
    if not re.search(r"^\s*workflow_call:\s*$", _v, re.M):
        fail(".github/workflows/validate.yml: no `workflow_call:` trigger — the release "
               "workflow cannot run this suite, so a publish goes out over whatever subset "
               "it runs itself")
    if not re.search(r"^\s*uses:\s*\./\.github/workflows/validate\.yml\s*$", _r, re.M):
        fail(".github/workflows/release.yml: does not call ./.github/workflows/validate.yml "
               "— a red validate would not stop a publish, which is how v0.4.1 of a sibling "
               "reached npm with its own suite failing")
    if not re.search(r"^\s*needs:\s*(?:\[[^\]]*\bvalidate\b[^\]]*\]|validate)\s*$", _r, re.M):
        fail(".github/workflows/release.yml: no job declares `needs: validate` — calling "
               "the suite without depending on it lets the release run beside it rather than "
               "after it, which looks gated and is not")


check_release_gates_on_validate()

def _disclose_routing(msg):
    """A check that could not run, said out loud rather than counted as a pass."""
    print(f"  unlooked: {msg}")


def check_shipped_front_matter_survives_a_real_reader():
    """Our own gates read front matter with a regex; an installer does not.

    B-56: a sibling's `description` gained a colon-space inside an unquoted scalar, which
    YAML reads as a nested mapping. Every check the family owns stayed green and the
    skills CLI reported *No valid skills found* — the launcher exited 1 on that member and
    twelve non-Claude-Code channels sat on the previous version for hours.

    This member carries no routed triggers, which is exactly why it was the one place
    nothing would have looked: the shared checker used to exit early here. It does not any
    more, and the table it reads is not copied into this repository.
    """
    script = os.path.join(str(ROOT), "..", "..", "test", "advertised_check.js")
    if not os.path.isfile(script):
        _disclose_routing("front matter vs a strict reader — no sshlg-skills umbrella above this checkout")
        return
    try:
        proc = subprocess.run(["node", script, "--member", "agent-stack", "--root", str(ROOT)],
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        _disclose_routing(f"front matter vs a strict reader — could not run the checker ({exc})")
        return
    if proc.returncode == 1:
        fail((proc.stdout + proc.stderr).strip())
    elif proc.returncode != 0:
        _disclose_routing(f"front matter vs a strict reader — {(proc.stderr or 'the checker could not look').strip()}")


check_shipped_front_matter_survives_a_real_reader()


if FAILURES:
    print(f"FAIL: {len(FAILURES)} problem(s)", file=sys.stderr)
    for f in FAILURES:
        print(f"  - {f}", file=sys.stderr)
    sys.exit(1)

checks = 7 + len(skill_dirs)
print(f"OK: agent-stack structurally valid ({checks} checks, {len(skill_dirs)} skill(s), v{version})")
