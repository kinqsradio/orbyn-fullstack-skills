# Web application checks

Use for a browser, an application origin, a session and a server that renders or serves user and external content. Add [multi-tenant SaaS](multi-tenant-saas.md) only where a tenant boundary is evidenced. A framework name or the word "web" proves no protection and no weakness.

## Trace

1. State-changing requests, from the initiating browser context through the origin and session to the server operation. A recognised session is not authorization for the intended action; establish the credential and request conditions before proposing a cross-site request scenario.
2. Identity, tenant, target object and operation at the server. Compare the normal view with export, background and admin routes. A passing read check says nothing about update or export.
3. User-controlled text, names, links and uploads into another user's view, above all a more privileged viewer's. Name the interpreter, the viewer's authority and any protective handling. Do not assume submitted text executes.
4. Private responses through shared caches and browser storage to their recipient. Name the reuse conditions, and ask whether attacker-influenced content can be stored in a shared cache.
5. Upload, preview and download as three paths: who submits, who interprets, who retrieves, who retains. A safe text renderer says nothing about preview.
6. Third-party code that runs with page access, apart from ordinary resource requests. Who can change it after review, and what can it read or send? A hostname alone is not disclosure.
7. Sign-out, expiry, account or tenant switch, privilege change and recovery. Invalidating a credential differs from clearing content already displayed or cached.
8. Authority carried across asynchronous work, retries and degraded paths.

## Scenario families

- Unintended state change through browser and session authority.
- User-controlled content interpreted in another user's view.
- Private response exposure through cache reuse or external resources.

Record a protected or unevidenced family as `protected` or `gap`. Do not force three threats.

## Checks to propose (all `not_run`)

- With synthetic users A and B and known object ownership: the allowed operation, a cross-owner attempt and an unintended-request attempt. Pass: allowed works and the unauthorized change is denied. Fail: an unauthorized change. Inconclusive: no state or authority observation.
- Warm a private response for its owner, then request it as the owner, as another authenticated user not entitled to it, and signed out. Pass: no private content reaches the unentitled. Fail: it does. Inconclusive: recipient, entitlement or cache path unobserved.

State the route tested in the plan so a result is not read as covering untested routes.
