# Navigation and route identity

Inspect installed Router and native-screen versions, entrypoint, routes and session
owner. In Expo Router a route file exports a screen; `_layout.tsx` owns its Stack,
Tabs or providers; groups `(name)` organize without adding a URL segment; `[id]`
adds a parameter; `+not-found` handles unmatched navigation. Shared controls and
platform implementations stay outside route paths. Preserve existing URL contracts.

A small supported stack can use `Stack` from `expo-router`, with `Stack.Screen`
options declared at the owning layout. Screens read `useLocalSearchParams` and
validate expected scalar IDs (arrays/missing are not silently authorized IDs).
Use `Link`/router push for navigation, replace for a deliberate history replacement,
and dismiss/back only when that stack can do so; direct cold links need a meaningful
fallback. Avoid converting every navigation into replace and losing Back behavior.

## Session, deep links and tabs

Map cold/warm deep links, signed-out redirect, post-auth return target, tab switch,
sheet open/dismiss, hardware/system back and sign-out. Route availability is not
resource authorization; the API still checks the requested account/tenant.
Fence async loaders and callbacks with route+session+generation. A late auth/loader
completion cannot reopen a route after its owner changes. Preserve intended
history without bouncing through a forbidden protected screen.

Choose installed JS tabs, custom headless tabs or supported native tabs based on
platform behavior and accessible labeling, not a universal native-tabs mandate.
`unstable-native-tabs`/NativeTabs API and OS-specific search/minimize/accessory
behavior vary by SDK; verify exact exports and safe-area/keyboard ownership.
Do not copy a future icon/label signature into an old app. Test badge, repeated tap,
scroll-to-top, back stack and web route fallback where the task needs them.

## Sheets, search, headers and transitions

Use supported native form-sheet presentation/detents only with bounded content,
scroll/keyboard/safe-area and dismiss/unsaved-work policy. Platform-specific sheet
options need a fallback and real device/simulator checks. Search is controlled by
the owning route; clear/debounce callbacks and in-flight results cannot mutate the
next route/account. Keep query identity separate from a localized display title.
Header/toolbar placement and actions use installed API; test hidden/disabled and
large-title/scroll edges. Apple zoom/Link previews require version/OS gates and
matching source/destination IDs. Preserve normal link behavior, focus, context
menus and dismiss continuity if the fancy transition is unavailable.

## Slice and evidence

The fixture's index→detail stack carries a validated item ID and account parameter;
invalid/missing input shows recovery rather than an invented object. Browser route
loading/source/type checks qualify only those surfaces. Cold/warm link, native
redirect, tab/sheet/back and gesture dismiss require named runtime observations;
record them separately in [mobile verification](../../../tdd/references/mobile-verification.md).
