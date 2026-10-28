# Conditional WebGL effects with meaningful fallback

Use WebGL only when a field/effect makes the mechanism clearer: light, water,
exhaust or another continuous phenomenon. Core parts and the explanation should
remain meaningful without it. This is not a default product background or a
mandatory shader aesthetic. Use the existing permitted browser/GPU; no unsafe
renderer, sandbox bypass or unrequested installation to obtain a pass.

## One camera and state

The maintained `kit/gl.mjs` exports glCamera, glLayer and GLSL helpers. Inspect the
actual uniforms and draw/dispose contract before use. Share projection, viewBox,
model instant and turning-group pose with SVG. Arrange back SVG, canvas and front
SVG layers deliberately; a canvas cannot depth-test against an SVG object.
Split geometry/effect layers or model explicit occluders when needed. Keep masks,
openings and parent/group identity aligned through all selected poses.

Use phase/event envelopes with continuity at boundaries: no energy before the
model event, no sudden color switch that contradicts its phase, and a truthful tail.
Bandlimit fine patterns to actual scale/DPR. Theme compositing matters: screen
blending can brighten but cannot darken; premultiplied alpha/background assumptions
must match the actual theme, including a nested theme not just the OS media query.

## Fallback and resource ownership

A missing context or shader compile/link failure retains useful geometry, input,
readout and explanatory content. Display an honest fallback state; do not turn a
failed shader into an empty figure. Test actual no-context and broken-shader paths
as well as a successful render. Announce semantic changes, not frames. Bound pixel
ratio/work and stop drawing when settled/offscreen; dispose listeners/GL resources
at the actual owning lifecycle. Reduced motion preserves the explanation and input.

## Verify the actual framebuffer

Read pixels in the same draw task when preservation is not guaranteed. A later
read of a cleared buffer can falsely show no effect. Record WebGL version, browser,
renderer/vendor, hardware or software path, viewport/DPR, model state and theme.
Use numeric pixel/mask/alpha controls and inspected images; deliberately break an
opening mask, phase boundary or shader and verify the corresponding check rejects
it. Test light/dark/nested themes and the meaningful fallback. A software renderer
is a distinct cell, never evidence of hardware parity. State measured draw cost
and finite sample bounds; source tests cannot qualify a real GPU surface.
