# Mobile engineering routing

Use the user's goal and the target's manifest, lockfile, app configuration, native
build files and instructions. Record Expo SDK, React, React Native, Router,
architecture, package manager, supported OS/deployment versions and whether native
directories are generated, manually maintained or mixed. Directory presence does
not settle ownership. No SDK or dependency installation follows from this read.

| Actual request | Read only the relevant owner |
| --- | --- |
| Expo dependency or explicit Expo execution | [Runtime](../../language-best-practices/references/mobile/expo-runtime.md) |
| Native screen, routing, media or local data | [Native UI](../../orbyn-ui-design/references/mobile/native-ui.md), [navigation](../../orbyn-ui-design/references/mobile/navigation.md), [data](../../orbyn-ui-design/references/mobile/data-and-lifecycle.md) |
| Motion, gestures or keyboard synchronization | [Mobile motion](../../orbyn-ui-design/references/mobile/motion.md); ordinary web motion stays at [UI motion](../../orbyn-ui-design/references/motion.md) |
| Module, DOM bridge, brownfield or web migration | [Mobile boundaries](../../architect/references/mobile-boundaries.md) |
| Upgrade, native generation or dev client | [Build and upgrade](../../orbyn-ci-design/references/mobile/build-and-upgrade.md) |
| EAS-only delivery of native iOS/Android code | [Distribution](../../orbyn-ci-design/references/mobile/distribution.md); no Expo runtime migration |
| OTA, release health, workflows or hosting | [Updates](../../orbyn-ci-design/references/mobile/updates-and-health.md), [workflows](../../orbyn-ci-design/references/mobile/workflows-and-hosting.md) |
| Expo Router API authority | [API routes](../../orbyn-backend-design/references/expo-api-routes.md) |
| Requested screen/native evidence | [Mobile verification](../../tdd/references/mobile-verification.md) |

A generic mobile technology choice goes to the existing stack-selection owner.
Bare RN, Swift and Kotlin work keep their own toolchain; mobile web uses the
[web input guide](../../orbyn-ui-design/references/mobile-web.md). An Expo example
is not permission to scaffold another app, replace styling, or rewrite navigation.

## Iteration and simulator session

Use a development binary for live source iteration when the change needs native
modules; use Expo Go only when its installed SDK and included modules fit. A static
artifact must match source and its native fingerprint/runtime, platform and device
architecture. Record app/bundle ID, source ref, build ID/profile, binary hash when
available, environment and intended screen. Start with existing project commands.

For local or authorized remote simulators, record the exact session/device ID,
launcher/owned PID, app instance, logs, preview URL, deep link and expiry. A preview
browser URL is not the simulator deep link. Tokens stay in ignored task-local
dotenv/config, never screenshots, logs or commits. Remote session creation, paid
time and artifact uploads require applicable authority; unavailable access is a
blocked cell, not a pass. Keep previews alive through review and hand off their
lifetime before cleanup. Stop only owned sessions/processes; never kill all adb,
qemu, port listeners or another contributor's device to clear a stale session.

Diagnose launch failure in order: device/OS/architecture; install identity; binary
native modules and permissions; Metro URL and network for dev builds; requested
route and logs; native crash report and matching symbols. Reuse the session only
if identity still matches. Capture the requested flow after navigation and settle,
including error/cancel/retry; a home screen screenshot cannot qualify it.

## Example selection and migration

Choose canonical examples pinned to the target SDK and capability, read the real
package/config/native dependencies, and note where demo assumptions differ from
production authentication, persistence, routing and access. Reach a runnable native
shell early in web migration, then replace a high-value screen through the same
API/session contract. A compile-only milestone leaves actual touch, keyboard,
permissions, back navigation, offline recovery and both platform cells open.

[Selected source record](../../orbyn-ui-design/references/mobile/sources.md)
identifies revision/license and the complete source disposition map. This guide is
usable offline; moving documentation remains a freshness check, not installed API proof.
