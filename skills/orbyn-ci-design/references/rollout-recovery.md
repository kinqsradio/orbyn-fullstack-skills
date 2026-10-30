# Health-driven rollout and recovery

Use for a requested release/rollout plan, deployment change or incident recovery.
Planning does not grant production access or execution authority. Existing service
runbooks, operators and release policy own the process. A CI artifact verification
is a prerequisite, not evidence that deployment succeeded.

Before an authorized rollout, bind the candidate, artifact digest, configuration,
feature flags, schema compatibility and destination to the release record. Name the
operational owner, observability route and recovery mechanism. Choose health signals
for the affected behavior: errors, latency, saturation, queue age, data integrity
and an appropriate user outcome. Establish a current control/baseline, observation
window and stop thresholds from service policy and workload; do not invent generic
numbers or treat missing telemetry as healthy.

Use the project's supported pilot/canary or progressive exposure mechanism when
risk and infrastructure justify it. At each step compare the exposed cohort with
the control, account for traffic volume and delayed jobs, and inspect relevant
business/data signals as well as HTTP success. Promote only when the required
observations are complete. Preserve the release identity as exposure changes.
A small low-risk release can use a simpler existing mechanism.

Stop on a breached threshold, incompatible writer, missing required telemetry or
unexplained regression. Separate stopping new exposure, disabling a feature,
rolling back code and restoring data: they have different effects. Verify that the
old binary can read current data before rollback. For irreversible conversions,
use the agreed forward repair/restore plan; do not start old writers against the
new format. Recheck health after recovery, including queued work and affected users.

During an incident, prioritize the authorized reversible mitigation, preserve
minimal diagnostic evidence, and use the service's communication/escalation policy.
Do not delay mitigation for a broad redesign or send unrequested messages. Record
what was mitigated, what remains impaired, owner and next check. Afterwards route
the demonstrated cause to `how`, the correction to its owner and a focused
prevention/control check. A green dashboard alone does not close a data-integrity
incident.

Example: a new worker is fast on fresh events but repeatedly fails old queued
payloads. Pause expansion, inspect queue age/retries by version, fence incompatible
writers as needed, and validate the chosen recovery against old payloads before
resuming. Report deployed exposure and recovery separately from CI pass state.

Primary context: [Google SRE canary releases](https://sre.google/workbook/canarying-releases/)
and [Azure safe deployment practices](https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/safe-deployments).
These are background links; the local method and consumer runbooks remain usable offline.

## Incident coordination and aftercare

For an active incident, use the service's severity/escalation rules and identify
one incident owner, operational responders and a communication owner where needed.
The agent may prepare an update; sending it requires existing authorization.
Record observed impact, start/last-known-good times, candidate/configuration changes,
mitigations and next check. Label hypotheses separately from facts. Prioritize
restoring the affected outcome before completing root-cause analysis.

At handoff, state current exposure, impaired users/data, running mitigations,
who owns the next decision and how to resume/revert safely. After recovery,
prepare a blameless causal timeline and bounded prevention actions with owners
and verification. Distinguish the trigger, contributing conditions and missing
controls; do not settle on “human error.” Verify restored user/data outcomes and
resolve follow-up ownership rather than closing solely on green HTTP health.

Primary background: [Google incident response](https://sre.google/workbook/incident-response/).

## Feature flags across entrypoints

Use when a rollout flag changes behavior. Resolve its actual owner, evaluation
location, cohort/exposure semantics, override precedence, unknown/error policy,
kill switch and removal owner. Keep existing flag tooling; a local deployment-only
switch need not become a remote service. Flags choose availability, not permission.

Represent unresolved, off, on and evaluation-error according to the contract.
Do not coerce an unresolved cold read to off and start a destructive migration or
persist a fallback choice. A target may deliberately serve a safe baseline while
pending or on error; that is an explicit fallback, not proof the remote flag is off.
Preserve current resource authorization even when stale state says on.

Synthetic archive rollout: route/deep link, command and tool adapter must agree on
availability and domain authority. Exercise a cold unresolved deep link, resolved
off with the supported baseline, on with allowed/denied resources, evaluation error,
and an on-to-off kill-switch change. Include retained caches/subscriptions where
they could preserve stale availability. The kill switch fences new work under its
actual contract; it does not undo committed effects or prove active jobs stopped.
Name behavior for in-flight work, overrides and reconnect/restart. Test the real
entrypoints affected; inspecting only the visible button is incomplete.

Retire temporary flags after required readers, cohorts and rollback compatibility
are accounted for. Never leave a second permanent implementation accidentally.
Changing a live remote flag remains a separately authorized operational effect;
ordinary local code changes do not acquire repeated stage-approval prompts.
