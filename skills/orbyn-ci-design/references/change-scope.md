# Proportional verification and deployment

Choose checks by changed behavior, trust boundary and affected consumers, not by
line count. A one-line authorization or schema change can require wider evidence
than a large prose edit. The agent makes this assessment from the actual diff;
the human need not invoke a separate skill or waive routine checks repeatedly.

| Change | Local evidence | Published CI / delivery |
| --- | --- | --- |
| Typo, inert comment or presentation-only prose, with no command/contract change | Inspect the diff; use relevant formatting/links if affected | No application build/test or deployment. Local-only work can end without a hosted run. Preserve any required merge status for a published change. |
| Skill instructions, routing, ownership or project policy | Catalog, links, source/license integrity, expected and adjacent task cases | Focused skill/source/sync checks; no live model/provider or whole-app suite solely for prose. |
| Executable helper | Relevant failure/recovery fixtures plus the checks it owns | Run the helper's meaningful tests; avoid unrelated product builds. |
| Runtime code, API/schema/data, dependencies, build inputs or CI policy | Trace callers/effects and choose affected contract checks | Run affected application checks. Shared or uncertain effects select broader checks. |
| Deployment or production change | Verify the actual candidate, target, recovery and authority | Separate explicit promotion policy; green CI alone grants no deployment authority. |

These are decisions about evidence, not labels that prove a change harmless.
Markdown used as a runtime template, executable documentation, generated inputs
or a comment whose tool consumes it is not automatically cosmetic. Inspect actual
callers and project conventions. Retain failed results; do not add a path filter
just to conceal an observed failure or call skipped tests passing.

## Designate gates for the feature worktree

Creating a branch/worktree or implementing a feature does not itself require a
new hosted workflow, CI service, pipeline framework or automatic deployment. Use
existing commands and local checks when sufficient. Change CI infrastructure only
when the task requires it and that change is within scope; do not add automation
for every task. Reuse existing affected-target selection before building another
classifier or mandatory manifest.

Before expensive checks or delegation, designate the worktree's gates in the
existing task brief, PR or verification guide. For a small task, a few lines are
enough; no new tracker or configuration file is mandatory. Record:

- Exact checkout/base/candidate and affected contracts, packages and consumers.
- Named commands/jobs for the current stage, prerequisites and the reason each
  check is selected. A gate must test a meaningful outcome, not merely exit green.
- Explicit exclusions and coverage limits, plus conditions that broaden the set.
- Actual results for the tested revision; required, selected, intentionally
  unselected, blocked and not-run are distinct states.

| Stage | Designated checks |
| --- | --- |
| Feature worktree / iteration | Focused regression or contract tests, relevant package lint/type/build and affected consumer checks. Do not default to a whole-repository suite on every edit. |
| PR / integration | Refresh the selection from the complete current diff and dependency evidence, and satisfy the repository's required statuses. Include cross-package/integration coverage where boundaries change. |
| Release / promotion | Apply the existing release policy to the actual artifact/environment only when release is in scope. Broader release qualification need not run on every feature iteration; green feature CI grants no deployment authority. |

The plan is revisable evidence selection, not a permanent exemption. Reassess when
the diff, shared schema/API, generator, dependency/lockfile, build configuration or
consumer graph changes, or when failures expose wider effects. Start with the
smallest discriminating check; use the established broader/full fallback when
impact cannot be bounded reliably or current project policy requires it. Worktree
isolation and a feature label are not evidence of isolated runtime impact.

Respect required repository checks until an authorized policy change is reviewed
and applied; do not bypass protection, rename a status or mark an unexecuted suite
passing. A scoped required aggregate can be a good design when the repository
supports it, but its selector and selected jobs must fail closed. Never reduce
the selection merely to hide a failure. Narrow selection does not authorize
ignoring changed consumers, security boundaries or previously observed failures.

After checks pass, repeat only for changed inputs, new failures, evidence expiry
or project requirements. Do not rerun an identical full suite once per delegate
or worktree just because a new session starts. Reuse evidence only when candidate,
relevant inputs, environment and policy still match; a sibling worktree's green
summary or stale baseline is not current evidence.

Example: a task-editor client fix with an unchanged API may designate its failing
interaction regression and affected client type/lint checks, excluding unrelated
backend suites. If the patch changes a shared save schema or concurrent-write
contract, add generator, API and affected client integration checks; widen further
if dynamic consumers cannot be enumerated. A local README typo needs only relevant
document checks. These examples select evidence, not universal commands or waivers.

## Encode a conservative fast path

Use the project's existing [affected-target graph](affected-targets.md) when it
provides trustworthy scope. When no such graph exists, prefer a small known
docs/skills allowlist with full checks for anything unmapped before building a new
selection system. The consuming project owns the map. Root dependencies, shared
code, CI definitions and the classifier
itself need broad checks. Check every changed path, including deleted paths and
both sides of renames. Use complete Git changes at exact revisions; incomplete
pagination, an unavailable base or an unknown path must not silently select the
lightweight lane. PR comparisons use their merge base; a push compares the exact
before/after revisions across the entire push.

Keep an always-triggered required result. Do not skip a required workflow with
top-level path filters or a skip-CI commit marker: GitHub can leave its status
pending. Conditional application jobs can intentionally skip, while the final
gate still runs and rejects classifier errors, missing decisions, cancellation,
failures or an unexpectedly skipped selected job. Check the configured required
status names before changing them; YAML alone does not apply branch protection.
Support an explicit full-run option for diagnosis. A green small lane is evidence
for that lane, not proof that every application test ran.

The portable [scope helper](../scripts/ci_scope.py) accepts a project-owned JSON
policy with `schema_version: 1`, string lists `docs_files`, `docs_prefixes`,
`skills_files`, `skills_prefixes`, `deployment_files`, `deployment_prefixes` and
`application_jobs`. File entries are exact relative paths; prefixes end in `/`.
No shell, globs or commands are evaluated. Documentation prefixes admit only
Markdown/reStructuredText/text files; skill ownership takes precedence. Unknown
paths run the application lane, and unavailable change evidence also disables
automatic deployment. The helper's own scripts and `.github/` always take the
broad lane. The final gate requires the complete configured application-job list.

Test docs-only, skills-only, helper, runtime/shared dependency, rename/deletion,
mixed, unknown and missing-base cases, plus classifier failure and every selected
job's failed/cancelled/skipped result. Run the real proposed workflow as well;
fixture decisions do not establish hosted execution or branch protection.

A path classifier cannot prove that an edit inside runtime code is only an inert
comment. Keep that file on its conservative lane until a separately reviewed
semantic mechanism exists; do not trust a PR label or the author's line count as
a substitute. The local policy can still avoid unnecessary experiments for a
reviewed cosmetic edit without pretending hosted checks were executed.

## Keep CD separate

A documentation/skill-only success must not automatically redeploy the product.
For automated deployment, require the existing authorized promotion setting,
successful checks, trusted canonical push event and a runtime-change decision
bound to the exact candidate. Unknown changes may justify broader CI while still
requiring a deliberate deployment decision. An explicit manual deployment remains
a separate authorized operation.

If a follow-up workflow consumes a scope artifact, restrict its originating
repository/event/head and validate its schema and exact revision. Treat it only
as data; never execute downloaded artifact code or PR code with deployment
secrets. Missing/mismatched evidence blocks automatic promotion. Do not infer the
whole push from only its last commit. Preserve current secret/environment and
production authorization controls.

Official behavior checked 24 October 2026:
[required and skipped checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[job dependencies and always-running gates](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs),
[workflow-run security boundary](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).
