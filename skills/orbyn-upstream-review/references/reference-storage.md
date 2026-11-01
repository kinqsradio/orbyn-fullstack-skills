# Reference storage, handling and caches

Read the section that applies when extracting or licensing a source, or once the default layout in
[Keep downloaded research outside Git](../SKILL.md#keep-downloaded-research-outside-git)
no longer covers the source, the ignore state or a shared cache.

## Non-Git sources and existing locations

For non-Git research sources, use a stable source ID plus content digest/version
and retrieval date. Retain supplied source files and their provenance. Existing
ignored `openSrc/` research can remain where it is; do not move/delete it just to
enforce the new name.

## Ignore state that does not verify

If files are already tracked, stop publication of that material, preserve it and
report the paths; do not erase history or discard files automatically. In a non-Git
project, prepare the exclusion and report that Git enforcement is unverified until
a repository exists.

## Handle downloaded material

Inspect paths and size before extraction; reject traversal, unexpected links and
special files. Local-only does not make licensed or private material publishable.
Preserve the original notices in the local source.

## Offline support and vendored code

Bundled offline support under a skill's `references/upstream/` differs from raw
research: those files need an explicit reuse decision, compatible license/notices,
pinned snapshot hashes and existing source checks. Do not relocate approved offline
support into an ignored folder and leave an active skill dependent on an absent download.

Existing intentionally vendored code that the project builds or runs remains
under its dependency/source owner and licensing contract. The research rule
does not authorize deleting, moving or untracking that dependency. Promote new
vendored code only as an explicit reviewed dependency change at its owning path,
with the required notices and source manifest; do not commit the research folder.

## Shared reference-cache identity

A managed reference advertisement, attached cache and actual readable source are
separate facts. Freeze the resolved commit and selected file hashes before
comparison; a shared cache refresh/reset can change bytes between attachment and
a later read. Recheck identity before applying a returned finding. Preserve both
observations on drift; do not silently replace the reference or count a catalog
listing as readiness. Existing target restrictions and source-owned conventions
remain evidence about that project, not universal library policy.

## Repeated research on one upstream

Reuse a suitable ignored partial/no-checkout source cache where supported, with
immutable selected pin/hash receipts per comparison. Inspect existing cache
identity/owner and live readers first; do not reset another review's source or
create a full clone per task/day/agent. This cache is distinct from a target working
clone; do not convert or move an active target merely to save space. Preserve
approved offline support and notices.

Its terminal retention decision follows [artifact retention](../../orbyn-workflow/references/artifact-lifecycle.md#retention-and-growth-decisions)
and the [closeout gate](../../orbyn-worktree/references/task-closeout.md); a download
or new review does not authorize cache eviction or a janitor.
