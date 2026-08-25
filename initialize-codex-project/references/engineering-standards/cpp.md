# C++ Engineering Profile

## Authority sources

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- The target's C++ standard, ABI, platform, compiler, warning, formatter, static
  analysis, and existing style configuration remain verified constraints.

## Naming and API design

- Use the project's selected naming/layout variant consistently while adopting
  Core Guidelines safety and interface principles for new or materially changed code.
- Prefer strong types, self-contained headers, narrow interfaces, explicit
  ownership, and RAII. Keep public headers portable and minimize transitive exposure.
- Express invariants through constructors and types; avoid long primitive
  parameter lists, naked allocation, and macro-defined APIs.

## Architecture and dependencies

- Preserve component and include direction. Keep platform, transport, and storage
  details behind verified boundaries without speculative interfaces.
- Prefer composition, value semantics, and standard facilities. Introduce
  polymorphism only for demonstrated runtime variation and ownership requirements.

## Control flow and decomposition

- Keep lifetime and failure paths visible. Prefer guard clauses and named
  operations over deeply nested conditionals, macros, and template cleverness.
- Split translation units by cohesive responsibility and compile-time boundary;
  do not fragment tightly coupled implementation solely to meet a line target.

## Errors, concurrency, and resources

- Follow the project's exception/no-exception contract. Preserve error context
  and never mix incompatible error models without an adapter boundary.
- Use RAII for every resource, avoid owning raw pointers, minimize shared mutable
  state, and make thread-safety and synchronization contracts explicit.

## Testing and enforcement

- Test public contracts, ownership/lifetime edge cases, error paths, concurrency,
  ABI/serialization compatibility, and consumers of changed headers.
- Use confirmed formatter, compiler warnings, sanitizers, static analysis, build,
  and test commands; do not assume Google-specific toolchain restrictions apply.
