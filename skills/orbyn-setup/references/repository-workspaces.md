# Nested engineering workspace

## Default layout

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

Use the nested layout unless a person or managing application registers a target
[in place](#in-place-targets). Do not install, vendor, copy or symlink shared
skills into targets; do not create target public-skill locks or sync pipelines.
The library alone changes when shared skills improve. Report its actual revision
and dirty state; an open PR candidate is not released `main`. Teams can agree a
reviewed library revision and check it out in their outer workspace without adding
a library dependency inside every target repository.

## In-place targets

A person, or an application managing this library for them, can register a target
that stays at its existing path. The library remains the agent's root; the task
names the target's absolute path. This is the same outer/target relationship
without relocation, not a target installation. Registering a path authorizes work
in that checkout only; it does not authorize moving, cloning or deleting it.

- Grant the host access to the selected checkout with its own session mechanism,
  such as an additional-directory flag or sandbox writable root. Never edit
  user-wide settings or write into the target to achieve this.
- Compare writes against the canonical checkout path, including symlink escapes,
  and resolve relative tool paths explicitly: the agent's working directory is
  the library, not the target.
- Read target instructions directly. A separate root makes host discovery less
  certain than nesting, so report it as unobserved unless actually observed.
- Run `python3 skills/orbyn-setup/scripts/workspace.py check --in-place --target <path>`.
  It requires a Git root, and refuses the library, anything inside it and any
  folder containing it.
- Worktrees stay siblings of the primary clone, at `<project>-wt/<purpose>/` beside
  the target. No target files, excludes or instructions are written.

Choosing in-place registration is an explicit decision. A setup request with no
such decision still uses the nested layout.

## Instructions and ownership

Select the exact target/worktree and retrieval roots before searching. Follow
[action scope](action-scope.md) for separate instruction/code lookup, relevant
refresh and the difference between file reads, request inclusion and enforcement.
The method uses ordinary filesystem/Git inspection; no registry, daemon, index,
mandatory hooks or per-target configuration is added.

Before changing a target, resolve its actual Git root and worktree/common Git
metadata. Read its AGENT.md, AGENTS.md, CLAUDE.md, codex.md, .cursorrules, applicable nested
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

## Project-owned instructions now and later

Every target, including Orbyn, can own or later add `AGENT.md`, `AGENTS.md`,
`CLAUDE.md`, nested instructions and local skills. Names alone do not make them a
copied installation. Keep project commands, module ownership, data constraints,
verification rules and guide pointers with that target's existing owner. Shared
engineering methods remain in the outer library. No setup step creates these
files or moves the target's own skills automatically.

Orbyn's cleanup retires its current duplicated shared-policy wrappers and copied
skillset. It does not permanently ban project instruction filenames or legitimate
local guidance. A future Orbyn instruction file can point to CONTRIBUTING.md and
its development/operations/design guides without embedding another library copy.
A CI guard can reject known copied library assets and sync tooling; it cannot
prove from a filename that prose is project-specific or that an agent read it.
Review the actual instructions and their owner.

The agent reads the outer entrypoint and relevant shared skills, resolves the
selected target Git root, then reads its root and applicable nested guidance.
User instructions and host permissions take precedence. Target-specific stack,
checks and contribution rules specialize compatible shared methods. If a real
conflict remains, identify both files/rules, continue independent safe work and
resolve the conflict before dependent actions. Do not merge the files, silently
ignore the project rule or claim that nesting determines a host's discovery order.
`AGENT.md` is a supported file to inspect, not a promise that every host loads it
automatically; read it directly when required.

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
By default it refuses external targets, symlinked roots, ancestor/subdirectory
confusion and linked worktrees whose common Git metadata remains outside the nested
workspace; `--in-place` applies the separate rules above.
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
