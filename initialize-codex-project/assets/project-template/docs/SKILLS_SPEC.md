# Repository Skills Specification

Repository skills live at `.agents/skills/<skill-name>/SKILL.md`.

Each skill must define a discriminating trigger, required inputs, authority documents, workflow, stopping conditions, observable acceptance, applicable verification, and expected output. It must not expand user authorization or duplicate the full project documentation.

- Use lowercase letters, digits, and hyphens; keep names below 64 characters.
- Keep `SKILL.md` concise; add references/scripts/assets only for concrete recurring value.
- Validate frontmatter, folder/name agreement, descriptions, references, scripts, and unfinished placeholders.
- Keep ordinary automatic discovery unless explicit-only invocation is specifically requested.
- Create domain skills only after the workflow is stable and repeated.
