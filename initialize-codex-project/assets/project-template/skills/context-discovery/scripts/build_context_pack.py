#!/usr/bin/env python3
"""Select a bounded list of relevant repository files without reading content."""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import importlib.util
import re
import sys
from collections import OrderedDict
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MODULE_FIELDS = {
    "id",
    "paths",
    "responsibility",
    "entrypoints",
    "public_contracts",
    "dependencies",
    "consumers",
    "tests",
    "authority_docs",
    "generated_paths",
}
ROUTE_FIELDS = {
    "id",
    "task_types",
    "module_ids",
    "initial_paths",
    "expand_when",
}


class ContextPackError(RuntimeError):
    """Raised for invalid routing data or unsafe file selection."""


def check_provenance(record):
    if "provenance" not in record:
        return
    spec = importlib.util.spec_from_file_location("routing_evidence", Path(__file__).with_name("audit_evidence.py"))
    if spec is None or spec.loader is None:
        raise ContextPackError("cannot load provenance validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.validate_provenance(record["provenance"])
    except RuntimeError as exc:
        raise ContextPackError(str(exc)) from exc


def load_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContextPackError(f"cannot load project map {path}: {exc}") from exc


def require_object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ContextPackError(f"{label} must be an object")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextPackError(f"{label} must be a non-blank string")
    return value


def require_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContextPackError(f"{label} must be a positive integer")
    return value


def require_string_list(value: Any, label: str, allow_empty: bool = True) -> List[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ContextPackError(f"{label} must be an array of non-blank strings")
    if not allow_empty and not value:
        raise ContextPackError(f"{label} must not be empty")
    return list(value)


def normalize_relative(raw: str, label: str, allow_glob: bool = False) -> str:
    value = raw.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ContextPackError(f"unsafe {label}: {raw!r}")
    normalized = path.as_posix()
    if normalized in {"", "."} or normalized.startswith("./"):
        raise ContextPackError(f"invalid {label}: {raw!r}")
    if not allow_glob and any(char in normalized for char in "*?["):
        raise ContextPackError(f"globs are not allowed in {label}: {raw!r}")
    return normalized


def validate_project_map(raw: Any) -> Dict[str, Any]:
    data = require_object(raw, "project map")
    required = {
        "schema_version",
        "project_name",
        "budgets",
        "excluded_paths",
        "modules",
        "context_routes",
        "documentation_gaps",
    }
    unknown = sorted(set(data) - required)
    missing = sorted(required - set(data))
    if unknown or missing:
        raise ContextPackError(
            f"project map keys invalid; missing={missing}, unknown={unknown}"
        )
    if data["schema_version"] != 1:
        raise ContextPackError("project map schema_version must be 1")
    require_string(data["project_name"], "project_name")

    budgets = require_object(data["budgets"], "budgets")
    if set(budgets) != {
        "max_initial_files",
        "max_initial_bytes",
        "max_expansion_rounds",
    }:
        raise ContextPackError("budgets must define files, bytes, and expansion rounds")
    for key, value in budgets.items():
        require_positive_int(value, f"budgets.{key}")

    exclusions = require_string_list(data["excluded_paths"], "excluded_paths")
    data["excluded_paths"] = [
        normalize_relative(item, "excluded path", allow_glob=True)
        for item in exclusions
    ]
    require_string_list(data["documentation_gaps"], "documentation_gaps")

    modules = data["modules"]
    if not isinstance(modules, list) or not modules:
        raise ContextPackError("modules must be a non-empty array")
    module_ids: List[str] = []
    exact_path_fields = [
        "entrypoints",
        "public_contracts",
        "tests",
        "authority_docs",
        "generated_paths",
    ]
    for index, raw_module in enumerate(modules):
        module = require_object(raw_module, f"modules[{index}]")
        if set(module) - {"provenance"} != MODULE_FIELDS:
            raise ContextPackError(f"modules[{index}] has missing or unknown fields")
        check_provenance(module)
        module_id = require_string(module["id"], f"modules[{index}].id")
        if not ID_PATTERN.fullmatch(module_id) or module_id in module_ids:
            raise ContextPackError(f"invalid or duplicate module id: {module_id}")
        module_ids.append(module_id)
        require_string(module["responsibility"], f"modules[{index}].responsibility")
        module["paths"] = [
            normalize_relative(item, f"modules[{index}].paths", allow_glob=True)
            for item in require_string_list(
                module["paths"], f"modules[{index}].paths", allow_empty=False
            )
        ]
        for field in exact_path_fields:
            module[field] = [
                normalize_relative(item, f"modules[{index}].{field}")
                for item in require_string_list(
                    module[field], f"modules[{index}].{field}"
                )
            ]
        for field in ("dependencies", "consumers"):
            require_string_list(module[field], f"modules[{index}].{field}")

    known_ids = set(module_ids)
    for index, module in enumerate(modules):
        for field in ("dependencies", "consumers"):
            unknown_ids = sorted(set(module[field]) - known_ids)
            if unknown_ids:
                raise ContextPackError(
                    f"modules[{index}].{field} references unknown modules: {unknown_ids}"
                )

    routes = data["context_routes"]
    if not isinstance(routes, list):
        raise ContextPackError("context_routes must be an array")
    route_ids: List[str] = []
    for index, raw_route in enumerate(routes):
        route = require_object(raw_route, f"context_routes[{index}]")
        if set(route) != ROUTE_FIELDS:
            raise ContextPackError(
                f"context_routes[{index}] has missing or unknown fields"
            )
        route_id = require_string(route["id"], f"context_routes[{index}].id")
        if not ID_PATTERN.fullmatch(route_id) or route_id in route_ids:
            raise ContextPackError(f"invalid or duplicate route id: {route_id}")
        route_ids.append(route_id)
        require_string_list(
            route["task_types"], f"context_routes[{index}].task_types", allow_empty=False
        )
        route_modules = require_string_list(
            route["module_ids"], f"context_routes[{index}].module_ids", allow_empty=False
        )
        unknown_modules = sorted(set(route_modules) - known_ids)
        if unknown_modules:
            raise ContextPackError(
                f"context_routes[{index}] references unknown modules: {unknown_modules}"
            )
        route["initial_paths"] = [
            normalize_relative(item, f"context_routes[{index}].initial_paths")
            for item in require_string_list(
                route["initial_paths"],
                f"context_routes[{index}].initial_paths",
            )
        ]
        require_string_list(route["expand_when"], f"context_routes[{index}].expand_when")
    return data


def path_matches(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def safe_file_size(root: Path, relative: str) -> Tuple[Optional[int], Optional[str]]:
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            return None, f"symbolic-link path rejected: {relative}"
    if not current.exists():
        return None, f"missing path: {relative}"
    if not current.is_file():
        return None, f"non-file path rejected: {relative}"
    try:
        return current.stat().st_size, None
    except OSError as exc:
        return None, f"cannot stat {relative}: {exc}"


def build_context_pack(
    project_root: Path,
    project_map: Mapping[str, Any],
    module_ids: Sequence[str] = (),
    changed_files: Sequence[str] = (),
    task_type: Optional[str] = None,
    max_files: Optional[int] = None,
    max_bytes: Optional[int] = None,
) -> Dict[str, Any]:
    data = validate_project_map(copy.deepcopy(dict(project_map)))
    root = project_root.absolute()
    if root.is_symlink() or not root.is_dir():
        raise ContextPackError(f"project root must be a real directory: {root}")
    normalized_changes = [
        normalize_relative(item, "changed file") for item in changed_files
    ]
    known_modules = {module["id"]: module for module in data["modules"]}
    unknown_requested = sorted(set(module_ids) - set(known_modules))
    if unknown_requested:
        raise ContextPackError(f"unknown requested modules: {unknown_requested}")

    selected_module_ids: List[str] = list(dict.fromkeys(module_ids))
    for changed in normalized_changes:
        for module in data["modules"]:
            if path_matches(changed, module["paths"]) and module["id"] not in selected_module_ids:
                selected_module_ids.append(module["id"])

    has_scope_hint = bool(module_ids or changed_files)
    task_routes = [route for route in data["context_routes"]
                   if task_type is not None and task_type in route["task_types"]]
    if not has_scope_hint:
        task_modules = {module_id for route in task_routes for module_id in route["module_ids"]}
        selected_module_ids = [module_id for module_id in known_modules if module_id in task_modules]
    selected_routes = sorted([
        route for route in data["context_routes"]
        if set(route["module_ids"]) & set(selected_module_ids)
    ], key=lambda route: route["id"])

    candidates: "OrderedDict[str, List[str]]" = OrderedDict()

    def add(path: str, reason: str) -> None:
        normalized = normalize_relative(path, "context candidate")
        candidates.setdefault(normalized, [])
        if reason not in candidates[normalized]:
            candidates[normalized].append(reason)

    for changed in normalized_changes:
        add(changed, "changed-file")
    # Essential module evidence precedes broad route examples in the budget.
    for module_id in selected_module_ids:
        module = known_modules[module_id]
        for field in ("authority_docs", "public_contracts", "tests", "entrypoints"):
            for path in module[field]:
                add(path, f"module:{module_id}:{field}")
    outside_scope = []
    for route in selected_routes:
        for path in route["initial_paths"]:
            owners = {module["id"] for module in data["modules"] if path_matches(path, module["paths"])}
            if has_scope_hint and owners and not owners.intersection(selected_module_ids) and path not in candidates:
                outside_scope.append({"path": path, "reason": "outside-selected-modules"})
            else:
                add(path, f"route:{route['id']}")

    file_budget = (
        data["budgets"]["max_initial_files"] if max_files is None else max_files
    )
    byte_budget = (
        data["budgets"]["max_initial_bytes"] if max_bytes is None else max_bytes
    )
    require_positive_int(file_budget, "max_files")
    require_positive_int(byte_budget, "max_bytes")

    selected_files: List[Dict[str, Any]] = []
    omitted: List[Dict[str, Any]] = list(outside_scope)
    gaps: List[str] = list(data["documentation_gaps"])
    total_bytes = 0
    exclusions = data["excluded_paths"]
    for path, reasons in candidates.items():
        if path_matches(path, exclusions):
            omitted.append({"path": path, "reason": "excluded-path"})
            continue
        size, error = safe_file_size(root, path)
        if error:
            gaps.append(error)
            omitted.append({"path": path, "reason": error})
            continue
        assert size is not None
        if len(selected_files) >= file_budget:
            omitted.append({"path": path, "reason": "file-budget"})
            continue
        if total_bytes + size > byte_budget:
            omitted.append({"path": path, "reason": "byte-budget", "bytes": size})
            continue
        selected_files.append({"path": path, "reasons": reasons, "bytes": size})
        total_bytes += size

    expand_when: List[str] = []
    for route in selected_routes:
        for condition in route["expand_when"]:
            if condition not in expand_when:
                expand_when.append(condition)
    return {
        "schema_version": 1,
        "project_name": data["project_name"],
        "task_type": task_type,
        "selected_modules": selected_module_ids,
        "scope_required": not has_scope_hint and len(selected_module_ids) > 1,
        "candidate_routes": [route["id"] for route in task_routes],
        "execution_authorized": False,
        "selected_routes": [route["id"] for route in selected_routes],
        "files": selected_files,
        "total_files": len(selected_files),
        "total_bytes": total_bytes,
        "budget": {
            "max_files": file_budget,
            "max_bytes": byte_budget,
            "max_expansion_rounds": data["budgets"]["max_expansion_rounds"],
        },
        "omitted": omitted,
        "gaps": list(dict.fromkeys(gaps)),
        "expand_when": expand_when,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path)
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--task-type")
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--max-bytes", type=int)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = args.project_root.absolute()
    map_path = args.map_path or root / ".agents" / "ai" / "project-map.json"
    if not map_path.is_absolute():
        map_path = root / map_path
    try:
        data = load_json(map_path)
        result = build_context_pack(
            project_root=root,
            project_map=data,
            module_ids=args.module,
            changed_files=args.changed_file,
            task_type=args.task_type,
            max_files=args.max_files,
            max_bytes=args.max_bytes,
        )
    except ContextPackError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
