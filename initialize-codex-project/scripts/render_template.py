#!/usr/bin/env python3
"""Render the Codex project template without overwriting target files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from render_validation import ValidationError, validate_rendered
from safe_paths import SafePathError, write_exclusive


PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
STATE_PATH = PurePosixPath("docs/CODEX_TEMPLATE_STATE.json")
CORE_SOURCES = (
    ".agents/ai/project-map.json.template",
    ".agents/ai/verification-routes.json.template",
    "AGENTS.md.template",
    "docs/AI_CONTEXT_STRATEGY.md.template",
    "docs/CHANGE_IMPACT.md",
    "docs/CODEX_USAGE.md.template",
    "docs/CODEX_WORKFLOW.md",
    "docs/CODING_RULES_LOG.md.template",
    "docs/CODING_STANDARDS.md.template",
    "docs/TASK_TEMPLATE.md.template",
    "docs/VERIFICATION.md.template",
    "skills/build-and-test/SKILL.md.template",
    "skills/build-and-test/scripts/select_checks.py",
    "skills/code-review/SKILL.md.template",
    "skills/context-discovery/SKILL.md.template",
    "skills/context-discovery/scripts/build_context_pack.py",
    "skills/context-discovery/scripts/audit_evidence.py",
)


MINIMAL_SOURCES = (
    "AGENTS.md.template",
    "docs/CODEX_WORKFLOW.md",
    "docs/CODING_STANDARDS.md.template",
    "docs/VERIFICATION.md.template",
)


class RenderError(RuntimeError):
    """Raised when rendering is unsafe or the context is invalid."""


@dataclass(frozen=True)
class RenderedFile:
    source: str
    target: PurePosixPath
    content: bytes


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def source_root() -> Path:
    return skill_root() / "assets" / "project-template"


def template_version() -> str:
    path = skill_root() / "VERSION"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RenderError(f"cannot read template version: {path}: {exc}") from exc


def normalize_source_name(raw: str) -> str:
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise RenderError(f"unsafe included source path: {raw!r}")
    normalized = path.as_posix()
    if normalized == "." or normalized.startswith("./"):
        raise RenderError(f"invalid included source path: {raw!r}")
    return normalized


def discover_sources(root: Path) -> Dict[str, Path]:
    if not root.is_dir():
        raise RenderError(f"template source directory does not exist: {root}")
    sources: Dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if path.name != ".DS_Store" and path.is_file():
            name = path.relative_to(root).as_posix()
            sources[name] = path
    if not sources:
        raise RenderError(f"template source directory is empty: {root}")
    return sources


def target_name_for(source_name: str) -> PurePosixPath:
    source_path = PurePosixPath(source_name)
    parts = source_path.parts
    if parts and parts[0] == "skills":
        target = PurePosixPath(".agents", "skills", *parts[1:])
    else:
        target = source_path
    if target.name.endswith(".template"):
        target = target.with_name(target.name[: -len(".template")])
    if target.is_absolute() or ".." in target.parts:
        raise RenderError(f"unsafe rendered target path: {target}")
    return target


def placeholder_names(text: str) -> Set[str]:
    return set(PLACEHOLDER_PATTERN.findall(text))


def all_placeholder_names(root: Path) -> Set[str]:
    names: Set[str] = set()
    for path in discover_sources(root).values():
        try:
            names.update(placeholder_names(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError) as exc:
            raise RenderError(f"cannot read UTF-8 template {path}: {exc}") from exc
    return names


def load_context(path: Path) -> Tuple[Dict[str, Any], Optional[List[str]]]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RenderError(f"cannot load context {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RenderError("context root must be a JSON object")
    allowed_keys = {"values", "include", "preset"}
    unknown_keys = sorted(set(raw) - allowed_keys)
    if unknown_keys:
        raise RenderError(f"unknown context keys: {', '.join(unknown_keys)}")
    values_raw = raw.get("values")
    if not isinstance(values_raw, dict):
        raise RenderError("context.values must be a JSON object")
    values: Dict[str, Any] = {}
    for key, value in values_raw.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise RenderError(f"invalid placeholder name in context: {key!r}")
        if key.endswith("_JSON"):
            if not isinstance(value, (dict, list)) or not value:
                raise RenderError(
                    f"structured context value for {key} must be a non-empty object or array"
                )
            try:
                json.dumps(value, allow_nan=False)
            except (TypeError, ValueError) as exc:
                raise RenderError(f"context value for {key} is not valid JSON: {exc}") from exc
        else:
            if not isinstance(value, str):
                raise RenderError(f"context value for {key} must be a string")
            if not value.strip():
                raise RenderError(f"context value for {key} must not be blank")
        values[key] = value
    include_raw = raw.get("include")
    preset_raw = raw.get("preset", "minimal")
    if not isinstance(preset_raw, str) or preset_raw not in {"minimal", "core", "full"}:
        raise RenderError("context.preset must be 'minimal', 'core' or 'full'")
    if include_raw is not None and "preset" in raw:
        raise RenderError("context.include and context.preset are mutually exclusive")
    include: Optional[List[str]] = None
    if include_raw is not None:
        if not isinstance(include_raw, list) or not all(
            isinstance(item, str) for item in include_raw
        ):
            raise RenderError("context.include must be an array of source paths")
        include = [normalize_source_name(item) for item in include_raw]
        if len(include) != len(set(include)):
            raise RenderError("context.include contains duplicate paths")
    elif preset_raw == "minimal":
        include = list(MINIMAL_SOURCES)
    elif preset_raw == "core":
        include = list(CORE_SOURCES)
    return values, include


def render_text(text: str, values: Mapping[str, Any], source_name: str) -> str:
    required = placeholder_names(text)
    missing = sorted(required - set(values))
    if missing:
        raise RenderError(
            f"missing placeholder values for {source_name}: {', '.join(missing)}"
        )

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = values[name]
        if name.endswith("_JSON"):
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        if not isinstance(value, str):
            raise RenderError(f"plain placeholder {name} requires a string value")
        return value

    rendered = PLACEHOLDER_PATTERN.sub(replace, text)
    if "{{" in rendered or "}}" in rendered:
        raise RenderError(f"unresolved or malformed placeholder in {source_name}")
    return rendered


def build_rendered_files(
    root: Path,
    values: Mapping[str, Any],
    include: Optional[Sequence[str]] = None,
) -> List[RenderedFile]:
    sources = discover_sources(root)
    selected = sorted(sources) if include is None else list(include)
    missing_sources = sorted(set(selected) - set(sources))
    if missing_sources:
        raise RenderError(
            "included template sources do not exist: " + ", ".join(missing_sources)
        )
    known_placeholders = all_placeholder_names(root)
    unknown_values = sorted(set(values) - known_placeholders)
    if unknown_values:
        raise RenderError(
            "context contains unknown placeholder values: " + ", ".join(unknown_values)
        )

    rendered_files: List[RenderedFile] = []
    targets: Set[PurePosixPath] = set()
    for source_name in selected:
        path = sources[source_name]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RenderError(f"cannot read UTF-8 template {path}: {exc}") from exc
        target = target_name_for(source_name)
        if target in targets or target == STATE_PATH:
            raise RenderError(f"duplicate or reserved rendered target: {target}")
        targets.add(target)
        rendered = render_text(text, values, source_name)
        rendered_files.append(
            RenderedFile(source_name, target, rendered.encode("utf-8"))
        )
    return rendered_files


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def context_sha256(values: Mapping[str, Any], include: Optional[Sequence[str]]) -> str:
    canonical = json.dumps(
        {"include": sorted(include) if include is not None else None, "values": values},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(canonical)


def with_state_manifest(
    files: Sequence[RenderedFile],
    values: Mapping[str, Any],
    include: Optional[Sequence[str]],
) -> List[RenderedFile]:
    entries = [
        {
            "sha256": sha256(item.content),
            "source": item.source,
            "target": item.target.as_posix(),
        }
        for item in sorted(files, key=lambda item: item.target.as_posix())
    ]
    manifest = {
        "context_sha256": context_sha256(values, include),
        "files": entries,
        "template_version": template_version(),
    }
    content = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    return list(files) + [RenderedFile("<generated-state>", STATE_PATH, content)]


def classify_files(
    target_root: Path, files: Sequence[RenderedFile]
) -> List[Tuple[str, RenderedFile]]:
    if target_root.is_symlink():
        raise RenderError(f"target root must not be a symbolic link: {target_root}")
    if target_root.exists() and not target_root.is_dir():
        raise RenderError(f"target is not a directory: {target_root}")
    classifications: List[Tuple[str, RenderedFile]] = []
    for item in sorted(files, key=lambda entry: entry.target.as_posix()):
        target = target_root.joinpath(*item.target.parts)
        current = target_root
        for part in item.target.parts:
            current = current / part
            if current.is_symlink():
                raise RenderError(
                    f"refusing rendered path through symbolic link: {current}"
                )
        if not target.exists():
            status = "create"
        elif not target.is_file():
            status = "conflict"
        else:
            try:
                status = "unchanged" if target.read_bytes() == item.content else "conflict"
            except OSError as exc:
                raise RenderError(f"cannot inspect target {target}: {exc}") from exc
        classifications.append((status, item))
    return classifications


def write_new_files(
    target_root: Path, classifications: Sequence[Tuple[str, RenderedFile]]
) -> None:
    conflicts = [
        item.target.as_posix()
        for status, item in classifications
        if status == "conflict"
    ]
    if conflicts:
        raise RenderError(
            "refusing to overwrite non-identical targets: " + ", ".join(conflicts)
        )

    try:
        write_exclusive(target_root, (
            (item.target.as_posix(), item.content)
            for status, item in classifications if status == "create"
        ))
    except SafePathError as exc:
        raise RenderError(str(exc)) from exc


def render_project(
    context_path: Path,
    target_root: Path,
    write: bool,
    root: Optional[Path] = None,
) -> List[Tuple[str, RenderedFile]]:
    if target_root.is_symlink():
        raise RenderError(f"target root must not be a symbolic link: {target_root}")
    # Resolve trusted parent aliases once, before discovery. Never resolve a
    # rendered path or re-resolve the root after classification.
    target_root = target_root.absolute()
    target_root = target_root.parent.resolve() / target_root.name
    actual_root = root if root is not None else source_root()
    values, include = load_context(context_path)
    rendered = build_rendered_files(actual_root, values, include)
    files = with_state_manifest(rendered, values, include)
    classifications = classify_files(target_root, files)
    conflicts = [
        item.target.as_posix()
        for status, item in classifications
        if status == "conflict"
    ]
    if conflicts:
        raise RenderError(
            "refusing to overwrite non-identical targets: " + ", ".join(conflicts)
        )
    try:
        validate_rendered(files, actual_root, target_root)
    except ValidationError as exc:
        raise RenderError(str(exc)) from exc
    if write:
        write_new_files(target_root, classifications)
    return classifications


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render approved Codex project files without overwriting conflicts."
    )
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        classifications = render_project(
            context_path=args.context,
            target_root=args.target.absolute(),
            write=args.write,
        )
    except (RenderError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    mode = "write" if args.write else "dry-run"
    print(f"mode: {mode}")
    for status, item in classifications:
        print(f"{status}: {item.target.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
