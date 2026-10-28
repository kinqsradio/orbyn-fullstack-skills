# OTA activation and cohort health

An update's eligible binary must have matching platform and runtime version and
all required native capabilities. Channel→branch→update mapping determines delivery;
it is not a direct channel field equality between arbitrary binary and update JSON.
Build/publish environment and profile are deployment provenance and intended-audience
checks, not substitutes for runtime compatibility. Record actual resolved mapping,
project, source, binary, platform/runtime, build profile/env and update group/ID.

## Activation recipe

Inspect configured updates URL, runtimeVersion policy, channel/header and installed
expo-updates behavior. For authorized service investigation use installed
`eas channel:view`, `eas branch:view`, `eas update:view` help/JSON and actual IDs,
not a moving latest record. Publishing or remapping needs its own effect authority.
A native module/config/entitlement change needs a compatible new binary; OTA cannot
supply missing native code. Check fresh launch, check/download, reload/next-launch
activation and fallback/rollback behavior on the intended Release binary. Downloaded
is not activated, and Expo Go/dev-client success is not release startup evidence.
Record preview-vs-production and incompatible-runtime negative controls.

## Update Insights and channel health

Use installed CLI's `eas update:insights <groupId> --json` or the `update:view
--insights --json` wrapper with an explicit selected group. Their payloads differ:
the wrapper nests update entries and insights; don't parse them as identical.
For `channel:insights`, select channel/runtime/window explicitly and paginate or
record limits. Keep per-platform series, group ID, timespan, complete inventory,
sample count, numerator and denominator with the report. Do not derive unique
people by adding per-platform users or embedded and OTA populations. Most-popular/
top-N updates may omit the tail; that is not complete OTA adoption.

Downloads, launches, unique users and error reports answer different questions.
A cumulative failure count divided by downloads is not automatically a crash rate.
Self-reported/delayed events and launch dispatch restrictions can censor failures.
No samples/partial access is unknown, not zero crashes. Compare same platform,
runtime, build/update cohort, time window and metric denominator. Set a justified
product release criterion and minimum exposure, not universal magic thresholds.
Investigate counterevidence before rollback and preserve missing series/errors.

## Observe setup and interpretation

Verify installed expo-observe and actual native binary support; Expo Go is not a
valid substitute for a module it lacks. The pinned source distinguishes SDK55
AppMetricsRoot/AppMetrics from SDK56+ ObserveRoot/useObserve and later integrations;
inspect current installed exports/types before choosing the wrapper. Wrap the actual
root once, mark interactive only when meaningful requested content/actions are usable,
and keep route instrumentation aligned with actual navigation. A splash-hidden time
is not necessarily task readiness. Rebuild when native integration changes.

Choose app startup/launch/TTI and route-navigation metrics separately; include actual
metric definition, percentile/count/window, app state, device, network and build/update
identity. Use installed `eas observe:metrics-summary`, `metrics`, `routes`, `events`,
`session`, `errors`, `event`, `versions` help for scoped reads. Respect each platform's
cursor and session event/log truncation. Follow a slow cohort into actual sessions,
then correlate JS/UI frame, requests and errors rather than infer root cause from
one high percentile. Keep native symbol/source-map identity for readable stacks.

Library integrations must be optional when the package is optional; initialize once,
retain opt-in/privacy filters, bounded event payloads and errors/warnings policy.
Never log tokens, text fields or private route params by default, and do not enroll
telemetry or upload diagnostics merely because a skill mentions setup. Synthetic
health controls validate the interpretation boundary only, not live EAS data.
