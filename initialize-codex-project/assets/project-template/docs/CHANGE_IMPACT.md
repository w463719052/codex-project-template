# Change Impact Analysis

Apply detail in proportion to the task class. L1 records concise evidence that
contracts and protected boundaries are unchanged. L2 completes applicable
module and directory impacts. L3/L4 complete every section before
implementation. Write `none` with evidence instead of silently skipping a
category. A newly discovered impact outside the class boundary triggers
reclassification or renewed approval.

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

- [ ] L1 files, L2 directories, or L3/L4 exact scope remain authorized.
- [ ] Public contract and compatibility changes are explicitly approved.
- [ ] New dependencies/configuration/external actions are explicitly approved.
- [ ] Verification covers direct behavior and applicable consumers.
- [ ] Otherwise, implementation is stopped pending renewed approval.
