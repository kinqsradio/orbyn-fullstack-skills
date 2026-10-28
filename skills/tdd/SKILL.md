---
name: tdd
description: "Design focused contract tests, failing-before regressions or verification of critical properties; use for requested TDD, model checking and verification drift, with practical boundaries and explicit evidence limits."
---

# Tdd

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

An implementation or repair request normally includes focused local regression
checks. Respect tests excluded by the current user, session or consumer policy;
this skill grants no production or live-provider authority.

Identify the smallest observable contract. Reproduce the defect in a test at its
owning boundary, run it before the fix and check it fails for the intended reason.
Make the production correction, then rerun that check and relevant adjacent cases.
Do not test a copy of the implementation or weaken assertions to obtain green.
Use the [reproduction contract](../how/references/reproduction.md) for baseline,
fixture and runner discovery. Confirm the intended test actually ran; zero
selected tests, an unrelated setup error or a skipped mode is not regression proof.

If the practical test requires unrelated harness churn or unrealistic mocks,
explain the limitation and use the closest authorized evidence. Retain failing
attempts. A passing new test without a demonstrated baseline failure provides
less regression evidence; state that distinction. No production databases or
unapproved live-provider calls. Read [development](../orbyn-workflow/references/project-policy.md#development-resources)
for guarded database and package prerequisites.

## Regression evidence across layers

Test observable contracts at real effect/adaptor boundaries. Keep mocks focused
on unavailable effects rather than private helper choreography. Build and verify
one failing contract at a time, then extend from observed behavior; do not write
a speculative batch before confirming that the first signal catches the defect.
An internal reorganization should preserve useful behavior tests.

For a stale update, place the regression at the API/version boundary and assert that the rejected write preserves the original record. A snapshot of the error string alone does not prove the invariant. Add a UI check only when the changed user flow needs separate evidence and that check is authorized.

## Operational method

Use the [local operating method](references/operating-method.md) for the execution
sequence, concrete failure case, expected result and stopping condition. It is
Orbyn-authored guidance; historical source notices remain in provenance.

## Choose a useful strategy

For a critical invariant, event-order race, explicit formal verification request
or stale verification model, use [property verification](references/formal-verification.md)
and its [drift review](references/verification-drift.md). Choose tools from the
property and real code, demonstrate a failing control, and distinguish model
results from implementation evidence. Ordinary small UI edits need no formal model.

For requested test design, use [test strategy](references/test-strategy.md) to select the real boundary, fixtures, failure controls and execution scope. A plan can be the requested output; this skill does not turn every test request into mandatory production edits.

For model-powered application quality, pair deterministic permission/state tests
with [task evaluations](../orbyn-ai-application/references/evaluations.md).
A correct schema or one expected answer is not a reliability estimate; preserve
held-out cases, repeated-trial failures and critical slices. This does not require
live model calls for ordinary deterministic changes.

When clocks, async cleanup, readiness, module identity or runner legs can hide the
assertion, use [test reliability](references/test-reliability.md). Preserve actual
production/fixture boundaries and first-attempt evidence.
