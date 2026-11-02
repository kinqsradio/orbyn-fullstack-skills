# Data platform checks

Use for producers, ingestion, transformations, analytical stores, notebooks and consumers. State sensitive fields, permitted audience and use, execution scope and consumer rules first. Correctly authorized broad outputs and public data are counterexamples to unsupported disclosure claims; missing lineage is a gap, not proof of disclosure. A changed source record is not a harmful decision, and a notebook is not privileged execution.

## Trace

1. **Producer to ingestion.** Who supplied a record, who may submit it, and is it accurate for its use? Origin, event time, schema and units, correction authority. An authenticated feed can carry a wrong or altered value; a bad value alone does not name an adversary.
2. **Raw to transformed.** Follow specific fields through selection, joins, aggregation, derived features and intermediate copies. A renamed or hashed field, or a missing direct identifier, is not anonymization.
3. **Transformation to publication.** Compare output fields, row scope, audience and intended use with policy. Include exports and materialized copies.
4. **Analyst to execution identity.** Notebook author, interactive session, scheduled principal and dataset owner differ. Find the dataset decision for read, write, export and delegation, including other projects. A shared runtime is a premise to examine, not an escape.
5. **Store to consumer decision.** Name the consumer, the rule that uses the values and the consequence of an altered input. A dataset called "features" proves no training or poisoning.
6. **Correction, replay, recovery.** Late records, duplicates, changed versions, failed transformations, backfills. Which version does a consumer see, and how does a correction reach derived copies and past decisions?
7. **Retention and governance.** Ownership, purpose, classification, revocation and retention through intermediate data, notebook outputs, exports and restores. Policy is not evidence it was applied.
8. **AI boundary.** With an ML system, model the shared feature or dataset boundary once, with one owner; keep source integrity, consumer decisions and serving authority distinct.

## Scenario families

Sensitive fields surviving into broader-access outputs; corrupted or malicious source values driving a downstream decision; analyst execution reaching datasets beyond intended authority.

## Checks to propose (all `not_run`, isolated synthetic copies only)

- Trace a marked restricted field and an allowed public field through the same transformation as the broad reader. Pass: the permitted output arrives and the forbidden field or prohibited derivation does not. A pass does not show anonymization against unknown joins.
- Compare an accepted baseline with one altered or stale record, then its correction, in a non-operational consumer.
- Compare an allowed and a forbidden dataset through interactive and scheduled execution. Results cover only the named identities, operations and revision.
