# Swift: contracts to preserve

## Resolve the target

Inspect Package.swift, resolved dependencies, Xcode/Swift language mode and deployment targets. Concurrency checking and SDK availability depend on that actual configuration, so preserve the language mode during migration.

## Apply at the affected boundary

- Use value/reference semantics deliberately and make ownership of escaping closures explicit. Use weak captures for real retain cycles only; a weak owner silently disappearing can lose a necessary completion.
- Respect actor isolation and Sendable contracts. Fix the owner of a demonstrated cross-actor mutation instead of silencing it. `@unchecked Sendable` requires an audited synchronization proof.
- Treat cancellation as cooperative and keep child tasks attached to their lifecycle. Keep task groups bounded and drain them. A detached or unstructured Task needs explicit lifetime and error ownership, and cancelling a task does not roll back a remote write.
- Keep UI state on its platform owner, often MainActor. Preserve throwing errors and avoid forced unwrap/try on external data. Codable decoding does not establish domain authorization.

## Worked failure and correction

An actor interleaves other work at await, so an isolated method is not an atomic
transaction. Capture the revision, then revalidate after suspension:

```swift
enum SaveError: Error { case stale }

actor DraftStore {
    private var revision = 0
    private var receipt: String?

    func edit() { revision += 1 }

    func save(_ write: @Sendable () async throws -> String) async throws {
        let expected = revision
        let result = try await write() // edit() can run during this await.
        guard revision == expected else { throw SaveError.stale }
        receipt = result
    }
}
```

The stale path means local state no longer matches. The remote write may still have
happened, so reconcile it or retry under a bounded policy.

## Traps to check

- `async` does not leave the current actor for CPU work, and `Task { }` inherits the enclosing isolation. Nonisolated async functions run on the caller's actor with `NonisolatedNonsendingByDefault` (SE-0461), otherwise concurrently; use `@concurrent` where that feature is available. Module default isolation (SE-0466) can make unannotated code MainActor. Read the build settings before moving work.
- A struct copy still aliases any stored class reference. Copying `[Box]` is not a deep snapshot; use immutable value payloads or an explicit copy when isolation needs one.
- `some` is one hidden concrete type and `any` is an existential. Extension-only methods do not gain dynamic dispatch when a concrete type shadows the name; protocol requirements do.
- Keep noncopyable and transfer features gated to the declared compiler and language mode.
- Keep String indices tied to their string. Characters are grapheme clusters; UTF-8 and UTF-16 offsets are different coordinates, so convert at the interop boundary.
- SwiftUI `.task(id:)` follows view identity, but adapters must still honor cancellation and fence late callbacks. Do not attach long-lived work to a transient view.
- Measure allocation and ARC cost before replacing safe abstractions with unsafe memory. Omit raw user data and stable secrets from logs.

## Callback bridges

A checked continuation must resume exactly once. Coordinate callback, failure and
cancellation through one synchronized state, because cancellation can arrive before
the continuation is attached. Store the winning result, detach under the lock, resume
after releasing it, and ignore later completions. A cancellation handler cannot call
a nonisolated, unsynchronized UI owner. Keep actor/thread requirements, pre-first-await
execution and errors explicit across native module calls.

## Evidence to report

Use the supported toolchain build, strict concurrency configuration and authorized Swift Testing/XCTest target tests. A package build is not iOS interaction, device behavior or proof of freedom from logical races.

This library's synthetic `tests/fixtures/mobile-ui-workflow/swift-contracts.swift`
exercises reference aliasing, requirement/extension dispatch, actor generation and
callback/cancellation races. It does not qualify SwiftUI lifecycle, a native module
or all possible interleavings.

## Primary references

Reviewed 24 October 2026: [Swift concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/), [Swift ARC](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/).

Focused semantics reviewed 30 October 2026: [Swift String coordinates](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/stringsandcharacters/).

Reviewed 1 November 2026: [SE-0461 async function isolation](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md), [SE-0466 default actor isolation](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md), both implemented in Swift 6.2. [Swift blog](https://www.swift.org/blog/) (Swift 6.4 released 15 September 2026).
