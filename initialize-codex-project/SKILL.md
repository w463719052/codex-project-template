---
name: initialize-codex-project
description: Initialize or deliberately update a repository's Codex guidance from verified project evidence. Generate lightweight instructions by default; add routing and project skills only when selected. Do not use for ordinary feature work.
---

# Initialize Codex Project

Create only the guidance this target needs. Preserve existing work and authority;
do not import another project's commands, device identifiers, preferences, or
specialized skills. Initialization does not authorize application, dependency,
CI/build, history, or external changes.

## Discover the selected output

Inspect starting `git status --short`, applicable instructions, source/test
entrypoints, build/CI commands, and existing target files. Search narrowly; collect
only evidence needed for the selected artifacts. Record unknowns as named gaps.

Default `minimal` produces four guidance files plus the automatic state manifest:

- `AGENTS.md`: authority, project paths, constraints, and task navigation.
- `docs/CODEX_WORKFLOW.md`: scope, authorization, verification, and handoff.
- `docs/CODING_STANDARDS.md`: applicable language profiles and target constraints.
- `docs/VERIFICATION.md`: verified commands, evidence, and applicability.

No routing JSON, project skills, provenance fingerprints, or task logs are
required for this default. Keep project facts concise and link existing authority
rather than duplicate it. Never require a full repository inventory just to
initialize a small project.

For changed-code standards, read `references/engineering-standards/BASELINE.md`
and only the profiles selected from target language/build evidence. If language
scope is unclear, use the read-only selector:

```text
python3 -B <skill-directory>/scripts/select_language_profiles.py --project-root <repository>
```

For polyglot targets, `--scope <relative-module>` and `--role` can narrow evidence.
Review ambiguity and truncation before declaring a profile inapplicable. Record
applicable baseline rules, source links, enforcement paths, and conflicts in the
generated standards so they are usable without this initializer installed.
Industry baselines guide new/materially changed code; verified build, security,
privacy, compatibility, and public contracts remain hard constraints. Framework
rules need target evidence. Propose conflicting configuration migration separately.

## Filter content before rendering

Keep the entrypoint to verified key paths, hard constraints, and reading triggers.
Aim for at most 60 rendered lines; remove duplication and reference existing
project documents before expanding it. Do not create another document just to
move text out, or discard necessary constraints/gaps to meet a length target.

Preserve the template's core engineering rules: readable code, useful maintained
comments, thorough task reasoning with proportionate implementation, and best-fit
technology within verified compatibility requirements. Keep their full wording
in coding standards; do not duplicate it across generated documents.

For coding guidance, cite enforcement configuration instead of copying its rules.
Summarize applicable industry baselines; retain project-specific compatibility
limits and evidenced recurring mistakes. Each retained rule should identify its
scope and the decision it changes. Do not copy entire profiles or replace the
industry baseline with legacy habits. Generic advice adds no value by itself.

Use existing command/evidence fields to associate each exact command with the
changed paths or behavior that require it, its repository/CI source, prerequisites,
and side effects. Use the validation matrix for escalation to consumer/integration
checks; do not repeat commands in it. Unknown applicability stays a named gap.
Never populate a command from a generic example or merely infer it is runnable.

## Select extensions only when needed

Use explicit `preset: "core"` for projects needing maintained module/verification
routes and context-discovery, build-and-test, and code-review skills. It retains
17 template files. `full` selects all 24; choose it only when every optional
document is justified. Use `include` for an exact source list, never with `preset`.

For these extensions, inspect existing metadata/skills and collect module paths,
contracts, consumers, tests, exclusion/budget choices, and evidenced commands.
Routing tools select candidates; they do not authorize or execute checks.
Optional provenance/auditing is for requested maintenance, not daily discovery.
Do not automatically promote a complex reference project's configuration into
the default. Architecture, shared-library, and domain skills need demonstrated use.

## Propose, render, verify

Apply `GATE-01`/`GATE-02`: declare a bounded L1 change before editing; L2 requires
one approved directory plan; L3/L4 require explicit approval of exact files,
contracts, consumers, impact, risks, and checks. L4 also needs rollback and
operational/owner evidence. Use the higher class if uncertain. Stop before
unapproved scope or protected-boundary changes. Preserve existing work under
`WORKTREE-01`; do not reset, clean, overwrite, commit, or rewrite history.

Use `assets/project-template/` and supply only placeholders required by the
selected sources, from verified evidence or explicit gaps. Known unused values
remain accepted for older contexts. No new configuration is needed for minimal.
Files ending in `.template` lose that suffix; sources under `skills/` render under
`.agents/skills/`. Do not leave placeholders or invent target commands.

```text
python3 -B <skill-directory>/scripts/render_template.py --context <context.json> --target <repository> --dry-run
python3 -B <skill-directory>/scripts/render_template.py --context <context.json> --target <repository> --write
```

Approve the dry-run's complete file list before `--write`. Omitted `preset` means
minimal in 3.0.0; explicitly set core to retain the earlier output set. Actual
schema/reference validation and exclusive POSIX writes protect generated output.
For non-identical existing files, propose a focused merge; never bypass collisions
or remove existing files because they are absent from a smaller preset.

Before handoff, review entrypoint scope, actionable coding rules, command
applicability, and task-local reuse. Report actual entrypoint line count and
unresolved gaps once at initialization; this is not a daily checklist. Template
validation uses a fixed synthetic sample (60 entrypoint lines, 10,000 guidance
bytes) to catch growth, not to truncate necessary target facts.
With the approved checks, validate templates, review generated references and
placeholders, and compare diff/status against the starting state. Application
builds/tests are not needed for guidance-only initialization unless requested.
Report created files, evidence/gaps, pass/fail/not-run, and daily entrypoints.
Ordinary use is: describe the task, follow the scoped workflow, run relevant
checks, review the diff. No mandatory skill chain or persistent task record.

## Requested maintenance

The template defines defaults; initialization discovers project facts. Later
changes require evidence and matching authorization. Do not learn preferences
in the background, persist observations without confirmation, or synchronize
project customizations back into this template automatically.

Use `scripts/report_upgrade.py --target <repository>` to inspect baseline drift;
add `--context <verified-context.json>` only for candidate comparison. It never
merges or deletes; missing old contents prevent a safe three-way merge claim.

Use `references/ab-study-protocol.md` only for a requested real workflow experiment.
Examples and static bytes are not measured model token savings. Do not start
model sessions from an ordinary initialization request.
