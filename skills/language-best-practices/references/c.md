# C: contracts to preserve

## Resolve the target

Inspect the C standard, compiler/target flags, ABI, allocation conventions and platform APIs. A .h file may belong to C, C++ or a shared ABI; resolve its real owner.

## Apply at the affected boundary

- Pair every allocation/resource with its actual release owner. Define pointer length, capacity, nullability and lifetime at each function/FFI boundary.
- Check range and multiplication/addition overflow before allocating or indexing. sizeof a pointer is not the pointed-to object size; signed overflow is not a portable wrapping contract.
- Keep byte buffers distinct from NUL-terminated strings. Check snprintf return values and capacity; a bounded call alone does not prove the result was complete.
- Use one understandable cleanup path for partial initialization. Synchronize shared invariants with the platform's atomics/locks; volatile is not thread synchronization.

## Worked failure and correction

Check an externally supplied element count before allocation:

```c
if (count > SIZE_MAX / sizeof *items) {
    return RANGE_ERROR;
}
items = malloc(count * sizeof *items);
```

Define the zero-count contract, handle allocation failure and release successful
allocation exactly once. This is an original fragment, not a complete allocator.

## Evidence to report

Use the actual compiler warnings and authorized sanitizer/behavior checks for bounds and cleanup. Sanitizers observe executed behavior and do not prove absence of undefined behavior.

## Maintainability and checks

Keep public ABI ownership, capacity/length/error conventions and partial cleanup
consistent. For a nonzero resize, assign `realloc` to a temporary: failure leaves
the original allocation valid, so overwriting its only pointer leaks it. On success
use the returned pointer and invalidate old aliases. Handle zero size separately
under the target standard/library; do not generalize old realloc-zero behavior
to C23. Check overflow before computing the requested bytes.

## Primary references

Reviewed 24 October 2026. These independently written instructions and synthetic
examples are usable offline. The links identify semantics and update evidence;
verify compatibility with the project's target before using newer APIs.

[CERT allocation rule](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/memory-management-mem/mem35-c/), [Clang undefined-behavior sanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html).

Focused semantics reviewed 30 October 2026: [SEI zero-size allocation](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/recommendations/memory-management-mem/mem04-c/), [C23 draft N3096 7.24.3.7](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3096.pdf).
