import argparse
from datetime import date
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import leetcode


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "problems").mkdir()
        shutil.copytree(leetcode.ROOT / "templates", self.root / "templates")
        (self.root / "README.md").write_text(
            f"My intro\n{leetcode.START}\n{leetcode.END}\nMy footer\n", encoding="utf-8"
        )

    def new(self, problem_id=1, slug="two-sum", title="Two Sum", difficulty="Easy"):
        return leetcode.new_problem(
            argparse.Namespace(id=problem_id, slug=slug, title=title, difficulty=difficulty, topics=["array"]),
            self.root,
        )

    def test_empty_journal_has_zero_solved_and_preserves_manual_text(self):
        leetcode.refresh(self.root)
        leetcode.refresh(self.root, check=True)
        text = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("**0 solved**", text)
        self.assertTrue(text.startswith("My intro\n"))
        self.assertTrue(text.endswith("My footer\n"))

    def test_new_problem_is_in_progress_with_all_files(self):
        folder = self.new()
        self.assertEqual(folder.name, "0001-two-sum")
        self.assertEqual({path.name for path in folder.iterdir()}, {"README.md", "problem.json", "solution.cpp", "main.cpp"})
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "in-progress")
        self.assertIsNone(data["solved_on"])
        text = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("**0 solved** · **1 in progress**", text)
        self.assertIn("problems/0001-two-sum/", text)

    def test_duplicate_id_does_not_overwrite_work(self):
        folder = self.new()
        (folder / "solution.cpp").write_text("my own code", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.new(slug="another-slug")
        self.assertEqual((folder / "solution.cpp").read_text(encoding="utf-8"), "my own code")
        self.assertFalse((self.root / "problems" / "0001-another-slug").exists())

    def test_done_updates_counts_and_keeps_original_date(self):
        folder = self.new()
        leetcode.mark_done(1, self.root)
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        self.assertEqual(data["solved_on"], date.today().isoformat())
        data["solved_on"] = "2026-01-02"
        (folder / "problem.json").write_text(json.dumps(data), encoding="utf-8")
        leetcode.mark_done(1, self.root)
        self.assertEqual(json.loads((folder / "problem.json").read_text(encoding="utf-8"))["solved_on"], "2026-01-02")
        text = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("**1 solved** · **0 in progress**", text)
        self.assertIn("| 1 | 0 | 0 |", text)

    def test_missing_problem_cannot_be_marked_done(self):
        with self.assertRaises(ValueError):
            leetcode.mark_done(999, self.root)

    def test_invalid_slug_cannot_escape_problem_directory(self):
        for slug in ("../outside", "..", "C:\\outside", "Uppercase", "two--sum"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                self.new(slug=slug)
        self.assertEqual(list((self.root / "problems").iterdir()), [])

    def test_check_detects_stale_index(self):
        self.new()
        readme = self.root / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("Two Sum", "Old title"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outdated"):
            leetcode.refresh(self.root, check=True)

    def test_manual_problem_without_metadata_is_reported(self):
        (self.root / "problems" / "0002-add-two-numbers").mkdir()
        with self.assertRaisesRegex(ValueError, "0002-add-two-numbers"):
            leetcode.refresh(self.root)

    def test_solved_problem_needs_valid_date(self):
        folder = self.new()
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        data["status"] = "solved"
        for invalid_date in (None, "2026-02-30", "2026-1-1"):
            with self.subTest(date=invalid_date), self.assertRaises(ValueError):
                leetcode.validate({**data, "solved_on": invalid_date})

    def test_numeric_sort_and_markdown_table_escaping(self):
        self.new(10, "regular-expression-matching", "Regex | [matching]", "Hard")
        self.new(2, "add-two-numbers", "Add Two Numbers", "Medium")
        text = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertLess(text.index("| 2 |"), text.index("| 10 |"))
        self.assertIn("Regex \\| \\[matching\\]", text)


if __name__ == "__main__":
    unittest.main()
