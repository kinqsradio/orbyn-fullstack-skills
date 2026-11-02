# Choose the architecture

Pick one primary architecture for the decision the model supports, and a secondary only where it adds a distinct boundary. Write the choice in the run folder as `selection.md` before analysing. Selecting a file is not running it, and the choice proves nothing about the system.

## Choose

1. Start from the rows of the [boundary guide](../threat-boundaries.md) that apply, then list from the evidence: objective, actors, assets, data owners, entry points, workflows, trust crossings and lifecycle changes. Keep unknowns as unknowns; do not complete a familiar architecture from memory.
2. Choose the primary by the boundary and lifecycle that dominate the decision, not by component count or fashion. A web portal is not automatically microservices. Where evidence cannot separate two candidates, say so, name the evidence that would, and do not declare two primaries.
3. Add a secondary only for a distinct subsystem boundary with its own evidence, and say what it adds and excludes. Drop one that repeats the primary. Example: web primary for the browser and session, multi-tenant SaaS secondary for the one tenant-scoped export flow.
4. Name excluded families and why they add no distinct boundary.
5. State the cheapest next evidence that would improve the choice.

Bundled architecture checks: [web](architectures/web.md), [API](architectures/api.md), [multi-tenant SaaS](architectures/multi-tenant-saas.md), [agentic AI](architectures/agentic-ai.md), [RAG](architectures/rag.md), [CI/CD and supply chain](architectures/cicd-supply-chain.md), [CLI and developer tools](architectures/cli-developer-tools.md), [desktop](architectures/desktop.md), [mobile](architectures/mobile.md), [serverless](architectures/serverless.md), [microservices](architectures/microservices.md), [data platform](architectures/data-platform.md). For anything else (event streaming, firmware, payments, identity federation) use the neutral baseline in the [method reference](../threat-model.md#baseline-questions), say no architecture file exists, and record the missing boundary checks as a gap.

For MCP servers and tool connectors, route by the decision. Planning and delegation authority points to agentic AI; the receiving service's authorization points to API or another service architecture. Either way, add [tool and shared credential boundaries](tool-credential-boundaries.md).

## Composition

For a mixed system:

- Give every boundary one guide row and exactly one owning architecture. Other architectures contribute to a threat or control without co-owning the boundary. An unknown owner stays unknown with a gap.
- Use one id per actor, asset, boundary and control across architectures. Equal labels or reused local numbers such as `T-001` are not identity evidence; look for the same actor, prerequisite and boundary before merging two threats.
- Two views of one scenario are one observation, not two. Overlapping reports are not independent evidence.
- Merge a shared control only when its mechanism and scope match, and keep which paths each observation covers.
