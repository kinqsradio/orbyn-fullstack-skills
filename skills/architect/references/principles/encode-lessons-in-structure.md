# Encode lessons in structure

Identify the common cause before generalizing a correction. Prefer a type, schema, existing lint rule or runtime invariant where it actually enforces the property. Keep judgment in focused guidance. Do not write personal memory, trackers or organization-wide rules without authorization, or make unrelated cleanup part of every fix.

## Decision in practice

Can the owning representation rule out the recurring error?

If a conversation can show both “waiting” and “completed”, replace independent booleans with a lifecycle union at the shared contract. Update serializers and consumers together. A repeated warning in a prompt is weaker than a representation that cannot encode the contradictory state.

When that contract is a TypeScript schema, load
[TypeScript guidance](../../../language-best-practices/references/typescript.md) to carry the fix
through runtime validation, shared types and callers. For other stacks, use the
consuming project's schema owner; this principle does not choose a language.

For another implementation language, use its [local language guide](../../../language-best-practices/SKILL.md)
and the consuming project's contract owner. Preserve valid-state and runtime
validation principles without requiring TypeScript syntax or schema libraries.

## The ladder: highest level that works

A class of mistake counts once it has happened twice (two reverts, two review comments). Assume the next contributor is an agent that sees only the files it opened and copies the nearest example. For each class, take the highest rung that actually works and say why the higher ones did not:

1. **Architecture.** One owner per piece of state, one supported way per task, internals hidden so the wrong import fails, one source of truth in place of hand-synced lists. Delete the old path an agent would copy.
2. **Types.** Make the bad state unwritable (the lifecycle union above).
3. **A lint or CI check whose message names the fix.** "Use `loadConfig()` from the settings module" teaches; "bad import" does not. Where the bad pattern is already common, fail only when a change adds more. A suppression names its reason, an expiry date and who approved it. Use the project's own linter and its [rule examples](../../../language-best-practices/references/code-quality.md#turn-a-bug-class-into-a-lint-rule).
4. **A behavior test.** Fix or delete a test that still passes when the behavior breaks, or fails when only internals change.
5. **Docs or agent rules, last,** for judgment calls only. Nothing fails when an agent skips them.

Prove each check on a real past mistake: it fails on the old bad shape and passes on the legitimate neighbour. Run the same command locally and in CI. With the user's authority, keep a table in the project's agent instruction file pairing each rule with what enforces it; a rule whose mistake can no longer happen leaves the table, and a rule that nothing enforces is a repeat, so lift it a rung in the same change. A bug fix reaches this ladder from its [lint-rule step](../../../orbyn-workflow/playbooks/bug-fix.md).

## Apply and hand off

Write the recurring invalid state and identify the representation that permits it. Move the invariant into that owner and migrate its producers and consumers together.

Concrete check: Replacing two lifecycle booleans requires updating persisted readers as well as the type. Keep a compatibility path for old stored data until it is deliberately retired.

Return the changed invariant, its owning location and the observation or evidence
gap. Carry execution through [architect](../../SKILL.md) when relevant. This
principle refines that task; it does not create another mandatory phase.

## Source and license

Adapted from Lauren Tan's pstack [encode lessons in structure](https://github.com/cursor/plugins/blob/74dd2291e8e37b12fd6dc49b2acbd655c6bdaf12/pstack/skills/principle-encode-lessons-in-structure/SKILL.md),
revision `74dd2291e8e37b12fd6dc49b2acbd655c6bdaf12`. The ladder draws on pstack's
[correct](https://github.com/cursor/plugins/blob/ae5650febf4320793844c12c4adaa937f417f8da/pstack/skills/correct/SKILL.md),
revision `ae5650febf4320793844c12c4adaa937f417f8da`.
Orbyn adaptations and worked examples retain the [original MIT notice](LICENSE.txt).

For a repeated-error audit, collect the selected corrections/reverts/reviews and
cluster common causes before changing a guard. Demonstrate that the guard rejects
a representative historical/synthetic bad shape and permits the legitimate adjacent
shape. Where a durable rule already exists, link its real enforcement command or
label it judgment-only; remove obsolete duplicate warnings only when the replacement
actually makes them unnecessary. No organization-wide registry is required.
