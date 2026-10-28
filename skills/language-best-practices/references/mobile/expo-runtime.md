# Expo runtime and dependency contract

Read the actual package/lock/config and native owners before choosing an API.
Record Expo SDK, RN/React/Router, Node, platform deployment targets, architecture,
Reanimated/Worklets/Gesture Handler versions and package manager. Check installed
exports/types and the matching SDK documentation. A newer upstream recipe cannot
establish compatibility with an older binary. Do not add Expo to EAS-only native work.

## Development, generated native and release

| Execution | Contract |
| --- | --- |
| Expo Go | Shared prebuilt native modules, SDK constraints; no arbitrary custom module |
| Development build | App-owned native binary with dev client; native dependency/config changes require rebuild |
| Release | Embedded bundle/native configuration, no dev server assumption; verify launch with Metro stopped |

Use the project's package manager and SDK-compatible dependency mechanism (for an
npm Expo project, inspect `npx expo install --check` before a scoped install).
Commands that fetch packages or generate native files are task actions, not setup
requirements for reading skills. Keep lockfile and actual binary identity together.
`expo config` may execute dynamic project configuration: inspect it before running
and avoid dumping secret values into evidence. `EXPO_PUBLIC_*` is client-visible.

Before prebuild, inspect ignored/tracked native trees, config plugins, patches,
Podfile/Gradle and release flavors. CNG configuration is source only when those
trees are demonstrably disposable; otherwise preserve manual edits and migrate
explicitly. Clean prebuild can erase work. Generate only in a disposable owned
copy first, compare semantic/native diffs and define recovery. New native modules,
entitlements, privacy declarations, deployment targets or architectures need matching
native builds; JavaScript export alone cannot qualify them.

## Native modules and views

For local capabilities prefer the target's existing module layout; standalone
packages have a separate API/peer/autolinking support contract. In a supported
Expo Modules DSL target, `Name`, `Function`/`AsyncFunction`, `Events` and view props
must match JS names and payloads. `requireNativeModule` failing is a binary or
registration problem, not a reason to silently substitute a web success stub.
Read [mobile boundaries](../../../architect/references/mobile-boundaries.md) for
config registration, lifecycle, brownfield and experimental macro migration.
Use the existing [Swift](../swift.md) and [Kotlin](../kotlin.md) contracts for
isolation, queues, nullability, errors and cancellation. Native callbacks must not
outlive their owner; stop observing when the last subscriber leaves.

## API gates

The synthetic fixture in `tests/fixtures/mobile-ui-workflow` deliberately selects
SDK 55 and basic RN controls/Router. It does not prescribe that SDK to consumers.
Universal `@expo/ui`, platform SwiftUI/Compose and drop-in components have distinct
exports/host requirements that evolve across SDKs: check installed declarations.
Reanimated 4/Worklets require supported native architecture and configured build
plugins; retain an existing compatible stack or use a supported alternative.
A language mode, compiler or architecture change is its own migration, never an
incidental fix for a missing symbol. [Build/upgrade](../../../orbyn-ci-design/references/mobile/build-and-upgrade.md)
owns the sequence and rollback; no engine/provider or global settings change is implied.
