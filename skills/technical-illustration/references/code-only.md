# Code-only rule

Every picture and every movement in a video comes from code we write in the project.
This is the default for all motion work here. Only the user can lift it, for a named
item in a named job.

## What counts

| Allowed                                                 | Not allowed                                                                 |
| ------------------------------------------------------- | --------------------------------------------------------------------------- |
| Our own shaders, geometry, rigs, noise and motion code  | Image, video, music or voice generators and any hosted model                |
| Platform runtimes: browser, WebGL2, canvas, Node, Python standard library | 3D and animation libraries, such as three.js, or vendored copies of them |
| System fonts, or letterforms drawn in code              | Downloaded fonts, stock art, textures, HDRIs, footage and sound packs       |
| FFmpeg, and a headless browser driver such as Playwright | Downloaded rigs, models, motion capture or animation clips                  |
| Audio, lyrics and logos the user supplies for this job  | Blender, After Effects, Live2D, Spine, Unity, Unreal, Rive or Lottie sources |
| Measurements we compute from the supplied audio         | Rendering, upscaling or tracing frames through someone else's service       |
| Lyric times placed by hand on measured onsets           | Python packages in the picture or sound path, such as OpenCV, numpy or librosa |

FFmpeg and a headless browser driver are the two exceptions, because they are
non-creative infrastructure. FFmpeg decodes and encodes, and a driver such as Playwright
opens the page and carries frames to the encoder. Neither puts anything on screen or in
the soundtrack, so both stay allowed. If a tool would decide what appears on screen, it
is a creative tool and this rule covers it. When unsure, write the code.

The motion kit's optional Three.js graphics profile and Lottie input fall under this
rule, as do `still_to_layers.py` (OpenCV), `analyze-audio.py` (librosa and numpy) and any
speech model. Leave them out unless the user approves them for the job.

The [product-illustration](../../product-illustration/SKILL.md) kit is adapted MIT source
held in this library, and its host runtime is React, react-dom and lucide-react. Web
illustrations built with it are outside this video rule. A video that uses the kit needs the
user's approval for those three modules and must list them as allowances in the report, or
it replaces `Icon` and renders without them. Everything else in this rule still applies.

A [stack diagram](../../stack-diagram/SKILL.md) stays outside this rule as a document, and
its fetched logos are not supplied ones. A diagram inside a film is redrawn in the film's own
code, using only logos the user supplied.

## Treat missing things as code to write

Never answer "that needs an asset" or "that needs an animation tool". New poses, walks,
acting, faces and 3D worlds are all code problems, so build them with
[character animation](character-animation.md) and [3D worlds](3d-worlds.md).

| Need             | Write this                                                     |
| ---------------- | -------------------------------------------------------------- |
| Texture          | Layered noise and masks in a shader                            |
| Reference look   | Your own shapes, palette and timing, drawn from a written brief |
| Character        | Named joints driving primitives you draw                       |
| Motion capture   | A parametric gait, plus authored key poses                     |
| 3D model         | Signed distance functions or a generated mesh                  |
| Stock background | A procedural world                                             |

State the honest limit in terms of style and effort: a code-built character is stylised,
and more acting means more authored poses. Say that plainly, then build it.

## Music videos

Use no album artwork, and no layers cut from it, even when a cover sits beside the track.
Derive the idea from the lyrics and the measured audio, then generate every visual. A
supplied image is used only when the user explicitly asks for it. Then the character
in it must really move, so follow [animate an image](animate-an-image.md); a pan or zoom
alone never counts.

## References are for learning

Study a reference video for technique: timing, composition, shot length, how a hit
decays. Keep the lesson, as in [video styles](video-styles.md). Never download a reference
to reuse it, copy its frames or art, recreate its characters or trace its shots. A
measurement capture under [motion-match](../../motion-match/SKILL.md) is allowed: it stays in
an ignored local folder, only its written numbers carry forward, and it is never a deliverable.

## Prove it

Run the check on the film's source folder before rendering:

```sh
python3 scripts/check-code-only.py path/to/film
```

An empty folder exits 2, because nothing was checked. The check reads every file in
the folder except a top-level `.git`, follows no links, and fails on:

- Media, font, model, archive and manifest files by name, in any letter case.
- Media or binary bytes under any name: file signatures, NUL bytes anywhere, and text
  that is not valid UTF-8.
- `data:` payloads and long base64 runs in any text file, comments included.
- Lottie, glTF and Spine data in JSON text.
- Vendored libraries, by folder, by filename such as `three.module.js`, and by a
  third-party licence notice.
- Packages loaded by any written form of `import`, `require` or `importScripts`,
  including inline `<script>` and Python's `importlib`.
- Imports with a computed name, plus `eval` and `new Function`.
- URLs in code, markup, CSS, JSON, Python and plain text, by exact host. Only
  `www.w3.org`, `localhost`, `127.0.0.1` and `::1` are exempt, and any URL with a user name
  fails. URLs in code comments and Python docstrings are left alone.
- Paths that leave the folder, and every symbolic link.

The report's `limits` list what it cannot see, so a pass is not proof on its own:

- A name or URL built at run time, or an alias such as `const load = require`.
- Bytes written as number arrays, or encoded some other way.
- A library renamed with its notice removed.
- Lottie or glTF data written as a JavaScript object.
- Where drawn shapes came from, so traced art in our own code passes.

Pass `--allow relative/path` only for one file the user supplied for this job, and
`--allow-module name` only when the user approved it. A link fails even when it points
at an allowed file. List every allowance in your report. You still answer for what the
film was built from.
