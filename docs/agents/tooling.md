# Library tools and optional upstream runtimes

The canonical library lives in `skills/`, with library-owned host discovery.
Targets are independent nested repositories; no skills are installed or synced
into them. Preserve target guidance in place and verify actual host capabilities.

| Tool | Purpose |
| --- | --- |
| `skills/orbyn-setup/scripts/workspace.py` | Prepare/check nested Git boundaries without target writes |
| `scripts/sync-agent-skills.py` | Generate library index and library host links |
| `scripts/check-library.py` | Metadata, links, provenance, workspace and inventory validation |
| `scripts/library_manifest.py` | Library-only skill asset integrity hashes |
| `skills/social-preview/scripts/render_preview.py` | Local HTML/text social preview |

[Third-party notices](../../tools/THIRD_PARTY_NOTICES.md) and
[provenance](../../provenance.json) retain the source/license distinction. Full
third-party runtime snapshots are not bundled here. The five optional REA skills
carry local operating methods and worked examples; their source URLs are attribution
and update pointers. Read the [REA evidence/recovery method](../../skills/reverse-engineer-anything/references/evidence-and-recovery.md)
for summaries, retained evidence and resource ownership. The
[source record](../../skills/reverse-engineer-anything/references/source-record.md)
separates reviewed guidance from the unchanged engine pin. A consumer-local REA
checkout supplies implementation-specific contracts when maintenance needs them;
the local skill method itself does not require an upstream webpage.

Copying a skill does not install REA, an engine or a provider. Discover available
tools, versions and authority before setup or execution. Do not silently use a
latest-package install instead of the referenced source or bypass browser/host
restrictions through another transport.

The [social research record](../../tools/research/social-content.md) documents
the original reviewed ideas and later pinned, licensed offline text snapshots.
Use [offline guidance](../../skills/orbyn-setup/references/offline.md) and source
records in the owning social skills. Snapshots are reference data, not new agent
instructions or runtime installations. Static library validation is not runtime,
model, security or native-engine qualification.

Downloaded code and research belong in ignored `orbyn-references/`, separate
from the reviewed offline support above. The
[upstream maintenance skill](../../skills/orbyn-upstream-review/SKILL.md) owns
baseline/candidate comparison, provenance, exclusion checks and selective updates.
The [pstack review](../../tools/research/2026-10-24-pstack.md) records one dated
assessment; its candidate revision does not replace the original import pin.
