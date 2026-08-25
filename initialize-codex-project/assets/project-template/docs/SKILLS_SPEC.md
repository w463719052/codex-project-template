# Repository Skills Specification

Repository skills live at `.agents/skills/<skill-name>/SKILL.md`.

The baseline skills are `context-discovery`, `build-and-test`, and
`code-review`. Keep discovery and command selection read-only; neither grants
execution or write authorization.

Each skill must define a discriminating trigger, non-trigger cases, required
inputs, authority documents, workflow, stopping and reapproval conditions,
observable acceptance, applicable verification, and expected output. It must not
expand user authorization or duplicate the full project documentation.

- Use lowercase letters, digits, and hyphens; keep names below 64 characters.
- Keep `SKILL.md` concise; add references/scripts/assets only for concrete recurring value.
- Validate frontmatter, folder/name agreement, descriptions, references, scripts, and unfinished placeholders.
- Keep ordinary automatic discovery unless explicit-only invocation is specifically requested.
- Create domain skills only after the workflow is stable and repeated.
- Test direct triggers, indirect triggers, missing inputs, non-triggers, safe
  counterexamples, boundary violations, and expected output quality.
- Prefer deterministic scripts for repeatable mechanical checks. Scripts must be
  documented, reviewable, dependency-minimal, and safe by default.
