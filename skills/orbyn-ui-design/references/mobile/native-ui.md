# Native controls and content

Apply to demonstrated Expo/RN work. Read [runtime](../../../language-best-practices/references/mobile/expo-runtime.md)
and preserve the target's tokens, native component owner and platform conventions.
Choose the smallest supported component that meets the task, rather than replacing
the installed UI stack by preference.

## Component and layout selection

| Family | Capability and boundary |
| --- | --- |
| RN core controls | Text, View, Pressable, TextInput, Switch; portable supported behavior, native keyboard/accessibility |
| Universal `@expo/ui` | Shared facade where installed; verify Host, component props and native-state requirements |
| `@expo/ui/swift-ui` | Apple-only views/modifiers in supported binary; Host and RN-host bridge measured explicitly |
| `@expo/ui/jetpack-compose` | Android-only composables/modifiers; no importing unsupported platform code on web/iOS |
| Drop-in replacements | Check installed exported API, behavior, theming and peer/native requirements before substitution |

Keep platform-specific implementation in `.ios`/`.android` components outside route
files, with an explicit supported fallback. Host size, flex and intrinsic content
must be measured; RN children inside a native-host view are not ordinary DOM layout.
A Form/List of grouped native rows is not a virtualized large collection. Use the
project's FlatList/SectionList or proven virtualization, stable item keys, bounded
render work, empty/error/footer and item semantics. Do not nest same-axis virtualized
lists in a plain ScrollView to conceal warnings.

Use semantic color roles for foreground/background/separator/destructive/disabled,
light/dark/high-contrast variants and text scale. Keep real text responsive to
accessibility size, safe-area insets and RTL; do not hardcode every label height.
Use platform accessibility role/label/value/state and group only meaningful units.
A switch's current value and a field's error must remain perceivable. Preserve
screen-reader order, focus on error/recovery, hardware keyboard and visible actions
when the on-screen keyboard is open. Test large data and long/RTL values through
the same [stress fixtures](../stress-fixtures.md), not a copied screen.

## Icons, surfaces and media

Use actual installed icon families or supported platform symbols with text labels
and a fallback for unavailable OS symbols. Decorative icons are hidden from AT;
color alone cannot identify the action. Gradient/text/mask APIs differ by SDK and
platform; retain solid high-contrast content when a gradient/material is unsupported.
Blur/glass needs supported reduced-transparency and contrast fallbacks, readable
foreground and sensible clipping. A visual effect cannot replace hit targets.

For images use bounded dimensions/aspect, placeholder/error, content-fit and cache
identity; do not decode unbounded originals for thumbnails. Video/audio needs an
owned player, pause/background policy, permission/route interruption and release
on unmount. `expo-av` to audio/video migration is in the [upgrade guide](../../../orbyn-ci-design/references/mobile/build-and-upgrade.md).
Pick secure credential storage, ordinary preferences or file/media storage by data
classification and backup/deletion policy; web storage is not native secure storage.
Never put tokens in public config or media URLs logged as diagnostics.

WebGPU/Three is conditional specialist work: verify actual Expo/native/browser
bindings, renderer support, surface resize, GPU/resource disposal, frame budget,
background suspension and fallback. Avoid assuming DOM canvas globals in RN.
Use a normal image/control fallback if the capability is absent; no automatic GPU
or package installation follows from the source's example.

## Runnable slice

The fixture's real `RecoveryScreen` uses TextInput, Switch, FlatList, error/retry,
account switch and route link with source-injected delayed transport. Its same
controller rejects late completions after account change and disposal. Typecheck,
web rendering and native interaction are separate receipts. A rendered RN web view
does not prove iOS/Android keyboard, AT, scroll or text scaling.

## Offline API selection example

The pinned source's newer universal API uses `Host`, `Column`, `Button` and `Text`
from `@expo/ui`, for example a Host with `matchContents` containing a Column and a
Button with `onPress`. Its universal TextInput uses `useNativeState` observable
value rather than an RN plain string; synchronous transforming callbacks require
the supported Worklets integration. This is version-qualified source guidance,
not a claim those exports exist in SDK55. Verify `node_modules/@expo/ui/package.json`
exports, installed declaration of Host/component props and platform native code.
Read a small selected declaration locally; do not run upstream component-list code
or infer runtime readiness from parsing a symbol. If the installed family lacks
that API, retain RN controls or its supported platform family instead of upgrading
merely to match the example.

For a selected SwiftUI family import components from the installed
`@expo/ui/swift-ui` entry and Host from the entry its installed declarations require;
for Compose do the same with `@expo/ui/jetpack-compose`. A platform-specific component
behind `.ios.tsx`/`.android.tsx` should have a common prop contract and explicit fallback.
Drop-in community replacement exports use their own entrypoints and signatures;
a universal BottomSheet is not automatically a drop-in gorhom sheet. Build and
operate native controls before calling a replacement complete.
