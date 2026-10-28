# Disposable mobile/UI workflow qualification

Original synthetic source, not an application template or a new shared skill.
Use an owned copy under ignored output. SDK55/Expo55.0.32, RN0.83.10,
React19.2.0 and Router55.0.16 are this fixture's selected versions, not consumer defaults.

From the library root, copy this directory to a **new** task-owned output path,
then run `npm ci --ignore-scripts --no-audit --no-fund` in that copy using a
task-local npm cache. Do not install into the tracked fixture. Review package
scripts/dependencies before native generation or compilation. Then run:

```sh
npm run typecheck
node --test contracts.test.mjs
EXPO_NO_TELEMETRY=1 CI=1 npx --no-install expo export --platform web
node --test browser.test.mjs
```

The browser test uses installed Chrome and the locked Playwright client, owns an
ephemeral loopback HTTP server/browser and closes only those resources. It operates
the actual RN/Router RecoveryScreen and the ordinary web motion fixture, saving
captures/trace under ignored output. Browser evidence does not qualify native UI.
The controller tests model no real API, tracker, store or EAS service.

Native iOS is a separate optional qualification: in the owned copy, inspect Expo
config, prebuild iOS without installing, inspect generated native/plugin/script
changes, install pods with a task-local CP_HOME_DIR, then build Release for a named
simulator with a task-local derivedDataPath and no signing. The fixture helper
`configure-ui-tests.rb` refuses any project outside this task's disposable
`output/mobile-ui-workflow/runtime/ios/OrbynWorkflowFixture.xcodeproj` path. It adds
only a new NativeWorkflowTests target; do not apply it to consumer code. The
`native-ui-tests.swift` test operates account switch, native switch, offline retry
and actual detail route and retains the screenshot in xcresult. Create a task-owned
simulator and use its exact UDID; never erase/kill another user's device. OS boot,
app launch, build and interaction failures remain distinct. A home/boot screenshot
cannot pass the requested detail flow. Actual test/run status is in the verification
report, not implied by these commands.

Compile `swift-contracts.swift` with the actual installed compiler, Swift6 strict
concurrency and an owned module cache/output. It qualifies selected macOS language
semantics, not SwiftUI/mobile/module behavior. `@unchecked Sendable` is confined to
the locked exactly-once adapter with explicit synchronization, not a policy default.

The prospective paired pilot protocol lists8tasks×3trials×2conditions. It contains
no model result, judge answers or active evaluator/provider configuration. The full
frozen evaluator/fixtures, tool admission, model/effort/processing acknowledgment,
inclusion/isolation evidence and retained failures are required before scoring.
