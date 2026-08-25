#!/usr/bin/env python3
"""Run deterministic context and verification routing benchmark scenarios."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List


class BenchmarkError(RuntimeError):
    """Raised when benchmark data or a routing expectation is invalid."""


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BenchmarkError(f"cannot load routing module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise BenchmarkError(f"cannot load benchmark input {path}: {exc}") from exc


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise BenchmarkError(f"{label}: expected {expected!r}, got {actual!r}")


def run_benchmark(repository_root: Path) -> Dict[str, Any]:
    skill_root = repository_root / "initialize-codex-project"
    asset_root = skill_root / "assets/project-template"
    context_module = load_module(
        asset_root / "skills/context-discovery/scripts/build_context_pack.py",
        "benchmark_context_pack",
    )
    checks_module = load_module(
        asset_root / "skills/build-and-test/scripts/select_checks.py",
        "benchmark_select_checks",
    )
    project_map = load_json(repository_root / ".agents/ai/project-map.json")
    routes = load_json(repository_root / ".agents/ai/verification-routes.json")
    benchmark = load_json(skill_root / "benchmarks/routing-scenarios.json")
    if not isinstance(benchmark, dict) or set(benchmark) != {"schema_version", "scenarios"}:
        raise BenchmarkError("benchmark root has missing or unknown fields")
    if benchmark["schema_version"] != 1 or not isinstance(benchmark["scenarios"], list):
        raise BenchmarkError("unsupported benchmark schema")

    results: List[Dict[str, Any]] = []
    for scenario in benchmark["scenarios"]:
        scenario_id = scenario["id"]
        context = scenario["context"]
        expected = scenario["expected"]
        pack = context_module.build_context_pack(
            project_root=repository_root,
            project_map=project_map,
            module_ids=context["module_ids"],
            changed_files=context["changed_files"],
            task_type=context["task_type"],
        )
        selection = checks_module.select_checks(
            routes, scenario["verification_changed_files"]
        )
        command_ids = [command["id"] for command in selection["commands"]]
        require_equal(pack["selected_modules"], expected["module_ids"], f"{scenario_id} modules")
        require_equal(pack["selected_routes"], expected["context_route_ids"], f"{scenario_id} context routes")
        require_equal(selection["matched_routes"], expected["verification_route_ids"], f"{scenario_id} verification routes")
        require_equal(command_ids, expected["command_ids"], f"{scenario_id} commands")
        if pack["total_files"] > expected["max_files"]:
            raise BenchmarkError(f"{scenario_id} exceeded file budget")
        if pack["total_bytes"] > expected["max_bytes"]:
            raise BenchmarkError(f"{scenario_id} exceeded byte budget")
        if selection["execution_authorized"]:
            raise BenchmarkError(f"{scenario_id} selector authorized execution")
        results.append(
            {
                "id": scenario_id,
                "selected_files": pack["total_files"],
                "selected_bytes_proxy": pack["total_bytes"],
                "selected_commands": len(command_ids),
            }
        )
    return {
        "schema_version": 1,
        "metric_note": "Bytes and file counts are deterministic context-size proxies, not model token telemetry.",
        "scenarios": results,
        "totals": {
            "selected_files": sum(item["selected_files"] for item in results),
            "selected_bytes_proxy": sum(item["selected_bytes_proxy"] for item in results),
            "selected_commands": sum(item["selected_commands"] for item in results),
        },
    }


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    try:
        result = run_benchmark(repository_root)
    except (BenchmarkError, RuntimeError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
