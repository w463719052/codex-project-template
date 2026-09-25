#!/usr/bin/env python3
"""Report target drift and optional candidate changes; never merge or write."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys
import json

from render_template import (
    STATE_PATH, build_rendered_files, load_context, source_root, target_name_for,
    template_version, RenderError,
)
from render_validation import ValidationError, strict_json, validate_rendered
from safe_paths import SafePathError, relative_parts


class UpgradeError(RuntimeError):
    """A manifest or target cannot be inspected safely."""


def read_target(root, relative):
    current = root
    if root.is_symlink() or not root.is_dir():
        raise UpgradeError("target must be an existing non-symlink directory")
    for part in relative_parts(relative):
        current = current / part
        if current.is_symlink():
            raise UpgradeError(f"refusing symbolic-link target: {relative}")
    if not current.exists():
        return None
    if not current.is_file():
        raise UpgradeError(f"target is not a regular file: {relative}")
    return current.read_bytes()


def validate_manifest(raw):
    if not isinstance(raw, dict) or set(raw) != {"template_version", "context_sha256", "files"}:
        raise UpgradeError("state manifest has missing or unknown fields")
    if not isinstance(raw["template_version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", raw["template_version"]):
        raise UpgradeError("invalid state template version")
    def digest(value):
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
    if not digest(raw["context_sha256"]) or not isinstance(raw["files"], list):
        raise UpgradeError("invalid state context hash or files")
    seen = set()
    for item in raw["files"]:
        if not isinstance(item, dict) or set(item) != {"source", "target", "sha256"}:
            raise UpgradeError("invalid manifest file entry")
        for key in ("source", "target"):
            if not isinstance(item[key], str):
                raise UpgradeError(f"manifest {key} must be a relative path")
            relative_parts(item[key])
        if item["target"] == STATE_PATH.as_posix() or item["target"] in seen:
            raise UpgradeError("duplicate or reserved target in manifest")
        if target_name_for(item["source"]).as_posix() != item["target"]:
            raise UpgradeError("manifest source/target mapping mismatch")
        if not digest(item["sha256"]):
            raise UpgradeError("invalid file hash in manifest")
        seen.add(item["target"])
    return raw


def report_upgrade(root, context_path=None):
    content = read_target(root, STATE_PATH.as_posix())
    if content is None:
        raise UpgradeError("missing template state; do not infer an initialization baseline")
    manifest = validate_manifest(strict_json(content.decode("utf-8"), "template state"))
    baseline = {item["target"]: item for item in manifest["files"]}
    candidates = None
    if context_path is not None:
        values, include = load_context(context_path)
        files = build_rendered_files(source_root(), values, include)
        validate_rendered(files, source_root(), root)
        candidates = {item.target.as_posix(): item for item in files}
    results = []
    targets = set(baseline) | (set(candidates) if candidates is not None else set())
    for target in sorted(targets):
        current = read_target(root, target)
        actual = hashlib.sha256(current).hexdigest() if current is not None else None
        old = baseline.get(target, {}).get("sha256")
        candidate = candidates.get(target) if candidates is not None else None
        new = hashlib.sha256(candidate.content).hexdigest() if candidate is not None else None
        if old is None:
            status = "new" if actual is None else "already-current" if actual == new else "unmanaged-conflict"
        elif actual is None:
            status = "missing"
        elif candidates is not None and candidate is None:
            status = "not-selected"
        elif new is not None and actual == new and actual != old:
            status = "already-current"
        elif actual != old:
            status = "both-changed" if new is not None and new != old else "target-modified"
        else:
            status = "template-changed" if new is not None and new != old else "unchanged"
        results.append({"target": target, "status": status, "baseline_sha256": old,
                        "current_sha256": actual, "candidate_sha256": new})
    return {
        "schema_version": 1, "mode": "candidate-comparison" if candidates is not None else "drift-only",
        "baseline_version": manifest["template_version"],
        "candidate_version": template_version() if candidates is not None else None,
        "files": results, "execution_authorized": False,
        "note": "Read-only hashes, not a merge. Unlisted target files are untouched; not-selected never means delete. Old source contents are not available for three-way merging.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--context", type=Path, help="Verified candidate context; omit for drift only")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(report_upgrade(args.target.absolute(), args.context), indent=2, sort_keys=True))
        return 0
    except (UpgradeError, RenderError, ValidationError, SafePathError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
