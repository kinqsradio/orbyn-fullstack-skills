# Keep full-screen passes upright

Read this when a film or figure runs an image through WebGL framebuffers, or when
`readPixels` output reaches an encoder. Three conventions disagree, and each one
can flip the picture on its own:

| Stage | Row 0 means |
|---|---|
| Decoded image or typed-array art uploaded with `texImage2D` | Top of the art, at texture `v = 0` |
| Full-screen quad `uv = position * .5 + .5` | `uv.y = 0` is the bottom of the output |
| `readPixels` from a framebuffer or canvas | Bottom row first |

Two flips cancel, so a pipeline can look right until one pass is added or removed.
A whole film can turn upside down while canvas text stays upright, because text
reached the shader through a different upload path.

## Fix it once

1. Choose one convention: framebuffer contents stay in GL order (bottom row first).
2. Correct Y-down art in exactly one place, where it enters the first pass, by
   sampling `vec2(uv.x, 1. - uv.y)`. Later pass-to-pass samples use `uv` unchanged.
3. Give every upload path, including text canvases and `UNPACK_FLIP_Y_WEBGL`, the
   same treatment. Record what each path does beside the pass list.
4. Declare the read order to the exporter with `rowOrder: 'bottom-first'`. Leave the
   flip to the exporter, and never add a compensating flip inside a shader.

## Prove it with an asymmetric card

Use a test card with four different quadrants: red top-left, green top-right, blue
bottom-left, white bottom-right. A symmetric card looks the same after a flip, so
it proves nothing.

The streaming exporter does this before it starts the encoder: it hands
`orientationChart()` from `frame-stream.mjs` to the page's `calibrate()`, reads the
result back, and stops the export unless `classifyOrientation()` returns `upright`.
It names `flipped-vertical`, `flipped-horizontal`, `rotated-180` or `unrecognized`.

Worked failure: a two-pass film samples art with `uv` in its first pass and reads
bottom-first. `calibrate()` returns blue over white, the classifier reports
`flipped-vertical`, and `receipt.json` records the failure with no `film.mp4`.
`tests/fixtures/stream-film/film.js` is the synthetic pass chain.

Route the card through every geometric pass. Skip only colour steps that move hue,
or the result reads `unrecognized`. Send it through each upload path that reaches
the screen, because a card on the art path proves nothing about canvas text. Then
open a decoded frame and read one line of text in the final file.
