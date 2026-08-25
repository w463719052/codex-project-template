---
name: initialize-codex-project
description: Initialize or adapt a repository-specific Codex-first workflow by inspecting the actual project and creating AGENTS.md, bounded context and verification routes, workflow docs, and baseline context-discovery, build-and-test, and code-review skills. Use for new repositories or deliberate workflow upgrades; do not use for ordinary feature implementation.
---

# Initialize Codex Project

Create a project-specific workflow from evidence, not assumptions. This skill
may create approved documentation and repository skills. It does not authorize
changes to application code, dependencies, CI, build configuration, Git
history, or external systems unless the user separately approves that exact
expanded scope.

## Inputs

Determine the target repository root and the user's requested scope. Before writing, inspect:

- existing `AGENTS.md` or overrides, contributor/readme/architecture/product documents;
- languages, frameworks, source and test directories;
- package/build files, schemes/targets, test runners, formatters, linters, CI, and generated paths;
- source-language extensions and build markers needed to select only applicable
  industry engineering profiles;
- `git status --short`, including pre-existing user changes;
- existing `.agents/skills` and naming conflicts.
- existing `.agents/ai/project-map.json`, verification routes, module maps, and
  representative task sizes.

Use the bundled read-only selector during discovery when source languages are
not already established by stronger target evidence:

```text
python3 -B <skill-directory>/scripts/select_language_profiles.py --project-root <repository>
```

The selector reads path metadata only, does not read source contents, never
writes, and always reports `execution_authorized: false`. Always load
`references/engineering-standards/BASELINE.md`, then review ambiguous results
and load only the selected language files. If `truncated` is true, report
selection as incomplete and expand the metadata budget before treating an
absent profile as inapplicable. The catalog records reviewed primary sources;
framework variants and target-specific constraints still require target evidence.

Record the starting status and keep it available for final comparison. Treat
unknown product, architecture, coding, security, privacy, deployment, ownership,
or command decisions as named documentation gaps.

Use the files under `assets/project-template/` as structural templates. Replace
every `{{PLACEHOLDER}}` with verified project data, an explicitly named gap, or
an explicitly approved decision. Never leave a placeholder or blank required
section in generated output. Omit an inapplicable source file through the
approved `include` list or a focused merge instead of rendering empty guidance.
Files ending in `.template` must be rendered without that suffix. Render
`assets/project-template/skills/<name>/SKILL.md.template` to
`<target>/.agents/skills/<name>/SKILL.md`; do not copy the intermediate `skills/` directory into the target root.

For `docs/CODING_STANDARDS.md`, record detected languages, selection evidence,
applicable industry profiles, existing project enforcement, and every known
conflict. New and materially changed code uses the industry profile as its
preferred engineering baseline. Verified compiler/build/CI, public-contract,
compatibility, security/privacy, and platform requirements remain hard
constraints. Record a mechanically enforced conflict and propose configuration
migration separately; never hide or bypass it.

Build `.agents/ai/project-map.json` from verified module paths, entrypoints,
contracts, dependencies, consumers, tests, authority documents, generated
paths, exclusions, and conservative file/byte/expansion budgets. Build
`.agents/ai/verification-routes.json` only from evidenced project commands.
Routing tools select context or checks; they do not read source content beyond
metadata, execute commands, or grant execution authorization.

Prefer the bundled renderer for new, non-conflicting files:

```text
python3 -B <skill-directory>/scripts/render_template.py --context <context.json> --target <repository> --dry-run
python3 -B <skill-directory>/scripts/render_template.py --context <context.json> --target <repository> --write
```

Run `--write` only after the dry-run output and complete file list are approved.
The renderer never overwrites non-identical files. For existing instruction
systems, inspect and propose a focused merge; do not bypass collision handling.

## Workflow

1. **Investigate read-only.** Detect the stack, authority documents, repository
   and module boundaries, commands and their evidence, generated paths, missing
   decisions, current status, routing metadata, selected language profiles,
   profile/project conflicts, and existing-file conflicts.
2. **Propose.** Report the exact output files, focused merges, non-goals, impact,
   risks, documentation gaps, and verification. Do not write yet.
3. **Obtain approval.** Wait for explicit approval of the proposed plan and file
   set. An initial request to initialize a project is not approval of an unseen
   plan.
4. **Render approved scope.** Generate only useful files. Keep `AGENTS.md`
   concise; put detail in docs/skills and create bounded context and verification
   routes. Validate JSON schemas before writing.
5. **Stop on expansion.** If implementation needs an unapproved file, command,
   dependency, config change, public contract, or external action, stop and
   present a scope-change request before continuing.
6. **Verify.** Run `python3 -B
   <skill-directory>/scripts/validate_templates.py`, check referenced paths and
   placeholders, validate generated skills, run `git diff --check`, and review
   status/diff against the starting state. Run application builds or tests only
   when the approved initialization changes executable behavior or the user asks.

## Required behavior

- If the target has uncommitted changes, preserve them and keep generated changes distinguishable.
- If a required product or coding decision is unknown, leave a clearly named documentation gap; do not invent policy.
- Generic workflow rules and reviewed industry language profiles may be reused.
  Framework variants, architecture, privacy, product, deployment, compatibility,
  and command-specific rules must come from verified target evidence.
- Apply selected industry profiles first to new and materially changed code;
  consider existing rules for compatibility and record conflicts. Never turn a
  focused change into an unapproved whole-repository style migration.
- Use a fixed, documented authority order. Never resolve conflicts from an
  inferred file timestamp.
- Capture module responsibilities, public contracts, dependency direction,
  callers/consumers, and change impact when evidence exists; otherwise record
  the gap for owner approval.
- Do not extract or propose a shared library merely because code looks similar.
  Apply the target's approved shared-library standard and require API, test,
  compatibility, versioning, migration, and usage documentation.
- `build-and-test` must report pass/fail/not-run and must not equate build with tests.
- `context-discovery` must remain read-only, enforce configured budgets, and
  report omissions and expansion triggers.
- Verification selection must always report `execution_authorized: false`;
  executing a selected command is a separate approved step.
- `code-review` must default to review-only behavior and findings-first output.
- When the same manual correction appears in at least three places or recurs
  across tasks, record or propose a candidate in `docs/CODING_RULES_LOG.md` and
  prefer an approved formatter, linter, static check, template, generator, or
  test for mechanical enforcement. Rule/config/history changes remain gated.
- Do not create domain skills until a repeated, stable project workflow justifies them.

## Completion

Report created/updated files, approved-scope compliance, evidence used for
commands, validation results, unresolved gaps, and the exact daily usage:

```text
Define task → bounded discovery if needed → approve plan → use the matching skill → $build-and-test → $code-review
```
