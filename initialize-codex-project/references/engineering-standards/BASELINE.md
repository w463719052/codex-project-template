# Engineering Baseline

Use this baseline for newly written or materially changed code. Existing
formatter, compiler, CI, public-contract, compatibility, security, and platform
constraints remain hard boundaries. Record conflicts instead of silently
discarding either the baseline or verified project evidence.

## Authority sources

This profile contains cross-language maintainability rules derived from common
engineering practice. Language-specific syntax, APIs, and idioms come from the
selected language profiles and their linked primary sources.

## Naming and API design

- Name types and modules for responsibilities; name operations for observable
  behavior. Avoid vague buckets such as `Manager`, `Helper`, or `Utils` unless
  the project defines a precise meaning.
- Optimize public APIs for clarity at the call site. Keep public surfaces small,
  explicit, compatible, documented, and difficult to misuse.
- Prefer domain types over unrelated primitive parameters when they make
  invariants and intent visible.

## Architecture and dependencies

- Preserve verified module ownership and dependency direction. Domain logic
  should not depend directly on UI, transport, persistence, or framework details
  unless the documented architecture requires it.
- Introduce a pattern only for a demonstrated variation, lifecycle, ownership,
  or test seam. Do not add repositories, factories, adapters, or abstractions
  merely because a pattern exists.
- Keep state ownership and side effects explicit. Pass dependencies through the
  project's established construction boundary rather than hiding them globally.

## Control flow and decomposition

- Keep the successful path easy to scan. Prefer early returns or guard clauses
  over deeply nested conditionals.
- Three nesting levels, roughly forty logical lines in one function, excessive
  branching, or multiple reasons to change are review triggers, not automatic
  failures. Restructure only when the result has clearer responsibilities.
- A file should have one primary responsibility. A few hundred lines, multiple
  unrelated primary types, or repeated navigation between distant sections are
  split-review triggers, not mechanical line limits.
- Do not replace one cohesive function with many trivial one-line wrappers.
  Every extraction should improve naming, ownership, reuse, or testability.

## Errors, concurrency, and resources

- Preserve actionable error context without exposing secrets or duplicating
  logs at every layer. Never silently swallow failure.
- Make cancellation, deadlines, task ownership, shared mutable state, cleanup,
  and resource lifetime explicit according to the language profile.
- Prefer immutable values and deterministic data flow unless mutation is the
  clearer, measured, or framework-required choice.

## Testing and enforcement

- Test observable behavior, boundaries, errors, and regression cases in
  proportion to the change. Avoid tests coupled only to private implementation.
- Prefer formatter, linter, compiler, static analysis, templates, and tests for
  mechanical rules. Keep contextual design decisions in reviewable prose.
- If the same manual correction appears in at least three places or recurs
  across tasks, present a candidate in conversation. Record it only after confirmation, using
  an optional rules log, and propose an approved rule or automated check.
