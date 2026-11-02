# Microservices checks

Use for workload identities, service interfaces, network segments, distributed state and operators. State the business invariant and evidence limits before deriving scenarios. A reachable endpoint proves neither acceptance nor a defect, and a mesh, segment, gateway, signed assertion or retry label proves neither weakness nor effectiveness. With a cloud control plane in scope, keep one global id per shared actor and service.

## Trace

1. **Workload identity.** The process, its runtime identity and the human or service that initiated the operation differ. Issuance, replacement, expiry, revocation. An authenticated peer is not entitled to every operation.
2. **Reachability and operation authority.** A compromised low-privilege service reaching a higher-privilege operation: separate a network route from an accepted business request, and find the decision point on that exact operation.
3. **Chained delegation.** Follow the original user, tenant, resource and action through upstream, intermediate and downstream services. Where is context kept, narrowed, replaced or lost? A gateway check does not cover later hops.
4. **Distributed ownership.** Who owns each resource, reservation and result? A local success is not completion of the whole transaction.
5. **Retries and partial outcomes.** Failure before the effect, success with a lost reply and unknown outcome differ. Check duplicate, delayed and reordered work, changed intent under an old transaction id, cancellation racing completion, compensation.
6. **Recovery and availability.** Dependency outage, retry amplification, restart and replay authority, reconciliation. Does a receiver accept a protected operation while token validation or a policy dependency is down, or on a stale cached decision? Unknown behaviour is a gap.
7. **Operators and control plane.** Business authorization differs from the power to change identities, routes and configuration. A deployment right is not customer-data access.
8. **Attribution and exposure.** Request attribution through messages, logs and support views; which principals see which sensitive fields.

## Scenario families

Downstream privilege reached from a low-privilege service; authority lost or amplified along a chain; transaction integrity under retry or partial failure.

## Checks to propose (all `not_run`)

Compare denied and allowed identities against the same downstream operation and inspect state effects. For retries, lose a reply, redeliver and reorder one test transaction and check the invariant across every participating service. State pass, fail and inconclusive; invent no thresholds.
