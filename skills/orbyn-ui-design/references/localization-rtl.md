# Localization, direction and semantic continuity

Use for translated or bidirectional interfaces and live locale changes. Keep the
consumer's localization APIs, source copy, glossary and review ownership. Language
and writing direction are independent inputs; RTL English is a useful control.

## Preserve meaning and order

Keep semantic DOM and keyboard focus order aligned with the task. Use logical CSS
properties for reading flow. Keep physical pointer coordinates, native controls,
canvas axes and hit-testing explicit: translating layout does not automatically
mirror these. Mirror icons that indicate reading/navigation direction when their
meaning requires it; preserve diagrams, media controls, brand marks and symbols
whose meaning would change under mirroring. Test submenu anchors and actual hit
zones, not only a screenshot of a flipped row.

Isolate embedded code, IDs, paths, URLs and numbers using the consumer's bidi-aware
markup (for example a deliberately directed `bdi`). Preserve the actual copyable
value; decorative text ordering must not corrupt a path or identifier. Exercise
mixed Arabic/Hebrew and Latin strings with punctuation and both outer directions.
Native terminology review remains necessary where not available.

RTL scroll values differ by browser; choose a normalized logical start/end helper
from the consumer's supported renderer contract rather than assume scrollLeft is
always positive. Test overflow, both endpoints, keyboard movement and nested
scrollers on the actual browser; source inspection is not scroll qualification.

## Translate whole contracts

Use full phrases and the owning plural/interpolation/fallback APIs. Do not assemble
sentences from English fragments. Preserve placeholder names, MDX/code syntax,
identifiers and established product names; translate authored explanatory copy,
not executable artifacts. Check missing keys/fallback behavior, zero/one/many
counts, interpolated mixed-direction names and live locale switches. Record a
terminology uncertainty instead of asserting native-language fluency from an
English fixture. Avoid universal English-only or source-project naming policies.

Native asynchronous labels (menus, dialogs, window controls and notifications)
need their actual consuming surface. A web view translation or a stale cached menu
is not proof that a native label updated. Record event/locale ownership across the
boundary; do not require a full application restart to hide stale reactivity.

## Keep interaction through state changes

Distinguish first load from refetch and preserve relevant focus, selection and
scroll when content identity stays the same. If identity changes, choose the
meaningful focus target and announce it once. Reduced motion must retain content,
input and the explanatory state; do not remove the only way to understand a step.
Announce user choices and meaningful phase changes rather than animation frames.

Use semantic theme and font roles; test nested theme/portal inheritance, clipping,
fallback glyphs and transition geometry. Narrowing a Suspense boundary changes
which region can blank; it does not prevent suspension. Verify the consumer's
actual reactive behavior before prescribing a framework API or token fallback.

## Verify a compact matrix

Freeze authored input and expected copy/focus/hit/scroll behavior, then run LTR and
RTL independently of language, a long/mixed string, zero/one/many plural values,
a missing key, live locale change, refetch and reduced motion. Drive keyboard and
pointer actions in the actual renderer and inspect resulting state. Include a
negative control with damaged interpolation, a wrongly mirrored directional icon
or incorrect RTL scroll endpoint. State which OS/native/locale review cells are
unrun; a synthetic browser sample does not qualify every script or native surface.
