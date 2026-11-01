---
name: orbyn-backend-design
description: "Design and implement API/service behavior across validation, authorization, persistence, concurrency and client errors using the consuming project's stack. Use architect first for unsettled ownership; use orbyn-data-migration for stored-format changes."
---

# Backend contracts that reach the client

Start from the consuming project's instructions and actual API, transport and
domain owners. Use [how](../how/SKILL.md) to trace the existing request, and
[architect](../architect/SKILL.md) when ownership or lifecycle is undecided.
Use the project's own stack: do not introduce Fastify, PostgreSQL, Zod or any other
Orbyn stack component merely because it appears in an example.

## Method

1. **State the contract:** the caller's input, allowed identity/scope, successful result and expected domain failures.
2. **Identify the authority reads:** which reads establish authority/freshness, and which write or external effect must preserve them. Check access to the referenced tenant resource; a parsed ID and a signed-in session do not prove it.
3. **Validate at the trust boundary.** Place parsing there and reuse the owning schema inside the service. Express failures in the owning contract, and do not scatter defensive checks over already valid internal values.
4. **Protect the write.** Keep transactions around related persistence, with version conditions or locks where stale state matters. Concurrent writers need application-level ownership or fencing; a Git worktree cannot isolate them.
5. **Handle external effects.** Define operation identity, unknown outcomes and reconciliation, and do not hold a database transaction open while a remote provider decides. Retries, crashes and duplicate delivery need an explicit idempotency key, effect identity or recovery contract. Preserve cancellation and cleanup ownership.
6. **Trace the result through the shared client and each affected UI.** Keep errors recognizable enough for a client to preserve its draft, explain the failure and retry deliberately. Never return success for a rejected effect or expose internal exceptions and credentials as UI copy.
7. **Verify, when authorized,** the legitimate outcome, denied access, stale update and relevant retry behavior at the owning boundary.
8. **Return** the changed contract, affected callers, evidence and recovery limits.

For example, moving a task between projects requires source/destination scope, stage compatibility, a concurrency condition and a consistent API result. Updating one route without its shared schema and mobile caller leaves the feature incomplete. A lost save response needs reconciliation/idempotency at the real backend boundary; a simulated preview cannot prove absence of duplicate effects. [Retrying an external effect](examples/retry-safe-effect.md) separates request identity, durable state and an unknown provider outcome in a synthetic task.

## Hand off

- Persisted-format changes: [data migration](../orbyn-data-migration/SKILL.md).
- Visible flows: [UI design](../orbyn-ui-design/SKILL.md).
- Coordinated work: [orbyn-workflow](../orbyn-workflow/SKILL.md).
- Choosing a replacement stack: stack selection and architect, not an incidental service implementation.
- Model-proposed tool arguments or generated data: [AI application engineering](../orbyn-ai-application/SKILL.md) for context, quality and the bounded-loop contract. This backend owner still enforces current authorization, semantic validation and durable effect identity outside the model.

## Read when needed

- Service readiness or a material workload change: the [operating contract](../architect/references/service-readiness.md) covers the user completion indicator and observation window, demand/quota bounds, operator/recovery ownership, and data classification, retention/deletion and safe diagnostic fields. Put these in the returned criteria; unknown targets or policies remain unresolved gates.
- Actual service/runtime: [language guidance](../language-best-practices/SKILL.md). Database syntax and isolation need the engine's SQL reference; language types alone do not prove transaction or authorization behavior.
- Bounded input/work, error semantics, concurrency and stable pagination: [production service contracts](references/service-contracts.md).
- An operation needing diagnosable phases and privacy-aware records: [observability](references/observability.md). Installing telemetry or a provider is a separate decision.
- Critical retry, lease or worker lifecycle rules, when justified: connect current effect boundaries to [statecharts](../architect/references/statecharts.md) and [property verification](../tdd/references/formal-verification.md).
- Worked examples: the [boundary method](references/principles/boundary-discipline.md) and [idempotency method](references/principles/make-operations-idempotent.md).
- Supported Expo Router server endpoints: [API route authority](references/expo-api-routes.md). Native/browser route state cannot establish server resource access.
