"""Validate actual rendered contracts, shared by the CLI and template checks."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from safe_paths import SafePathError, relative_parts


class ValidationError(RuntimeError):
    """A rendered artifact is invalid or refers to an unavailable dependency."""


PATH_PATTERN = re.compile(r"`((?:docs|\.agents)/[^`]+|AGENTS\.md)`")
SCRIPT_DEPENDENCIES = {
    ".agents/skills/context-discovery/scripts/build_context_pack.py": [
        ".agents/skills/context-discovery/scripts/audit_evidence.py"
    ],
    ".agents/skills/build-and-test/scripts/select_checks.py": [
        ".agents/skills/context-discovery/scripts/audit_evidence.py"
    ],
}
OPTIONAL_PATTERN = re.compile(r"<!-- optional-reference: ([^\s]+) -->")


def load_validator(root: Path, relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, root / relative)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load validator: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_json(text: str, label: str):
    def reject(value):
        raise ValueError(f"non-finite JSON number: {value}")
    try:
        data = json.loads(text, parse_constant=reject)
        json.dumps(data, allow_nan=False)
        return data
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"invalid JSON in {label}: {exc}") from exc


def existing_reference(root: Path, relative: str) -> bool:
    current = root
    if current.is_symlink():
        raise ValidationError(f"symbolic link target root: {root}")
    try:
        parts = relative_parts(relative)
    except SafePathError as exc:
        raise ValidationError(str(exc)) from exc
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValidationError(f"symbolic link reference: {relative}")
    return current.is_file() or current.is_dir()


def validate_rendered(files, source_root: Path, target_root: Path | None = None):
    by_target = {item.target.as_posix(): item for item in files}
    schemas = {
        ".agents/ai/project-map.json": (
            "skills/context-discovery/scripts/build_context_pack.py", "validate_project_map"
        ),
        ".agents/ai/verification-routes.json": (
            "skills/build-and-test/scripts/select_checks.py", "validate_verification_routes"
        ),
    }
    for name in by_target:
        for dependency in SCRIPT_DEPENDENCIES.get(name, []):
            if dependency not in by_target and not (
                target_root is not None and existing_reference(target_root, dependency)
            ):
                raise ValidationError(f"missing script dependency in {name}: {dependency}")
    for name, item in by_target.items():
        text = item.content.decode("utf-8")
        if name.endswith(".json"):
            data = strict_json(text, name)
            if name in schemas:
                script, function = schemas[name]
                module = load_validator(source_root, script, function)
                try:
                    getattr(module, function)(data)
                except (RuntimeError, ValueError, TypeError) as exc:
                    raise ValidationError(f"invalid routing schema in {name}: {exc}") from exc
        if not name.endswith(".md"):
            continue
        optional = set(OPTIONAL_PATTERN.findall(text))
        for reference in PATH_PATTERN.findall(text):
            if any(marker in reference for marker in ("<", ">", "$")):
                continue
            try:
                relative_parts(reference)
            except SafePathError as exc:
                raise ValidationError(str(exc)) from exc
            if reference in optional or reference in by_target:
                continue
            if any(
                target.startswith(reference.rstrip("/") + "/") for target in by_target
            ):
                continue
            if target_root is not None and existing_reference(target_root, reference):
                continue
            raise ValidationError(f"missing referenced target in {name}: {reference}")
