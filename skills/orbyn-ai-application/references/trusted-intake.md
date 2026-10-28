# Qualify a consumer-owned report intake adapter

Use only when a consumer requests issue-to-thread/tracker automation. Shared
engineering guidance supplies no Slack/tracker service, credentials or standing
traffic authority. Keep the implementation and its actual provider contract with
the consuming app, not copied shared skills or internal foreign-host APIs.

## Admission and identity

Bind immutable source workspace/channel/thread/root/permalink and configured
producer identity. Recheck the parent exists and is accessible before authorized
writes; no sibling destination, fallback root post or operations timestamp can
replace it. Accept one valid configured verdict for that source; spoofed actors,
conflicting markers and linked prompts do not grant tool authority. Classify an
incoming bug, performance issue, request or question by evidence. Route ownership
from confirmed cause/configuration, not symptom guesses or inaccessible source.

Workers doing analysis must actually lack write credentials/capabilities. A prompt
ban with exposed posting tools is not isolation. Inspect the host's effective
permissions; if it cannot enforce the required separation, keep effects with the
local trusted owner or block that integration. Do not change global settings to
make the isolation claim true.

## Dedupe and effects

Use a stable source identity and operation key. Distinguish confident duplicate,
possibly related, weak resemblance and regression lead; uncertainty is not permission
to file/reopen. Repeated delivery of the same permalink cannot create another issue
or reply. Update only approved fields and preserve the recurrence/source link.
Before creation, know whether the adapter can compensate a failed source handoff.
If compensation is required but unavailable, stop before creation. After a failure,
cancel/close only the issue created by this run through supported semantics, read
back the outcome and retain unknown status. Do not delete unrelated issues, mint
a fresh identity or call uncertain compensation complete.

Bound one substantive reply, direct answer and follow-up window by actual authority.
Recheck destination, dedupe and stop state before the effect; unchanged repeated
triggers stay quiet. Source deletion or stop cancels dependent effects. A trigger,
trusted marker or green check never supplies message/merge/deploy permission.

## Qualify before enabling

Use disposable fake thread/tracker services and a controlled application journey
for parent deletion, spoofed/conflicting verdict, duplicate trigger, uncertain
write, failed reply/compensation, late result and stop. Capture actual requests,
state/readback and cleanup. Then qualify the actual specified provider/auth/schema
and app-control launch/doctor/drive/capture/record/cleanup path before real traffic.
Fake services do not qualify live Slack/tracker permissions or end-to-end intake.
No startup/recording/cleanup evidence means that adapter remains open.

For an existing fix or active owner, switch to verify-only rather than race it.
Use [existing-fix verification](../../how/references/reproduction.md#verify-an-existing-fix)
for matched baseline/patched observations; a bot diagnosis alone is not ownership
or proof of repair.
