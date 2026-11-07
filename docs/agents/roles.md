# Roles and artifacts

Roles describe responsibility, not separate permanent chats or model identities.
A role runs on a tier chosen by the resolved [harness](harness.md).

| Role | Owns | Returns | Default tier |
| --- | --- | --- | --- |
| Lead | Scope, decisions, integration and delivery | Reviewed result with actual evidence/limits | lead |
| Investigator | A bounded source/runtime question | Anchors, mechanism and uncertainties | worker; scout when bounded and mechanical; lead when diagnosis is ambiguous |
| Architect | A consequential contract | Interfaces, lifecycle, failure and compatibility | lead |
| Engineer | Assigned implementation and cleanup | Changed artifact/diff and authorized checks | worker (Claude: all routine and feature work; Codex: bounded work, complex work goes to lead) |
| Designer | Product UI, copy and behavior not yet in the designs, plan or artifacts | A draft with the flow, every state and the copy (no product edits), using [UI design](../../skills/orbyn-ui-design/SKILL.md) and [content design](../../skills/orbyn-content-design/SKILL.md) | Claude: worker (`sonnet`); Codex: lead (`gpt-6.1-sol`) |
| Reviewer | Read-only challenge of a candidate | Concrete scenario, location and impact | lead for consequential review |
| Verifier | An assigned evidence boundary | Candidate, observation and exclusions | worker; scout when running a named check |

All security work runs on the lead tier. A scout never decides: it searches,
extracts, classifies, regenerates files, runs a named check and makes tiny
mechanical edits under clear instruction. When a worker fails or the task proves
ambiguous, escalate one tier to lead and record the reason.

The [model policy](model-policy.md) lists the tiers and defaults; the host decides
availability. Children never create recursive agents or extra project sessions.
