# Decide what is worth building and how to learn

Use for an uncertain product opportunity, prioritization or outcome-validation
request, not every implementation ticket. An explicit well-defined small fix can
proceed directly. Keep the existing brief/decision record; do not impose interviews,
a telemetry SDK, an A/B test or a new product-management framework.

## Frame evidence before a solution

Name the affected segment, task, current journey/workaround, observed difficulty
and baseline. Distinguish direct observations, reported needs, aggregate behavior
and assumptions. Record source/date, relevance and sampling limitations. Do not
invent interviews, personas, quotes, demand or stakeholder agreement. A request
for a feature is evidence of that request, not proof of its proposed solution.
Use [user evidence](../../orbyn-research/references/user-evidence.md) for ethical
collection and interpretation; ordinary desk research cannot substitute for users.

Compare no change, a manual/process improvement, a smaller deterministic feature
and the proposed investment where viable. Consider severity/frequency, underserved
users, accessibility, support/operation cost, reversibility and opportunity cost.
Avoid precise prioritization scores when inputs are unknown. Name assumptions
that would change the priority and the actual decision owner when unresolved.

## Choose the smallest useful learning step

Identify the riskiest uncertainty: need, usability, feasibility, authority, value
or adoption. Choose the cheapest ethical observation that could change the decision.
Existing support evidence may resolve a wording problem; an openable prototype can
resolve a task-flow problem; a technical spike can resolve integration uncertainty.
Neither a polished prototype nor an engineering benchmark proves demand.

Define the hypothesis, comparison/baseline, participant or event eligibility,
primary measure, denominator, observation window, guardrails and keep/revise/stop
rule before observing outcomes. Explain missing baselines and uncertainty rather
than fabricating numbers. Select measures tied to useful task completion; clicks,
feature counts, model fluency or shipment alone are not product value. Instrument
only when authorized, using existing systems and minimum necessary fields.

For a randomized experiment, verify allocation/randomization unit, exposure,
contamination, sample-size/power assumptions and data quality. Investigate sample
ratio mismatch and broken instrumentation before interpreting effects. Avoid
peeking, repeated unplanned comparisons and causal claims from uncontrolled
before/after changes or convenience samples. If randomization is impractical,
state the alternative design and its inference limits. Do not run experiments on
people or add production telemetry simply because the plan mentions them.

## Hand off and revisit

Separate implementation acceptance (the feature meets its contract) from outcome
learning (it improves the intended user's task). Define both when relevant; do
not block a bounded engineering fix on an invented business experiment. Sequence
one coherent deliverable and its recovery path, then revisit investment when the
specified evidence arrives. A negative finding can justify no build or retirement.

Return the problem/evidence, viable alternatives, chosen learning step, measures
and limits, decision/owner and next reversible action. Use [UI prototypes](../../orbyn-ui-design/references/prototypes.md)
for interaction evidence, [technical strategy](technical-strategy.md) for cross-team
adoption and [AI application engineering](../../orbyn-ai-application/SKILL.md) only
when model-powered product behavior is actually in scope. The
[no-build example](../examples/no-build-decision.md) shows a valid stopping decision.

Research/update pointers reviewed 26 October 2026: [GOV.UK discovery](https://www.gov.uk/service-manual/user-research/user-research-in-discovery),
[service metrics](https://www.gov.uk/service-manual/measuring-success/how-to-set-performance-metrics-for-your-service),
[Microsoft pre-experiment patterns](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage/),
[sample-ratio mismatch](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/).
Original local synthesis; no source text, SDK or runtime imported. These methods
work offline; current provider/version claims still need applicable verification.
