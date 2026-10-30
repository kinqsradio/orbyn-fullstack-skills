# Discover project context in place

Resolve the target Git root under the [nested workspace contract](repository-workspaces.md).
Read its instructions, manifests, contribution guide and relevant architecture,
design, brand, verification and operations guides. Follow existing owner pointers;
load only what the current task needs. Shared examples never mandate Orbyn's stack.

If the target already owns `.agents/orbyn-context.json`, its existing document and
owner pointers can be checked read-only:

```sh
python3 skills/orbyn-setup/scripts/project_context.py check --project repo/widget
```

The optional schema has `schema_version: 1`, a nonblank `project_name`, and
`documents` / `owners` maps of existing project-relative paths. Documents point to
files and owners to files/directories; paths cannot escape the target. Commands
and credentials are rejected. The map grants no authority. Setup no longer
creates a map, installs discovery links or changes any target configuration.
When absent, discover the actual source and guides normally; no placeholder file
or manual form is required.

Keep project preferences with the target's existing owner. The library owns the
method and public synthetic examples; it never absorbs target context into its
catalog or public content merely because the agent can read it.

For a requested durable UI review, discover the actual design document/package
owner and exact filename case here; use `design.md` only when none exists.
The UI owner's [review-package method](../../orbyn-ui-design/references/review-packages.md)
keeps prototype/settings/feedback with that target. This adds no context schema,
setup installation or mandatory map; private review data is not library content.
