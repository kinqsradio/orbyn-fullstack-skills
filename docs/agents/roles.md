# Roles and artifacts

Roles describe responsibility, not separate permanent chats or model identities.

| Role | Owns | Returns |
| --- | --- | --- |
| Lead | Scope, decisions, integration and delivery | Reviewed result with actual evidence/limits |
| Investigator | A bounded source/runtime question | Anchors, mechanism and uncertainties |
| Architect | A consequential contract | Interfaces, lifecycle, failure and compatibility |
| Engineer | Assigned implementation and cleanup | Changed artifact/diff and authorized checks |
| Reviewer | Read-only challenge of a candidate | Concrete scenario, location and impact |
| Verifier | An assigned evidence boundary | Candidate, observation and exclusions |

Use the consuming project's configured tiers. The optional `orbyn-agent` reference
is for complex work; `orbyn-light` is for bounded lookup, documentation and focused
checks. The [model policy](model-policy.md) and actual host determine availability.
Children never create recursive agents or extra project sessions.
