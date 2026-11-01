# Go: contracts to preserve

## Resolve the target

Inspect go.mod language/toolchain directives, build tags, CGO and module boundaries. Use the supported compiler and gofmt; do not install an unrelated style framework. The `go` line changes semantics: per-iteration loop variables need 1.22, and collectable unstopped timers need 1.23. `sync.WaitGroup.Go` needs 1.25 and `errors.AsType` needs 1.26.

## Apply at the affected boundary

- Carry request context explicitly through blocking operations, and `defer cancel()` for every derived context. Every goroutine needs an owner, a completion path and shutdown behavior; a channel send can block forever after the receiver exits.
- Handle returned errors and wrap with context while preserving matching: `fmt.Errorf("load %s: %w", id, err)`. Use panic for programmer invariants only where project policy permits it.
- Close response bodies and other resources on every path, and bound external reads. A defer inside a long loop retains resources until the function returns, so move the loop body into a function.
- Treat slices, maps and pointers as potentially shared aliases. Synchronize the whole invariant, not individual reads. Define narrow interfaces at the consumer, not one per struct.

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

The caller still owns starting and joining workers and closing channels exactly once;
the snippet does not make an arbitrary worker pool leak-free.

## Traps to check

- `http.Get` and `http.DefaultClient` have no timeout. Use a request context deadline or a client with `Timeout` set.
- Writing to a nil map panics; reading one does not.
- `append` may write into a shared backing array. Use `slices.Clone` before appending to a slice you do not own.
- After iterating `database/sql` rows, check `rows.Err()`: a failed loop otherwise looks like a short result.
- An `error` holding a typed nil pointer is not nil. Return a literal `nil` on success.
- Do not copy a used Mutex, Once or WaitGroup, including through containing structs or value receivers.
- Keep exported APIs deliberate and use internal packages where they fit.

## Evidence to report

Use configured package tests and go vet when authorized. The race detector observes executed paths; a clean -race run is not proof of race freedom or logical atomicity. On 1.27, the `goroutineleak` profile reports some blocked goroutines, and misses those reachable from globals or runnable goroutines.

## Primary references

Reviewed 24 October 2026: [Go review comments](https://go.dev/wiki/CodeReviewComments), [Go race detector](https://go.dev/doc/articles/race_detector), [Go errors](https://go.dev/blog/go1.13-errors).

Focused semantics reviewed 30 October 2026: [Go nil-error FAQ](https://go.dev/doc/faq#nil_error), [sync ownership](https://pkg.go.dev/sync).

Reviewed 1 November 2026: [Go 1.22 loop variables](https://go.dev/doc/go1.22), [Go 1.23 timers](https://go.dev/doc/go1.23), [Go 1.25](https://go.dev/doc/go1.25), [Go 1.26](https://go.dev/doc/go1.26), [Go 1.27](https://go.dev/doc/go1.27), [net/http client timeouts](https://pkg.go.dev/net/http).
