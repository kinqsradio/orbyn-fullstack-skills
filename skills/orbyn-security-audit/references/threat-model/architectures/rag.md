# Retrieval-augmented generation checks

Use for document ingestion, source permissions, retrieval, model context, citations and answers. Never invent a corpus, index, cache, tenant or tool from the label. Add [multi-tenant SaaS](multi-tenant-saas.md) only for an evidenced tenant boundary, and [agentic AI](agentic-ai.md) only where answers trigger actions.

## Trace

1. **Source admission.** Who can create, replace or withdraw content, and who admits it? Keep publisher, document revision, ingestion worker and source permission authority distinct. Track what provenance survives chunking.
2. **Instruction influence.** Attacker-editable retrieved text through retrieval and context assembly to an unauthorized answer or disclosure. Retrieved text is data, not authority. A delimiter or "trusted publisher" label is neither resistance nor a bypass.
3. **Permission propagation.** Source access rules through ingestion, index, query authorization, retrieval, context admission and delivery. The ingestion service's access does not decide who may receive derived content. Check denied, changed and revoked access at each step.
4. **Caches and residual copies.** Retrieval caches, answer caches and history: scope, freshness, behaviour after a subject change, source removal, revocation and reindexing. Do not assume deleting a source removed its descendants.
5. **Grounding and citations.** Trace each substantive claim to the retrieved passage, revision and authority. Separate stale but real, forged provenance, misattributed and fabricated. A resolving link does not show support.
6. **Output audience.** Answers, citation snippets, exports and diagnostics to their actual recipients, even when the full source is withheld.
7. **Recovery and operating authority.** Who may ingest, rebuild an index, purge a cache, pick a revision or restore, and who may read the content? Stale policy during outage, failed refresh or rollback.

## Scenario families

Retrieved instructions changing authorized behaviour; document permissions lost across derived content and answers; stale or fabricated material supporting a misleading answer or citation. Vector-specific scenarios need evidence of similarity retrieval.

## Checks to propose (all `not_run`)

- A clean synthetic passage against an instruction-bearing one, judged against the answer objective.
- An authorized subject against a revoked one, on fresh retrieval and on a warmed cache.
- A known source passage against a stale or fabricated citation. No authorization to test, or no context trace, is inconclusive.
