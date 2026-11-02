# Verifying ours

A round is: capture ours the same way, run `spec.mjs check`, run `compare.mjs` when the reference frames are available, build sheets, read everything, change one cause. Keep every round's folders: `ours-1`, `check-1`, `compare-1`, then `ours-2`.

## The two checks

`spec.mjs check` reads only the written spec and our track, so it needs no reference capture. It is the main gate, and the only one for a third-party reference once its raw capture is gone.

| Row result | Meaning |
| --- | --- |
| start, end | Our first and last visible change against the row |
| easing RMSE | Our curve against the row's, after removing any start shift, so a late start is reported once |
| family | Spec against ours, printed so you can see what to change |
| distance | Travel against the row |
| gaps | Differences between consecutive starts of one property, the stagger |
| still | A property that must not move |

`compare.mjs` reads frames and writes `report.md` and `report.json`. Exit 1 means a gate failed.

- **Timing error**: start, end, duration and peak of the activity window, in seconds. It reads motion whatever the colours or copy.
- **Curve gap**: the largest distance between the two cumulative activity curves. It catches a shape change that leaves the window alone, such as a wrong stagger.
- **Setup**: settings that differ between the two `capture.json` files. Fix the capture before reading anything else.
- **Mean mismatch**: gated only at pixel fidelity. At motion fidelity read it as a trend: low at rest, spiking only where states differ.
- **Activity bars**: same shape means same easing and stagger.

`--auto-align` and `--offset` exist for a video reference, which has no shared t = 0. Between two captures both are refused, because it would hide a late start.

## Pass criteria

Motion fidelity, per row:

- start and end within 80 ms; stagger gaps within 40 ms
- easing RMSE at most 0.05 against the spec curve
- travel within 10%, same direction
- nothing moves that is still in the reference, and the reverse
- sheets: the same visual state at the same timestamp, allowing for our own design

Pixel fidelity, own or licensed references only, adds:

- mean mismatch at most 2%, no frame above 5% (`--fidelity pixel`)
- same fonts, sizes, colours and assets

Mixed work: the matched region passes with `--region`, and the additions appear on a sheet and are described.

## Reading failures

| Symptom | Usual cause | Fix |
| --- | --- | --- |
| start and end off by the same amount, gaps fine | a missing or wrong base delay | change the delay |
| ours ends early and is front-loaded | easing too aggressive, or the visible duration used as the declared one | use the row's `durationMs` |
| easing fails, family linear against out | wrong curve | change the curve |
| gaps fail, first row passes | per-item delay | `delay = base + index × step` |
| reference overshoots, ours does not | spring against bezier | sample a spring |
| high mismatch at rest | layout, font fallback or crop differs | fix the capture crop, then the layout |
| motion where the reference is still | a stray transition, or the pointer resting on a hover state | remove it, or move the pointer away |
| only the last frames differ | fill mode or end state | hold the final state |
| scroll trigger early or late | observer threshold differs | match the entry point from `track.json` |

## Stopping

Stop when every row passes and the latest sheets show the same states. Say so with the numbers.

Stop after 5 rounds, or sooner when the remaining difference is out of your hands, such as a font licence or a third-party embed. Report the row, its last numbers and the reason. Keep every threshold where it is. If you think a looser bar is right, say which and why, and let the user decide.

If the reference differs between captures, use the virtual clock and the same seed. Whatever still differs is its noise floor: compare the reference against itself before judging ours.

## Report block

```markdown
## Verification (round N of M)
| element / property | start / end ms | easing RMSE | gap ms | distance % | result |
| .title opacity | +0 / −17 | 0.012 (out → out) | 0 | 0.4 | pass |
Sheets: output/motion-match/<name>/compare-N/sheets/compare-01.png
Residuals: none, or the row, numbers and reason
```
