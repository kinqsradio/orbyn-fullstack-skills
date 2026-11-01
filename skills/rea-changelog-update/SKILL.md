---
name: rea-changelog-update
description: "Prepare REA release notes from pinned upstream history when requested; does not publish or infer REA history from Orbyn Git."
---

# Prepare REA release notes from real history

This local method prepares user-facing notes and attribution. It does not tag,
merge, publish, fetch history or rewrite released notes without scope.

Read the actual REA checkout's release policy when operating on that project.
Without a checkout, use supplied verified history and keep its limits explicit. The
[upstream review skill](../orbyn-upstream-review/SKILL.md) owns source freshness.

## Fix the editorial range

Identify the published baseline tag/commit, exact editorial target SHA, proposed
version and release component from the actual REA repository or supplied metadata.

- When Release Please owns the release, inspect the base branch's manifest and
  configuration; do not infer the baseline from an unrelated consumer's version.
- REA tags use `rea-agents-VERSION`; verify the actual tag rather than inventing one.
- A vendored source snapshot has no independent Git history. Never use the consuming
  project's Git log as REA release history.
- Keep a shared-skill/local-tool recipe update separate from an engine release: it
  does not advance an REA runtime pin or establish a new provider capability.

If the baseline or target cannot be established, prepare only a labelled partial
draft and name the missing inputs.

## Inventory the range

List the full range, including merged side branches, direct commits, reverts,
backports and known PR/issue associations. Preserve exact source links and identity
limits. Network access is not mandatory: use local history for a bounded inventory
and leave unknown GitHub handles/associations unknown. Do not execute an online
collector just to satisfy a template.

## Write user outcomes

Inspect ambiguous diffs before describing behavior. Group capabilities and fixes
by analyst outcome. Include breaking changes with old/new behavior and a concrete
migration. Keep internal tests/cleanup in the contribution inventory, even when they
do not lead the public highlights. Check reverts before claiming something still
ships. Do not infer live-provider verification from fixture tests.

Keep notes concise and the reviewed inventory available under the project's
release-artifact policy; do not publish private metadata or raw session logs by
default.

## Preserve attribution

Verify human author/coauthor/issue-reporter identities using actual metadata.
Unknown handles stay unknown; do not credit the merger as a substitute or guess
accounts from email. Preserve source attribution and the project's credit rules;
do not copy another maintainer's self-thanks or bot policy as a universal rule.
Link grouped contributions without losing their known credits.

## Reconcile automation without publishing

For an authorized local edit, update only the intended version section and preserve
older history. Keep version artifacts and bot-owned metadata consistent.

Inspect the actual bot workflow before editing a live release branch/body: a running
proposal can overwrite prose, and a finalization label is not permission to publish.
Do not apply an upstream label or run release scripts blindly from this skill.

## Check and return

Use existing locally available validators/renderers when checks are in scope. Check
that the inventory target still matches the release's product boundary, notes cover
breaking changes and credits are supported. Refresh the inventory after new product
commits, and review the diff for metadata-only changes too. A local CHANGELOG edit
does not establish that a remote release body changed.

Return the range, draft notes, contribution evidence, unresolved identities,
compatibility migrations and actual delivery state. Release publication and source
pin changes remain separate decisions. See the [worked example](references/worked-example.md)
and [source record](../reverse-engineer-anything/references/source-record.md).
