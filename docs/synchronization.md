# One skill source, independent target repositories

The outer `orbyn-fullstack-skills` checkout is the sole shared skill source.
Independent target repositories and sibling worktrees live in its ignored `repo/`
workspace. Read [setup](installation.md) and the
[workspace contract](../skills/orbyn-setup/references/repository-workspaces.md).

Shared methods, routing, examples and source notices change here. Target source,
AGENTS.md, skills, contribution rules, private configuration and evidence remain
with that target. Nothing is copied, installed, exported or pinned into it. No
consumer sync PR or skill-upstream CI is needed after a library update. Existing
upstream instructions stay in place; target guidance and shared methods are read
together with the actual host/user precedence, not by assumed nesting behavior.

The library's `distribution/manifest.json` is a local integrity inventory of
canonical skill assets, maintained by `scripts/library_manifest.py`. It is not a
consumer lock, install package or synchronization contract. Focused synthetic tests
can copy assets into temporary fixtures to verify dependency closure; that does
not support installing them into projects.

## Contributions and shared updates

Prepare a focused library branch/diff for a reusable improvement, separate from
any target PR. Preserve required notices and never publish project content merely
because it is visible under repo/. Publication and merge need user/project scope.
After a checked merge, coordinate updating the single library workspace without
resetting dirty work or silently switching active sessions to another candidate.
Record actual library/target commits when reproducibility matters. Offline cached
refs and unobserved host discovery stay explicit.

## Retiring the former installation

The copy/link installer, company-skill migration and pin/pull/export synchronizer
are retired. Follow the
[ownership and preservation procedure](../skills/orbyn-setup/references/repository-workspaces.md#retiring-old-installations)
for an explicitly authorized migration. Rehome project CI/runtime dependencies
before removing copied skills; retain required credits, project knowledge, local
work and active paths. Do not delete an unrelated project's own AGENTS.md or skills.
Historical evaluation reports describe the older delivery model and remain dated
evidence, not current setup directions. REA engine/runtime upgrades remain separate.
