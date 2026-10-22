# Review a concrete contract

Pin the source/candidate and intended behavior. Trace affected callers and storage,
then look for an actual scenario that violates ownership, authority, freshness,
ordering, cancellation, recovery or public compatibility.

Each finding needs a tight location, triggering state, consequence and correction
direction. Separate reproducible defects, evidence gaps and optional improvements.
Verify allegations against current source; a source name or scanner label is not
proof. Respect read-only review scope. A clean source review is not native UX,
live-provider or production acceptance evidence.
