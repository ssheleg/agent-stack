#!/usr/bin/env python3
"""`residue.py --reap-own`: remove only the trees the old leaking fixture left (AG-06b).

Before the port to `residue.workspace()`, `test/plant_guard_test.py` made eight nameless
`tempfile.mkdtemp()` trees per run and removed none; the identical fixture (md5
`623a086d10a04940573c31cbebb93e31`) did the same in `seo-aeo-audit`. Those trees are named
`tmpXXXXXXXX` like every other program's, so a prefix cannot attribute them, and the operator's
rule is that a run frees disk only through residue it can prove is its own.

Content can prove it. The fixture wrote fixed bytes into a fixed shape, and each of its cases
left one of seven end states. A directory is claimed only when ALL of these hold:

- a direct child of the temp root, named as `mkdtemp()` names (`tmp` + 8 of `[a-z0-9_]`),
  and not a symlink;
- its entries are exactly `copy/` and, optionally, `copy.plant-manifest.json`;
- `copy/` holds, as regular files with no symlinks, exactly one of the seven file sets the
  fixture's cases end in, byte for byte (`sub/b.sh` is in every one);
- the manifest, when present, is the fixture's own snapshot: `a.txt` and `sub/b.sh` with the
  fixture's two SHA-256 digests and nothing else;
- nothing in it changed in the last `--min-age-hours` (default 24), so a run still in
  progress is never reaped from under itself.

Anything that differs by one byte, one entry, one name or one link is somebody else's and is
left alone. A dry run is the default; `--apply` removes, re-checking each tree immediately
before it goes. The fingerprint identifies the FIXTURE, not the repository: a tree from
`seo-aeo-audit`'s byte-identical copy matches too, and both are this family's own suites.
"""
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import time

A = b"hello\n"
A_PLANTED = b"hello\nplanted\n"
B = b"#!/bin/sh\necho hi\n"
ORPHAN = b"# orphan\n"
MANIFEST = "copy.plant-manifest.json"
NAME = re.compile(r"^tmp[a-z0-9_]{8}$")
MAX_BYTES = 4096


def sha(data):
    return hashlib.sha256(data).hexdigest()


# The seven end states, as {relative path: bytes}. `nochange` is also where the
# manifest-outside, missing-snapshot and churn-before-verify cases stop.
STATES = (
    {"a.txt": A, "sub/b.sh": B},                                   # no change, mode, manifest
    {"a.txt": A_PLANTED, "sub/b.sh": B},                           # content edit
    {"a.txt": A, "sub/b.sh": B, "orphan.md": ORPHAN},              # new file
    {"sub/b.sh": B},                                               # deletion
    {"a.txt": A, "sub/b.sh": B, ".git/index": b"before\n"},        # git churn, before
    {"a.txt": A, "sub/b.sh": B, ".git/index": b"after\n"},         # git churn, after
)
FIXTURE_SNAPSHOT = sorted([("a.txt", sha(A)), ("sub/b.sh", sha(B))])


def _read_tree(copy):
    """{rel: bytes} for every entry under `copy`, or None if anything is not plain."""
    files, total = {}, 0
    for dirpath, dirnames, filenames in os.walk(copy, followlinks=False):
        for d in dirnames:
            if os.path.islink(os.path.join(dirpath, d)):
                return None
        for f in filenames:
            full = os.path.join(dirpath, f)
            st = os.lstat(full)
            if not stat.S_ISREG(st.st_mode):
                return None
            total += st.st_size
            if total > MAX_BYTES:
                return None
            with open(full, "rb") as fh:
                files[os.path.relpath(full, copy).replace(os.sep, "/")] = fh.read()
    return files


def _newest_mtime(top):
    newest = os.lstat(top).st_mtime
    for dirpath, dirnames, filenames in os.walk(top, followlinks=False):
        for n in dirnames + filenames:
            newest = max(newest, os.lstat(os.path.join(dirpath, n)).st_mtime)
    return newest


def is_fixture_tree(top, min_age_s=24 * 3600, now=None):
    """True only when `top` is, byte for byte, a tree the leaking fixture left."""
    try:
        if not NAME.match(os.path.basename(top)):
            return False
        st = os.lstat(top)
        if not stat.S_ISDIR(st.st_mode):
            return False                       # a symlink or a file is never ours
        entries = set(os.listdir(top))
        if entries not in ({"copy"}, {"copy", MANIFEST}):
            return False
        copy = os.path.join(top, "copy")
        if not stat.S_ISDIR(os.lstat(copy).st_mode):
            return False
        files = _read_tree(copy)
        if files is None or files not in STATES:
            return False
        if MANIFEST in entries:
            mpath = os.path.join(top, MANIFEST)
            if not stat.S_ISREG(os.lstat(mpath).st_mode) or os.lstat(mpath).st_size > MAX_BYTES:
                return False
            with open(mpath, encoding="utf-8") as fh:
                snap = json.load(fh)
            if not isinstance(snap, list) or not all(
                    isinstance(e, list) and len(e) == 3 and all(isinstance(x, str) for x in e)
                    for e in snap):
                return False
            if sorted((e[0], e[2]) for e in snap) != FIXTURE_SNAPSHOT:
                return False
        now = time.time() if now is None else now
        return now - _newest_mtime(top) >= min_age_s
    except (OSError, ValueError, UnicodeDecodeError):
        return False                           # unreadable is not provably ours


def find_own(tmpdir, min_age_s=24 * 3600):
    out = []
    for name in sorted(os.listdir(tmpdir)):
        if NAME.match(name):
            path = os.path.join(tmpdir, name)
            if is_fixture_tree(path, min_age_s):
                out.append(path)
    return out


def main(argv):
    apply = "--apply" in argv
    tmpdir = tempfile.gettempdir()
    min_age_h = 24.0
    it = iter(argv)
    for a in it:
        if a == "--tmpdir":
            tmpdir = next(it, "")
        elif a == "--min-age-hours":
            min_age_h = float(next(it, "24"))
        elif a not in ("--reap-own", "--apply"):
            print(f"reap-own CANNOT RUN: unknown argument {a!r}", file=sys.stderr)
            return 2
    if not os.path.isdir(tmpdir):
        print(f"reap-own CANNOT RUN: {tmpdir!r} is not a directory", file=sys.stderr)
        return 2
    min_age_s = min_age_h * 3600
    own = find_own(tmpdir, min_age_s)
    if not apply:
        print(f"reap-own: {len(own)} tree(s) match the leaking fixture's fingerprint under "
              f"{tmpdir} — DRY RUN, nothing removed. Re-run with --apply to remove them.")
        for p in own[:20]:
            print(f"    {p}")
        if len(own) > 20:
            print(f"    … and {len(own) - 20} more")
        return 0
    removed, skipped = 0, 0
    for p in own:
        if not is_fixture_tree(p, min_age_s):  # re-checked right before it goes
            skipped += 1
            continue
        shutil.rmtree(p, ignore_errors=True)
        if os.path.exists(p):
            skipped += 1
        else:
            removed += 1
    print(f"reap-own: {len(own)} tree(s) matched under {tmpdir}; removed {removed}, "
          f"left {skipped} (changed since the scan or would not go)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
