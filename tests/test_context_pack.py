from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPOSITORY_ROOT / "tests/fixtures/ai-routing"
SCRIPT = (
    REPOSITORY_ROOT
    / "initialize-codex-project/assets/project-template/skills/context-discovery/scripts/build_context_pack.py"
)
SPEC = importlib.util.spec_from_file_location("context_pack_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ContextPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_map = json.loads(
            (FIXTURE / "project-map.json").read_text(encoding="utf-8")
        )
        self.project_root = FIXTURE / "repo"

    def test_task_route_selects_bounded_context(self) -> None:
        result = MODULE.build_context_pack(
            self.project_root, self.project_map, task_type="feature"
        )
        self.assertEqual(result["selected_modules"], ["core"])
        self.assertEqual(result["selected_routes"], ["core-change"])
        self.assertEqual(
            [item["path"] for item in result["files"]],
            ["docs/architecture.md", "tests/test_core.py", "src/core.py"],
        )
        self.assertLessEqual(result["total_files"], result["budget"]["max_files"])
        self.assertLessEqual(result["total_bytes"], result["budget"]["max_bytes"])

    def test_budget_omits_files_without_reading_extra_content(self) -> None:
        result = MODULE.build_context_pack(
            self.project_root,
            self.project_map,
            task_type="feature",
            max_files=1,
        )
        self.assertEqual(result["total_files"], 1)
        self.assertTrue(any(item["reason"] == "file-budget" for item in result["omitted"]))

    def test_input_map_is_not_mutated(self) -> None:
        before = copy.deepcopy(self.project_map)
        MODULE.build_context_pack(
            self.project_root, self.project_map, changed_files=["src/core.py"]
        )
        self.assertEqual(self.project_map, before)

    def test_unsafe_changed_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(MODULE.ContextPackError, "unsafe changed file"):
            MODULE.build_context_pack(
                self.project_root, self.project_map, changed_files=["../secret"]
            )

    def test_zero_budget_is_rejected_instead_of_using_default(self) -> None:
        with self.assertRaisesRegex(MODULE.ContextPackError, "positive integer"):
            MODULE.build_context_pack(
                self.project_root, self.project_map, task_type="feature", max_files=0
            )

    def test_symlink_candidate_is_reported_and_omitted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="context-pack-symlink-") as temp:
            root = Path(temp)
            (root / "src").mkdir()
            try:
                (root / "src/core.py").symlink_to(self.project_root / "src/core.py")
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symbolic links unavailable: {exc}")
            result = MODULE.build_context_pack(
                root, self.project_map, changed_files=["src/core.py"]
            )
            self.assertEqual(result["files"], [])
            self.assertTrue(
                any("symbolic-link" in item["reason"] for item in result["omitted"])
            )

    def test_route_membership_does_not_depend_on_array_order(self):
        extra = copy.deepcopy(self.project_map["context_routes"][0])
        extra.update(id="other-core", task_types=["other"])
        self.project_map["context_routes"].insert(0, extra)
        first = MODULE.build_context_pack(self.project_root, self.project_map, task_type="feature")
        self.project_map["context_routes"].reverse()
        second = MODULE.build_context_pack(self.project_root, self.project_map, task_type="feature")
        self.assertEqual(set(first["selected_routes"]), set(second["selected_routes"]))
        self.assertEqual(set(first["selected_routes"]), {"core-change", "other-core"})

    def test_explicit_scope_prevents_generic_task_expansion(self):
        data = json.loads((FIXTURE / "multi-module-map.json").read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "AGENTS.md").write_text("rules")
            for name in ("alpha", "beta"):
                (root / name).mkdir()
                (root / name / "main.py").write_text("source")
                (root / name / "test_main.py").write_text("test")
            result = MODULE.build_context_pack(root, data, changed_files=["alpha/main.py"], task_type="fix")
            self.assertEqual(result["selected_modules"], ["alpha"])
            self.assertEqual([item["path"] for item in result["files"]], ["alpha/main.py", "AGENTS.md", "alpha/test_main.py"])
            self.assertIn({"path": "beta/main.py", "reason": "outside-selected-modules"}, result["omitted"])
            self.assertFalse(result["scope_required"])
            broad = MODULE.build_context_pack(root, data, task_type="fix")
            self.assertTrue(broad["scope_required"])

    def test_optional_provenance_is_validated(self):
        self.project_map["modules"][0]["provenance"] = [{"path": "../outside"}]
        with self.assertRaisesRegex(MODULE.ContextPackError, "unsafe provenance"):
            MODULE.build_context_pack(self.project_root, self.project_map, task_type="fix")


if __name__ == "__main__":
    unittest.main()
