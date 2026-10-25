# Explicit local engineering memory

Use for a direct request to remember, find, correct, categorize, tag, archive or
forget durable engineering context. Ordinary reflection and source investigation
do not enable capture. The helper is optional, local and offline; it does not
scan chats, train a model, write host-native memory or upload anything.

## Agent-operated setup

Honor existing exact-scope authorization and host restrictions. Select a private
user-owned data directory outside all Git checkouts and host configuration.
Resolve the actual target, not the outer library, before binding a project.
Never silently put personal/project context in the public library or a fork.
Use [memory.py](../scripts/memory.py) with Python 3.11+; `--help` describes its CLI.
The human asks for the outcome; the agent executes these steps within scope.

Example paths below are placeholders, not preconfigured storage:

```sh
python3 skills/reflect/scripts/memory.py --root /private/engineering-memory init --mode manual
python3 skills/reflect/scripts/memory.py --root /private/engineering-memory --project /work/target register
```

Initialization without `--mode manual` defaults to off. An ordinary workspace
setup does not initialize memory. `mode --mode off` prevents store operations and
keeps existing records; forgetting is a separate action. Only manual capture is
implemented: explicit requests authorize the selected local operation. Assisted
capture and host-native adapters remain future work, not implied capabilities.
For an existing initialized root, use its registered scope and inspect `list` or
`taxonomy`; do not run `init` again. It deliberately refuses a nonempty root.

Selectors are exactly one of `--project PATH`, `--personal`, `--reusable`.
Worktrees with the same Git common directory share a registered project store.
A different clone/fork/path needs explicit registration. Non-Git directories work.
Moving a registered project needs a deliberate binding migration; do not silently
alias by remote URL/name. Writable organization stores and remote multi-user access
are unsupported. Reusable is a separate local scope, not public visibility.

The root contains a registry/deletion ledger and separate SQLite stores, with
owned private exports under `artifacts/`. SQLite data is not application-encrypted.
The local trust boundary is the OS user, not the scope labels. No live database
on a network share or automatic cross-device sync is supported. Keep the complete
root, especially the deletion ledger, when preserving this system.

## Structured records and classification

`remember --input draft.json --op UNIQUE_ID` accepts the editable fields in the
[synthetic record draft](../examples/memory-draft.json). Required fields are title,
statement, category and at least one domain. Metadata is validated by the
[record contract](../scripts/learning/schema.py); `taxonomy` shows current values.

| Dimension | Contract |
| --- | --- |
| Scope | Project, personal or explicitly registered reusable store; derived from the selected binding, not input text |
| Category | One of preference, project-fact, decision, convention, workflow, failure-pattern, solution-pattern, constraint, learning |
| Domains | One or more architecture, backend, frontend, ui, ux, accessibility, data, security, testing, performance, platform, operations, delivery, developer-experience, technical-strategy |
| Tags | Up to 12 lowercase labels under `tech:`, `topic:`, `concern:`, `platform:` or `module:`; custom values stay scoped |
| Evidence | User-stated, observed, reproduced or validated; the latter two require pointers, but the helper does not prove their claims |
| Applicability | Optional lists of modules, platforms, versions and branches |
| Sensitivity | Public, internal or restricted; changing this label grants no access or publication rights |
| State | Proposed, active, conflicted, stale, superseded or archived; forgotten bodies are removed |

Records have generated opaque IDs, revision numbers, UTC timestamps and typed
relations. Pointers are inert metadata, not instructions or permission to read a
file. Related skill names must exist. Same-scope relations may support, contradict,
supersede or derive from another existing record. Cross-scope references are refused.
Read limits: title 200 characters, body 8,000, record 32 KiB, import 1 MiB/100
records; initial store capacity is 10,000 records. No enterprise scale claim follows.

Exact duplicate title/body creates a distinct record but reports the existing IDs;
inspect those before deciding whether to keep both or correct the original. Tags
normalize known aliases such as `tech:postgres` to `tech:postgresql`. Categories
and domains are versioned in code. Unknown imported categories are rejected as a
whole; leave the input file untouched and explicitly map it before reimporting.

## CRUD and retrieval

Revision values are bounded to signed SQLite integers with one terminal forgetting
slot. Each stored relation reserves an additional revision for later cleanup.
Imports, restores and edits that consume this headroom are rejected atomically.
Forgetting advances every changed dependent's revision and marks it stale; it
never reuses a revision or skips a dependency merely because the counter is high.
Automatic dependency cleanup preserves a monotonic update timestamp even if the
local clock moves backwards.

Every mutating record command requires a unique `--op` identifier. Keep that ID
when retrying the same request after an unknown result. Reusing it with different
content fails. Receipts contain IDs/revisions, not archived copies of the body.
Replays report their original outcome; use `show` for current state.
Operation IDs accept 1-80 lowercase letters, digits, underscores or hyphens,
starting with a letter or digit. Standard lowercase UUIDs work, including those
starting with digits. Prefer opaque generated IDs; never encode remembered text
or secrets in an operation ID.

- `show ID` inspects one record, including inactive states.
- `find --query TEXT --category CATEGORY --domain DOMAIN --tag TAG` filters only
  the selected scope. `list` is the same operation with an empty query.
- `--applicability context.json` supplies applicable module/platform/version/branch
  lists. A constrained record without matching context stays out of ordinary recall.
- `update --selection selection.json --input patch.json --op ID` corrects, retags
  or recategorizes a frozen `{ "memory_id": expected_revision }` selection. All
  selected records succeed together or none do. Scope/identity cannot be patched.
- `archive ID --revision N --op ID` removes from ordinary recall reversibly; an
  explicit revision-checked status update can reactivate it.
- `forget ID --revision N --op ID` removes the body and managed derivatives.
- `merge-tag --old TAG --new TAG --selection selection.json --op ID` creates a
  scoped alias and retags the exact affected set. Include inactive records when
  preparing the selection; missing/new/changed records cause a conflict.
  Both names resolve through existing aliases before selection, just like search.
  Merging an alias therefore moves all records carrying its canonical source tag
  and preserves lookup by that source's existing aliases. A merge between names
  already sharing one canonical tag is rejected without changing state.

Ordinary recall excludes proposed, stale, conflicted, superseded, archived and
expired records. `--include-inactive` supports inspection, not permission to apply
them. Search returns category/domain/tag facets from eligible results in that scope,
stable ordering, evidence/freshness and a generation/revision receipt. Defaults:
five results, 4,000 total body characters. Truncation is labelled. There is no
embedding provider, opaque relevance score or cross-project search union.

Before consequential use, call `revalidate --input receipt.json` with the result's
`receipt` object. A concurrent edit/delete invalidates it. This verifies store
freshness, not the referenced source. Check actual current code and policy too.
`check-sources ID --revision N --op ID` compares project-relative `source` evidence
against a `sha256:<digest>` revision. It reads at most 1 MiB per file, refuses
traversal/symlinks and marks changed/missing sources stale. Test results, user
statements and opaque external pointers still require their own verification.

Preference/decision records default to no review deadline; other categories get
a 90-day `review_after`. Explicit UTC `expires_at` prevents later normal recall.
Set short expiry for transient environment observations when appropriate. Reading
does not refresh deadlines. No background retention task or reminder is created.
Current user/project instructions and checked source outrank remembered context.
Contradictions need evidence, not a timestamp/popularity vote.

## Preview, export and recovery

`export --selection selection.json --format json|markdown|html` creates a managed
private file and reports its path. HTML is a read-only human review snapshot with
search and category/domain/tag filters, escaped record text, labelled keyboard
controls and no external resources. Open only the returned file or serve its
dedicated artifact directory on loopback for an authorized preview. Never expose
the registry/database directory. No writable browser API is installed.

JSON exports retain IDs and scope. `import --input export.json --op ID` accepts
only the same store, refuses existing/forgotten IDs, and imports as proposed.
For edits to existing IDs use `update`, not import. Bulk import is atomic; imported
text cannot enable capture, widen scope or publish itself. Cross-scope promotion
requires an independently reviewed new record, not relabelling an export.

`backup` creates a consistent managed SQLite snapshot. `restore --artifact ID
--generation N --op ID` restores missing records only, as proposed, into the same
registered store. It preserves newer existing records and applies the separate
deletion ledger. Registry revision high-water marks prevent restoration from
reusing a revision held by an older editor. It does not overwrite/recover a corrupt live database or accept
an arbitrary external database. Such recovery needs a separately reviewed repair;
never replace the registry/ledger with an older copy to make restore work.

## What forget means

The transaction removes the body and its payload fingerprints, suppresses stale
retries/imports through a minimal ID/revision tombstone, removes dependent candidate
drafts, and marks managed exports/backups/patches for cleanup. Related surviving
records lose the deleted relation and become stale. No raw remembered text is
kept as an audit trail. Search never returns a forgotten record.

Cleanup is a separate recoverable step. A durable artifact reservation precedes
file creation, so an interrupted export remains known. `cleanup` retries pending
files, refuses replaced symlinks/hardlinks and reports what remains. Do not say
“fully erased” when a managed file could not be removed. The receipt identifies
unmanaged copies, published Git history, snapshots and host chat context outside
control. Logical deletion and ordinary SQLite page scrubbing are not forensic
erasure. Forget does not delete original application source or other owners' files.

Keep memory outside task worktrees. Follow
[artifact lifecycle](../../orbyn-workflow/references/artifact-lifecycle.md) for
owned preview servers and evidence. A merged patch is not authority to delete a
person's memory root, backups, active worktree or pending human preview.

## Turn selected evidence into a method improvement

Use the [lesson handoff](../../orbyn-skill-creator/references/memory-learning.md).
Memory text never directly edits released skills. Prepare a bounded general
change, synthetic failing/adjacent cases and an explicit destination. The agent
performs authorized handoffs; the human does not need to invoke each skill.
