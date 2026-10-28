# Print from the live model

Use the same authored model, build and meaningful poses as the live figure. Choose
paper, formats, named views, parts, explanatory steps, fonts and vector/raster
boundaries before export. The optional `scripts/print.mjs` consumes an explicit
trusted sheet module; that module is executable input, not inert data.
The bundled [sample sheet schema](upstream/anatomy/scripts/print-sheet.test.mjs)
shows the actual views/main/parts/steps fields; read the selected live model’s
public controls rather than invent a state-setting function.

## Capture actual selected views

Build the exact page first. Each named view supplies actions and resets around a
selected pose. The maintained capture assigns unique per-view and per-layer SVG
namespaces; identical original clip/gradient IDs from different poses must not
collide in one sheet. Preserve href/url references when remapping. Verify with two
views that use the same old IDs for different clip/gradient definitions.

A required focus/part selector matching nothing is an error, not a warning to
ignore. Preserve actual boxes/anchors and selected state. Do not copy one rest
screenshot into every pose. Record fonts/style and text ownership; missing fonts,
substituted glyphs, clipped content and stale crops are visible artifact defects.

## Vector and raster truth

The bundled print-sheet helpers support poster/drawing/detailed layouts and A4 or
letter paper. Inspect the exact sheet schema/API before constructing it. SVG
remains vector where supported; WebGL/canvas effects may need explicit raster
captures with matching model pose. Label those layers as raster rather than call
the whole sheet vector. Preserve permitted font inputs and useful document text.

The PDF process must have a bounded deadline and checked status/error. Generate to
an owned staged path first; verify nonempty output and expected page count before
replacing an existing PDF. Retain a recoverable previous output and failed attempt.
A stale existing PDF or a process killed after writing partial bytes is not success.
Optional PNG generation must pass independently before the replacement transaction.

## Inspect every configured page

Run the existing permitted PDF renderer/inspector (for example Poppler) and record
its version. Render every page of every selected format, including second and later
pages. Inspect captions, IDs, focus links, crops, margins, font fallback and vector/
raster fidelity against the live poses. Validate actual PDF page count with the
PDF tool; a byte-pattern estimate is not a substitute for inspection. A first-page
thumbnail cannot qualify a detailed multi-page format. Return the live artifact,
PDF and per-page evidence with exact model/build hashes and unrun output cells.
