from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPOSITORY_ROOT / "initialize-codex-project/scripts/benchmark_routing.py"
SPEC = importlib.util.spec_from_file_location("benchmark_routing_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PerformanceRoutingTests(unittest.TestCase):
    def test_repository_scenarios_meet_routing_budgets(self) -> None:
        result = MODULE.run_benchmark(REPOSITORY_ROOT)
        self.assertEqual(len(result["scenarios"]), 3)
        self.assertIn("not model token telemetry", result["metric_note"])
        self.assertGreater(result["totals"]["selected_files"], 0)
        self.assertGreater(result["totals"]["selected_commands"], 0)


if __name__ == "__main__":
    unittest.main()
