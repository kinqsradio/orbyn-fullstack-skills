# Nested engineering workspace

## One supported layout

```text
orbyn-fullstack-skills/          open this as the agent workspace
  AGENTS.md                     shared engineering policy
  skills/                       canonical methods and local references
  .agents/skills/               library discovery
  .claude/skills/               library discovery
  repo/                         ignored; independent Git histories
    widget/                     target primary clone, its own .git
    widget-wt/
      fix-save/                 target linked worktree
```

Use nested workspaces exclusively. Do not install, vendor, copy or symlink shared
skills into targets; do not create target public-skill locks or sync pipelines.
The library alone changes when shared skills improve. Report its actual revision
and dirty state; an open PR candidate is not released `main`. Teams can agree a
reviewed library revision and check it out in their outer workspace without adding
a library dependency inside every target repository.

## Instructions and ownership

Before changing a target, resolve its actual Git root and worktree/common Git
metadata. Read its AGENTS.md, CLAUDE.md, codex.md, .cursorrules, applicable nested
instructions, contribution rules and existing skills. Preserve all upstream-owned
guidance in place. Orbyn's explicitly authorized retirement of its duplicated
installation is a project migration, never a rule to delete another project's
AGENTS.md or skills. Existing project rules govern its stack, checks and contribution
contracts; shared methods apply where compatible. Human scope and host permissions
remain higher priority. Resolve a material conflict before dependent edits.

Start the agent in the library root, identify the target and read relevant shared
skills explicitly when needed. Hosts may limit ancestor discovery at a Git root,
use workspace trust boundaries, or retain instructions already loaded in a running
session. Nesting is filesystem organization, not proof of effective discovery or
an authority override. Observe actual host discovery when available; otherwise
report manual file reads separately. Reopen/rebind a session only with the user's
applicable session scope, and never copy instructions as a silent workaround.

Company or upstream skills stay with their owner in its existing paths. A same-name
skill does not authorize replacement or renaming. Select the target-specific rule
and compatible library method explicitly; name collisions remain visible.

## Git, runtime and publication boundaries

`repo/`, `openSrc/` and `orbyn-references/` must remain ignored and absent from the
library's index, including gitlinks. The checker rejects tracked nested content.
Inspect target and library Git states independently; a clean parent says nothing
about dirty/unpushed target work. Never force-add target source, history, secrets,
research downloads, outputs or company instructions into the public library.
A folder is not access control: follow the target's visibility and redistribution
rules before cloning or publication.

Use sibling `repo/<project-slug>-wt/<purpose>/` worktrees with neutral purpose branches.
Keep branches local until delivery is authorized; reuse approved contribution
storage under [worktree policy](../../orbyn-worktree/SKILL.md). Assign independent
ports, databases, processes and artifact directories as needed. Target CI builds
the target; library CI validates the library. Neither executes the other repo's
setup code merely to check nesting. No REA engine or runtime upgrade follows.

The helper uses Git metadata only. `prepare` creates the ignored workspace folder;
`check` reads root/revision/status/instruction metadata and flags same-name skills.
It refuses external targets, symlinked roots, ancestor/subdirectory confusion and
linked worktrees whose common Git metadata remains outside the nested workspace.
It never clones, moves or rewrites the target, edits global configuration, or
claims observed host discovery. Agents complete authorized Git operations separately.

## Retiring old installations

1. Inventory both repositories, open PRs, local commits, worktree registrations,
   ignored output, private configuration, active processes and path owners.
   Reconcile legitimate pending changes before deleting a copied installation.
   Preserve recoverable commits and valuable untracked/ignored artifacts. A clean
   status or merged PR is insufficient evidence that a checkout can be removed.
2. Audit references to copied skills, host links, root instruction wrappers, locks,
   sync scripts and CI. Rehome any project runtime/CI dependency before removing
   shared copies. Preserve needed project facts and required licenses/notices.
   Only remove material proven owned by the retired installation, under explicit
   migration authority. Do not classify foreign skills by their names alone.
3. Publish/merge the scoped cleanup only when authorized and its required checks
   pass. Leave unrelated product work intact. Document the nested contributor
   setup and surviving project guides. Retain historical evidence as history,
   clearly separated from current setup instructions.
4. Coordinate with owners before relocating an existing primary clone. Preserve
   its Git objects, dirty files, envs, ignored output and linked worktrees. Prefer
   supported Git worktree moves/repair where applicable; never move another active
   session's cwd, rewrite .git manually, or use forced clean/reset/removal. Verify
   all registrations, origins, branches and artifact hashes at the final paths.
   If owners still need a legacy path, retain it and report migration incomplete.
5. Recheck the nested target and its own main/CI state. Release old paths only
   after preservation and host/session continuity are established. A transitional
   recovery checkout is preserved data, not a second supported installation.

## Worked contribution

An agent opens the library, targets `repo/widget`, reads widget's own AGENTS.md
and test policy, then uses the local `how` reproduction method. Widget's existing
`.agents/skills/how` is preserved and its project-specific contract read first;
the helper reports the overlap. The agent fixes widget in
`repo/widget-wt/save-retry`, runs widget's authorized tests and submits only widget
changes to its verified upstream. A reusable skill improvement uses a separate
library diff and publication authority. No setup-only files enter widget's PR.
