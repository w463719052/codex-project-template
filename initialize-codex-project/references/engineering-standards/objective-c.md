# Objective-C Engineering Profile

## Authority sources

- [Apple Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/)
- Treat this archived source as the Apple naming and Cocoa API baseline while
  respecting the target's supported SDK, ARC policy, and verified local tooling.

## Naming and API design

- Use clear Cocoa-style selector names that make argument roles readable at the
  call site. Follow established prefixes and avoid ambiguous abbreviations.
- Distinguish object, scalar, Boolean, notification, delegate, and error naming
  according to Cocoa conventions. Keep headers minimal and self-explanatory.
- Document nullability, ownership, designated initializers, and public behavior.

## Architecture and dependencies

- Keep framework-facing adapters separate from domain decisions when the
  existing architecture supports that boundary.
- Prefer composition and focused protocols. Avoid broad delegate interfaces,
  categories used as dumping grounds, and implicit global state.

## Control flow and decomposition

- Use early exits for invalid inputs and failures. Extract nested callback logic
  around meaningful asynchronous operations or ownership boundaries.
- Split headers and implementations by cohesive responsibility; do not expose
  private helpers or imports in public headers without a contract need.

## Errors, concurrency, and resources

- Follow Cocoa error conventions consistently. Preserve `NSError` context and
  never ignore required completion paths.
- Make queue expectations, callback thread, cancellation, weak/strong capture,
  ARC ownership, and non-object resource cleanup explicit.

## Testing and enforcement

- Test initializer failure, delegation, asynchronous completion, ownership-
  sensitive behavior, and Objective-C/Swift interoperability boundaries.
- Use only confirmed compiler warnings, analyzer, formatter, linter, and test commands.
