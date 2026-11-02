# API checks

Use for a service interface with callers, an identity, owned resources, a gateway or backend, and outbound callbacks. Add federation checks only for evidenced issuer, subject, client and audience relationships. Do not infer OAuth, a token format, a gateway product or a delivery guarantee from the word "API".

## Trace

1. The caller's identity and intended audience through admission at the gateway and authorization in the backend. Recognising a caller grants no permission on every object. Equal subject strings from different issuers are not one principal.
2. A changed object id through single reads, updates, bulk selection, asynchronous export execution and result download. A passing GET check proves nothing about export. Ask what authority is rechecked when work is delayed, ownership changes or access is revoked.
3. Object, function and property authority as three questions. An allowed read does not authorize a privileged operation or every returned property. Take permitted fields from supplied policy, not guessed business rules.
4. Replay, duplicates, concurrent requests and order against a named business invariant: the allowed competing transitions, the commitment point and the allowed number of effects. A unique request id establishes neither safe sequencing nor exactly-once processing.
5. A caller-controlled callback from registration through storage, the outbound worker, destination checks and redirects. A configurable URL is not proof of server-side request forgery.
6. The callback payload to its recipient, and response fields back into state. An acknowledgement may record receipt; it must not change business state.
7. Bulk export and callback work: cancellation, delay, retained results, retries, slow destinations, oversized responses. Take limits from supplied objectives; invent none.

## Scenario families

- A caller selecting another owner's object, including through bulk export.
- Replay, duplicates or concurrent sequencing that violates a privileged-operation invariant.
- A caller-influenced callback destination, or a response crossing outbound, data or state authority.

For each, name the scoped protection and a counterexample that would defeat the hypothesis.

## Checks to propose (all `not_run`)

- Write an expected-outcome matrix first: each test actor and seeded object, with each action and property marked allowed, denied or unknown. An unknown cell makes that path inconclusive, never a pass. Compare an allowed read with a changed id, a mixed-owner export, delayed execution after revocation and retrieval by the other principal.
- Use inert receivers the tester owns, with synthetic payloads, for permitted and forbidden destinations and redirects. Check what is sent and whether crafted acknowledgement fields change only notification state. Never contact internal, third-party or production destinations.
- Against an isolated sink, replay and race competing transitions at the commitment point. Judge by the stated invariant, not an assumed delivery guarantee.
