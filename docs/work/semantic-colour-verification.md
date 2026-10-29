# Reference palettes and semantic-colour qualification

Local candidate based on `e68be8ba6fb404e97cf03edd1f1899358dd2aac5`.
The existing UI owner gains conditional colour guidance, a factual catalogue,
solid/known-alpha contrast helper and an original self-contained gallery.
No new skill, default palette, target theme adoption or global setup is introduced.

## Source facts and ownership

All seven user-supplied images were inspected. The catalogue preserves six
positions per image: 41 legible hex labels and one null at blue/ice position 3.
No value was inferred from adjacent colours or sampled pixels. Visible source
credit **@uiuxaadi** is retained; post URLs and a screenshot reuse license were not
supplied. No screenshots, app chrome, source graphics or source layout are bundled.
Collection names are editorial. The role proposals, gallery, helper and guidance
are independently authored; original skill lineage/MIT notices remain unchanged.

Added white/dark neutrals and status colours are declared separately from raw
swatches, with explicit origins visible in the role panels. Existing target
brands, shared tokens, user/system colour choices and native owners take priority.
The guide does not impose all seven palettes, a 60/30/10 ratio, psychological
outcomes or palette-wide accessibility claims.

## Deterministic evidence

- Independent transcription matches all 42 positions. Independent opaque-sRGB
  calculations match all 100 raw pairs to 1e-12. Raw normal-text pair counts by
  palette are 6/15, 7/15, 5/10, 1/15, 5/15, 5/15 and 4/15. In rose/mist only
  #F1F7F7 against #5D6B6B meets 4.5:1; using that collection does not make every
  pastel pairing readable.
- All 168 declared role-pair numeric checks across seven light/dark proposals
  meet their named target. These are contextual solid-colour proposals, not
  certification or evidence of automatic target adoption.
- The #81737A/white regression ratio is 4.499922485663913: it displays 4.50:1 but
  stays **below** the normal-text target. Black/white=21, identical colours=1,
  threshold equality, malformed/unknown inputs and known-alpha composition have
  explicit controls. Missing/blank alpha does not silently become zero in the UI.
- Normal/secondary/placeholder/action text, qualifying large text, meaningful
  non-text cues and focus adjacency are distinguished. Large-text/focus numeric
  targets do not establish actual size, area, placement or visibility. Alpha is
  supported only as normal source-over of one known foreground onto one opaque
  background; gradients, images, unknown layers, filters/blends stay unverified.

The Python helper returns 0 for the named numeric target met, 1 for below target,
2 for invalid/unsupported input. The gallery's independent JavaScript path has the
same boundary tests. Neither rounds before classification or labels a palette
“accessible”. Source-reference credit and unknowns are not replaced by role tokens.

## Rendered and interaction evidence

The final gallery is generated with:

```sh
python3 skills/orbyn-ui-design/scripts/build_colour_gallery.py \
  --out "$new_gallery_output"
```

The output must be new and its parent must exist. It contains one self-contained
HTML file and source/output receipt; no package installation, fetch, server,
provider or target write is required. Build completion is separate from rendering.

Author browser checks used installed Chrome 156.0.8078.48 through local Playwright:
all seven choices × two modes were exercised. There were 126 selected actual
computed-style pair checks, plus hover action-label and keyboard-focus checks for
each surface. Empty-title errors, focus return, aria-invalid, valid simulated
save, disabled action and keyboard palette selection were observed. Reference
selection preserves focus and changes only this local illustration. Independent
review separately checked 140 computed default role pairs across all 14 proposals,
and selected real hover states. Those are selected browser checks, not every
possible state or platform.

The selected-marker row was corrected to evaluate accent against its actual
panel surface, rather than the surrounding page. Earlier output is preserved.
The preview never implies that simulated saves are durable/backend effects.
Status labels include visible text/icons rather than relying on colour alone.

The initial phone header used too much space before the first choice. Copy and
spacing were shortened while keeping brand precedence and proposal-only scope
visible. At 320×844, the first choice now starts before y=500; root width and
scroll width both equal 320 even with raw/role/audit details expanded. Only the
audit's two-dimensional table scrolls. Author inspected desktop overview,
rose light/dark proposals and the final 320px capture; independent review retains
its own earlier wide/narrow observations. No user-study, screen-reader, forced
colours, zoom, print or installed native qualification is claimed.

Final output is `output/colour-palettes/gallery-final/index.html` in the task
worktree. It is byte-identical to browser-inspected `gallery-v4/index.html`,
verified after the final builder-origin validation. Earlier v1/v2/v3/v4 outputs,
captures and actual commands/results remain ignored; they are not public artifacts
or dependencies of the reusable gallery. Independent evidence stays separately
in the primary checkout's ignored `orbyn-references/palette-review/`.

## Integration and limits

- Full supported-Python 3.13.3 discovery: **204 tests, 195 pass and 9 skipped**, in
  21.482 seconds. The skips are existing optional Java/TLC statechart integration
  tests whose opt-in variables were not supplied; no new statechart qualification
  is claimed. All 11 new colour tests pass.
- **Five Node colour tests pass**. The gallery/calculator/cold output and prior
  output preservation are tested; unknown or undeclared role values/origins fail.
- Library/source/license/link/manifest/discovery checks and diff whitespace pass.
  All **36 canonical owners** remain; six development definitions were appended
  with all **372 previous case objects and holdouts unchanged** (378 total).
- Original gallery source contains no screenshot assets. No memory writes,
  global installation, project token changes, model defaults, Orbyn changes or
  REA engine updates are part of this task. No paid panel or live agent quality
  benchmark was run. Static definitions are not agent performance results.

Primary W3C context is retained in the offline guide as update pointers. The
computed ratios, browser observations, semantic-role choices, provenance and
whole-interface accessibility assessment are deliberately separate evidence.
Candidate delivery state is recorded separately from this qualification report.
