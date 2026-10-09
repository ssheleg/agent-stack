#!/usr/bin/env python3
"""Read-only explicit-input instruction measurement; never a host load receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat


def import_paths(text):
    """Recognize documented plain @paths, excluding fenced/inline code and quotes.

    This deliberately small Markdown scanner is not the host's implementation.
    Escaped spaces are supported; quotes do not make an import.
    """
    visible = []
    fence = None
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            visible.append("\n")
        elif match:
            fence = match[1]
            visible.append("\n")
        else:
            visible.append(line)
    plain = "".join(visible)
    # Match equal backtick runs, including multiline code spans.
    plain = re.sub(r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)", " ", plain)
    pattern = r'''(?<![\w@\\'"`])@((?:\\ |[^\s'"`<>])+)'''
    return [match[1].replace("\\ ", " ") for match in re.finditer(pattern, plain)]


def canonical(path, parent=None):
    expanded = Path(path).expanduser()
    if not expanded.is_absolute() and parent is not None:
        expanded = parent / expanded
    return expanded.resolve()


def measure(roots, allowed_imports=(), limit_chars=None, max_file_bytes=2_000_000):
    rows, issues, edges, visiting = {}, [], [], set()

    def resolve_inputs(values):
        resolved = []
        for value in values:
            try:
                resolved.append(canonical(value))
            except (OSError, RuntimeError, ValueError):
                issues.append({"kind": "invalid_input_path"})
        return resolved

    root_paths = resolve_inputs(roots)
    allowed = set(root_paths) | set(resolve_inputs(allowed_imports))
    if not root_paths:
        issues.append({"kind": "no_roots"})
    if len(allowed) > 256:
        issues.append({"kind": "too_many_inputs", "maximum": 256})
        root_paths = []

    def visit(path, depth):
        if path in visiting:
            issues.append({"kind": "cycle", "path": str(path)})
            return
        if path in rows:
            return
        if path not in allowed:
            issues.append({"kind": "unlisted_import", "path": str(path)})
            return
        if depth > 4:
            issues.append({"kind": "import_depth_exceeded", "path": str(path), "maximum": 4})
            return
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("not_regular_file")
            # Bounded read even if the file grows after stat; bytes never printed.
            with path.open("rb") as stream:
                data = stream.read(max_file_bytes + 1)
            if len(data) > max_file_bytes:
                raise ValueError("file_too_large")
            content = data.decode("utf-8")
        except (OSError, UnicodeError, ValueError) as exc:
            issues.append({"kind": "unreadable", "path": str(path),
                           "reason": str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else type(exc).__name__})
            return
        rows[path] = {"path": str(path), "characters": len(content), "utf8_bytes": len(data),
                      "lines": len(content.splitlines()), "sha256": hashlib.sha256(data).hexdigest()}
        visiting.add(path)
        for value in import_paths(content):
            try:
                target = canonical(value, path.parent)
            except (OSError, RuntimeError, ValueError):
                issues.append({"kind": "invalid_import_path", "source": str(path)})
                continue
            edges.append({"source": str(path), "target": str(target)})
            visit(target, depth + 1)
        visiting.remove(path)

    for root in root_paths:
        visit(root, 0)
    files = sorted(rows.values(), key=lambda row: row["path"])
    total = sum(row["characters"] for row in files)
    groups = {}
    for row in files:
        groups.setdefault(row["sha256"], []).append(row["path"])
    over = limit_chars is not None and total > limit_chars
    return {
        "schema": 1,
        "scope": "explicit files and allowed imports; not a host load receipt",
        "character_unit": "Unicode code points; not tokens or UTF-16 units",
        "status": "PARTIAL" if issues else ("OVER_BUDGET" if over else "MEASURED"),
        "limit_chars": limit_chars,
        "over_budget": over,
        "total_characters": total,
        "total_utf8_bytes": sum(row["utf8_bytes"] for row in files),
        "files": files,
        "import_edges": edges,
        "duplicate_content": [paths for paths in groups.values() if len(paths) > 1],
        "issues": issues,
    }


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="known instruction roots; no discovery")
    parser.add_argument("--allow-import", action="append", default=[], help="explicit file allowed for import; repeat as needed")
    parser.add_argument("--limit-chars", type=positive, help="your local character budget, not a claimed host limit")
    parser.add_argument("--max-file-bytes", type=positive, default=2_000_000)
    args = parser.parse_args()
    result = measure(args.files, args.allow_import, args.limit_chars, args.max_file_bytes)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if result["status"] == "PARTIAL" else int(result["over_budget"])


if __name__ == "__main__":
    raise SystemExit(main())
