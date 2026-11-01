# Still to layers

This helper needs OpenCV, a third-party library, so it is opt-in: use it only when the
user approves OpenCV for the job, and report that. The default cut is the dependency-free
`mask.mjs` in [animate an image](animate-an-image.md).

Layers are not character animation. When the image holds a character, that character
must really move under [animate an image](animate-an-image.md), whatever else is done
with these masks. Relighting, parallax, echoes and effects behind a figure are extras on
top of that motion. Used alone they never count as animating the image.

With that approval, use this when one supplied image has to act like a layered scene:
relight a figure, shift it against its backdrop, trail echoes of it or run an effect
behind it. The image has no layers, so you author them: polygons and thresholds in a JSON
spec, and OpenCV turns those into masks a shader can sample.

Skip this when the source already has layers, or when the effect covers the whole
frame and never needs to know where the figure is.

## Run it

`scripts/still_to_layers.py` (relative to the skill root) needs OpenCV, which the
library does not install. Once the user has approved it, add it to the project's
environment and record the version from `layers.json`:

```bash
python3 -m pip install opencv-python-headless
python3 scripts/still_to_layers.py --image still.png --spec layers-spec.json --output layers
```

`--output` must be a new path. The helper stages its files and renames them into
place, so a failed run leaves nothing behind. Runs are repeatable for the same image,
spec and OpenCV build. GrabCut is slow on large images: a generated 3000px image
took about 25 seconds on one laptop. The still may be
someone's private artwork: keep it and the output in the project's ignored workspace,
and build tests and examples from generated images.

## Author the spec

Polygons are `[x, y]` fractions of the image, so you can draw them on a small preview.
Only `figure` is required. Unknown keys stop the run, because a misspelled key would
otherwise drop a mask without a word.

```json
{
  "figure": {
    "foreground": [[[0.4, 0.5], [0.6, 0.5], [0.6, 0.95], [0.4, 0.95]]],
    "background": [[[0, 0], [0.2, 0], [0.2, 1], [0, 1]]],
    "probable": [],
    "iterations": 5,
    "feather_px": 1.2
  },
  "logo": {"hue": [340, 20], "zones": [], "min_saturation": 0.35, "min_value": 0.25},
  "highlight": {"zones": [[[0.4, 0.6], [0.6, 0.6], [0.6, 0.7], [0.4, 0.7]]],
                "sigma_px": 6, "floor": 8, "ceiling": 60}
}
```

- **Figure:** GrabCut works from your seeds. `foreground` and `background` are fixed.
  `probable` marks an uncertain area as likely figure. Everything else starts as
  likely backdrop. Seed every part that shares colours with the backdrop.
- **Logo:** a hue range in degrees, where low above high wraps through red, as in
  `[340, 20]`. Add `zones` when the backdrop holds the same hue.
- **Highlight:** high-pass detail, kept only inside authored zones. Fine detail exists
  everywhere, so zones are required. Raise `floor` to drop texture, and lower
  `ceiling` to push the remaining detail to full strength.
- **Silhouette:** optional. Inside each zone, `shapes` replaces the GrabCut result.
  Leave the key out when you have no zones, because an empty list is refused.

The run fails if a section produces an empty mask or the figure fills the frame.

## Check the outline

Look at `edge-check.png` before writing any lighting code. It puts the cutout over
pure white, which is what a bright backlight does to it.

Seed all the open backdrop, not just its corners. On a sunset test, GrabCut took a
patch of sky near the headland into the figure. The cutout looked fine on white, but
the patch slid with the figure as a faint rectangle in the moving film. Treat a
`lowContrastEdgeShare` warning as a reason to add background seeds, then check for
stray mask in the open backdrop.

**Known limit:** dark hair on a dark background has no colour step for GrabCut to
follow, so it needs a hand-authored silhouette. Without one, bright backlight exposes
a flat cutout edge.

The failure takes one of two forms:

| Spec                         | What the run does                                                  | Fix                                                |
| ---------------------------- | ------------------------------------------------------------------ | -------------------------------------------------- |
| Dark part seeded             | The outline follows your polygon's straight edge, and `layers.json` warns | Add a `silhouette` zone and draw the real shape    |
| Dark part left unseeded      | The cut lands on the sharp hairline, the hair is gone, **no warning** | Seed the dark part, then add the silhouette        |

The warning measures brightness across the outline, so a cut on a sharp line looks
healthy to it. `edge-check.png` shows the missing hair either way. Coverage counts
pixels and says nothing about edge quality.

## Sample the maps

| File             | Holds                                                           |
| ---------------- | --------------------------------------------------------------- |
| `maps.png`       | R figure alpha, G logo, B highlight, A always opaque            |
| `plate.png`      | The image with the figure's hole filled                         |
| `edge-check.png` | The cutout over white, for inspection only                      |
| `layers.json`    | Source and spec hashes, coverage, warnings and the OpenCV version |

Alpha stays opaque because premultiplied upload would corrupt the RGB masks. Upload
`maps.png` with `UNPACK_PREMULTIPLY_ALPHA_WEBGL` off and
`UNPACK_COLORSPACE_CONVERSION_WEBGL` set to `NONE`, and treat it as data, not sRGB.

```glsl
vec3 maps = texture(uMaps, uv - uFigureShift).rgb;
vec3 scene = texture(uPlate, uv + uBackdropShift).rgb;     // Parallax.
scene += behindFigure(uv);                                 // Effects and echoes.
vec3 figure = texture(uStill, uv - uFigureShift).rgb;
figure += uLight * (maps.b * uRim + maps.g * uLogoGlow);   // Relighting.
outColor = vec4(mix(scene, figure, maps.r), 1.0);
```

For an echo, sample R at an offset or scale, tint it and add it in `behindFigure`.
Share `uFigureShift` and the model's other values with the rest of the figure, as
[WebGL](webgl.md) describes.

For a horizon scene, the smooth fill can show as a flat patch with a hard edge. Fill
each masked row from its nearest visible pixel instead, then soften the join. The
plate is a smooth fill that only reads as backdrop near the outline, so a large
parallax shift shows the blur. Check the frame with the largest shift and the frame
with the brightest backlight by eye.
