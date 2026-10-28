# Swift: contracts to preserve

## Resolve the target

Inspect Package.swift, resolved dependencies, Xcode/Swift language mode and deployment targets. Concurrency checking and SDK availability depend on that actual configuration.

## Apply at the affected boundary

- Use value/reference semantics deliberately and make ownership of escaping closures explicit. Apply weak references for real retain cycles, not mechanically to every closure.
- Respect actor isolation and Sendable contracts. Do not silence a demonstrated cross-actor mutation with unchecked annotations before fixing its owner.
- Treat cancellation as cooperative and keep child tasks attached to their intended lifecycle. A detached or unstructured Task requires explicit lifetime/error ownership.
- Keep UI state on its platform owner (often MainActor). Preserve throwing errors and avoid forced unwrap/try on external data. Codable decoding does not establish domain authorization.

## Worked failure and correction

An actor can still interleave work at await. For a save based on a revision:

1. Capture the revision before the asynchronous operation.
2. After await, verify the state still matches that revision.
3. Commit through the owning authority or reject/retry with a bounded policy.

Actor isolation prevents overlapping unsynchronized access; it does not make the
entire suspended operation an atomic transaction.

## Evidence to report

Use the supported toolchain build/checks and authorized target tests. A package build is not iOS interaction, device behavior or proof of freedom from logical races.

## Maintainability and checks

Keep actor/public API and SDK availability explicit. Revalidate state after suspension when another operation can change the invariant. Test a meaningful asynchronous interleaving or recovery boundary when authorized; do not silence isolation diagnostics with unchecked annotations or claim a package build qualifies device behavior.

## Primary references

Reviewed 24 October 2026. These independently written instructions and synthetic
examples are usable offline. The links identify semantics and update evidence;
verify compatibility with the project's target before using newer APIs.

[Swift concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/), [Swift ARC](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/).

## Semantic depth and asynchronous adapters

A struct copy copies stored values; a stored class reference still aliases its
instance. Copying `[Box]` or a struct containing Box is not a deep immutable snapshot.
Choose immutable value payloads or an explicit copy when isolation needs it. Resolve
`some` (one hidden concrete type) versus `any` (existential) at the actual API;
protocol requirements participate in witness dispatch, extension-only methods do
not gain dynamic dispatch merely because a concrete type shadows the name.
Keep noncopyable/transfer features gated to the declared compiler/language mode.

An actor can interleave after suspension. Capture generation/identity, await the
external work, then revalidate the invariant before mutation. An isolated method
is not an atomic transaction across await. Keep task groups bounded and drain/
propagate cancellation/errors; detached tasks need explicit completion/lifetime.
SwiftUI `.task(id:)` tracks view identity but adapters must still consume cancellation
and fence late callbacks. Do not attach long-lived work to a transient view without
an owner, and never infer that cancelling a task rolls back a remote write.

For callback bridges, a checked continuation must resume exactly once. Coordinate
callback, failure and cancellation through one synchronized state; cancellation
can arrive before continuation attachment. Store the winning result, detach under
the lock, resume after releasing it, and ignore later completions. `@unchecked
Sendable` requires an audited synchronization proof, not warning suppression.
Cancellation handlers cannot blindly call a nonisolated, unsynchronized UI owner.
Keep actor/thread requirements, pre-first-await execution and errors across native
module calls explicit. Use weak captures only for actual cycles; a weak owner
silently disappearing can also lose a necessary completion.

The original synthetic `tests/fixtures/mobile-ui-workflow/swift-contracts.swift`
compiles on the toolchain recorded in the verification report and exercises nested
reference aliasing, requirement/extension dispatch, actor generation and callback/
cancellation races. It does not qualify SwiftUI view lifecycle, a native module or
all possible thread interleavings. Use the target's supported Swift Testing/XCTest
and strict concurrency configuration; preserve its language mode during migration.
Measure allocation/ARC work before replacing safe abstractions with unsafe memory.
Privacy-aware logs should omit raw user data and stable secrets; actor safety is
not a license to capture telemetry.
