# Implementing the motion

Use what the project already uses. Adding an animation library to a project that animates with CSS is a change the user did not ask for. When nothing exists yet, prefer CSS keyframes, transitions and scroll-driven animations, then the Web Animations API.

For a video, follow the [code-only rule](../../technical-illustration/references/code-only.md): every picture and movement comes from code written in the project, and animation libraries stay out unless the user lifts the rule for a named item.

When the reference is someone else's, take the numbers and nothing else. Write the markup, styles and copy yourself. If you catch yourself looking at their stylesheet to choose a colour, a radius or a layout, stop.

## Easing

`spec.mjs` writes a `cubic-bezier(...)` you can paste into CSS or the Web Animations API. Translate it to the project's own animation tool if it has one.

A spring has no bezier form. Fit it, then generate it:

- Overshoot ≈ `exp(−π ζ / sqrt(1 − ζ²))`, with `ζ = damping / (2·sqrt(stiffness·mass))`. 10% overshoot gives ζ ≈ 0.59, 5% gives 0.69, 20% gives 0.46.
- Settle time ≈ `4 / (ζ·ω)`, with `ω = sqrt(stiffness/mass)`.
- Start from mass 1, pick ζ from the overshoot, then stiffness from the settle time. `easing.mjs` reports the fitted values.
- In CSS, sample the curve into `linear(...)`, or give the Web Animations API sampled keyframes.

## Patterns

**Fade-up stagger**

```css
.item { opacity: 0; transform: translateY(32px); animation: up 700ms cubic-bezier(.16,1,.3,1) forwards; animation-delay: calc(var(--i) * 90ms + 200ms); }
@keyframes up { to { opacity: 1; transform: none; } }
```

**Enter-viewport trigger**: use `IntersectionObserver` with `threshold` set to the fraction visible when the reference starts, read from `track.json`. Scroll-driven CSS works where supported: `animation-timeline: view(); animation-range: entry 0% entry 40%`.

**Scroll-linked**: `animation-timeline: scroll()` with `animation-range`. The mapping is scroll px to value; take both endpoints from the track.

**Text reveal by line or word**: wrap each piece in an `overflow: hidden` box and animate `translateY(110%)` to 0. Keep the accessible text intact: `aria-label` on the container and `aria-hidden` on the pieces.

**Hover lift**: animate `transform`, not `top`. Check the hover-out frames too.

**Marquee**: duplicate the content once and run `translateX(0)` to `translateX(-50%)`, linear, for the measured period.

**Clip reveal**: `clip-path: inset(0 100% 0 0)` to `inset(0 0 0 0)`.

**Frame-rate independent lag**: `x += (target − x) · k` becomes `x += (target − x) · (1 − (1 − k) ** (dt / 16.67))`.

## Details that decide the match

- `transform-origin`: a menu scales from its button corner, a modal from its centre.
- `overflow: hidden` wrappers decide whether a sliding element is clipped.
- Transform order: `translate() scale()` is not `scale() translate()`. Use individual properties where the stack allows.
- Fill and initial state: render the pre-motion state in CSS, so the first frame already matches and the final state never flashes.
- Reduced motion: wrap non-essential motion in `@media (prefers-reduced-motion: no-preference)`. If the reference ignores it, add it anyway, unless the user says not to, and mention it.
- Fonts: for pixel fidelity on work we may copy, load the same family before capturing, or every frame mismatches. At motion fidelity ignore text pixels and read the timing rows.
