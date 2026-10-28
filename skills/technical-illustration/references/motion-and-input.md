# Motion, input and semantic time

Define a state transition table before animation: rest, ready, user-controlled,
transitioning and settled, plus the model's meaningful phases. Specify what arms a
control and what can interrupt it. Give each rendered frame one sampled instant;
geometry, phase, number and caption must agree at that instant.

## Takeover and reversal

When the person drags or presses a key, begin from what is visibly rendered,
including an in-flight transition. Do not jump to a stale target or restart a tour.
Automatic motion yields to user input. A control whose physical mechanism has not
arrived is not ready merely because its event listener exists. Define how a new
command is buffered/rejected until ready and test both decisions.

Exercise intermediate/prefix states, tails and reversals, not only rest/endpoints.
A part's visual grouping is different from physical attachment: a cable can be
painted with one layer while its endpoints belong to moving components. Verify
attachments through the actual schedule. Use the owning elapsed clock; a slow RAF
fixture changes RAF/performance time, not wall timers or network delivery.

## Lifecycle and accessibility

Native keyboard and pointer interaction should operate the same model. Record
focus target, key/code, hit zone and actual event surface. Synthetic DOM dispatch
is not native input proof. Keep instructions, readout and operable controls when
prefers-reduced-motion is enabled; reduced motion can choose immediate/limited
poses while preserving the meaningful state.

Announce user choices and semantic phase changes once, never 60 updates per second.
Use an appropriate live region separate from constantly changing visual numbers.
Do not steal focus for passive animation. Preserve text/contrast under theme change.

Own listeners, timers, RAF and observer handles. Suspend work when settled or
outside the relevant visibility surface and resume from current model time
without a discontinuity. A stale ref or replaced figure must not receive writes.
Cancel/join supported work before teardown and test remount/replacement. Define
what happens to retained input/state while paused rather than silently reset it.

## Evidence

Run one legitimate takeover/reversal and a planted stale-target or early-arming
control at actual intermediate times. Inspect captured frames and native readouts;
compare model values to visible phase and geometry. Test reduced motion, settled
and offscreen transitions independently. Bounded samples qualify those states only,
not every possible continuous trajectory or assistive technology.
