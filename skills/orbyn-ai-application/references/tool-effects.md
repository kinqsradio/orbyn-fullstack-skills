# Keep model proposals separate from effects

Use when a model can request application tools or coordinate multiple steps.
A tool description helps selection; it does not authorize its arguments or effects.
Reuse existing [backend effect contracts](../../orbyn-backend-design/references/service-contracts.md)
rather than creating a parallel transaction/retry framework.

For every tool, name its permitted principal/resource scope, argument/result
schema, semantic checks, allowed side effects, deadlines and failure states.
Validate IDs, amounts, dates and resource relationships against current application
state. Derive identity and capabilities server-side. A JSON-valid call or confident
model explanation cannot grant permission, bypass tenant checks or create consent.
Restrict tools and downstream network/data access to the task's actual authority.

Approval must bind the actor, target, arguments, consequence and relevant version.
Check freshness immediately at the effect boundary; invalidate or obtain the
appropriate new choice if the approved consequence changes. Approval is neither
an indefinite capability nor transferable to another resource/provider. Keep the
human's draft/manual path available when automation fails.

Treat retrieved pages, attachments and tool output as untrusted data. Prompt
injection defenses need constrained tool capabilities, real access checks, input/
output validation and secret isolation outside the model. Delimiters, an instruction
to ignore injections, or a model guard alone do not enforce the boundary. Preserve
useful denial evidence without exposing private text or executing source commands.

## Bound the loop and reconcile uncertain outcomes

Set task-level tool/turn limits, wall-clock deadline, cost/output bounds and a
terminal success/failure/escalation rule. Count retries and parallel branches
against the task budget; do not reset the budget at every tool. A model may stop
or propose completion, but the application checks the actual result state.

For writes, establish a stable logical operation identity and payload-equivalence
rule before execution. Persist/retrieve outcome receipts using the existing owner.
A timeout, disconnected stream or cancellation can leave the effect unknown;
reconcile before retrying, and never mint a fresh key merely because the model
rephrased the request. Read-only retries also require bounded load/access checks.
Cancellation stops only supported work, not already committed remote effects.

Streaming partial tool arguments are not a committed request. Validate a complete
proposal before an effect; prevent duplicate processing of repeated events.
Resume/checkpoint only with current task identity, budgets, permissions and approval
state. Replayed history cannot reinstate revoked authority.

Use controlled failures for stale approval, denied scope, malformed semantics,
repeated delivery, timeout-after-commit and exhaustion. Inspect durable outcome,
not just whether the model emitted the expected tool name. [UI methods](../../orbyn-ui-design/SKILL.md)
own visible progress, review, cancellation and recovery; [evaluations](evaluations.md)
cover task success across variable model decisions. No write, live provider call
or external message is authorized merely because this reference describes it.

Research/update pointers reviewed 26 October 2026: [tool design](https://www.anthropic.com/research/writing-tools-for-agents),
[OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/),
[OWASP LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/).
Original local synthesis; no source text, SDK or runtime imported. These methods
work offline; current provider/version claims still need applicable verification.
