# Go: contracts to preserve

## Resolve the target

Inspect go.mod language/toolchain directives, build tags, CGO and module boundaries. Use the supported compiler and gofmt; do not install an unrelated style framework.

## Apply at the affected boundary

- Carry request context explicitly through blocking operations. Every goroutine needs an owner, completion path and cancellation/shutdown behavior; a channel send can block after the receiver exits.
- Handle returned errors and wrap with context while preserving errors.Is/errors.As matching. Use panic for programmer invariants only where project policy permits it.
- Close response bodies/resources on every path and bound external reads. A defer inside a long loop retains resources until that function returns.
- Treat slices/maps/pointers as potentially shared aliases. Synchronize the whole invariant, not just individual reads; use narrow consumer-owned interfaces when a real boundary requires them.

## Worked failure and correction

A bounded worker send must notice that its request has ended:

```go
select {
case results <- result:
    return nil
case <-ctx.Done():
    return ctx.Err()
}
```

The caller still owns starting/joining workers and closing channels exactly once;
the snippet does not make an arbitrary worker pool leak-free.

## Evidence to report

Use configured package tests and go vet when authorized. The race detector observes executed paths; a clean -race run is not proof of race freedom or logical atomicity.

## Maintainability and checks

Keep packages/exported APIs deliberate, using internal packages and narrow
consumer interfaces where they fit, not one interface per struct. An `error` containing a typed nil pointer is
not a nil interface; return an explicit nil on success. Preserve wrapped error
identity. Do not copy used synchronization values such as Mutex, Once or WaitGroup,
including through containing structs/value receivers; share the intended owner.
A fresh zero-value mutex is valid, and a nil concrete pointer can still be nil.

## Primary references

Reviewed 24 October 2026. These independently written instructions and synthetic
examples are usable offline. The links identify semantics and update evidence;
verify compatibility with the project's target before using newer APIs.

[Go review comments](https://go.dev/wiki/CodeReviewComments), [Go race detector](https://go.dev/doc/articles/race_detector), [Go errors](https://go.dev/blog/go1.13-errors).

Focused semantics reviewed 30 October 2026: [Go nil-error FAQ](https://go.dev/doc/faq#nil_error), [sync ownership](https://pkg.go.dev/sync).
