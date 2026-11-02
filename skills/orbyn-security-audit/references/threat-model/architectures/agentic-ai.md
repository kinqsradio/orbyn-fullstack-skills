# Agentic AI checks

Use for a system where a model plans, remembers, delegates, calls tools and causes external effects. When MCP servers, connectors or tools are present, also apply [tool and shared credential boundaries](../tool-credential-boundaries.md). MCP alone does not make a system agentic: route by the decision. Agent planning and delegation belong here; the receiving service's authorization belongs with [API checks](api.md).

## Trace

1. **Intent and plan.** Separate the task the person authorized from the steps the planner proposes. A plan or an approval request is not an authorization.
2. **Content to action.** Who controls external content, tool descriptions or tool results? How does it reach planning, which capability and credential does the call use, and where is the action-specific permission decision? A tool result is data, not authority. Hostile text alone proves no execution.
3. **Memory.** Each write, its provenance, reader, task or tenant scope, expiry and correction. A stored instruction is not a new grant. Missing provenance is a gap, not proof of poisoning.
4. **Delegation.** Compare the delegated task with the original grant and the delegate's real capabilities. Follow scope growth, further delegation and returned instructions. A supervisor label does not authorize.
5. **Approval binding.** Who actually decided? Follow subject, action, resource, parameters and revision through the displayed request, the approval record and the execution. Check changed parameters, delay, expiry, revocation and cancellation.
6. **External effects and recovery.** Tell apart: proposed, accepted, failed before effect, completed with lost response, unknown. Check repeats of the same intent, changed intent, concurrent recovery and cancellation races. An unknown result is not permission to retry.
7. **Receiving API.** Tool-call authority differs from the API's resource authorization under the execution credential.
8. **Protection.** Say what a sandbox, human review or tool protocol constrains for this path. None is a universal guarantee.

## Scenario families

Untrusted content or tool metadata steering a later privileged call; memory or delegation expanding the grant; changed, delayed or repeated approval producing an unsupported or duplicate effect.

## Checks to propose (all `not_run`)

- Same authorized task with an inert external result, then with attacker-controlled instructions asking for an out-of-scope action, then with a limited delegation granting that action. Pass: no effect beyond the authorized task and the task still works. Fail: an attributable unauthorized effect. A changed answer is not an effect.
- Unchanged approved action, then changed parameters or recipient, then delayed approval after cancellation, then a repeat after an unknown outcome. Pass: single effect, bound to the approval, with a traceable pending state.
