# Runtime and registry boundaries

## Admission, execution and recovery boundaries

For an asynchronous operation, distinguish accepted admission, actual execution,
committed outcome and recovery ownership. A process-local recovery marker cannot
fence another process. Use the existing durable owner where cross-process claims
require it; do not add a queue/database solely to rename local state. Define event,
reply and snapshot ordering independently: an event can precede its command reply,
and a storage load can resolve after newer state. Tests must place these events
in the adverse order and check the current owner before a late mutation applies.

## Registry selection and freshness

Define duplicate-key policy and selected implementation identity at registration,
not only at enumeration. Retain source/generation metadata so an ordered replacement
can be distinguished from an accidental shadow. Test the actual resolver after
replacement, deletion and source-target change; a cached catalog entry does not
prove the selected body or its nested data is current. Invalidate at the owning
boundary, preserving failures/unavailable sources instead of silently reusing stale
bytes as current. This is a generic registry contract, not a source-product setup
procedure or requirement for a new registry.
