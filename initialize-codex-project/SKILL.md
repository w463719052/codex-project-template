---
name: initialize-codex-project
description: Initialize or adapt a repository-specific Codex-first workflow by inspecting the actual project and creating AGENTS.md, workflow docs, verification guidance, and baseline build-and-test and code-review skills. Use for new repositories or deliberate workflow upgrades; do not use for ordinary feature implementation.
---

# Initialize Codex Project

Create a project-specific workflow from evidence, not from assumptions. This skill may create documentation and repository skills; it does not authorize changes to application code, dependencies, CI, build configuration, Git history, or external systems.

## Inputs

Determine the target repository root and the user's requested scope. Before writing, inspect:

- existing `AGENTS.md` or overrides, contributor/readme/architecture/product documents;
- languages, frameworks, source and test directories;
- package/build files, schemes/targets, test runners, formatters, linters, CI, and generated paths;
- `git status --short`, including pre-existing user changes;
- existing `.agents/skills` and naming conflicts.

Use the files under `assets/project-template/` as structural templates. Replace every
`{{PLACEHOLDER}}` with verified project data or remove the inapplicable section. Never leave a placeholder in generated output.
Files ending in `.template` must be rendered without that suffix. Render
`assets/project-template/skills/<name>/SKILL.md.template` to
`<target>/.agents/skills/<name>/SKILL.md`; do not copy the intermediate `skills/` directory into the target root.

## Workflow

1. **Report before writing.** Summarize detected stack, authoritative documents, confirmed commands, missing evidence, existing-file conflicts, proposed files, and non-goals.
2. **Choose scope.** Generate only useful files. Preserve an existing instruction system; propose a focused merge instead of replacing it.
3. **Render project files.** Keep `AGENTS.md` concise. Put detailed execution and verification guidance in docs. Create repository skills at `.agents/skills/<name>/SKILL.md`.
4. **Confirm commands.** Prefer commands already used by CI or repository scripts. A help/list/dry-run command may confirm names. Do not install tools or mutate configuration to validate discovery.
5. **Verify.** Check all referenced paths, scan for placeholders, validate each generated skill, run `git diff --check`, and review status/diff. Run application builds or tests only when the user requests them or when the initialization also changes executable behavior.

## Required behavior

- If the target has uncommitted changes, preserve them and keep generated changes distinguishable.
- If a required product or coding decision is unknown, leave a clearly named documentation gap; do not invent policy.
- Generic workflow rules may be reused, but language-, framework-, architecture-, privacy-, product-, deployment-, and command-specific rules must come from the target.
- `build-and-test` must report pass/fail/not-run and must not equate build with tests.
- `code-review` must default to review-only behavior and findings-first output.
- Do not create domain skills until a repeated, stable project workflow justifies them.

## Completion

Report created/updated files, evidence used for commands, validation results, unresolved gaps, and the exact daily usage:

```text
Define task → use the matching project skill → $build-and-test → $code-review
```
