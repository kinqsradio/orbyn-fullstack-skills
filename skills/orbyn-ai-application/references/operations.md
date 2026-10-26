# Operate and change AI behavior deliberately

Use for integration, qualification or an authorized release plan. Inspect existing
providers, telemetry and release policy first. This method adds no automatic
provider setup, subscriptions, background monitoring or deployment.

Treat model/provider changes, prompts, schemas/tools, retrieval corpus/index,
permission/cache policy, context selection and budget settings as one identifiable
behavior bundle. Preserve rollback compatibility and source lineage. Record the
actual deployed bundle separately from a local proposed configuration. Immutable
code alone cannot pin a changing hosted model or external corpus; state that limit.

Choose user-relevant quality/error thresholds, latency and cost/work budgets, quota
and concurrency bounds, and ownership of incidents and support. Account for
retries, parallel work, retrieval, judges and unsuccessful requests. Bound queues
and enforce cancellation/deadlines at the actual owners. A provider's nominal
limit is not measured application capacity. Diagnose phases through the existing
[observability contract](../../orbyn-backend-design/references/observability.md)
without logging full prompts or private documents by default.

Define degradation deliberately: deterministic/manual alternatives, a supported
partial answer, bounded retry, abstention or escalation. A fallback must preserve
permissions, consent, data residency/retention, recipients, quality requirements,
approval and effect identity.
Do not send sensitive context to another provider or serve a stale unauthorized
cache entry merely to maintain availability. Make material behavior changes
visible using the existing [AI interaction rules](../../orbyn-ui-design/references/design-rules.md#ai-interactions).

Use [task evaluations](evaluations.md) and deterministic checks for the changed
bundle before claiming readiness. Roll out only within actual authority using
existing [release/health methods](../../orbyn-ci-design/references/rollout-recovery.md):
bounded exposure where appropriate, meaningful denominators, guardrails, stop
conditions, accountable owner and rollback/manual recovery. A shadow evaluation
can still disclose data or consume quota; it needs its own applicable scope.
Do not mistake a green offline score or a shipped feature for user benefit.

Observe authorized quality feedback, abstentions/corrections, denied actions,
latency/cost and errors by relevant slice. Minimize capture and state sampling,
consent and retention limits. A drift signal is a reason to investigate, not an
automatic retrain, prompt rewrite or provider switch. Requalify changed assumptions
or bundles against affected cases and untouched critical slices; preserve prior
attempts. Revoke or expire caches/derived records consistently with source access.

Return proposed/observed bundle identity, selected evidence, resource bounds,
fallback and rollback limits, owner and revisit trigger. No production-health
claim follows from fixtures, browser previews or an unexecuted rollout plan.

Research/update pointers reviewed 26 October 2026: [NIST AI 600-1, July 2024](https://doi.org/10.6028/NIST.AI.600-1),
[Google PAIR feedback/control](https://pair.withgoogle.com/chapter/feedback-controls/).
Original local synthesis; no source text, SDK or runtime imported. These methods
work offline; current provider/version claims still need applicable verification.
