# Close out a task without losing its work

Use at a meaningful authorized handoff, merge, closed-unmerged result, abandonment
or recovery takeover. Decide disposition even when the endpoint is a local patch
or no-merge handoff. A few final lines can suffice for small work. This method is
an assessment, not new authority to commit, publish, stop resources or delete.
A cleanup dry run inventories and proposes only; it does not perform teardown,
move files, prune refs, reclone or run mutation probes.

## One identity, independently verified states

Reuse the existing task/issue note and later PR alias with an issue backlink where
one exists. No mandatory issue, extra chat, log directory or tracker is required.
Keep private recovery/resource details in its approved ignored record; no secrets.

| Boundary | Evidence to reconcile in that same record |
| --- | --- |
| Source | Repository identity, owner, exact worktree/branch/base/head, dirty snapshot and tested revision; a commit may coexist with later dirty changes |
| Commit | Not requested, failed, or successful return plus verified HEAD/tree and intended diff; a command attempted is not a commit |
| Push | Local only, failed/unknown, or observed destination/ref/full remote head matching the intended commit; tracking `origin/main` does not prove task publication |
| PR | Absent, draft/open/blocked, closed-unmerged or merged; actual repository/number/head and landing base/commit when merged |
| Resources | Active, held for review, preserved elsewhere, retired or unresolved; actual paths/handles, owner, next action and hold reason/review trigger |

Worker exit, clean Git status, a gone tracking ref and PR closure establish none
of the other states. Preserve earlier results as historical, update current claims
and label unavailable remote readback last-observed/unknown. Do not repeat a possibly
completed publication blindly. Closing an issue/PR, commenting or archiving a chat
remains a separate external effect; PR closure does not prove an issue resolved.
The [publication gate](../../orbyn-workflow/playbooks/opening-a-pr.md#commit-and-push-gate)
owns successful commit/push verification; no auto-commit of unrelated work for cleanup.

## Decide what remains and why

| Current observation | Disposition to record, within existing authority |
| --- | --- |
| Dirty/unpushed/unreviewed source | Keep owned checkout and next action; preserve a recoverable checkpoint for a pause |
| Open/draft PR or pending human preview | Keep resumable source and required evidence; identify any separately disposable idle resources |
| Blocked/waiting | Keep needed source/evidence, blocker, responsible next check and review trigger; release only unneeded owned resources within scope |
| Exact reviewed head merged | Verify actual landing content/base and relevant CI, then inspect later work/dependencies/resources before proposing retirement |
| Closed without merge | Preserve unlanded work and reason/next decision; do not label it delivered or silently discard it |
| Replaced/interrupted owner | Fence former writers under the supported lifecycle, reconcile late/partial effects and keep exact resume identity |

A hold needs a reason and review event/date under project policy, not permanent
silent accumulation. Unknown ownership means hold with a named ownership-resolution
check, never deletion. A review trigger is not a scheduler; no automatic TTL,
future reminder or new monitor follows. Do not reopen stopped work to inspect it.
[Artifact retention](../../orbyn-workflow/references/artifact-lifecycle.md#retention-and-growth-decisions)
owns what to keep and how to make the retained package reopenable.

## Retirement gate for an exact path or ref

Only propose an item as ready when its following boundaries are accounted for;
perform removal later only with applicable cleanup authority and fresh rechecks.
Use existing Git/host tools and a small task record, not a new inventory platform.

1. **Identity and ownership:** exact canonical path/ref and repository; actual
   current writer, host attachment/session cwd, locks and dependent work. Primary,
   active, release or foreign source is not a retirement candidate. Do not follow
   a symlink/changed binding into a different checkout.
2. **Source and landing:** inspect staged/unstaged/untracked source, local commits,
   verified pushed/PR heads and actual landing state. Squash/rebase changes ancestry:
   `branch --merged` alone is insufficient. Compare reviewed head and landing content
   in their real base context, later unpushed commits and dependent branches/PRs.
   Neither a branch name nor a gone remote ref proves the local work landed.
3. **Resources:** inspect ignored output/configuration, previews/processes, running
   tests, containers/volumes, shared mutable dependencies and recovery needs.
   A clean status hides ignored files. An active server or another owner's build
   can depend on this directory even when its PR merged.
4. **Preservation:** copy only approved exact paths to a permitted durable owner
   when needed, including local assets/restart instructions and relevant failed
   evidence. Verify hashes and reopen the retained artifact or verify restore
   prerequisites. Git commits/bundles do not contain ignored output or credentials.
   Incremental bundles can require a retained base; a successful bundle creation
   is not a demonstrated standalone recovery path. Keep unknown/unlanded work.
5. **Supported action and readback:** use the host's supported managed archive or
   ordinary `git worktree remove` for the verified inactive path after preservation.
   Do not substitute filesystem deletion, force removal or reset/clean. If an
   operation refuses, investigate and retain the item; no automatic force fallback.
   Interrupted teardown requires actual path/registration/process readback before
   retry, not a second blind removal. Report retained/archived/removed separately.

Worktree retirement, local branch deletion, remote branch deletion and local
remote-tracking pruning are distinct decisions with exact scopes. Inspect configured
upstreams/refspecs and tags before any future prune. Pruning local tracking data
is not deletion of a hosted branch. A safe local deletion refusal after a squash
merge is evidence to investigate/preserve, not permission for force deletion.
Do not globally prune Git objects, Docker, caches, temporary roots or sessions.
Allocated directory sums and logical sizes are not promised physical reclaimed
space; report measured post-state only after an authorized operation actually ran.

## Synthetic closeout example

PR 17 merged by squash, but its task tree has a later local commit, ignored review
captures and a live preview. The source row records the later HEAD; push records
the older observed PR head; PR records the actual merged commit. Resources remain
held for preview review. Keep the later source and a verified reopenable evidence
package, check dependent work and obtain the owner's release before any separately
authorized teardown. An ancestry-only check, clean status or merged badge cannot
turn this tree into disposable cache. If PR 17 had closed without merge, its
unlanded source would still need preservation and a disposition.

This is independently authored guidance and a synthetic example, not an executed
cleanup qualification. Tool context reviewed 30 October 2026:
[Git worktree lifecycle](https://git-scm.com/docs/git-worktree),
[bundle prerequisites](https://git-scm.com/docs/git-bundle),
[local branch deletion](https://git-scm.com/docs/git-branch) and
[remote-tracking prune scope](https://git-scm.com/docs/git-remote).
Use installed/host semantics; these pointers grant no deletion authority.
