# Serverless checks

Use for event sources, short-lived functions, execution roles, managed stores and configuration. State the business authorization and transaction invariant and any supplied resource budgets first. An empty input yields gaps, not invented components. Asynchronous or managed labels prove neither a defect nor a protection. Add [microservices](microservices.md) checks for service-to-service chains, and bound event-driven channel checks to the channel.

## Trace

1. **Event source and admission.** Caller, event source, channel publisher and permitted trigger are different. Who chooses each event field: resource, version, tenant, destination, work count? Copied caller metadata is not authoritative because a trusted service delivered it.
2. **Function and runtime identity.** Asset, execution role and one invocation differ. Follow the event-selected object into reads, writes and notifications under that role. Permission to invoke is not resource-owner authority.
3. **Managed storage and authorization state.** Tie immutable input versions, ownership, release status and notification recipients to their authoritative records. Check replacement, deletion, quarantine and revocation between admission and effect. A storage address is not permission.
4. **Duplicates and concurrency.** One business intent has several event, delivery and invocation ids. Check repeated delivery under different invocations, simultaneous completion and cancellation racing release. Assume no ordering or exactly-once processing.
5. **Chains, queues and budgets.** One admitted input through derivatives, processing, notification, error work and replay. Identify feedback edges and fan-out, and compare aggregate work with supplied budgets. A per-invocation cap does not bound a chain. Invent no thresholds.
6. **Execution-context lifecycle.** Reused memory, temp data, cached authorization and credentials across invocations and principals. Short-lived code does not mean a clean runtime.
7. **Configuration and recovery authority.** Changing triggers, role scope, routing or replay is different from releasing a resource. A deployment right is not data access.
8. **Notification channel.** Publisher admission, subscriber scope, retention and replay. Correlation is not authorization.

## Scenario families

Event fields exercising function authority; duplicate or concurrent work violating an invariant; chain or queue amplification exceeding a budget.

## Checks to propose (all `not_run`)

Authorized against forbidden resource and recipient fields under the same function authority; the same effect under different invocation ids with overlapping workers and reordered cancellation; within-budget work against a bounded fan-out or retry case. Unknown schedules or downstream work are inconclusive, never a pass.
