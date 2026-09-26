from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPOSITORY_ROOT / "initialize-codex-project" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from render_template import (  # noqa: E402
    RenderError,
    RenderedFile,
    classify_files,
    write_new_files,
    all_placeholder_names,
    build_rendered_files,
    render_project,
    source_root,
)


class RenderTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-template-test-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_finder_metadata_is_ignored_but_hidden_templates_are_rendered(self) -> None:
        templates = self.root / "templates"
        (templates / "docs").mkdir(parents=True)
        for name in (".DS_Store", "docs/.DS_Store"):
            (templates / name).write_bytes(b"\x00\xff{{IGNORED}}")
        (templates / ".editorconfig.template").write_text("root = true\n")
        (templates / "docs/note.template").write_text("{{PROJECT_NAME}}\n")

        self.assertEqual(all_placeholder_names(templates), {"PROJECT_NAME"})
        files = build_rendered_files(templates, {"PROJECT_NAME": "Demo"})
        self.assertEqual(
            {item.target.as_posix(): item.content for item in files},
            {".editorconfig": b"root = true\n", "docs/note": b"Demo\n"},
        )

    def test_other_non_utf8_templates_still_report_an_error(self) -> None:
        (self.root / "broken.template").write_bytes(b"\xff")
        with self.assertRaisesRegex(RenderError, "cannot read UTF-8 template"):
            all_placeholder_names(self.root)

    def write_context(
        self, include=None, preset=None, omit=None, extras=None, filename="context.json"
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
        if preset is not None:
            context["preset"] = preset
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
        context = self.write_context(include=["docs/ADR_TEMPLATE.md"])
        target = self.root / "target"
        result = render_project(context, target, write=False)
        self.assertFalse(target.exists())
        self.assertEqual([status for status, _ in result], ["create", "create"])

    def test_write_maps_skill_and_strips_template_suffix(self) -> None:
        context = self.write_context(preset="core")
        target = self.root / "target"
        render_project(context, target, write=True)
        skill = target / ".agents" / "skills" / "build-and-test" / "SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertNotIn("{{", skill.read_text(encoding="utf-8"))
        self.assertTrue((target / "docs" / "CODEX_TEMPLATE_STATE.json").is_file())

    def test_explicit_core_keeps_coding_rules_log_and_skills(self) -> None:
        context = self.write_context(preset="core")
        target = self.root / "target"
        render_project(context, target, write=True)
        log = target / "docs" / "CODING_RULES_LOG.md"
        self.assertTrue(log.is_file())
        self.assertIn("## Promotion threshold", log.read_text(encoding="utf-8"))
        standards = target / "docs" / "CODING_STANDARDS.md"
        self.assertIn(
            "selected industry language baseline",
            standards.read_text(encoding="utf-8"),
        )
        self.assertFalse((target / "docs" / "ARCHITECTURE.md").exists())
        state = json.loads(
            (target / "docs" / "CODEX_TEMPLATE_STATE.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(
            any(entry["target"] == "docs/CODEX_WORKFLOW.md" for entry in state["files"])
        )
        workflow = (target / "docs" / "CODEX_WORKFLOW.md").read_text(encoding="utf-8")
        self.assertIn("sole canonical definition", workflow)
        for name in ("CODEX_USAGE.md", "TASK_TEMPLATE.md", "CHANGE_IMPACT.md"):
            text = (target / "docs" / name).read_text(encoding="utf-8")
            self.assertIn("docs/CODEX_WORKFLOW.md", text)
            self.assertNotIn("**L1 —", text)
        task = (target / "docs" / "TASK_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertNotIn("## Scope-change triggers", task)

    def test_full_preset_renders_optional_documents(self) -> None:
        context = self.write_context(preset="full")
        target = self.root / "target"
        render_project(context, target, write=True)
        self.assertTrue((target / "docs" / "ARCHITECTURE.md").is_file())
        self.assertTrue((target / "docs" / "AI_PERFORMANCE_BUDGET.md").is_file())

    def test_include_and_preset_are_mutually_exclusive(self) -> None:
        context = self.write_context(
            include=["AGENTS.md.template"], preset="core"
        )
        with self.assertRaisesRegex(RenderError, "mutually exclusive"):
            render_project(context, self.root / "target", write=False)

    def test_unknown_preset_is_rejected(self) -> None:
        context = self.write_context(preset="everything")
        with self.assertRaisesRegex(RenderError, "must be 'minimal', 'core' or 'full'"):
            render_project(context, self.root / "target", write=False)

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
                    "include": ["docs/ADR_TEMPLATE.md"],
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
        context = self.write_context(include=["docs/ADR_TEMPLATE.md"])
        target = self.root / "target"
        first = render_project(context, target, write=True)
        second = render_project(context, target, write=True)
        self.assertEqual([status for status, _ in first], ["create", "create"])
        self.assertEqual([status for status, _ in second], ["unchanged", "unchanged"])

    def test_include_order_does_not_change_generated_state(self) -> None:
        sources = ["docs/ADR_TEMPLATE.md", "docs/LIBRARY_DOCUMENTATION_TEMPLATE.md"]
        first_context = self.write_context(include=sources, filename="first.json")
        second_context = self.write_context(
            include=list(reversed(sources)), filename="second.json"
        )
        target = self.root / "target"
        render_project(first_context, target, write=True)
        second = render_project(second_context, target, write=False)
        self.assertTrue(all(status == "unchanged" for status, _ in second))

    def test_write_failure_removes_created_file(self) -> None:
        context = self.write_context(include=["docs/ADR_TEMPLATE.md"])
        target = self.root / "target"
        with mock.patch("safe_paths.os.fdopen", side_effect=OSError("write failed")):
            with self.assertRaisesRegex(RenderError, "write failed"):
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

    def test_invalid_actual_schema_rejected_by_cli_without_output(self):
        context = self.write_context(preset="core", extras={"PROJECT_MAP_JSON": {"unexpected": True}})
        target = self.root / "target"
        for mode in ("--dry-run", "--write"):
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPTS / "render_template.py"),
                 "--context", str(context), "--target", str(target), mode],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("invalid routing schema", result.stderr)
            self.assertFalse(target.exists())

    def test_focused_render_requires_references_or_existing_files(self):
        context = self.write_context(include=["AGENTS.md.template"])
        target = self.root / "target"
        with self.assertRaisesRegex(RenderError, "missing referenced target"):
            render_project(context, target, write=True)
        self.assertFalse(target.exists())
        # Install a valid baseline, then inspect a focused unchanged file. Its
        # manifest differs, so validate the actual references independently.
        full = self.write_context(filename="full.json")
        render_project(full, target, write=True)
        from render_validation import validate_rendered
        from render_template import build_rendered_files, load_context
        values, include = load_context(context)
        validate_rendered(build_rendered_files(source_root(), values, include), source_root(), target)

    def test_ancestor_swapped_after_classification_cannot_escape(self):
        target = self.root.resolve() / "target"
        outside = self.root.resolve() / "outside"
        (target / ".agents/skills/example").mkdir(parents=True)
        (outside / "skills/example").mkdir(parents=True)
        item = RenderedFile("example", PurePosixPath(".agents/skills/example/SKILL.md"), b"safe")
        classified = classify_files(target, [item])
        (target / ".agents").rename(target / "original")
        (target / ".agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RenderError, "safe write"):
            write_new_files(target, classified)
        self.assertFalse((outside / "skills/example/SKILL.md").exists())

    def test_focused_script_requires_auditor_dependency(self):
        context = self.write_context(include=[
            "skills/build-and-test/scripts/select_checks.py"
        ])
        target = self.root / "target"
        with self.assertRaisesRegex(RenderError, "missing script dependency"):
            render_project(context, target, write=True)
        self.assertFalse(target.exists())

    def test_rollback_preserves_replaced_file_and_reports_incomplete(self):
        import safe_paths
        target = self.root.resolve() / "target"
        target.mkdir()
        real_fdopen = os.fdopen

        def replace_then_fail(descriptor, mode):
            with real_fdopen(descriptor, mode) as handle:
                handle.write(b"original")
            (target / "a.txt").rename(target / "moved.txt")
            (target / "a.txt").write_bytes(b"replacement")
            raise OSError("injected failure")

        with mock.patch.object(safe_paths.os, "fdopen", side_effect=replace_then_fail):
            with self.assertRaisesRegex(RenderError, "incomplete rollback.*replaced object"):
                write_new_files(target, [("create", RenderedFile(
                    "first", PurePosixPath("a.txt"), b"new"
                ))])
        self.assertEqual((target / "a.txt").read_bytes(), b"replacement")
        self.assertEqual((target / "moved.txt").read_bytes(), b"original")

    def test_late_conflict_rolls_back_only_created_files(self):
        target = self.root.resolve() / "target"
        target.mkdir()
        first = RenderedFile("first", PurePosixPath("a.txt"), b"new")
        last = RenderedFile("last", PurePosixPath("z.txt"), b"new")
        classified = classify_files(target, [first, last])
        (target / "z.txt").write_bytes(b"user")
        with self.assertRaises(RenderError):
            write_new_files(target, classified)
        self.assertFalse((target / "a.txt").exists())
        self.assertEqual((target / "z.txt").read_bytes(), b"user")


if __name__ == "__main__":
    unittest.main()
