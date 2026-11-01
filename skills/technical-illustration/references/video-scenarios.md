# Choose the video you are making

Each kind of video fails in its own way. Find the row that fits, then follow its
section. A job can combine sections: an anime background behind lyrics uses both.

| Request                                       | Section                                                 |
| --------------------------------------------- | ------------------------------------------------------- |
| Words on screen timed to a song               | [Lyric video](#lyric-video)                             |
| Painted or anime-style scenery                | [Anime-style background](#anime-style-background)       |
| Calm scene with no story, often looping       | [Ambient background](#ambient-background)               |
| Full animation, with or without a story       | [Full animation](#full-animation)                       |
| Promo, explainer, kinetic type, product video | [Motion graphics](#motion-graphics)                     |
| Bars, rings or shapes driven by the music     | [Audio visualizer](#audio-visualizer)                   |
| Logo reveal, intro or outro                   | [Logo and branding](logo-and-branding.md)               |
| One master for several shapes or lengths      | [Several formats](#several-formats-from-one-model)      |

Ordinary trimming or editing of existing footage goes to the project's media tools.

## Settle these first

Ask only what you cannot infer. A wrong answer here means a full re-render.

- **Sources and rights:** which audio, art, lyrics and logo are supplied, and may
  they be used this way?
- **Delivery:** platform, aspect ratio, length and whether it must loop.
- **Words:** lyrics, narration, titles or none?
- **Motion budget:** what actually moves, given the sources?

Use these defaults when the brief is silent, and say that you chose them.

| Kind                                | Frame rate | Why                                     |
| ----------------------------------- | ---------- | --------------------------------------- |
| Anime-style, full animation         | 24         | Matches held-drawing timing             |
| Lyric video, ambient, motion design | 30         | Smooth type with smaller files          |
| Visualizer, fast camera moves       | 60         | Beat response stays sharp               |

Render 1920x1080 unless told otherwise. Before a full render, review a 10-second
sample around the busiest section. Anything over 120 seconds uses
[long-form streaming](../../orbyn-ui-design/examples/spatial-review/motion-films.md#stream-a-full-length-film).

Every video finishes with `flash-check.py`, a real viewing of the file and the
[legibility check](#check-words-and-logos) when it carries words or a logo.

View frames at full size as well as on a contact sheet, and step through a whole
cycle. In a one-image test, every script passed while the haze blotched the sky, and a
mask error only showed in some frames. Crop in on horizons and any edge near a moved
layer. Keep new haze or light subtle, and judge it against the source image.

## Lyric video

The job is reading along, so type comes first and art serves it.

1. Use only the supplied lyrics. Time them with [music timing](music-timing.md), and
   never display transcribed text the user did not supply.
2. Split lines at breath and phrase ends. Keep one or two lines of about 42
   characters each.
3. Show a line slightly before it is sung, and hold it long enough to read: at least
   1 second, at about 17 characters a second.
4. Change layout by song section, not by line, so a chorus looks like a chorus.
5. Reserve a calm, darker zone for the words before designing the background.
6. Ship `captions.vtt` alongside the video. Burned-in type is not a caption track.

Watch for: a reveal so stylish the line is gone before it can be read, word pops on
every kick that turn into flashing, and bright highlights crossing behind white text.

Done when the whole song reads comfortably on a phone, and every line matches the
supplied lyrics exactly.

## Anime-style background

Aim for the look of painted scenery with a little life in it: a sky, a horizon, and
slow layered movement.

- **Rights:** work in the style, not from a specific show. Refuse to reproduce named
  characters, series stills or studio logos. Supplied art needs the user's rights.
- **Source:** with one supplied image, split it using
  [still to layers](still-to-layers.md). Without one, build it in code: gradient sky,
  two or three cloud layers, a silhouetted mid-ground and flat cel shadows.
- **Depth:** move layers at different speeds, with the farthest slowest. Keep the
  camera slow, because fast parallax exposes flat layers.
- **Life:** add one or two seeded effects, such as drifting petals, rain, light shafts
  or distant lights. Too many reads as a screensaver.
- **Timing:** hold drawn elements on twos by rounding their sample time to 12 frames a
  second, and keep the camera at the full rate. This gives the held-drawing feel.
- **Finish:** add light grain and a soft bloom on highlights, and check them against
  the [effect budgets](../../orbyn-ui-design/examples/spatial-review/motion-films.md#motion-blur-effects-and-budgets).

Watch for: a cutout edge against bright backlight, and a character who should be
moving but cannot. A still gives camera movement and atmosphere, not new poses,
talking or hair in the wind.

Done when a viewer reads it as a scene, and nothing looks sliced or swimming.

## Ambient background

Used behind streams, desktops, displays or study playlists, so it must not demand
attention. Keep motion slow, avoid bright peaks, and leave nothing that draws the eye.

For a seamless loop:

1. Pick the loop length first, such as 20 or 60 seconds.
2. Make every motion periodic. Each element completes a whole number of cycles in
   that length, and noise samples a circle in its domain so it returns to its start.
3. Let particles wrap: anything leaving one edge re-enters as the loop closes.
4. For haze or drifting noise that can't wrap, crossfade two fields: each drifts a
   little and fades to zero before it restarts, so the loop has no visible reset.
5. Render one extra frame, so frame N is the moment the loop returns to frame 0.
   Extract both, with 600 as N for 20 seconds at 30 fps, then compare them:
   ```sh
   ffmpeg -i loop.mp4 -vf "select='eq(n,0)+eq(n,600)'" -fps_mode passthrough seam-%d.png
   ffmpeg -i seam-1.png -i seam-2.png -lavfi psnr -f null -
   ```
   Above about 40 dB the frames are very close. Drop the extra frame from delivery.

Watch for: a pop at the seam, a visible jump in grain, and audio that doesn't loop at
the same length.

Done when you can watch it pass the seam three times and not find it.

## Full animation

State the limit first. Code draws what a model describes. It can animate shapes,
vector characters and rigged cutouts, but it won't turn a still into a performance.
If the request needs natural acting, lip-sync or hand-drawn character work, say so
before starting and name what can be delivered instead.

1. Write a shot list: what happens, for how long, and why.
2. Build an animatic of blocked shapes and approve its timing with the audio. Changes
   here cost minutes, and changes after rendering cost hours.
3. Rig characters as named parts with pivots, so a walk or a head turn is data. Reuse
   cycles, and offset them so two characters never move in step.
4. Add follow-through: lead with the body, and let hair, cloth and tails arrive later.
5. Cut on an action, and keep one idea on screen in each shot.

With no lyrics, the picture carries the piece, so plan a beginning, a change and an
ending. Follow the music's sections; don't react to every beat.

Watch for: everything moving at once, identical cycles, and a strong opening that
then repeats for three minutes.

Done when the story or idea is clear with the sound off.

## Motion graphics

Promos, explainers, kinetic type and product videos are about one message.

1. Write the single sentence the viewer should keep.
2. Assign one idea to each shot, and read every on-screen word aloud to time it.
3. Use a small consistent set of easings and one direction of travel.
4. Use real numbers and real screens. Label anything synthetic as a mockup.
5. Finish on one clear action, and hold the end card for at least 3 seconds.

Use the [fourteen scene primitives](../../orbyn-ui-design/examples/spatial-review/motion-films.md#fourteen-scene-primitives)
before writing a custom scene. Explainer numbers come from the same model as the
drawing, as in [craft and model](craft-and-model.md).

Watch for: unsupported claims, text that leaves too soon, and decoration between
ideas.

Done when someone who has not seen it can repeat the message after one viewing.

## Audio visualizer

Bake per-frame features with [music timing](music-timing.md) and drive shapes from
them. Map bass to size, onsets to accents and high bands to fine detail. Ease every
value on its way down, so shapes fall smoothly instead of chattering. Keep a focal
point, such as supplied cover art, and let the bars support it.

Watch for: strobing on kicks, so limit brightness jumps and run `flash-check.py`.

Done when the movement clearly follows the song on a silent viewing.

## Several formats from one model

Keep one timeline and lay out each format separately. Don't crop a wide master into a
vertical one, because the type and logo fall off.

- Define a focal point and a type zone for each aspect ratio: 16:9, 9:16, 1:1.
- Vertical platforms cover parts of the frame with their own buttons and captions.
  Check the platform's current layout before placing words near the edges.
- Cut a teaser on a section boundary, and start on the strongest moment.

Check every format separately, since a pass in one proves nothing about another.

## Check words and logos

Render a plate with the type and logo hidden, as a short film or as stills of the key
moments, then check each box as fractions of the frame:

```sh
python3 scripts/legibility-check.py plate.mp4 --box lyric:.1,.72,.8,.14@12-48
python3 scripts/legibility-check.py plate.mp4 --box logo:.84,.06,.1,.08 --min-contrast 3
```

`--box` takes `name:x,y,w,h`, with an optional `@from-to` in seconds. Exit 1 reports
the worst moment and its time. Fix that by moving the box, darkening the art under it
or adding a shadow to the type, then check again. Dimming the whole film is the last
resort. The check is a screen for sampled frames, so still read the real thing.
