#!/usr/bin/env python3
"""Fixtures for `residue.py --reap-own` (AG-06b), run in a sandbox, never the real $TMPDIR.

Every case builds its own fake temp root inside a `residue.workspace()` and passes it with
`--tmpdir`, so nothing here can read or remove a directory this run did not make. The trees
are the eight terminal states of the leaking fixture (`plant_guard_test.py` before the port)
plus near-misses that differ by one byte, one entry, one name or one symlink: a reaper that
removes a near-miss is deleting somebody else's directory.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import residue  # noqa: E402
import reap_own  # noqa: E402

failures = []
OLD = time.time() - 3 * 86400


def case(name, fn):
    residue.open_case(name)
    try:
        fn()
    except Exception as e:  # an error is a failure too, and must not stop the cases after it
        e = e if isinstance(e, AssertionError) else f"{type(e).__name__}: {e}"
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")
    else:
        print(f"  ok  {name}")
        residue.close_case(name)


def put(path, data, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    os.chmod(path, mode)


def age(top, when=OLD):
    for dirpath, dirnames, filenames in os.walk(top):
        for n in dirnames + filenames:
            os.utime(os.path.join(dirpath, n), (when, when), follow_symlinks=False)
    os.utime(top, (when, when))


def fixture_tree(tmp, name, state="nochange", manifest=True):
    """One leaked tree exactly as the old fixture left it, in one of its terminal states."""
    top = os.path.join(tmp, name)
    copy = os.path.join(top, "copy")
    if state != "deleted":
        put(os.path.join(copy, "a.txt"),
            reap_own.A_PLANTED if state == "content" else reap_own.A)
    put(os.path.join(copy, "sub", "b.sh"), reap_own.B, 0o644 if state == "mode" else 0o755)
    if state == "newfile":
        put(os.path.join(copy, "orphan.md"), reap_own.ORPHAN)
    if state == "gitchurn":
        put(os.path.join(copy, ".git", "index"), b"after\n")
    if manifest:
        snap = [["a.txt", "0o644", reap_own.sha(reap_own.A)],
                ["sub/b.sh", "0o755", reap_own.sha(reap_own.B)]]
        with open(os.path.join(top, "copy.plant-manifest.json"), "w") as fh:
            json.dump(snap, fh)
    age(top)
    return top


def sandbox():
    tmp = residue.workspace("reap-own")
    return tmp


def cli(tmp, *extra, home=None):
    env = dict(os.environ)
    if home is not None:
        env["HOME"] = home
    r = subprocess.run([sys.executable, os.path.join(HERE, "residue.py"), "--reap-own",
                        "--tmpdir", tmp, *extra], capture_output=True, text=True, env=env)
    return r


def refused(r, why):
    assert r.returncode == 2, f"{why}: expected exit 2, got {r.returncode}: {r.stdout}"
    assert "CANNOT RUN" in r.stderr and "Traceback" not in r.stderr, f"{why}: {r.stderr}"


STATES = ["content", "mode", "nochange", "newfile", "deleted", "gitchurn"]


def every_terminal_state_is_recognised():
    tmp = sandbox()
    names = []
    for i, st in enumerate(STATES):
        names.append(os.path.basename(fixture_tree(tmp, "tmp%08d" % i, st)))
    names.append(os.path.basename(fixture_tree(tmp, "tmpnosnap01", "nochange", manifest=False)))
    found = sorted(os.path.basename(p) for p in reap_own.find_own(tmp))
    assert found == sorted(names), f"expected {sorted(names)}, found {found}"


def near_misses_are_left_alone():
    tmp = sandbox()
    # one extra byte
    t = fixture_tree(tmp, "tmpextrab01")
    put(os.path.join(t, "copy", "a.txt"), reap_own.A + b"x")
    age(t)
    # one extra entry
    t = fixture_tree(tmp, "tmpextraf01")
    put(os.path.join(t, "copy", "notes.txt"), b"mine\n")
    age(t)
    # an extra entry at the top
    t = fixture_tree(tmp, "tmpextrat01")
    put(os.path.join(t, "keep.db"), b"\0")
    age(t)
    # a name that mkdtemp() would not produce
    fixture_tree(tmp, "agent-stack-test-1-x")
    fixture_tree(tmp, "tmp_short")
    # a symlink where a file was
    t = fixture_tree(tmp, "tmpsymlnk01")
    os.remove(os.path.join(t, "copy", "a.txt"))
    os.symlink("/etc/hosts", os.path.join(t, "copy", "a.txt"))
    age(t)
    # the top itself a symlink to a fixture-shaped tree elsewhere
    real = fixture_tree(tmp, "realtree-not-tmp")
    os.symlink(real, os.path.join(tmp, "tmplinked01"))
    # a manifest that is not the fixture's
    t = fixture_tree(tmp, "tmpbadman01")
    with open(os.path.join(t, "copy.plant-manifest.json"), "w") as fh:
        json.dump([["a.txt", "0o644", "0" * 64]], fh)
    age(t)
    # b.sh missing: the fixture never deletes it
    t = fixture_tree(tmp, "tmpnobsh001")
    os.remove(os.path.join(t, "copy", "sub", "b.sh"))
    age(t)
    # The plants must differ by the property they name, not by an accident of naming: every
    # near-miss but the two deliberate name-misses carries a name mkdtemp() could produce.
    named = [n for n in os.listdir(tmp) if n not in ("agent-stack-test-1-x", "tmp_short",
                                                      "realtree-not-tmp")]
    bad = [n for n in named if not reap_own.NAME.match(n)]
    assert not bad, f"PLANT DID NOT LAND: {bad} are excluded by name, not by content"
    found = sorted(os.path.basename(p) for p in reap_own.find_own(tmp))
    assert found == [], f"near-misses were claimed as own: {found}"


def a_young_tree_is_left_alone():
    tmp = sandbox()
    t = fixture_tree(tmp, "tmpyoung001")
    age(t, time.time())
    assert reap_own.find_own(tmp) == [], "a tree younger than the age floor was claimed"
    assert reap_own.find_own(tmp, min_age_s=0) == [t], "the age floor is not the only gate"


def dry_run_is_the_default_and_removes_nothing():
    tmp = sandbox()
    t = fixture_tree(tmp, "tmpdryrun01")
    r = cli(tmp)
    assert r.returncode == 0, f"exit {r.returncode}: {r.stderr}"
    assert os.path.isdir(t), "the dry run removed a tree"
    line = [ln for ln in r.stdout.splitlines() if ln.startswith("reap-own:")]
    assert line and "1 tree(s) match" in line[0] and "DRY RUN" in line[0], r.stdout


def apply_removes_exactly_the_matches():
    tmp = sandbox()
    own = [fixture_tree(tmp, "tmpapply0%02d" % i, st) for i, st in enumerate(STATES)]
    other = fixture_tree(tmp, "tmpother001")
    put(os.path.join(other, "copy", "notes.txt"), b"mine\n")
    age(other)
    r = cli(tmp, "--apply")
    assert r.returncode == 0, f"exit {r.returncode}: {r.stderr}"
    gone = [p for p in own if not os.path.exists(p)]
    assert len(gone) == len(own), f"{len(own) - len(gone)} matching tree(s) survived --apply"
    assert os.path.isdir(other), "--apply removed a tree that is not the fixture's"
    assert f"removed {len(own)}" in r.stdout, r.stdout


def a_missing_tmpdir_refuses():
    r = cli("/nonexistent/reap-own-root")
    assert r.returncode == 2, f"expected 2, got {r.returncode}"
    assert "CANNOT RUN" in r.stderr, r.stderr


# ---- review round on PR #45: each case below was written before its fix and watched failing.
# The root cases run with HOME pointed into a sandbox and never pass --apply, so a reaper that
# wrongly accepted the root could only list, never remove.

def the_filesystem_root_is_refused():
    refused(cli("/"), "--tmpdir /")
    refused(cli(""), "--tmpdir ''")


def home_is_refused():
    home = os.path.join(sandbox(), "home")
    os.makedirs(home)
    refused(cli(home, home=home), "--tmpdir $HOME")
    refused(cli(home + "/sub/..", home=home), "--tmpdir $HOME spelled through ..")


def an_ancestor_of_home_is_refused():
    box = sandbox()
    home = os.path.join(box, "users", "me")
    os.makedirs(home)
    refused(cli(os.path.join(box, "users"), home=home), "--tmpdir parent of $HOME")
    refused(cli(box, home=home), "--tmpdir grandparent of $HOME")


def a_bad_age_floor_is_refused():
    tmp = sandbox()
    for v in ("nan", "inf", "-inf", "0", "0.5", "-3", "soon", ""):
        refused(cli(tmp, "--min-age-hours", v), f"--min-age-hours {v!r}")
    r = cli(tmp, "--min-age-hours", "1")
    assert r.returncode == 0, f"--min-age-hours 1 refused: {r.stderr}"


def a_tree_changed_in_the_removal_window_is_put_back():
    tmp = sandbox()
    t = fixture_tree(tmp, "tmpwindow01")
    other = fixture_tree(tmp, "tmpwindow02")

    def tamper(quarantined):
        # Somebody writes into the tree between the scan and the removal.
        assert os.path.basename(quarantined) != "tmpwindow01", "the tree was not quarantined"
        assert os.path.dirname(quarantined) == tmp, "quarantine left the temp root"
        if "tmpwindow01" in quarantined:
            put(os.path.join(quarantined, "copy", "late.txt"), b"mine\n")

    removed, left = reap_own.reap([t, other], tmp, min_age_s=0, _window=tamper)
    assert os.path.isdir(t), "a tree changed in the window was removed"
    assert os.path.isfile(os.path.join(t, "copy", "late.txt")), "the changed tree lost its write"
    assert not os.path.exists(other), "the untouched tree was not removed"
    assert (removed, left) == (1, 1), f"expected (1, 1), got {(removed, left)}"
    assert sorted(os.listdir(tmp)) == ["tmpwindow01"], f"quarantine residue: {os.listdir(tmp)}"


def an_extra_empty_directory_is_not_the_fixture():
    tmp = sandbox()
    t = fixture_tree(tmp, "tmpemptyd01")
    os.makedirs(os.path.join(t, "copy", "mine"))
    age(t)
    t2 = fixture_tree(tmp, "tmpemptyd02")
    os.makedirs(os.path.join(t2, "copy", ".git"))   # .git without the churn state's index
    age(t2)
    found = sorted(os.path.basename(p) for p in reap_own.find_own(tmp))
    assert found == [], f"a tree with an extra empty directory was claimed: {found}"


def the_counts_are_the_fixture_s():
    assert len(reap_own.STATES) == 5, f"{len(reap_own.STATES)} file sets, the fixture has 5"
    assert not any(st[0].get(".git/index") == b"before\n" for st in reap_own.STATES), \
        "the churn case's pre-snap state is not terminal"


CASES = [
    ("the fixture's eight cases, five distinct file sets, are all recognised", every_terminal_state_is_recognised),
    ("near-misses by one byte, entry, name, symlink or manifest are left alone", near_misses_are_left_alone),
    ("a tree younger than the age floor is left alone", a_young_tree_is_left_alone),
    ("dry run is the default and removes nothing", dry_run_is_the_default_and_removes_nothing),
    ("--apply removes exactly the matches", apply_removes_exactly_the_matches),
    ("a missing temp root refuses rather than reports clean", a_missing_tmpdir_refuses),
    ("--tmpdir / (and an empty root) is refused", the_filesystem_root_is_refused),
    ("--tmpdir $HOME is refused", home_is_refused),
    ("--tmpdir at an ancestor of $HOME is refused", an_ancestor_of_home_is_refused),
    ("a non-finite, sub-hour or non-numeric age floor is refused", a_bad_age_floor_is_refused),
    ("a tree changed in the removal window is put back, not removed", a_tree_changed_in_the_removal_window_is_put_back),
    ("an extra empty directory makes a tree somebody else's", an_extra_empty_directory_is_not_the_fixture),
    ("the end-state count is the fixture's, five", the_counts_are_the_fixture_s),
]
for n, f in CASES:
    case(n, f)

if failures:
    print(f"\nFAIL: {len(failures)} of {len(CASES)}")
    sys.exit(1)
print(f"\nPASS: reap-own — {len(CASES)} cases")
