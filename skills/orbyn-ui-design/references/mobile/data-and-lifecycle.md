# Mobile data, connectivity and lifecycle

Reuse the actual cache/query/session owner. Scope cache keys by account/tenant,
resource, filters and relevant permission/version. Clear or invalidate credentials
and sensitive cache on sign-out; do not show the previous person's data as an
optimistic default. Connectivity can be unknown and a network link does not prove
the API is reachable. Retain visible pending/error/stale state and a deliberate retry.

Every effect captures owner+generation before starting. Consume AbortSignal at the
transport if supported, and also fence after await: cancellation alone cannot stop
a server effect or an adapter that ignores it. Route unmount, account change,
foreground/reconnect and user retry must supersede the prior attempt without
letting late success/error replace the current screen. Stop subscriptions and
owned timers when no longer relevant; coalesce foreground retries rather than
starting one per event. Never serialize credentials into fixture or cache keys.

For mutations carry a stable operation ID through retries, distinguish rejected,
committed and unknown outcomes, and reconcile before repeating an ambiguous write.
Keep drafts on offline/error; scope optimistic rollback to the matching version.
Native storage has its own persistence, encryption/backup and deletion contract.

Use installed Router loader APIs only when exports and runtime support match;
client loader data is not server authorization. A plain supported hook/query layer
is a valid alternative. API/server loaders must still validate session, input and
resource authority; avoid caching personalized responses as public artifacts.

## Executable example

The fixture `src/contracts.mjs` owns `createRecoveryController`; its transport
receives the current account and AbortSignal. `RecoveryScreen` subscribes to that
exact controller and disposes it on unmount. Delayed A completion after switch to B,
late failure, ignored abort, offline/retry and unmount are tested at that boundary.
The transport is synthetic, so these tests do not establish deployed API or mobile
radio behavior. Run the named native flow when claiming real foreground recovery.
Pair [async state](../async-state.md) with [mobile verification](../../../tdd/references/mobile-verification.md).

## Foreground and query adapter recipe

For an installed RN AppState interface, subscribe inside the component/effect and
remove that exact subscription during cleanup:

```tsx
useEffect(() => {
  const subscription = AppState.addEventListener('change', next => {
    if (next === 'active') refreshCurrentOwner();
  });
  return () => subscription.remove();
}, [refreshCurrentOwner]);
```

`refreshCurrentOwner` is the consumer's owner-aware, coalesced refresh function;
it must still fence account/route/generation and avoid duplicate mutations. Import
AppState from the installed `react-native`; do not create a process-wide listener
per render. First foreground may not imply a transition from background, so use
the actual lifecycle contract when distinguishing resume from initial load.

If the target already uses TanStack Query, inspect its installed version and pass
the query function's signal into the actual fetch (`fetch(url, { signal })`), include
account/tenant/resource in queryKey, and reset/remove sensitive scoped queries on
sign-out. Wire focusManager/onlineManager to one owned AppState/NetInfo adapter
only if those APIs exist in the installed packages. NetInfo can report unknown
connectivity/reachability; do not coerce unknown into demonstrated online access
or successful service health. Remove the exact subscriptions and let retry/cache
policy belong to the query owner. This recipe adds no Query/NetInfo dependency.
