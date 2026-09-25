#!/usr/bin/env python3
"""Select relevant engineering profiles from repository path metadata only."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


DEFAULT_MAX_FILES = 200_000
EVIDENCE_SAMPLE_LIMIT = 10
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SelectionError(RuntimeError):
    """Raised when profile selection cannot be completed safely."""


def default_catalog_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "references"
        / "engineering-standards"
        / "catalog.json"
    )


def _string_list(value: Any, label: str) -> List[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise SelectionError(f"{label} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise SelectionError(f"{label} contains duplicates")
    return value


def load_catalog(path: Path) -> Dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SelectionError(f"cannot load profile catalog {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise SelectionError("profile catalog schema_version must be 1")
    if not isinstance(raw.get("last_verified"), str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw["last_verified"]
    ):
        raise SelectionError("profile catalog last_verified must be YYYY-MM-DD")
    profiles = raw.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise SelectionError("profile catalog profiles must be a non-empty array")

    required = {
        "authority_sources",
        "conditional_extensions",
        "id",
        "marker_names",
        "reference",
        "select_on_markers",
        "strong_extensions",
        "title",
    }
    seen_ids: Set[str] = set()
    seen_references: Set[str] = set()
    for index, profile in enumerate(profiles):
        label = f"profiles[{index}]"
        if not isinstance(profile, dict) or set(profile) != required:
            raise SelectionError(f"{label} must contain exactly {sorted(required)}")
        profile_id = profile["id"]
        if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.fullmatch(profile_id):
            raise SelectionError(f"{label}.id is invalid")
        if profile_id in seen_ids:
            raise SelectionError(f"duplicate profile id: {profile_id}")
        seen_ids.add(profile_id)
        reference = profile["reference"]
        if (
            not isinstance(reference, str)
            or Path(reference).name != reference
            or not reference.endswith(".md")
        ):
            raise SelectionError(f"{label}.reference must be a local Markdown filename")
        if reference in seen_references:
            raise SelectionError(f"duplicate profile reference: {reference}")
        seen_references.add(reference)
        if not isinstance(profile["title"], str) or not profile["title"].strip():
            raise SelectionError(f"{label}.title must be a non-empty string")
        if not isinstance(profile["select_on_markers"], bool):
            raise SelectionError(f"{label}.select_on_markers must be boolean")
        strong = _string_list(profile["strong_extensions"], f"{label}.strong_extensions")
        conditional = _string_list(
            profile["conditional_extensions"], f"{label}.conditional_extensions"
        )
        _string_list(profile["marker_names"], f"{label}.marker_names")
        if set(strong) & set(conditional):
            raise SelectionError(f"{label} repeats an extension across detection groups")
        for extension in strong + conditional:
            if not extension.startswith(".") or extension != extension.lower():
                raise SelectionError(f"invalid lowercase extension in {label}: {extension}")
        sources = profile["authority_sources"]
        if not isinstance(sources, list) or not sources:
            raise SelectionError(f"{label}.authority_sources must be non-empty")
        for source in sources:
            if not isinstance(source, dict) or set(source) != {"title", "url"}:
                raise SelectionError(f"invalid authority source in {label}")
            if not all(isinstance(source[key], str) and source[key] for key in source):
                raise SelectionError(f"blank authority source in {label}")
            if not source["url"].startswith("https://"):
                raise SelectionError(f"authority URL must use HTTPS in {label}")

    return raw


def _sample(paths: Iterable[str]) -> List[str]:
    return sorted(paths)[:EVIDENCE_SAMPLE_LIMIT]


def collect_path_evidence(
    project_root: Path, max_files: int, scopes: Sequence[str] = ()
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], int, bool]:
    if max_files <= 0:
        raise SelectionError("max_files must be positive")
    if project_root.is_symlink() or not project_root.is_dir():
        raise SelectionError(f"project root must be a non-symlink directory: {project_root}")

    scan_roots = []
    for raw in scopes or (".",):
        path = PurePosixPath(raw)
        if path.is_absolute() or ".." in path.parts or any(c in raw for c in "\\:\x00"):
            raise SelectionError(f"unsafe scope: {raw!r}")
        current = project_root
        for part in path.parts:
            current = current / part
            if current.is_symlink():
                raise SelectionError(f"symbolic-link scope rejected: {raw}")
        if not current.exists():
            raise SelectionError(f"missing scope: {raw}")
        scan_roots.append(current)

    def walk_scopes():
        for scan_root in sorted(set(scan_roots)):
            if scan_root.is_file():
                yield str(scan_root.parent), [], [scan_root.name]
            else:
                yield from os.walk(scan_root, followlinks=False)

    seen = set()
    extension_files: Dict[str, Set[str]] = {}
    marker_files: Dict[str, Set[str]] = {}
    scanned_files = 0
    truncated = False
    for current, directory_names, file_names in walk_scopes():
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in EXCLUDED_DIRECTORY_NAMES
            and not (Path(current) / name).is_symlink()
        )
        for name in sorted(file_names):
            path = Path(current) / name
            if path.is_symlink() or path in seen:
                continue
            seen.add(path)
            scanned_files += 1
            if scanned_files > max_files:
                scanned_files = max_files
                truncated = True
                return extension_files, marker_files, scanned_files, truncated
            relative = path.relative_to(project_root).as_posix()
            suffix = path.suffix.lower()
            if suffix:
                extension_files.setdefault(suffix, set()).add(relative)
            marker_files.setdefault(name, set()).add(relative)
    return extension_files, marker_files, scanned_files, truncated


def select_profiles(
    catalog: Mapping[str, Any], project_root: Path, max_files: int = DEFAULT_MAX_FILES,
    scopes: Sequence[str] = (), role: str = "unknown"
) -> Dict[str, Any]:
    if role not in {"unknown", "application", "test", "tooling"}:
        raise SelectionError("role must be unknown, application, test, or tooling")
    extension_files, marker_files, scanned_files, truncated = collect_path_evidence(
        project_root, max_files, scopes
    )
    selected: List[Dict[str, Any]] = []
    ambiguous: List[Dict[str, Any]] = []

    for profile in catalog["profiles"]:
        strong_paths = set().union(
            *(extension_files.get(ext, set()) for ext in profile["strong_extensions"])
        )
        conditional_paths = set().union(
            *(
                extension_files.get(ext, set())
                for ext in profile["conditional_extensions"]
            )
        )
        markers = set().union(
            *(marker_files.get(name, set()) for name in profile["marker_names"])
        )
        is_selected = bool(strong_paths) or bool(conditional_paths and markers)
        if profile["select_on_markers"] and markers:
            is_selected = True
        evidence = {
            "conditional_extension_files": _sample(conditional_paths),
            "marker_files": _sample(markers),
            "strong_extension_files": _sample(strong_paths),
        }
        record = {
            "authority_sources": profile["authority_sources"],
            "evidence": evidence,
            "id": profile["id"],
            "reference": profile["reference"],
            "title": profile["title"],
        }
        if is_selected:
            selected.append(record)
        elif conditional_paths:
            ambiguous.append(record)

    return {
        "scope": {"paths": list(scopes) or ["."], "role": role},
        "ambiguous_profiles": ambiguous,
        "catalog_last_verified": catalog["last_verified"],
        "execution_authorized": False,
        "scanned_files": scanned_files,
        "schema_version": 1,
        "selected_profiles": selected,
        "truncated": truncated,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select language engineering profiles from path metadata without reading source content."
    )
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--catalog", type=Path, default=default_catalog_path())
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--scope", action="append", default=[], help="Relative module path; repeatable")
    parser.add_argument("--role", choices=["unknown", "application", "test", "tooling"], default="unknown")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        result = select_profiles(catalog, args.project_root.absolute(), args.max_files, args.scope, args.role)
    except SelectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
