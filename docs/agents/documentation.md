# Documentation ownership

`skills/` owns reusable instructions; `docs/agents/` explains how the library's
defaults work together. The consuming project owns product architecture, API,
operations and private policy. Keep those sources separate.

Update the owning contract once and migrate incoming links. Keep source attribution
in [provenance](../../provenance.json) and [notices](../../tools/THIRD_PARTY_NOTICES.md).
Do not copy private work records into this public repository. A durable public
example should use synthetic data and identify what it demonstrates.

Prefer an existing owner over a new policy file. Record a rationale only when it
will help a future decision. Validate actual links and commands without running
unrelated application builds. A static validation result is not live agent evidence.
