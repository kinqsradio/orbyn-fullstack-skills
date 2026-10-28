# Mobile boundaries, extensions and migration

Apply to demonstrated Expo/RN or an explicit native integration. Inspect the
actual runtime, native tree and host contract before generation. Existing
[vertical ownership](vertical-codebase.md) still applies: route files adapt URLs
and layout; capability modules own behavior/data; native hosts own native lifecycle.

## Route, DOM and native UI boundary

Keep Router screens/layouts separate from reusable/platform-specific components;
platform extensions resolve behind a common interface. Native DOM components use
an explicit supported `use dom` boundary and serializable props. Functions require
the framework's supported callback bridge, not arbitrary function/object transfer.
Document JSON types, limits, errors, cancellation and owner generation. Refs, layout,
assets and event propagation cross different runtimes: measure container size,
keyboard/scroll and message origin rather than assuming RN style semantics or DOM
availability. Bundle asset paths for the actual native/WebView origin; sanitize
untrusted HTML, navigation and incoming messages. Native permissions stay native;
a DOM bridge cannot authorize camera/files or expose arbitrary native calls.

## Module and native view checklist

1. Choose local module vs distributable package. Use the installed create-expo-module
   CLI options only after inspecting help and target scope; never run an upstream
   scaffold simply because a guide names it. Keep npm/native names and paths stable.
2. Register Apple module classes and Android fully qualified module names in the
   supported `expo-module.config.json`; inspect autolinking output for the actual
   build variant. A JS wrapper without native registration is incomplete.
3. Define sync/async/event/view APIs: JS name, type/nullability/default/requiredness,
   actor/queue, pre-first-await execution, error mapping and cancellation owner.
4. Own `OnCreate`/`OnDestroy`, observation start/stop, app/activity listeners and
   native-view mount/prop/event lifetimes. Release listeners/player/file/resources;
   after disposal no callback may publish to another JS owner.
5. Config plugins modify configuration deterministically and idempotently through
   supported mods, preserving unrelated Info.plist/entitlement/manifest/Gradle data.
   Never write raw secrets into app config or destructive string-replace native files.
6. Build the matching binary, resolve the module by name in the running app, call
   sync/async paths, subscribe/unsubscribe events, deny permission, cancel/unmount
   during callbacks and verify view prop/event behavior. TS compile does not prove it.

A minimal supported DSL shape is `Name("Counter")`, `Function("read")` and an
`AsyncFunction("reset")` with deliberate queue/actor; the TS wrapper calls
`requireNativeModule("Counter")`. It is a shape, not a compiler-qualified module.
Check the target's ExpoModulesCore version and native toolchain before selecting
signatures. Native views additionally map prop updates and event payload names to
the installed `requireNativeView` contract, avoiding double listener registration.

## Brownfield: integrated and isolated

| Approach | Owner/compatibility | Verify |
| --- | --- | --- |
| Integrated native host | RN/Expo dependencies and native build in host; shared runtime/resources | Version alignment, autolinking, AppDelegate/activity hooks and host lifecycle |
| Isolated artifact | Producer builds framework/AAR/library against a declared host ABI/toolchain contract | Correct architecture, signing/resource/dependency packaging, host embedding and artifact identity |

Record host and producer commits, React/RN/Expo and native ABI/toolchain versions,
artifact hash, supported platform/flavor and entry module. Initial props carry a
fresh request ID and validated payload. The native host owns one presentation and
one correlated result; dismiss/back/swipe/RN cancel converge on the same one-shot
completion. Remove listeners before closing, invalidate request on teardown and
reopen with new props/ID. A stale listener cannot complete the next presentation.
No presentation callback is an authorization bypass for host effects.

Troubleshoot missing symbol/autolinking, duplicate RN/runtime, architecture slice,
resource bundle, entry module, Metro URL and release embedded bundle separately.
Test a matching Release host/artifact with Metro stopped, cold start, result,
cancel from both sides, swipe/back, reopen and background. Debug server success
leaves release integration open. Do not regenerate a manually maintained host.

## Web-to-native migration

Inventory auth/data/navigation, DOM/CSS/storage/browser APIs and platform policies;
select a narrow high-value flow and runnable native shell before broad conversion.
Map CSS layout to supported RN/native styles (no cascade/DOM assumption), HTML input
and events to native controls, localStorage to classified native storage, browser
history to real back stacks, file/media URLs to permissioned native assets. Preserve
API/session/error/idempotency contracts and record each false friend explicitly.
DOM bridges can stage specialized content but cannot pretend every browser library
is native. Test actual iOS/Android input, permission denial, deep link/back, offline
and accessibility before calling the migrated flow complete. Payments/vendor policy
requires current official target policy evidence; no universal provider or fee rule.

## Experimental module macros

Migration is conditional, not a stable automatic rewrite. Verify paired macro and
ExpoModulesCore support in installed packages, build configuration and deployment
target. Maintain an API map of JS names, events/payloads, defaults/requiredness,
static/class placement, queue/actor and errors. Preserve unsupported DSL rather
than force-converting it. Check for duplicate Name/registration/events/hooks and
changed pre-first-await behavior. Compile native code, resolve module in the running
app and roundtrip TS/native sync/async/event/view behavior. No macro/compiler mode
change is implied by a missing API. Retain old implementation and recovery until
that matrix passes. [Runtime](../../language-best-practices/references/mobile/expo-runtime.md)
and [verification](../../tdd/references/mobile-verification.md) own the relevant checks.
