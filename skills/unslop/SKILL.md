---
name: unslop
description: "Edit agent prose and documentation for clear factual communication while preserving the requested voice and evidence. Use orbyn-content-design for interface copy and social-content for posts."
---

# Unslop

## Edit the passage

1. Identify the reader, the requested outcome and the statements whose wording
   carries technical or evidential meaning.
2. Before shortening anything, mark what must survive: exact names, measured
   quantities, release state, caveats, attribution, uncertainty and the user's
   writing style or intended voice.
3. For a tutorial, how-to, reference or explanation, apply the conditional
   [document purpose method](../orbyn-workflow/references/explanation-and-recaps.md#technical-documents)
   before polishing sentences.
4. Edit one passage around its main point. Lead with the concrete result or
   action. Use familiar words and verbs, one main idea per paragraph and paragraph
   breaks that follow the reasoning. Add headings only when they help navigation.
   Keep terminology consistent with the owning product or API contract.
5. Replace vague claims with supported actions or outcomes. Remove filler,
   repetition, duplicated setup, inflated claims, forced contrasts and decorative
   formatting. Do not manufacture metrics or a numerical benefit, and do not remove
   evidence to make prose sound stronger.
6. Read the complete result as a whole, for meaning. A checklist of forbidden words
   cannot prove clear writing, and word-count reduction alone is not a quality
   measure.
7. Return the requested edited copy. Add an evidence note only where a factual gap
   affects publication.

Two cases to watch:

- “The export is ready” may be shorter but false if only HTML source was generated;
  retain the missing PDF inspection.
- A user's intentional humor or informal phrasing is not automatically filler.

## Scope and owners

Follow the consuming project's instructions and requested scope; use the
[portable defaults](../orbyn-workflow/references/project-policy.md) only where
guidance is missing.

- Product copy and labels: use [content design](../orbyn-content-design/SKILL.md).
  Do not rewrite user-authored product content as a side effect of UI simplification.
- Social posts: use [social-content](../social-content/SKILL.md) for post strategy,
  author voice, platform adaptation and carousel copy; this skill supplies the
  prose pass.
- Visuals: use [social-preview](../social-preview/SKILL.md) for rendered feed
  mockups, attached visuals and visual composition. Editing a caption does not
  require generating visual assets.
- Source comments: they explain non-obvious constraints and leave the next line to
  the code. When writing or reviewing them, read
  [source comments](references/source-comments.md).
