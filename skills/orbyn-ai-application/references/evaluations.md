# Evaluate the task and the consequences

Use when changing model, prompt, retrieval, tools, context strategy or AI behavior.
Reuse the project's evaluator and evidence storage; no new paid service, judge,
model call or trace capture is implied. Offline planning/fixtures can be the
requested result. Deterministic [contract tests](../../tdd/references/test-strategy.md)
protect permissions, schemas and state; task-quality evaluation addresses variable
answers and decisions. Neither substitutes for the other.

## Define cases before tuning

State the target population/task, baseline, success/failure criteria and material
error costs. Use consented/redacted data only under the applicable policy, or
synthetic cases labelled as such. Version inputs, expected source/outcome evidence,
case provenance and intended usage; synthetic tests do not prove user demand or
production representativeness. Split tuning/development from held-out assessment;
group near-duplicates/users/sources where leakage matters. Do not tune against the
holdout or rewrite its rubric after observing results. Record exposure if a set
must become development data and reserve a fresh assessment set.

Cover ordinary tasks plus relevant languages, accessibility/task contexts, long
inputs, unsupported/no-evidence questions, stale/revoked permissions, adversarial
content, conflicting sources and provider/tool failures. Name critical slices
that cannot be traded away by a strong global average. For actions, check actual
final state, allowed intermediate effects and receipts; a model's success claim,
expected wording or correct tool selection alone is not an outcome oracle.

## Compare fairly and grade independently

Freeze baseline/candidate bundles and name the intended changed variables. Hold
non-target cases, fixtures, tool protocols, settings and budget constraints fixed;
record provider/model configuration per condition. A model/provider comparison may
change that factor deliberately; unavoidable environment differences are confounds
to report, not evidence of its isolated effect. Model outputs vary: use repeated paired
trials at a sample size justified by the risk and variability. Preserve all failed,
refused, timed-out and exhausted attempts. Report denominators, variation and
uncertainty; one lucky transcript or one run per case is a smoke check, not a
reliability estimate. Do not claim statistical significance without a suitable
analysis or causal user impact from an offline benchmark.

Prefer independently checkable outputs/outcomes where possible. For judgment
rubrics, use explicit criteria and calibrate against human-reviewed examples,
including known wrong/unsupported answers. Check judge bias, position/order effects,
self-preference, disagreement and susceptibility to instructions in answers. Keep
untrusted text out of judge instructions. Record judge/version and calibration
limits; agreement between models does not establish truth. Borderline or critical
failures need accountable review rather than averaging them away.

Record useful task completion, unsupported answers, appropriate abstention and
false refusals separately. Do not rerun until green, discard flaky attempts or
let a judge approve application effects. Log necessary redacted observable events
and outcomes, not hidden chain-of-thought or private reasoning traces.

Report retrieval relevance/coverage separately from answer correctness/support and
tool-effect correctness. Include end-to-end and relevant phase latency, time to
useful output, total cost/work including retries, failures and parallel steps.
Name measurement method, units and version-dependent pricing assumptions; token
counts are not automatically billed amounts or user value. Quality, authority and
resource budgets need explicit acceptance thresholds and a keep/revise/stop rule.

Retain only authorized minimal evidence: case/run IDs, versions, outcome categories
and necessary redacted excerpts. Do not upload raw private prompts, secrets,
documents or traces to judges/loggers. Apply retention/deletion/access rules to
managed derivatives. Return results and blocked/unperformed checks honestly, then
select [affected gates](../../orbyn-ci-design/references/change-scope.md) for the
changed boundary; do not make every edit a whole-app or paid-model sweep.

Research/update pointers reviewed 26 October 2026: [agent evaluations, January 2026](https://www.anthropic.com/research/demystifying-evals-for-ai-agents),
[RAGAs, EACL 2024](https://aclanthology.org/2024.eacl-demo.16/).
Original local synthesis; no source text, SDK or runtime imported. These methods
work offline; current provider/version claims still need applicable verification.
