"""Exercise selectable workflows as rendered target repositories."""

from dataclasses import replace
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "initialize-codex-project/scripts"
sys.path.insert(0, str(SCRIPTS))
from render_template import (MINIMAL_SOURCES, CORE_SOURCES, render_project, source_root,
                             placeholder_names, build_rendered_files, RenderError)
from validate_templates import sample_values, validate_default_guidance_size


class WorkflowContractsTests(unittest.TestCase):
    def test_all_presets_render_without_required_missing_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for preset, expected in (("minimal", len(MINIMAL_SOURCES)), ("core", len(CORE_SOURCES)), ("full", 24)):
                context = base / (preset + ".json")
                context.write_text(json.dumps({"values": sample_values(source_root()), "preset": preset}))
                target = base / preset
                rendered = render_project(context, target, write=True)
                self.assertEqual(len(rendered), expected + 1)
                self.assertEqual((target / "docs/TASK_TEMPLATE.md").exists(), preset != "minimal")
                workflow = (target / "docs/CODEX_WORKFLOW.md").read_text()
                self.assertIn("conversation by default", workflow)
                self.assertIn("do not ask again for the same authorization", workflow)
                self.assertFalse((target / "docs/tasks").exists())
                if preset == "minimal":
                    self.assertFalse((target / ".agents").exists())
                    continue
                for script, arguments in (
                    ("context-discovery/scripts/build_context_pack.py", []),
                    ("build-and-test/scripts/select_checks.py", ["--changed-file", "AGENTS.md"]),
                    ("context-discovery/scripts/audit_evidence.py", []),
                ):
                    result = subprocess.run(
                        [sys.executable, "-B", str(target / ".agents/skills" / script),
                         "--project-root", str(target), *arguments],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIsInstance(json.loads(result.stdout), dict)

    def test_default_needs_only_selected_fields_and_matches_explicit_minimal(self):
        required = set().union(*(
            placeholder_names((source_root() / name).read_text())
            for name in MINIMAL_SOURCES
        ))
        values = {key: value for key, value in sample_values(source_root()).items()
                  if key in required}
        self.assertNotIn("PROJECT_MAP_JSON", values)
        self.assertNotIn("VERIFICATION_ROUTES_JSON", values)
        expected = {"AGENTS.md", "docs/CODEX_WORKFLOW.md",
                    "docs/CODING_STANDARDS.md", "docs/VERIFICATION.md",
                    "docs/CODEX_TEMPLATE_STATE.json"}
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            outputs = []
            for index, selection in enumerate(({}, {"preset": "minimal"})):
                context = base / f"context-{index}.json"
                context.write_text(json.dumps({"values": values, **selection}))
                target = base / f"target-{index}"
                render_project(context, target, write=True)
                output = {p.relative_to(target).as_posix(): p.read_bytes()
                          for p in target.rglob("*") if p.is_file()}
                self.assertEqual(set(output), expected)
                outputs.append(output)
            self.assertEqual(outputs[0], outputs[1])

    def test_known_unused_legacy_values_remain_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            context = base / "context.json"
            context.write_text(json.dumps({"values": sample_values(source_root())}))
            result = render_project(context, base / "target", write=False)
            self.assertEqual(len(result), 5)
            self.assertFalse((base / "target").exists())

    def test_fixed_sample_size_boundaries_use_utf8_bytes_and_lines(self):
        files = build_rendered_files(source_root(), sample_values(source_root()), MINIMAL_SOURCES)
        metrics = validate_default_guidance_size(files)
        self.assertLessEqual(metrics["entrypoint_lines"], 60)
        self.assertLessEqual(metrics["guidance_bytes"], 10000)
        # Fill to the exact byte boundary with multibyte text, then cross it.
        index = next(i for i, item in enumerate(files) if item.target.name == "VERIFICATION.md")
        room = 10000 - metrics["guidance_bytes"]
        padding = "中".encode("utf-8") * (room // 3) + b"x" * (room % 3)
        files[index] = replace(files[index], content=files[index].content + padding)
        self.assertEqual(validate_default_guidance_size(files)["guidance_bytes"], 10000)
        files[index] = replace(files[index], content=files[index].content + b"x")
        with self.assertRaisesRegex(RenderError, "exceeds 10000 bytes"):
            validate_default_guidance_size(files)
        files = build_rendered_files(source_root(), sample_values(source_root()), MINIMAL_SOURCES)
        index = next(i for i, item in enumerate(files) if item.target.name == "AGENTS.md")
        files[index] = replace(files[index], content=files[index].content +
                               b"\n" * (60 - metrics["entrypoint_lines"]))
        self.assertEqual(validate_default_guidance_size(files)["entrypoint_lines"], 60)
        files[index] = replace(files[index], content=files[index].content + b"\n")
        with self.assertRaisesRegex(RenderError, "exceeds 60 lines"):
            validate_default_guidance_size(files)

    def test_real_target_content_is_not_truncated_by_sample_budget(self):
        values = sample_values(source_root())
        evidence = "Verified target constraint.\n" * 400
        values["ARCHITECTURE_SUMMARY"] = evidence
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            context = base / "context.json"
            context.write_text(json.dumps({"values": values}))
            target = base / "target"
            render_project(context, target, write=True)
            self.assertIn(evidence, (target / "AGENTS.md").read_text())
            self.assertEqual(sum(p.is_file() for p in target.rglob("*")), 5)

    def test_recording_requires_confirmation_at_both_rule_entrypoints(self):
        standards = (source_root() / "docs/CODING_STANDARDS.md.template").read_text()
        rules = (source_root() / "docs/CODING_RULES_LOG.md.template").read_text()
        self.assertIn("wait for confirmation before recording", standards)
        self.assertIn("Wait for explicit confirmation before recording", rules)


if __name__ == "__main__":
    unittest.main()
