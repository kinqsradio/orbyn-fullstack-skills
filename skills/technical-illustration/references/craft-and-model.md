# Explain a mechanism with one model

First write the one decision or relationship the reader should understand. A
physical metaphor earns its place when the object's operation expresses that
relationship. Prefer an ordinary chart or labelled diagram when axes/data are the
actual subject. Do not assert fabricated physics is measured product behavior.
Describe units, valid state envelope, approximations and where the analogy stops.

## Model before decorative parts

Separate pure calculation from DOM, time and drawing. Given model state and sampled
instant, return phase, relevant values and geometry inputs. Render every part,
readout, caption and accessible description from that same sample. A gauge easing
toward a target cannot label itself with the target's value while showing the old
pose. Either sample the visible value or explain the lag explicitly.

Example: a token bucket model has capacity, tokens, refill rate, last instant and
requested cost. Its frame distinguishes accepted consumption from rejected work;
clamped tokens and the text come from the same calculation. Test empty/full,
exact-capacity, insufficient-cost, refill and reverse/takeover states. A decorative
valve is not a separate authority for the token count.

Keep stable IDs for meaningful parts and semantic phases. Use repetition, material,
line weight and contrast to reveal purpose; do not impose mandatory part counts,
light-first styling or a universal ban on arrows/comments. Labels must remain
readable at the actual delivered size. Preserve contextual captions and useful
text even if GPU/animation is unavailable.

## Establish the artifact contract

Choose standalone HTML/SVG or a consumer-owned React component, with the target's
actual build and assets. Keep model, build, style, interaction and tests separately
owned; bind their hashes at delivery. The bundled `kit/iso-kit.mjs` provides
`cameraOf`, `iso`, `depthOf`, `pathOf`, `extrude`, `slabOf` and `cylinder`; inspect
exact exported signatures before using them. Apply the same camera to every
geometry and overlay. CSS and model are artifact inputs, not implied by a kit hash.

Produce a meaningful rest pose first, then one real interaction. Inspect it at
usable width before adding details. Add invariants to the model and independent
shape/readout checks rather than a second copied model that can share its defect.
Retain the baseline artifact. Fix actual source when an observed mismatch occurs;
do not paint a corrected screenshot over broken live behavior.

Finish with the built artifact, model explanation, reproduction command, inspected
states and explicit unsupported surfaces. A working figure is the output; this
method does not require a public gallery, hosted service or new application stack.
