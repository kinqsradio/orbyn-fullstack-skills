# Reading frames and writing the motion spec

The spec turns "I watched it" into rows you can check. Write it before building and update it when verification teaches you something.

`spec.mjs draft` writes `spec.json`, the contract, and `spec.md`, a table to read. Fill in `target` and `destination`, and replace every `?`. `spec.mjs check` refuses to run while one remains.

```json
{
  "schema": 1, "name": "hero", "rights": "third-party", "fidelity": "motion",
  "target": "the hero of the page the user named, on load",
  "destination": "the project's hero component",
  "rows": [
    { "selector": ".title", "prop": "opacity", "from": 0, "to": 1, "startMs": 200, "endMs": 660,
      "easing": "cubic-bezier(0.22,1,0.36,1)", "family": "out", "delayMs": 200, "durationMs": 700,
      "overshootPct": 0, "fitRmse": 0.003, "source": "track" },
    { "selector": ".title", "prop": "scale", "still": true, "value": 1 }
  ]
}
```

`startMs` and `endMs` are the first and last visible change, measured the same way on both sides. `delayMs` and `durationMs` are the fitted values to put in the code; an ease-out's declared duration runs past its visible end. Add `cloneSelector` to a row when our element has a different selector. For a third-party reference the row describes behaviour only, and our markup, look and copy are our own.

Note the static facts the motion depends on in the markdown beside the spec: element sizes, z-order, overflow clipping and transform origins. Add fonts, colours and spacing only for pixel fidelity on work we may copy.

## Where the numbers come from

In order of preference:

1. `inspect.json › animations`: delay, duration, per-keyframe easing, iterations and direction.
2. `track.json` through `spec.mjs draft` or `easing.mjs`: delay, visible window, overshoot and the best-fitting easing, for any technology. Overshoot above 2% means a spring or a back easing.
3. Frames, for videos and gifs: find the first and last frame where an element changes. `start = first/fps`, `end = (last + 1)/fps`. If it covers more than half its distance in the first third, it is an ease-out; less than a quarter, an ease-in; symmetric, an ease-in-out; equal steps, linear. `compare.mjs` prints an activity curve that shows these shapes as bars.
4. Staggers: the gap between sibling starts. Note whether it is constant, grows, or runs per word or per character.

## Patterns worth recognising

| Pattern | Tell-tale frames | Typical numbers |
| --- | --- | --- |
| fade-up stagger | siblings rise 16 to 48 px while fading, each slightly later | 500 to 800 ms, strong ease-out, stagger 60 to 150 ms |
| text reveal | pieces appear in order, often clipped by their line box | 600 to 1000 ms, stagger 20 to 50 ms |
| clip reveal | content uncovers along an edge, no fade | 800 to 1200 ms, ease-in-out |
| scale-in | grows from 0.9 to 0.96 with a fade, origin at the anchor | 150 to 250 ms, ease-out |
| hover lift | moves up 2 to 8 px, shadow grows | 150 to 300 ms, ease-out |
| marquee | continuous translateX of a duplicated row | linear, period 10 to 40 s; measure the period |
| scroll-linked | changes only while scrolling | ties to `scrollY` ranges |
| pinned section | stays fixed while the page scrolls past | `y` constant for a scroll range |
| parallax | layers move at fractions of the scroll delta | ratios such as 0.2, 0.5 and 1 |
| spring | overshoots, then settles | stiffness and damping; see the implementation notes |
| pulse | opacity or position oscillates | period 1 to 2 s, ease-in-out |
| page transition | old view exits, new view enters | 300 to 600 ms, exit shorter than enter |

## How to read a sheet

- Go row by row with the labels. Write down, per element, the frame it first moves and the frame it rests. Do this for every element, not only the biggest.
- Compare consecutive frames: a big jump then small changes is an ease-out; small then big is an ease-in.
- Look for what is easy to miss: a backdrop that fades, a shadow that grows, a blur that clears, a border that appears.
- Note what does not move. Something moving where the reference is still fails just as much.
