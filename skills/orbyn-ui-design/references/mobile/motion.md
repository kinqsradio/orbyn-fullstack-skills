# RN/Expo motion and gesture runtime

Start with [runtime compatibility](../../../language-best-practices/references/mobile/expo-runtime.md)
and the actual installed versions/architecture. Core Animated, LayoutAnimation,
Reanimated or platform controls can fit the task; do not replace a working stack
by decree. Reanimated 4/Worklets configuration differs from older releases.
GestureHandlerRootView and the project's configured Worklets/Babel plugin must
match the supported binary. A bundler success does not prove worklet execution.

## Construction recipes

- Press: native Pressable controls admission; feedback can begin on press-in,
  return on release/cancel; onPress commits once. Keyboard/AT must reach the same action.
- Sheet: measure available height/insets and content, define admissible snap points;
  gesture begins from current translated position, updates shared UI value, ends
  from position+release velocity, commits one snap; cancelled/unmounted owner cannot commit.
- Swipe row: arbitrate horizontal drag against vertical scroll and pointer ownership;
  reveal an accessible action and require a cancellable destructive commit. Removal
  layout and stale row ID are separate from per-frame translation.
- Collapsing header: scroll handler writes a shared UI value; derived styles interpolate
  bounded measurements. Avoid React setState every frame and scroll feedback loops.
- List entrances: stable identity and first-appearance scope; do not replay all rows
  on every filter or remount. Reduced motion can skip entrance entirely.
- Segmented indicator: measure label/layout changes (locale/text scale) outside frames;
  shared x/width animate to the selected item, preserving selected semantics.
- Keyboard footer: use the supported keyboard animation clock/provider when installed;
  do not start an unrelated duration timer or double-apply safe-area/keyboard insets.
- Navigation: prefer supported Router/native transitions; own cancellation, source/
  destination identity and back/dismiss rather than animating disconnected screenshots.
- Toast: admission/outcome stays with the operation; enter/exit lifetime cannot steal
  focus or erase durable status. See [notifications](../async-state.md#notification-identity).

## Worklet boundary

On a verified Reanimated/Worklets target, per-frame translation/opacity and
velocity stay in the UI runtime. Cross to RN only for threshold/end/state effects
through that installed version's supported bridge (`scheduleOnRN` for the verified
Worklets version, older APIs only when actually installed). A closure carries row/
route/account generation and current admission; UI work does not grant authority
to commit a stale RN callback. Cancel animation/subscriptions and invalidate owner
on unmount. Shared values are not React state: read/write via the installed API.
Haptics happen at meaningful threshold/end, not every frame; disabled/unavailable
haptics retain full visible/accessible feedback and must not fail the action.

The critical experiment is real gesture under deliberately busy RN JS: capture
UI movement and RN completion, one admitted commit and correct snap/velocity.
Test takeover, second pointer, cancel, unmount, late callback, keyboard and reduced
motion. A Node state-machine test cannot prove UI-thread continuity or 120fps.
Record that cell as unrun until actual supported native interaction is observed.
The [verification guide](../../../tdd/references/mobile-verification.md) names it
separately from basic screen/navigation qualification.
