---
name: automate-me
description: "Capture a working preference the user explicitly asks to keep in a reusable local skill, using the current conversation or user-selected examples. Use reflect for lessons from task evidence and orbyn-skill-creator for shared library skills."
---

# Automate me

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where guidance is missing.

Use only the conversation or records the user selected. Do not mine unrelated
sessions or run automatic historical corpus mining.

## Method

1. **Separate the signal.** Distinguish an explicit enduring preference from a one-off task constraint and from your own inference.
2. **Scope the rule.** Write a positive example and a nearby case where the rule should stay inactive before choosing its owner.
3. **Find the existing owner:** locate an existing skill for the workflow before creating one. Use repository policy for a shared workflow, a consumer-owned skill for company behavior, and a personal path only when explicitly requested. Public library contribution is a separate scope decision. Prefer a small edit over another overlapping mode skill.
4. **Write it.** Use the available skill-authoring guidance, concise descriptions and references loaded only when needed. Preserve useful defaults, tool permissions, task scope, existing authorization, notices and settings.
5. **Return** the exact changed owner and resulting file, the preferences it encodes, its non-trigger example and checks actually performed. If the user only asks for advice, return the proposed rule without writing it.

For “inspect exported PDFs,” when the user asks to encode a repeated export readback, encode the export artifact, the inspection step and what to report if the viewer is unavailable. Keep the rule beside the exporter rather than in three unrelated prompts. Preserve what the preference actually covers: a PDF readback rule should not require application builds for a prose edit.

## Conflicting examples

Prefer an explicit current choice over old inference, retain contradictory evidence and label weak confidence. One temporary platform exception does not establish a general preference. A repeated explicit correction can support a minimal scoped owner edit; missing artifact evidence or an unresolved conflict can justify no change.

## Side effects

Do not change global models, memory, global configuration, connectors, schedules or recurring tasks as a side effect; saving a preference authorizes none of them.
