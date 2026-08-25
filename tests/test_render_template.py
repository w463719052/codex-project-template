from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPOSITORY_ROOT / "initialize-codex-project" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from render_template import (  # noqa: E402
    RenderError,
    all_placeholder_names,
    render_project,
    source_root,
)


class RenderTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-template-test-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_context(
        self, include=None, omit=None, extras=None, filename="context.json"
    ) -> Path:
        values = {}
        for name in all_placeholder_names(source_root()):
            if name == "PROJECT_MAP_JSON":
                values[name] = self.project_map()
            elif name == "VERIFICATION_ROUTES_JSON":
                values[name] = self.verification_routes()
            else:
                values[name] = (
                    "Test Project"
                    if name == "PROJECT_NAME"
                    else f"Evidence for {name}."
                )
        if omit:
            values.pop(omit)
        if extras:
            values.update(extras)
        context = {"values": values}
        if include is not None:
            context["include"] = include
        path = self.root / filename
        path.write_text(json.dumps(context), encoding="utf-8")
        return path

    @staticmethod
    def project_map():
        return {
            "schema_version": 1,
            "project_name": "Test Project",
            "budgets": {
                "max_initial_files": 3,
                "max_initial_bytes": 4096,
                "max_expansion_rounds": 1,
            },
            "excluded_paths": [".git/**"],
            "modules": [
                {
                    "id": "governance",
                    "paths": ["AGENTS.md", "docs/**"],
                    "responsibility": "Repository governance.",
                    "entrypoints": ["AGENTS.md"],
                    "public_contracts": [],
                    "dependencies": [],
                    "consumers": [],
                    "tests": [],
                    "authority_docs": ["AGENTS.md"],
                    "generated_paths": [],
                }
            ],
            "context_routes": [],
            "documentation_gaps": [],
        }

    @staticmethod
    def verification_routes():
        return {
            "schema_version": 1,
            "commands": [
                {
                    "id": "diff-check",
                    "command": "git diff --check",
                    "kind": "diff",
                    "evidence": "docs/VERIFICATION.md#diff-checks",
                    "mutates": False,
                }
            ],
            "routes": [],
            "fallback_check_ids": ["diff-check"],
            "documentation_gaps": [],
        }

    def test_dry_run_does_not_create_target(self) -> None:
        context = self.write_context(include=["AGENTS.md.template"])
        target = self.root / "target"
        result = render_project(context, target, write=False)
        self.assertFalse(target.exists())
        self.assertEqual([status for status, _ in result], ["create", "create"])

    def test_write_maps_skill_and_strips_template_suffix(self) -> None:
        context = self.write_context(
            include=["skills/build-and-test/SKILL.md.template"]
        )
        target = self.root / "target"
        render_project(context, target, write=True)
        skill = target / ".agents" / "skills" / "build-and-test" / "SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertNotIn("{{", skill.read_text(encoding="utf-8"))
        self.assertTrue((target / "docs" / "CODEX_TEMPLATE_STATE.json").is_file())

    def test_default_render_includes_coding_rules_log(self) -> None:
        context = self.write_context()
        target = self.root / "target"
        render_project(context, target, write=True)
        log = target / "docs" / "CODING_RULES_LOG.md"
        self.assertTrue(log.is_file())
        self.assertIn("## Promotion threshold", log.read_text(encoding="utf-8"))
        standards = target / "docs" / "CODING_STANDARDS.md"
        self.assertIn(
            "selected industry language baseline first while treating",
            standards.read_text(encoding="utf-8"),
        )

    def test_missing_placeholder_is_rejected(self) -> None:
        context = self.write_context(
            include=["AGENTS.md.template"], omit="PROJECT_NAME"
        )
        with self.assertRaisesRegex(RenderError, "missing placeholder values"):
            render_project(context, self.root / "target", write=False)

    def test_unknown_context_value_is_rejected(self) -> None:
        context = self.write_context(
            include=["AGENTS.md.template"], extras={"TYPO_VALUE": "unexpected"}
        )
        with self.assertRaisesRegex(RenderError, "unknown placeholder values"):
            render_project(context, self.root / "target", write=False)

    def test_blank_context_value_is_rejected(self) -> None:
        context = self.write_context(extras={"PROJECT_NAME": "   "})
        with self.assertRaisesRegex(RenderError, "must not be blank"):
            render_project(context, self.root / "target", write=False)

    def test_blank_structured_context_value_is_rejected(self) -> None:
        context = self.write_context(extras={"PROJECT_MAP_JSON": {}})
        with self.assertRaisesRegex(RenderError, "non-empty object or array"):
            render_project(context, self.root / "target", write=False)

    def test_structured_placeholders_render_as_valid_json(self) -> None:
        context = self.write_context(
            include=[
                ".agents/ai/project-map.json.template",
                ".agents/ai/verification-routes.json.template",
            ]
        )
        target = self.root / "target"
        render_project(context, target, write=True)
        project_map = json.loads(
            (target / ".agents/ai/project-map.json").read_text(encoding="utf-8")
        )
        routes = json.loads(
            (target / ".agents/ai/verification-routes.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(project_map["project_name"], "Test Project")
        self.assertFalse(routes["commands"][0]["mutates"])

    def test_old_focused_context_does_not_require_new_values(self) -> None:
        context = self.root / "old-context.json"
        context.write_text(
            json.dumps(
                {
                    "values": {},
                    "include": ["docs/CODEX_WORKFLOW.md"],
                }
            ),
            encoding="utf-8",
        )
        result = render_project(context, self.root / "target", write=False)
        self.assertEqual([status for status, _ in result], ["create", "create"])

    def test_included_source_cannot_escape_template_root(self) -> None:
        context = self.write_context(include=["../AGENTS.md"])
        with self.assertRaisesRegex(RenderError, "unsafe included source path"):
            render_project(context, self.root / "target", write=False)

    def test_conflict_prevents_partial_write(self) -> None:
        context = self.write_context(
            include=["AGENTS.md.template", "docs/CODEX_WORKFLOW.md"]
        )
        target = self.root / "target"
        target.mkdir()
        (target / "AGENTS.md").write_text("existing\n", encoding="utf-8")
        with self.assertRaisesRegex(RenderError, "refusing to overwrite"):
            render_project(context, target, write=True)
        self.assertFalse((target / "docs" / "CODEX_WORKFLOW.md").exists())
        self.assertEqual(
            (target / "AGENTS.md").read_text(encoding="utf-8"), "existing\n"
        )

    def test_repeated_identical_write_is_stable(self) -> None:
        context = self.write_context(include=["docs/CODEX_WORKFLOW.md"])
        target = self.root / "target"
        first = render_project(context, target, write=True)
        second = render_project(context, target, write=True)
        self.assertEqual([status for status, _ in first], ["create", "create"])
        self.assertEqual([status for status, _ in second], ["unchanged", "unchanged"])

    def test_include_order_does_not_change_generated_state(self) -> None:
        sources = ["AGENTS.md.template", "docs/CODEX_WORKFLOW.md"]
        first_context = self.write_context(include=sources, filename="first.json")
        second_context = self.write_context(
            include=list(reversed(sources)), filename="second.json"
        )
        target = self.root / "target"
        render_project(first_context, target, write=True)
        second = render_project(second_context, target, write=False)
        self.assertTrue(all(status == "unchanged" for status, _ in second))

    def test_write_failure_removes_created_file(self) -> None:
        context = self.write_context(include=["docs/CODEX_WORKFLOW.md"])
        target = self.root / "target"
        with mock.patch("render_template.os.fdopen", side_effect=OSError("write failed")):
            with self.assertRaisesRegex(OSError, "write failed"):
                render_project(context, target, write=True)
        self.assertFalse((target / "docs" / "CODEX_WORKFLOW.md").exists())
        self.assertFalse(target.exists())

    def test_symlinked_target_path_is_rejected(self) -> None:
        context = self.write_context(include=["docs/CODEX_WORKFLOW.md"])
        target = self.root / "target"
        outside = self.root / "outside"
        target.mkdir()
        outside.mkdir()
        try:
            (target / "docs").symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symbolic links unavailable: {exc}")
        with self.assertRaisesRegex(RenderError, "symbolic link"):
            render_project(context, target, write=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_target_root_is_rejected(self) -> None:
        context = self.write_context(include=["docs/CODEX_WORKFLOW.md"])
        outside = self.root / "outside"
        target = self.root / "target"
        outside.mkdir()
        try:
            target.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symbolic links unavailable: {exc}")
        with self.assertRaisesRegex(RenderError, "target root.*symbolic link"):
            render_project(context, target, write=True)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
