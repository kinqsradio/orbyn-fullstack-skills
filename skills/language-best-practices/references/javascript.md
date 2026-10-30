# JavaScript: contracts to preserve

## Resolve the target

Inspect package.json, lockfile, module type, engines and actual browser/Node/worker target. Preserve CommonJS/ESM boundaries and supported syntax.

## Apply at the affected boundary

- Return or await every promise that belongs to the operation. A rejected Promise.all does not cancel sibling work; propagate an AbortSignal to APIs that support it and settle owned work before releasing its resources.
- Keep CPU-heavy work off latency-sensitive event loops when measurement justifies a worker. Async syntax does not parallelize CPU work.
- Validate network/storage input before domain use. Keep authorization at the effect, avoid executable HTML/string evaluation and preserve URL/origin policy.
- Separate missing values from valid falsy values. Choose nullish defaults deliberately; preserve numeric/serialization limits at API boundaries.

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
cancellation and shutdown; adding void does not create that owner.

## Evidence to report

Use the configured runtime and lint/type checks for the touched module. A passing promise fixture does not prove browser rendering or cancellation of an unsupported underlying API.

## Maintainability and checks

Keep module exports and ESM/CommonJS boundaries deliberate; preserve adapter
errors and current-request identity; the application owns logging/configuration.
For Node streams, honor backpressure instead of queueing unlimited writes.
A false `write()` result means wait for drain, not resubmit the accepted chunk.
Use the supported `pipeline` API, awaiting its promise
or checking its callback; pass cancellation through supported signals and handle
errors/cleanup. Inspect HTTP ownership before piping: error teardown can destroy
the socket before a fallback response. Browser streams use their own API contract.

## Callbacks retained beyond a view

Inspect the installed cache/library's ownership and disposal semantics before
changing query options, selectors, pagination or metadata callbacks. A cache may
retain them after a component unmounts. Capturing a view accessor, DOM node or
old account client can then outlive its authority or throw on later use. A closure
does not necessarily retain every surrounding variable; naming it or moving it
without changing captured dependencies proves nothing about lifetime or memory.

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
permission. On account/project change, partition/invalidate results and replace
options under the real cache policy, fence old responses and cancel supported
work. Rebuild snapshots when their inputs change; a one-time snapshot must not
silently disable required reactivity. Check transitive captures in `loadPage`,
selectors and wrappers as well as the visible options literal.

A discriminating fixture retains options, unmounts/disposes the view, then invokes
the retained query/selector. The old view accessor must not run. Switch account
and confirm separate identity/no application of the old result; test revocation at
the actual service boundary. A per-mount observer callback is legitimate when its
owner really disposes/unsubscribes it. No blanket inline-closure ban, module-level
factory, query library or AST rule is required. These are lifecycle checks, not a
measured heap reduction; memory claims require their own profiling evidence.

## Primary references

Reviewed 24 October 2026. These independently written instructions and synthetic
examples are usable offline. The links identify semantics and update evidence;
verify compatibility with the project's target before using newer APIs.

[MDN promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises), [Node packages/module boundaries](https://nodejs.org/api/packages.html).

Focused semantics reviewed 30 October 2026: [Node 22 stream backpressure/pipeline](https://nodejs.org/docs/latest-v22.x/api/stream.html).
