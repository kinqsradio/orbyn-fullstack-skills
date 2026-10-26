# Product and AI application engineering: research and upgrade contract

Date: 26 October 2026. Baseline: `5355fbbffecc03d35c1c059d754fc825bcfb606a`.
Scope: improve the shared library, retaining its [nested workspace](../installation.md)
and [action-scope contract](../../skills/orbyn-setup/references/action-scope.md).
No target installation, application changes, provider purchase, telemetry enablement
or publication follows from this work. Research lead owns this synthesis and
candidate verification; Orbyn Skills Builder 2 owns skill implementation.

## Decision and baseline gaps

The baseline has 34 maintained skills and 215 evaluation definitions. Planning
already covers problem framing, alternatives and outcome measures; UI owns task
flows, prototypes and recovery. Backend owns authorization, effect identity,
unknown outcomes and observability. CI owns proportional gates; the skill evaluator
owns recorded skill trials. These are useful foundations, not evidence of a complete
product-discovery or AI application method.

Product engineering needs a repeatable connection from observed user problems to
risk-resolving experiments and decisions after delivery. Strengthen existing
planning, research and UI owners. A new generic product skill would overlap those
owners and increase routing ambiguity.

AI application engineering has a distinct missing trigger: building or changing
model-powered application behavior. Add one focused `orbyn-ai-application` owner
that coordinates product fit, context, retrieval, tool effects, application evals
and operation. It must not replace backend, UI, testing, security or CI owners.
It is not a model-training curriculum, host installation guide or default route
for every task performed by an AI coding assistant.

## Primary evidence and implications

Sources below were inspected online on the research date. Explanations are
independent synthesis, not imported source text. Publication dates identify
versions where known; mutable vendor pages do not prove installed capability.

| Source | Finding used | Local implication and limitation |
| --- | --- | --- |
| [GOV.UK discovery research](https://www.gov.uk/service-manual/user-research/user-research-in-discovery) | Understand users, existing journeys and barriers before choosing a solution. | Record evidence and assumptions separately; include accessibility and non-digital steps. Government delivery requirements are not universal product policy. |
| [GOV.UK research planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service) | Choose methods from prioritized questions. | Resolve the riskiest assumption with the cheapest credible observation; do not mandate interviews for a known defect. |
| [GOV.UK service metrics](https://www.gov.uk/service-manual/measuring-success/how-to-set-performance-metrics-for-your-service) | Derive measures from intended benefits and interpret them with research. | Define an outcome, baseline, population, denominator and window. Do not import government-specific mandatory KPIs or publication duties. |
| [GOV.UK moderated usability](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) | Observe likely users completing believable, nonleading tasks. | Prototype task success can identify usability problems; it does not establish market demand, retention or production reliability. |
| [Microsoft ExP pre-experiment patterns, 2020](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage/) | Hypotheses, metric selection, randomization units and data quality affect conclusions. | Specify decisions and guardrails before measurement; account for team/network interference and adequate sensitivity. A/B testing is optional, not a universal stage. |
| [Microsoft sample-ratio mismatch, 2020](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/) | Missing or disproportionate assignments can invalidate experiment interpretation. | Diagnose assignment/exposure/logging defects before asserting lift. A before/after chart is not a randomized causal estimate. |
| [Google PAIR user needs](https://pair.withgoogle.com/chapter/user-needs/) | AI value depends on the user problem and whether automation or augmentation fits. | Compare deterministic/manual alternatives before selecting a model or agent; preserve human control where errors are consequential. |
| [Google PAIR mental models](https://pair.withgoogle.com/chapter/mental-models/) and [feedback/control](https://pair.withgoogle.com/chapter/feedback-controls/) | Expectations and control affect interaction; feedback has different meanings. | Explain capability and limits, correction and fallback. Feedback is not automatic training consent; engagement alone is not success. |
| [Amershi et al., CHI 2019](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/) | Human-AI guidance covers initial interaction, errors and change over time. | Test dismissal, correction, uncertainty and changed capabilities. The paper does not certify our UX or authorize collection of user behavior. |
| [Anthropic effective agents, 2024 with later page updates](https://www.anthropic.com/research/building-effective-agents) | Simple calls and defined workflows can be adequate; autonomy has costs. | Add agent loops only for demonstrated dynamic decisions. This is architectural inspiration, not a requirement to use an SDK or current hosted service. |
| [Anthropic tool design, 2025](https://www.anthropic.com/research/writing-tools-for-agents) | Clear tool contracts and useful bounded responses aid agent use. | Specify inputs, semantics, pagination, errors and effects; preserve server-side enforcement. No particular tool-call sequence is universally correct. |
| [Anthropic context engineering, 2025](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | Context selection and compaction involve information-loss trade-offs. | Budget context, preserve provenance and critical constraints, and evaluate long-session recovery. No automatic memory capture or subagents are implied. |
| [Anthropic agent evals, January 2026](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Evaluate actual outcomes, grader suitability, repeated trials and isolated environments. | Pin baseline/candidate bundles; retain failures and calibrate subjective judgments. Benchmark results do not establish production value. |
| [RAGAs, EACL 2024](https://aclanthology.org/2024.eacl-demo.16/) | Retrieval relevance, faithful use of evidence and answer quality are different evaluation dimensions. | Diagnose retrieval separately from generation; automatic judges remain fallible. No RAGAs dependency or advertised accuracy gain is adopted. |
| [Azure AI Search security filters](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search) | Result filtering depends on supplied principal data and application enforcement. | Enforce authenticated access before context exposure; test stale permissions and caches. A filter string is not authentication; the library does not require Azure. |
| [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) and [LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | External content can steer models; excessive tool authority increases consequences. | Treat retrieved content as untrusted and enforce permissions/effects outside the model. Prompts, citations, RAG or approval dialogs alone do not guarantee safety. This is design guidance, not a security scan. |
| [NIST AI 600-1, July 2024](https://doi.org/10.6028/NIST.AI.600-1) | Risk measurement, provenance, predeployment evidence and ongoing monitoring have contextual limits. | Record residual risk and requalification triggers. No compliance certification or mandatory governance platform is claimed. |

## Product contract

For a consequential new feature, the existing brief should connect:

1. Person/segment, task and current journey; observed evidence, source/date and
   limits; unresolved assumptions rather than invented interviews or personas.
2. Falsifiable outcome hypothesis, no-change/manual/smaller alternative, and the
   riskiest assumption. Prioritization considers impact, uncertainty, effort,
   dependencies and reversibility without invented precise scores.
3. Smallest suitable investigation: existing evidence review, interview plan,
   nonleading usability task, prototype or controlled experiment. Name consent,
   inclusion, access and collection limits. Research plans are not executed studies.
4. Primary outcome and guardrails with unit, eligible population, numerator/
   denominator, baseline, observation window and data-quality checks. Use existing
   authorized instrumentation; no unsolicited analytics installation.
5. Implementation acceptance separately from outcome learning. Decide proceed,
   revise, stop or gather more evidence; insufficient traffic or a biased sample
   cannot become a universal win. For randomized studies, predefine assignment,
   exposure, analysis and stopping, uncertainty and interference considerations.

For small known fixes, use the established contract and focused regression; do not
force discovery documents, a dashboard or an experiment platform.

## AI application contract

Use one short application contract in the existing design or task record:

- **Fit and baseline:** user outcome, unacceptable failures, deterministic/manual
  comparator; choose a single call, fixed workflow or bounded agent with reasons.
- **Inputs and context:** data classification, authority, source provenance,
  prompt/model/configuration versions, context budget, overflow/compaction policy,
  structured schema and semantic validation. Valid JSON is not correct or authorized.
- **Retrieval when needed:** ingestion/version/deletion ownership, selected corpus,
  query/access filtering, chunk/source lineage, bounded lexical baseline, optional
  semantic/hybrid/reranking comparisons. Permissions apply before model/reranker
  exposure and to caches/logs; revocation must prevent stale authorized results.
- **Generated outputs:** evidence-supported claims, conflicting/stale/no-source
  behavior, abstention and user correction. Similarity is not calibrated confidence;
  a citation must support the claim and remain accessible to the intended user.
- **Effects:** narrow tool contract and validated resource IDs; server-side auth,
  business rules, current intent/version approval where required, operation identity,
  duplicate/unknown-outcome reconciliation, cancellation and bounded iteration.
  Cancellation of generation cannot undo a committed external action.
- **Evaluation:** representative common, difficult, negative and adversarial tasks;
  development/held-out separation, dataset provenance, repeated matched trials,
  actual outcome state and calibrated graders. Report critical slices and failures
  separately, rather than hiding them inside aggregate quality.
- **Operation:** quality/latency/cost budgets including failed attempts and retries,
  privacy-aware diagnostic fields, retention/deletion, fallback preserving scope,
  exact version bundle, staged qualification and recovery. A cheaper provider or
  cache cannot silently change data residency, authorization or the user contract.

Application evals live with the consuming application. The shared skill evaluator
continues to evaluate skill selection and recorded behavior; it does not become a
universal AI runtime or production evaluation service. Model training, provider
installation and production deployment remain separate work.

## Ownership and integration

| Decision | Canonical owner | Handoff |
| --- | --- | --- |
| Product hypothesis, prioritization and outcome decision | `orbyn-plan` | Research evidence and smallest delivery slice |
| User evidence and method limits | `orbyn-research` | UI task validation or plan decision |
| Usability, capability expectations, correction and recovery | `orbyn-ui-design`, with content owner | Actual rendered/interactive acceptance |
| Model-powered application contract | `orbyn-ai-application` | Architecture, backend, UI, TDD and CI mechanics |
| Tool authorization, persistence and retry effects | `orbyn-backend-design` | Application-specific negative-path tests |
| Deterministic tests and probabilistic evaluation boundaries | `tdd` and AI application owner | Scoped CI and release policy |
| Workflow routing and shared discoverability | `orbyn-workflow`, catalog and generated hosts | Relevant owner only; no default whole-library loading |

Preserve existing licenses and source lineage. Update README/current audit,
catalog relationships, provenance and generated manifest consistently. No changes
to nesting, per-target installations, shared runtime providers or default model
settings are required. New source citations are attribution/update pointers;
essential procedures must remain usable offline from local references.

## Verification and completion criteria

Builder freezes one explicit candidate allowlist and content hashes. The research
lead reviews the actual final source, examples and cases independently. At minimum,
review these scenarios against the authored methods:

| Scenario | Required decision / failure boundary |
| --- | --- |
| Proposed onboarding feature with weak evidence | Investigate the failure; compare content/manual/no-build intervention; label assumptions |
| Easy prototype, no evidence of demand | Record usability finding; do not claim adoption, value or causal improvement |
| A/B lift with assignment/exposure defects | Withhold causal conclusion; diagnose data quality; retain null/negative evidence |
| Known label typo | Direct bounded task; no forced product-discovery or AI process |
| Deterministic rules meet the outcome | Reject unnecessary LLM/agent infrastructure |
| Relevant document absent vs present but ignored | Separate retrieval failure from answer-generation failure |
| Cross-tenant, revoked, cached or malicious document | Enforce access before exposure; content cannot grant tool authority |
| Valid structured output names unauthorized resource | Reject at the actual auth/semantic boundary |
| Tool timeout after possible commit or stale approval | Reconcile operation identity; no blind replay or stale approved action |
| Better average score, worse critical slice or cost | Preserve failure slices and budgets; qualify the decision instead of declaring a win |
| Provider unavailable or model version changed | Offline work stays unqualified; re-evaluate changed bundle; no silent installation/switch |
| Feedback, telemetry or external publication suggested | Require actual task/data authority; no automatic capture or learning |

Add original synthetic development cases covering positive routes, adjacent
nontriggers and missing/adversarial evidence; preserve all 215 baseline definitions
and historical trials. Run library/asset/link/manifest, generated-discovery,
evaluation validation and whitespace checks. Select helper regression tests from
actual catalog/tooling impact; no unrelated consumer-app sweep or paid model call
is necessary. Static checks validate authored contracts, not live-agent efficacy.

Completion means the integrated local candidate contains the methods, examples,
routing and cases, and independent review finds no unresolved material gap. It does
not require a commit, publication or a claim that user demand, model quality,
security or production reliability has been demonstrated. Those require their own
authorized observed evidence. Review receipt records exact final files and limits.
