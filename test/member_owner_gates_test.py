#!/usr/bin/env python3
"""Run bounded plants through the real owner validator; account for every copy."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import residue

ROOT = Path(__file__).resolve().parent.parent
BOARD = 'docs/evidence/backlog.md'
RELEASE = '.github/workflows/release.yml'

def duplicate(text):
    line = next(x for x in text.splitlines() if x.startswith('| B-160 |'))
    return text.replace(line, line.replace('| B-160 |', '| B-159 |'), 1)

cases = [
    ('duplicate declaration', BOARD, duplicate, 'board duplicate ID'),
    ('group overlaps later declaration', BOARD, lambda s: s.replace('| B-160 |', '| AG-04 |', 1), 'board duplicate ID'),
    ('even backslash pipe escape', BOARD, lambda s: s.replace('\\| wc -l', '\\\\| wc -l', 1), 'owner board row width'),
    ('missing separator', BOARD, lambda s: s.replace('|---|---|---|---|---|---|---|---|', '', 1), 'matching separator'),
    ('orphan after blank', BOARD, lambda s: duplicate(s.replace('| B-159 |','\n| B-159 |',1)), 'owner board orphan declaration'),
    ('orphan after comment', BOARD, lambda s: duplicate(s.replace('| B-159 |','<!-- table continuation -->\n| B-159 |',1)), 'owner board orphan declaration'),
    ('missing board', BOARD, lambda _: None, 'owner board missing'),
    ('missing header', BOARD, lambda s: s.replace('| id | What | Source |', '| key | What | Source |', 1), 'owner board declaration header'),
    ('missing ancestry', RELEASE, lambda s: s.replace('git merge-base --is-ancestor', 'git merge-base-removed --is-ancestor'), 'release ancestry guard'),
    ('shallow checkout', RELEASE, lambda s: s.replace('fetch-depth: 0', 'fetch-depth: 1'), 'release full-history checkout'),
    ('ancestry conditional', RELEASE, lambda s: s.replace('      - name: The tag must be reachable', '      - if: false\n        name: The tag must be reachable'), 'release ancestry step conditional'),
    ('ancestry ignores failure', RELEASE, lambda s: s.replace('      - name: The tag must be reachable', '      - continue-on-error: true\n        name: The tag must be reachable'), 'release ancestry failure ignored'),
    ('early successful exit', RELEASE, lambda s: s.replace('          if ! git merge-base', '          exit 0\n          if ! git merge-base', 1), 'release ancestry guard'),
]
failures=[]
for label, relative, change, diagnostic in cases:
    residue.open_case(label)
    temporary=Path(residue.workspace('member-owner-gates'))
    copy=temporary/'repo'
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('.git','node_modules','__pycache__','.agent-sync'))
    target=copy/relative
    before=target.read_text();after=change(before);assert before!=after,label
    if after is None:target.unlink()
    else:target.write_text(after)
    p=subprocess.run([sys.executable,str(copy/'test/validate.py')],cwd=copy,capture_output=True,text=True)
    output=p.stdout+p.stderr
    if p.returncode!=1 or diagnostic not in output:
        failures.append(f'{label}: expected exit1 and {diagnostic!r}; got exit{p.returncode}')
    else:residue.close_case(label)
# The original summary repeats IDs deliberately; namespace and formatting must
# not create false duplicates or silently drop declarations.
controls = [
    ('unchanged board', lambda s:s),
    ('foreign namespace distinct', lambda s:s.replace('| B-160 |','| B-118 |',1)),
    ('formatted identifier', lambda s:s.replace('| B-160 |','| **B-160** |',1)),
]
for label, change in controls:
    residue.open_case(label)
    temporary=Path(residue.workspace('member-owner-control'));copy=temporary/'repo'
    shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('.git','node_modules','__pycache__','.agent-sync'))
    target=copy/BOARD;target.write_text(change(target.read_text()))
    p=subprocess.run([sys.executable,str(copy/'test/validate.py')],cwd=copy,capture_output=True,text=True)
    if p.returncode:failures.append(label+' rejected: '+p.stdout+p.stderr)
    else:residue.close_case(label)
for failure in failures:print('FAIL: '+failure)
print(f'Owner gates: {len(cases)+len(controls)} process controls; {len(failures)} failures')
residue.report()
raise SystemExit(bool(failures))
