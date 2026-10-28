# Diagnose motion cost

Capture the same completed interaction, content size, concurrent workload, build,
viewport, hardware and runtime before and after a change. Inventory driver and
per-frame work: RN JS/UI threads or browser style/layout/paint/composite/React.
A screenshot shows a pose; `transform` or CSS spelling cannot prove compositor
execution, a GPU path or a frame-rate guarantee.

Use the target profiler to locate long tasks, repeated layout reads/writes,
invalidated paint, inherited CSS-variable work, rerenders or expensive effects.
Compare idle and busy-load behavior through the real component; never simply remove
the workload for the after result. Localize frequently changing variables where
measured descendant invalidation is the cause. Batch reads then writes; prefer
supported compositor-friendly properties when they preserve the actual layout,
hit-testing, clipping and text sharpness. Scaling an expanding text panel is not
a semantic replacement for height/layout. Small bounded layout animation can be
acceptable when measurements support it.

`will-change`, layers, blur and offscreen surfaces consume memory and can increase
work; add only for a measured need and remove with the animation owner. Keep frames
free of network/state cross-runtime chatter and heavy logging. A JS-blocked WAAPI
animation may still visually progress while click delivery is delayed: record both,
not just apparent smoothness. RN worklets have a separate runtime contract.

Retain traces, interaction start/end and failures. Report observed duration/frame
or task metrics and sample count, not an invented universal threshold. Include
correctness checks (focus, final pose, input, text/layout and cleanup) so a faster
but incomplete interaction cannot win. Browser emulation and debug JS traces do
not establish release-device smoothness. Use the existing performance playbook
for cause/budget, then [motion](motion.md) for correction and [mobile verification](../../tdd/references/mobile-verification.md)
for native evidence.
