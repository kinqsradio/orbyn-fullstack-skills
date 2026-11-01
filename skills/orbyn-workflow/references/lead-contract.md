# Lead, delegate, review and deliver

Use for substantial work, before dispatching a child or reviewing returned work.
A small clear edit or narrow explanation can proceed directly under the
[workflow](../SKILL.md).

## Lead contract

The owning lead grounds and scopes the outcome, chooses the design and delegates
substantial investigation and implementation as applicable. The lead stays
responsible for integration, review and verification. A child forbidden further
delegation completes its assigned task directly and returns the artifact to its
owner; it never waits for a nested worker.

Before dispatch, establish the requested end state, exclusions, current checkout
and candidate, owning data/contracts, failure behavior and authorized evidence.
For continuation, choose the minimum [task record](task-record.md) that preserves
the next action; use a [structured handoff](handoffs.md) only when validation helps.
Reconcile stale revisions before acting. Routine work can rely on its existing
diff, PR and CI without another log. Resolve blocking facts first. Use the selected
playbook to shape the work rather than repeating every workflow phase.

For multi-step implementation, write a short throughput checkpoint:

- Blocking first steps before dispatch.
- Independent workstreams and their owned paths.
- Shared mutable state to separate or serialize under one owner.
- Smallest safe decomposition, including why one worker is sufficient when coupled.

Mark an inapplicable dimension briefly instead of manufacturing parallel work.
For read-only investigation, one line naming the independent slices or why one
investigator is sufficient is enough. Revisit the checkpoint when a phase changes
ownership or dependencies.

## Delegate within the current session

Follow the [consumer host and coordination boundary](project-policy.md#delegation-and-host-configuration).
Use configured named roles and preserve the required model, effort and processing
mode. If the host cannot do so, report the limit and continue permitted direct
work. Never silently substitute a model, launch a hidden inference process or
install a provider. Library model presets are optional; consumer-owned policy wins.

Give each child its role, outcome, source/candidate, owned files, allowed effects,
exclusions, relevant pointers and stopping condition. Reuse matching children;
tell writers they share the checkout and must preserve others' work. Default to
one child, at most two, without recursive delegation. Split independent outputs
only; serialize shared generated files and fixtures. Children return evidence to
the lead, who owns integration and review.

New sidebar/project chats require an explicit human request. This workflow
authorizes bounded native children, not extra user-owned sessions or messages.
Do not create sessions recursively or turn design comparison into a model panel.

## Execution invariants

Complete the agreed outcome, including necessary caller migration and removal,
without silently expanding authority. Use a small reusable tool for proven
repetition when its cost and failure behavior justify it. Separate concurrent
writers' files, fixtures and resources before serializing what truly must be shared.
Match each completion claim to direct evidence for the requested artifact; retain
missing checks as limits. Read the conditional methods for
[outcomes](principles/outcome-oriented-execution.md),
[automation](principles/build-the-lever.md),
[shared state](principles/separate-before-serializing-shared-state.md) or
[proof](principles/prove-it-works.md) when needed.
For requested rollout or incident work, use the CI owner's
[health and recovery method](../../orbyn-ci-design/references/rollout-recovery.md).

## Review

For substantial work, the lead must inspect the actual returned artifacts and
diff against the intended contract, including affected callers, authority,
failure/recovery and unrelated changes. Treat a delegate's summary as evidence to
inspect. Route concrete fixes back to the same child and review the resulting
diff. The lead writes the final assessment.

## Verify

The lead performs verification proportional to the changed contract and inspects
its results. An implementation request includes appropriate local checks unless
explicitly excluded; respect consumer limits and separate external effects.
Documentation needs document/link checks rather than product builds. When runtime
or surface evidence is unavailable or excluded, report that limit explicitly.

Additional independent Verifier/Reviewer assignments are optional unless requested.
Requested independent qualification uses the same frozen candidate and at most
three full review rounds under [delivery](project-policy.md#verification-and-review).
This limit applies to requested independent qualification, not ordinary lead
correction loops.

## Deliver

Deliver only the requested scope. Report changed behavior/artifacts, actual
evidence, unresolved limits and local/committed/pushed/merged/deployed state.
Report the result without ceremonial principle citations.

For authorized delivery, verify the successful owned commit and its validated tree
before pushing. A failed stage/commit stops dependent push, PR and CI actions; do
not treat a later command's success as repairing that missing prerequisite. Use
the [commit and push gate](../playbooks/opening-a-pr.md#commit-and-push-gate) for
the execution and remote-ref checks. Preserve the patch when host metadata is
blocked. Start a PR, merge, publish, deployment, external message or monitor only
under explicit authority; delegation and playbooks grant none.

If the current task demonstrates a meaningful general skill gap, follow the
[optional contribution feedback](../../orbyn-skill-creator/references/contribution-feedback.md):
prepare a concrete proposal, then offer it once without blocking the user's task.
Keep company-only material local. Publication, self-edits, telemetry and cross-user
learning stay off unless separately authorized; exact existing contribution
authority still applies.
