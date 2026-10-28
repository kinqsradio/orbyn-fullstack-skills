# Expo Router API authority

Use only when the target has supported Router API/server runtime. A route such as
`app/api/items+api.ts` exports the installed method-handler contract (`GET`, `POST`)
and must run on a compatible server adapter. Static web/native bundles cannot
carry a server secret or establish server execution. Inspect installed types and
actual hosting mode before choosing Request/Response and environment APIs.

A server request must authenticate the caller, validate method/body/query, resolve
account/tenant/resource authority and enforce the write's version/idempotency.
Client route params, UI login state or a typed response cannot replace those
checks. Return meaningful 401/403/404/conflict/retry errors without leaking internal
exceptions. Mark personalized caching/private responses deliberately; no shared
public cache by default. Native and web clients use the actual environment/base
URL, appropriate cookie/token/CSRF/CORS contract and bounded cancellation.

For an authorized write: validate input, resolve session/scope, execute the owning
transaction/effect with stable operation identity, then return a checked result.
Unknown downstream outcomes are reconciled before retry; request disconnect cannot
undo a committed server effect. Keep runtime secrets server-only; EXPO_PUBLIC data
is visible. Check legitimate, denied cross-tenant, malformed, duplicate/stale and
wrong-preview-alias cases. Local handler tests prove handler behavior, not deployed
network/auth or production routing. [Hosting](../../orbyn-ci-design/references/mobile/workflows-and-hosting.md)
owns deployment identity and effect boundaries.
