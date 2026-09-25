import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "initialize-codex-project/assets/project-template/skills/context-discovery/scripts/audit_evidence.py"
SPEC = importlib.util.spec_from_file_location("audit_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EvidenceAuditTests(unittest.TestCase):
    def test_current_stale_missing_and_legacy_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "build.json"
            source.write_bytes(b"verified source")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            document = {"commands": [
                {"id": "current", "provenance": [{"path": "build.json", "sha256": digest}]},
                {"id": "stale", "provenance": [{"path": "build.json", "sha256": "0" * 64}]},
                {"id": "missing", "provenance": [{"path": "missing.json", "sha256": digest}]},
                {"id": "legacy", "evidence": "prose remains supported"},
            ]}
            result = MODULE.audit_document(root, document)
            self.assertEqual([item["status"] for item in result["evidence"]], ["current", "stale", "missing", "unverified"])
            self.assertEqual(source.read_bytes(), b"verified source")
            self.assertFalse(result["execution_authorized"])

    def test_symlink_sources_and_invalid_dates_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source").write_text("source")
            (root / "link").symlink_to(root / "source")
            with self.assertRaisesRegex(MODULE.EvidenceError, "symbolic-link"):
                MODULE.fingerprint(root, "link")
        with self.assertRaisesRegex(MODULE.EvidenceError, "verified_at"):
            MODULE.validate_provenance([{"path": "source", "verified_at": "2026-02-30"}])


if __name__ == "__main__":
    unittest.main()
