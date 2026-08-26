# Codex-first Workflow

This is the canonical approval state machine. Other documents reference its
rule IDs instead of restating the gate.

## 1. Investigate read-only

Read `AGENTS.md`, the task, starting status, and the smallest relevant evidence
set. For large or unfamiliar work, apply `CONTEXT-01` with `$context-discovery`.
Inspect implementation entrypoints, callers/consumers, contracts, tests, and
verification evidence. Apply `EVIDENCE-01`: record unknown target facts as
documentation gaps instead of guessing.
For source changes, identify each affected language/module, read its selected
industry profile in `docs/CODING_STANDARDS.md`, and compare it with existing
project conventions and mechanical enforcement. Treat unresolved profile or
rule conflicts as proposal inputs, not silent implementation choices.
State the goal, non-goals, assumptions, compatibility, risks, documentation
gaps, and observable completion criteria. Do not modify files or external state.

## 2. Classify and declare the scope

Use `docs/TASK_TEMPLATE.md` and `docs/CHANGE_IMPACT.md`. Name every proposed
file/module, behavior and contract change, verification command, non-goal, and
known risk. For each command, cite its repository or CI evidence.

Apply the most conservative matching class:

- **L1 — bounded local change.** The exact source/test/doc files are known, the
  change stays in one module, and it preserves public contracts, schemas,
  dependencies, build/CI/configuration, persistent data, security/privacy,
  deployment, and external state. A direct request to implement, fix, or modify
  authorizes the agent to declare this scope concisely and proceed. Questions,
  diagnosis, review, or status requests do not authorize writes.
- **L2 — approved module or directory change.** The behavior is bounded but
  implementation may discover or add files inside explicitly approved
  directories. Present the goal, directory boundaries, protected exclusions,
  risks, and verification, then wait for one approval.
- **L3 — cross-module or contract-sensitive change.** Present exact files,
  consumers, contracts, impact, risks, and verification, then wait for explicit
  approval.
- **L4 — architecture, security/privacy, migration, destructive, external, or
  high-cost failure change.** Apply the complete L3 contract plus rollback,
  operational, and owner evidence. Wait for explicit approval.

If classification is uncertain, use the next higher class. Task size alone
never makes a protected boundary L1 or L2.

## 3. Authorization gate (`GATE-01`)

For L1, record the direct implementation request as authorization, announce the
class, exact files, behavior, non-goals, and checks, and proceed without waiting
for another confirmation. If any L1 condition is unverified, reclassify before
writing.

For L2, wait for explicit approval of the directory-boundary plan. Files may
change within those directories when they remain inside the approved behavior
and protected exclusions. For L3/L4, wait for explicit approval of the exact
plan and file set. Record the authorization source in the task contract.

Allowed before approval: read files, inspect status/diffs/configuration, list or
dry-run confirmed commands, and prepare the proposal. Not allowed: file writes,
dependency installation, formatting that mutates files, external actions, or
configuration changes.

## 4. Execute the approved scope

- Make the smallest coherent change.
- Update tests with behavior.
- Apply `WORKTREE-01` and `MODULE-01`.
- For L1, edit only the declared files. For L2, edit only inside approved
  directories. For L3/L4, edit only approved files and modules.
- Apply the selected language industry baseline to new and materially changed
  code while preserving verified hard constraints and approved compatibility.
- Run the smallest relevant check after each meaningful stage.

## 5. Scope-change gate (`GATE-02`)

Stop immediately when an assumption fails or the class boundary no longer
holds. L1 must reclassify before touching an undeclared file. L2 requires renewed
approval before leaving an approved directory or approved behavior. Every class
requires renewed approval before a public API/schema change, dependency,
build/CI/config change, destructive operation, external action, protected
security/privacy boundary, migration, or unrelated cleanup. Report:

- why the approved plan is insufficient;
- the newly affected files, modules, consumers, and risks;
- alternatives and the recommended option;
- added or changed verification.

Continue only after renewed approval.

## 6. Verify

Apply `VERIFY-01` and follow `docs/VERIFICATION.md`. A selected command is not
authorized until the task permits execution. A command not run is not a pass. Separate
implementation failures from environment failures and report both precisely.
Do not edit production code merely to make verification pass unless that fix is
inside the approved scope.

## 7. Review diff and hand off

Run `git diff --check`, inspect relevant diff/stat/status against the starting
state, confirm every change is approved, and check for generated, secret,
private, binary, or unrelated files. Trace changed behavior through consumers
and report changes, evidence, unverified items, and residual risk. If the same
manual correction or explicit operator workflow choice is evidenced three times
across locations or tasks, present a candidate using
`docs/CODING_RULES_LOG.md` under `ADAPT-01`. Do not persist the observation or synchronize a
rule until the user confirms it. Rule, tool, configuration, or historical-scope
changes still require the applicable authorization gate.

## Parallel work

Use multiple agents or worktrees only when explicitly allowed, interfaces are
stable, write scopes do not overlap, and parallelism has clear value. The
integrating agent owns scope compliance, final diff review, and repository-level
verification. Parallelism does not expand task approval (`WORKTREE-01`).
