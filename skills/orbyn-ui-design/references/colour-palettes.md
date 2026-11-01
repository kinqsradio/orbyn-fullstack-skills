# Reference palettes and semantic colour

Use for a colour-direction request, an unbranded prototype, supplied palette
references or a colour/contrast review. Preserve the consuming product's existing
brand, tokens, user choices and platform conventions first. A small component fix
does not authorize recolouring the app. No reference palette is a universal
Orbyn default, required seven-theme system or promise of a psychological outcome.

## Separate reference facts from design decisions

The [catalogue](../assets/reference-palettes.json) transcribes seven supplied
screenshots: 41 legible #RRGGBB labels and one unknown third position in blue/ice.
Its visible source credit is **@uiuxaadi**. Post URLs and a screenshot reuse license
were not supplied; no screenshot artwork, app chrome or source layout is bundled.
Collection names are our editorial labels. Role assignments and gallery are our
original proposals, not verified names or a collaboration with that source.

Keep confirmed values and ordering unchanged. Record a missing label as unknown;
do not guess it from neighbouring colours or present sampled pixels as its exact
hex. If pixel sampling is useful for an authorized approximation, label it as a
separate sampled/estimated value with its method, never a repaired transcription.
The local helper deliberately refuses missing/ambiguous values.

Choose a reference only when it serves the product and requested direction. It is
fine to keep an existing brand or use a subset. There is no fixed colour-count or
60/30/10 allocation rule. Inventory colours do not automatically become status,
text, interactive or chart-series roles.

## Map roles and preserve meaning

Assign page and raised surfaces; primary and secondary text; action fill/label;
hover/pressed/selected states; meaningful control boundaries; focus; and status
text/indicators as needed. Check each actual foreground/background context in
both supported themes. Give added neutrals or status tokens an explicit origin
and rationale instead of silently changing the reference palette. The catalogue's
light/dark roles illustrate one possible mapping, not automatic target tokens.

The pale rose/mist reference has only one raw normal-text pair meeting 4.5:1
(#F1F7F7 against #5D6B6B, approximately 5.13:1). It can still be useful: preserve
its colour identity, use a verified pair or explicitly add an appropriate neutral.
Do not call every combination in that palette readable. Different role mappings
can be better under different product constraints.

Show error/success/selection with visible text, shape or an icon as well as
colour. For forms, keep programmatic labels/errors and focus behavior. A visible
non-colour distinction and assistive-technology semantics address different needs;
a contrast ratio or an aria-label alone does not establish both.

## Check the applicable pair, not the palette

| Context | Numeric target and separate evidence |
| --- | --- |
| Normal body, secondary, placeholder and action-label text | At least 4.5:1 against its actual background; check opacity and theme/state changes |
| Qualifying large text | At least 3:1 only after actual size/weight qualify (normally 18pt/24 CSS px, or 14pt/about 18.67 CSS px bold); generic 18px text is not automatically large |
| Meaningful UI/graphic state cue | At least 3:1 against meaningful adjacent colours when needed to identify the control, state or content; not every decorative border |
| Authored focus cue | Evaluate relevant adjacent colours, visibility, area/placement and obstruction separately; a 3:1 pair calculation alone is not full focus compliance |
| Inactive or decorative content | Identify the applicable exemption rather than claiming a text failure or whole-interface pass; retain useful legibility where practical |

Use unrounded ratios for threshold decisions: 4.499 is below 4.5 even when a
formatted label says 4.50. The small [contrast helper](../scripts/colour_contrast.py)
computes known solid sRGB pairs and a known foreground alpha over one opaque
background. It performs no installation, screenshot sampling or target writes:

```sh
python3 "$library/skills/orbyn-ui-design/scripts/colour_contrast.py" \
  '#81737A' '#FFFFFF' --kind normal
```

This example displays 4.50:1 but exits 1 (below target). Exit 0 means the named
numeric target is met; exit 2 is invalid/unsupported input. `--kind large`,
`nontext` and `focus-adjacency` select numeric targets, not automatic contextual
qualification. Use `--alpha 0.5` only when the underlying opaque background and
normal source-over composition are actually known. Preserve full ratio and scope.

Gradients, images, transparency over unknown layers, blend/filter effects and
multiple overlays need composition-aware inspection over the meaningful rendered
region. Checking gradient endpoints can miss a failing interior. Do not round,
assume an opaque ancestor, or sample one favourable point and claim the whole
region passes. Document any sampled scope and remaining unknowns. Materially
changed surfaces need fresh evidence.

## Inspect a usable preview and hand off

The [original gallery](../examples/colour-gallery/guide.md) lets a human choose
among all seven references, inspect light/dark roles and origins, try hover/focus,
local simulated form success/error and intentionally failing pair choices. It
works offline; its standards links are update pointers, not execution dependencies.
It separates raw labels, derived roles and contextual checks.
A build is not browser verification or evidence that target brand tokens changed.

Carry approved semantic roles through the existing web/desktop/mobile component
owners; preserve platform high-contrast/system-colour behavior and dynamic text.
Inspect final computed styles after shared CSS, transparency and overlays apply.
Exercise keyboard focus, error text and states at the requested widths. Browser
observations do not qualify native controls. Route actual Expo/RN/native surfaces
through the existing UI/runtime owners instead of declaring parity from this HTML.
Return the chosen rationale, values/origins, checked pairs and context, interaction
observations and unverified surfaces. Do not claim a palette is “WCAG compliant”.

## Primary standards and provenance

Reviewed 30 October 2026: W3C WCAG 2.2 Understanding
[text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
and [use of colour](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).
The local explanation/calculator is independently authored; these pointers support
its thresholds and review context, not a bundled standards manual or certification.
Existing skill lineage and MIT notices remain unchanged. Screenshot attribution
and unknowns are preserved separately in the catalogue; no graphics are copied.
