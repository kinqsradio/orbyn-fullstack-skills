# Character animation in code

A character here is data: named joints, a pose for each moment, and code that draws
primitives on those joints. New poses, walks, acting and lip movement are all things
you author, so nothing about them needs an outside asset. The working kit and its tests
are in [`examples/code-only-film/rig.mjs`](../examples/code-only-film/rig.mjs).

Sample everything from absolute time. Frame 100 must look identical whether you reach
it by playing, seeking or rewinding, so you can render one frame or one section again
and have it match the rest. The exporter itself takes frames in order and rejects any
that arrive out of order, so this rule is for re-rendering, not for parallel capture.

## Build the character

1. Choose the style first: 2D with drawn shapes, or 3D with signed distance primitives.
   A simple, consistent design beats a detailed one that falls apart in motion.
2. Define a joint tree with named parents and offsets: pelvis, spine, head, shoulders,
   elbows, hands, hips, knees, feet.
3. Use forward kinematics for arcs: arms swinging, heads turning.
4. Use two-bone inverse kinematics for contact: a foot on the ground, a hand on a rail.
   Give the bend a direction, so a knee never flips backward.
5. Set proportions in head-heights. About 6 reads as a stylised adult, and 2 to 3 as
   cute. Keep one scale for the whole film.

## Animate the body

Block the key poses first, and play them with holds before adding any in-betweens. If
the stepped version doesn't read, smoothing will not save it.

| Principle        | In code                                                                |
| ---------------- | ---------------------------------------------------------------------- |
| Anticipation     | A small move the other way before the main action                      |
| Overlap          | Each child joint lags its parent by a frame or two                     |
| Arcs             | Rotate joints; don't move hands in straight lines                      |
| Weight           | Pelvis drops as weight lands, and stays low for a beat on a heavy move |
| Silhouette       | Check a pose as a filled black shape; arms clear of the body           |
| Asymmetry        | Offset left and right, so nothing mirrors exactly                      |
| Holds            | Let a pose sit, adding only a small drift so it stays alive            |

**Choose the timing by style.** A snap with no in-betweens hits hard for a beat-driven
visualizer. Smooth easing suits calm acting. Animate on twos by rounding the character's
sample time to 12 fps while the camera stays at full rate, which gives a drawn feel.

## Walks and runs

Drive a walk from one phase value and a speed. Each foot has a stance phase and a swing
phase:

1. During stance, the foot stays at a fixed world position. This is the rule that stops
   foot sliding, so compute it from the body's travel and never from a looped offset.
2. During swing, lift the foot on an arc to the next planted position.
3. Solve the knees with inverse kinematics from pelvis to foot.
4. Bob the pelvis twice per cycle, lowest as the feet are furthest apart, and sway it
   toward the stance side.
5. Swing the arms opposite the legs, and counter-rotate the shoulders against the hips.
6. Keep the head steadier than the body.

A run adds a flight phase with both feet off the ground, a forward lean and a bigger
bob. Sample the ground height under each foot, so feet meet uneven terrain.

## Hair, cloth and tails

Treat these as chains that follow the root late. Never use a stateful integrator, since
its result depends on the frames played before it, which breaks seeking. Compute each
link as a pure function of the root's motion, delayed further down the chain, or bake
the samples once into a table. Pin the first link, and let the last link move most.

## Faces

Keep the face simple and let timing do the work.

- **Eyes:** blink at irregular seeded gaps, closing over 2 frames and opening over 3 or
  4. Move the eyes a moment before the head turns.
- **Mouth:** a few timed shapes are enough: closed, open wide, rounded, and teeth. Drive
  them from the supplied lyrics' timing, with the shape switched just before the sound.
- **Brows:** usually carry more feeling than the mouth, so change them on emotional
  beats.

## Acting to music

Choose a role for each body part, so everything doesn't react at once. Use sustained
energy for slow sway, onsets for one chosen accent, and section changes for new poses.
Plan poses on phrases, then let the beat nudge them.

## Check before rendering

Render a short loop with a plain floor and the camera side-on, then check:

- Stance feet stay still in world space: the kit's test measures this.
- Feet touch the ground, and hands reach what they should.
- Knees and elbows never pop or flip.
- Frame 100 is identical after seeking and after playing.
- Silhouettes read at the size used in the film.
- Step through a whole cycle. A walk can pass every number and still look stiff, so
  watch it and fix the poses.
