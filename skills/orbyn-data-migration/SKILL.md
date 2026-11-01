---
name: orbyn-data-migration
description: "Plan and implement stored-data, schema and writer migrations with compatibility, cutover, retry and recovery evidence. Use for durable format changes; not a routine in-memory type refactor or permission to run production migrations."
---

# Migrate data with an explicit writer boundary

Read the consuming project's migration conventions and current schema. Use
[architect](../architect/SKILL.md) for an unsettled model.

Production execution, backups, operator cutover and irreversible retirement remain
within the user's explicit effect scope.

## Method

1. **Find every active reader and writer,** including jobs, released clients and cached payloads. Do not infer deployed writer state from a local branch.
2. **Define the change:** old/new representation, invariant, migration identity and cutover condition.
3. **Write the cutover contract.** The final design or implementation handoff for a durable transition must identify **active writers and versions, allowed writes per phase, the actual enforcement point, old-writer rejection/current-writer control evidence, and compatible recovery**. Use the [writer cutover method](references/writer-cutover.md). An API flag or lock that an old/direct writer bypasses is insufficient. Unknown writer state blocks unsafe conversion or retirement, not safe discovery or compatibility work. For a pure in-memory refactor, explain why this durable cutover contract is inapplicable.
4. **Choose phases:** expansion, backfill, reader/writer transition and retirement, only as the system needs them. Name what can run concurrently with each phase. A lock helps only when all writers honor it; an older deployed service may require fencing or shutdown before data conversion. Retain compatibility for external clients that cannot move atomically.
5. **Make backfills bounded and resumable** at a durable cursor or operation key. Account for deleted records, partial batches, transactions, unique constraints and evolving data while the migration runs.
6. **Define recovery.** Keep original values or a defined recovery route when conversion loses information. Avoid “rollback” instructions that restart old writers against an incompatible format.
7. **Exercise it, when authorized,** in a disposable environment: representative old data, a partial/retried migration, legitimate concurrent behavior and recovery. Capture the exact schema/candidate and counts without exposing user payloads. A dry-run query is not a completed data conversion.
8. **Deliver** the migration and caller changes, phase/order, actual evidence and remaining operator steps. Keep the owning product guide current rather than creating a second backlog.

For example, replacing one task time range with multiple sessions changes stored records, API shapes, background work and calendar rendering. Define the translation and ownership once; several UI adapters cannot establish storage compatibility. [Cutting over session writers](examples/session-cutover.md) shows why a backfill is insufficient while a legacy writer remains active, with staged recovery.

## Incident recovery

The final plan must separately gate reopening and closure on reconciled data, user-visible success, and queued/replayed work health. Name the operational owner, observation window and stop conditions; missing targets or telemetry remain unresolved. Use the [recovery method](../orbyn-ci-design/references/rollout-recovery.md). Confirm recovery through these gates; a successful writer control alone is insufficient.

## Independently released consumers

Use the task's [impact map](../how/references/impact-map.md) to identify stored, event, generated and external readers/writers, their owners and supported versions. Pilot representative old/new coexistence and a failed/retried batch before wider backfill. Track durable progress, counts, rejected records and drift without exposing payloads. Reconcile intervening writes and deployment changes before resuming. Fence or drain incompatible writers using the system's actual mechanism, and retire compatibility only after explicit adoption and integrity evidence. A source search or local schema migration cannot establish that old deployed writers stopped.

## Read when needed

- A costly concurrent cutover: [property verification](../tdd/references/formal-verification.md) to model writer admission, durable fencing, in-flight writes, retries and phase transitions at their actual atomic boundaries. A useful rule is that an old-epoch writer cannot commit after the cutover fence. Replay a counterexample against the real storage boundary and assert unchanged effects on rejection. A bounded model pass cannot establish that old deployed processes have stopped.
- Effect boundaries: [backend design](../orbyn-backend-design/SKILL.md).
- A repeatable qualification lane: [CI design](../orbyn-ci-design/SKILL.md).
- Internal APIs without durable/wire changes: the architect's [staged change method](../architect/references/large-changes.md).
