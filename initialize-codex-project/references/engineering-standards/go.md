# Go Engineering Profile

## Authority sources

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- Effective Go is useful but explicitly not actively updated; combine it with
  current Go documentation, review guidance, `gofmt`, and target-version evidence.

## Naming and API design

- Let `gofmt` decide formatting. Use short, clear package names and idiomatic
  exported names that do not repeat the package name.
- Keep interfaces small and define them near consumers when that matches the
  verified ownership boundary. Do not create interfaces only to mirror implementations.
- Make zero values useful when practical and document exported APIs and invariants.

## Architecture and dependencies

- Keep packages cohesive, dependency direction acyclic, and commands thin.
  Avoid generic utility packages and global service registries.
- Pass dependencies explicitly. Introduce internal boundaries for real ownership,
  substitution, or compatibility needs rather than architectural ceremony.

## Control flow and decomposition

- Handle errors early so the successful path continues down the page. Avoid
  unnecessary `else`, dense anonymous functions, and clever one-line control flow.
- Split functions and files around cohesive operations and package ownership;
  keep closely related types and methods discoverable together.

## Errors, concurrency, and resources

- Return errors with useful context, preserve identity when callers inspect it,
  and avoid logging and returning the same error at every layer.
- Give every goroutine an owner and termination path. Propagate context only for
  request-scoped cancellation/deadlines and close resources deterministically.

## Testing and enforcement

- Prefer table-driven tests when they improve case clarity. Test exported behavior,
  errors, races, cancellation, and package consumers.
- Use confirmed `gofmt`, `go vet`, race, build, and test commands from the project.
