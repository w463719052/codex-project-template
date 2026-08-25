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

## 2. Propose the scope contract

Use `docs/TASK_TEMPLATE.md` and `docs/CHANGE_IMPACT.md`. Name every proposed
file/module, behavior and contract change, verification command, non-goal, and
known risk. For each command, cite its repository or CI evidence.

Every implementation applies `GATE-01`. A small task may use a concise plan but
does not skip approval.

## 3. Approval gate (`GATE-01`)

Wait for explicit approval of the plan and file set. An initial request to
implement a feature or fix is not approval of an unseen plan. Record approval in
the task contract before editing. Transition `proposed → approved` only after
that explicit approval.

Allowed before approval: read files, inspect status/diffs/configuration, list or
dry-run confirmed commands, and prepare the proposal. Not allowed: file writes,
dependency installation, formatting that mutates files, external actions, or
configuration changes.

## 4. Execute the approved scope

- Make the smallest coherent change.
- Update tests with behavior.
- Apply `WORKTREE-01` and `MODULE-01`.
- Edit only approved files and modules.
- Apply the selected language industry baseline to new and materially changed
  code while preserving verified hard constraints and approved compatibility.
- Run the smallest relevant check after each meaningful stage.

## 5. Scope-change gate (`GATE-02`)

Stop immediately when an assumption fails or implementation requires an
unapproved file/module, public API/schema change, dependency, build/CI/config
change, destructive operation, external action, or unrelated cleanup. Report:

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
manual correction occurs in at least three places or recurs across tasks, record
or propose a candidate in `docs/CODING_RULES_LOG.md`; changing a rule, tool, or
historical scope still requires the applicable approval gate.

## Parallel work

Use multiple agents or worktrees only when explicitly allowed, interfaces are
stable, write scopes do not overlap, and parallelism has clear value. The
integrating agent owns scope compliance, final diff review, and repository-level
verification. Parallelism does not expand task approval (`WORKTREE-01`).
