# React figures and accessible lifecycle

Use the consuming project's existing React build, peer versions, styles and
component ownership. The maintained `kit/react/draw.tsx`, `live.tsx` and
`kit/iso-kit.ts` are optional drawing modules; they do not install a React app.
Source-declared React 18+ is not proof every version/framework combination works.
Pin React/ReactDOM/compiler/bundler in the actual consumer or qualification lock.

## Render a useful server rest pose

Compute deterministic rest geometry/readout before effects run. Avoid random IDs,
wall-time-dependent markup or browser globals in server rendering. Hydration must
match that pose before an effect advances it. A static-markup render test does not
qualify hydration, streaming or browser lifecycle. Exercise the real SSR output,
actual hydration warnings and first meaningful readout in the browser.

The bundled draw module supplies React drawing primitives; inspect their actual
props rather than translate APIs from another kit. The live hooks own listeners,
visibility and readout anchors. Keep every figure's anchor/readout inside its own
identity. The nearest eligible readout can change when a ref or DOM node is
replaced; do not keep writing a detached or previous figure's element.

Test two figures with different states, a late readout mount, a replaced anchor,
a replaced readout, a streamed first section and StrictMode cleanup/remount.
A visual number already matching a cached value must not prevent the first write
to a newly mounted target. Repeating the same state should not create needless
mutation/announcement traffic once the actual current target is initialized.

## Visibility and meaningful updates

Observe the actual intended figure, not an unrelated wrapper. Stop settled or
offscreen animation work and resume without jumping. Dispose every owned timer,
observer and listener; generation checks prevent replaced components from applying
late callbacks. Reduced motion preserves model/input/readout and explanatory text.
Use semantic labels and a bounded live region for meaningful user decisions or
phase changes, not every rendered frame.

Verify actual SVG styling, opacity and shape coverage under light/dark and nested
themes. Typography/font and clipping can differ after hydration. Native input,
server markup, browser pixels, mutation counts and accessibility state are separate
checks; snapshots or jsdom alone cannot prove browser geometry or screen-reader
behavior. Record unrun framework, OS and assistive-technology cells explicitly.
