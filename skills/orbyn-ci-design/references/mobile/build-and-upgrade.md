# Expo build and upgrade sequence

Start from [runtime ownership](../../../language-best-practices/references/mobile/expo-runtime.md).
Record source/lock, SDK/React/RN, native ownership, platform/toolchain/build flavor,
config plugins, patches and known failures. A dependency install is not a native
binary upgrade. Keep a recoverable baseline and an owned disposable generation copy.

## Local decision sequence

1. Inspect package manager, installed Expo CLI help and SDK compatibility. For a
   supported npm project, `npx expo install --check` and a scoped Expo Doctor can
   diagnose drift; inspect commands before any fetching/execution. Preserve lockfile.
2. Upgrade one coherent SDK/React/RN/native set using that SDK's migration notes.
   Review patch rationale and APIs before removing patches. Do not auto-select latest.
3. Identify generated vs manual native code from config/history, not folder presence.
   Run prebuild only in authorized owned copies first; `--clean` deletes generated
   trees and must never erase manual edits. Compare plist/manifest/Pod/Gradle and
   plugin effects; preserve credentials, native work and other flavors.
4. Rebuild matching dev clients after native dependency/config changes. Verify JS
   startup, route/auth, permissions, media, modules and background/reconnect.
5. Build affected Release platforms and start with Metro stopped. Record actual
   artifact identity and unrun cells; restore coherent package/config/native state
   on rollback rather than only reverting one JS dependency.

## Concrete migration families

| Change | Preserve and verify |
| --- | --- |
| `expo-av`→audio | Session/category/interruption, recording permission, player lifecycle, position/loop and background policy; new hook/player API is not a mechanical rename |
| `expo-av`→video | Native surface/player ownership, fullscreen/PiP/platform support, track/subtitle selection, events and disposal; source asset identity and denied playback |
| JS tabs→native tabs | Installed NativeTabs exports/OS support, icons/badges/search/accessory, back/scroll-to-top, safe area, keyboard and web fallback |
| React Navigation→Router | URL/param/history/session contract and deep links; map layout/groups/routes, do not rename files and lose navigation semantics |
| React 19 | Installed RN peer support, ref/effect/Suspense behavior, actual StrictMode cleanup and hydration/web where relevant |
| React Compiler | Supported compiler/config, mutation/purity boundaries and measured behavior; no incidental enablement or presumed performance gain |
| New architecture | Supported RN/Expo/module compatibility, native libraries/autolinking, build flags, startup/events/gestures and rollback; old supported consumers are not silently migrated |

EAS build is a separate authorized service action. Verify account/project, platform,
profile, env, credentials and artifact before triggering. Local build typecheck,
simulator startup, cloud build, device installation and store release are different
receipts. [Distribution](distribution.md) and [updates](updates-and-health.md)
carry the artifact forward; no cloud/signing operation follows from editing this guide.
