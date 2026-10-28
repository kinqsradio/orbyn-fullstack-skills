# Mobile evidence and requested-screen verification

Freeze source/lock, fixture seed/hash, SDK/RN/React/native modules, architecture,
build profile/env, binary/build ID, device/OS and expected route/state. Name required
platform cells before capture. Bind every screenshot/log/interaction to that
candidate and requested flow. Root-screen, blank, error/dialog and stale/incompatible
binary controls must fail the claim. An Expo Go image cannot qualify a missing native
module; a successful bundle cannot prove actual control, keyboard or release behavior.

| Surface | Useful check | What remains distinct |
| --- | --- | --- |
| JS/controller | Late account response, ignored abort, error/retry, disposal and duplicate commit | Native transport/foreground/radio |
| Real RN/Router web | Operate same screen, route+ID, error/retry, long/RTL data and keyboard | iOS/Android layout/AT/back/keyboard |
| iOS simulator / Android emulator | Matching binary, requested screen, deep link/back, input/safe area, permission/error | Physical haptic, device performance, hardware/AT |
| Release host | Metro stopped, cold launch, embedded artifact/modules, brownfield correlated cancel/reopen | Store processing/approval/rollout and live health |
| Worklet gesture | Busy RN JS, UI movement, pointer/velocity/snap, one commit, cancellation/unmount | Other OS/device/library versions |
| Native module/macro | Actual compile/module lookup/TS-native call/event/view roundtrip and teardown | Unbuilt platforms and unsupported DSL |
| Store/OTA/cloud | Actual scoped receipt, compatible audience/artifact and activation/readback | Services not exercised by local fixtures |

Use task-owned simulator/device/session IDs and exact PIDs; keep shared devices,
adb, ports and foreign processes intact. Preserve failed captures/logs. If browser
or native access is denied, report that surface blocked; do not bypass permissions.
A screenshot plus static accessibility labels is not assistive-technology testing.

Adverse fixtures enter through the same real component/data interface. Include
minimized negative controls, not only a happy screenshot. Source/metadata validators,
deterministic connector stubs, browser rendering, native interaction and agent trials
are separate evidence levels. Missing a required platform remains incomplete.
[Evaluation](../../orbyn-skill-creator/references/evaluations.md) keeps baseline,
context, trusted result reuse and observed model configuration explicit.
