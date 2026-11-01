# Java: contracts to preserve

## Resolve the target

Inspect Maven/Gradle wrapper, Java toolchain/release target and dependency locks. Verify records, sealed types and virtual-thread support against that target.

## Apply at the affected boundary

- Keep construction valid and expose explicit domain states; records do not validate fields or make referenced collections immutable.
- Use try-with-resources for owned AutoCloseable resources. Preserve the primary failure and suppressed close failures; garbage collection does not provide timely release.
- Propagate InterruptedException when the interface allows it. If translating it, restore the interrupt flag and preserve cancellation rather than retrying forever.
- Keep JDBC parameters, transaction boundaries and executor lifetime explicit. Do not expose persistence exceptions as domain results.
- Create one virtual thread per task and never pool them; limit access to a service with a Semaphore. They help I/O concurrency, not CPU throughput. Replace thread-local object caches with immutable shared objects such as `DateTimeFormatter`.
- Name charsets at contracts. UTF-8 is the default only from JDK 18, and `System.out` follows the console.

## Worked failure and correction

Translate interruption without losing the signal:

```java
try {
    worker.join();
} catch (InterruptedException failure) {
    Thread.currentThread().interrupt();
    throw new IllegalStateException("Join interrupted", failure);
}
```

Prefer propagating InterruptedException when callers can handle it directly;
translation belongs at an interface that requires it. A broad `catch (Exception)`
catches it too.

## Traps to check

- `==` compares references on String and boxed numbers. Use `equals`, and override `equals` and `hashCode` together. Do not mutate fields used by a map key.
- `new BigDecimal(0.1)` keeps the binary value; use the String constructor or `valueOf`, and choose scale and rounding deliberately. `equals` includes scale (1.0 differs from 1.00); use `compareTo` for numeric equality.
- `Collections.unmodifiableList` is a view of a list that can still change; `List.copyOf` is a snapshot and rejects nulls.
- `CompletableFuture.cancel(true)` does not interrupt its computation. Cancel through the owner of the underlying work.
- Before JDK 24, blocking inside `synchronized` pins a virtual thread to its carrier. From 24, pinning remains for native frames and class initialization; do not migrate locks on that basis alone.

## Evidence to report

Use the project wrapper and configured compiler/analyzers plus scoped authorized tests. Building on a newer developer JDK alone does not establish compatibility with the deployment release. Check `jdk.VirtualThreadPinned` events before claiming a pinning fix.

## Primary references

Reviewed 24 October 2026: [JLS 25 resource statements](https://docs.oracle.com/javase/specs/jls/se25/html/jls-14.html#jls-14.20.3), [JDK 25 Thread contract](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html).

Focused semantics reviewed 30 October 2026: [JDK 25 CompletableFuture cancellation](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html#cancel(boolean)), [BigDecimal](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/math/BigDecimal.html).

Reviewed 1 November 2026: [JDK 25 virtual threads guide](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html), [JEP 491 pinning](https://openjdk.org/jeps/491), [JEP 400 UTF-8 default](https://openjdk.org/jeps/400), [JDK release dates](https://openjdk.org/projects/jdk/) (JDK 27 reached GA on 15 September 2026).
