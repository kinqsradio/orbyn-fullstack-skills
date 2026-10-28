# Mobile web input and viewport

This guide is for browser surfaces; it does not substitute for native Expo/RN.
Detect capabilities rather than user-agent/device names. Hybrid touch/mouse/pen
and hardware keyboard may coexist; `hover`/`pointer` media queries are hints,
not permission to hide the only action from another input method.

Start visual press feedback on pointer down if useful; commit through cancellable
click/keyboard activation. Track pointer identity and cancel on scroll intent,
pointercancel, lost capture or unmount. Do not perform destructive actions on down.
Scope `touch-action` to the gesture's axis only when needed; keep pinch zoom and
native scrolling available. Never disable root zoom, selection, link menus or
callouts merely to feel native. Content should remain selectable; decorative
controls may use local selection rules when that does not hide information.

Choose viewport strategy from the task: `100svh` reserves a stable small viewport;
`100dvh` follows browser chrome but may resize during scroll. Neither promises
keyboard clearance. Use safe-area env insets with fallbacks, scrollable content
and tested keyboard/visualViewport behavior before fixed bottom actions. Keep
focused input and submit reachable in portrait/landscape and browser chrome changes.
Do not disable zoom to avoid input auto-zoom; choose readable input typography
that works with actual browser accessibility settings. A universal 16px rule does
not replace testing a scaled user setting.

Use a bounded sheet scroll container with deliberate overscroll behavior; local
containment may prevent accidental scroll chaining but can change pull-to-refresh
or navigation. Verify nested scrolling, sticky headers, long forms, safe area and
back navigation on claimed devices. Preserve browser autocomplete/inputmode/label,
password managers and native selection. Theme-color/browser chrome is optional
platform styling, not proof of app installation or input correctness.

Test hybrid hover/touch, keyboard cancellation, scroll vs press, pinch zoom,
selection, open keyboard, bottom action visibility, RTL and long text. Emulation
qualifies CSS/event behavior only; mobile Safari/Chrome keyboard and viewport
need actual device evidence. [Motion](motion.md) and [stress fixtures](stress-fixtures.md)
share the same real component/data boundary.
