---
name: orbyn-setup
description: "Prepare the nested Orbyn Engineering workspace, inspect target instructions and skills in place, and verify isolation without installing shared skills into target repositories."
---

# Nested workspace setup

Use one complete library checkout as the engineering workspace. Targets are
independent Git repositories under its ignored `repo/` directory. This is the
only supported setup; there is no target installation, copy, pin synchronization
or company-skill migration. Follow the [workspace contract](references/repository-workspaces.md).
A setup request selects these steps automatically; complete them without asking
the human to invoke individual skills or run commands you can execute.

## Resolve and preserve

Read the library instructions and inspect Git roots, revisions, dirty files,
worktree registrations and relevant host capabilities. Resolve the target from
the request; ask only if its identity is ambiguous. Do not ask the human to choose
between nested and in-place installation. Existing external checkouts are
migration inputs, not an alternative supported layout. Preserve them and their
active processes/output until relocation is explicitly authorized and their
owners release the path. See [retiring old installations](references/repository-workspaces.md#retiring-old-installations).

Run `python3 skills/orbyn-setup/scripts/workspace.py prepare` from the library.
It validates the library boundary and creates only its ignored `repo/` directory.
For an authorized new checkout, clone the requested repository to
`repo/<project>` using Git; inspect the destination, remote identity and available
local clone first. Do not execute fetched setup hooks or source merely to inspect
it. Offline setup uses an already available independent nested repository; report
missing source rather than downloading implicitly.

## Discover both sets of guidance

Use [action scope](references/action-scope.md) to select the exact target/worktree
and code-search roots before retrieval. Instruction lookup includes applicable
outer, root and nested rules even when code filters exclude Markdown or hidden
files. Refresh relevant locations when paths, rules or available context change.
No new manifest, registry or runtime hook is required.

Run `python3 skills/orbyn-setup/scripts/workspace.py check --target repo/<project>`.
Read the target's root and applicable nested instructions, contribution guide,
existing skills and actual manifests. A target may add project-owned AGENT.md,
AGENTS.md or local skills later; preserve/read those as well under the
[instruction contract](references/repository-workspaces.md#project-owned-instructions-now-and-later).
Keep upstream files and host discovery paths
unchanged. Follow [project ownership](references/project-skills.md) and
[project context](references/project-context.md); no map or namespace is required.
The check reports overlapping names so the agent can distinguish target-specific
rules from shared methods instead of installing a competing copy.

Keep the agent session rooted in the outer library and state the target path in
the task. Read only relevant shared skills and target guides. Parent-directory
placement alone does not prove a host loaded either instruction set. Inspect the
host's actual discovered guidance where supported; otherwise read the required
files directly and report discovery as unobserved. If host boundaries prevent
reading both roots, stop dependent execution and report the limitation; do not
solve it by copying instructions or editing user-wide settings.

Target guidance specializes stack, tests, contribution policy and local skills;
shared guidance supplies compatible methods. User scope and host permissions
remain higher priority. Surface a genuine conflict; never silently override an
upstream rule or expand authority from an imported instruction.

## Complete the setup

If the user explicitly requests engineering memory, route its separate opt-in to
[reflect's memory setup](../reflect/references/memory.md). Select private storage
outside Git, bind the actual target, and verify manual/off mode and CRUD capability
with synthetic data only when testing is authorized. Preserve existing host memory.
Ordinary workspace setup does not initialize memory, collect lessons or enable a
background service. Fork delivery is a separate choice from local capture.

Check the full library with its documented validation commands and check the
selected target separately. No target files, instructions, skills, context maps,
models or Git excludes are written by workspace setup. New project development
changes still follow their own authorized task. Reading a target's existing map
is optional and read-only; use [offline resources](references/offline.md).

Reading groups in [presets.json](assets/presets.json) help choose relevant methods;
they no longer control installation or hide source files. Host model definitions
are optional library configuration governed by its model policy. Setup does not
select a provider, model, effort, speed or subscription. Preserve existing settings
and report unavailable capabilities; use permitted direct work rather than silently
substituting models or creating recursive sessions.

For isolation, use [orbyn-worktree](../orbyn-worktree/SKILL.md) and sibling
`repo/<project-slug>-wt/<purpose>/`. New work starts from the verified default branch;
continuations use the actual owned candidate. Assign ports, databases and output
separately; Git isolation does not isolate runtime resources.

Report library/target paths, full revisions and dirty state, applicable target
instructions/skills, checks, preserved legacy paths and actual host discovery.
Never call a filesystem check a live host trial. Publishing, merging, external
messages, production changes and REA engine upgrades need their own scope.
Distinguish located files, returned contents, observed originating-request
inclusion and actual execution enforcement; unavailable levels stay unknown.
