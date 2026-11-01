---
name: orbyn-research
description: "Resolve a specific product-evidence, architectural, dependency, platform or design uncertainty using local evidence and authoritative external sources before choosing an implementation."
---

# Research for an Orbyn decision

Read [stack boundaries](../orbyn-workflow/references/project-policy.md#stack-and-ownership)
before starting.

## Method

1. **Name the decision,** the unknown and the evidence that would change the choice. Aim to settle that one decision rather than write a general technology survey.
2. **Start locally.** Trace local code with `how` first; installed manifests and current source outrank generic tutorials about this project. For a language implementation question, consult the relevant [local guide](../language-best-practices/SKILL.md) first, then verify only the unresolved target-version behavior.
3. **Go to primary sources** for external facts: official documentation, source repositories, standards or original research. Verify version and provider applicability. Use focused searches and stop when the decision is supported, leaving the rest of the domain and unrelated background alone.
4. **Resolve conflicts.** If evidence conflicts, record the conflict and the cheapest useful observation to resolve it. Evaluate compatibility, maintenance, authority boundaries, latency/cost and failure recovery relevant to the decision. For UI, evaluate task flow, readability, focus, responsive behavior and existing tokens; generic aesthetic claims are not evidence.
5. **Return a compact evidence table:** question, source/version/date, finding, implication and remaining uncertainty. Separate facts from inference and recommendations. Cite the exact page or local source near the claim.
6. **Feed findings** into `orbyn-plan`, `architect`, `orbyn-ui-design` or the owning guide. Keep only decision-relevant findings in a durable record; one research result does not warrant a new skill.

For a retry or streaming API, record the supported version, cancellation/unknown-outcome behavior and the implication for the current adapter. Separate documented availability from this account’s observed access: a documented capability does not establish that this installed host, account or configured provider supports it.

## Boundaries

- Imported examples do not authorize new external services, telemetry or CDN assets.
- Describe a needed runtime experiment's scope and use it only when authorized. Do not call a source review a benchmark or live qualification.
- A source survey or popularity alone neither settles project fit nor authorizes implementation.
- Download source or research references to the ignored local `orbyn-references/` workspace, under the exclusion/provenance rules in [upstream review](../orbyn-upstream-review/SKILL.md). Use that owner for freshness comparisons and update decisions. Raw downloads stay outside public commits; retain only reviewed findings and licensed, deliberately selected support files.

## Read when needed

- Technology recommendations: feed current primary evidence and uncertainty to [stack selection](../orbyn-stack-selection/SKILL.md).
- Consequential protocol, lifecycle, platform or performance uncertainty: [comparable implementations](references/comparable-implementations.md). Start with the local question and constraints, study relevant mechanisms and mismatches, then feed the decision into contracts and regression checks. Skip the external repository survey for familiar bounded work.
- User needs, demand or usability evidence: [user research](references/user-evidence.md). Reuse available authorized evidence, and distinguish observation from inference and research plans from completed studies. Do not invent users/results or initiate recruitment, recording or telemetry. Product investment decisions belong to [planning](../orbyn-plan/references/product-discovery.md).
