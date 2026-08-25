# Java Engineering Profile

## Authority sources

- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- Project framework, supported JDK, formatter, static analysis, and compatibility
  rules remain verified constraints.

## Naming and API design

- Follow Google Java source layout, naming, import, formatting, and Javadoc
  rules unless a confirmed tool enforces a conflicting project requirement.
- Keep types cohesive, constructors valid, visibility minimal, and public APIs
  explicit about nullability, ownership, side effects, and compatibility.
- Prefer domain objects or records over long primitive parameter lists.

## Architecture and dependencies

- Preserve module and layer direction. Keep framework, persistence, and transport
  details outside domain logic where the target architecture defines that boundary.
- Prefer constructor injection at established composition roots. Avoid service
  locators, mutable global state, and interfaces with only speculative consumers.

## Control flow and decomposition

- Favor guard clauses and small cohesive operations over nested conditionals and
  multi-stage methods. Use streams only when the pipeline remains easier to read.
- Split classes by responsibility and reason to change; do not create one-method
  classes solely to satisfy a pattern name.

## Errors, concurrency, and resources

- Use exceptions for exceptional failures, preserve causes, and avoid catching
  broad exceptions without recovery. Make expected domain failures explicit.
- Use structured ownership for executors/tasks where available, document thread
  safety, minimize shared mutation, and close resources with language facilities.

## Testing and enforcement

- Test public behavior, validation, exception contracts, concurrency boundaries,
  serialization, and consumers of changed APIs.
- Use the verified formatter, compiler warnings, static analyzers, and test runner.
