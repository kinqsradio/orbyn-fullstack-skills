# Lyric video and artwork animation: production reference

Use when supplied artwork, music and lyrics become a visualizer with individually
timed words or visible character movement. Apply the sections that match the brief.
For ordinary line captions, use the simpler [lyric-video path](video-scenarios.md#lyric-video).

## Resolve the production inputs

Identify the source art, audio, authoritative lyric text, permitted use, delivery
format and existing renderer. Reuse the [motion tools](../../orbyn-ui-design/examples/spatial-review/motion/README.md)
and [music timing](music-timing.md) before writing another renderer or alignment
tool. This reference supplies production guidance, not a bundled rig or provider.

| Decision | Establish from the brief | Check in the short sample |
| --- | --- | --- |
| Character performance | Which parts move, range and pace | Hair, hand and face motion are visible at the intended crop |
| Camera | Focal point, framing and section changes | Subject remains framed and moved layers expose no holes |
| Typography | Line captions or separate word arrivals; emphasis hierarchy | Dense phrases read at delivery and small viewing sizes |
| Audio reaction | Sustained energy versus selected onset accents | Accents follow music without making every joint twitch |

Infer these choices from the brief and refinements; ask only about material
unknowns. A calm still portrait with line captions is a valid separate direction.

## Choose a method that matches the requested motion

| Method | Useful for | Boundary to describe |
| --- | --- | --- |
| Camera and layer motion | Crop changes, depth, atmosphere | A pan/zoom alone supplies no character performance |
| Masked deformation or named parts with pivots | Bounded hair, body and hand movement | Local 2D puppeting; no newly generated poses or editable 3D rig |
| Registered replacement drawings | Authored blinks or other small state changes | Quality depends on matching the source and inspecting the full cycle |
| A qualified animation path with suitable assets | New poses, lip-sync, natural acting | Establish the actual tool/asset capability for that request |

Use the smallest viable local method. Limited puppeting may satisfy the brief
without an external service. Describe its limits before promising a performance.

For a blink, compare open, intermediate, closed and reopened states against the
source face. Register replacement drawings to stable facial landmarks, match
colour/crop, and composite only the intended region. Inspect source frames and the
encoded cycle close up for sliding patches, face drift, seams and residual iris.
A high registration score alone cannot accept the drawing. Independent pupil warps
can break gaze and eyelid anatomy; omit them unless the full cycle survives review.
These checks apply when animating eyes; they do not require generating eye assets.

## Tune motion without shifting vocal arrivals

| Symptom | Adjustment to try | Trap to check |
| --- | --- | --- |
| Body or hand feels hurried | Lengthen cycles, reduce displacement; try phrase-scale sway | Keep accepted word arrivals unchanged |
| Hair moves rigidly with the head | Delay follow-through and tune its amplitude | Check attachments and exposed edges at extremes |
| Everything reacts on each kick | Smooth sustained energy; reserve onsets for selected accents | Independent parts need distinct motion roles |
| Image jumps at closely spaced onsets | Continuous attack/release or overlapping decays | Do not discard an unfinished pulse at the next onset |
| Word entrances feel abrupt | Ease or lengthen the entrance around the accepted arrival | Preserve audible timing and readable dwell |

Inspect closely spaced onsets, section joins and full movement cycles. Tempo,
amplitude, frame rate, fonts, colours and effect counts remain brief-specific
choices. More frames or a new encoder cannot establish that movement feels right.

## Keep lyric text and timing corrigible

Keep supplied text authoritative and generated timings editable. Compare ordered
words and counts; inspect missing/collapsed timestamps and first words attached to
preceding silence. Review audible arrivals in the short sample, retaining unresolved
estimates as such. A complete word count does not prove every timestamp correct.

Compose phrases with readable hierarchy and per-word timing when requested.
For synthetic text such as “Lanterns drift softly”, emphasize “Lanterns”, use smaller
supporting words and retain each audible arrival. Choose effects that serve the
phrase, with a caption track readable independently of the decorative animation.

## Measure typography in the delivery renderer

Font/em measurements can differ between rasterizers, including Pillow and libass.
Probe with the actual backend and loaded fonts: large/small words, outlines,
dense phrases and entrance extremes. Inspect raster bounds, overlap, safe areas
and contrast in the encoded sample. A layout manifest does not establish that
the encoded glyphs match it. Keep the existing plate legibility check as a screen,
alongside reading the finished type.

## Worked failure and correction

**Symptom:** moving hair, a swaying hand and large/small arriving words were
requested, but the sample is a zooming portrait with one caption line.

**Correction:** use the four decisions above to expose the missing part motion
and word composition. Author the required local motion, preserve source lyrics
and audible arrivals, then inspect another bounded encoded sample.

**Adjacent control:** a calm background with ordinary captions needs no puppeting,
replacement eyes or individual word effects.

## Evidence to report

Use the existing busiest-section preview before the expensive full render. Include
dense words, a strong accent, a complete blink if used and representative part
motion. View the encoded sample with sound at delivery and small viewing sizes.
Fix observed mismatches in the source and repeat the bounded sample. This is a
production check within existing authority, not another permission ceremony.

Full songs retain [long-form streaming](../../orbyn-ui-design/examples/spatial-review/motion-films.md#stream-a-full-length-film).
For delivery, use [encoded output qualification](motion-sequences.md#persist-and-qualify-the-actual-delivery):
report decode, cadence, mux metadata and viewing/listening coverage separately.
Keep subjective acceptance distinct from mechanical passes and preserve separately
requested outputs, such as an unbranded poster, with their own checks.
