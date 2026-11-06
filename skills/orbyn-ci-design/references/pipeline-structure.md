# Pipeline structure for many services and environments

Use when one repository builds or deploys several services, or deploys to more than
one environment. Platform-neutral; GitHub Actions is the worked case.

## One manifest owns the routing

Keep one checked-in manifest that says, for each service: the paths that belong to it,
the checks it needs, and per environment its deploy target and whether a person must
approve. Rules shared by every service (build, unit tests, security scan) are written
once; per-service and per-environment rules live in the manifest, not in branches of a
script. Two entries never claim the same path for the same environment.

```json
{
  "schema_version": 1,
  "shared_paths": ["packages/shared/**"],
  "ignored_paths": ["docs/**", "*.md"],
  "services": {
    "api": {"paths": ["services/api/**"], "checks": ["unit", "contract"],
            "deploy": {"staging": {"target": "api-staging"},
                       "production": {"target": "api-prod", "approval": "required"}}},
    "web": {"paths": ["apps/web/**"], "checks": ["unit", "e2e"],
            "deploy": {"staging": {"target": "web-staging"},
                       "production": {"target": "web-prod", "approval": "required"}}}
  }
}
```

## A selector decides, the platform runs

1. A selector reads the manifest and the complete change set and prints the matrix:
   `ci_scope.py services --manifest services.json --base <sha> --head <sha> --event pull_request --environment production`
   ([`ci_scope.py`](../scripts/ci_scope.py)) prints `{"include": [...]}` with each
   affected service, its checks, its target and approval for that environment, and the
   reason it was picked; `--github-output` writes it for the next job. A shared path, a
   path no service owns, or incomplete evidence selects every service, as
   [change scope](change-scope.md#encode-a-conservative-fast-path) requires. Where the
   build system has its own [affected targets](affected-targets.md) query, use that.
2. The workflow fans out one job per matrix entry. Each job gets its own status, runs
   in parallel, retries alone and keeps its own record of what went where.
3. Each job calls small step scripts (build, migrate, deploy, smoke test) that also run
   on a laptop with the same arguments, so a failure can be reproduced without CI.

Do not run every deploy from one long orchestrator script: a failure halfway leaves a
partial deploy with no per-service record, nothing runs in parallel, and the
platform's approvals and environment secrets cannot apply to each step.

Share pipeline rules as reusable workflows or shared actions with inputs (service,
environment), one owner each, instead of copying job definitions.

## Environments are enforced by the platform

Give each environment its own secrets and protection rules in the CI platform:
production requires an approval and accepts deploys only from the protected branch.
A selector or script never grants that approval, and a pull request's code never runs
with deploy secrets. Promotion stays the deliberate decision in
[keep CD separate](change-scope.md#keep-cd-separate).

## Make it fast

Measure the slowest step first, then:

- run only what the change affects, and the full suite on the main branch and nightly
- split the slowest test module into parallel units and start the slowest first; the
  run is never shorter than its longest unit
- size worker counts to the work: subprocess-heavy tests wait on I/O and can use more
  workers than cores
- cache dependencies by lockfile hash, and build once and reuse the artifact downstream
- cancel superseded runs on the same branch, and stop a job early only when nothing
  after it is useful
