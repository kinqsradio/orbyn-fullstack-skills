# Installation and project context

The primary flow is [clone, then ask the agent to set up the target project](../README.md).
The commands below are the agent/CI execution reference, not required human steps.
Keep a clone of the complete library at a stable path. Python 3.11+ is needed
for its helpers. From the library clone:

```sh
python3 scripts/install.py --project /path/to/project --host both
python3 scripts/install.py --list-presets
python3 scripts/install.py --project /path/to/project --preset core --preset creator --dry-run
python3 scripts/install.py --project /path/to/project --preset core --preset creator
python3 scripts/install.py --project /path/to/project --host codex --skill how --skill architect
python3 scripts/install.py --project /path/to/project --all
```

The installer preflights every destination before writing. Existing canonical
links are idempotent; a file or link owned by something else is refused. It does
not replace root instructions, model settings or connectors. The full clone
keeps cross-skill references, guides, resources and notices available even when
only some skills are registered for automatic discovery.

The consuming project's rules take precedence. Read its [actual stack](agents/stack.md)
and commands rather than copying the example architecture. `orbyn-*` identifies
the maintained engineering approach, not a requirement to use the Orbyn product.
Ask for a specific skill or open `SKILL.md` directly if host discovery is unavailable.

For a vendored consumer, copy the managed `skills/` tree from a reviewed library
revision, generate its local host links, and create `skills/upstream-lock.json`
with the pin command in [synchronization](synchronization.md). The consuming
project keeps its own policy/guides. Preserve license and provenance notices when
redistributing adapted material; installing a selection is not a license exemption.

Do not commit a local symlink to a machine-specific clone as a portable shared
installation. Use a pinned copy, a documented checkout location or regenerate the
links for each developer. This library's own discovery links are relative and portable.

## Presets and existing installations

The default is `core` (12 skills), including setup and skill ownership routing, instead of all 50. Existing links stay
installed: this is additive selection, not an uninstall or reset. Use `--all` to
reproduce the former default. An explicit `--skill` or `--preset` replaces the
default selection for that invocation; combine `--preset core` when you want both.
`--all` cannot be combined with either selector. Dry runs preflight conflicts
without creating directories or links.

| Preset       | Purpose                                                                   | Skills |
| ------------ | ------------------------------------------------------------------------- | ------ |
| `core`       | Investigation, planning, architecture, review, TypeScript, backend and UI | 12     |
| `web`        | Web task flow and product copy                                            | 4      |
| `data`       | API, persistence, migrations and CI                                       | 5      |
| `mobile`     | Mobile interaction and connected API work                                 | 4      |
| `creator`    | Social copy, carousels and previews                                       | 3      |
| `maintainer` | Setup, skill authoring, CI and reflection                                 | 4      |
| `rea`        | Optional artifact investigation and REA maintenance                       | 5      |

The [preset catalog](../skills/orbyn-setup/assets/presets.json) owns membership.
Selections overlap and are deduplicated. Presets do not install a framework,
provider or model configuration. This library's development checkout and Orbyn's
vendor integration retain all discovery links so maintainers can validate the
whole catalog; a fresh external installation uses the smaller default. To remove
a selection, explicitly review and remove its owned discovery links. The installer
does not infer removal intent from a smaller preset.

## Customize the consuming project

From the library checkout, create an optional map of existing project guides:

```sh
python3 skills/orbyn-setup/scripts/project_context.py init --project /path/to/project
python3 skills/orbyn-setup/scripts/project_context.py check --project /path/to/project
```

Review `.agents/orbyn-context.json` in that project and fill missing owner paths.
Existing valid maps are preserved. It stores relative pointers, not guide contents,
commands, credentials or a personal voice profile. Root instructions and user
scope retain precedence. The [context guide](../skills/orbyn-setup/references/project-context.md)
describes the contract; this file is excluded from public skill synchronization.


## Existing company projects and local skills

Keep existing docs, instructions, model settings and unrelated skills in place.
Use the [ownership/migration guide](../skills/orbyn-setup/references/project-skills.md)
to classify existing skills before relocating anything. Company skills live at
`project-skills/<company-or-repo>/<namespaced-skill>/`; both hosts discover them,
while public skill sync excludes them. A fresh install never guesses ownership
or silently removes conflicting content.

```sh
python3 scripts/install.py --project /path/to/company-repo --project-skills --dry-run
python3 scripts/install.py --project /path/to/company-repo --project-skills
```

For explicitly identified company skills currently stored in host folders:

```sh
python3 scripts/install.py --project /path/to/company-repo --namespace acme --migrate-skill release --dry-run
python3 scripts/install.py --project /path/to/company-repo --namespace acme --migrate-skill release
```

Repeat `--migrate-skill` for selected skills. Migration reconciles both hosts,
requires matching copies when both exist, names the canonical copy `acme-release`,
and preserves assets/licenses. It stages a recoverable backup with a receipt in a
private sibling directory before replacing old entries. Filesystem errors trigger
rollback of owned changes and retain the backup. Power loss or a failed recovery
still requires inspection of that receipt and originals. Review incoming skill-name
references and project instructions after migration; the helper does not rewrite
a company's docs. Re-run ordinary installation with `--project-skills` to check
idempotency; a completed migration has no old entry to migrate again.

Conflicts, unsafe links or external relative references requiring rebasing stop
before project writes. Sources inside managed `skills/` require pin/ownership
reconciliation first. External skill source directories are copied when explicitly
selected; their originals stay untouched. Unsupported layouts need an agent-led migration with reviewed
path reconciliation; no tool can infer a company's ownership or redistribution rights.

For [offline use](../skills/orbyn-setup/references/offline.md), retain the complete
local clone/vendor tree. Installation, discovery and validation do not fetch sources,
models or runtimes. A machine-specific discovery link needs the documented clone
location or local regeneration on each developer's machine.
