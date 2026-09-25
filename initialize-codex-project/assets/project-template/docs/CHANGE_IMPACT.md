# Change Impact Analysis

This is an optional worksheet for L3/L4 tasks. Perform the analysis in the
conversation by default. If the operator explicitly requests a persistent
record, copy the relevant structure to that record; do not append task history
here. L1/L2 need only a concise impact summary. Classification and approval
remain defined by `docs/CODEX_WORKFLOW.md`.

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
