#!/usr/bin/env python3
"""`residue.py --reap-own`: remove only the trees the old leaking fixture left (AG-06b).

Before the port to `residue.workspace()`, `test/plant_guard_test.py` made eight nameless
`tempfile.mkdtemp()` trees per run and removed none; the identical fixture (md5
`623a086d10a04940573c31cbebb93e31`) did the same in `seo-aeo-audit`. Those trees are named
`tmpXXXXXXXX` like every other program's, so a prefix cannot attribute them, and the operator's
rule is that a run frees disk only through residue it can prove is its own.

Content can prove it. The fixture wrote fixed bytes into a fixed shape, and its eight cases
end in five distinct file sets (no-change, mode-only, manifest-outside and missing-snapshot
share one). A directory is claimed only when ALL of these hold:

- a direct child of the temp root, named as `mkdtemp()` names (`tmp` + 8 of `[a-z0-9_]`),
  and not a symlink;
- its entries are exactly `copy/` and, optionally, `copy.plant-manifest.json`;
- `copy/` holds, as regular files with no symlinks, exactly one of those five file sets, byte
  for byte (`sub/b.sh` is in every one), and exactly the directories that set needs (`sub`,
  plus `.git` for the churn state) — an extra directory, empty or not, is somebody else's;
- the manifest, when present, is the fixture's own snapshot: `a.txt` and `sub/b.sh` with the
  fixture's two SHA-256 digests and nothing else;
- nothing in it changed in the last `--min-age-hours` (default 24), so a run still in
  progress is never reaped from under itself.

Anything that differs by one byte, one entry, one name or one link is somebody else's and is
left alone. A dry run is the default. `--apply` first renames each tree, atomically, to a
quarantine name in the same root, re-verifies the renamed tree, and only then removes it; a
tree that changed in that window is renamed back. The root itself is refused when it is empty,
`/`, `$HOME` or an ancestor of `$HOME` (after `realpath`), and the age floor when it is not a
finite number of at least one hour. The fingerprint identifies the FIXTURE, not the repository: a tree from
`seo-aeo-audit`'s byte-identical copy matches too, and both are this family's own suites.
"""
import hashlib
import json
import math
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


# The five end states, as ({relative path: bytes}, {relative directories}). The churn case
# writes `.git/index` as "before" and the snapshot then runs; a tree left at "before" means
# the snapshot never ran, which is not a state the fixture's cases end in.
STATES = (
    ({"a.txt": A, "sub/b.sh": B}, {"sub"}),                        # no change, mode, manifest, no snap
    ({"a.txt": A_PLANTED, "sub/b.sh": B}, {"sub"}),                # content edit
    ({"a.txt": A, "sub/b.sh": B, "orphan.md": ORPHAN}, {"sub"}),   # new file
    ({"sub/b.sh": B}, {"sub"}),                                    # deletion
    ({"a.txt": A, "sub/b.sh": B, ".git/index": b"after\n"}, {"sub", ".git"}),  # git churn
)
FIXTURE_SNAPSHOT = sorted([("a.txt", sha(A)), ("sub/b.sh", sha(B))])


def _read_tree(copy):
    """({rel: bytes}, {rel dirs}) for everything under `copy`, or None if anything is not plain."""
    files, dirs, total = {}, set(), 0
    for dirpath, dirnames, filenames in os.walk(copy, followlinks=False):
        for d in dirnames:
            full = os.path.join(dirpath, d)
            if os.path.islink(full):
                return None
            dirs.add(os.path.relpath(full, copy).replace(os.sep, "/"))
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
    return files, dirs


def _newest_mtime(top):
    newest = os.lstat(top).st_mtime
    for dirpath, dirnames, filenames in os.walk(top, followlinks=False):
        for n in dirnames + filenames:
            newest = max(newest, os.lstat(os.path.join(dirpath, n)).st_mtime)
    return newest


def is_fixture_tree(top, min_age_s=24 * 3600, now=None):
    """True only when `top` is, byte for byte, a tree the leaking fixture left."""
    return bool(NAME.match(os.path.basename(top))) and _has_fixture_shape(top, min_age_s, now)


def _has_fixture_shape(top, min_age_s=24 * 3600, now=None):
    """The content half of the fingerprint, independent of the name — so a tree renamed to
    its quarantine name can be re-verified by exactly the same rule."""
    try:
        st = os.lstat(top)
        if not stat.S_ISDIR(st.st_mode):
            return False                       # a symlink or a file is never ours
        entries = set(os.listdir(top))
        if entries not in ({"copy"}, {"copy", MANIFEST}):
            return False
        copy = os.path.join(top, "copy")
        if not stat.S_ISDIR(os.lstat(copy).st_mode):
            return False
        tree = _read_tree(copy)
        if tree is None or tree not in STATES:
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


QUARANTINE_PREFIX = ".reap-own-quarantine-"


def reap(paths, root, min_age_s, _window=None):
    """Remove each tree only after it has been moved out of reach and re-verified there.

    `os.rename` within one directory is atomic, so after it nobody holding the old path can
    write into the tree; the content is then checked again under the new name, and a tree
    that no longer matches goes back to its own name. `_window` is a test seam called with
    the quarantine path between the rename and the re-check. Returns (removed, left).
    """
    removed = left = 0
    for p in paths:
        q = os.path.join(root, "%s%d-%s" % (QUARANTINE_PREFIX, os.getpid(),
                                            os.path.basename(p)))
        try:
            os.rename(p, q)
        except OSError:
            left += 1                          # gone or moved since the scan: not ours now
            continue
        if _window:
            _window(q)
        if not _has_fixture_shape(q, min_age_s):
            try:
                os.rename(q, p)                # changed in the window: give it its name back
            except OSError:
                print(f"reap-own: {q} changed after the scan and could not be renamed back "
                      f"to {p}; left in place", file=sys.stderr)
            left += 1
            continue
        shutil.rmtree(q, ignore_errors=True)
        if os.path.exists(q):
            left += 1
        else:
            removed += 1
    return removed, left


def _refuse(msg):
    print(f"reap-own CANNOT RUN: {msg}", file=sys.stderr)
    return 2


def _unsafe_root(tmpdir):
    """Why `tmpdir` must not be reaped, or None. Compared after realpath on both sides."""
    if not tmpdir:
        return "the temp root is empty"
    real = os.path.realpath(tmpdir)
    home = os.path.realpath(os.path.expanduser("~")) if os.environ.get("HOME") else None
    if real == os.path.realpath(os.sep):
        return f"{tmpdir!r} is the filesystem root"
    if home and real == home:
        return f"{tmpdir!r} is $HOME"
    if home and home.startswith(real.rstrip(os.sep) + os.sep):
        return f"{tmpdir!r} is an ancestor of $HOME"
    return None


def main(argv):
    apply = "--apply" in argv
    tmpdir = tempfile.gettempdir()
    min_age_raw = "24"
    it = iter(argv)
    for a in it:
        if a == "--tmpdir":
            tmpdir = next(it, "")
        elif a == "--min-age-hours":
            min_age_raw = next(it, "")
        elif a not in ("--reap-own", "--apply"):
            return _refuse(f"unknown argument {a!r}")
    try:
        min_age_h = float(min_age_raw)
    except ValueError:
        return _refuse(f"--min-age-hours {min_age_raw!r} is not a number")
    if not math.isfinite(min_age_h) or min_age_h < 1:
        return _refuse(f"--min-age-hours {min_age_raw!r} must be a finite number of at "
                       "least 1 — a younger tree may belong to a run still in progress")
    why = _unsafe_root(tmpdir)
    if why:
        return _refuse(why)
    if not os.path.isdir(tmpdir):
        return _refuse(f"{tmpdir!r} is not a directory")
    tmpdir = os.path.realpath(tmpdir)
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
    removed, left = reap(own, tmpdir, min_age_s)
    print(f"reap-own: {len(own)} tree(s) matched under {tmpdir}; removed {removed}, "
          f"left {left} (changed since the scan, or would not go)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
