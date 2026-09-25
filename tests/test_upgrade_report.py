import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "initialize-codex-project/scripts"
sys.path.insert(0, str(SCRIPTS))
from report_upgrade import report_upgrade, UpgradeError
from render_template import render_project, STATE_PATH


class UpgradeReportTests(unittest.TestCase):
    def test_drift_keeps_target_edits_and_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            context = base / "context.json"
            context.write_text(json.dumps({"values": {}, "include": ["docs/ADR_TEMPLATE.md"]}))
            target = base / "target"
            render_project(context, target, True)
            output = target / "docs/ADR_TEMPLATE.md"
            output.write_text("project customization")
            extra = target / "custom-skill.md"
            extra.write_text("unmanaged")
            before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            result = report_upgrade(target)
            self.assertEqual(result["files"][0]["status"], "target-modified")
            self.assertEqual(result["mode"], "drift-only")
            self.assertEqual(before, {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()})
            result = report_upgrade(target, context)
            self.assertEqual(result["files"][0]["status"], "target-modified")

    def test_candidate_comparison_distinguishes_both_and_template_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            context = base / "context.json"
            context.write_text(json.dumps({"values": {}, "include": ["docs/ADR_TEMPLATE.md"]}))
            target = base / "target"
            render_project(context, target, True)
            state_path = target / STATE_PATH
            state = json.loads(state_path.read_text())
            state["files"][0]["sha256"] = hashlib.sha256(b"old version").hexdigest()
            state_path.write_text(json.dumps(state))
            (target / "docs/ADR_TEMPLATE.md").write_bytes(b"old version")
            self.assertEqual(report_upgrade(target, context)["files"][0]["status"], "template-changed")
            (target / "docs/ADR_TEMPLATE.md").write_bytes(b"custom")
            self.assertEqual(report_upgrade(target, context)["files"][0]["status"], "both-changed")

    def test_smaller_candidate_does_not_remove_existing_extensions(self):
        from validate_templates import sample_values
        from render_template import source_root, RenderError
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            context = base / "context.json"
            values = sample_values(source_root())
            context.write_text(json.dumps({"values": values, "preset": "core"}))
            target = base / "target"
            render_project(context, target, True)
            before = {p.relative_to(target).as_posix(): p.read_bytes()
                      for p in target.rglob("*") if p.is_file()}
            context.write_text(json.dumps({"values": values}))
            report = report_upgrade(target, context)
            excluded = [item for item in report["files"] if item["status"] == "not-selected"]
            self.assertEqual(len(excluded), 13)
            self.assertEqual(len(report["files"]), 17)
            # The changed manifest is a collision, not permission to prune files.
            with self.assertRaises(RenderError):
                render_project(context, target, True)
            after = {p.relative_to(target).as_posix(): p.read_bytes()
                     for p in target.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_manifest_escape_is_rejected(self):
        from safe_paths import SafePathError
        from report_upgrade import validate_manifest
        state = {"template_version": "2.0.0", "context_sha256": "0" * 64,
                 "files": [{"source": "../secret", "target": "../secret", "sha256": "0" * 64}]}
        with self.assertRaises(SafePathError):
            validate_manifest(state)

    def test_missing_state_is_not_inferred(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(UpgradeError, "missing template state"):
                report_upgrade(Path(temporary))


if __name__ == "__main__":
    unittest.main()
