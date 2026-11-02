# Compare a visual reference

Use the parent [workflow](../SKILL.md) and [UI owner](../../orbyn-ui-design/SKILL.md).
Settle who owns the reference first. Exact parity applies to our own designs, or a design the
user owns or has licensed. For anyone else's product, match how it moves through
[motion-match](../../motion-match/SKILL.md) and keep our own design: never copy their code,
assets, fonts, brand, layout or copy.

Pin the supplied reference and actual candidate, content fixture, viewport, zoom,
theme and interaction state. Label a conceptual reference rather than presenting
it as existing product behavior.

Compare the changed flow at the requested widths. Inspect hierarchy, reading
order, content wrapping, focus, reachable actions, overlays and the relevant
loading/error/empty state. Preserve drafts, authority and recovery; matching a
static screenshot cannot justify removing a real interaction.

Classify differences as intended adaptation, concrete defect or unverified
surface. Correct reproduced overflow or navigation problems at their owner, then
recheck the affected state. Avoid unrelated screen sweeps and do not shrink all
text to fit one capture.

Return the reference/candidate identities, captures actually inspected, fixes and
remaining platform limits. Source or DOM inspection is not pixel inspection;
a browser result is not installed-native evidence. Follow permitted browser
access and report blocked inspection without bypassing it through another path.

For exact parity claims, freeze reference bytes, renderer/harness, data, theme,
viewport and relevant font/environment inputs before candidate changes. Keep raw
unmasked captures. Choose justified masks/tolerances before comparison and measure
both a real mismatch and nondeterministic noise control; a rewritten reference or
blanket animation/font mask cannot make the candidate pass. Inspect localized image
differences as well as aggregate metrics. Baseline corrections are separate reviewed
changes. For a Figma reference, use [design intake](../../orbyn-ui-design/references/design-intake.md).
