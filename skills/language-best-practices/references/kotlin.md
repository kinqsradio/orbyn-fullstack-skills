# Kotlin: contracts to preserve

## Resolve the target

Inspect Gradle/Kotlin plugin versions, JVM/Android/native targets and kotlinx.coroutines version. Distinguish language features from coroutine-library and platform lifecycle features.

## Apply at the affected boundary

- Validate Java platform types at their boundary; avoid !! on external state. val does not make its referenced object immutable, and data-class copy is shallow.
- Use a lifecycle-owned CoroutineScope and structured children. Do not replace request/screen ownership with GlobalScope or runBlocking on a UI thread.
- Rethrow CancellationException before translating routine failures. Broad Throwable catches and runCatching can accidentally turn cancellation into success.
- Protect shared state across dispatchers and keep blocking I/O off the main dispatcher. Model lifecycle variants with sealed types where supported; persist domain data separately from UI state.

## Worked failure and correction

Keep cancellation observable while mapping a failed lookup:

```kotlin
try {
    lookup()
} catch (cancelled: CancellationException) {
    throw cancelled
} catch (failure: IOException) {
    reportUnavailable(failure)
}
```

The enclosing lifecycle owns this coroutine. Cleanup still belongs in finally/use
and must follow the coroutine library's cancellation contract.

## Evidence to report

Use the configured Gradle tasks and target-specific authorized tests. A JVM unit test does not establish Android lifecycle, native interop or installed-device behavior.

## Maintainability and checks

Keep domain state separate from framework lifetime and use existing coroutine
test facilities. A cold `flow {}` runs again per collection, potentially repeating
effects; share/state only with an explicit scope and replay policy. StateFlow
conflates by equality: mutating/reusing the same object may hide a change, and slow
collectors may skip intermediate states. Prefer immutable replacement for state;
it is not an every-event queue. `update` lambdas may rerun under contention, so
keep external effects out of the transform. Inspect the installed coroutines API.

## Primary references

Reviewed 24 October 2026. These independently written instructions and synthetic
examples are usable offline. The links identify semantics and update evidence;
verify compatibility with the project's target before using newer APIs.

[Kotlin structured coroutines](https://kotlinlang.org/docs/coroutines-basics.html), [Kotlin coroutine errors](https://kotlinlang.org/docs/exception-handling.html).

Focused semantics reviewed 30 October 2026: [Cold Flow](https://kotlinlang.org/docs/coroutines-flow.html#cold-flows), [StateFlow equality](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/), [update retries](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html).
