#!/usr/bin/env python3
"""Select evidenced verification commands for changed paths without running them."""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KINDS = {"build", "test", "format", "lint", "static", "diff", "manual"}
COMMAND_FIELDS = {"id", "command", "kind", "evidence", "mutates"}
ROUTE_FIELDS = {
    "id",
    "path_patterns",
    "focused_check_ids",
    "consumer_check_ids",
    "required_build_ids",
    "escalate_when",
}


class CheckSelectionError(RuntimeError):
    """Raised for invalid verification metadata or changed paths."""


def load_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise CheckSelectionError(f"cannot load verification routes {path}: {exc}") from exc


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CheckSelectionError(f"{label} must be a non-blank string")
    return value


def require_string_list(value: Any, label: str, allow_empty: bool = True) -> List[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise CheckSelectionError(f"{label} must be an array of non-blank strings")
    if not allow_empty and not value:
        raise CheckSelectionError(f"{label} must not be empty")
    return list(value)


def normalize_relative(raw: str, label: str, allow_glob: bool = False) -> str:
    value = raw.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise CheckSelectionError(f"unsafe {label}: {raw!r}")
    normalized = path.as_posix()
    if normalized in {"", "."} or normalized.startswith("./"):
        raise CheckSelectionError(f"invalid {label}: {raw!r}")
    if not allow_glob and any(char in normalized for char in "*?["):
        raise CheckSelectionError(f"globs are not allowed in {label}: {raw!r}")
    return normalized


def validate_verification_routes(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise CheckSelectionError("verification routes must be an object")
    required = {
        "schema_version",
        "commands",
        "routes",
        "fallback_check_ids",
        "documentation_gaps",
    }
    if set(raw) != required:
        raise CheckSelectionError("verification routes has missing or unknown fields")
    if raw["schema_version"] != 1:
        raise CheckSelectionError("verification routes schema_version must be 1")
    require_string_list(raw["documentation_gaps"], "documentation_gaps")

    commands = raw["commands"]
    if not isinstance(commands, list):
        raise CheckSelectionError("commands must be an array")
    command_ids: List[str] = []
    for index, command in enumerate(commands):
        if not isinstance(command, dict) or set(command) != COMMAND_FIELDS:
            raise CheckSelectionError(f"commands[{index}] has missing or unknown fields")
        command_id = require_string(command["id"], f"commands[{index}].id")
        if not ID_PATTERN.fullmatch(command_id) or command_id in command_ids:
            raise CheckSelectionError(f"invalid or duplicate command id: {command_id}")
        command_ids.append(command_id)
        require_string(command["command"], f"commands[{index}].command")
        kind = require_string(command["kind"], f"commands[{index}].kind")
        if kind not in KINDS:
            raise CheckSelectionError(f"unsupported command kind: {kind}")
        require_string(command["evidence"], f"commands[{index}].evidence")
        if not isinstance(command["mutates"], bool):
            raise CheckSelectionError(f"commands[{index}].mutates must be boolean")

    known_commands = set(command_ids)
    fallback = require_string_list(raw["fallback_check_ids"], "fallback_check_ids")
    unknown_fallback = sorted(set(fallback) - known_commands)
    if unknown_fallback:
        raise CheckSelectionError(f"fallback references unknown commands: {unknown_fallback}")

    routes = raw["routes"]
    if not isinstance(routes, list):
        raise CheckSelectionError("routes must be an array")
    route_ids: List[str] = []
    for index, route in enumerate(routes):
        if not isinstance(route, dict) or set(route) != ROUTE_FIELDS:
            raise CheckSelectionError(f"routes[{index}] has missing or unknown fields")
        route_id = require_string(route["id"], f"routes[{index}].id")
        if not ID_PATTERN.fullmatch(route_id) or route_id in route_ids:
            raise CheckSelectionError(f"invalid or duplicate route id: {route_id}")
        route_ids.append(route_id)
        route["path_patterns"] = [
            normalize_relative(item, f"routes[{index}].path_patterns", allow_glob=True)
            for item in require_string_list(
                route["path_patterns"], f"routes[{index}].path_patterns", allow_empty=False
            )
        ]
        for field in (
            "focused_check_ids",
            "consumer_check_ids",
            "required_build_ids",
        ):
            ids = require_string_list(route[field], f"routes[{index}].{field}")
            unknown = sorted(set(ids) - known_commands)
            if unknown:
                raise CheckSelectionError(
                    f"routes[{index}].{field} references unknown commands: {unknown}"
                )
        require_string_list(route["escalate_when"], f"routes[{index}].escalate_when")
    return raw


def select_checks(
    verification_routes: Mapping[str, Any], changed_files: Sequence[str]
) -> Dict[str, Any]:
    data = validate_verification_routes(copy.deepcopy(dict(verification_routes)))
    if not changed_files:
        raise CheckSelectionError("at least one changed file is required")
    changed = [normalize_relative(path, "changed file") for path in changed_files]
    command_by_id = {item["id"]: item for item in data["commands"]}
    matched_routes: List[Mapping[str, Any]] = []
    matched_paths: Dict[str, List[str]] = {path: [] for path in changed}
    for route in data["routes"]:
        for path in changed:
            if any(
                fnmatch.fnmatchcase(path, pattern) for pattern in route["path_patterns"]
            ):
                matched_paths[path].append(route["id"])
                if route not in matched_routes:
                    matched_routes.append(route)

    unmatched = [path for path, routes in matched_paths.items() if not routes]
    selected: Dict[str, Dict[str, Any]] = {}

    def add(command_id: str, category: str, route_id: str) -> None:
        record = selected.setdefault(
            command_id,
            {
                **command_by_id[command_id],
                "categories": [],
                "selected_by_routes": [],
            },
        )
        if category not in record["categories"]:
            record["categories"].append(category)
        if route_id not in record["selected_by_routes"]:
            record["selected_by_routes"].append(route_id)

    categories = (
        ("focused_check_ids", "focused"),
        ("consumer_check_ids", "consumer"),
        ("required_build_ids", "required-build"),
    )
    for route in matched_routes:
        for field, category in categories:
            for command_id in route[field]:
                add(command_id, category, route["id"])
    if unmatched:
        for command_id in data["fallback_check_ids"]:
            add(command_id, "fallback", "<unmatched-path>")

    escalation_conditions: List[str] = []
    for route in matched_routes:
        for condition in route["escalate_when"]:
            if condition not in escalation_conditions:
                escalation_conditions.append(condition)
    return {
        "schema_version": 1,
        "changed_files": changed,
        "matched_routes": [route["id"] for route in matched_routes],
        "path_matches": matched_paths,
        "unmatched_paths": unmatched,
        "commands": list(selected.values()),
        "escalate_when": escalation_conditions,
        "documentation_gaps": data["documentation_gaps"],
        "execution_authorized": False,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--routes", dest="routes_path", type=Path)
    parser.add_argument("--changed-file", action="append", required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = args.project_root.absolute()
    routes_path = args.routes_path or root / ".agents" / "ai" / "verification-routes.json"
    if not routes_path.is_absolute():
        routes_path = root / routes_path
    try:
        result = select_checks(load_json(routes_path), args.changed_file)
    except CheckSelectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
