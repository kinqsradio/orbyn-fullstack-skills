---
name: orbyn-setup
description: "Prepare the nested Orbyn Engineering workspace, inspect target instructions and skills in place, and verify isolation without installing shared skills into target repositories."
---

# Nested workspace setup

Use one complete library checkout as the engineering workspace. Targets are
independent Git repositories, under its ignored `repo/` directory by default or
[registered in place](references/repository-workspaces.md#in-place-targets) by
explicit decision. There is no target installation, copy, pin synchronization
or company-skill migration. Follow the [workspace contract](references/repository-workspaces.md).
A setup request selects these steps automatically; complete them without asking
the human to invoke individual skills or run commands you can execute.

## Method

1. **Inspect.** Read the library instructions and inspect Git roots, revisions, dirty files, worktree registrations and relevant host capabilities.
2. **Resolve the target** from the request, asking only if its identity is ambiguous. Use the nested layout unless the human or a managing application registered the target in place; do not ask the human to choose a layout.
3. **Prepare the library.** Run `python3 skills/orbyn-setup/scripts/workspace.py prepare` from the library. It validates the library boundary and creates only its ignored `repo/` directory.
4. **Get the checkout.** For an authorized new checkout, inspect the destination, remote identity and available local clone, then clone the requested repository to `repo/<project>` using Git. Do not execute fetched setup hooks or source merely to inspect it. Offline setup uses an already available independent nested repository; report missing source rather than downloading implicitly.
5. **Select search roots.** Use [action scope](references/action-scope.md) to select the exact target/worktree and code-search roots before retrieval. Instruction lookup includes applicable outer, root and nested rules even when code filters exclude Markdown or hidden files. Refresh relevant locations when paths, rules or available context change. Check [ripgrep readiness and fallback](references/offline.md#ripgrep-readiness-and-fallback) in the actual agent environment before relying on `rg`; a missing tool does not authorize an install, so use bounded inspection with an available alternative.
6. **Read the target's guidance.** Run `python3 skills/orbyn-setup/scripts/workspace.py check --target repo/<project>`. Read the target's root and applicable nested instructions, contribution guide, existing skills and actual manifests. The check reports overlapping names so you can distinguish target-specific rules from shared methods instead of installing a competing copy.
7. **Root the session in the outer library** and state the target path in the task. Read only relevant shared skills and target guides. Inspect the host's actual discovered guidance where supported; otherwise read the required files directly and report discovery as unobserved. Parent-directory placement alone does not prove a host loaded either instruction set.
8. **Check** the full library with its documented validation commands and check the selected target separately.
9. **Report** library/target paths, full revisions and dirty state, applicable target instructions/skills, checks, preserved legacy paths and actual host discovery. Distinguish located files, returned contents, observed originating-request inclusion and actual execution enforcement; unavailable levels stay unknown. Never call a filesystem check a live host trial.

## What setup leaves alone

- Workspace setup writes no target files, instructions, skills, context maps, models or Git excludes. New project development changes follow their own authorized task. Reading a target's existing map is optional and read-only; use [offline resources](references/offline.md).
- Keep upstream files and host discovery paths unchanged. A target may add project-owned AGENT.md, AGENTS.md or local skills later; preserve and read those under the [instruction contract](references/repository-workspaces.md#project-owned-instructions-now-and-later). Follow [project ownership](references/project-skills.md) and [project context](references/project-context.md); no map or namespace is required.
- Existing external checkouts are migration inputs unless registered in place. Preserve them and their active processes/output until relocation is explicitly authorized and their owners release the path. See [retiring old installations](references/repository-workspaces.md#retiring-old-installations).
- Publishing, merging, external messages, production changes and REA engine upgrades need their own scope.
- Report the resolved harness for each target with the `harness.py` in the loaded `orbyn-workflow` skill's directory, by absolute path (`python3 <orbyn-workflow directory>/scripts/harness.py resolve --target <target>`; a missing script means stop and report). To tune one repository, the owner may add `.orbyn/harness.json` there (a target change needing normal authority) or a local `repo/.harness/<target-slug>.json`; setup writes neither. See [harness settings](../orbyn-workflow/references/harness-settings.md).
- Setup does not select a provider, model, effort, speed or subscription. Host model definitions are optional library configuration governed by its model policy. Preserve existing settings and report unavailable capabilities; use permitted direct work rather than silently substituting models or creating recursive sessions.
- Reading groups in [presets.json](assets/presets.json) help choose relevant methods; they no longer control installation or hide source files.

## Resolve instruction conflicts

Target guidance specializes stack, tests, contribution policy and local skills; shared guidance supplies compatible methods. User scope and host permissions remain higher priority. Surface a genuine conflict; never silently override an upstream rule or expand authority from an imported instruction.

If host boundaries prevent reading both roots, stop dependent execution and report the limitation. Do not solve it by copying instructions or editing user-wide settings.

## Resume after a workspace or runtime change

After migration/resumption, a failed working directory or a runtime mismatch, reconcile the actual selected checkout with the host's saved session binding where observable. An explicit command workdir, a moved folder or project membership does not prove the session was rebound. Use a supported authorized host mechanism if needed; otherwise report the stale/unknown binding, use a valid explicit workdir for supported work and retain that distinction. Do not recreate a deleted checkout or rewrite global session settings/PATH to hide the problem.

Inspect the next required command's documented runner/version and resolve a compatible already-installed runtime in the actual execution environment before an expensive run. A harmless version/capability check is sufficient when available. Do not execute untrusted setup hooks or install a runtime implicitly. If no runtime is supported, report the dependent check blocked and continue independent work. Reuse current matching readiness evidence. This is conditional recovery, not a full setup ritual on every action or a reason to repeat passed suites.

## Read when needed

- An explicit engineering-memory request: route its separate opt-in to [reflect's memory setup](../reflect/references/memory.md), with private storage outside Git bound to the actual target. Ordinary workspace setup does not initialize memory, collect lessons or enable a background service.
- Isolation: [orbyn-worktree](../orbyn-worktree/SKILL.md) and sibling `repo/<project-slug>-wt/<purpose>/`. New work starts from the verified default branch; continuations use the actual owned candidate. Assign ports, databases and output separately, because Git isolation does not isolate runtime resources.
