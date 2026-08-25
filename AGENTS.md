# Codex Project Template Agent Instructions

This repository packages a reusable Codex-first project initializer. Keep the
repository skill, generated templates, deterministic tooling, tests, and README
consistent with one another.

## Authority and scope

- The user's latest explicitly approved plan is the implementation boundary.
- `initialize-codex-project/SKILL.md` defines initializer behavior.
- `initialize-codex-project/assets/project-template/` defines generated output.
- `initialize-codex-project/references/engineering-standards/` defines the
  reviewed industry language baselines available for target selection.
- `README.md` documents installation and operator-facing usage.
- If these sources conflict or required project evidence is missing, stop and
  report the conflict instead of choosing a rule by timestamp or assumption.

## Approval gate

Use these stable rule IDs in plans, templates, reviews, and validation results:

- `GATE-01`: before editing, report files, behavior, non-goals, risks, and
  verification; write only after explicit approval of that exact plan.
- `GATE-02`: stop for renewed approval before any unlisted file/module,
  dependency, CI/build/config change, public contract, external action, or
  newly discovered scope.
- `WORKTREE-01`: preserve existing work; never reset, clean, overwrite, commit,
  rewrite history, or reformat unrelated files.
- `EVIDENCE-01`: derive target-specific facts and commands from verified target
  evidence; derive industry baselines only from reviewed primary sources; record
  unknowns and conflicts as documentation gaps.
- `CONTEXT-01`: start from `.agents/ai/project-map.json`, use bounded context,
  and expand only for a named evidence trigger.
- `MODULE-01`: preserve documented responsibilities, public contracts,
  dependency direction, consumers, and shared-library gates.
- `VERIFY-01`: select only evidenced, scope-relevant checks; execution remains
  separately authorized, and not-run never means pass.

## Repository invariants

- Apply `WORKTREE-01` throughout the task.
- Do not modify any target business repository while developing this template.
- Apply `EVIDENCE-01`; never import this repository's project decisions into a
  generated target.
- Select language profiles from target path/build evidence. For new and
  materially changed code, industry baselines are the preferred engineering
  standard while verified build, compatibility, security/privacy, and public-
  contract requirements remain hard constraints.
- If substantially the same manual correction appears at least three times or
  recurs across tasks, require a recorded candidate and an approved rule or
  automation replacement; never expand silently into config or history migration.
- Files ending in `.template` render without that suffix. Files below template
  `skills/` render below target `.agents/skills/`.
- All template placeholders must be supplied by verified discovery or an
  explicitly recorded documentation gap. Generated output must contain none.
- Rendering must be dry-run-first, collision-safe, deterministic, and must not
  overwrite non-identical target files.
- Keep `AGENTS.md` concise. Put detailed workflow, architecture, coding,
  verification, and library guidance in the referenced documents.

## Verification

Run after relevant changes:

```text
python3 -B initialize-codex-project/scripts/validate_templates.py
python3 -B -m unittest discover -s tests -v
python3 -B initialize-codex-project/scripts/benchmark_routing.py
git diff --check
git status --short
```

Review the complete diff and report pass, fail, or not-run for every applicable
check. A build is not a test, and a command not run is not a pass.

## Code review rules

- Treat an approval-gate bypass, target-file overwrite, unresolved placeholder,
  invented target command, or incorrect rendered path as a blocking defect.
- Trace template changes through the renderer, tests, generated file map,
  README, language-profile catalog, and target-facing skills.
- Prefer deterministic validation for mechanical rules; reserve agent guidance
  for contextual decisions that cannot be encoded reliably.
