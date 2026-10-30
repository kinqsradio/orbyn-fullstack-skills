# Asynchronous UI state and recovery

Use when changing fetch/search/save flows, optimistic updates, subscriptions or
screen lifetime. Read the actual framework/lifecycle and shared domain contract.
Keep loading, domain progress and presentation state distinct; a view should not
invent its own durable operation lifecycle.

## Own each request and result

Identify the inputs, identity/scope, operation key or request generation, and
cleanup owner. A result may update the view only while it belongs to the current
request and resource. Cancel supported work on replacement/disposal, and reject
stale results independently when the underlying effect cannot be cancelled.
Cancellation does not roll back an already committed server write.

Example: search A starts, search B starts, B resolves, then A resolves. The visible
result must remain B. An abort request alone is insufficient if A's operation
ignores cancellation or completed before the signal; compare the current request
identity before applying its result.

Account changes and permission revocation also change ownership. Clear or fence
cached results according to the actual cache owner; a URL or component name alone
is not a tenant-safe cache key. Current server-side authority remains required.

## Preserve the person's work

For a failed save, retain the draft and original identity/version. Distinguish
local edit, pending submission, known committed result and unknown outcome. A
retry must reuse or reconcile the operation contract rather than duplicate an
external action. An optimistic update needs a defined conflict/rebase/rollback
owner and must not overwrite a newer confirmed update with an old snapshot.

Keep long-lived subscriptions and event listeners attached to the appropriate
lifecycle. Define reconnect ordering, duplicate handling and cleanup where relevant.
Avoid a second local domain-status store that continually synchronizes with the
canonical result. Platform focus, selection and expansion state can remain local.

When authorized, check the relevant out-of-order response, account/scope change,
failed-save recovery and disposal path at the actual renderer width. Inspect
keyboard/accessibility state for changed interactions. A screenshot or unit stub
alone does not establish the complete recovery flow or installed-native behavior.

Return state ownership, sequence/failure behavior, implemented recovery and actual
evidence. Use the backend owner for committed effects and the local language
guides for JS promises, Kotlin coroutines, Swift actors or other actual runtimes.

Reviewed 24 October 2026 against [AbortController's supported cancellation contract](https://developer.mozilla.org/en-US/docs/Web/API/AbortController).
The stale-result method and examples are independently authored and framework-neutral.

For turn-bound voice playback, transcript finalization and barge-in, use the provider-neutral [speech method](../../orbyn-ai-application/references/speech.md); actual capture permissions and native/audio surface require their own observation.

## Generation and transport lifetimes

Plugin generation, route identity and mounted screen identity are distinct leases.
A reload during await must fence callbacks even when a route name repeats. Do not
let a late persistence load replace newer in-memory state; compare generation and
operation identity at application time. A command reply does not imply all events
are delivered, and a snapshot is not an event barrier.

For a PTY surface, identify the owned terminal session independently from its PID.
Process exit can precede transport EOF; preserve pending output until the actual
stream ends. Enforce bounded buffers in bytes with explicit overflow/backpressure
and multibyte-boundary handling, not only character counts. Reconnect/resize/input
require current session ownership; PID reuse is not continuity. Windows paths,
keyboard protocol and EOF need their own actual-surface checks.

For reactive locale/theme/loading transitions, use
[localization and RTL](localization-rtl.md). A smaller Suspense boundary reduces
the affected region; it does not prevent suspension or prove focus continuity.

## Notification identity

Notifications observe an operation; they do not own the durable result. Keep stable
operation ID plus current attempt/generation and intended surface. Retry may update
the same notification; a late old success/error cannot overwrite the new attempt,
dismiss another surface, or duplicate the outcome. Remove subscriptions on unmount
without discarding a still-owned operation. Keep completed/error status available
in the task view after the toast disappears. Multiple notification surfaces are
legitimate when intentionally targeted. For an installed Sonner version inspect
its actual `toast` ID/update/promise/dismiss and toaster-target APIs; do not install
it or assert root-only mounting universally. No toast conveys authorization or
replaces field-level errors, recovery and accessible live feedback.

For goal/routine grouping, quiet no-change results and meaningful failure/decision
escalation, use the content owner's [attention method](../../orbyn-content-design/references/outcomes-and-attention.md#group-routine-results-around-the-decision).
It does not replace operation identity, delivery deduplication or durable review.
