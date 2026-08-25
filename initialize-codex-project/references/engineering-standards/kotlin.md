# Kotlin Engineering Profile

## Authority sources

- [Kotlin Coding Conventions](https://kotlinlang.org/docs/coding-conventions.html)
- For Android modules, [Android Architecture Recommendations](https://developer.android.com/topic/architecture/recommendations)

## Naming and API design

- Follow Kotlin naming and file-organization conventions. Prefer meaningful
  nouns for types, verbs for actions, and names that reveal mutation or returned copies.
- Prefer immutable interfaces and `val`; omit redundant syntax. Make library
  visibility, return types, and KDoc explicit where compatibility depends on them.
- Use nullability and sealed/domain types to express states instead of sentinel values.

## Architecture and dependencies

- Keep UI and data responsibilities distinct in Android code; expose state in
  one direction and keep data access behind verified repository boundaries.
- Add a domain/use-case layer only when it removes real reuse or complexity from
  callers. Do not create a layer for every operation by default.
- Keep extensions near their owning concept or consumer; avoid global extension buckets.

## Control flow and decomposition

- Prefer readable `when`, collection operations, and early returns, but replace
  clever chains with explicit control flow when allocations or intent become unclear.
- Split large classes, composables, and coroutine pipelines around state ownership
  and behavior, not arbitrary line counts.

## Errors, concurrency, and resources

- Preserve exception causes and model expected domain outcomes explicitly.
- Use structured concurrency, propagate cancellation, inject dispatchers only at
  verified boundaries, and avoid unowned scopes.
- Close resources deterministically and keep mutable shared state isolated.

## Testing and enforcement

- Test coroutine cancellation, flows/state transitions, lifecycle boundaries,
  errors, and public behavior with deterministic dispatchers when configured.
- Use the project's confirmed Kotlin formatter, inspections, compiler, lint, and tests.
