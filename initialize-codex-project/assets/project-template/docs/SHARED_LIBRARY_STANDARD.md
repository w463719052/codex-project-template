# Shared Library Standard

Shared code is a public dependency, not a cleanup technique. Prefer a cohesive
implementation inside the owning module until evidence shows a stable reusable
contract.

## Extraction gate

A candidate may proceed only when the approved proposal demonstrates:

- one focused responsibility with clear non-goals;
- at least two independent real consumers, or another project-specific
  threshold explicitly approved by maintainers;
- a stable abstraction based on consumer needs rather than copied syntax;
- no dependency on a consuming product's UI, storage, configuration, or domain
  internals;
- a minimal public API with documented errors, lifecycle, concurrency,
  cancellation, performance, and compatibility behavior;
- independent unit tests plus consumer contract/integration coverage;
- ownership, versioning, release, deprecation, migration, and support policy;
- lower total coupling and maintenance cost than keeping implementations local.

Similarity alone is insufficient. If consumers are likely to evolve differently,
keep the code local or share a smaller stable primitive.

## Dependency rules

- The library must not import its consumers or require consumer-specific
  initialization.
- Consumers depend on a documented public entrypoint, never library internals.
- Side effects and platform integrations stay behind explicit adapters.
- Avoid circular package/repository dependencies.
- Use dependency injection or small protocols only where they represent a real
  variation point; do not abstract speculatively.
- A new library, package link, repository reference, or production dependency
  is outside scope until explicitly approved.

## Public API and compatibility

- Keep the exported surface minimal and cohesive.
- Document ownership of inputs, outputs, resources, callbacks, and threads/tasks.
- Define error categories and compatibility guarantees.
- Use semantic versioning or the project's approved equivalent.
- Require a migration and deprecation path for breaking changes.
- Test every supported runtime/platform combination or document exclusions.

## Required documentation

Create the library documentation from `docs/LIBRARY_DOCUMENTATION_TEMPLATE.md`.
It must include overview and non-goals, installation/linking, quickstart, public
API, examples, errors and edge cases, concurrency/resource behavior,
compatibility, performance, testing, versioning, changelog, migration, security
or privacy considerations, ownership, and support.

Documentation and examples are part of the public contract. A shared library is
not complete while required sections or consumer migration guidance are missing.

## Verification and release

- Run library unit/static/build checks independently.
- Run contract or integration checks for every known consumer.
- Confirm package/link resolution from a clean supported environment.
- Review public symbols and generated API documentation.
- Record compatibility impact and rollback for each release.
- Do not publish, tag, push, or update external consumers without separate
  explicit authorization.
