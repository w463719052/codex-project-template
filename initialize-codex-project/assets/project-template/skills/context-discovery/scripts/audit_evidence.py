#!/usr/bin/env python3
"""Audit optional source fingerprints without executing commands or updating metadata."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


class EvidenceError(RuntimeError):
    """Evidence metadata is malformed or unsafe."""


def relative_path(value):
    if not isinstance(value, str) or not value:
        raise EvidenceError("provenance path must be a non-empty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or any(c in value for c in "\\:\x00"):
        raise EvidenceError(f"unsafe provenance path: {value!r}")
    return path


def validate_provenance(value):
    if not isinstance(value, list):
        raise EvidenceError("provenance must be an array")
    allowed = {"path", "sha256", "verified_at", "scope", "environment", "prerequisites"}
    for item in value:
        if not isinstance(item, dict) or "path" not in item or set(item) - allowed:
            raise EvidenceError("provenance entry requires path and only known fields")
        relative_path(item["path"])
        if "sha256" in item and (not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])):
            raise EvidenceError("provenance sha256 must be 64 lowercase hex characters")
        if "verified_at" in item:
            try:
                if not isinstance(item["verified_at"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["verified_at"]):
                    raise ValueError("expected YYYY-MM-DD")
                date.fromisoformat(item["verified_at"])
            except ValueError as exc:
                raise EvidenceError(f"invalid provenance verified_at: {exc}") from exc
        for field in ("scope", "environment"):
            if field in item and (not isinstance(item[field], str) or not item[field].strip()):
                raise EvidenceError(f"provenance {field} must be non-blank text")
        if "prerequisites" in item and (not isinstance(item["prerequisites"], list) or not all(
            isinstance(entry, str) and entry.strip() for entry in item["prerequisites"]
        )):
            raise EvidenceError("provenance prerequisites must be a string array")
    return value


def fingerprint(root, relative):
    current = root
    if current.is_symlink() or not current.is_dir():
        raise EvidenceError("project root must be a real directory")
    for part in relative_path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise EvidenceError(f"symbolic-link evidence rejected: {relative}")
    if not current.exists():
        return None
    if not current.is_file():
        raise EvidenceError(f"evidence is not a regular file: {relative}")
    digest = hashlib.sha256()
    with current.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_document(root, document, source="metadata"):
    if not isinstance(document, dict):
        raise EvidenceError("metadata must be an object")
    results = []
    for collection in ("commands", "modules"):
        records = document.get(collection, [])
        if not isinstance(records, list):
            raise EvidenceError(f"{collection} must be an array")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                raise EvidenceError(f"{collection} records require an id")
            provenance = validate_provenance(record.get("provenance", []))
            prefix = {"source": source, "collection": collection, "id": record["id"]}
            if not provenance:
                results.append({**prefix, "status": "unverified", "reason": "no source fingerprint recorded"})
            for item in provenance:
                actual = fingerprint(root, item["path"])
                status = "missing" if actual is None else "unverified" if "sha256" not in item else "current" if actual == item["sha256"] else "stale"
                results.append({**prefix, **item, "actual_sha256": actual, "status": status})
    return {
        "schema_version": 1, "evidence": results, "execution_authorized": False,
        "note": "Current means source bytes match; it does not verify command success, environment, or semantic accuracy.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--metadata", action="append", help="Repository-relative map/routes path; repeatable")
    args = parser.parse_args(argv)
    try:
        root = args.project_root.absolute()
        paths = args.metadata or [".agents/ai/project-map.json", ".agents/ai/verification-routes.json"]
        reports = []
        for path in paths:
            if fingerprint(root, path) is None:
                raise EvidenceError(f"missing metadata: {path}")
            document = json.loads(root.joinpath(*relative_path(path).parts).read_text())
            reports.append(audit_document(root, document, path))
        print(json.dumps({"reports": reports, "execution_authorized": False}, indent=2, sort_keys=True))
        return 1 if any(item["status"] in {"stale", "missing"} for report in reports for item in report["evidence"]) else 0
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
