# Swift Engineering Profile

## Authority sources

- [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)
- Use the target's verified Swift version, SwiftFormat/SwiftLint configuration,
  package settings, and Apple-platform framework guidance as compatibility evidence.

## Naming and API design

- Optimize names for clarity and fluent use at the call site; clarity is more
  important than brevity. Name mutating and nonmutating operations distinctly.
- Use argument labels, nouns, verbs, and Boolean names according to Swift API
  conventions. Document public declarations and make visibility explicit.
- Model invalid states with types, enums, and constrained initializers instead
  of loosely related strings, flags, and optionals.

## Architecture and dependencies

- Keep domain behavior independent of UIKit, SwiftUI, storage, and transport
  when the verified module structure provides such a boundary.
- Give state one owner. Keep view rendering declarative and move reusable
  business decisions out of views without creating ceremonial layers.
- Introduce protocols at real substitution or module boundaries, not for every
  concrete type.

## Control flow and decomposition

- Prefer `guard` for preconditions and early exits when it leaves the successful
  path linear. Avoid long chains of nested optional unwrapping.
- Split large views, closures, and functions around coherent behavior or state
  ownership. Keep related small declarations together when separation harms discovery.

## Errors, concurrency, and resources

- Use typed throwing APIs or explicit result modeling when callers can recover;
  preserve the underlying cause and actionable context.
- Under Swift concurrency, make isolation and `Sendable` assumptions explicit.
  Propagate cancellation and avoid detached tasks without documented ownership.
- Use deterministic cleanup and avoid retain cycles in escaping closures.

## Testing and enforcement

- Test public behavior, async cancellation, actor/isolation boundaries, and
  state transitions. Prefer fakes at verified boundaries over pervasive mocks.
- Use only the repository's confirmed Swift compiler, formatter, linter, build,
  and test commands.
