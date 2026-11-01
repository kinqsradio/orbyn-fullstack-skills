# Reclone or replace a checkout

Read this before recloning, replacing a checkout or treating an empty reference
cache as lost work. Check reuse first under
[Reuse before cloning or replacing](../SKILL.md#reuse-before-cloning-or-replacing).

## Decide whether to reclone

Reclone only for a new repository, proven missing/unrecoverable source store,
necessary separate trust/credential boundary or demonstrated incompatible need.
Try suitable supported readiness/repair first. A stale cwd, conflict or old build
is not itself a reason to reclone.

## Read a partial or no-checkout cache

An intentional partial/no-checkout reference cache can lack an index or visible
source and show deletion-like status. Resolve its intended materialization mode,
pinned source and owner before interpreting that as lost work/corruption; a promisor
setting alone shows neither intent nor safety. Do not reset, checkout over or
reclone it on that symptom alone.

## Replace when authorized

1. Preserve local refs/commits, binary-capable staged/unstaged snapshots, untracked
   source and valuable ignored data/configuration in permitted storage.
2. Verify any bundle prerequisites and the replacement beside the old checkout.
3. Deliberately rebind task/host paths and reread instructions. Check the host
   binding itself; a successful explicit workdir does not show that it changed.
4. Use [continuation readiness](../../orbyn-setup/SKILL.md#resume-after-a-workspace-or-runtime-change).

Do not automatically copy credentials, move an active path or delete the old clone.
