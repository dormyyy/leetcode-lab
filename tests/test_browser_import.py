import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import leetcode, leetcode_api
from tools.browser_import import import_browser
from test_online import QUESTION

CODE = 'class Solution { public: ListNode* addTwoNumbers(ListNode* first, ListNode*) { return first; } };\n'


class BrowserImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "problems").mkdir()
        shutil.copytree(leetcode.ROOT / "templates", self.root / "templates")
        (self.root / "README.md").write_text(f"My intro\n{leetcode.START}\n{leetcode.END}\nMy footer\n", encoding="utf-8")
        self.incoming = self.root / "browser-sync" / "0002-add-two-numbers"
        self.incoming.mkdir(parents=True)
        (self.incoming / "solution.cpp").write_text(CODE, encoding="utf-8")
        self.fetch = patch.object(leetcode_api, "fetch_question", side_effect=lambda _: copy.deepcopy(QUESTION))
        self.fetch.start()
        self.addCleanup(self.fetch.stop)

    def task(self):
        return self.root / "problems" / "0002-add-two-numbers"

    def test_new_accepted_code_becomes_a_local_task(self):
        self.assertEqual(import_browser(self.root), ["0002-add-two-numbers"])
        folder = self.task()
        self.assertEqual((folder / "accepted/solution.cpp").read_text(encoding="utf-8"), CODE)
        self.assertIn(CODE.strip(), (folder / "solution.cpp").read_text(encoding="utf-8"))
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "solved")
        self.assertEqual(data["status_source"], "browser-extension")
        self.assertEqual(data["browser_sync"]["latest_cpp"], "accepted/solution.cpp")
        leetcode.refresh(self.root, check=True)

    def test_reimport_is_idempotent(self):
        import_browser(self.root)
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(import_browser(self.root), [])
        self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_student_code_and_notes_survive_import(self):
        folder = leetcode.new_online("add-two-numbers", self.root)
        (folder / "solution.cpp").write_text("// My unfinished local approach\n", encoding="utf-8")
        (folder / "README.md").write_text("My personal reasoning", encoding="utf-8")
        import_browser(self.root)
        self.assertEqual((folder / "solution.cpp").read_text(encoding="utf-8"), "// My unfinished local approach\n")
        self.assertEqual((folder / "README.md").read_text(encoding="utf-8"), "My personal reasoning")
        self.assertEqual((folder / "accepted/solution.cpp").read_text(encoding="utf-8"), CODE)

    def test_later_cpp_version_updates_only_an_unmodified_imported_primary(self):
        import_browser(self.root)
        next_code = CODE.replace("return first", "return nullptr")
        (self.incoming / "solution_2.cpp").write_text(next_code, encoding="utf-8")
        import_browser(self.root)
        self.assertIn(next_code.strip(), (self.task() / "solution.cpp").read_text(encoding="utf-8"))
        self.assertEqual((self.task() / "accepted/solution.cpp").read_text(encoding="utf-8"), CODE)
        self.assertEqual((self.task() / "accepted/solution_2.cpp").read_text(encoding="utf-8"), next_code)

    def test_annotated_archive_is_not_overwritten(self):
        import_browser(self.root)
        archived = self.task() / "accepted/solution.cpp"
        archived.write_text("My annotated copy", encoding="utf-8")
        import_browser(self.root)
        self.assertEqual(archived.read_text(encoding="utf-8"), "My annotated copy")
        data = json.loads((self.task() / "problem.json").read_text(encoding="utf-8"))
        saved = self.task() / data["browser_sync"]["files"]["solution.cpp"]["saved_as"]
        self.assertEqual(saved.read_text(encoding="utf-8"), CODE)

    def test_python_is_archived_without_replacing_the_cpp_starter(self):
        (self.incoming / "solution.cpp").unlink()
        python_code = "class Solution: pass\n"
        (self.incoming / "solution.py").write_text(python_code, encoding="utf-8")
        import_browser(self.root)
        self.assertIn("Implement the LeetCode method first", (self.task() / "solution.cpp").read_text(encoding="utf-8"))
        self.assertEqual((self.task() / "accepted/solution.py").read_text(encoding="utf-8"), python_code)

    def test_problem_id_mismatch_does_not_create_a_task(self):
        self.incoming.rename(self.incoming.with_name("0001-add-two-numbers"))
        with self.assertRaises(ValueError):
            import_browser(self.root)
        self.assertEqual(list((self.root / "problems").iterdir()), [])

    def test_metadata_only_upload_does_not_claim_a_solved_problem(self):
        (self.incoming / "solution.cpp").unlink()
        (self.incoming / "README.md").write_text("description only", encoding="utf-8")
        self.assertEqual(import_browser(self.root), [])
        self.assertEqual(list((self.root / "problems").iterdir()), [])

    def test_extension_topic_links_use_the_actual_main_branch(self):
        readme = self.root / "README.md"
        text = readme.read_text(encoding="utf-8") + "\n[Archive](https://github.com/dormyyy/leetcode-lab/tree/master/browser-sync/0002-add-two-numbers)\n"
        readme.write_text(text, encoding="utf-8")
        import_browser(self.root)
        updated = readme.read_text(encoding="utf-8")
        self.assertIn("tree/main/browser-sync/0002-add-two-numbers", updated)
        self.assertIn("My intro", updated)
        self.assertIn("My footer", updated)


if __name__ == "__main__":
    unittest.main()
