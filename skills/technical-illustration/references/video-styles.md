# Video styles and how their motion works

Each style below is a working method, not a look. The timings come from stepping
through five public videos frame by frame on 1 November 2026. They were studied for
technique only and nothing was copied. Build everything from code under the
[code-only rule](code-only.md).

Pick one style per film and keep to its rules. Most weak videos mix the energy of one
style with the pacing of another.

## Choose by what the song needs

| Style               | Use it for                     | Shots        | What moves                          | Text                     |
| ------------------- | ------------------------------ | ------------ | ----------------------------------- | ------------------------ |
| Hit-pulse visualizer | Phonk, hard electronic music   | One          | A few looping systems plus hits     | None                     |
| Quiet lyric card    | Ballads, pop, long listening   | One          | Almost nothing                      | Two balanced lines       |
| Word stack          | Fast cute pop, nightcore       | One          | Gentle idle, drifting particles     | Words build to the vocal |
| Kinetic cut         | High-energy rock, dance        | Many, fast   | Type, camera, transitions           | Huge single words        |
| 3D journey          | Instrumentals, no lyrics       | Few, long    | A figure crossing a world           | None                     |

## Hit-pulse visualizer

One held composition, with three or four separate systems running over it: a ring or
chain turning behind the subject, particles flying past, a hero object held still, and
a part that changes pose.

- **Hits are short.** Directional blur, channel split and bloom peak on the onset and
  have gone within about 3 frames at 30 fps. The clean image is what stays in memory.
- **Space hits by the beat.** At 150 BPM, a hit lands every 0.4 s. Don't hit every kick.
- **Snap poses.** A hand changes from open to fist between one frame and the next, on
  the beat, with no in-between. Smooth tweening looks weak here.
- **Rotate the ring continuously.** Steady motion under sharp hits gives the contrast.

## Quiet lyric card

Nearly nothing moves, and the type is the craft.

- Keep each line anchored in the same place, as two rows of balanced length.
- Crossfade between lines in about 0.5 s, with no slide or scale.
- Use a clean hand-drawn or rounded letterform with a soft shadow, large enough to read
  on a phone.
- End with a short brand sting: a mark drawing on, a wipe and a card. Keep it under 8 s.

## Word stack

One held character or scene with a soft idle, and lyrics that build word by word.

- Each sung word appears in place at its own onset: "What", "What you", "What you want".
- The finished phrase fades and drifts as the next one lands in the same spot, so the
  eye never has to travel. At a fast tempo this cycle runs about every 0.5 s.
- Use large rounded type with a thick outline, so it stays readable over a busy image.
- Keep the idle to about 2 or 3 small moves: sway, drifting hearts or petals, a blink.

## Kinetic cut

The most demanding style. Lots of shots, with type treated as a graphic.

- **Depth sandwich:** put a huge word behind the character. Hold the character's pose
  while the word hits, which reads as depth without any 3D. The hold is a pause in
  acting only: keep hair, breathing and blinks running, because a film built from an
  image still needs [real character motion](animate-an-image.md).
- **One-frame accent:** a new word arrives with a colour-channel split on its first
  frame, and settles over the next two.
- **Transitions are accents.** A burst of white shards opens a shot, and a whip blur
  carries straight into the next close-up.
- **Vary the graphic:** repeated stacked words, slit glitches, scanlines, a neon
  perspective corridor. Use each for one section and move on.
- **Rest:** drop to black with one small word now and then, so the next hit lands.

## 3D journey

A small figure crosses a large world toward a visible goal, so the picture carries the
piece without lyrics.

- Keep the figure small in frame. A long shot hides detail and sells scale.
- Give the world a beacon that is always readable, such as a glowing shape on the horizon.
- Track slowly from behind and to the side. Use long shots, then cut on a section change.
- Fill the air with something: floating shapes give depth, and foreground rocks pass the
  lens.
- At a drop, alternate clean frames with a vertical pixel-stretch, at most 3 bright
  pulses a second, so at least 0.34 s apart. The studied video pulsed faster, but more
  than 3 flashes in a second is a seizure risk and fails `flash-check.py`.
  Light events, such as a lens flare appearing, mark quieter moments.

Build it with [3D worlds](3d-worlds.md) and [character animation](character-animation.md).

## What all five share

- One focal point at a time, and a composition that still works as a still.
- Strong contrast between what stays still and what hits.
- Motion tied to musical sections first, and to individual beats second.
- A short, deliberate accent, not a long effect. Long effects read as noise.
- Far fewer moving things than you would guess.
