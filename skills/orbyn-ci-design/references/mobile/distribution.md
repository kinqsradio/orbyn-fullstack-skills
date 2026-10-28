# Native distribution and App Clips

Inventory source/lock, bundle/package ID, team/project, platform, version/build,
signing profile/entitlements, build profile/environment, artifact hash and intended
store/track. EAS can deliver a native-only app without adding Expo runtime.
Use installed CLI help and selected platform documentation for command syntax;
never auto-enroll signing, upload or submit just to validate guidance.

## State and operation recipe

| Step | Concrete evidence |
| --- | --- |
| Build | Actual Release artifact, supported architecture/min OS, matching config and embedded bundle |
| Install/launch | Named simulator/device/build, Metro stopped, requested critical flow and permission recovery |
| Upload | Actual destination and upload/build processing ID; upload accepted is not store approval |
| Internal/TestFlight | Processing/test availability, tester group and actual installed build; internal vs external review distinct |
| Submit | App/version/track, metadata/privacy declarations/screenshots/review notes and submission receipt |
| Approve/roll out | Store decision, phased rollout/track state, owner and recovery action |
| Observe | Cohort/window/denominator and reported failures; availability is not demonstrated healthy usage |

For EAS inspect `eas build --help`, profile in eas.json, and existing account/project
identity; only within explicit effect scope trigger build, select actual build ID,
then inspect `eas submit --help` and configured submission profile. Pin the artifact
instead of submitting an ambiguous latest build. Retain failed processing/review
and reconcile an unknown upload outcome before retrying. Native Xcode archive/
Organizer or Gradle bundle delivery keeps its own signing and store path.

For Apple verify bundle/version/build, signing/team and distribution entitlements,
privacy manifests, usage descriptions and required capabilities; TestFlight beta
review differs from App Store review. For Google verify applicationId/versionCode,
AAB/signing, service-account scope, testing/production track, rollout fraction,
country/access and declarations. Do not log credentials or upload key material.
Metadata has its own owner: localized names/descriptions/keywords, real screenshots,
privacy/support URLs, review contact and truthful capability claims. Changing copy
cannot manufacture approved platform policy compliance. Verify current rules for
payments and restricted capabilities before giving commercial/legal guidance.

## App Clip target

Treat the Clip as a distinct target with parent association, bundle identifier,
provisioning/entitlements, invocation URL/domain, associated-domain/AASA entries,
size/distribution constraints and minimum OS. Verify the parent app association,
invocation path and installed-vs-not-installed behavior. Give the Clip only needed
permissions; copying all parent entitlements is wrong. Any native module needs
Clip-compatible API/linking/resource size and must compile/run in the Clip target,
not just the full app. Test denied permissions, unavailable full-app handoff,
transient storage and activation. Current store size/policy limits are versioned
facts, so inspect official target rules rather than hardcoding a timeless number.

[Mobile verification](../../../tdd/references/mobile-verification.md) records
which native/store cells were actually exercised. No actual upload, credential
creation, telemetry enrollment or production change is required to qualify this text.
