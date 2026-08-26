# Change Impact Analysis

Use this worksheet for L3/L4 tasks. L1/L2 record their concise impact summary in
`docs/TASK_TEMPLATE.md`; if investigation requires this full worksheet,
reclassify under `docs/CODEX_WORKFLOW.md` before implementation. For L3/L4,
complete every applicable field and write `none` with evidence instead of
silently skipping a category.

## Change surface

- Requested behavior:
- Direct implementation files/modules:
- Public contracts changed:
- Data/configuration changed:
- Generated artifacts changed:

## Dependency and consumer trace

- Direct callers:
- Downstream consumers:
- Cross-module dependencies:
- External clients/integrations:
- Compatibility expectations:

Trace from the changed entrypoint in both directions: inputs and dependencies
upstream; callers, observers, stored data, generated output, and integrations
downstream.

## Failure and operational behavior

- Error and missing-data behavior:
- Cancellation/concurrency/resource behavior:
- Security/privacy implications:
- Performance/capacity implications:
- Logging/metrics/alerts:
- Deployment/configuration/migration:
- Rollback or safe-disable path:

## Regression prevention

- Smallest focused test:
- Module/target suite:
- Consumer/contract/integration tests:
- Build/static checks:
- Manual verification:
- Existing gaps and residual risk:

## Scope decision

- [ ] Exact L3/L4 files and modules remain authorized.
- [ ] Public contract and compatibility changes are explicitly approved.
- [ ] New dependencies/configuration/external actions are explicitly approved.
- [ ] Verification covers direct behavior and applicable consumers.
- [ ] Otherwise, implementation is stopped pending renewed approval.
