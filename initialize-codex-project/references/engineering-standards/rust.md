# Rust Engineering Profile

## Authority sources

- [Rust Style Guide](https://doc.rust-lang.org/style-guide/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- The target's Rust edition, MSRV, `rustfmt`, Clippy, feature, and workspace
  configuration remain verified constraints.

## Naming and API design

- Follow default Rust formatting and naming. Design APIs so ownership, borrowing,
  lifetimes, fallibility, and invariants are visible in types.
- Prefer enums and newtypes for meaningful states. Keep public traits focused and
  implement standard traits when their semantics genuinely match.
- Document public items, safety invariants, panics, errors, and feature behavior.

## Architecture and dependencies

- Keep crates and modules cohesive and dependency direction explicit. Avoid a
  shared crate without stable consumers and a justified public contract.
- Prefer generics for static variation and trait objects for verified runtime
  substitution; do not introduce either only to anticipate hypothetical reuse.

## Control flow and decomposition

- Use pattern matching and `?` when they keep the successful path clear. Replace
  deeply nested matches, closures, or iterator chains with named operations when needed.
- Split modules around ownership and public responsibilities, while keeping a
  type's closely related implementation discoverable.

## Errors, concurrency, and resources

- Use typed errors for recoverable library behavior, preserve sources, and reserve
  panics for violated invariants or unrecoverable programmer errors.
- Minimize shared mutation, document `Send`/`Sync` and unsafe invariants, propagate
  cancellation where the runtime supports it, and rely on RAII for cleanup.

## Testing and enforcement

- Test public behavior, error variants, feature combinations, concurrency, and
  unsafe boundaries. Add documentation tests for public examples when appropriate.
- Use confirmed `cargo fmt`, Clippy, test, build, and MSRV checks from the project.
