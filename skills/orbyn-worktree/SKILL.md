---
name: orbyn-worktree
description: "Manage local task branches, private contribution storage when supported and Git worktree isolation; use sibling <repo>-wt directories, purpose-based names and preservation before cleanup."
---

# Worktree ownership and lifecycle

Use this skill when a task needs checkout isolation, the user requests a worktree,
or an existing worktree needs reconciliation/cleanup. The
[workflow](../orbyn-workflow/SKILL.md) selects it from the ordinary task request,
without a separate invocation. Follow the consuming project's instructions,
requested checkout and host permissions. A small clear edit can stay in its
current checkout.

## Resolve the repository and owner first

Inspect the current checkout, branch, HEAD, tracked/untracked changes and
`git worktree list --porcelain`. Resolve the primary clone and common repository
from Git registration and the task; the current directory may be a linked worktree.
A linked worktree's `.git` is normally a pointer: do not treat it as an independent
clone or derive another `-wt` root from it.

Preserve unrelated changes and outputs. Do not stash, reset, switch another owner's
checkout, copy dirty files or move existing worktrees merely to enforce this convention.

## Reuse before cloning or replacing

Before creating a checkout, inspect registered trees, canonical repository/remotes,
host attachments and bindings, and any existing reference cache. Reuse a worktree
only when its repository, task owner, branch, source and local work fit this task.
Confirm that no active session still holds a clean directory before reusing it.

Continue the same task/PR in its owned branch and checkout through review and
corrections. Start a new independent task from the verified current default branch
and a stack from its exact reviewed dependency. Do not use a historical task branch
just because it is current, or create a clone per agent/day/retry.

## Sibling location and names

For a primary clone `<parent>/<repo>`, the default root is its sibling
`<parent>/<repo-slug>-wt/`. Use a stable lowercase hyphenated repo slug; reuse an
existing established sibling root rather than creating a case-only alternative.
Each worktree has one direct child directory named for its purpose slug, not the
branch's slash-separated path:

```text
orbyn-fullstack-skills/repo/
  orbyn/                         primary clone
  orbyn-wt/
    task-rescheduling/           feat/task-rescheduling
    save-retry/                  fix/save-retry
    worktree-policy/             chore/worktree-policy
```

Targets use the library-root ignored `repo/` workspace by default under the
[nested repository contract](../orbyn-setup/references/repository-workspaces.md):
`orbyn-fullstack-skills/repo/widget` uses sibling `repo/widget-wt/<purpose>/`.
An explicit user location or an established consuming-project policy wins.

Use lowercase letters, digits and hyphens for a short directory slug, normally
under 64 characters. Use neutral branch prefixes such as `feat/`, `fix/`, `chore/`,
`docs/` or `refactor/`. Do not use agent, assistant, vendor or model branding in a
new branch or directory name. Avoid path separators, traversal, spaces, Windows
device names and case-only distinctions.

Inspect collisions before choosing a name. If the existing path/branch is unrelated
or still owned, choose a distinct purpose or a suffix such as `-2`; never overwrite
a directory, reuse a foreign branch or use force to bypass Git's already-checked-out
protection. Keep existing legacy paths/branch names intact.

## Keep task branches local and publish deliberately

A worktree and its branch are local Git state; they need no branch on the company's
remote. Reuse one owned task branch and worktree through implementation, correction
and review instead of creating one per agent, phase or retry. Never push every
delegate branch. Serialize operations on shared Git refs, remotes and configuration
under one owner.

Keep work local by default. Before any push, follow
[contribution storage](references/contribution-storage.md). A local branch is
recoverable only while its checkout/Git data remain; preserve valuable unpushed
work before cleanup.

## Create and verify the selected checkout

Resolve the requested base revision before writes. Continue an existing task/PR
from its actual branch or reviewed commit. For new work, use the project's verified
default branch/ref, not an unrelated current feature branch or a stale local `main`.
Fetch only when available and authorized; label an offline/cached base as such.

Create a **new** branch from a verified base with
`git worktree add -b <branch> <path> <base>`. Reuse an existing branch with
`worktree add <path> <branch>` only after ownership/checkout inspection. Avoid `-B`,
`--force` and duplicate branch checkouts. Verify the final path, branch, base/HEAD
and status before editing.

Use the selected worktree as the working directory for every subsequent edit/check.
After selecting or switching checkout, reread nested instructions and re-resolve
search roots there under [action scope](../orbyn-setup/references/action-scope.md).

Preserve project environment files; do not automatically copy secrets or run setup
hooks from source. Worktrees share Git objects and may still share databases, ports,
fixtures or external services: assign those separately.

If the host denies Git metadata writes, preserve the patch and report delivery as
blocked. Never rewrite `.git`, supply an alternate index or bypass the sandbox.

## Designate task verification

Before expensive runs, use the CI owner's [feature-worktree gates](../orbyn-ci-design/references/change-scope.md#designate-gates-for-the-feature-worktree).
Name focused checks, exclusions and conditions for widening in the existing task
brief. A new worktree adds no entire-app suite, hosted CI or deployment.

## Preserve before cleanup

At a meaningful handoff or terminal delivery result, apply the single
[task closeout method](references/task-closeout.md): reconcile source, commit,
push, PR and resource states, decide retention with a reason/review trigger,
and assess exact-path retirement separately from permission to remove it.

Never delete another owner's work; unknown ownership means hold. A squash merge or
clean status alone does not clear a tree for removal. Use supported managed archive/Git removal
only after ownership, later commits, dependencies, ignored artifacts, live previews
and recovery are resolved. A refusal has no automatic force fallback; local/remote
ref deletion and tracking prune remain separate.

After a merge, [retire the worktree in the same closeout](references/task-closeout.md#retire-at-delivery)
when you have cleanup authority, and archive its ignored files first: plain
`git worktree remove` deletes them. Keep a merged tree only with a named reason and
review event. Before creating a worktree, run the inventory and retire your own
finished trees.

Return the selected path/base/head, verified delivery state, retained resources,
recovery pointers and actual closeout disposition. A dry run changes nothing.

## Read when needed

- Pushing, forks, private storage, backups or a public PR: [contribution storage](references/contribution-storage.md).
- Recloning, replacing a checkout or an empty partial cache: [checkout replacement](references/checkout-replacement.md).
- In-place, external or bare layouts, delegate branches, unattended runs, denied metadata writes, required dirty primary changes, host worktree tools, search results from another checkout, required statuses at delivery or a worked command example: [checkout setup](references/checkout-setup.md).
- Preview/evidence storage, server/volume ownership or retention classes: [artifact lifecycle](../orbyn-workflow/references/artifact-lifecycle.md).
