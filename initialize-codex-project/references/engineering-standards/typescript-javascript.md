# TypeScript and JavaScript Engineering Profile

## Authority sources

- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- The target's ECMAScript runtime, compiler options, framework, formatter, and
  lint configuration define supported syntax and enforced compatibility.

## Naming and API design

- Prefer TypeScript for typed modules when the project already uses it. Keep
  exported types and functions small, explicit, documented, and stable.
- Use descriptive camel-case names, `const` by default, narrow types, tagged
  unions for variant states, and `unknown` plus validation at untrusted boundaries.
- Avoid `any`, suppression directives, implicit globals, prototype mutation,
  and dynamic evaluation unless a verified exception documents the risk.

## Architecture and dependencies

- Keep domain behavior independent of UI framework, transport, storage, and
  runtime globals when module boundaries permit it.
- When `web-frontend` is also selected, apply its semantic HTML, CSS, component,
  accessibility, browser lifecycle, security, and interaction rules in addition
  to this language profile.
- Use explicit imports and dependency direction. Avoid barrel files or generic
  utility modules when they hide ownership or introduce cycles.

## Control flow and decomposition

- Prefer early returns and named intermediate values over nested callbacks,
  chained ternaries, and dense functional pipelines.
- Split components, hooks, services, and modules around state ownership and
  behavior. Do not extract trivial wrappers that obscure the call path.

## Errors, concurrency, and resources

- Validate external data at boundaries. Preserve error causes and distinguish
  expected domain results from exceptional failures.
- Await or deliberately own promises, propagate abort signals, clean up timers,
  subscriptions, listeners, and streams, and prevent stale asynchronous updates.

## Testing and enforcement

- Test public behavior, type boundaries, validation, async failure/cancellation,
  rendering state, and compatibility where relevant.
- Use confirmed compiler, formatter, linter, framework, and test commands only.
