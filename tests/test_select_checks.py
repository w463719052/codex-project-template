from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPOSITORY_ROOT / "tests/fixtures/ai-routing"
SCRIPT = (
    REPOSITORY_ROOT
    / "initialize-codex-project/assets/project-template/skills/build-and-test/scripts/select_checks.py"
)
SPEC = importlib.util.spec_from_file_location("select_checks_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SelectChecksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.routes = json.loads(
            (FIXTURE / "verification-routes.json").read_text(encoding="utf-8")
        )

    def test_selects_focused_and_required_checks(self) -> None:
        result = MODULE.select_checks(self.routes, ["src/core.py"])
        self.assertEqual(result["matched_routes"], ["core"])
        self.assertEqual(
            [item["id"] for item in result["commands"]],
            ["core-tests", "diff-check"],
        )
        self.assertFalse(result["execution_authorized"])

    def test_unmatched_path_uses_fallback(self) -> None:
        result = MODULE.select_checks(self.routes, ["README.md"])
        self.assertEqual(result["unmatched_paths"], ["README.md"])
        self.assertEqual([item["id"] for item in result["commands"]], ["diff-check"])

    def test_routes_are_not_mutated(self) -> None:
        before = copy.deepcopy(self.routes)
        MODULE.select_checks(self.routes, ["docs/architecture.md"])
        self.assertEqual(self.routes, before)

    def test_empty_change_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(MODULE.CheckSelectionError, "at least one"):
            MODULE.select_checks(self.routes, [])

    def test_unsafe_changed_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(MODULE.CheckSelectionError, "unsafe changed file"):
            MODULE.select_checks(self.routes, ["../outside.py"])

    def test_unknown_command_reference_is_rejected(self) -> None:
        routes = copy.deepcopy(self.routes)
        routes["routes"][0]["focused_check_ids"] = ["missing-command"]
        with self.assertRaisesRegex(MODULE.CheckSelectionError, "unknown commands"):
            MODULE.select_checks(routes, ["src/core.py"])


if __name__ == "__main__":
    unittest.main()
