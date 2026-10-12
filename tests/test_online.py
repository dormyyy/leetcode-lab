import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import cpp_runner, leetcode, leetcode_api

SIGNATURE = {
    "name": "addTwoNumbers",
    "params": [{"name": "l1", "type": "ListNode"}, {"name": "l2", "type": "ListNode"}],
    "return": {"type": "ListNode"},
}
QUESTION = {
    "questionFrontendId": "2", "titleSlug": "add-two-numbers", "title": "Add Two Numbers", "difficulty": "Medium",
    "topicTags": [{"slug": "linked-list"}], "signature": SIGNATURE,
    "exampleTestcases": "[2,4,3]\n[5,6,4]\n[0]\n[0]",
    "cpp": "class Solution { public: ListNode* addTwoNumbers(ListNode* l1, ListNode* l2) {\n\n} };",
}
PROFILE = {
    "username": "dormyyy", "solved": {"All": 8, "Easy": 8, "Medium": 0, "Hard": 0}, "recent_accepted": [],
}


class OnlineJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "problems").mkdir()
        shutil.copytree(leetcode.ROOT / "templates", self.root / "templates")
        (self.root / "README.md").write_text(f"Intro\n{leetcode.START}\n{leetcode.END}\nFooter\n", encoding="utf-8")
        (self.root / "leetcode.json").write_text('{"username":"dormyyy"}', encoding="utf-8")

    def new(self):
        with patch.object(leetcode_api, "fetch_question", return_value=copy.deepcopy(QUESTION)):
            return leetcode.new_online("add-two-numbers", self.root)

    def sync(self, profile=PROFILE):
        with patch.object(leetcode_api, "fetch_profile", return_value=copy.deepcopy(profile)):
            return leetcode.sync_profile(self.root)

    def test_slug_download_creates_real_signature_and_list_calls(self):
        folder = self.new()
        self.assertEqual(folder.name, "0002-add-two-numbers")
        self.assertIn("ListNode* addTwoNumbers", (folder / "solution.cpp").read_text(encoding="utf-8"))
        self.assertIn("throw std::logic_error", (folder / "solution.cpp").read_text(encoding="utf-8"))
        self.assertIn("lc::list({2, 4, 3})", (folder / "cases.generated.hpp").read_text(encoding="utf-8"))
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        self.assertEqual(data["runner"], "automatic")
        self.assertEqual(data["status"], "in-progress")

    def test_existing_problem_is_not_fetched_or_overwritten(self):
        folder = self.new()
        (folder / "solution.cpp").write_text("user code", encoding="utf-8")
        with patch.object(leetcode_api, "fetch_question") as fetch, self.assertRaises(ValueError):
            leetcode.new_online("add-two-numbers", self.root)
        fetch.assert_not_called()
        self.assertEqual((folder / "solution.cpp").read_text(encoding="utf-8"), "user code")

    def test_account_solved_and_repository_solved_are_separate(self):
        self.new()
        self.sync()
        text = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("**8 solved on LeetCode**", text)
        self.assertIn("**0 solved** · **1 in progress**", text)
        leetcode.refresh(self.root, check=True)

    def test_unchanged_sync_does_not_change_any_file(self):
        self.new()
        self.sync()
        paths = [self.root / "README.md", self.root / "progress/leetcode.json"]
        previous = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
        self.sync()
        self.assertEqual(previous, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths})

    def test_recent_accepted_marks_only_the_matching_problem(self):
        folder = self.new()
        (folder / "solution.cpp").write_text("// my saved solution", encoding="utf-8")
        profile = copy.deepcopy(PROFILE)
        profile["solved"] = {"All": 9, "Easy": 8, "Medium": 1, "Hard": 0}
        profile["recent_accepted"] = [{"id": "123", "titleSlug": "add-two-numbers", "timestamp": "1760000000"}]
        self.sync(profile)
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "solved")
        self.assertEqual(data["accepted_submission_id"], "123")
        self.assertIn("**1 solved**", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_accepted_on_website_does_not_mark_an_empty_local_starter_solved(self):
        folder = self.new()
        profile = copy.deepcopy(PROFILE)
        profile["solved"] = {"All": 9, "Easy": 8, "Medium": 1, "Hard": 0}
        profile["recent_accepted"] = [{"id": "123", "titleSlug": "add-two-numbers", "timestamp": "1760000000"}]
        self.sync(profile)
        data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "in-progress")
        self.assertIn("**9 solved on LeetCode**", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_network_failure_keeps_cache_and_problem_status(self):
        folder = self.new()
        self.sync()
        paths = [self.root / "README.md", self.root / "progress/leetcode.json", folder / "problem.json"]
        previous = {path: path.read_bytes() for path in paths}
        with patch.object(leetcode_api, "fetch_profile", side_effect=ValueError("unavailable")), self.assertRaises(ValueError):
            leetcode.sync_profile(self.root)
        self.assertEqual(previous, {path: path.read_bytes() for path in paths})

    def test_driver_regeneration_keeps_solution_and_manual_runner(self):
        folder = self.new()
        (folder / "main.cpp").write_text("custom main", encoding="utf-8")
        before = (folder / "solution.cpp").read_bytes()
        cases = [{"inputs": [[1], [2]], "expected": [3]}]
        (folder / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        leetcode.generate_driver("add-two-numbers", self.root)
        self.assertEqual((folder / "solution.cpp").read_bytes(), before)
        self.assertEqual((folder / "main.cpp").read_text(encoding="utf-8"), "custom main")
        self.assertIn("lc::check", (folder / "cases.generated.hpp").read_text(encoding="utf-8"))

    def test_manual_judge_uses_explicit_fallback(self):
        content, reason = cpp_runner.make_driver({"manual": True}, [{"inputs": []}])
        self.assertIsNotNone(reason)
        self.assertIn("custom judge", content)
        self.assertNotIn("solution.", content)

    def test_parameter_count_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            cpp_runner.render_driver(SIGNATURE, [{"inputs": [[1]]}])

    def test_scalar_array_matrix_tree_and_character_conversion(self):
        self.assertEqual(cpp_runner.cpp_value([[1, 2], []], "integer[][]"), "std::vector<std::vector<int>>{std::vector<int>{1, 2}, std::vector<int>{}}")
        self.assertEqual(cpp_runner.cpp_value([1, None, 2], "TreeNode"), "lc::tree({1, std::nullopt, 2})")
        self.assertEqual(cpp_runner.cpp_value([], "ListNode"), "lc::list({})")
        self.assertEqual(cpp_runner.cpp_value("'", "character"), "'\\''")
        self.assertEqual(cpp_runner.cpp_value(False, "boolean"), "false")
        with self.assertRaises(ValueError):
            cpp_runner.cpp_value(True, "integer")

    def test_cpp_string_does_not_interpret_control_characters_as_code(self):
        literal = cpp_runner.cpp_string('"; std::abort(); //\n\x01A')
        self.assertTrue(literal.startswith('"\\"'))
        self.assertIn("\\012\\001A", literal)

    def test_starter_comments_and_type_definitions_are_not_changed(self):
        comment = "/* struct ListNode { ListNode() {} }; */"
        source = cpp_runner.solution_source(comment + "\nclass Solution { public: int method() {} };")
        self.assertIn(comment, source)
        self.assertEqual(source.count("throw std::logic_error"), 1)

    def test_void_method_observes_the_output_parameter(self):
        signature = {"name": "reverseString", "params": [{"name": "s", "type": "character[]"}], "return": {"type": "void"}, "output": {"paramindex": 0}}
        driver = cpp_runner.render_driver(signature, [{"inputs": [["h", "i"]], "expected": ["i", "h"]}])
        self.assertIn("solution.reverseString(input_0);", driver)
        self.assertIn("lc::check(input_0", driver)

    def test_design_problem_generates_a_sequence_of_method_calls(self):
        signature = {"systemdesign": True, "classname": "MinStack", "constructor": {"params": []}, "methods": [{"name": "push", "params": [{"name": "x", "type": "integer"}], "return": {"type": "void"}}, {"name": "top", "params": [], "return": {"type": "integer"}}]}
        driver = cpp_runner.render_driver(signature, [{"inputs": [["MinStack", "push", "top"], [[], [4], []]], "expected": [None, None, 4]}])
        self.assertIn("MinStack solution{};", driver)
        self.assertIn("solution.push(arg_1_0)", driver)
        self.assertIn("solution.top()", driver)


class PublicApiTests(unittest.TestCase):
    def test_invalid_profile_does_not_turn_into_zero_solved(self):
        with patch.object(leetcode_api, "graphql", return_value={"matchedUser": None}), self.assertRaises(ValueError):
            leetcode_api.fetch_profile("missing")

    def test_inconsistent_counter_response_is_rejected(self):
        data = {"matchedUser": {"username": "dormyyy", "submitStatsGlobal": {"acSubmissionNum": [{"difficulty": name, "count": count} for name, count in {"All": 8, "Easy": 0, "Medium": 0, "Hard": 0}.items()]}}, "recentAcSubmissionList": []}
        with patch.object(leetcode_api, "graphql", return_value=data), self.assertRaises(ValueError):
            leetcode_api.fetch_profile("dormyyy")


if __name__ == "__main__":
    unittest.main()
