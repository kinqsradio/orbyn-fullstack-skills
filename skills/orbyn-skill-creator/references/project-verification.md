# Leave a maintainable project verification check

Use only when authorized work warrants a durable check of a named critical
property. Reuse the project's existing tests/specification owner first. Create a
project-local skill only if an agent needs repeatable instructions that existing
project guidance does not supply. A visual prototype alone needs no new skill.

Follow [target ownership](../../orbyn-setup/references/project-skills.md): use the
target's documented paths, naming, host discovery and authoring checks. If no
convention exists, use an appropriate project-owned verification/test location;
select a host-specific skill path only when discovery is actually needed and
supported. Do not impose `project-skills/`, install both host links, move foreign
guidance, or register target material in the shared catalog/manifest.

Leave a complete local contract, without depending on our checkout's absolute path:

- Trigger: covered property and changes that require another check.
- Coverage: source files/functions and other writers, revision or dirty source
  digests, model/harness/config digests and last confirmed correspondence.
- Execution: exact existing command, pinned tools, prerequisites, bounds,
  assumptions, timeout/resource budget and expected termination/results.
- Interpretation: plain-language rule/harm, model scope, counterexample replay,
  negative control and distinct model-only versus real-code evidence.
- Maintenance: [drift review](../../tdd/references/verification-drift.md), including
  renamed/new writers, unchanged intended properties and blocked outcomes.
- Lifecycle: owner, tracked durable sources, ignored raw results and cleanup/
  restart instructions for task-owned resources.

Follow the new instructions once from a fresh disposable context. Run the actual
check, demonstrate detection of a relevant broken variant, restore and rerun.
If it cannot run or cannot detect the break, label it draft/blocked and correct
the check within scope. Do not claim qualification from writing instructions.

This selected adaptation is recorded in [the source record](verification-source.md).

## Non-formal application and command adapters

A repeatable user-journey check need not be a formal model or a new skill. Keep
its launch, read-only doctor, drive, capture and cleanup commands in the consumer's
existing verification owner. Resolve real supported commands/accessible handles;
placeholders and guessed screen coordinates leave the recipe draft.

Launch in owned disposable storage and wait for usable journey readiness, including
required migrations, seeds and authentication. A health endpoint alone may answer
before those prerequisites finish. Doctor checks exact build/candidate, instance
ownership, URL, storage and account without modifying them; a matching port is not
identity. Declare whether an owned server persists between recipes or each CLI/PTY
starts with fresh state. Never reuse an unrelated user's instance or spawn a server
for an ordinary library test.

Drive one actual entrypoint to its observable result. Capture the initiating action,
resulting UI/output and relevant persisted/external effects; reopen or read back
committed data through a second appropriate view when persistence is promised.
Fixture setup can establish preconditions; injecting the promised final state
cannot prove the action. Dry-run labels are not safety evidence: observe actual
file, network and ref effects, including reads/fetches/browser startup, under the
allowed effect scope. Keep every alternate shortcut/CLI route separately evidenced.

Declare seed/reset conditions before each independent recipe. On a surprising
result rerun doctor; a healthy server can still have a wedged UI. Reset/relaunch
only the owned fixture if needed, preserving the failure. After repairing a selector
or harness, re-drive the real journey before advancing qualification. Cleanup stops
owned processes, preserves proof and verifies retained artifacts can be reopened.
A fresh-context attempt of the documented commands is required for a cold-usable
claim; report docs-as-written separately from inferred recovery. Missing credentials
or entitlements are environment blockers until evidence establishes a documentation
error. Record attempted path, actual unmet prerequisite and next discriminating check.
