# Multi-tenant SaaS checks

Use for tenant identity, shared services, data partitions, support access and tenant configuration. Do not infer a product, a partition mechanism or an implemented control from the architecture name. Pair with [data platform](data-platform.md) when reports pass through shared transformations, and keep the same source-record, tenant and output ids.

## Trace

1. The trusted source that verifies tenant selection and current membership, followed into the exact query and any reused execution context. Tell a tenant member, a tenant administrator and a platform support actor apart. Authentication alone is not entitlement.
2. Tenant-sensitive results into caches and back to recipients: the permitted recipient set and invalidation when membership changes. Intentionally global values are a separate class.
3. A report request through the producer's authority, shared queue, worker context, retries and delayed execution. When is membership checked again? A tenant field on a job is not proof it is trustworthy.
4. Export generation, stored output and later retrieval as separate steps, including a saved retrieval link after revocation.
5. Tenant administration against platform support impersonation: granted tenant, target actor, permitted operation, expiry, revocation, audit. Authorized support actions are counterexamples, not defects.
6. Tenant configuration against shared behaviour: trace a tenant setting to its consumers. Influence on another tenant needs a concrete shared dependency.
7. Shared bottlenecks: queue depth, concurrency, expensive reports, storage. Ingress rate limits do not show worker fairness. Mark a quota implemented only on implementation evidence, and effective only on a passed, executed check.
8. Onboarding, revocation, offboarding, retention and restore across records, caches, queued work and exports. A shared backup is not a leak by itself.

## Scenario families

Cross-tenant read through query, cache, job or export; support or administrative authority beyond its grant; one tenant exhausting shared capacity.

## Checks to propose (all `not_run`)

- Derive an allow, deny or unknown matrix from supplied memberships, ownership and deliberately shared data. Exercise query, cache, delayed jobs and export retrieval, including revocation before execution. Judge by content and persistent effect, not status code. Pass: every observed case matches the matrix.
- Separate tenant-administrator checks from delegated support-grant checks: permitted operations, out-of-scope tenants, writes outside the grant, shared-setting changes, expired grants. Never perform privileged impersonation while modelling.
- Capacity checks need bounded isolated jobs and supplied budgets. Never stress production.
