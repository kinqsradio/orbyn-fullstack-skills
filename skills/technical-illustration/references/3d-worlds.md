# 3D worlds in code

Build worlds in a WebGL2 fragment shader or your own mesh code, with no 3D library or
imported model. This covers scenes and films. For a mechanical part that turns to explain
how it works, use the [beta 3D path](3d.md). [The worked film](../examples/code-only-film/)
shows terrain, a walking figure and a beacon together.

## Pick a method

| Method                      | Best for                                 | Cost                         |
| --------------------------- | ---------------------------------------- | ---------------------------- |
| Raymarched signed distances | Terrain, rocks, smooth forms, characters | Heavy per pixel, simple code |
| Heightfield march           | Large landscapes                         | Cheaper than a full distance field |
| Generated mesh, own WebGL2  | Many hard objects, instancing            | More code, fast at runtime   |
| Layered 2.5D planes         | Parallax backgrounds, depth sandwiches   | Cheapest                     |

Rendered frames need no real-time speed, so one frame a second is fine for an export.
Use the method that gives the best picture, then bound the render time.

## Build the world

1. **Set the frame first.** Decide the camera, horizon and focal point before modelling.
   A beacon on the horizon gives the eye somewhere to go.
2. **Shape in layers.** Sum noise from large to small: big landforms, then ridges, then
   grit. Fold or ridge the noise for rock, and use smooth noise for dunes.
3. **Colour by data.** Tint by height, slope and noise, so cliffs differ from flat ground.
4. **Light it simply.** One sun, one sky fill and a soft shadow do most of the work. Add
   ambient occlusion from a few distance samples.
5. **Add air.** Fog colour should match the sky at the horizon. This one step does the
   most to make a world look big.
6. **Fill the space.** Scatter objects with seeded hashes, and rotate them slowly.
7. **Grade last.** Apply tone mapping, a small vignette and light grain. Never add grain
   to cover banding that should be fixed with a smoother gradient.

Keep every random value seeded and every animation a pure function of time, so any
frame can be rendered again on its own and match. That match holds on one renderer. A
different GPU, or a software renderer, can round differently, so a byte-for-byte match
across machines is not promised.

## Put a character in it

Build the body from capsule and rounded-box distances, with joints supplied as uniforms
from the [rig](character-animation.md). Query the same terrain function in the walk
cycle, so feet land on the actual ground. Keep the shader's height function and the
JavaScript one identical, because any difference shows as floating feet.
`tests/test_character_rig.py` opens
[`height-parity.html`](../examples/code-only-film/height-parity.html) in headless Chrome,
runs the shader's own height function beside the JavaScript one at 6,912 ground points
and fails on a gap over 1 cm. It covers the height function at full detail only, and it
skips where no Chrome is present, so run it after changing either copy.

Give the character a soft contact shadow, since it does more for grounding than any
detail on the body. Keep it small in frame, and let scale do the work.

## Move the camera

- Track on a smooth path, and aim at a point ahead of the subject.
- Use low angles for scale, and pass foreground rocks close to the lens for depth.
- Keep the horizon level unless a move has a reason.
- Cut on section changes, and keep each shot a few bars long.
- Fake depth of field by blurring with distance from the focus plane.

## Add post effects

Run these on the rendered picture, keep them short, and tie them to onsets.

- **Pixel stretch:** smear columns along one axis, decaying over a few frames.
- **Channel split:** offset red and blue, peak on the onset frame and gone within about
  3 frames at 30 fps, as [video styles](video-styles.md) times it.
- **Bloom:** blur bright areas and add them back.
- **Glow objects:** add a smooth falloff around bright shapes in the shader.

## Check the render

- Follow [full-screen pass orientation](fullscreen-pass-orientation.md), and verify with
  the asymmetric calibration card before a long render.
- Review a short sample before a long one, including the busiest shot.
- Look for banding in the sky, shimmering noise in the distance and floating feet.
  Shimmer means detail is finer than a pixel, so fade high octaves with distance.
- Record which GPU ran it. A software renderer may differ, so treat it as a separate run.
- Run `flash-check.py`, because stretched and bloomed hits can flash.
