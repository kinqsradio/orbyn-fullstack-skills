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

Establish the upfront goal, permitted effects/resources, result destination and
bounds. Continue authorized investigation, drafting, verification and recovery
without repeated stage approvals. Ask only for a required unresolved fact or a
concrete effect outside the current grant; continue independent permitted work.
Routine reversible commands need no new preview ceremony. A changed consequence
still requires the appropriate authority at its actual boundary. UI/control labels
follow the [content outcome method](../../orbyn-content-design/references/outcomes-and-attention.md);
they do not themselves pause execution, revoke grants or confirm a stop.


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

For a requested report-to-thread/tracker integration, use the conditional
[trusted intake contract](trusted-intake.md). It defines admission/dedupe and
compensation requirements; it does not ship or authorize a provider adapter.

## Mutable catalogs and decoder boundaries

Tool registration/catalog visibility is not execution authority. A shallow
registration snapshot does not freeze a mutable producer's nested payloads; copy
or version the data at the owning boundary when immutable replay is the contract.
Test mutation after publication against the actual consumer, not a frozen stand-in.
Provider pass-through envelopes may intentionally preserve unknown extension
fields; closed orchestration decisions and authorization variants still require
explicit exhaustive validation. Do not make all decoders permissive to support one
provider extension. Replays use selected redacted exchanges and fixed identities;
no key or live provider is needed for a deterministic contract fixture.

Effective authority may combine account, agent/session and saved policy. Check the
actual resulting allowed effect and current resource identity, rather than assume
that inherited context grants access. A query-level rule or a permission prompt
does not prove internal path fencing, credential separation or OS sandboxing.
Declare and test those boundaries separately within authorized disposable scope;
retain a denial rather than widen policy to obtain a passing result.

## Carry a tool/API change to its intended consumers

Use when adding/changing a generated API or model-callable application tool.
Trace schema/generator, domain effect, registration/context, adapters and intended
result consumers. Reuse actual service/client owners, not another parallel tool
framework. The [CI evidence map](../../orbyn-ci-design/references/verification-map.md#generated-outputs-and-intended-consumers)
owns generation/drift and consumer disposition.

Synthetic `archiveItem` integration:

| Boundary | Required evidence when this consumer exists |
| --- | --- |
| Schema and generated surface | Owner defines validated input and archived/denied/stale results; supported regeneration/check has no unexplained drift |
| HTTP and tool adapters | Both call the same authorized domain operation with current principal, resource, version and logical operation identity |
| Tool discovery/context | Registered callable name, argument/result schema and permitted contextual scope reach the actual orchestration consumer |
| Intended client/result | Shared client invokes the method; the product's required renderer/manual result path explains confirmed, denied and uncertain outcomes |
| Deliberate absence | Internal-only endpoint may have no public SDK or visible renderer; record that contract instead of adding a fake consumer |

Select a legitimate archive, denied cross-scope resource and stale version through
both adapters where supported. A shape-valid tool call must still be denied by the
domain owner. A missing registration or required result handler is incomplete even
when types compile. A stale exclusion/nonexistent skipped method fails the coverage
claim; a justified internal-only absence is legitimate. If the write commits but
refresh/presentation fails, reconcile the existing receipt instead of archiving a
second time. Adapter stubs establish their controlled contract, not provider
acceptance or end-to-end production execution. No model call is needed to test
this deterministic path.
