# Codex-first Workflow

This is the sole canonical definition of task classes and authorization.

## Scope and authorization (`GATE-01`)

Inspect the task, applicable instructions, starting status, and relevant evidence
before editing. State scope and checks in the conversation by default; scale
analysis to the task. Persistent records are opt-in.

- **L1 — bounded local change.** Exact files in one module, preserving public
  contracts, schemas, dependencies, build/CI/configuration, persistent data,
  security/privacy, deployment, and external state. A direct implementation
  request authorizes the declared scope and verified non-mutating checks.
  Questions and review requests do not authorize edits.
- **L2 — module or directory change.** Obtain one approval for goal, directory
  boundaries, protected exclusions, risks, and checks. Discover files within
  those boundaries as needed.
- **L3 — cross-module or contract-sensitive change.** Obtain explicit approval
  of exact files, consumers, contracts, impact, non-goals, risks, gaps, and checks.
- **L4 — architecture, security/privacy, migration, destructive, external, or
  high-cost failure change.** Use L3 plus rollback, operational, and owner evidence;
  obtain explicit approval of that plan.

Use the higher class when uncertain. Before approval, investigate read-only and
prepare the proposal; do not modify files/configuration or external state.
Reuse approval while its goal, scope, commands, prerequisites, and protected
boundaries remain unchanged; do not ask again for the same authorization.

Reuse already-read guidance and established scope while available and unchanged.
Reread only relevant parts when rules change, a new module/boundary is involved,
evidence conflicts, or context is lost. Reestablish missing scope/authorization;
never assume it or skip new constraints to save tokens. This guides task-local
reading, not client injection or background memory.

## Work within scope

- `WORKTREE-01`: preserve existing changes; never reset, clean, overwrite, commit,
  rewrite history, or reformat unrelated files.
- `EVIDENCE-01`: verify project facts and commands from repository evidence;
  record unknowns as documentation gaps. Do not install tools for discovery.
- `CONTEXT-01`: start with task paths, applicable authority, callers, contracts,
  and tests. Search before reading. Expand only for a named missing dependency
  or evidence gap. Use an installed project map for unfamiliar work; no map is
  required for direct bounded discovery.
- `MODULE-01`: preserve responsibilities, dependency direction, contracts,
  consumers, and documented shared-library gates. No speculative extraction.
- Apply selected language baselines in `docs/CODING_STANDARDS.md` to changed
  source; preserve verified build, compatibility, security/privacy, and public
  contracts. Keep tests proportional to behavior changes.

## Expansion (`GATE-02`)

Stop before an L1 declaration no longer holds, L2 leaves approved directories or
behavior, or L3/L4 touches unlisted scope. Every class requires renewed approval
for an unapproved public contract/schema, dependency, build/CI/configuration,
security/privacy, destructive/external action, migration, or unrelated cleanup.
Explain the new evidence, affected files/consumers, alternatives, risks, and
changed verification before continuing.

## Verify and hand off

`VERIFY-01`: follow `docs/VERIFICATION.md`. Selection is not execution permission;
use L1 authorization or the approved L2-L4 checks. Build is not a test, and
not-run never means pass. Report environment failures separately from defects.
Review the relevant diff/status against the starting state and run
`git diff --check`. Report the outcome, checks, remaining gaps, and material risk.
Review-only requests do not authorize fixes.

`ADAPT-01`: after three evidenced explicit operator choices, or substantially
the same manual correction in three places or across tasks, propose a scoped
rule candidate in conversation. Wait for confirmation before recording or
synchronizing it; never weaken protected boundaries from habits. Rule, tool,
configuration, and historical migrations still use the matching approval gate.

Use multiple agents or worktrees only when explicitly allowed and their scopes
are independent. Integration and verification remain the task owner's duty.
