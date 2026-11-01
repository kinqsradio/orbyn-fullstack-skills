---
name: orbyn-ai-application
description: "Design, implement or evaluate model-powered application behavior: grounded answers, retrieval, structured generation, tool workflows and quality/cost operation. Not model training, generic AI-assisted coding or host/provider setup."
---

# Engineer a model-powered application

Use for a model-powered product contract. For an ordinary API, UI, bug fix or
agent-host setup without one, use its existing owner. For problem evidence and
whether to build, use [product discovery](../orbyn-plan/references/product-discovery.md).

This skill does not train models, install an SDK/provider, enable capture, purchase
access or authorize live calls. A security scan still needs its own explicit request.

## Method

1. **Start from the user's task** and the consuming project's current source, authority, provider capabilities and data policy. AI is an implementation choice, not the outcome.
2. **Compare the baseline.** Weigh the existing/manual or deterministic baseline before adding a model, retrieval pipeline or autonomous loop. Use the smallest design that can meet the task's quality, latency, cost and failure requirements.
3. **Select the changed boundary** and read only its method:
   - [Application contract](references/application-contract.md): use-case baseline, model versus workflow/agent, prompt/context versions and structured outputs.
   - [Grounded retrieval](references/retrieval.md): ingestion/query lineage, permission filtering, source quality and answer support.
   - [Tool effects](references/tool-effects.md): proposals versus authorized effects, semantic validation, approval, unknown outcomes and bounded loops.
   - [Streaming interactions](references/streaming-interactions.md): typed progress, state convergence, terminal witnesses, passive history and supported pending resume.
   - [Assistant-chat UI](../orbyn-ui-design/references/assistant-chat.md): consuming-product components/tokens, composer/runtime ownership, safe parts and reading intent.
   - [Task evaluations](references/evaluations.md): representative slices, independent outcomes, repeated comparisons, calibrated grading and privacy.
   - [Operation and change](references/operations.md): version bundles, budgets, fallback, qualification, rollout and retention.
4. **Connect the owners.** Use [backend design](../orbyn-backend-design/SKILL.md) for actual authorization, state, concurrency and effect mechanics, and [UI design](../orbyn-ui-design/SKILL.md) for usable suggestions, progress, correction, manual alternatives and recovery. Use [TDD](../tdd/SKILL.md) for deterministic contract regressions and the [CI owner's designated gates](../orbyn-ci-design/references/change-scope.md#designate-gates-for-the-feature-worktree) for affected checks. Ordinary unit tests and task-quality evaluations answer different questions.
5. **Put security controls at actual data/effect boundaries.** A prompt instruction or schema is neither authorization nor an injection barrier.
6. **Deliver** the selected baseline/design, inputs and trust boundaries, permission and output/effect contracts, versioned evaluation plan/results, resource bounds and unverified surfaces. Distinguish a proposed experiment, offline fixture, live provider observation and released behavior.

Missing credentials/data/authority are limits, not reasons to install, fabricate results or run paid calls.

The [document-assistant example](examples/document-assistant.md) connects retrieval, revocation, a tool timeout and evaluation without requiring a provider. Methods are original local guidance; linked primary sources are research/update pointers, not mandatory downloads or imported workflows.
