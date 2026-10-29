# Behavioral verification adaptation record

Reviewed 26 October 2026. Source: [Lauren Tan’s pstack](https://github.com/cursor/plugins/blob/99b609a72323b70204eab407c622f436e858e112/pstack/),
revision `99b609a72323b70204eab407c622f436e858e112`, MIT. The complete
[notice](verification-LICENSE.txt) is preserved unchanged.

| Reviewed path | SHA-256 |
| --- | --- |
| `LICENSE` | `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e` |
| `skills/statechart/SKILL.md` | `b1c544782b1527ba09e63311e4faa4c277c86aa33b0506590f8082b7b4bea505` |
| `skills/create-formal-verification-skill/SKILL.md` | `5e489d938620883502c27c9c2f32143ae7aa8c0543088dad996b2c815d2acc52` |
| `skills/maintain-formal-verification-skill/SKILL.md` | `0c96f54293542d3818b68754562b338073958781a9684454611dca37592e2d2c` |

Selected adaptation: [formal-verification.md](formal-verification.md), [verification-drift.md](verification-drift.md)

Orbyn preserves code/model correspondence, falsification, bounded claims and
verification maintenance. We add existing-owner routing, proportional prototype
rigor, target-owned paths, dirty-source identity and explicit artifact lifecycle.
At this historical review we did not import upstream scripts, automatic dependency installation, model
selection, host-specific paths or recursive delegation. Raw source stays in
ignored `orbyn-references/`; this method works without that folder.

Pele is an optional external renderer, reviewed at
[`4eff76f98c73b6817800a05773517f35832e4e92`](https://github.com/obsidianmd/pele/tree/4eff76f98c73b6817800a05773517f35832e4e92).
Its package metadata identifies version 1.10.0; no Pele code or assets are bundled.
An existing dependency has its own lock/license owner. The adapter is Orbyn code
and imports only an explicitly selected trusted installed entrypoint. Rendering
is separate from model checking.

## Review of compiler-era guidance, 27 October 2026

Reviewed [pstack at `519d36aa98955bf680db01bcde5fdfba686dc901`](https://github.com/cursor/plugins/tree/519d36aa98955bf680db01bcde5fdfba686dc901/pstack),
plugin 0.15.34, MIT, against the earlier review above. This is a new review,
not an advance of the historical import or adaptation revision.

| Reviewed path at this revision | SHA-256 |
| --- | --- |
| `LICENSE` | `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e` |
| `skills/statechart/SKILL.md` | `010b7b4532406739b1c3a426d1a45f02bb618a42561fc96b3976e064a7f8384d` |
| `skills/create-formal-verification-skill/SKILL.md` | `30ef0ac27612ecd16fdc081112113221d673053cef3f8603db11932193861211` |
| `skills/maintain-formal-verification-skill/SKILL.md` | `0c96f54293542d3818b68754562b338073958781a9684454611dca37592e2d2c` |

The independently authored worked examples clarify lossy projections, qualified
action identity, per-property status, chart omissions and evidence boundaries.
They are illustrative, not captured checker output. Existing source lineage and
notices remain intact. No compiler source, runtime installation or default tool
selection is incorporated; the methods remain usable offline without research
snapshots. Compiler execution qualification is separate from written guidance
and does not establish live agent or consumer implementation performance.

## Optional compiler incorporation, 30 October 2026

Pinned source: [cursor/plugins at 1ba91fc25c0977741dd0e267849e6234b037ed0a](https://github.com/cursor/plugins/tree/1ba91fc25c0977741dd0e267849e6234b037ed0a/pstack/skills/statechart),
pstack 0.15.36. The three reviewed skill subtrees are unchanged from the prior
519d36aa review; this does not refresh old environment qualification. Historical
import/review pins above remain separate.

Architect now deliberately redistributes the unmodified 26-file TypeScript
runtime closure with the original MIT notice in its
[offline snapshot](../../architect/references/upstream/pstack-statechart/snapshot.json).
The [optional adapter](../../architect/references/statechart-compiler.md), local
ESM boundary, conservative visibility guard and synthetic leased-job sample are
Orbyn-authored. No upstream active SKILL.md, bootstrap script, Java/TLC binary,
renderer or complete test corpus is bundled. Checksums/source paths identify
every imported file; missing external tools remain explicit prerequisites.

Current qualification and failed attempts are reported separately in the
`docs/work/statechart-compiler-verification.md` maintainer record (optional
library metadata, not an offline method dependency).
Model, projection, bounded source correspondence and public-method replay are
separate results; optional Linux/Windows/native-host and arbitrary-code claims
are not implied.
