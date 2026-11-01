# Rust: contracts to preserve

## Resolve the target

Inspect Cargo.toml edition/rust-version, rust-toolchain, Cargo.lock, enabled features and target. Preserve the minimum supported Rust version and public API contracts. The edition changes drop order: from 2024, `if let` temporaries drop before `else`, so a lock held in the condition no longer deadlocks the `else`. A `cargo fix --edition` rewrite to `match` keeps the old timing; review each one.

## Apply at the affected boundary

- Express owned versus borrowed data deliberately. Trace lifetime and concurrency ownership before adding clone, Arc or a mutex to silence the borrow checker. `Arc` shares ownership, not synchronization of mutable contents.
- Use Result and meaningful error propagation for expected failures. Keep unwrap/expect at documented invariants, not on untrusted input or routine I/O. Use `.get()` where an index comes from input.
- An async future can be dropped at any suspension point. Cancellation does not roll back a committed effect; design retry identity and cleanup at the effect owner, and check cancel safety for each `select!` branch.
- Do not hold a blocking mutex guard across await, and move blocking work to the runtime's blocking pool.
- Keep unsafe/FFI small with explicit allocation, aliasing, alignment and lifetime invariants. Safe wrappers must uphold them for every caller.

## Worked failure and correction

Return a borrow tied to its real input instead of allocating only to satisfy a signature:

```rust
fn first_tag(tags: &[String]) -> Option<&str> {
    tags.first().map(String::as_str)
}
```

An owned String is appropriate when the value must outlive tags, including when the
function builds it locally. The decision is lifetime ownership, not a blanket rule
against allocation.

## Traps to check

- Arithmetic overflow panics in debug and wraps in the default release profile. Use `checked_add` and friends on sizes and values from input.
- `as` truncates integers silently: `1234u16 as u8` is 210. Use `u8::try_from(value)`.
- `let _ = mutex.lock()` releases the guard immediately. Bind `let _guard` to hold it.
- `Vec` capacity is not initialized length. Prefer push/extend/resize; unsafe `set_len(n)` requires n within capacity and every newly exposed element initialized.
- Keep public types and dependency exposure intentional, and avoid generic layers without real callers. Debug output must not reveal secrets.

## Evidence to report

Use configured cargo check/test, formatting and Clippy within authorized scope. Compilation proves neither unsafe-code soundness nor transactional cancellation safety. Test in release mode when overflow behavior matters.

## Primary references

Reviewed 24 October 2026: [Rust ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html), [Cargo rust-version](https://doc.rust-lang.org/cargo/reference/rust-version.html), [Rust unsafe](https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html).

Focused semantics reviewed 30 October 2026: [Vec set_len safety](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.set_len), [Arc thread safety](https://doc.rust-lang.org/std/sync/struct.Arc.html#thread-safety).

Reviewed 1 November 2026: [overflow and `as` casts](https://doc.rust-lang.org/reference/expressions/operator-expr.html), [Rust 2024 `if let` scope](https://doc.rust-lang.org/edition-guide/rust-2024/temporary-if-let-scope.html).
