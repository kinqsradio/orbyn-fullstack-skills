# Reproducible adverse UI inputs

Map field→source/schema→actual constraint→component→wrap/truncate/full-access
choice before fabricating extremes. Missing schema length is not an invented cap
or automatic validation task. Use deterministic seed and synthetic values through
the real fixture/loader/data interface; do not copy the screen into a toy page.
Keep production data, credentials and persistent debug controls out.

| Family | Discriminating fixtures |
| --- | --- |
| Names and identifiers | Grapheme-rich emoji, one-word name, combining marks, CJK/Arabic/RTL, long unbroken ID; avoid western first/last assumptions |
| Text | Empty/optional, translated long labels, paragraphs, URLs; accessible full value beyond a mouse-only title |
| Numbers | Zero/one plurals, large/negative money with currency, grouping, precise units, unknown rather than fake zero |
| Collections | Empty/one/realistic large, mixed heights, stable keys, pending/error/partial pages; use actual virtualization |
| Time | Zone/day boundary, DST, past/future, unknown date, relative label ambiguity |
| Media | Missing/slow/broken image, extreme aspect, placeholder failure, long captions |
| State | Offline, denied, pending retry, stale result, keyboard open, reduced motion, RTL, supported contrast/transparency preferences |

Record seed/input hash, schema/version, source/candidate, scenario, runtime and
actual container. Minimize a failure to the fields needed to discriminate its cause;
one giant pathological dataset obscures it. Fix the owning wrap, width, overflow,
layout, schema or data semantics; do not shrink everything or silently discard
meaning. Long values may wrap, use intentional truncation plus an accessible
copy/details path, or choose an alternate layout. Tooltip title alone fails touch
and keyboard full-access. Check controls and focus remain reachable.

The Expo fixture injects deterministic multilingual rows through its actual screen
controller; browser checks must navigate and operate that same screen. Tests that
only check the fixture JSON validate generation, not layout. Preserve failure
captures, remove only owned temporary toggles, and promote a minimized behavioral
regression under [TDD](../../tdd/SKILL.md) when it protects a demonstrated defect.
