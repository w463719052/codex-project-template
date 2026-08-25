# Python Engineering Profile

## Authority sources

- [PEP 8](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- The target's supported Python versions, formatter, linter, type checker,
  packaging, and framework configuration remain verified constraints.

## Naming and API design

- Follow PEP 8 naming and layout, supplemented by the selected formatter and
  Google guidance for language usage, typing, exceptions, resources, and documentation.
- Use type annotations on maintained public and cross-module boundaries when the
  project supports them. Prefer domain types over unstructured dictionaries.
- Keep module APIs explicit, minimize mutable globals, and document public behavior.

## Architecture and dependencies

- Keep domain behavior separate from web, CLI, persistence, and transport
  adapters when the verified project structure defines those boundaries.
- Prefer explicit dependency passing at established composition points. Avoid
  import-time work, hidden registries, and generic helper modules without ownership.

## Control flow and decomposition

- Prefer guard clauses, comprehensions that remain simple, generators for lazy
  flows, and named intermediate values for complex transformations.
- Split long functions and modules around coherent responsibilities. Avoid deeply
  nested local functions, comprehensions, and exception handling.

## Errors, concurrency, and resources

- Catch the narrowest useful exception, preserve causes, avoid bare `except`, and
  provide actionable context without leaking sensitive values.
- Use context managers for resources. Make task ownership, cancellation, blocking
  work, and shared mutable state explicit in async or threaded code.

## Testing and enforcement

- Test public behavior, boundary validation, errors, async cancellation, and
  serialization. Avoid mocks that merely duplicate implementation details.
- Use only confirmed formatter, linter, type checker, test, and packaging commands.
