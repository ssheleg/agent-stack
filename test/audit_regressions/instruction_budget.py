#!/usr/bin/env python3
"""Synthetic preservation and budget regressions; no host/home data read."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

SCRIPT = Path(__file__).resolve().parents[2] / "plugins/agent-stack/skills/agent-harness/scripts/instruction_budget.py"
spec = importlib.util.spec_from_file_location("instruction_budget", SCRIPT)
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


class InstructionBudget(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="instruction-budget-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_unicode_is_characters_not_bytes_or_tokens(self):
        path = self.put("CLAUDE.md", "Ж😀\n")
        out = budget.measure([path], limit_chars=3)
        self.assertEqual((out["total_characters"], out["total_utf8_bytes"]), (3, 7))
        self.assertEqual(out["status"], "MEASURED")
        self.assertTrue(budget.measure([path], limit_chars=2)["over_budget"])

    def test_relative_imports_are_eager_not_a_saving(self):
        parent = self.put("nested/CLAUDE.md", "@../detail.md\n")
        detail = self.put("detail.md", "Keep an essential requirement.\n")
        before = {p: p.read_bytes() for p in [parent, detail]}
        out = budget.measure([parent], [detail])
        self.assertEqual(out["total_characters"], sum(len(p.read_text()) for p in before))
        self.assertEqual(out["status"], "MEASURED")
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_code_spans_fences_quotes_email_and_escaped_at_do_not_import(self):
        text = '''`@inline.md` and ``@inline2`` and `across
@span.md`
```md
@fenced.md
```
~~~~
@long-fence.md
~~~
@still-fenced.md
~~~~
"@quoted.md" '@also.md' \\@escaped.md test@example.org
@real.md
'''
        self.assertEqual(budget.import_paths(text), ["real.md"])

    def test_escaped_spaces_and_plain_bare_filename(self):
        text = "@Design\\ Docs/policy.md and @README\n"
        self.assertEqual(budget.import_paths(text), ["Design Docs/policy.md", "README"])
        root = self.put("root.md", text)
        detail = self.put("Design Docs/policy.md", "policy")
        readme = self.put("README", "summary")
        self.assertEqual(len(budget.measure([root], [detail, readme])["files"]), 3)

    def test_import_is_not_read_without_explicit_allowlist(self):
        root = self.put("root.md", "@secret.md")
        secret = self.put("secret.md", "PRIVATE_CANARY_DO_NOT_PRINT")
        out = budget.measure([root])
        self.assertEqual(out["status"], "PARTIAL")
        self.assertEqual(out["total_characters"], len(root.read_text()))
        self.assertEqual(out["issues"][0]["kind"], "unlisted_import")
        self.assertNotIn(secret.read_text(), json.dumps(out))

    def test_explicit_missing_import_cannot_pass(self):
        root = self.put("root.md", "@missing.md")
        out = budget.measure([root], [self.root / "missing.md"])
        self.assertEqual(out["status"], "PARTIAL")
        self.assertEqual(out["issues"][0]["reason"], "FileNotFoundError")

    def test_diamond_and_repeated_root_count_unique_paths_once(self):
        root = self.put("root.md", "@a.md @b.md")
        a = self.put("a.md", "@shared.md")
        b = self.put("b.md", "@shared.md")
        shared = self.put("shared.md", "one copy")
        out = budget.measure([root, root], [a, b, shared])
        self.assertEqual(out["status"], "MEASURED")
        self.assertEqual(len(out["files"]), 4)
        self.assertEqual(out["total_characters"], sum(len(p.read_text()) for p in [root, a, b, shared]))
        self.assertEqual(out["duplicate_content"], [[str(a), str(b)]])

    def test_cycle_is_partial_and_terminates(self):
        a = self.put("a.md", "@b.md")
        b = self.put("b.md", "@a.md")
        out = budget.measure([a], [b])
        self.assertEqual(out["status"], "PARTIAL")
        self.assertEqual(out["issues"][0]["kind"], "cycle")
        self.assertEqual(len(out["files"]), 2)

    def test_equal_content_distinct_files_still_cost_twice(self):
        a = self.put("a.md", "same")
        b = self.put("b.md", "same")
        out = budget.measure([a, b])
        self.assertEqual(out["total_characters"], 8)
        self.assertEqual(out["duplicate_content"], [[str(a), str(b)]])

    def test_symlink_alias_is_same_input(self):
        real = self.put("real.md", "same file")
        link = self.root / "link.md"
        link.symlink_to(real)
        out = budget.measure([real, link])
        self.assertEqual(len(out["files"]), 1)

    def test_overlong_chain_is_partial(self):
        chain = [self.put(str(i) + ".md", "@" + str(i + 1) + ".md" if i < 5 else "end") for i in range(6)]
        out = budget.measure([chain[0]], chain[1:])
        self.assertEqual(out["status"], "PARTIAL")
        self.assertEqual(out["issues"][0]["kind"], "import_depth_exceeded")

    def test_invalid_utf8_oversize_directory_and_no_roots(self):
        invalid = self.root / "invalid.md"
        invalid.write_bytes(b"\xffCANARY")
        large = self.put("large.md", "CANARY")
        for out in [budget.measure([invalid]), budget.measure([large], max_file_bytes=3), budget.measure([self.root]), budget.measure([]), budget.measure(["invalid\x00path"])]:
            self.assertEqual(out["status"], "PARTIAL")
            self.assertNotIn("CANARY", json.dumps(out))

    def test_cli_exit_codes_and_input_preservation(self):
        path = self.put("CLAUDE.md", "Keep this rule.\n")
        before = path.read_bytes()
        for extra, code in [([], 0), (["--limit-chars", "1"], 1), ([str(self.root / "missing.md")], 2)]:
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)] + extra, capture_output=True, text=True)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertIn("not a host load receipt", json.loads(result.stdout)["scope"])
        self.assertEqual(path.read_bytes(), before)

    def test_external_imports_not_read_or_executed(self):
        root = self.put("root.md", "@/does/not/exist/secret @$(touch-marker)")
        before = set(self.root.iterdir())
        out = budget.measure([root])
        self.assertEqual(out["status"], "PARTIAL")
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertEqual(len(out["files"]), 1)


if __name__ == "__main__":
    unittest.main()
