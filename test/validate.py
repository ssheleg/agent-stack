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
import glob
import subprocess
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    # Accounts for what this run leaves on disk and prints it at exit, `nothing` included
    # — see test/residue.py. Tolerant on purpose: a gate that refuses to start because a
    # helper is absent is worse than one that runs and discloses that it could not account
    # for itself. Nothing in THIS file writes to $TMPDIR today; the import is what makes
    # the next thing that does visible in this command's own output.
    import residue  # noqa: F401
except ImportError:
    print("  unlooked: residue — test/residue.py is absent, so this run cannot say what "
          "it left on disk")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 5% under the 1024 cap. Not this repo's number: `DESC_TARGET` in make-skill's
# `scripts/audit_skill.py`, the family's authority on skill budgets.
DESC_WORKING_LIMIT = 970
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

# The house body limits. 5000 is the platform budget; 4750 is the working limit
# that leaves room for one more correction, and the number `make-skill` enforces.
BODY_BUDGET_TOKENS = 5000
BODY_WORKING_TOKENS = 4750
notes = []

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

    # --- the body budget, which this gate has never measured ----------------
    # B-126: `agent-orchestrator` reached 4749 of the house's 4750-token working
    # limit with nobody watching. The limit is real doctrine — `make-skill` ships
    # it and its own gate enforces it — and this repository's gate did not, so a
    # file could sit one token from the edge and the next release would breach it
    # silently. HARD failure at the platform budget; the working limit REPORTS,
    # matching the house auditor's own semantics, because a warning that fails a
    # build is a warning nobody may act on gradually.
    # CI's *House skill audit* job runs `make-skill`'s auditor and is the AUTHORITY on
    # this number; the check here exists so the same drift shows up on `npm test` instead
    # of on a push. Two corrections its first draft needed, both recorded because each
    # was a wrong measurement rather than a strict one:
    #   * it counted the whole file, front matter included — 4757 against a real body of
    #     4494 chars//4 — so it flagged a file the auditor passes;
    #   * `len//4` over the body then read ~4494 where the auditor read 4609, which errs
    #     LOW and would warn late.
    # The divisor is calibrated on that measured pair (4609 tokens / 17,977 body chars
    # -> 3.9), so this tracks the authority closely and slightly high. Re-derive it if the
    # auditor's tokenizer changes; do not widen it to make a failing file pass.
    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    body_tokens = int(len(body) / 3.9)
    if body_tokens > BODY_BUDGET_TOKENS:
        fail(f"{name}/SKILL.md: body ~{body_tokens} tokens, past the {BODY_BUDGET_TOKENS} "
             "budget — the answer at this point is a split, not a trim")
    elif body_tokens > BODY_WORKING_TOKENS:
        notes.append(f"{name}/SKILL.md: body ~{body_tokens} tokens, past the "
                     f"{BODY_WORKING_TOKENS} working limit ({BODY_BUDGET_TOKENS} budget) — "
                     "displace before the next addition")

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
    elif len(fm_desc) > DESC_WORKING_LIMIT:
        # The house working limit, and it was checked nowhere here. Three of four skills sat
        # past it on 2026-08-20 — 1019, 986 and 983 chars — one with FIVE characters of
        # headroom before the hard cap, which is not room for the "and not for X" clause the
        # next near-miss neighbour requires. The family's own auditor
        # (`make-skill/scripts/audit_skill.py`, DESC_TARGET) is the authority for the number;
        # this is the gate that stops the drift returning silently.
        fail(
            f"{name}/SKILL.md: description is {len(fm_desc)} chars, past the "
            f"{DESC_WORKING_LIMIT}-char working limit (hard cap 1024). A description at 99% "
            "of cap cannot absorb the clause that says what this skill is NOT for, and that "
            "clause is what stops a sibling stealing its triggers"
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


def _pack_docs():
    """Every prose document this pack ships, keyed `<skill>/<file>`.

    One enumeration, because two of them drift: a check that sweeps "every document" is
    only as good as its idea of which documents exist.
    """
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
    return docs


def check_one_home_per_fact():
    import itertools
    shingled = {k: _runs(v) for k, v in _pack_docs().items()}
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

# ------------------------------------------------- the node contract's five fields
#
# Same mechanism as the checker contract above, deliberately: a machine-readable
# declaration beside the prose, a floor that ratchets, and named keys that cannot leave in
# silence. It is here because the same defect was found twice by the same audit. The
# manifesto states a useful node as *one input, one job, one output, one owner, and its own
# completion test* (`manifesto` → *"one input, one job, one output, one owner, and its own completion test"*); §1 of the graph reference shipped
# three of the five — "One input, one output, one job" — while giving the manifesto's own
# justification in nearly the manifesto's words, so nothing about the sentence read as
# abridged. `grep -i owner` and `grep -i 'completion test'` over the file both exited 1.
#
# ONE home, not two. The checker contract needed a mirror check because it is stated in two
# documents on purpose; this list is stated once, and `grep` confirms it (the only match for
# "one input" in `plugins/` is that line). So this check compares the declaration against
# its own prose rather than against a sibling, and no second home is created to police.
NODE_CONTRACT_FLOOR = 5
# Named individually because these two are the row: they are what the 2026-08-18 audit
# measured as absent, and the three that were present were never at risk.
NODE_CONTRACT_REQUIRED = {"owner", "check"}
NODE_CONTRACT_DOC = ("agent-orchestrator/references/graph-engineering.md",
                     "## 1. Node and edge")
NODE_DECL = re.compile(r"<!--\s*node-contract:\s*([^>]+?)\s*-->")
# The completion test's field name is `check` in `task-pipeline`'s graph schema. Requiring
# the backticked name AND the pack that defines it is the guard against the family holding
# two names for one field: doctrine can describe "its own completion test" forever, and a
# reader implementing it then picks a name nobody else uses.
NODE_CHECK_FIELD = "`check`"
NODE_CHECK_OWNER_PACK = "task-pipeline"


def check_node_contract_keeps_its_five_fields():
    rel, heading = NODE_CONTRACT_DOC
    path = os.path.join(SKILL_ROOT, *rel.split("/"))
    if not os.path.isfile(path):
        fail(f"{rel}: missing — it is the only home of the node contract")
        return
    body = _section(open(path, encoding="utf-8").read(), heading)
    if body is None:
        fail(f"{rel}: no section starting {heading!r} — the node contract lost its home")
        return
    m = NODE_DECL.search(body)
    if not m:
        fail(f"{rel}: {heading} has no `<!-- node-contract: … -->` declaration. The field "
             "list is prose everywhere else, and prose is what dropped two of the five "
             "fields for the whole life of this file without a single check noticing")
        return
    fields = [x.strip() for x in m.group(1).split(",") if x.strip()]
    # Comments stripped before reading the prose, or the declaration itself would satisfy
    # the requirement that the prose names each field — a guard that cannot fail.
    prose = re.sub(r"<!--.*?-->", "", body, flags=re.S)

    if len(fields) < NODE_CONTRACT_FLOOR:
        fail(f"the node contract declares {len(fields)} fields, floor is "
             f"{NODE_CONTRACT_FLOOR}: {fields}. The floor is a ratchet — a field may be "
             "added, never quietly dropped. This file shipped at three of five and read "
             "as complete, which is the whole reason the floor exists")

    for key in sorted(NODE_CONTRACT_REQUIRED - set(fields)):
        fail(f"the node contract no longer declares {key!r}. `owner` is *one owner* and "
             "`check` is *its own completion test* — the two the 2026-08-18 conformance "
             "audit measured as absent against the manifesto. Without `owner`, shared "
             "mutation is answered by worktree isolation, which removes the race and not "
             "the question of whose version wins; without `check`, no node states what "
             "closes it and the convergence re-derives it or nobody does")

    for key in fields:
        if not re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", prose, re.I):
            fail(f"{rel}: the node contract declares {key!r} but the prose never names it "
                 "— the declaration would then be the only place the field exists, and a "
                 "reader of the document would never see it")

    word = NUMBER_WORDS.get(len(fields))
    if word and not re.search(rf"(?<![\w-]){word}(?![\w-])", prose, re.I):
        fail(f"{rel}: the contract has {len(fields)} fields and the prose never says "
             f"{word!r}. The sentence that lost two fields still counted correctly for the "
             "three it kept; a spelled count nothing checks is how prose and list drift")

    # The field name, not just the concept. Both halves, because either alone lets the
    # family end up with two names for one field.
    if NODE_CHECK_FIELD not in prose:
        fail(f"{rel}: the node contract never names the field {NODE_CHECK_FIELD} in code "
             "formatting. 'Its own completion test' is the requirement; `check` is what it "
             "is called in this family, and doctrine that states only the first leaves the "
             "next implementer to invent a third name for it")
    if NODE_CHECK_OWNER_PACK not in prose:
        fail(f"{rel}: the node contract names {NODE_CHECK_FIELD} without saying that "
             f"{NODE_CHECK_OWNER_PACK} is where the field is defined. A shared field name "
             "with no stated owner is a coincidence the next edit is free to break")


check_node_contract_keeps_its_five_fields()

# ------------------------------------- the two eval tiers, named together
#
# Third use of the same mechanism, and the sharpest row the 2026-08-18 conformance audit
# found: not a thinner statement of a manifesto rule but the opposite imperative.
# `manifesto` → *"you cannot connect it to the evidence graph later without inventing the test"* treats *a requirement with no observable as unfinished,
# because you cannot connect it to the evidence graph later without inventing the test after
# seeing the implementation*, and *"The evidence graph says how the result will be known"* says an evidence graph built after the code "has
# already let the output decide what counts as success". `agent-evals/SKILL.md` answered
# **"Never author the suite up front."**
#
# Both rules are right, because they are about different objects: an *observable* is a
# criterion — what would count as success — and a *corpus* is a sample, which inputs you
# happen to have. Neither text performed that reconciliation, and `agent-evals` had no word
# for the first tier at all: `grep -ci 'observable'` and `grep -ci 'requirement'` over it
# both returned 0. Its own §3 convicted the sentence without help from the manifesto — the
# offline suite is the release gate, and a suite that may never be authored up front cannot
# gate a first release, which has no production to grow a corpus from.
#
# So prose alone is not the fix. The tiers are declared machine-readably in their one home,
# and — the part that actually holds — **every section anywhere in this pack that dates an
# eval must name both tiers.** One imperative shipped alone in a document that never named
# the other is exactly how the absolute got here.
EVAL_TIERS_FLOOR = 2
# Named individually because these two ARE the row: `observable` is the concept the pack was
# missing, `corpus` is the rule that survives this change untouched.
EVAL_TIERS_REQUIRED = {"observable", "corpus"}
EVAL_TIERS_DOC = ("agent-evals/SKILL.md", "## 6.")
EVAL_TIERS_DECL = re.compile(r"<!--\s*eval-tiers:\s*([^>]+?)\s*-->")
# Each tier's clock, in words. A tier named with no timing is the concept without the
# requirement — the same hole as doctrine that describes "its own completion test" forever
# and never names the field.
EVAL_TIER_CLOCKS = ("before the implementation", "from production")
# Every phrase in this pack that dates an eval. A section carrying one owes both tiers.
EVAL_TIMING_TRIGGERS = (
    r"never author the suite up front",
    r"authored up front",
    r"eval exists before",
    r"before the prompt is tuned",
    r"before the implementation",
    r"grown from production",
)
# The bar was asserted in two checklists as *before the prompt is tuned* — a real bar, and
# not the manifesto's, which is before the implementation. One line now carries both tiers,
# byte-identical in both hosts by design: 23 words, 12 shingles, inside the duplication floor
# of 20. It is COMPARED rather than trusted, because the drift that matters is one host
# reworded and the other left behind — and both halves would still name both tiers while
# disagreeing about when.
EVAL_TIERS_HOSTS = ("agent-orchestrator/SKILL.md", "agent-harness/SKILL.md")
CHECKLIST_ITEM = re.compile(r"^- \[ \] (.+?)(?=\n- \[ \]|\n\s*\n|\n#|\Z)", re.S | re.M)


def check_eval_tiers_are_named_together():
    rel, heading = EVAL_TIERS_DOC
    path = os.path.join(SKILL_ROOT, *rel.split("/"))
    if not os.path.isfile(path):
        fail(f"{rel}: missing — it is the only home of the two eval tiers")
        return
    body = _section(open(path, encoding="utf-8").read(), heading)
    if body is None:
        fail(f"{rel}: no section starting {heading!r} — the two eval tiers lost their home")
        return
    m = EVAL_TIERS_DECL.search(body)
    if not m:
        fail(f"{rel}: {heading} has no `<!-- eval-tiers: … -->` declaration. The tiers are "
             "prose everywhere else, and prose is what let one of them be stated as an "
             "absolute with the other absent for the whole life of this file")
        return
    tiers = [x.strip() for x in m.group(1).split(",") if x.strip()]
    # Comments stripped before reading the prose, or the declaration itself would satisfy the
    # requirement that the prose names each tier — a guard that cannot fail.
    prose = re.sub(r"<!--.*?-->", "", body, flags=re.S)

    if len(tiers) < EVAL_TIERS_FLOOR:
        fail(f"the eval-tier contract declares {len(tiers)} tier(s), floor is "
             f"{EVAL_TIERS_FLOOR}: {tiers}. The floor is a ratchet, and here it guards the "
             "pair itself — a single tier is the state this repository shipped in, where one "
             "timing rule read as universal because the other had no name")

    for key in sorted(EVAL_TIERS_REQUIRED - set(tiers)):
        fail(f"the eval-tier contract no longer declares {key!r}. `observable` is the "
             "criterion, written before the implementation because a requirement with no "
             "observable cannot be attached to evidence later without inventing the test "
             "after seeing the code; `corpus` is the sample, grown from production because "
             "invented inputs test your imagination. Dropping either turns the other back "
             "into an absolute, which is the 2026-08-18 audit's AG-03 finding")

    for key in tiers:
        if not re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", prose, re.I):
            fail(f"{rel}: the eval-tier contract declares {key!r} but the prose never names "
                 "it — the declaration would then be the only place the tier exists, and a "
                 "reader of the document would never see it")

    word = NUMBER_WORDS.get(len(tiers))
    if word and not re.search(rf"(?<![\w-]){word}(?![\w-])", prose, re.I):
        fail(f"{rel}: the contract has {len(tiers)} tiers and the prose never says {word!r}. "
             "A spelled count nothing checks is how prose and list drift apart")

    low = prose.lower()
    for clock in EVAL_TIER_CLOCKS:
        if clock not in low:
            fail(f"{rel}: the tiers are named but {clock!r} never appears. A tier with no "
                 "clock is the concept without the requirement — the whole finding was that "
                 "one rule had a date and the other had no name, so both dates are stated "
                 "here or neither is enforceable")

    # The part that holds the reconciliation. Every section in the pack that dates an eval
    # must name both tiers, wherever it lives — including a document nobody has written yet.
    for doc_rel, doc_text in sorted(_pack_docs().items()):
        clean = re.sub(r"<!--.*?-->", "", doc_text, flags=re.S)
        # The opening chunk before the first `##` is a section too: that is where the
        # unqualified version of this rule was, and a sweep that skipped it would have
        # scored the original defect as green.
        for sec in re.split(r"(?m)^(?=## )", clean):
            tripped = [t for t in EVAL_TIMING_TRIGGERS if re.search(t, sec, re.I)]
            if not tripped:
                continue
            absent = [k for k in sorted(EVAL_TIERS_REQUIRED)
                      if not re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", sec, re.I)]
            if not absent:
                continue
            first = next((ln for ln in sec.strip().split("\n") if ln.strip()), "")
            where = first[:70] if first.startswith("## ") else "(opening section)"
            fail(f"{doc_rel}: {where} dates an eval ({tripped[0]!r}) and never names "
                 f"{absent} in the same section. The two tiers are stated together or not at "
                 "all: a timing rule alone reads as the whole rule, which is how "
                 "\"never author the suite up front\" came to contradict the requirement "
                 "that every requirement carry an observable before there is code")

    # One line, two hosts, compared.
    picked = {}
    for host in EVAL_TIERS_HOSTS:
        hpath = os.path.join(SKILL_ROOT, *host.split("/"))
        if not os.path.isfile(hpath):
            fail(f"{host}: missing — it is one of the two hosts of the eval-timing line")
            continue
        htext = re.sub(r"<!--.*?-->", "", open(hpath, encoding="utf-8").read(), flags=re.S)
        hits = [" ".join(it.split()) for it in CHECKLIST_ITEM.findall(htext)
                if re.search(r"(?<![\w-])observable(?![\w-])", it, re.I)]
        if len(hits) != 1:
            fail(f"{host}: {len(hits)} checklist item(s) name an observable, expected exactly "
                 "one. This is the line that raises the bar from *before the prompt is tuned* "
                 "to *before the implementation*; zero means the host reverted to the lower "
                 "bar, more than one means two of them can now disagree")
            continue
        if "corpus" not in hits[0].lower():
            fail(f"{host}: the eval-timing checklist line names an observable and not the "
                 "corpus. Half the reconciliation is the half that reads as an absolute")
        picked[host] = hits[0]

    if len(picked) == len(EVAL_TIERS_HOSTS) and len(set(picked.values())) != 1:
        fail("the eval-timing checklist line differs between "
             f"{' and '.join(EVAL_TIERS_HOSTS)}: {list(picked.values())}. One of the two is "
             "now the other's past, and a reader cannot tell which bar this pack holds")


check_eval_tiers_are_named_together()

# ------------------------------- the priority axes, and the scalar that must not return
#
# Fourth use of the same declaration mechanism, against the flattest contradiction the
# 2026-08-18 conformance audit found: `audit.md` opened with *"A prioritized change plan …
# **Not a score**"* and *"pass/fail with a named failure condition beats a scalar that names
# no fix"*, and then computed `P = blast × confidence / effort` and ordered the plan by it.
#
# The manifesto backs the refusal — `manifesto` → *"These axes are not a fake numerical score"*
# — and names FOUR axes, the last being *"How many agents, repositories, services,
# and owners meet at the change"*. Two of them,
# **Irreversibility** and **Coordination**, appeared nowhere in this pack (`grep -ci
# irreversib` → 0, `grep -ci coordinat` → 0), while `effort` — a **cost** — had been
# substituted into their place. So the file held neither position: not the manifesto's axes,
# and not its own refusal of a scalar.
#
# The position taken is the one the document already argued for: publish the axes, drop the
# arithmetic. Which makes two things checkable, and both are checked, because either alone
# leaves the defect reachable — the axes could come back as multiplicands, or the scalar
# could come back under different axis names.
PRIORITY_AXES_DOC = ("agent-harness/references/audit.md", "## Priority")
PRIORITY_AXES_DECL = re.compile(r"<!--\s*priority-axes:\s*([^>]+?)\s*-->")
# Not a floor and not a subset: the manifesto names four axes and this is the whole list, so
# an axis that is not one of them is as wrong as an axis that is missing. `effort` is the
# specific wrong one this row exists for, and it is refused by exactly this equality.
PRIORITY_AXES_REQUIRED = ("impact", "irreversibility", "uncertainty", "coordination")
# A phrase, not a line. `manifesto.md:419-422` rotted: those lines now hold "The
# strongest is mechanical", and the axes moved twenty lines down. Swept 2026-08-24
# with the same change that converted the conformance register (R-003).
PRIORITY_AXES_SOURCE = ('manifesto → "How many agents, repositories, services, and '
                        'owners meet at the change"')
# Any arithmetic over the axes, PRESCRIBED rather than quoted. Two design decisions, and the
# second was found by watching this check refuse a correct document:
#
#  * the name is an alternation, not the literal `P`, because renaming the variable to
#    `score` would have walked the first draft of this check straight past the defect;
#  * the whole line must BE the formula. The shipped defect was `P = blast × confidence /
#    effort` alone on its own line — that is what a reader follows as an instruction. A
#    formula inside a sentence explaining why it was dropped is a citation, and the first
#    draft refused exactly that: the paragraph that records the removal. Naming a dead
#    formula is how the record survives; claiming one is the defect.
PRIORITY_SCALAR = re.compile(
    r"(?m)^\s*`?\s*(?:P|score|priority|rank|weight)\s*=\s*[^`\n]*[×*/][^`\n]*`?\s*$")
# The other half: the formula can be defined anywhere and the plan still ordered by it.
PRIORITY_ORDERING = re.compile(r"ordered by (?:P\b|the (?:score|number|scalar))", re.I)


def check_priority_axes_are_the_manifesto_s_and_carry_no_scalar():
    rel, heading = PRIORITY_AXES_DOC
    path = os.path.join(SKILL_ROOT, *rel.split("/"))
    if not os.path.isfile(path):
        fail(f"{rel}: missing — it is the only home of the audit's priority rule")
        return
    text = open(path, encoding="utf-8").read()
    body = _section(text, heading)
    if body is None:
        fail(f"{rel}: no section starting {heading!r} — the priority rule lost its home")
        return
    m = PRIORITY_AXES_DECL.search(body)
    if not m:
        fail(f"{rel}: {heading} has no `<!-- priority-axes: … -->` declaration. The axis "
             "list was prose, and prose is what let two of the manifesto's four axes be "
             "absent from the whole pack while a cost was substituted for them")
        return
    axes = [x.strip().lower() for x in m.group(1).split(",") if x.strip()]
    prose = re.sub(r"<!--.*?-->", "", body, flags=re.S)

    if tuple(axes) != PRIORITY_AXES_REQUIRED:
        fail(f"{rel}: the priority axes are {axes}, and the manifesto names "
             f"{list(PRIORITY_AXES_REQUIRED)} ({PRIORITY_AXES_SOURCE}). This is an equality, "
             "not a floor: a fifth axis nobody sourced is as wrong as a missing one, and the "
             "defect this closes was `effort` — a cost — standing where Irreversibility and "
             "Coordination should have been")

    for axis in axes:
        if not re.search(rf"(?<![\w-]){re.escape(axis)}", prose, re.I):
            fail(f"{rel}: the declaration names the axis {axis!r} and the prose never does "
                 "— the axis would exist only in a comment, and a reader of the document "
                 "would rank findings without it")

    word = NUMBER_WORDS.get(len(axes))
    if word and not re.search(rf"(?<![\w-]){word}(?![\w-])", prose, re.I):
        fail(f"{rel}: there are {len(axes)} axes and the prose never says {word!r} — a "
             "spelled count nothing checks is how a list and its description drift")

    # The axes must also reach the pack at large, not just this one section: two of them were
    # missing from every file, and a section that names them while no other document does is
    # the same defect one scope smaller.
    pack = "\n".join(_pack_docs().values()).lower()
    for axis in ("irreversib", "coordinat"):
        if axis not in pack:
            fail(f"the pack never uses {axis!r} anywhere. Both of the axes this row restored "
                 "were absent from every document in it, which is why a cost could be "
                 "substituted without anybody noticing a manifesto axis had gone")

    # And the arithmetic, refused across the whole pack rather than one section — a formula
    # moved one heading down is the same contradiction with a better hiding place.
    for doc_rel, doc_text in sorted(_pack_docs().items()):
        hit = PRIORITY_SCALAR.search(doc_text)
        if hit:
            fail(f"{doc_rel}: prescribes a priority scalar — {hit.group(0).strip()[:80]!r}. "
                 "This pack's position is that a score ends the conversation an audit exists "
                 "to start, and multiplication is also a one-way function on the inputs the "
                 "ranking claims can be argued with: `3 × 1 / 3` and `1 × 1 / 1` both print "
                 "1. Publish the axes; do not multiply them")
        order = PRIORITY_ORDERING.search(doc_text)
        if order:
            fail(f"{doc_rel}: orders the plan by a scalar — {order.group(0)!r}. The formula "
                 "can live anywhere and the ranking still be a number; the plan is ordered "
                 "by the axes, first separating axis winning")


check_priority_axes_are_the_manifesto_s_and_carry_no_scalar()


# ------------------------------ every temp tree goes through the residue ledger
#
# `test/residue.py` accounts for what a run leaves in `$TMPDIR` and prints one line about
# it, `nothing` included — ported from `make-skill`, which measured the defect first. It
# only accounts for trees taken through `residue.workspace()`, and that is the hole this
# check closes: the leak was re-planted by swapping one `residue.workspace()` call back to
# a bare `tempfile.mkdtemp()`, the fixture passed, and the ledger printed
# *"this run left nothing — 0 temp tree(s) created"*. A bypass that reports clean is
# indistinguishable from no leak, which is the exact reading the ledger exists to prevent.
#
# So the ledger is the only door. `residue.py` itself is exempt — it is the module that
# calls `mkdtemp` on everyone's behalf — and `TemporaryDirectory` is refused with it,
# because a context manager that cleans up on the happy path still deletes the tree a
# failing case needs to be read.
# Assembled from parts on purpose. Spelled out, the pattern contains the very literals it
# looks for, and this file is inside the set it scans — it passed only because a `)`
# happened to follow each name. A guard that is green by luck is a guard nobody has
# watched, so the names never appear here as callable text.
TEMP_MAKERS = re.compile(r"(?<![\w.])(?:tempfile\.)?(?:" + "mkdtemp" + "|Temporary"
                         + "Directory" + r")\s*\(")
TEMP_LEDGER_EXEMPT = {"residue.py"}


def check_temp_trees_go_through_the_residue_ledger():
    tests = sorted(glob.glob(os.path.join(ROOT, "test", "*.py")))
    if not tests:
        fail("test/: no python files — the suite cannot be checked for temp-tree accounting")
        return
    for path in tests:
        base = os.path.basename(path)
        if base in TEMP_LEDGER_EXEMPT:
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        # Comments and docstrings mention `mkdtemp` when they explain why it is banned. A
        # guard that reads an explanation as a violation refuses the document that records
        # the fix — so only lines that would RUN are read.
        code = "\n".join(ln for ln in text.split("\n")
                         if not ln.lstrip().startswith("#"))
        code = re.sub(r'"""(?:.|\n)*?"""', "", code)
        hit = TEMP_MAKERS.search(code)
        if hit:
            line = code[:hit.start()].count("\n") + 1
            fail(f"test/{base}: creates a temp tree outside the residue ledger — "
                 f"{hit.group(0)!r} near line {line} of the stripped source. Use "
                 "`residue.workspace(tag)`: a tree the ledger never saw is a tree the "
                 "gate's residue line reports as nothing, which is how 2576 nameless "
                 "`tmpXXXXXXXX` directories accumulated with every run printing clean")


check_temp_trees_go_through_the_residue_ledger()


# --------------------- the ledger may not describe an artifact that is not there
#
# AG-07 and AG-08, and they are one defect read from two ends. Three sections of
# `docs/evidence/verification.md` were headed `(AG-0N, unreleased)` and carried *"No
# release: the version stays 0.11.1 and the CHANGELOG is untouched, so every row below is
# measured on the working tree rather than on a published artifact"* — while v0.12.0 was
# tagged, on npm and in the CHANGELOG. Under those paragraphs, 35 rows across the three
# sections all read `**verified**`, against this file's own opening: *"A row sits at `never`
# until somebody has watched its check pass on the shipped artifact — not on a branch, not
# in a plan."*
#
# So a section either states no release and carries no `verified` row, or it names the
# version it shipped in and that version exists. Both directions, because either alone
# leaves a true-looking ledger: the first stops rows being graded against a tree, the second
# stops a section announcing a release nobody cut.
LEDGER = os.path.join("docs", "evidence", "verification.md")
NO_RELEASE = re.compile(r"\*\*No release\*\*|\bunreleased\b", re.I)
STAYS_AT = re.compile(r"version stays `?v?(\d+\.\d+\.\d+)`?")
# Case-insensitive, and that is not cosmetic: the first version of this pattern was
# lowercase-only, and the ledger states the claim as **Shipped in v0.12.0** at the head of
# every section — so every real claim in the file went unchecked while the check reported
# green. Found by a plant that stopped firing, not by reading the regex.
SHIPPED_IN = re.compile(r"shipped in v(\d+\.\d+\.\d+)", re.I)
VERIFIED_ROW = re.compile(r"\*\*verified\*\*")
# A quoted passage is evidence, not an assertion: `*"…"*` is how this ledger cites the
# sentence a row replaced, and an inline code span is how it quotes a plant's own text.
QUOTATION = re.compile(r"\*\"[^\"]*\"\*", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")


def _released_versions(changelog):
    return {m for m in re.findall(r"(?m)^##+\s+\[?v?(\d+\.\d+\.\d+)", changelog)}


def check_ledger_tables_keep_their_shape():
    """A markdown row whose cell count drifts reads as a different row entirely.

    Seen TWICE from this repository, both times caught by the UMBRELLA rather than
    here — B-124 (a grep pattern's `|` in a board row) and B-126 (an orphaned
    fragment left by a failed string replacement, which also carried a bare `|`).
    The family's rule is that a class seen twice becomes a script, so this is the
    script: the member now refuses what a sibling had been catching for it.

    A `|` inside a cell must be escaped as `\|`; the neighbouring rows already do
    it. Splitting on an unescaped pipe is exactly how a reader — and the umbrella —
    counts the columns, so the check counts them the same way.
    """
    for rel in ("docs/evidence/backlog.md", "docs/evidence/verification.md"):
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        width = None
        for n, line in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
            if not line.startswith("|"):
                continue
            cells = len(re.split(r"(?<!\\)\|", line)) - 2
            if re.fullmatch(r"\|[-\s|:]+\|", line):
                continue
            if line.startswith("| id ") or line.startswith("| REQ "):
                width = cells
                continue
            if width is not None and cells != width:
                fail(f"{rel}:{n}: row has {cells} cells against the {width} its own header "
                     "declares — escape a `|` inside a cell as `\\|`, or the columns after "
                     "it shift and Status reads as whatever landed in its place")


def check_the_ledger_matches_what_shipped():
    path = os.path.join(ROOT, LEDGER)
    if not os.path.isfile(path):
        fail(f"{LEDGER}: missing — an absent ledger and a clean one are indistinguishable "
             "from the number alone, which is the reading this file exists to prevent")
        return
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    cpath = os.path.join(ROOT, "CHANGELOG.md")
    changelog = open(cpath, encoding="utf-8").read() if os.path.isfile(cpath) else ""
    released = _released_versions(changelog)
    newest = max((tuple(int(x) for x in v.split(".")) for v in released), default=(0, 0, 0))

    for sec in re.split(r"(?m)^(?=## )", text)[1:]:
        head = sec.splitlines()[0].strip()
        # A ledger that closes this defect QUOTES the sentence it replaced — that is how the
        # record survives — and the first two drafts of this check refused exactly that: the
        # paragraph recording the removal, and the row quoting the plant's own text. The
        # umbrella's rule applies here as much as to a Bash guard: read what is CLAIMED, not
        # what is cited. So a `*"…"*` quotation is dropped before any of these patterns run,
        # and `shipped in vX` additionally has to survive outside a backtick span.
        claimed_text = QUOTATION.sub(" ", sec)
        announce_text = INLINE_CODE.sub(" ", claimed_text)
        if NO_RELEASE.search(claimed_text):
            rows = len(VERIFIED_ROW.findall(claimed_text))
            if rows:
                fail(f"{LEDGER}: {head[:70]!r} declares no release and carries {rows} row(s) "
                     "marked **verified**. This file's own opening puts a row at `never` "
                     "until its check has been watched passing ON THE SHIPPED ARTIFACT — a "
                     "`verified` row over a working tree is the grade standing in for the "
                     "measurement")
            stays = STAYS_AT.search(claimed_text)
            if stays:
                at = tuple(int(x) for x in stays.group(1).split("."))
                if at < newest:
                    fail(f"{LEDGER}: {head[:70]!r} says the version stays "
                         f"{stays.group(1)} while the CHANGELOG has released "
                         f"{'.'.join(str(n) for n in newest)}. The claim was true when it "
                         "was written and false from the moment the tag was cut, and "
                         "nothing re-read it")
        for claimed in sorted(set(SHIPPED_IN.findall(announce_text))):
            if released and claimed not in released:
                fail(f"{LEDGER}: {head[:70]!r} says the work shipped in v{claimed} and the "
                     "CHANGELOG has no such release — a ledger announcing a version nobody "
                     "cut is worse than one that says nothing")


check_the_ledger_matches_what_shipped()

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


check_ledger_tables_keep_their_shape()
check_shipped_front_matter_survives_a_real_reader()


# Notes print on EVERY run, pass or fail. A budget warning that only appeared beside a
# failure would be invisible on exactly the runs where it still had time to be acted on.
if notes:
    print(f"NOTE: {len(notes)} thing(s) inside the gate but past a house limit")
    for n in notes:
        print(f"  ~ {n}")

if FAILURES:
    print(f"FAIL: {len(FAILURES)} problem(s)", file=sys.stderr)
    for f in FAILURES:
        print(f"  - {f}", file=sys.stderr)
    sys.exit(1)

# Counted, never restated. This was `9 + len(skill_dirs)` — a hand-bumped literal, and the
# hand missed: five ledger rows quote the number as evidence that a check was added, and the
# check added on 2026-08-20 did not move it at all. The named checks are read out of this
# module's own globals, so adding one is the only way to change the count.
named_checks = sorted(n for n, v in list(globals().items())
                      if n.startswith("check_") and callable(v))
checks = len(named_checks) + len(skill_dirs)
print(f"OK: agent-stack structurally valid ({checks} checks = {len(named_checks)} named + "
      f"{len(skill_dirs)} per-skill, {len(skill_dirs)} skill(s), v{version})")
