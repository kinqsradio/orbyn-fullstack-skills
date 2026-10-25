# Third-party attribution

Original Orbyn-maintained material is MIT licensed by Anh Dang and contributors.
Adaptations retain the source copyright and license in each affected skill's
`LICENSE`. [provenance.json](../provenance.json) maps every skill to its origin and
distinguishes source adaptations from first-party integrations.

## pstack — Lauren Tan

Engineering adaptations derive from `pstack` in
[cursor/plugins](https://github.com/cursor/plugins/tree/74dd2291e8e37b12fd6dc49b2acbd655c6bdaf12/pstack),
revision `74dd2291e8e37b12fd6dc49b2acbd655c6bdaf12`.
Copyright (c) 2026 Lauren Tan. [Original MIT license](licenses/pstack-MIT.txt).
The source-to-local mapping is preserved in [skill-adaptations.json](skill-adaptations.json).
Orbyn's decision examples, authority boundaries and integration changes do not
remove the original author's credit. Full upstream source is not bundled here.

## REA — morluto

Five optional skills adapt
[morluto/rea](https://github.com/morluto/rea/tree/ccc7da309d7db385d5c6d73b0a3a8e093be33504),
revision `ccc7da309d7db385d5c6d73b0a3a8e093be33504`, package 6.7.0.
Copyright (c) 2026 morluto. [Original MIT license](licenses/rea-MIT.txt).
The historical source revision remains unchanged. The maintained local methods
and synthetic examples no longer require fetching the upstream skill bodies.
Selected investigation recovery/evidence guidance also draws on documentation
reviewed at `2250e67bc271c83f9e200ee298aa04a2457438a6`; the
[source record](../skills/reverse-engineer-anything/references/source-record.md)
distinguishes that review from an engine pin. No complete upstream manual or
runtime source snapshot is added. REA runtime, engines and dependencies are not
included or installed. Their own licenses apply when obtained separately.

## Reviewed inspiration and external guidance

Corey Haines's marketing/social skills and Anthropic's canvas-design were reviewed
to inform the social workflow. The original active methods were independently authored. Later offline additions
bundle unmodified text references: [Corey Haines social source record](../skills/social-content/references/source-record.md)
(MIT, Copyright (c) 2025 Corey Haines) and
[Anthropic canvas-design source record](../skills/social-preview/references/source-record.md)
(Apache-2.0, with the original license). Each record pins its revision and hashes.
No font binaries or artwork are included. See the [research distinction](research/social-content.md).
UI guidance retains its primary GOV.UK/W3C and other research citations in the
owning references. Citing an idea does not claim its author directly contributed
to Orbyn's code or endorses this library.


## Audit record tooling

The record schema, validators and synthetic validator fixtures retain their
[original MIT license](../skills/orbyn-security-audit/references/upstream/audit-records/LICENSE),
Copyright (c) 2025-2026 Cloudflare, Inc. Their
[pinned source metadata](../skills/orbyn-security-audit/references/upstream/audit-records/snapshot.json)
identifies the exact revision and original paths. The active workflow/protocol
are maintained separately under Orbyn ownership. No upstream skill entry point
or workflow text is bundled.

## Reviewed engineering ideas

Matt Pocock’s engineering ideas informed improvements to existing owners. No
upstream skill collection or workflow text is installed. The exact source/revision
is recorded in [provenance](../provenance.json) as reviewed inspiration. This
credit does not imply affiliation, endorsement or original authorship of an idea.
Downloaded research material under `openSrc/` remains local and ignored.

The contribution milestone also reviewed Jesse Vincent's `obra/superpowers`
(MIT), Sentry's `getsentry/skills` (Apache-2.0), and GitHub's
`awesome-copilot` (MIT). Its
[portable source record](../skills/orbyn-workflow/references/contribution-sources.md)
pins revisions and retains the reproduction brief's transitive source credit.
The new methods and examples are independently authored; no text, scripts or
upstream workflow collection from those reviews is redistributed. Existing
pstack source notices and portable licenses remain unchanged.
