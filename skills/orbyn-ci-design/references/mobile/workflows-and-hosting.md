# EAS workflow and hosting contracts

Inspect installed CLI, project configuration and exact supported schema before
writing YAML. Keep selected schema bytes/version/hash task-local; if fetching is
necessary use a bounded timeout/size and ignored destination. Do not execute or
import a schema-fetcher that silently writes under active skills. Installed export
parsing is not proof a cloud runtime supports a component.

A minimal *shape*, to validate against the installed EAS schema before use:

```yaml
name: Preview artifact
on:
  workflow_dispatch: {}
jobs:
  build_ios:
    type: build
    params:
      platform: ios
      profile: preview
```

The preview build profile must exist in the consuming project. This is a minimal
manual-trigger shape checked against official syntax documentation on28October2026,
not authenticated EAS validation or a cloud run. Use the selected schema's
supported artifact/output interpolation and job conditions, never guess them.
Carry build/source/artifact IDs from producer to dependent jobs. Define branches,
events, environments and failure/cancel behavior; a downstream submit/deploy must
use the checked artifact. Untrusted fork PR code cannot receive trusted secrets
or promote a cache/baseline simply because a prior job succeeded. Scope credentials,
permissions, concurrency and idempotency to actual effects. Local schema validation
does not start cloud jobs or prove remote service readiness.

## Router hosting

Server API routes need a compatible server export/adapter; a static client export
cannot run server code. Resolve production vs preview deployments, deployment ID,
URL/custom domain/alias and environment explicitly. Build/publish/alias mutation
are separate effects; verify a preview before an authorized alias promotion.
Read [API routes](../../../orbyn-backend-design/references/expo-api-routes.md) for
request authority and client/server secret boundaries. An `EXPO_PUBLIC_` variable
is public bundle data; keep server secrets on the actual server runtime.

After an authorized deployment, read back actual deployment and alias identity,
then issue scoped health/denied-request checks against that URL. A local response
or successful upload cannot establish production alias correctness. Reconcile an
unknown deploy outcome by listing/reading actual IDs before retrying. Keep previous
artifact/alias and rollback owner; no automatic production rollback is authorized.

## Validate each changed workflow

Keep workflows in `.eas/workflows/*.yml` or `.yaml`; inspect the selected schema's
required trigger (`on`), supported job types, parameter/condition limits and file
size before authoring. Confirm every `needs`/`after` target exists, output expression
matches the producer's real schema, and every build/submit profile exists in the
project's eas.json. For the installed EAS CLI, inspect `eas workflow:validate --help`
and validate each changed file from that linked project, for example:

```sh
eas workflow:validate .eas/workflows/preview.yml --non-interactive
```

This may require authenticated project/server access. Report missing auth/link or
server validation as blocked; local YAML/JSON Schema success cannot replace the
CLI's profile and server checks. Do not fetch an unpinned latest CLI, link accounts,
change profiles or start workflow jobs to obtain a green result. When offline,
use previously pinned schema bytes and explicitly retain the service gate.
The manual trigger avoids an automatic push/PR service action in the example.
Select actual project profiles and validate the complete file before an authorized
run. Official [workflow syntax](https://docs.expo.dev/eas/workflows/syntax/) is the
update pointer. The public schema fetch returned403during authoring, so current
server-schema and authenticated CLI validation remain unqualified.
