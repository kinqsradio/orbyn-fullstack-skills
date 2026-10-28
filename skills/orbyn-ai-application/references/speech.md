# Provider-neutral speech lifecycle

Use for requested voice, dictation or read-aloud changes. Inspect the consuming
application's actual provider, protocol and supported browser/native surface.
Do not replace its vendor, install a socket service or start microphone capture
merely because this reference exists. UI owns consent and recovery; backend owns
credentials, admission and bounded effects.

## Capture and transport

Acquire capture/playback resources from the required user gesture/permission,
with an explicit owner and cleanup on cancellation, account change and teardown.
No auto microphone/playback on load. Record the actual capture sample rate, channel
count, encoding, frame size, transport and playback format separately. Requested
sample rate may not be granted. Resample using a supported implementation where
needed; validate frame alignment and container headers. Container bytes are not raw
PCM. Batch suits bounded one-shot dictation; streaming requires an actual interim-
latency need and justified connection/recovery complexity. Existing provider schema
and permission checks remain authoritative.

## Turns, transcripts and playback

Bind audio chunks, transcript updates and player work to current conversation,
turn and generation. Barge-in cancels old queued playback and rejects late old
chunks without globally blocking microphone input. Reconcile server cancellation
and unknown remote outcomes; a local stop cannot undo an accepted remote effect.
Create a message at the provider's committed turn boundary, then distinguish delta
from cumulative transcript updates. Keep finalized segments and one replaceable
interim tail so pauses/two utterances neither duplicate nor lose final words.
A final event is not interchangeable with arbitrary stream closure.

Read-aloud has one active message/player; switching messages stops previous work.
Extract intended prose from markup with the consumer's parser, preserving meaningful
citations/brackets and neutralizing only documented control tags. Do not speak
unfinished streaming text by default. Chunk long text at meaningful boundaries,
maintain order and bound prefetch. Cache identity includes permitted principal,
text revision, voice, speed, format and relevant provider/version; expire/revoke
with source access. No cross-voice or stale unauthorized audio reuse.

## Diagnostics and qualification

Use existing bounded redacted diagnostics for permission, capture, transport,
first-audio, decode/playback and underrun phases; counts/bytes/timing and suitable
level measurements can distinguish silence, echo and starvation. Do not log raw
audio, transcripts, tokens or one event per chunk by default. Exporter failure
must not break the business path. No unauthenticated log sink or production flag
is installed by this method.

First exercise controlled format, turn, partial/final, cancellation and stale-cache
fixtures. Then check the actual permitted audio surface and resource lifetime
before claiming integration support. Synthetic state/format tests do not qualify
microphone permissions, audible playback, native barge-in or a live provider.
