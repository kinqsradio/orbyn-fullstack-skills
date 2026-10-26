# Choose and bound model behavior

Use for a new or changed model-powered product path. Identify the person, task,
input distribution, current journey, harmful errors and acceptable manual outcome.
Choose a measurable success rule and representative examples before a model.
A fluent answer, tool call or completed request is not task success.

Compare no change/manual support, deterministic rules or ordinary search, a single
model call, a fixed workflow and a dynamic agent. Add autonomy only for decisions
that cannot usefully be predetermined, and only with bounded effects. Record why
the simpler baseline fails the actual task; popularity and a benchmark unrelated
to the workload do not settle fit. Model choice follows the consuming project's
constraints and [stack selection](../../orbyn-stack-selection/SKILL.md), not a
mandatory vendor, SDK, RAG framework or vector database.

## Change a prompt as a testable hypothesis

Specify task, allowed inputs/context, output and failure behavior explicitly; add
representative examples/counterexamples where they resolve ambiguity. Version the
prompt and compare one stated hypothesis with the baseline using development
cases, then a protected assessment set. Do not optimize held-out examples or
mistake a prompt rule for enforced permission. A longer prompt is not evidence
of better behavior.

## Define the input and output contract

Name permitted data/recipients, supported languages and modalities, maximum input,
output and context sizes, time/cost bounds, fallback and escalation. Verify the
actual provider/version's tools, structured outputs, streaming, retention and
cancellation behavior only where the task depends on them. A documented API
feature is not evidence of this account's access or successful integration.

Version the behaviorally relevant bundle: model/provider identifier, prompts,
schema/tool definitions, context selection, retrieval/index/configuration and
limits. Identify dynamic inputs separately; do not claim a seed guarantees identical
provider results. Keep system instructions, user intent, retrieved documents and
tool results distinct. Retrieved text remains data even when it contains commands.

Budget context by relevance and authority. Reserve space for output/tool responses;
truncate or summarize deliberately with source links and important constraints
retained. Do not solve overload by concatenating every memory, document and trace.
Reject oversized/untrusted fields at the real boundary and keep secrets out of
prompts and diagnostic exports. No implicit cross-project memory access follows.

Treat generated structured output as untrusted. Schema validation checks shape,
not factual support, correct resource IDs, business semantics or permission.
Validate those independently before rendering consequential claims or committing
an effect. Bound repair/retry attempts; invalid/truncated output, refusal, unsupported input,
provider failure and no-evidence answers need deliberate user-visible states.
Do not silently swap provider or data recipient as an error-recovery shortcut.
Generated HTML, code and SQL need the consuming owner's validation, safe rendering
or constrained execution at the actual sink; do not directly evaluate/execute
model text. Schema-valid output is not trusted executable content.

For an answer-only feature, citations and abstention may be the key contract.
For an action feature, use [tool effects](tool-effects.md). Use controlled stubs
for protocol/state checks and separate authorized live observations from them.
Return the smallest chosen design and baseline, invariants, bounded inputs/outputs,
version bundle, evaluation/stop criteria and unresolved provider assumptions.

Research/update pointers reviewed 26 October 2026: [Google PAIR user needs](https://pair.withgoogle.com/chapter/user-needs/),
[effective agents](https://www.anthropic.com/research/building-effective-agents),
[context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents).
Original local synthesis; no source text, SDK or runtime imported. These methods
work offline; current provider/version claims still need applicable verification.
