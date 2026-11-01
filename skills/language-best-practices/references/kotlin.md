# Kotlin: contracts to preserve

## Resolve the target

Inspect Gradle/Kotlin plugin versions, JVM/Android/native targets and kotlinx.coroutines version. Distinguish language features from coroutine-library and platform lifecycle features.

## Apply at the affected boundary

- Validate Java platform types at their boundary; avoid !! on external state. val does not make its referenced object immutable, and data-class copy is shallow.
- Use a lifecycle-owned CoroutineScope and structured children. Do not replace request/screen ownership with GlobalScope, runBlocking on a UI thread, or `launch(SupervisorJob())`, which severs the parent link.
- Rethrow CancellationException before translating routine failures. Broad Exception or Throwable catches and runCatching can turn cancellation into success.
- Protect shared state across dispatchers and keep blocking I/O off the main dispatcher. Model lifecycle variants with sealed types where supported; persist domain data separately from UI state.

## Worked failure and correction

A broad catch must keep cancellation observable:

```kotlin
try {
    lookup()
} catch (cancelled: CancellationException) {
    throw cancelled
} catch (failure: Exception) {
    reportUnavailable(failure)
}
```

CancellationException is not an IOException, so a catch limited to IOException needs
no rethrow and is the better choice when it covers the real failures. The enclosing
lifecycle owns this coroutine.

## Traps to check

- Suspending calls in `finally` fail once the coroutine is cancelled. Wrap required suspending cleanup in `withContext(NonCancellable) { ... }`; never `launch(NonCancellable)`.
- `withTimeout` throws TimeoutCancellationException, a CancellationException. An uncaught timeout in `launch` ends quietly without failing the parent; use `withTimeoutOrNull` when a timeout is a result.
- `withTimeout` cannot stop blocking code, and can discard a resource returned from its block. Use `runInterruptible` for blocking JVM calls, and close resources inside the block.
- A cold `flow {}` runs again per collection, potentially repeating effects. Share it only with an explicit scope and replay policy.
- StateFlow conflates by equality: mutating the same object hides a change, and slow collectors skip states. Publish immutable replacements, and do not use it as an every-event queue.
- `update` lambdas may rerun under contention, so keep external effects out of the transform.

## Evidence to report

Use the configured Gradle tasks, existing coroutine test facilities and target-specific authorized tests. A JVM unit test does not establish Android lifecycle, native interop or installed-device behavior.

## Primary references

Reviewed 24 October 2026: [Kotlin structured coroutines](https://kotlinlang.org/docs/coroutines-basics.html), [Kotlin coroutine errors](https://kotlinlang.org/docs/exception-handling.html).

Focused semantics reviewed 30 October 2026: [Cold Flow](https://kotlinlang.org/docs/coroutines-flow.html#cold-flows), [StateFlow equality](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/), [update retries](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html).

Reviewed 1 November 2026: [withTimeout](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout.html), [NonCancellable](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-non-cancellable/), [Kotlin releases](https://kotlinlang.org/docs/releases.html) (2.4.21 was latest stable).
