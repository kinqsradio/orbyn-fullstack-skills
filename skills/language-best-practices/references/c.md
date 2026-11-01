# C: contracts to preserve

## Resolve the target

Inspect the C standard, compiler/target flags, ABI, allocation conventions and platform APIs. A .h file may belong to C, C++ or a shared ABI; resolve its real owner.

## Apply at the affected boundary

- Pair every allocation and resource with its release owner. Define pointer length, capacity, nullability and lifetime at each function/FFI boundary.
- Check range and overflow before allocating or indexing. sizeof a pointer is not the pointed-to object size, and signed overflow is undefined rather than wrapping. On C23 targets, `ckd_mul` from `<stdckdint.h>` reports overflow.
- Keep byte buffers distinct from NUL-terminated strings. Check snprintf's return value: a result at or above the capacity means truncation.
- Use one cleanup path for partial initialization, usually `goto cleanup` releasing in reverse order. Synchronize shared invariants with atomics or locks; volatile is not thread synchronization.

## Worked failure and correction

Check an externally supplied element count before allocation:

```c
if (count > SIZE_MAX / sizeof *items) {
    return RANGE_ERROR;
}
items = malloc(count * sizeof *items);
```

Define the zero-count contract, handle allocation failure and release a successful
allocation exactly once. This is a fragment, not a complete allocator.

## Traps to check

- Never pass input as a format string: use `printf("%s", name)`, not `printf(name)`.
- `strncpy` does not terminate the destination when the source fills it. Prefer `snprintf`, or terminate explicitly.
- Comparing signed with unsigned converts the signed value: `-1 < 1u` is false. Convert after a range check.
- Pass `unsigned char` values to `<ctype.h>` functions. A negative plain `char` is undefined.
- Read `errno` only after a call has reported failure.
- Use `memmove` for overlapping ranges; `memcpy` overlap is undefined.
- Assign `realloc` to a temporary: on failure the original stays valid, so overwriting its only pointer leaks it. On success, invalidate old aliases.
- Handle zero size separately: `realloc(ptr, 0)` is undefined in C23.

## Evidence to report

Use the actual compiler warnings (for example `-Wall -Wextra -Wconversion` where configured) and authorized sanitizer/behavior checks for bounds and cleanup. Sanitizers observe executed behavior and do not prove absence of undefined behavior.

## Primary references

Reviewed 24 October 2026: [CERT allocation rule](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/memory-management-mem/mem35-c/), [Clang undefined-behavior sanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html).

Focused semantics reviewed 30 October 2026: [SEI zero-size allocation](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/recommendations/memory-management-mem/mem04-c/), [C23 draft N3096 7.24.3.7](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3096.pdf).

Reviewed 1 November 2026: [`<stdckdint.h>` (C23)](https://cppreference.com/c/header/stdckdint).
