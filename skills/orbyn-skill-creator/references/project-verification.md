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
