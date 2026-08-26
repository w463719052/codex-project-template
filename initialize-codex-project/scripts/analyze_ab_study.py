#!/usr/bin/env python3
"""Validate and summarize paired Codex workflow A/B study records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


class StudyError(RuntimeError):
    """Raised when A/B study input is unsafe, incomplete, or inconsistent."""


METRIC_FIELDS = (
    "user_round_trips",
    "elapsed_seconds",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "scope_escapes",
    "review_defects",
)
NONNEGATIVE_INTEGER_FIELDS = {
    "user_round_trips",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "scope_escapes",
    "review_defects",
}
PAIRING_FIELDS = (
    "task_id",
    "base_revision",
    "model_configuration",
    "environment",
    "acceptance_checks",
)


def load_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise StudyError(f"cannot load study {path}: {exc}") from exc


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StudyError(f"{label} must be a non-empty string")
    return value


def validate_metric(value: Any, name: str, label: str) -> Optional[float]:
    if value is None and name in {"input_tokens", "output_tokens", "total_tokens"}:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise StudyError(f"{label}.{name} must be a non-negative number or allowed null")
    if name in NONNEGATIVE_INTEGER_FIELDS and not isinstance(value, int):
        raise StudyError(f"{label}.{name} must be an integer or allowed null")
    return float(value)


def validate_run(raw: Any, index: int) -> Dict[str, Any]:
    label = f"runs[{index}]"
    if not isinstance(raw, dict):
        raise StudyError(f"{label} must be an object")
    required = {
        "pair_id",
        "task_id",
        "arm",
        "base_revision",
        "model_configuration",
        "environment",
        "acceptance_checks",
        "metrics",
    }
    if set(raw) != required:
        raise StudyError(
            f"{label} has missing or unknown fields: expected {sorted(required)}"
        )
    result = {key: require_string(raw[key], f"{label}.{key}") for key in (
        "pair_id", "task_id", "base_revision", "model_configuration", "environment"
    )}
    arm = raw["arm"]
    if arm not in {"A", "B"}:
        raise StudyError(f"{label}.arm must be 'A' or 'B'")
    result["arm"] = arm
    checks = raw["acceptance_checks"]
    if not isinstance(checks, list) or not checks or not all(
        isinstance(item, str) and item.strip() for item in checks
    ):
        raise StudyError(f"{label}.acceptance_checks must be a non-empty string array")
    result["acceptance_checks"] = checks
    metrics = raw["metrics"]
    if not isinstance(metrics, dict) or set(metrics) != {
        "first_pass_success", *METRIC_FIELDS
    }:
        raise StudyError(f"{label}.metrics has missing or unknown fields")
    if not isinstance(metrics["first_pass_success"], bool):
        raise StudyError(f"{label}.metrics.first_pass_success must be boolean")
    normalized_metrics: Dict[str, Any] = {
        "first_pass_success": metrics["first_pass_success"]
    }
    for name in METRIC_FIELDS:
        normalized_metrics[name] = validate_metric(metrics[name], name, label)
    token_values = [normalized_metrics[name] for name in (
        "input_tokens", "output_tokens", "total_tokens"
    )]
    if all(value is not None for value in token_values):
        if token_values[0] + token_values[1] != token_values[2]:
            raise StudyError(f"{label} token total must equal input plus output")
    result["metrics"] = normalized_metrics
    return result


def mean(values: Sequence[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    return None if not present else sum(present) / len(present)


def summarize_arm(runs: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "runs": len(runs),
        "first_pass_success_rate": mean(
            [1.0 if run["metrics"]["first_pass_success"] else 0.0 for run in runs]
        ),
    }
    for name in METRIC_FIELDS:
        summary[f"mean_{name}"] = mean([run["metrics"][name] for run in runs])
    return summary


def analyze_study(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "study_id", "evidence_kind", "description", "runs"
    }:
        raise StudyError("study root has missing or unknown fields")
    if raw["schema_version"] != 1:
        raise StudyError("unsupported study schema_version")
    study_id = require_string(raw["study_id"], "study_id")
    description = require_string(raw["description"], "description")
    evidence_kind = raw["evidence_kind"]
    if evidence_kind not in {"example", "real"}:
        raise StudyError("evidence_kind must be 'example' or 'real'")
    if not isinstance(raw["runs"], list) or not raw["runs"]:
        raise StudyError("runs must be a non-empty array")
    runs = [validate_run(item, index) for index, item in enumerate(raw["runs"])]

    by_pair: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for run in runs:
        arms = by_pair.setdefault(run["pair_id"], {})
        if run["arm"] in arms:
            raise StudyError(f"duplicate arm {run['arm']} for pair {run['pair_id']}")
        arms[run["arm"]] = run

    complete: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    incomplete: List[str] = []
    confounded: Dict[str, List[str]] = {}
    for pair_id, arms in sorted(by_pair.items()):
        if set(arms) != {"A", "B"}:
            incomplete.append(pair_id)
            continue
        mismatches = [field for field in PAIRING_FIELDS if arms["A"][field] != arms["B"][field]]
        if mismatches:
            confounded[pair_id] = mismatches
            continue
        complete.append((arms["A"], arms["B"]))

    arm_a = [pair[0] for pair in complete]
    arm_b = [pair[1] for pair in complete]
    deltas: Dict[str, Optional[float]] = {
        "first_pass_success_rate": None,
    }
    if complete:
        a_success = summarize_arm(arm_a)["first_pass_success_rate"]
        b_success = summarize_arm(arm_b)["first_pass_success_rate"]
        deltas["first_pass_success_rate"] = b_success - a_success
    for name in METRIC_FIELDS:
        pair_deltas = []
        for a_run, b_run in complete:
            a_value = a_run["metrics"][name]
            b_value = b_run["metrics"][name]
            pair_deltas.append(None if a_value is None or b_value is None else b_value - a_value)
        deltas[name] = mean(pair_deltas)

    notes = []
    notes.append(
        "Reported deltas are descriptive; interpret them with sample size and study controls."
    )
    if evidence_kind == "example":
        notes.append("Example data validates the analyzer and is not performance evidence.")
    if incomplete:
        notes.append("Incomplete pairs are excluded from arm summaries and deltas.")
    if confounded:
        notes.append("Confounded pairs are excluded because pairing fields differ.")
    if any(deltas[name] is None for name in ("input_tokens", "output_tokens", "total_tokens")):
        notes.append("Missing token telemetry remains missing and is not treated as zero.")

    return {
        "schema_version": 1,
        "study_id": study_id,
        "description": description,
        "evidence_kind": evidence_kind,
        "complete_pairs": len(complete),
        "incomplete_pair_ids": incomplete,
        "confounded_pairs": confounded,
        "arms": {"A": summarize_arm(arm_a), "B": summarize_arm(arm_b)},
        "paired_delta_b_minus_a": deltas,
        "notes": notes,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze paired real-task workflow A/B records.")
    parser.add_argument("--input", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = analyze_study(load_json(args.input))
    except StudyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
