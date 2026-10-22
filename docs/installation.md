# Installation and project context

Keep a clone of the complete library at a stable path. Python 3.11+ is needed
for its helpers. From the library clone:

```sh
python3 scripts/install.py --project /path/to/project --host both
python3 scripts/install.py --project /path/to/project --host codex --skill how --skill architect
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
