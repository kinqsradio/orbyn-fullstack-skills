# Select the relevant trust boundaries

Map these checks to actual source paths and actors. They are hypothesis prompts,
not a checklist whose omissions automatically count as vulnerabilities. Inspect
controls along the full reachable path and report absent source facts as unknown.

| Boundary | Questions to resolve | Deeper checks |
| --- | --- | --- |
| Identity and resource authority | Does the effect use the current principal and resource membership? Can a client-supplied identity, stale approval or missing object check cross another user’s boundary? | [API](threat-model/architectures/api.md), [multi-tenant SaaS](threat-model/architectures/multi-tenant-saas.md), [microservices](threat-model/architectures/microservices.md) |
| Parsing, protocols and browser input | Do routing, decoding, framing, canonicalization, rendering and origin checks agree? Trace the same input through every relevant interpretation. | [web](threat-model/architectures/web.md) |
| Domain state and durable writes | Are version/state transitions atomic where needed? Can retries, races, cache keys or stale workers apply an unintended effect or mix tenant data? | [serverless](threat-model/architectures/serverless.md), [microservices](threat-model/architectures/microservices.md) |
| Files, native clients and local IPC | Are paths, links, exported handlers, deep links and helper calls constrained to the caller’s authority? Do not infer native behavior from browser code alone. | [desktop](threat-model/architectures/desktop.md), [mobile](threat-model/architectures/mobile.md), [CLI and developer tools](threat-model/architectures/cli-developer-tools.md) |
| AI and tool effects | Can lower-trust content alter tool authority, select another principal’s resources, expose secrets or turn model output into an unchecked effect? Distinguish untrusted data from instructions. | [agentic AI](threat-model/architectures/agentic-ai.md), [RAG](threat-model/architectures/rag.md) |
| Tool definitions and shared credentials | Who controls a tool’s name, description and schema, and can they change after approval? Does one credential serve several tools, so its grants are the union of all of them? Is the inbound caller’s authority checked apart from the credential the tool runs with? | [tool and shared credential boundaries](threat-model/tool-credential-boundaries.md), [agentic AI](threat-model/architectures/agentic-ai.md) |
| Jobs, queues and external providers | Who owns leases, retries, cancellation and terminal results? Can duplicate delivery or an unknown outcome bypass an invariant? Provider/deployment behavior needs actual evidence. | [serverless](threat-model/architectures/serverless.md), [microservices](threat-model/architectures/microservices.md) |
| Build, release and deployment | Which untrusted events can reach tokens, signing, dependency resolution, release artifacts or infrastructure changes? Inspect source policy and require missing live configuration as evidence. | [CI/CD and supply chain](threat-model/architectures/cicd-supply-chain.md) |
| Resource and data lifecycle | Are quotas, shared work, exports, retention, deletion, restore and cache/search isolation enforced at the real owner? Bound local availability checks and never stress a shared/live service. | [data platform](threat-model/architectures/data-platform.md), [multi-tenant SaaS](threat-model/architectures/multi-tenant-saas.md) |
| Native memory and binary boundaries | Where unsafe operations or parsers exist, trace size/lifetime/ownership and reachable attacker inputs. Missing local tooling limits execution claims; do not invent sanitizer results. | none bundled; record a gap |

Select checks by the target’s stack, exposed surfaces and requested scope. Record
why other classes are inapplicable, blocked or deferred. A finding needs a real
crossed boundary and consequence; recommend hardening separately when an existing
control already prevents the hypothesized effect.

## Use in a threat model

A [threat model](threat-model.md) starts from these rows. Name the row in the
`guide` field of each model boundary, spelled exactly as in the first column;
the checker refuses any other name. The architecture files in the last column add
checks the row does not ask, so skip a question the row already settled. A
boundary that fits no row is a gap: add the row here, with the change that needs
it, rather than inventing a name in one model.
