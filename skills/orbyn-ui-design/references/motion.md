# Motion that preserves the interaction

Use for ordinary product motion, not only illustration. State purpose (feedback,
continuity, hierarchy or explanation), trigger, frequency, actual driver, affected
properties, current pose/velocity, completion and cancellation. A frequent task
may need immediate spatial feedback; no fixed timing/easing/frequency rule fits
all products. Keep project tokens and accessible no-motion completion.

## Construction and interruption

1. Implement final static layout, semantic state and keyboard action first.
2. Identify the source/trigger and measure origin after collision/placement. An
   edge-flipped popover animates from the resolved anchor, not a fixed center.
3. Animate from the currently presented value. On reversal cancel/retarget using
   the live pose and, for a spring/drag, velocity; do not restart at an endpoint.
4. Keep exiting content alive only through its visual lifetime; remove it from
   tab order/input/AT at the correct semantic close boundary. Opacity alone does
   not hide a control. Do not leave a background dialog focusable.
5. Fence animation callbacks by owner/generation. Old exit completion cannot hide
   reopened content; teardown cancels frames/listeners/timers and releases capture.

CSS transitions fit state changes; CSS keyframes fit repeatable sequences; WAAPI
supports explicit control; a supported motion library fits measured gestures or
shared-layout needs. Choose from actual dependencies; no default replacement.
For WAAPI retargeting, read current computed presentation before cancelling,
then animate toward the current desired state. Apply final semantic state through
the real component, not just `fill: forwards`. Version-specific APIs need actual
browser checks. `transition: all` can animate unintended layout; explicit
properties help reasoning but cannot prove performance by themselves.

## Pointer and gesture ownership

A drag owns one pointer ID. Capture only that pointer, ignore unrelated pointers,
release on up/cancel/lost capture/unmount, and distinguish press feedback from
committed activation. Preserve keyboard, focus and an accessible non-gesture path.
On takeover snapshot live position/velocity, use relative translation and clamp
against measured geometry. Project release only when that matches the task, select
an admissible snap and issue one end/threshold commit. A cancelled destructive
interaction does not commit. Swipe/haptics are not exclusive feedback.

## Accessibility and review

Reduced motion may select an immediate final state; preserve task completion,
focus, feedback and cleanup. Respond to a changed preference while mounted.
Supported reduced-transparency/increased-contrast preferences get readable solid
surfaces; unsupported settings remain unverified rather than invented properties.
Review rapid open-close-open, delayed readiness, pointer takeover/cancel/multitouch,
keyboard and hidden focus, stale completion, reduced motion and route unmount.
Separate behavioral/accessibility defects from stylistic taste. A valid review may
recommend no animation. [Performance](animation-performance.md) owns trace claims;
[mobile motion](mobile/motion.md) keeps RN/UI runtimes explicit.

Useful vocabulary: origin is the resolved spatial source; interruption is a new
intent before completion; takeover preserves presentation/velocity; exit lifetime
is the interval before visual removal; settling is completion within the chosen
position/velocity tolerance. A glossary helps feedback without restricting language.

[Selected methods and notices](mobile/sources.md) preserve adaptation lineage.

## Code-driven composition

For code-driven UI motion and an editable preview, use the existing
[motion composition and inspector](../examples/spatial-review/motion/README.md).
Keep live gesture velocity, interrupted presence, keyboard takeover and reduced
motion separate from deterministic export seeks. Keep optional graphics/audio
backends out of ordinary product UI prerequisites.
