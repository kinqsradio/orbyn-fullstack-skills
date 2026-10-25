# Project and company guidance stays with its owner

Shared skills live only in the outer library's `skills/`. Target-owned skills,
instructions, design/brand guides and configuration stay in their established
locations inside the independent nested target. Read them in place. Do not move,
namespace, rename, register, export or synchronize them during setup.

A project may already use `project-skills/<company>/<name>/`, `.agents/skills`,
`.claude/skills`, `.cursor/skills` or a different documented convention. Follow
its own ownership and discovery rules. No new directory convention is imposed
on an open-source contribution. Read applicable supporting resources relative to
that project's canonical skill, keeping company examples and procedures local.

For a same-name shared and target skill, distinguish their paths and contracts.
Target-specific rules specialize compatible shared methods; never choose by an
assumed host precedence or overwrite the foreign copy. Surface conflicts with
user scope or required checks before dependent effects. The workspace helper
reports common discovery-name collisions without modifying either source.

Creating or adapting a company skill is separate authorized project work, not an
installation step. Improve its existing owner and update its own callers/tests
when requested. A reusable public proposal follows the
[contribution feedback policy](../../orbyn-skill-creator/references/contribution-feedback.md)
and needs publication authority; generic-looking text does not establish rights
to redistribute company material.

For old copied Orbyn installations, use the explicit preservation and ownership
steps in the [workspace contract](repository-workspaces.md#retiring-old-installations).
Never delete foreign guidance merely to make the target resemble Orbyn's cleanup.
No target skill registration or migration helper remains supported.
