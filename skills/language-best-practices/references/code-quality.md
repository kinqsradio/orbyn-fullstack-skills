# Code quality baseline

Apply this to any code you write or review, then read the language guide. Project rules and established local patterns come first. Examples use neutral pseudocode.

## Fit the surrounding code

Read the neighbouring files and their tests before writing. Match their naming, error style, layout and helpers.

- Do: extend the retry helper the client already uses.
- Avoid: a second helper in the style you prefer. Propose style changes separately.

## Name for the reader

Name by domain meaning and include units.

- Do: `timeoutMs`, `isExpired`, `pendingInvoices`.
- Avoid: `data`, `tmp2`, `flag`, `handleStuff`, or a bare `timeout`. If a name needs "and", the code has two jobs.

## One responsibility, small interfaces

Give each unit one reason to change, and ask callers only for what it uses. Judge by [how easily a reader follows it](../../architect/references/principles/minimize-reader-load.md), not line counts.

- Do: `previewOrder(order)` and `submitOrder(order)`.
- Avoid: `process(order, dryRun, skipTax, notify)`. Each flag doubles the paths to test.

## Remove rather than layer

Fix the rule where it lives, then delete what compensated for it. See [subtract before you add](../../architect/references/principles/subtract-before-you-add.md) and [migrating callers](../../architect/references/principles/migrate-callers-then-delete-legacy-apis.md).

- Do: correct the parser and remove the caller's workaround.
- Avoid: a wrapper, option or `if legacy` branch that keeps both paths alive.

## Keep the cause in errors

Handle an error only where you can act on it. Otherwise add context and propagate it.

- Do: `throw SyncError("fetch invoice " + id, cause: err)`.
- Avoid: `catch (e) { return null }`. The caller cannot tell "not found" from "database down".
- Avoid: empty catches, and catch-alls that turn failure into success. When ignoring an error is correct, such as best-effort cleanup after a reported failure, say why in a comment.

## Release what you acquire

Give every file, connection, lock, timer, subscription and temporary path one owner that releases it on success, failure and cancellation.

- Do: use the language's scope construct (`with`, `using`, `defer`, RAII) straight after acquiring.
- Avoid: `close()` on the last happy-path line, where an early return leaks it.
- Do: bound network calls with timeouts, and bound queues, caches and retries.

## Concurrency and shared state

Prefer one owner and passing values. When state must be shared, protect the whole invariant. See [backend design](../../orbyn-backend-design/SKILL.md) for durable effects and [idempotent operations](../../orbyn-backend-design/references/principles/make-operations-idempotent.md) for retries.

- Do: one atomic compare-and-set, or one lock across read, check and write.
- Avoid: `if not exists(key): create(key)` as two steps, which races.
- Avoid: holding a lock across I/O or callbacks, or taking two locks in different orders.
- Avoid: background work with no owner to wait for it, cancel it and see its errors.

## Validate at the boundary

Parse input once where it enters, including requests, files, environment and model output. Pass typed values inward and check authority at the effect, following [boundary discipline](../../orbyn-backend-design/references/principles/boundary-discipline.md).

- Do: reject malformed, oversized and out-of-range values with a specific error.
- Do: bind SQL parameters and pass process arguments as a list.
- Avoid: building SQL, shell, HTML or file paths by joining input strings.
- Avoid: trusting a client-supplied role or price.

## Keep secrets out of code and logs

- Do: read secrets from the configured store at runtime, and commit only placeholders.
- Do: log a key ID, never the key.
- Avoid: logging whole requests, headers, tokens or connection strings.
- Avoid: treating deletion as a fix. Rotate a committed secret; it stays in history.

## Log for the person on call

Say what failed, for which entity and what happens next. Libraries return errors; applications configure logging.

- Do: `warn("invoice sync retry", invoiceId, attempt, delayMs)`.
- Avoid: `log("here")`, `log("error")`, per-item logs in hot loops, and one failure logged at every layer.

## Add dependencies deliberately

Check the standard library and existing dependencies first.

- Do: confirm the exact package exists, then check maintenance, licence and transitive weight. Install through the lockfile and state why in the change.
- Avoid: a package for one small helper, a second library for a solved job, or a name recalled from memory.

## Comment the why

Follow [source comments](../../unslop/references/source-comments.md).

- Do: `// Retry once: the vendor returns 409 during failover.`
- Avoid: `// increment i`, commented-out code, and comments left stale by your change.

## Change tests with behaviour

Follow [tdd](../../tdd/SKILL.md). Unless the user or project excludes tests, a behaviour change includes a test that fails without it; a bug fix starts from a failing regression when practical.

- Do: assert observable results, including empty, boundary and failure cases.
- Avoid: asserting only that a mock was called, fixed sleeps, or editing an expected value just to pass.

## Delete dead code

Search callers first, including reflection, configuration and public APIs.

- Do: remove the imports, flags and helpers your change orphaned.
- Avoid: `_unused` renames and "removed" comments. Report unrelated dead code instead of mixing it in.

## Keep the diff small, then review it

Give each change one purpose. Read the full diff as a reviewer before finishing.

- Do: check that every hunk is needed, debug output is gone, failure paths work and all callers moved.
- Do: run the formatter and relevant checks your task authorizes, then report what you ran and skipped under [prove it works](../../orbyn-workflow/references/principles/prove-it-works.md).
- Avoid: reformatting untouched lines, drive-by renames, or claiming success from a clean compile.
