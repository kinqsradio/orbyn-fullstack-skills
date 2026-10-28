# Geometry, projection and independent checks

Choose one camera (`cameraOf`) and use it for SVG parts, bounds, line attachments,
shader coordinates and any hit regions. Keep world and view coordinates explicit.
A projected depth sort is not a complete solid-intersection proof. State which
objects are tested, sampled poses, clearance margins and allowed contacts.

## Match the drawing, not a stand-in

The bundled `kit/lathe.mjs`, `kit/tube.mjs` and `kit/audit.mjs` extend the core kit.
Read the actual profile, clipping, tube, transform and audit exports for the chosen
model. Preserve part/group identity and origin through transforms. A verifier must
use the actual drawn shape/attributes, including affine transforms, paths, taper,
rounded profiles and clipping. Empty clipping can make an apparently clear object
vanish; a simplified bounding proxy can miss a collision or a missing surface.

Enumerate drawn shape IDs and verification records in both directions. A coverage
heuristic can expose a missing record but cannot prove shape equivalence. Plant a
missing clipped shape, wrong attachment or profile transform and confirm the
appropriate oracle rejects it. Freeze the legitimate geometry rather than weaken
the verifier until a preferred picture passes.

## Texture and attachment

Treat meaningful line endpoints as attached to a stroke, dot, outline or occluding
fill at the actual sample. A short tick can have one rooted end; an intentionally
free/fading effect should be explicitly marked, not accidentally exempt everything.
Line width, curve sampling density, stroke joins/caps and painter order affect the
visible result. Sample arcs, Béziers and rounded rectangles at suitable density;
inspect the actual crop after a numerical line check.

Use `scripts/lines.mjs` for the maintained browser line check or the `lines` drive
action. It spawns the local maintained driver. Provide exact selected figure and
output scope, retain all failing endpoints and captured evidence, then fix source.
Check the whole action list validates before browser effects; invalid/missing
selectors or nonfinite controls must not quietly select an unrelated body element.

## Motion and evidence boundary

Test actual time schedule, reversals and transformed intermediates. A static clear
pose does not qualify the transition. Use exact sampling bounds/step and cost in
receipts. Compare pure model/audit output, actual DOM/SVG attributes and inspected
pixels as distinct evidence. A test based on the same faulty generated geometry
cannot establish correspondence without an independent control.
