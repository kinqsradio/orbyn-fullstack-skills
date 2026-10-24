# Public upstream and consuming projects

`kinqsradio/orbyn-fullstack-skills` is the upstream home for shared skills. A
private product can consume an exact file copy with a revision/hash lock while
keeping its own root policy, project guides, application source and credentials.
This avoids two independent “latest” copies and does not require external
contributors to access the private product.

## Pin an existing matching consumer

Clone the public repository at the desired reviewed commit. In a consumer whose
managed skills exactly match that revision:

```sh
python3 /path/to/orbyn-fullstack-skills/scripts/sync-public-skills.py pin \
  --root /path/to/consumer --upstream /path/to/orbyn-fullstack-skills
python3 /path/to/orbyn-fullstack-skills/scripts/sync-public-skills.py check --root /path/to/consumer
```

The lock records a full public commit and every managed file hash. The `check`
command uses no network and fails on a local edit, addition or removal. It does
not establish that the consumer tracks the newest upstream commit; updates are
an explicit choice. A consumer can copy the sync script into its own tooling
and use that trusted version for CI.

In CI, check out the lock's full revision from the canonical public repository,
then pass `check --upstream /path/to/that-checkout`. This also verifies that the
lock's hashes match the actual public manifest and commit, rather than trusting
locally edited lock metadata. The check reads the upstream files as data and does
not execute its helpers. Offline `check` alone is a local drift check.

## Work in the consumer, contribute upstream

1. Make the skill change in the consumer. Keep private policy/feature details
   outside shared skill files; use synthetic public examples.
2. Update a clean public clone and create a contribution branch there. The clone
   may be your fork; PRs target this repository's `main`.
3. Preview, then explicitly apply the export:

```sh
python3 scripts/sync-public-skills.py export --root /path/to/consumer --upstream /path/to/public-clone
python3 scripts/sync-public-skills.py export --root /path/to/consumer --upstream /path/to/public-clone --write
```

The tool compares the consumer's old pin, local files and upstream files. It
refuses conflicting edits and requires an upstream contribution branch for writes.
Only cataloged skill content plus the generated skill index/catalog can cross
the boundary. It never runs Git commit/push, opens a PR, copies history or exports
consumer root files. Review the actual content: an allowlist cannot determine
whether a sentence contains private information.

4. Regenerate the index/host links and manifest, run the contribution checks,
   commit, push your branch and open the public PR using the template.
5. After merge, check out the merged upstream revision. If the consumer already
   matches it, `pin` records that revision. Otherwise reconcile local edits first
   and use `pull` from the clean upstream checkout:

```sh
python3 scripts/sync-public-skills.py pull --root /path/to/consumer --upstream /path/to/public-clone
```

`pull` refuses outstanding local edits unless the consumer already exactly matches
the requested upstream content. It preflights managed paths, copies explicit
changes and updates the lock. Regenerate the consumer's host links afterward;
review removal of stale generated links if a skill was retired. Ordinary filesystem
failures can interrupt a multi-file copy, so retain the checkout/diff for recovery.

## What CI should do

- Public PRs: validate the catalog, frontmatter, links, attribution, manifest and
  focused helper/sync behavior with a read-only token and no secrets.
- Private consumer PRs/pushes: run `check` against the committed lock and canonical
  public checkout at that revision. A changed
  skill must be contributed/reconciled with a public pin before the check passes.
- A maintainer can prepare an update PR from a reviewed public revision. No
  automatic cross-repository write credential is required for drift detection.

CI does not silently publish a private diff or auto-merge a public contribution.
Branch protection must require the check to enforce it against direct pushes;
the files alone cannot guarantee maintainers will not bypass their own policy.
Human-reviewed CI is not live agent behavior qualification.

## Company-owned skill boundary

`project-skills/<company-or-repo>/<namespaced-skill>/` belongs to the consumer,
including its local references, licenses and company procedures. It is outside
inventory, import/export, public manifest and lock hashes. An edit there must not
require a public contribution. The [ownership guide](../skills/orbyn-setup/references/project-skills.md)
explains classification and migration. Host discovery supports both shared and
local skills without adding local names to `skills/catalog.json`.

When updating an older vendored integration, adopt the matching discovery helper
and asset-check support as well as the new shared references. Keep the consumer's
source/host/model integrity rules; teach them to validate the local namespace
separately, rather than accepting arbitrary discovery entries. A library clone
must not carry a consumer's actual `project-skills/` directory. This boundary
prevents automatic export; public authors still review content and Git history.

## One shared candidate and a complete release handoff

Before editing shared skills, inspect the public `main`, relevant open PR heads
and bases, consumer lock and owned local diffs. Name the canonical authoring
candidate and one writer for shared skill files. Reuse that owned candidate for
related corrections; do not create another parallel copy or PR for each follow-up.
Company-only material stays in the consumer namespace. A clean checkout does not
mean it contains pending work from another branch.

If work genuinely needs a stack, record dependency order and exact revisions.
The child starts from its actual parent candidate, and its PR targets that
parent until the parent is merged. Do not review the child as an isolated diff
against old `main`, describe an unmerged candidate as released, or resolve drift
by overwriting either checkout. Compare changes against the lock's baseline;
preserve and reconcile both owners' edits when the same managed file changed.

For an authorized release, the owning agent completes this handoff:

1. Verify the public candidate and checks, merge prerequisites in dependency
   order, then retarget/reconcile the next PR against the actual merged parent.
   Recheck the resulting diff and current head; a squash merge changes commit
   identity. Never force-rebase someone else's branch to hide the discrepancy.
2. Verify the intended public change is on `main` and its CI terminal result.
   Use the actual merged full SHA and manifest for the consumer update, even
   when an earlier review pin used an unmerged candidate.
3. Have the consumer owner reconcile its local managed edits, import the exact
   revision, regenerate discovery and check source/hash/context integrity. Keep
   unrelated application work, local output and company configuration preserved.
4. Complete the authorized consumer PR/merge and checks at its actual final
   revision. Reconcile any downstream CI or product-document PR without losing
   its owned delta. Report each repo's `main`, lock and remaining open work.

Merge authority remains a user/project decision. When it is absent, leave a
concrete checked candidate and state that `main` is behind the open PR; do not
claim synchronization or silently switch new users to an unreleased branch.
For offline work, report cached refs and unverified remote freshness. Installing
links from a local working tree exposes that tree's current files; it does not
freeze a release or make its contents equal to public `main`.
