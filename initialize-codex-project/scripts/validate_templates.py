#!/usr/bin/env python3
"""Validate template structure, rendering, paths, references, and skills."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence

from render_template import (
    CORE_SOURCES,
    PLACEHOLDER_PATTERN,
    STATE_PATH,
    RenderError,
    RenderedFile,
    all_placeholder_names,
    build_rendered_files,
    classify_files,
    discover_sources,
    load_context,
    skill_root,
    source_root,
    target_name_for,
    template_version,
    with_state_manifest,
    write_new_files,
)


EXPECTED_SOURCES = {
    ".agents/ai/project-map.json.template",
    ".agents/ai/verification-routes.json.template",
    "AGENTS.md.template",
    "docs/ADR_TEMPLATE.md",
    "docs/ARCHITECTURE.md.template",
    "docs/AI_CONTEXT_STRATEGY.md.template",
    "docs/AI_PERFORMANCE_BUDGET.md.template",
    "docs/CHANGE_IMPACT.md",
    "docs/CODEX_USAGE.md.template",
    "docs/CODEX_WORKFLOW.md",
    "docs/CODING_RULES_LOG.md.template",
    "docs/CODING_STANDARDS.md.template",
    "docs/LIBRARY_DOCUMENTATION_TEMPLATE.md",
    "docs/MODULE_MAP.md.template",
    "docs/SHARED_LIBRARY_STANDARD.md",
    "docs/SKILLS_SPEC.md",
    "docs/TASK_TEMPLATE.md.template",
    "docs/VERIFICATION.md.template",
    "skills/build-and-test/SKILL.md.template",
    "skills/build-and-test/scripts/select_checks.py",
    "skills/code-review/SKILL.md.template",
    "skills/context-discovery/SKILL.md.template",
    "skills/context-discovery/scripts/build_context_pack.py",
}
EXPECTED_ENGINEERING_PROFILE_REFERENCES = {
    "BASELINE.md",
    "c.md",
    "catalog.json",
    "cpp.md",
    "go.md",
    "java.md",
    "kotlin.md",
    "objective-c.md",
    "python.md",
    "rust.md",
    "swift.md",
    "typescript-javascript.md",
    "web-frontend.md",
}
REQUIRED_PROFILE_HEADINGS = {
    "## Authority sources",
    "## Naming and API design",
    "## Architecture and dependencies",
    "## Control flow and decomposition",
    "## Errors, concurrency, and resources",
    "## Testing and enforcement",
}
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
BACKTICK_PATH_PATTERN = re.compile(r"`((?:docs|\.agents)/[^`]+|AGENTS\.md)`")
ACTION_PIN_PATTERN = re.compile(
    r"uses:\s+actions/(checkout|setup-python)@([0-9a-f]{40})(?:\s|$)"
)
RULE_IDS = {
    "GATE-01",
    "GATE-02",
    "WORKTREE-01",
    "EVIDENCE-01",
    "CONTEXT-01",
    "MODULE-01",
    "VERIFY-01",
    "ADAPT-01",
}
WORKFLOW_CLASS_MARKERS = ("**L1 —", "**L2 —", "**L3 —", "**L4 —")
WORKFLOW_REFERENCE_TARGETS = (
    "AGENTS.md",
    "docs/CODEX_USAGE.md",
    "docs/TASK_TEMPLATE.md",
    "docs/CHANGE_IMPACT.md",
)


def fail(message: str) -> None:
    raise RenderError(message)


def sample_project_map() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "project_name": "Example Project",
        "budgets": {
            "max_initial_files": 4,
            "max_initial_bytes": 32768,
            "max_expansion_rounds": 2,
        },
        "excluded_paths": [".git/**"],
        "modules": [
            {
                "id": "governance",
                "paths": ["AGENTS.md", "docs/**"],
                "responsibility": "Repository governance.",
                "entrypoints": ["AGENTS.md"],
                "public_contracts": ["docs/CODEX_WORKFLOW.md"],
                "dependencies": [],
                "consumers": [],
                "tests": [],
                "authority_docs": ["AGENTS.md"],
                "generated_paths": [],
            }
        ],
        "context_routes": [
            {
                "id": "default-task",
                "task_types": ["feature"],
                "module_ids": ["governance"],
                "initial_paths": ["AGENTS.md"],
                "expand_when": ["A required contract is outside the initial pack."],
            }
        ],
        "documentation_gaps": [],
    }


def sample_verification_routes() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "commands": [
            {
                "id": "diff-check",
                "command": "git diff --check",
                "kind": "diff",
                "evidence": "docs/VERIFICATION.md#diff-checks",
                "mutates": False,
            }
        ],
        "routes": [
            {
                "id": "default-route",
                "path_patterns": ["**"],
                "focused_check_ids": ["diff-check"],
                "consumer_check_ids": [],
                "required_build_ids": [],
                "escalate_when": [],
            }
        ],
        "fallback_check_ids": ["diff-check"],
        "documentation_gaps": [],
    }


def sample_values(root: Path) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for name in sorted(all_placeholder_names(root)):
        if name == "PROJECT_MAP_JSON":
            values[name] = sample_project_map()
        elif name == "VERIFICATION_ROUTES_JSON":
            values[name] = sample_verification_routes()
        else:
            values[name] = (
                "Example Project"
                if name == "PROJECT_NAME"
                else f"Verified example for {name}."
            )
    return values


def load_script_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot load validator script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_json_loads(text: str, label: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        return json.loads(text, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RenderError(f"rendered JSON is invalid for {label}: {exc}") from exc


def parse_frontmatter(text: str, source_name: str) -> Mapping[str, str]:
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != "---":
        fail(f"skill is missing YAML frontmatter: {source_name}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise RenderError(f"skill frontmatter is not closed: {source_name}") from exc
    result: Dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            fail(f"unsupported skill frontmatter line in {source_name}: {line!r}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def validate_skills(rendered: Sequence[RenderedFile]) -> None:
    skill_count = 0
    for item in rendered:
        target = item.target
        if not (
            len(target.parts) == 4
            and target.parts[:2] == (".agents", "skills")
            and target.name == "SKILL.md"
        ):
            continue
        skill_count += 1
        folder_name = target.parts[2]
        text = item.content.decode("utf-8")
        frontmatter = parse_frontmatter(text, item.source)
        if frontmatter.get("name") != folder_name:
            fail(
                f"skill name/folder mismatch for {item.source}: "
                f"{frontmatter.get('name')!r} != {folder_name!r}"
            )
        description = frontmatter.get("description", "")
        if not description:
            fail(f"skill description is empty: {item.source}")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", folder_name):
            fail(f"invalid skill folder name: {folder_name}")
    if skill_count != 3:
        fail(f"expected 3 baseline skills, found {skill_count}")


def validate_routing_data(rendered: Sequence[RenderedFile]) -> None:
    by_target = {item.target.as_posix(): item for item in rendered}
    parsed_json = {
        target: strict_json_loads(item.content.decode("utf-8"), target)
        for target, item in by_target.items()
        if target.endswith(".json")
    }
    project_map = parsed_json[".agents/ai/project-map.json"]
    verification_routes = parsed_json[".agents/ai/verification-routes.json"]
    context_module = load_script_module(
        source_root()
        / "skills/context-discovery/scripts/build_context_pack.py",
        "validate_context_pack_asset",
    )
    checks_module = load_script_module(
        source_root() / "skills/build-and-test/scripts/select_checks.py",
        "validate_select_checks_asset",
    )
    try:
        context_module.validate_project_map(project_map)
        checks_module.validate_verification_routes(verification_routes)
    except RuntimeError as exc:
        raise RenderError(f"rendered routing schema is invalid: {exc}") from exc


def validate_rule_ids(rendered: Sequence[RenderedFile]) -> None:
    by_target = {item.target.as_posix(): item for item in rendered}
    for target in ("AGENTS.md", "docs/CODEX_WORKFLOW.md"):
        text = by_target[target].content.decode("utf-8")
        missing = sorted(rule_id for rule_id in RULE_IDS if rule_id not in text)
        if missing:
            fail(f"{target} is missing stable rule IDs: {', '.join(missing)}")
    repository_agents = (skill_root().parent / "AGENTS.md").read_text(encoding="utf-8")
    missing_root = sorted(
        rule_id for rule_id in RULE_IDS if rule_id not in repository_agents
    )
    if missing_root:
        fail("repository AGENTS.md is missing rule IDs: " + ", ".join(missing_root))


def validate_workflow_authority(rendered: Sequence[RenderedFile]) -> None:
    by_target = {item.target.as_posix(): item for item in rendered}
    workflow = by_target["docs/CODEX_WORKFLOW.md"].content.decode("utf-8")
    for marker in WORKFLOW_CLASS_MARKERS:
        if workflow.count(marker) != 1:
            fail(f"canonical workflow must define {marker} exactly once")
    if "sole canonical definition" not in workflow:
        fail("workflow does not declare canonical ownership")

    for target in WORKFLOW_REFERENCE_TARGETS:
        text = by_target[target].content.decode("utf-8")
        if "docs/CODEX_WORKFLOW.md" not in text:
            fail(f"{target} does not reference the canonical workflow")
        duplicated = [marker for marker in WORKFLOW_CLASS_MARKERS if marker in text]
        if duplicated:
            fail(f"{target} duplicates canonical task-class definitions")

    task_template = by_target["docs/TASK_TEMPLATE.md"].content.decode("utf-8")
    if "## Scope-change triggers" in task_template:
        fail("task template duplicates the canonical scope-change procedure")
    change_impact = by_target["docs/CHANGE_IMPACT.md"].content.decode("utf-8")
    if "worksheet for L3/L4 tasks" not in change_impact:
        fail("change-impact worksheet is not scoped to L3/L4")


def validate_initializer_skill() -> None:
    path = skill_root() / "SKILL.md"
    frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"), str(path))
    if frontmatter.get("name") != skill_root().name:
        fail("initializer skill name does not match its directory")
    if not frontmatter.get("description"):
        fail("initializer skill description is empty")


def validate_engineering_profiles() -> None:
    root = skill_root() / "references" / "engineering-standards"
    actual = {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }
    if actual != EXPECTED_ENGINEERING_PROFILE_REFERENCES:
        missing = sorted(EXPECTED_ENGINEERING_PROFILE_REFERENCES - actual)
        extra = sorted(actual - EXPECTED_ENGINEERING_PROFILE_REFERENCES)
        fail(f"engineering profile inventory mismatch; missing={missing}, extra={extra}")

    selector = load_script_module(
        skill_root() / "scripts" / "select_language_profiles.py",
        "validate_language_profile_selector",
    )
    try:
        catalog = selector.load_catalog(root / "catalog.json")
    except RuntimeError as exc:
        raise RenderError(f"invalid engineering profile catalog: {exc}") from exc
    catalog_references = {profile["reference"] for profile in catalog["profiles"]}
    expected_references = EXPECTED_ENGINEERING_PROFILE_REFERENCES - {
        "BASELINE.md",
        "catalog.json",
    }
    if catalog_references != expected_references:
        fail("catalog references do not match the engineering profile inventory")

    by_reference = {profile["reference"]: profile for profile in catalog["profiles"]}
    for reference in sorted(expected_references):
        text = (root / reference).read_text(encoding="utf-8")
        missing_headings = sorted(REQUIRED_PROFILE_HEADINGS - set(text.splitlines()))
        if missing_headings:
            fail(f"{reference} is missing profile headings: {', '.join(missing_headings)}")
        for source in by_reference[reference]["authority_sources"]:
            if source["url"] not in text:
                fail(f"{reference} is missing authority URL: {source['url']}")

    baseline = (root / "BASELINE.md").read_text(encoding="utf-8")
    missing_baseline = sorted(REQUIRED_PROFILE_HEADINGS - set(baseline.splitlines()))
    if missing_baseline:
        fail("BASELINE.md is missing required headings: " + ", ".join(missing_baseline))


def validate_references(rendered: Sequence[RenderedFile]) -> None:
    targets = {item.target.as_posix() for item in rendered}
    for item in rendered:
        if not item.target.as_posix().endswith(".md"):
            continue
        text = item.content.decode("utf-8")
        for match in BACKTICK_PATH_PATTERN.finditer(text):
            reference = match.group(1)
            if "<" in reference or ">" in reference or "$" in reference:
                continue
            if reference.endswith("/"):
                continue
            is_generated_directory = any(
                target.startswith(reference.rstrip("/") + "/") for target in targets
            )
            if reference not in targets and not is_generated_directory:
                fail(f"broken generated reference in {item.target}: {reference}")


def validate() -> None:
    root = source_root()
    sources = discover_sources(root)
    missing = sorted(EXPECTED_SOURCES - set(sources))
    if missing:
        fail("missing required template sources: " + ", ".join(missing))
    missing_core = sorted(set(CORE_SOURCES) - set(sources))
    if missing_core:
        fail("core preset references missing sources: " + ", ".join(missing_core))

    unexpected_placeholders: List[str] = []
    for source_name, path in sources.items():
        text = path.read_text(encoding="utf-8")
        if not source_name.endswith(".template") and PLACEHOLDER_PATTERN.search(text):
            unexpected_placeholders.append(source_name)
        stripped = PLACEHOLDER_PATTERN.sub("", text)
        if "{{" in stripped or "}}" in stripped:
            fail(f"malformed placeholder braces in {source_name}")
    if unexpected_placeholders:
        fail(
            "placeholders are allowed only in .template sources: "
            + ", ".join(sorted(unexpected_placeholders))
        )

    values = sample_values(root)
    rendered = build_rendered_files(root, values)
    target_names = [item.target for item in rendered]
    if len(target_names) != len(set(target_names)):
        fail("rendered target paths are not unique")
    if STATE_PATH in target_names:
        fail(f"template source collides with reserved state path: {STATE_PATH}")
    for item in rendered:
        text = item.content.decode("utf-8")
        if "{{" in text or "}}" in text:
            fail(f"rendered output contains a placeholder: {item.target}")
        expected_target = target_name_for(item.source)
        if item.target != expected_target:
            fail(f"incorrect target mapping for {item.source}")

    validate_skills(rendered)
    validate_routing_data(rendered)
    validate_rule_ids(rendered)
    validate_workflow_authority(rendered)
    validate_initializer_skill()
    validate_engineering_profiles()
    validate_references(rendered)

    core_rendered = build_rendered_files(root, values, CORE_SOURCES)
    if {item.source for item in core_rendered} != set(CORE_SOURCES):
        fail("core preset rendered an unexpected source set")
    validate_skills(core_rendered)
    validate_routing_data(core_rendered)
    validate_rule_ids(core_rendered)
    validate_workflow_authority(core_rendered)
    validate_references(core_rendered)

    example_path = skill_root() / "examples" / "context.example.json"
    example_values, example_include = load_context(example_path)
    example_rendered = build_rendered_files(root, example_values, example_include)
    if {item.source for item in example_rendered} != set(CORE_SOURCES):
        fail("example context does not render the default core preset")

    version = template_version()
    if not SEMVER_PATTERN.fullmatch(version):
        fail(f"template VERSION is not semantic x.y.z: {version!r}")
    repository_root = skill_root().parent
    readme = (repository_root / "README.md").read_text(encoding="utf-8")
    changelog = (repository_root / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"当前模板版本：`{version}`" not in readme:
        fail("README template version is missing or out of sync")
    if f"## {version} -" not in changelog:
        fail("CHANGELOG has no entry for the current template version")
    workflow_path = repository_root / ".github" / "workflows" / "validate.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    pinned_actions = {name for name, _ in ACTION_PIN_PATTERN.findall(workflow)}
    if pinned_actions != {"checkout", "setup-python"}:
        fail("CI actions must be present and pinned to full 40-character SHAs")

    files_with_state = with_state_manifest(core_rendered, values, CORE_SOURCES)
    with tempfile.TemporaryDirectory(prefix="codex-template-validation-") as temp:
        target = Path(temp) / "target"
        classifications = classify_files(target, files_with_state)
        if any(status != "create" for status, _ in classifications):
            fail("clean render did not classify every target as create")
        write_new_files(target, classifications)
        second = classify_files(target, files_with_state)
        if any(status != "unchanged" for status, _ in second):
            fail("second identical render is not stable")

    print(
        f"validated {len(sources)} sources, {len(core_rendered)} core and "
        f"{len(rendered)} full rendered files, "
        f"{len(values)} placeholders, template version {version}"
    )


def main() -> int:
    try:
        validate()
    except (OSError, UnicodeDecodeError, RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
