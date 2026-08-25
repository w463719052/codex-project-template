# Web Frontend Engineering Profile

## Authority sources

- [HTML Living Standard for Web Developers](https://html.spec.whatwg.org/dev/)
- [CSS Snapshot 2025](https://www.w3.org/TR/css-2025/)
- [Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/)
- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- Framework-specific architecture, rendering, routing, state, and testing rules
  must come from the detected framework version and verified target evidence.

## Naming and API design

- Use semantic HTML before generic containers or ARIA substitutes. Controls,
  links, labels, headings, landmarks, tables, and forms must express their real purpose.
- Name components, properties, events, CSS classes, tokens, and test selectors by
  domain intent rather than visual position or temporary implementation.
- Keep component inputs minimal, typed where supported, and explicit about
  optional, controlled/uncontrolled, loading, empty, error, and disabled states.
- Prefer standards-based browser APIs and progressive enhancement. Do not invent
  custom interaction semantics when a native accessible element already exists.

## Architecture and dependencies

- Keep state at the closest stable owner. Derive values instead of duplicating
  state, and introduce global state only for demonstrated cross-boundary ownership.
- Separate rendering, domain decisions, transport, persistence, analytics, and
  platform integration when doing so clarifies ownership and testing; do not add
  a layer or hook for every trivial expression.
- Split components and files around cohesive behavior, state, or reusable visual
  responsibility. Avoid both page-sized components and fragmented wrapper forests.
- Keep dependency direction visible. Prevent circular imports, hidden global
  registration, framework leakage into domain logic, and generic component dumping grounds.

## Control flow and decomposition

- Render loading, empty, success, partial, error, offline, and permission states
  deliberately. Keep branching readable with named state or focused subcomponents.
- Avoid nested ternaries, deeply nested templates, duplicated conditional markup,
  and effects that secretly coordinate unrelated state transitions.
- Keep CSS selectors shallow and locally owned. Prefer tokens, logical properties,
  responsive layout primitives, and predictable cascade boundaries over specificity wars.
- Treat viewport, zoom, text expansion, localization, reduced motion, color
  contrast, keyboard order, and touch target behavior as design inputs.

## Errors, concurrency, and resources

- Validate and encode untrusted data at the correct boundary. Avoid unsafe HTML
  injection, dangerous DOM sinks, client-side secrets, and trust based only on UI state.
- Give requests, promises, subscriptions, timers, observers, workers, object URLs,
  and event listeners explicit owners and cleanup paths. Cancel or ignore stale work.
- Preserve useful error context while presenting safe, actionable user feedback.
  Do not expose credentials, internal stack details, or sensitive server responses.
- Avoid unnecessary client JavaScript and rerenders. Lazy-load by measured user
  value without hiding essential content or breaking focus and navigation.

## Testing and enforcement

- Test user-observable behavior through semantic roles and interactions. Cover
  keyboard/focus behavior, accessibility, responsive states, async races, errors,
  navigation, forms, hydration/rendering boundaries, and critical visual regressions.
- Use only confirmed formatter, linter, type checker, HTML/CSS validator,
  accessibility checker, browser test, bundle/performance, and framework commands.
- Automated accessibility checks are incomplete; retain focused keyboard,
  screen-reader, zoom, contrast, and reduced-motion review where relevant.
