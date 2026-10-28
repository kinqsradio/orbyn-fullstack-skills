# Runtime forensics

Use the parent [workflow](../SKILL.md) for ownership and scope. Pin the observed
symptom, timestamp, build/candidate, process identity and environment. Resolve the
actual service, port, configuration and data owner before probing. A process
name or reused PID alone does not establish identity.

Capture the smallest authorized signal that distinguishes hypotheses: request
correlation, relevant phase timing, queue state, resource ownership or a bounded
log slice. Redact credentials and user payloads. Separate “the request was
accepted” from “the durable effect completed” and “the client received its result.”

For a stream that stops after reconnect, compare persisted operation state,
subscription identity and delivered sequence. Change one material factor at a
time. Preserve the original failure and reject explanations contradicted by the
observations. Do not restart a shared service or delete data as an automatic probe.

Use [how](../../how/SKILL.md) to map observations back to source. Return the
supported cause, candidate and signal, competing explanation, correction scope
and smallest missing observation. Remove only owned instrumentation and report
unresolved resource cleanup. Runtime evidence from one build does not qualify a
different candidate or production deployment.

For terminal startup, prompts or owned sessions, use the
[CLI/PTY method](../../architect/references/cli-contract.md). A controlled local
probe should discriminate competing mechanisms: for example correlate generation
and accepted operation state to distinguish stale subscription from dropped write,
with one matched legitimate control. Keep task-owned instrumentation bounded and
remove it afterward. Diagnosis scope grants no shared/production hotpatch authority.

Record the actual client, server and worker process/build identities separately.
Restarting a view or terminal may leave its server alive; prove ownership and
lifecycle before replacing a process. A source/reference advertisement is not a
ready running endpoint. Preserve the user's active services and settings; use an
owned fixture when a destructive lifecycle probe would exceed the task scope.
