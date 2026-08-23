# Codex-first Workflow

## Understand

Read `AGENTS.md`, the task, relevant authority documents, status, implementation entrypoints, tests, and build configuration. State goal, non-goals, assumptions, compatibility, risks, and observable completion criteria.

## Plan

Plan first when the task crosses architectural boundaries, changes public contracts/data schemas/concurrency/security/dependencies, affects several production files, contains ambiguity, or has costly failure modes. Each step must name its output and verification.

Direct execution is acceptable for small, local, unambiguous changes with known validation. It still requires Understand, Verify, and Review Diff.

## Execute

- Make the smallest coherent change.
- Update tests with behavior.
- Preserve dependency direction and existing user work.
- Stop and re-plan when assumptions fail, scope expands, or changes overlap unresolved work.
- Run the smallest relevant check after each meaningful stage.

## Verify

Follow `docs/VERIFICATION.md`. A command not run is not a pass. Separate implementation failures from environment failures and report both precisely.

## Review Diff

Run `git diff --check`, inspect relevant diff/stat/status, confirm no generated/secrets/private/unrelated files, and trace changed behavior through its consumers. Report changes, evidence, unverified items, and residual risk.

## Parallel work

Use multiple agents or worktrees only when interfaces are stable, write scopes do not overlap, and parallelism has clear value. The integrating agent owns final diff review and repository-level verification.
