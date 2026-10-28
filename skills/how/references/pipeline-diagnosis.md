# Diagnose a pipeline cluster at the owning boundary

Use after the [CI owner](../../orbyn-ci-design/references/bulk-failures.md) establishes
the expected matrix and failure inventory. A list of a thousand failures may have
several causes; a common error string does not prove one cause. Keep artifact,
configuration, suite, environment, instance, attempt and original evidence attached.

Choose a representative discriminating observation from each material cluster,
plus a passing control and exceptions that could falsify the hypothesis. Inspect
setup/dependency failures before assigning hundreds of downstream assertion bugs.
Trace the first relevant boundary using current source and authorized environment
facts. Separate application regression, test defect, stale expectation, input/data
drift, service/runner failure, concurrency/isolation and unknown. These are working
hypotheses, not classifications inferred from a keyword such as “timeout”.

For example, if only integration suites fail on one instance with connection
errors while unit suites pass, inspect that instance's dependency readiness and
configuration. A controlled healthy/unhealthy comparison can support the cause;
the error message alone cannot. If both configurations fail the same negative-total
assertion at the changed source boundary, reproduce the calculation independently.
One investigation need not fix every test individually.

Follow [reproduction](reproduction.md), preserving actual selected counts and
failing-before evidence. Keep source/configuration changes distinct. After a
supported fix, run the focused regression and affected cluster, then hand back
the project's required broader checks for the new candidate. Do not claim that a
representative test proves the entire cluster or environment passed.

Bound retries and exploration. Retain contradictions and unresolved groups in
the consumer's task record; ask only for consequential missing information or
authority, while continuing independent work. Hand confirmed cause, owning path,
regression, actual revision and remaining gaps to the workflow. Never erase
evidence or alter the CI gate solely because diagnosis is difficult.

## Cause-to-work-item reconciliation

For a multi-cause investigation use a compact record, not a second mandatory tracker:
repository/root/cause key; immutable observation IDs and attempt/source hashes;
hypothesis, supporting evidence, counterexample and confidence; current owner,
disposition, actual work-item/PR IDs, checked candidate and next discriminating action.
One cause may explain many tests; one symptom can have several causes. Preserve
all attempts and missing inventory. Keyword/model clustering is a lead, not cause proof.

Before an authorized write, validate destination/scope and complete pagination;
read current remote item/claim/head/PR, then reconcile by stable key and actual ID.
A title/label/local marker is a hint, not identity, atomic lock or completion. Lost
response after creation requires readback/list reconciliation before retry, not
another create. Bound pagination/cursor loops and retain unknown/partial outcomes.
Foreign claims block takeover. Current merged/head/assignment state outranks stale
local notes, but lack of read access does not establish absence. Late workers and
writes must still match current owner/candidate. Assignment alone is not atomic exclusion.
Routed means unresolved with a destination, observed acknowledgment if any and
remaining gate; resolved needs its actual evidence. Use the existing record format
or a paragraph when sufficient. No automatic Jira/Confluence writes or per-stage
approval ceremony; research ends with findings and a no-merge endpoint stays closed.

Synthetic example: 18 API tests and 7 browser tests share an exhausted database pool;
3 retries also show HTTP503 from an independent auth outage. Preserve attempt IDs,
prove pool saturation from connection trace and a targeted bound, and retain the
auth counterexample. `repo/root/pool` routes to storage item17, still unresolved;
`repo/root/auth` has item23/PR9 at headH, pending scoped CI. Replayed item17 creation
after lost response finds actual ID17 before another write. A same title in a
second repository is unrelated. The deterministic fixture checks adapter behavior,
not live tracker access or race-free atomic exclusion.
