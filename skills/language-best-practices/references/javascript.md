# JavaScript: contracts to preserve

## Resolve the target

Inspect package.json, lockfile, module type, engines and the actual browser/Node/worker target. Preserve CommonJS/ESM boundaries and supported syntax.

## Apply at the affected boundary

- Return or await every promise that belongs to the operation. A rejected Promise.all does not cancel sibling work; pass an AbortSignal to APIs that support it and settle owned work before releasing its resources.
- Do not pass an async callback to `forEach`: nothing waits for it and its rejections escape. Use `for...of` with await, or `await Promise.all(items.map(fn))`.
- Handle rejections. In Node, an unhandled rejection is raised as an uncaught exception by default and ends the process.
- Move CPU-heavy work off a latency-sensitive event loop when measurement justifies a worker. Async syntax does not parallelize CPU work.
- Validate network/storage input before domain use. Keep authorization at the effect, avoid executable HTML or string evaluation, and preserve URL and origin policy: check redirect targets and outbound hosts against an allowlist.
- Separate missing values from valid falsy values: `count ?? 10` keeps 0, `count || 10` does not. Send integers above 2^53 - 1 as strings, because JSON.parse rounds them.

## Worked failure and correction

A resource scope closes before an unreturned request completes:

```js
// Incomplete lifecycle: the caller cannot await the write.
function save(writer, payload) {
  writer.write(payload);
}
// The owning caller awaits this promise before closing writer.
async function save(writer, payload) {
  await writer.write(payload);
}
```

A detached task is valid only when another explicit owner handles its errors,
cancellation and shutdown; adding `void` does not create that owner.

## Traps to check

- `fetch` rejects on network failure, not on 404 or 500. Check `response.ok`, and pass a signal such as `AbortSignal.timeout(ms)` when the target supports it.
- Do not merge untrusted JSON recursively into plain objects: a `__proto__` key can pollute the prototype. Use a Map, an allowlist or a schema.
- For Node streams, a false `write()` result means wait for `drain`, not resubmit the accepted chunk. Use the `pipeline` API, awaiting its promise or checking its callback, and pass cancellation through supported signals.
- Inspect HTTP ownership before piping: error teardown can destroy the socket before a fallback response. Browser streams have their own API contract.
- Libraries return errors and leave logging and configuration to the application.

## Callbacks retained beyond a view

Inspect the installed cache/library's ownership and disposal semantics before
changing query options, selectors, pagination or metadata callbacks. A cache may
retain them after a component unmounts. Capturing a view accessor, DOM node or
old account client can then outlive its authority or throw on later use.

Synthetic options for a cache that outlives the view:

```js
function cachedPageOptions(loadPage, { accountId, projectId }) {
  // loadPage is an application-owned client, not a view-bound callback.
  // IDs here are plain validated snapshots, not reactive accessors or grants.
  return {
    key: ["pages", accountId, projectId],
    query: ({ signal }) => loadPage({ accountId, projectId, signal }),
    select: (rows) => rows.map(({ id, title }) => ({ id, title })),
  };
}
```

Keep current authorization at the service and actual effect; a cache key is not
permission. On account/project change, partition or invalidate results, replace
options under the real cache policy, fence old responses and cancel supported
work. Rebuild snapshots when their inputs change, and check transitive captures in
`loadPage`, selectors and wrappers as well as the visible literal.

Test by retaining the options, unmounting the view, then invoking the retained
query/selector: the old view accessor must not run. Switch account and confirm the
old result is not applied, and test revocation at the service boundary. A per-mount
observer callback is fine when its owner really unsubscribes it. Memory claims need
their own profiling evidence.

## Evidence to report

Use the configured runtime and lint/type checks for the touched module. A passing promise fixture does not prove browser rendering or cancellation of an unsupported underlying API.

## Primary references

Reviewed 24 October 2026: [MDN promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises), [Node packages/module boundaries](https://nodejs.org/api/packages.html).

Focused semantics reviewed 30 October 2026: [Node 22 stream backpressure/pipeline](https://nodejs.org/docs/latest-v22.x/api/stream.html).

Reviewed 1 November 2026: [Node 26 unhandled rejections](https://nodejs.org/docs/latest-v26.x/api/cli.html#--unhandled-rejectionsmode), [Node release status](https://nodejs.org/en/about/previous-releases) (22, 24 and 26 are LTS).
