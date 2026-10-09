# Instruction budgets — preserve requirements, reduce always-loaded text

**Load this when:** a host warns about instruction size, several instruction files
repeat policy, or a cleanup proposes moving rules into imports or skill references.

**Spec pinned:** Claude Code memory documentation, instruction loading and imports · read 2026-10-09

## Contents

- Separate three measurements
- Preserve before changing
- Measure explicit inputs
- Acceptance and limits
- Sources

## Separate three measurements

Claude Code documents that ancestor instruction files load at launch; descendants
load when relevant. Imports also load at launch, resolve relative to their owner,
and recurse up to four hops. Code spans and fenced code blocks suppress imports;
spaces in imported paths use backslash escapes, not quotes. The documented
under-200-lines target is guidance, not a universal refusal threshold.
[Source: Claude Code memory documentation](https://code.claude.com/docs/en/memory).

Keep these measurements separate:

1. **Always-loaded instructions:** the actual startup chain and eagerly imported
   content. Moving its paragraphs behind eager imports changes organization.
2. **Skill discovery:** names and descriptions offered by the host. Installed,
   available, selected and loaded are different observations.
3. **On-demand skill bodies and references:** only the material actually opened
   for the task. Do not sum every installed body as if all load at launch.

Use the threshold printed by the observed host or a declared local budget. A
warning at 150,000 characters on one installation does not establish a universal
Claude Code limit. Characters, UTF-8 bytes and tokenizer results are different
units; label the unit, counter and revision used.

## Preserve before changing

1. Read the exact loaded-chain inventory from the host when available. Inventory
   explicit files and imports; do not recursively dump a home directory or scan
   credential stores. Keep private instruction content and backups local.
2. Back up each owned file before changing it. Record hashes, file permissions
   and restore paths locally. Existing managed sections retain their installer
   ownership; do not rewrite another tool's block to make the number smaller.
3. Build a requirement map: old section → retained short rule or conditional
   reference → load trigger → verification. Preserve authorization boundaries,
   secrets handling, routing, working agreements and required delivery checks in
   the loaded core. A shorter file that silently drops these is a failed cleanup.
4. Remove exact repetitions only after confirming the surviving copy loads in
   every affected scope. Put project facts in their project, not global policy.
   Move task-specific procedures to a skill or ordinary reference with an explicit
   condition such as “before deployment, read …”. A mere link with no trigger is
   not proof of reachability. Do not replace the entire core with “read everything”.
5. Measure again and exercise representative tasks: everyday change, affected
   specialist task, secret handling, external action, and resume/handoff. Check
   that each selects the required rule. Mechanical coverage cannot prove that a
   model obeyed the rule; record behavioral replay as NOT_RUN when unavailable.
6. Reload a fresh host session and inspect its loaded files. Retain separate
   receipts for changed bytes, measured size and actual host loading. A running
   session keeps its existing context until the host reloads it.

Avoid swapping bulk text into unscoped rules, eager imports or unconditional
“read this other file” directives: these can recreate the same startup cost.
Improved model accuracy or latency needs a measured baseline and candidate run;
smaller files alone establish neither.

## Measure explicit inputs

Run the bundled script without loading its source into the task context:

```bash
python3 scripts/instruction_budget.py /project/CLAUDE.md /policy/CLAUDE.md \
  --allow-import /project/docs/always-loaded.md --limit-chars 120000
```

Paths above are placeholders. Supply only files that belong to the inspected
chain. Repeat `--allow-import` for each approved imported file. Root arguments
are allowed automatically; an allowed import is counted only when reachable.
A missing or unlisted import yields PARTIAL rather than reading arbitrary files.

Output contains paths, hashes, counts, import edges and issue categories, never
file bodies. Paths and hashes can themselves be private: keep operational output
local; use synthetic fixtures or reviewed aggregate metrics in public reports.
The script has no write, execution, network or discovery feature.

| Result | Meaning | Exit |
|---|---|---|
| MEASURED | Every input in this explicit graph was measured within the supplied budget, if any | 0 |
| OVER_BUDGET | Complete graph exceeds the caller's budget | 1 |
| PARTIAL | Missing/unreadable/unlisted input, cycle or traversal limit; observed sum is incomplete | 2 |

The total counts each resolved path once; a diamond import does not inflate it.
Distinct files with identical content both count and appear in duplicate groups.
This is a declared accounting model, not a claim about host deduplication. Symlink
aliases resolve to one path. Hard-link identities are not deduplicated.
A Unicode code point is one character here, including an astral symbol; it is not
one UTF-16 unit or one token. Decode failures never become replacement characters.
Reads are bounded to 2,000,000 bytes per file by default and 256 allowed paths;
non-regular inputs are refused. These are tool bounds, not host limits.

## Acceptance and limits

This scanner approximates documented plain `@path` imports, escaped spaces,
backtick spans and fenced blocks. It does not implement every Markdown edge case,
host version, path-scoped rule, consent state, implicit ancestor, organization
policy, dynamic hook, auto-memory file, skill injection or MCP tool schema.
Unusual syntax requires manual review. It does not verify semantic coverage or
turn prompt rules into an enforcement boundary.

Use both positive and negative controls: a clean small chain, a deliberately
oversized chain, eager import of a large file, missing import and a retained
mandatory requirement. Hash the original inputs before and after the check to
confirm it did not change them. Restore from the local backup if coverage fails.
Run the same measurement after future edits, then inspect the host's own load
view when its configuration changes. An unrelated MCP authentication warning
requires separate host authentication diagnosis; deleting instructions cannot
repair credentials.

## Sources

- [Claude Code: memory and instruction files](https://code.claude.com/docs/en/memory)
  — loading, imports and the line-count recommendation; checked 2026-10-09.
- The requirement map, explicit allowlist, local budget and acceptance sequence
  above are this skill's engineering procedure, not additional vendor limits.
