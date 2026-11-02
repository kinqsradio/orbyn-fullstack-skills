---
name: how
description: "Trace source behavior, data flow and dependency impact across code, build and runtime boundaries; reproduce and reduce defects before explaining or changing an unfamiliar subsystem."
---

# How

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

## Method

1. **Select the target.** Choose the exact target/worktree and search roots before a focused search; use [action scope](../orbyn-setup/references/action-scope.md). Locate governing root, ancestor and nested instructions separately from code filename filters.
2. **Anchor on the smallest observable entrypoint:** a route, button handler, CLI command or worker claim. Resolve its actual registration and caller before following symbols with similar names. Read types and configuration alongside the implementation, and only the smallest set of files that completes the path.
3. **Follow real callers, state and effects.** Keep a compact trace: entrypoint → validation/authority → state owner → effect → result consumer. Record inputs, validation, authority, transitions, persistence, output, errors and cleanup where relevant. Give each edge a file/symbol anchor and mark it statically established or observed at runtime. For background work, include acceptance persistence, claim ownership, terminal result delivery and cancellation cleanup.
4. **Investigate one concrete failure path beside the normal path.** Confirm execution with a caller or a run; a filename or comment alone does not establish it. When a search comes up empty, widen deliberately for the missing dependency; no match is not proof of global absence.
5. **Return the direct answer,** the few source locations needed to verify it, and meaningful unknowns. Explain the mechanism first, then critique only if requested. Avoid annotated dumps and unsupported historical explanations. Name an unresolved dynamic import, deployment setting or unavailable runtime rather than inventing the missing edge.

For an edit that disappears, follow version values through request parsing, conditional write and response handling; do not infer that a rerender caused the loss just because it is visible last. A useful explanation can follow a screen action → client method → API handler → authorization → transaction → response → rendered state. Stop at the relevant boundary and return those anchors. For an asynchronous path, identify who persists the work and who owns its terminal result.

Source tracing shows mechanics, not an author's intent. Use [why](../why/SKILL.md) when intent cannot be established from source.

## Diagnose a difficult bug

Reproduce, or label the diagnosis source-derived. Seek the smallest authorized repeatable signal for the user's exact symptom. Pin material inputs, source and timing where practical; vary one consequential factor and retain failed attempts. Separate observations from hypotheses. Trace the first producer of an invalid state before repairing consumers, and preserve user data.

If runtime access is unavailable, continue bounded source tracing and name the missing check without claiming a reproduction. Use the [reproduction and reduction method](references/reproduction.md) to pin the environment, confirm real runner selection and choose a behavioral oracle. Keep reproduction-only scope distinct from an authorized repair.

## Delegate substantial investigation

The owning lead delegates bounded source questions to named native Orbyn Investigators under the [workflow](../orbyn-workflow/SKILL.md). Pass file pointers and ask for a compact source-cited result. Stay within the resolved harness limits (`max_children`, `max_depth`) and use a scout for purely mechanical lookups; no recursive delegation; a child traces its assigned path directly. Narrow explanations stay direct. The lead inspects the evidence, reconciles contradictions and owns the final explanation.

## Read when needed

- Unfamiliar or cross-package work: the [impact map](references/impact-map.md). Include build/generator/configuration and runtime registration edges, existing review/operational owners and deployed consumers only where relevant. Stop when the decision is supported; a local caller search does not prove deployment coverage.
- Bounded searches and root causes: the [root-cause method](references/principles/fix-root-causes.md) and [context method](references/principles/guard-the-context-window.md) have concrete checks. Keep searches bounded, retain only decision-relevant anchors and record unresolved edges.
- Many CI failures: [pipeline diagnosis](references/pipeline-diagnosis.md), after the CI owner validates the complete report matrix. Preserve separate source, test, dependency and environment hypotheses; a symptom cluster is not a confirmed root cause. Reproduce a discriminating case and controls before correcting its owner.
- A consequential design or platform assumption that local tracing leaves unresolved: hand the specific unknown and source anchors to [comparative research](../orbyn-research/references/comparable-implementations.md). Understand this implementation first rather than running a GitHub-first survey.
- A requested review explanation or onboarding help: the [coaching and review method](../orbyn-workflow/references/engineering-scope.md#onboarding-and-review-that-transfer-understanding). Explain the concrete failure and smallest correction; pair the failure check with a legitimate normal-path control (for cleanup, exactly-once release and preserved result/exception). Do not claim to inspect a patch that was not supplied.
- Requested teaching, deliberate practice or a learning retrospective: [explanation and practice](../orbyn-workflow/references/explanation-and-recaps.md#understanding-and-practice) alongside the relevant source trace.
- An authored interactive explanatory figure with model-driven geometry, motion, readout and export: [technical illustration](../technical-illustration/SKILL.md). Ordinary explanations and simple diagrams stay here.
