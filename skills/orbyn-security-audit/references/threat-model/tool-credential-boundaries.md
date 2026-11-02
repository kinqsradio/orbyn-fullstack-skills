# Tool and shared credential boundaries

Apply when evidence includes MCP servers, agent tools, connectors, or several operations sharing one service identity. This adds checks inside the stage you are running; it is not a separate method. Inventory while gathering evidence, map while modelling, derive scenarios while analysing, seek counterevidence while challenging, and compare authority changes while reviewing a change. Read definitions and configuration from files; never connect to a server to collect missing metadata, and never read or copy a secret value.

## Tool definitions are an input surface

Tool names, titles, descriptions, schema property descriptions and annotations reach the model before any result does. Tool description poisoning is indirect injection through that metadata. Inspect:

- Who controls the metadata (server, registry, package, update channel), what the model sees, what the reviewer sees, and the definition's revision. Identify a tool by server plus name.
- Discovery, caches, refresh, reconnection and changes after approval. Do not assume change notifications invalidate approval.

Trace attacker-controlled metadata to model context, to the selected tool and arguments, to the approval, to the execution identity and downstream authorization, to the effect or disclosure. Follow both another trusted tool being redirected and data leaving through the poisoned tool's own arguments. A suspicious description, an authenticated server or a changed answer does not show an unauthorized effect.

Pinning gates changes but does not make a malicious first definition safe. A signature shows provenance, not intent. Scanning, labels, model resistance and confirmation prompts do not by themselves prevent anything; read what the prompt displays. Credential separation limits authority but not steering of another authorized tool.

## Effective authority per tool

Build a per-tool map in the model, with `path:start-end` evidence:

- Server, executor, handler, intended read, write or admin operations, and resource or tenant scope.
- Inbound caller identity and authorization, apart from the downstream execution principal and credential reference. An inbound token and a backend key are different boundaries even if they share a value. If an inbound token is forwarded downstream, check issuer and audience acceptance.
- The credential source by safe symbolic name, the tools sharing it, its configured grants, and evidence of effective restrictions. Matching variable names in separate deployments do not prove one credential.
- Which runtime can obtain each credential: environment inheritance, shared stores, brokers, fallback identities. Lifetime, rotation, revocation and audit attribution where known.

A tool named "read" or annotated read-only is a claim until the implementation enforces it. Do not infer live grants from a sample configuration.

## Analyse

Compare each tool's required authority with the credential's effective grants: one server credential can accumulate the union of many tools' permissions. A shared token alone shows exposure, not an exploitable write path. State the attacker capability in each threat: content control, code execution in the tool runtime, or credential possession. Treat runtime compromise as a stated prerequisite. Consider confused-deputy use without token theft, direct backend use, cross-tenant resource selection, loss of attribution, and the shared failure domain of rotation and revocation. Prompt injection is not required as the entry point.

Counterevidence is scoped: caller and resource authorization enforced outside the runtime, fixed operation allowlists, inaccessible credentials. A denial on one handler does not cover another handler or direct use. Checks inside a compromised runtime do not constrain that runtime's owner; for that attacker, look for downstream grant limits, independent identity checks, a protected broker or credential isolation.

## Propose and verify

Compare per-tool identities, separate read and write identities, per-task downscoped grants, and a broker that authorizes each operation. Different key strings with the same grants reduce nothing. Separate processes are not isolation if both can reach the write credential. State the trade-offs: deployment overhead, credential sprawl, rotation, audit correlation, availability.

Plan, as `not_run`, comparisons in an authorized isolated environment: benign, poisoned and post-approval-changed definitions; an allowed read against a write or out-of-scope attempt under the read identity; rotation and revocation across all consumers including cached credentials. Pass: allowed work succeeds, forbidden operations are denied, and old authority stops within policy. Missing decision or outcome evidence is inconclusive.
