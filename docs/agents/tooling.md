# Library tools and optional upstream runtimes

The canonical library lives in `skills/`. Codex and Claude Code discovery folders
link to it. The installer manages only its explicit skill links and refuses
conflicts. It never applies model presets, registers MCP or installs a runtime.

| Tool | Purpose |
| --- | --- |
| `scripts/install.py` | Link selected skills into a consuming project |
| `scripts/sync-agent-skills.py` | Generate catalog index and library host links |
| `scripts/check-library.py` | Metadata, links, provenance and manifest validation |
| `scripts/sync-public-skills.py` | Explicit hash-pinned consumer import/export |
| `skills/social-preview/scripts/render_preview.py` | Local HTML/text social preview |

[Third-party notices](../../tools/THIRD_PARTY_NOTICES.md) and
[provenance](../../provenance.json) retain the source/license distinction. Full
third-party runtime snapshots are not bundled here. The optional REA adapters
link to their pinned upstream skills and prefer a matching consumer-local source
when present. Read the selected upstream's own contribution/setup rules only when
the requested task actually needs that runtime.

Copying a skill does not install REA, an engine or a provider. Discover available
tools, versions and authority before setup or execution. Do not silently use a
latest-package install instead of the referenced source or bypass browser/host
restrictions through another transport.

The [social research record](../../tools/research/social-content.md) documents
reviewed ideas rather than imported code. Static library validation is not runtime,
model, security or native-engine qualification.
