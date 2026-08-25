# C Engineering Profile

## Authority sources

- [ISO/IEC 9899:2024 Programming languages — C](https://www.iso.org/standard/82075.html)
- [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c)
- The target's selected C revision, compiler extensions, ABI, platform, warning,
  formatter, analyzer, safety, and portability requirements remain hard constraints.

## Naming and API design

- Follow the project's selected naming convention consistently. Names should
  expose units, ownership, mutability, validity, and error behavior where those
  properties are not already clear from the type and scope.
- Keep public headers self-contained and minimal. Use include guards, forward
  declarations where valid, and opaque structures when callers should not depend
  on representation details.
- Prefer explicit-width or domain types when representation matters. Do not
  silently mix signed/unsigned values, sizes, counts, offsets, and error codes.

## Architecture and dependencies

- Treat each `.c`/`.h` pair or cohesive source group as an owned module with a
  narrow public interface. Keep internal declarations `static` where practical.
- Make allocation, initialization, shutdown, callback lifetime, and dependency
  ownership part of the module contract. Avoid mutable global state and hidden
  initialization order.
- Use function pointers, tables, and opaque contexts only for demonstrated
  platform variation, substitution, or state-machine needs—not speculative patterns.

## Control flow and decomposition

- Prefer guard clauses and a visible successful path. Keep conditions explicit;
  parenthesize non-obvious precedence and avoid side effects inside conditions.
- Use macros only when the language or verified platform boundary requires them;
  prefer typed functions, enums, constants, and generated tables otherwise.
- A single cleanup label can be clearer than duplicated release logic. Keep each
  jump forward-only, locally visible, and limited to deterministic cleanup.
- Split long routines around state transitions or ownership phases, not arbitrary
  line counts. Keep tightly coupled private helpers near their owning module.

## Errors, concurrency, and resources

- Validate external sizes, indices, ranges, pointers, integer conversions, and
  allocation results before use. Avoid undefined, unspecified, and implementation-
  defined behavior unless the target contract documents and verifies it.
- Document who allocates, owns, borrows, transfers, and releases each resource.
  Make partial-initialization cleanup correct and idempotent where required.
- Define thread-safety, signal-safety, atomic ordering, interrupt, and reentrancy
  expectations. Do not use `volatile` as a synchronization substitute.
- Preserve error causes through the project's established return-code, `errno`,
  status-object, logging, or callback contract without reporting the same failure repeatedly.

## Testing and enforcement

- Test boundary sizes, invalid input, allocation failure where injectable,
  cleanup paths, integer limits, state transitions, concurrency, and ABI consumers.
- Use only confirmed compiler warnings, formatter, static analyzer, sanitizer,
  fuzzing, build, and test commands. A sanitizer pass does not prove portability.
