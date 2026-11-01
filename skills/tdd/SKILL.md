---
name: tdd
description: "Design focused contract tests, failing-before regressions or verification of critical properties; use for requested TDD, model checking and verification drift, with practical boundaries and explicit evidence limits."
---

# TDD

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

An implementation or repair request normally includes focused local regression
checks. Respect tests excluded by the current user, session or consumer policy;
this skill grants no production or live-provider authority.

## Method

1. **Freeze the observed defect,** expected invariant and the smallest observable contract at a practical authorized test boundary. Use the [reproduction contract](../how/references/reproduction.md) for baseline, fixture and runner discovery.
2. **Write one regression** at the owning boundary, exercising the actual production path rather than a copy of the implementation. Assert state or externally meaningful behavior rather than private helper calls. Keep mocks on unavailable effects at real effect/adaptor boundaries, away from private helper choreography.
3. **Run it against the unchanged candidate first.** Confirm the intended test actually ran; zero selected tests, an unrelated setup error or a skipped mode is not regression proof. Check that it fails for the reported contract violation, not a missing dependency or broken fixture. Retain failing attempts.
4. **Make the smallest coherent production correction,** then rerun the same case, directly affected controls and relevant adjacent cases. Never weaken assertions to obtain green.
5. **Extend one failing contract at a time** from observed behavior. Confirm the first signal catches the defect before writing more, rather than a speculative batch.
6. **Refactor only after the meaningful signal is green.** Internal reorganization should preserve useful behavior tests, so keep contract tests rather than coupling them to the new implementation.

For a stale version write, place the regression at the API/version boundary. Arrange an existing record and newer version, send the stale mutation, and assert both rejection and unchanged persisted data. A snapshot of the error string alone misses a write that succeeds before returning an error. Include a legitimate current-version control when it distinguishes an overbroad rejection. Add a UI check only when the changed user flow needs separate evidence and that check is authorized.

## When the ideal test is out of reach

- Baseline execution unavailable: record that limit. A passing new test without a demonstrated baseline failure is weaker regression evidence, so state that distinction and do not call it failing-before evidence.
- The practical test requires unrelated harness churn or unrealistic mocks: explain the limitation and use the closest authorized evidence.
- No production databases or unapproved live-provider calls. Production databases and paid providers require their own applicable authority. Read [development](../orbyn-workflow/references/project-policy.md#development-resources) for guarded database and package prerequisites.

## Read when needed

- A repair that retains a previously ignored value: the [propagated-value method](references/propagated-values.md).
- A critical invariant, event-order race, explicit formal verification request or stale verification model: [property verification](references/formal-verification.md) and its [drift review](references/verification-drift.md). Choose tools from the property and real code, demonstrate a failing control, and distinguish model results from implementation evidence. Skip the formal model for ordinary small UI edits.
- Requested test design: [test strategy](references/test-strategy.md) to select the real boundary, fixtures, failure controls and execution scope. A plan can be the requested output; this skill does not turn every test request into mandatory production edits.
- Model-powered application quality: pair deterministic permission/state tests with [task evaluations](../orbyn-ai-application/references/evaluations.md). A correct schema or one expected answer is not a reliability estimate; preserve held-out cases, repeated-trial failures and critical slices. Ordinary deterministic changes do not require live model calls.
- Clocks, async cleanup, readiness, module identity or runner legs that can hide the assertion: [test reliability](references/test-reliability.md). Preserve actual production/fixture boundaries and first-attempt evidence.
- Actual Expo/RN requested-screen, binary/device and native evidence: [mobile verification](references/mobile-verification.md). Deterministic fixtures and screenshots do not close missing platforms or paid-service cells.
