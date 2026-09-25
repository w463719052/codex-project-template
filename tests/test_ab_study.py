from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPOSITORY_ROOT / "initialize-codex-project/scripts/analyze_ab_study.py"
SPEC = importlib.util.spec_from_file_location("analyze_ab_study_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AbStudyTests(unittest.TestCase):
    @staticmethod
    def make_run(pair_id: str, arm: str):
        return {
            "pair_id": pair_id,
            "task_id": "task-1",
            "arm": arm,
            "base_revision": "abc123",
            "model_configuration": "model-x/high",
            "environment": "linux-test",
            "acceptance_checks": ["unit-tests", "review"],
            "metrics": {
                "first_pass_success": arm == "B",
                "user_round_trips": 2 if arm == "A" else 1,
                "elapsed_seconds": 20.0 if arm == "A" else 10.0,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "scope_escapes": 1 if arm == "A" else 0,
                "review_defects": 1 if arm == "A" else 0,
            },
        }

    def study(self):
        return {
            "schema_version": 1,
            "study_id": "test-study",
            "evidence_kind": "real",
            "description": "Test records.",
            "runs": [self.make_run("pair-1", "A"), self.make_run("pair-1", "B")],
        }

    def test_reports_paired_deltas_and_preserves_missing_tokens(self) -> None:
        result = MODULE.analyze_study(self.study())
        self.assertEqual(result["complete_pairs"], 1)
        self.assertEqual(result["paired_delta_b_minus_a"]["user_round_trips"], -1.0)
        self.assertEqual(result["paired_delta_b_minus_a"]["first_pass_success_rate"], 1.0)
        self.assertIsNone(result["paired_delta_b_minus_a"]["total_tokens"])
        self.assertTrue(any("not treated as zero" in note for note in result["notes"]))

    def test_confounded_pair_is_excluded(self) -> None:
        study = self.study()
        study["runs"][1]["base_revision"] = "different"
        result = MODULE.analyze_study(study)
        self.assertEqual(result["complete_pairs"], 0)
        self.assertEqual(result["confounded_pairs"], {"pair-1": ["base_revision"]})

    def test_duplicate_arm_is_rejected(self) -> None:
        study = self.study()
        study["runs"].append(copy.deepcopy(study["runs"][0]))
        with self.assertRaisesRegex(MODULE.StudyError, "duplicate arm"):
            MODULE.analyze_study(study)

    def test_token_total_must_match_components(self) -> None:
        study = self.study()
        metrics = study["runs"][0]["metrics"]
        metrics.update({"input_tokens": 10, "output_tokens": 5, "total_tokens": 99})
        with self.assertRaisesRegex(MODULE.StudyError, "token total"):
            MODULE.analyze_study(study)

    def test_optional_telemetry_counts_only_observed_pairs(self):
        study = self.study()
        for run in study["runs"]:
            run["workflow"] = {"name": "baseline" if run["arm"] == "A" else "minimal", "version": "test"}
            run["repeat_id"] = "repeat-1"
            run["measurement"] = {"method": "session-log", "source": run["arm"] + ".json"}
        study["runs"][0]["metrics"].update(setup_seconds=3, maintenance_seconds=5)
        study["runs"][1]["metrics"].update(setup_seconds=4, maintenance_seconds=None)
        result = MODULE.analyze_study(study)
        self.assertEqual(result["paired_delta_b_minus_a"]["setup_seconds"], 1)
        self.assertEqual(result["paired_metric_samples"]["setup_seconds"], 1)
        self.assertEqual(result["paired_metric_samples"]["maintenance_seconds"], 0)
        self.assertIsNone(result["paired_delta_b_minus_a"]["maintenance_seconds"])

    def test_measurement_mismatch_excludes_pair(self):
        study = self.study()
        for run in study["runs"]:
            run["measurement"] = {"method": run["arm"], "source": "test"}
        result = MODULE.analyze_study(study)
        self.assertEqual(result["confounded_pairs"]["pair-1"], ["measurement.method"])

    def test_nonfinite_metrics_are_rejected(self):
        for invalid in (float("inf"), float("nan")):
            study = self.study()
            study["runs"][0]["metrics"]["elapsed_seconds"] = invalid
            with self.assertRaises(MODULE.StudyError):
                MODULE.analyze_study(study)

    def test_different_workflows_cannot_be_pooled(self):
        study = self.study()
        duplicate = copy.deepcopy(study["runs"][0])
        duplicate["pair_id"] = "pair-2"
        duplicate["workflow"] = {"name": "other", "version": "test"}
        study["runs"].append(duplicate)
        with self.assertRaisesRegex(MODULE.StudyError, "mixes workflow"):
            MODULE.analyze_study(study)

    def test_duplicate_repetition_is_rejected(self):
        study = self.study()
        study["runs"][0]["repeat_id"] = "one"
        duplicate = copy.deepcopy(study["runs"][0])
        duplicate["pair_id"] = "different-pair"
        study["runs"].append(duplicate)
        with self.assertRaisesRegex(MODULE.StudyError, "duplicate task repetition"):
            MODULE.analyze_study(study)


if __name__ == "__main__":
    unittest.main()
