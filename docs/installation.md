# Set up the nested engineering workspace

Open the complete library checkout as the agent workspace and ask the agent to
set up the target by URL or existing path. Nested is the only supported setup.
There is no target installer, copied skill bundle, consumer lock, pin promotion
or skill synchronization pipeline. The agent completes local steps automatically;
the human does not need extra skill invocations.

## Agent procedure

1. Read root policy and [orbyn-setup](../skills/orbyn-setup/SKILL.md). Resolve the
   requested target and inspect existing local work, worktrees and active owners.
2. Run `python3 skills/orbyn-setup/scripts/workspace.py prepare` from the library.
   It validates Git/ignore boundaries and creates only the ignored `repo/` folder.
3. Clone an authorized new target to `repo/<project>` or coordinate a recoverable
   migration of an existing external checkout. Never overwrite a destination,
   move an active owner's path, or lose dirty/ignored work. Existing paths stay
   preserved until the [retirement procedure](../skills/orbyn-setup/references/repository-workspaces.md#retiring-old-installations)
   is complete. Offline setup needs locally available source; no implicit download.
4. Read the target's root/nested instructions, contribution rules, own skills and
   project manifests. Do not change its instructions or discovery/configuration
   as a setup side effect. Target policy specializes compatible shared methods.
5. Run `python3 skills/orbyn-setup/scripts/workspace.py check --target repo/<project>`.
   Inspect target and library status separately. If isolation is needed, use
   `repo/<project-slug>-wt/<purpose>/` and check the actual selected worktree again.
6. Verify relevant host discovery when supported, or read required files directly
   and label discovery unobserved. Report exact paths/revisions, checks, preserved
   work and missing capabilities. A host may require a fresh outer-root session;
   changing user-wide settings or creating another chat needs applicable scope.

The helper never executes target code, clones/moves repositories, writes target
files, installs models/providers, or establishes live model/host behavior. The
agent owns authorized Git operations and project setup separately. Existing target
AGENTS.md, CLAUDE.md, Cursor rules and skills remain upstream-owned; Orbyn's own
explicit duplicate-installation retirement is not a generic deletion policy.

During work, use the [action scope method](../skills/orbyn-setup/references/action-scope.md)
to select the exact target/worktree before retrieving code or explicitly authorized
memory. Look up applicable instructions separately from code filters, and refresh
the affected guidance when paths, rules or available context change. Task-local
conversation context is sufficient; no additional registry, daemon, index,
mandatory hook or per-target installation is required.

The [action-level coverage research proposal](work/action-level-instruction-coverage-research.md)
separately proposes request-linkage and execution-coverage experiments. The current
procedural guidance does not implement its harness or prove that file reads reached
an originating model request or were enforced during execution.

## Reading groups

These groups help select relevant methods from the full canonical source. All
34 skills remain available at the outer workspace; groups do not install files
or modify host configuration. The default core has 14 methods.

| Group | Purpose | Skills |
| --- | --- | --- |
| `core` | Everyday investigation, design, implementation and review | 14 |
| `web` | Web UI, content and project-aware JavaScript/TypeScript guidance | 4 |
| `data` | API effects, stored-data compatibility and CI | 6 |
| `mobile` | Client contracts, native-aware UI and product language | 4 |
| `creator` | Social writing, previews and prose refinement | 3 |
| `maintainer` | Skill authoring, project setup and contribution automation | 5 |
| `rea` | Optional artifact investigation and REA maintenance | 5 |
| `security` | Explicit portable source audit, existing findings and CI trust boundaries; never starts a scan on install | 4 |
| `languages` | Language-aware implementation with 13 local guides, including TypeScript | 2 |
| `architecture` | Evidence-led stack selection and interface design, without automatic implementation | 5 |

## Offline and updates

Keep the full clone with local methods, examples, helpers and notices. Python
3.11+ and Git are required for library checks, while product tools depend on the
target. Read [offline limits](../skills/orbyn-setup/references/offline.md).

Update this one library checkout to a reviewed commit after preserving its dirty
work and coordinating active users. Target repositories need no skill pin updates.
For repeatable trials, record the actual library and target revisions, dirty state,
host settings and fixture protocol. Never call pending PR content released main.

For internal library maintenance, run:

```sh
python3 scripts/sync-agent-skills.py --write
python3 scripts/library_manifest.py --write
python3 scripts/check-library.py
python3 -m unittest discover -s tests -v
git diff --check
```

These generators maintain only library-owned discovery and integrity metadata.
Old `scripts/install.py` and `scripts/sync-public-skills.py` commands were removed;
use the nested procedure rather than recreating an installation in the target.
