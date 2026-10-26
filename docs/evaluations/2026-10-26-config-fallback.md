# Value propagation and fallback qualification

Initial qualification on 26 October 2026 covered a local uncommitted improvement
to the existing `tdd` and `interrogate` methods. The sections before the refresh
record below describe that historical snapshot and its evidence. Catalog remains
34; no product checkout, persistent memory, installation or settings changes.

## Change and frozen identity

TDD now follows a newly retained value into presence/truthiness, empty-result,
fallback and precedence checks. It calls for changed-field-only inputs and
relevant true/false/unset/empty/unmatched controls with populated fallback values.
Interrogate distinguishes expected consequences, compatibility risks, contract
violations and missing evidence, linking to the TDD method for test design.
Neither method requires a generic exhaustive matrix or silently changes defaults.

Three new development cases cover repair, review and an adjacent cosmetic edit.
All 194 prior case objects, including holdouts, remain unchanged. The initial
197-case suite SHA-256 is
`ff51c36b93b27ef33c393b62df24c7a3dc0d992ca2652f45f2c33dcd7693ab62`.
The generated distribution manifest is updated; owner names, catalog and discovery
are unchanged.

The [protocol](2026-10-26-config-fallback-protocol.json) pins exact method/source
hashes, synthetic fixture contents, tasks, rubrics and capabilities before trials.
Baseline commit: `5cd279815a025dc5f902fbd96db5f6ddd41389a1`.

| Method condition | Files excluding evaluation material | Inventory SHA-256 |
| --- | ---: | --- |
| Baseline | 292 | `81b1d023aedf81b1b998f86e31dd73f5b83a67d912612d4237ba94bdde865959` |
| Uncommitted candidate | 292 | `08825a1031921aa08ca84d3c0ef39be970864d46ec4938535885cf7db80f8d37` |

Digests hash compact sorted JSON with separators `(',', ':')`. Only the two
operating-method references differ between method conditions. The implementation
and suite bytes stayed frozen during collection. Grader revision fields record
the actual base commit for both conditions; candidate dirty-source identity is
the protocol's inventory and source digests, not an invented candidate commit.
This protocol and report are qualification metadata outside that method snapshot.

## Execution and results

Six fresh calls: one baseline/candidate pair for each new development case, plus
one unscored readiness call. Codex CLI `0.163.0-alpha.10.2`, `gpt-6.1-sol`, medium,
configured `service_tier=default`, fast modes disabled, workspace-write, five-minute
budget per call, at most two calls concurrently, alternating condition order.
Effective provider scheduling is unverified. These explicitly authorized CLI
calls are model experiments under the evaluation guide, not implementation
or review delegation. The implementing lead wrote and reviewed this change;
no independent source-review verdict is claimed for it.

Every call used a fresh synthetic Git root, its own copied method snapshot and
local discovery links. Per-call prompt inventories contained exactly 34 intended
skills, with advertised roots resolving within that own fixture. Evaluation
material was excluded from subject methods. Matching wrappers excluded outside
reads, downloads, installs, accounts, networking, delegation, commits, publication
and memory writes. Parent environment and user configuration were not modified.
Visible events and outputs are retained; reasoning items are excluded.

| Case | Baseline | Candidate | Decisive evidence |
| --- | --- | --- | --- |
| `value-propagation-fallback` | Pass | Pass | Two original tests pass; new true/false field-only regression fails before source repair; final eight tests pass; fallback contract preserved |
| `review-fallback-consequence` | Pass | Pass | Correct candidate retained, expected fallback consequence distinguished from the broken false-dropping variant, concrete defect and coverage gap explained |
| `config-review-adjacent-nontrigger` | Pass | Pass | Only requested README heading bytes change; no TDD/interrogate selection, configuration matrix, formal tool or product edit |

All six calls completed within budget. The actual suite grader reports **3/3
outcomes passed per condition**, zero failed or unverified. Recorded skill reads
also match expectations; these are completed outcome trials, not separate
first-response routing experiments. Exact rubric excerpts, captures, observed
usage/duration, artifact hashes and matching protocol are retained with the
scored run records. The comparison denominator is these three cases, not 197.

## Separate controller checks and retained limits

The controller reran each repair's delivered eight-test suite against the actual
repaired resolver: pass. Replacing only the source with the original implementation
causes assertion failures. A disposable mutation inside the delivered resolver
removes explicit false before normal selection; the same tests detect it too.
The negative runs have failures, not import/setup errors. Originals and subject
evidence are preserved. Ten independent contract examples per repair also pass,
including full-result equality, unmatched/null/empty controls, fresh dictionaries
and unchanged inputs. Both review fixtures were additionally replayed across
base/candidate/broken with true and false, confirming the reported distinction.

Both review agents ran their own finite 768-input comparisons and found zero
candidate mismatches, while base and the broken alternative fail the documented
contract. Those are bounded implementation checks, not unbounded proofs or tests
of a consuming application's behavior. The supplied combined-field test misses
the changed field-only fallback branch and passes the false-dropping alternative.

All six method copies match their pinned inventories. Supplied fixture files
remain unchanged except explicitly authorized resolver repair and README heading.
Failed attempts are retained: baseline repair instruction discovery exited 2
because a nonexistent optional directory was searched; this was not regression
proof. Expected pre-fix and mutant assertion failures are labelled as such. A
controller inspection attempted a nonexistent guessed test filename after its
successful checks; it did not affect qualification or require a product fix.

The full existing library suite passed **157 tests**. Library/link/provenance,
discovery, manifest and evaluation validation pass for 34 owners, 295 assets and
197 case definitions. No new helper tests that merely mirror instruction wording
were added. No further shared-method gap was identified by these observations.

This is one run per condition on three public synthetic development cases, with
unblinded lead grading. Both conditions succeeded; no general capability gain,
statistical equivalence, heldout result, enterprise-scale qualification or
production correctness follows. Other models/hosts and real consumers remain
unqualified by this study. No VS Code source or issue-specific logs were copied.

Raw captures, host overrides, controller logs, grader reports and comparison are
local in ignored `output/config-fallback-trials/round-1/`; fixtures are under
ignored `repo/config-fallback-trials/round-1/`. Keep while review/reproduction is
pending and record availability if retired. No servers or long-lived trial
processes are retained. Unrelated `.freebuff/` and other work remain untouched.
No staging, commit, push, PR, merge or persistent-memory update was performed.

## Refresh onto merged main

The delivery candidate is now based on
`4f2c4acb6d37e47e4d4a58f3aade604ef3807c46`, including merged REA and community
policy PR #24. The original six-file patch was saved and verified before the
branch fast-forward. Both owning method files remain byte-for-byte identical to
the previously independently approved candidate. All 198 released case objects
are preserved unchanged; the same three TDD cases are appended, for **201 cases**.
The manifest was regenerated from the reconciled files rather than choosing
either old manifest. The original 197-case protocol/captures remain unchanged
and are not regraded against the new suite.

Current suite SHA-256: `6addf528f213aa0c004b24565c996219068c218e328bc63c3790528d9e79033b`.
The [refresh protocol](2026-10-26-config-fallback-refresh-protocol.json) pins the
new base, exact condition methods, fixtures, tasks and rubrics before collection.
Its SHA-256 is `7a57d65c2f87f530d1ee88b460c64f58ca5fff6ddfb87de327825bd01c7f5df7`.
Measured source inventory SHA-256: `a40a01b6c5fc171d5126ae77cb4c340824063a05d89cdd4ba4f1e0ed13c2a563`.
This source inventory precedes the final report update; reporting metadata is
not a subject method. The shared Git base in evaluator records is not a claim
that baseline and dirty-candidate method bytes are identical.

A new readiness probe and six fresh model calls used the same host/model/settings
as the initial study, against baseline and candidate methods from this merged
base. Each prompt inventory advertised exactly its own fixture's 34 skills; all
293 condition-owned method files and supplied input hashes were checked. The
only method differences between conditions are the two intended operating
references. There was one replicate per condition/task and no held-out trial.

| Refreshed outcome task | Baseline | Candidate |
| --- | --- | --- |
| Repair missing propagation without rewriting fallback | Pass | Pass |
| Review intended fallback consequences and the false-dropping defect | Pass | Pass |
| Make only the requested cosmetic heading edit | Pass | Pass |

The current-suite evaluator reports 3/3 outcomes passed for each condition, zero
failed or unverified. The implementing lead reviewed complete visible commands,
source/tests and reports semantically; exact excerpts and formal grades are
retained with the scored records. Earlier independent approval applies to its
frozen snapshot; the lead performed the current base/integration review and
controller checks. No new independent-model review is claimed for the refresh.

Both repair runs executed a standalone failing regression with exit 1 before
editing the resolver. The lead independently replayed the delivered suites:
all 8 baseline-condition tests and all 9 candidate-condition tests pass repaired
source, fail the original for missing propagation, and fail a false-dropping
mutation. Negative results are assertion failures, not setup/import errors. Both
repairs also pass ten independent contract cases checking full output, defined
false, fallback selection, fresh results and unchanged inputs.

Both review reports identify the supplied correct candidate as contract-compatible,
separate compatibility consequences, and give expected/actual evidence for the
broken false-dropping version. Their own finite comparisons used 576 and 768
inputs respectively. A separate controller applies the same 768-input comparison
to each fixture and reproduces zero candidate mismatches, 192 base mismatches
and 96 broken-variant mismatches, with no freshness/input-mutation failures.
Neither finite enumeration is an unbounded correctness proof. Cosmetic trials
preserve all other README/settings/code bytes and read neither TDD nor
interrogate; they create no configuration matrix or product behavior change.

All **157 Python helper tests** and **65 bundled Node validator tests** pass on
the reconciled candidate. Library/discovery/manifest/provenance/link checks,
201-case validation and `git diff --check` pass. All REA/community-policy files
remain as released except the intended appended case objects and derived
manifest entries; unrelated `.freebuff/` remains outside the patch.

Retained limitations: one candidate pre-fix adjacent-test command followed
unittest with a version command, masking its shell exit despite the test failure.
It is not credited as independent failing-before proof; the earlier standalone
exit-1 regression and controller replay establish that signal. Both repair
fixtures are initially untracked Git data, so their `git diff --check` results
are not proof of artifact preservation. Exact controller content/hash checks
supply that evidence. Neither imperfection was hidden or fixed by weakening a
rubric, and no task, criterion or measured method changed during these trials.

Recorded aggregate metrics (summed call time; CLI-reported input plus output
tokens including cached input, not billing or unique context size):

- baseline: 174.056 seconds; 293,415 tokens.

- candidate: 175.959 seconds; 345,532 tokens.

Both conditions succeed on this small development subset. No general quality,
performance, enterprise-scale, cross-host or production guarantee follows; the
checks establish scoped compatibility and useful regression sensitivity. No
additional method defect was identified by the refresh.

Fresh full captures, failed attempts, controller logs, observed metrics and scored
records remain in ignored `output/config-fallback-refresh/round-1/`; the measured
source copy is in `output/config-fallback-refresh/frozen-source/`. They are local
evidence, not public downloads. The old independent-review packet remains intact.
All trial fixtures remain retained for human review/reproduction; no target
servers or providers were launched.
