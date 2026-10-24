---
name: orbyn-worktree
description: "Choose, create, reuse and clean up Git worktrees for isolated repository work; enforce sibling <repo>-wt directories, purpose-based names and preservation of local work."
---

# Worktree ownership and lifecycle

Use this skill when a task needs checkout isolation, the user requests a worktree,
or an existing worktree needs reconciliation/cleanup. The owning
[workflow](../orbyn-workflow/SKILL.md) selects it from the ordinary task request;
the human does not need a separate invocation. Follow the consuming project's
instructions, requested checkout and host permissions. A small clear edit can
stay in its current checkout; a new worktree is not mandatory for every task.

## Resolve the repository and owner first

Inspect the current checkout, branch, HEAD, tracked/untracked changes and
`git worktree list --porcelain`. Resolve the primary clone and common repository
from Git registration and the task, rather than assuming the current working
directory is the primary clone. A linked worktree's `.git` is normally a pointer;
do not treat it as another independent clone or derive another `-wt` root from it.
Bare or separately configured Git directories need an explicit project anchor.

Check existing worktrees and any applicable host attachment inventory before
creating another. Reuse a suitable worktree only when its repository, task owner,
branch, source and local work fit this task. A clean directory is not evidence
that another active session has released it. Preserve unrelated changes and
outputs; do not stash, reset, switch another owner's checkout, copy dirty files
or move existing worktrees merely to enforce this convention.

## Sibling location and names

For a primary clone `<parent>/<repo>`, the default root is its sibling
`<parent>/<repo-slug>-wt/`. Use a stable lowercase hyphenated repo slug; reuse an
existing established sibling root rather than creating a case-only alternative.
Each worktree has one direct child directory named for its purpose:

```text
Documents/GitHub/
  orbyn/                         primary clone
  orbyn-wt/
    task-rescheduling/           feat/task-rescheduling
    save-retry/                  fix/save-retry
    worktree-policy/             chore/worktree-policy
```

Use lowercase letters, digits and hyphens for a short directory slug, normally
under 64 characters. Use neutral branch prefixes such as `feat/`, `fix/`,
`chore/`, `docs/` or `refactor/`. Do not use agent, assistant, vendor or model
branding in a new branch or directory name. Avoid path separators, traversal,
spaces, Windows device names and case-only distinctions. A directory leaf uses
the purpose slug, not the branch's slash-separated path.

Inspect collisions before choosing another name. If the existing path/branch is
unrelated or still owned, choose a distinct purpose or a suffix such as `-2`;
never overwrite a directory, reuse a foreign branch or use force to bypass Git's
already-checked-out protection. Keep existing legacy paths/branch names intact.
An explicit user location or an established consuming-project policy wins.

## Create and verify the selected checkout

Resolve the requested base revision before writes. Continue an existing task/PR
from its actual branch or reviewed commit. For new work, use the project's
verified default branch/ref; do not assume that an unrelated current feature
branch or a stale local `main` is the desired base. Fetch only when available and
authorized; label an offline/cached base as such. A clean worktree does not copy
the primary checkout's uncommitted changes. If those changes are required, plan
a selective, recoverable transfer with their owner instead of silently omitting
or copying them.

Use a supported host worktree tool when it meets the requested layout and
ownership contract. If its storage path is fixed elsewhere, report the limitation
and use a permitted Git operation when appropriate; do not claim a custom path
was honored when the tool chose another. Creating a worktree does not create a
new project chat or authorize messaging another owner.

For a **new** branch with a verified base, an example operation is:

```sh
git -C /work/orbyn worktree add -b feat/task-rescheduling /work/orbyn-wt/task-rescheduling origin/main
git -C /work/orbyn-wt/task-rescheduling status --short --branch
git -C /work/orbyn-wt/task-rescheduling rev-parse --show-toplevel HEAD
```

These paths/ref are examples, not values to copy into another project. Reuse an
existing branch with `worktree add <path> <branch>` only after ownership/checkout
inspection. Avoid `-B`, `--force` and duplicate branch checkouts. Verify the final
path, branch, base/HEAD and status before editing. Use the selected worktree as
the working directory for every subsequent edit/check; reread relevant nested
instructions there. Preserve project environment files; do not automatically copy
secrets or run setup hooks from source. Worktrees share Git objects and may still
share databases, ports, fixtures or external services: assign those separately.

## Preserve before cleanup

Clean up only an owned, inactive worktree within the authorized delivery/cleanup
scope. Check tracked and untracked changes, unpushed/unmerged commits, locks,
ignored output, local configuration and active processes. `git status` alone does
not reveal ignored artifacts. Inspect ignored paths without printing secrets;
classify reproducible dependency caches separately from valuable output and
configuration. Preserve needed data in an owned recoverable location first.

For managed worktrees, use their supported archive flow and separately preserve
needed ignored files. For ordinary Git worktrees, use `git worktree remove` on
the verified exact path after preservation; never delete a checkout with a blanket
filesystem removal, forced reset/clean or force removal. Do not delete branches
or prune another owner's registrations as an incidental step. Move/repair/prune
only a diagnosed owned registration within scope; removal of a directory alone
does not reconcile Git metadata. If preservation or ownership is unresolved,
leave the worktree intact, record the reason and continue independent work.

Return the primary clone, sibling root, selected path, branch/base/HEAD, owner,
preserved data and actual retained/removed/archived state. A merged PR does not
prove its local checkout or outputs are safe to delete.
