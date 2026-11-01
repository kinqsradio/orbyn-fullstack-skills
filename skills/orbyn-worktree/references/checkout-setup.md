# Checkout setup outside the common path

Read the section that applies when the target layout, host or task differs from
the common path in [the skill entrypoint](../SKILL.md).

## Worked command example

For a **new** branch with a verified base, an example operation is:

```sh
git -C /work/orbyn-fullstack-skills/repo/orbyn worktree add -b feat/task-rescheduling /work/orbyn-fullstack-skills/repo/orbyn-wt/task-rescheduling origin/main
git -C /work/orbyn-fullstack-skills/repo/orbyn-wt/task-rescheduling status --short --branch
git -C /work/orbyn-fullstack-skills/repo/orbyn-wt/task-rescheduling rev-parse --show-toplevel HEAD
```

These paths/ref are examples; replace them with the actual project's values.

## Layouts other than a nested target

A target [registered in place](../../orbyn-setup/references/repository-workspaces.md#in-place-targets)
uses the same sibling rule beside its own path. Preserve target instructions/skills
and inspect its Git state separately. Other existing external checkouts remain
preservation inputs until a coordinated authorized move; never move active work
merely to satisfy the layout. The library's own maintenance worktrees can use its
established external sibling root, keeping library and target ownership distinct.

Keep target nesting and the library's established sibling root. Bare or separately
configured Git directories need an explicit project anchor.

## Delegate branches

Independent writers may need bounded temporary local branches/worktrees. Consolidate
their changes into the owning task branch and retire them only after preserving
the work.

## Unattended execution

Verify required host capabilities on a disposable checkout with the actual topology
before expensive work. A primary-clone commit probe says nothing about write access
to a linked worktree's separate Git index or common metadata, so probe the linked
topology itself. Test only effects already authorized by the task.

If the host denies metadata writes, preserve the patch and report delivery as
blocked; do not rewrite `.git`, supply an alternate index or bypass the sandbox.
A separately authorized new workspace needs its own readiness evidence; never move
or reset existing owned work to manufacture a passing probe.

## Uncommitted source from the primary checkout

A clean worktree does not copy the primary checkout's uncommitted changes. If those
changes are required, plan a selective, recoverable transfer with their owner
instead of silently omitting or copying them.

## Host worktree tools

Use a supported host worktree tool when it meets the requested layout and ownership
contract. If its storage path is fixed elsewhere, report the limitation and use a
permitted Git operation when appropriate; do not claim a custom path was honored
when the tool chose another. Creating a worktree creates no project chat and gives
no authority to message another owner.

## After switching checkout

Do not reuse another checkout's search results as current evidence. Shared Git
history or project memory can still differ in rules, source and branch-specific
applicability.

## Verification and runtime effects

Name focused checks for the affected contracts and consumers. Required repository
statuses still apply at delivery, and isolated files leave runtime effects shared
until you assign them separately.
