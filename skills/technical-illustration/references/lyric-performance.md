# Compose lyric typography with artwork performance

Use for a music-led artwork visualizer with individually timed words or visible
character movement. Ordinary line captions can keep the simpler
[lyric-video path](video-scenarios.md#lyric-video). Reuse the existing
[motion tools](../../orbyn-ui-design/examples/spatial-review/motion/README.md) and
[music timing](music-timing.md) before writing another renderer or alignment tool.
This method adds no bundled character rig or animation provider.

## Make the brief visible in a short sample

Separate four decisions: character/part performance, camera framing, typography,
and audio reaction. State which parts move and how visibly, the focal crop, whether
words have individual arrivals and size hierarchy, and which accents follow audio.
Infer these from the brief and refinements; ask only about material unknowns.

Use the existing busiest-section preview before the expensive full render. Include
dense words, a strong accent, a full blink if used, and representative part motion.
Inspect the actual encoded sample with sound, at delivery size and a small viewing
size. Resolve an observed mismatch in the source, then repeat the bounded sample.
This is an execution checkpoint, not a new requirement to obtain permission when
the user has already authorized the work. Full songs retain the existing
[streaming contract](../../orbyn-ui-design/examples/spatial-review/motion-films.md#stream-a-full-length-film).

Worked failure: a request for moving hair, a swaying hand and large/small arriving
words receives a zooming portrait with one caption line. The four decisions expose
the missing part motion and word composition in seconds, before rendering the song.
A calm background with ordinary captions is a legitimate different brief.

## Preserve the drawing while moving it

Choose the smallest viable local method: camera/layer motion, masked deformation,
named parts with pivots, or registered replacement drawings. Describe local 2D
puppeting honestly. A moving still alone does not supply character acting; a small
deformation is not a generated pose or an editable 3D rig. Establish missing tools
only for the performance actually requested; limited local motion may be sufficient.

For blinks, compare open, intermediate, closed and reopened states against the
source face. If using replacement artwork, register it to stable facial landmarks,
match colour and crop, and composite only the intended region. Check that the
surrounding face holds still and that eyes close cleanly. Independent pupil warps
can break gaze and eyelid anatomy; omit them unless the complete cycle survives
close-up inspection. Inspect both source frames and the encoded cycle for sliding
patches, exposed seams and residual iris. Registration scores alone cannot accept
the drawing. This is conditional asset QA, not a requirement to generate eye assets.

## Separate movement pace from vocal timing

When a preview feels too fast, adjust body/hand cycle lengths, displacement,
camera easing and word entrance duration while preserving accepted word arrivals.
Phrase-scale sway and delayed hair/cloth follow-through can provide slower motion
under faster accents. Use a smoothed energy envelope for sustained movement;
reserve onsets for selected accents rather than twitching every joint on each kick.

Sample pulse attack and release continuously. Overlapping decays or a continuous
envelope avoid dropping an unfinished pulse when the next onset arrives. Inspect
closely spaced onsets and section joins. Tempo, amplitude, frame rate and the number
of effects remain choices for this brief; more frames or a new encoder cannot
establish that the movement feels right.

## Check words through the actual renderer

Keep supplied text authoritative and generated timings editable. Compare the
ordered words and counts, inspect missing/collapsed timings and preceding-silence
errors, and review audible arrivals in the short sample. A complete word count
does not prove every timestamp correct. Preserve unresolved estimates as such.

Compose phrases with readable hierarchy and per-word timing when requested.
For synthetic text such as “Lanterns drift softly”, emphasize “Lanterns”, keep the
connecting words smaller and preserve their separate audible arrivals. Choose
effects to serve the phrase rather than requiring a fixed effect count. Keep the
caption track readable independently of the decorative word animation.

Measure and probe with the actual rendering backend and loaded fonts. Font/em
metrics from one library can disagree with another rasterizer, including libass.
Render representative large/small words, outlines and entrance extremes, then
inspect their raster bounds, overlap, safe areas and contrast. A layout manifest
cannot establish that the encoded glyphs match it. Finish with the existing
[encoded delivery checks](motion-sequences.md#persist-and-qualify-the-actual-delivery)
and report viewing/listening coverage separately from mechanical checks.
