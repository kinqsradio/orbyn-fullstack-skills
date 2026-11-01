# Animate an image

When a video is built from an image, the character inside it must move: hair, blinks,
breathing, the head and the hands. A pan, zoom, glow or particle layer over a still does
not count as animating it, however good it looks. Our own code does the work, under
the [code-only rule](code-only.md).

This applies once an image is in the job. A cover sitting beside a track stays out of
it unless the user asks for that image.

The kit is [`examples/image-puppet/`](../examples/image-puppet/): `mask.mjs` cuts the
picture apart, and `puppet.mjs` bends a mesh over the character. Bending keeps the
image's own pixels, so the style stays exact. The small painted states below are the
only new pixels.

## Method

1. **Read the image.** List what can move, and what would look wrong if it did: long
   hair and sleeves move well; a hand gripping something needs care.
2. **Separate the layers.** Keep the image in the film's folder, set `PICTURE` in
   `film.mjs`, and allow that one file: `check-code-only.py film --allow picture.png`.
   Draw the character's outline as a polygon in `regions.mjs`, staying just outside the
   hair, as in the demo's `mask`. `mask.mjs` paints it with canvas in the page, feathers
   it and fills the plate behind it. Look at the plate: moving hair uncovers whatever is
   behind it, so a poor fill shows at once. A complex edge needs more polygon points.
   [Still to layers](still-to-layers.md) gives a finer cut, but it needs OpenCV, so use
   it only when the user approves it for the job.
3. **Mark the regions.** Draw a polygon for each moving part. Build the rig from the
   table below, starting with hair, blink and breathing.
4. **Render a short sample,** then step through a complete cycle before going further.
5. **Add camera and effects last.** They support the character's motion and never
   replace it.

Every region needs a unique `id`, a `kind` and a `polygon`. `validateRegions` throws if a
required setting below is missing. Distances are fractions of the image; `amp` on `sway`
is in radians.

| Part      | Kind     | Required, with a starting value                                     | Optional                  | Notes                                       |
| --------- | -------- | ------------------------------------------------------------------- | ------------------------- | ------------------------------------------- |
| Hair      | `hair`   | `root` at the scalp, `tip` at the end, `amp` .008 to .042, `period` 2.3 to 4.6 s | `lag`, `phase`, `feather` | Give each lock its own period and phase     |
| Breathing | `breath` | `peakY` on the chest line that rises most, `amp` .004 to .012, `period` 3 to 5 s | `reach`, `phase`, `feather` | Motion fades to nothing `reach` from `peakY` |
| Head      | `sway`   | `pivot` at the neck, `amp` .01 to .03, `period` 5 to 8 s             | `phase`, `feather`        | Slowest motion on the body                  |
| Hand      | `sway`   | `pivot` at the wrist or elbow, `amp` .02 to .06, `period` 2 to 4 s   | `phase`, `feather`        | Move it on a phrase or a beat               |
| Eyes      | `blink`  | `lineY` at the lower lash line, one region for each eye              | `seed`, `feather`         | Same seed for both, plus a drawn closed eye |
| Mouth     | `mouth`  | `lineY` at the lip line, `open(time)` returning 0 to 1               | `height` .005 to .012, `feather` | Open just before the sound, plus a drawn open mouth |
| Clothing  | `hair`   | `root` at the seam, `tip` at the hem, `amp`, `period`                | `lag`, `phase`, `feather` | Ribbons and hems behave like hair           |

A warp moves pixels but can't draw a closed lid or the inside of a mouth. Paint those
states in code, matched to the image's colours and registered to the same place, and
bend them with the same mesh. `drawnState` says which to show: the warp moves the lid
part of the way, then the drawing takes over and the warp lets go. These small painted
states are the one thing added to the picture. Redraw them in `paintPicture` for each
real face.

Keep the eye region tight. Everything inside it moves with the lid, so fringe or blush
caught in the region gets dragged into spikes and smears. In a real image, cut hair that
crosses an eye into its own layer above the face. Long hair needs the same care, because
a mesh bends everything under a polygon. A lock over the shoulders drags the jacket with
it. Split the character into layers before you rig: back hair, body and face, then the
fringe and front locks. Each layer bends under its own regions only, and the head region
turns all of them together. The demo's `layers` list shows this.

Start small, then raise amplitude until it reads at phone size. Give everything a
different period, because shared timing makes the whole figure pulse as one block.

## Tie it to the music

Keep the idle running all the time, and add accents on top. Sustained energy can widen
the hair's sway and deepen breathing. Pick one onset type for one accent, such as a head
bob or a hand snap on the snare. For a hard style, cut between two held poses on the beat
as [video styles](video-styles.md) describes.

## What a warp cannot do

Bending moves existing pixels, so it cannot show what the image never drew: the far side
of a turned head, or fingers behind a closed hand. For a pose change that big, build two
registered versions of that part and snap between them on a beat, or build the character
in code under [character animation](character-animation.md). Say so before starting.

## Check it

- `invertedTriangles` returns 0 on every frame at the delivery rate, and at fine steps
  through each blink, so the mesh never folds. Step through every frame, because a
  blink's worst moment lasts under a frame.
- The frame stays covered. `deform` fades motion toward a frame edge over its last 6%,
  so the mesh's border stays on the border and no backdrop shows there.
- The background stays still where the character doesn't touch it.
- Nothing is sliced at a region edge. Raise `feather` if a seam shows. Keep it about 1.5
  times the region's peak displacement, because a smooth fade is steepest at 1.5 over
  its width and points overtake each other past that. Where regions overlap their motion
  adds, so use the sum: the demo's hair locks set their own wider feather.
- A blink looks natural at full size, with no smeared iris, and the drawn closed eye
  matches the skin around it. Step through the frames where the drawing takes over.
- Step through a complete hair and breathing cycle. Keep the character's head and
  hands attached.
- A viewer would say the character moved, without seeing the camera at all. If the
  camera were locked off, the shot should still be alive.
