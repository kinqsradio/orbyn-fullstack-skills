# Ground answers in authorized sources

Use when answers depend on external/project knowledge. Ordinary source search
belongs to `how`; this method owns an application's ingestion, retrieval and
answer-support contract. Do not mandate embeddings or a database migration.

## Preserve lineage and current access

Record corpus owner, allowed ingestion sources, source identity/version, extraction
method, chunk boundaries, transformations, index/embedding configuration and
update/deletion policy. A chunk ID alone is not a usable citation. Preserve a
stable path back to the exact source passage and its applicable date/version.
Treat OCR, missing sections, stale copies and contradictory documents as source
quality limits rather than filling gaps with model guesses.

At query time derive principal/tenant/resource scope from trusted application
identity, not model arguments or document instructions. Filter access before
content reaches the model, reranker, answer cache or any diagnostic export.
Do not retrieve all tenants and redact after generation. Permission filtering
must use the real store's enforceable semantics; a client-supplied tenant filter
or an index field without validated authorization is not an access boundary.

Propagate ACL updates, revocations and source deletions to indexes, derived chunks,
caches and controlled logs according to their ownership/retention contracts.
Authorize cached results for the current caller and permission version; a cache
hit is not permission. Define acceptable freshness and fail closed where current
access cannot be established. Recheck authorization at consequential reads/effects
when it may change during a long job. Do not promise erasure from unrelated backups
or third-party copies. Use [migration](../../orbyn-data-migration/SKILL.md) when an
existing index/version needs an actual storage transition.

## Measure retrieval separately from answering

Start with an available lexical/search baseline. Compare semantic, hybrid and
reranking only when representative cases justify their added latency/cost and
failure surface. Inspect filters, chunk quality, query interpretation and index
freshness before replacing the model. Preserve exact identifiers and rare terms
that semantic similarity may miss; do not invent a universal ranking formula.

Use held-out query/source relevance cases to inspect missing required passages,
precision, duplicates and relevant coverage within the context budget. Then assess
answer correctness, faithfulness and citation support separately. For a fixed k
and relevance rubric, precision@k is relevant retrieved items divided by k;
recall@k is relevant retrieved items divided by known relevant items. State how
short result sets, duplicate chunks and zero known-relevant cases are handled;
incomplete relevance labels limit recall claims. Choose k and thresholds from the
task/context budget, not a universal target. Keep answer support, citation
correctness and appropriate abstention as separate judgments. Good retrieval
can feed a bad answer; a plausible answer does not prove adequate retrieval.
Reference-free model scores alone cannot establish source truth or completeness.

Distinguish a successful empty authorized search from denied access, incomplete
retrieval or a provider/index error; do not disguise failure as absence or fall
back to an unfiltered/global corpus.

For no evidence, inaccessible sources, stale/conflicting material or a question
outside corpus scope, return a bounded explanation, supported partial answer or
abstention. A citation must support its associated claim, not merely mention the
topic. Source version/date and uncertainty must survive summarization. Do not
invent documents, citations or confidence percentages.

Include cross-tenant near matches, revoked cached access, injection in a retrieved
passage, exact-ID queries, unsupported questions and conflicting versions in
[task evaluations](evaluations.md). Keep real documents/traces private and use
synthetic cases in public examples. Return lineage/access/freshness rules, baseline
comparison, retrieval versus answer findings and remaining coverage limits.

Research/update pointers reviewed 26 October 2026: [RAGAs, EACL 2024](https://aclanthology.org/2024.eacl-demo.16/),
[Azure search security-filter limitations](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search).
Original local synthesis; no source text, SDK or runtime imported. These methods
work offline; current provider/version claims still need applicable verification.
