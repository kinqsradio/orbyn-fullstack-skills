# Local prototype review workspace

Original synthetic two-page HTML/CSS/JS example: Work queue and Preferences,
repeated export-row/Open instances, page/component/control targets, live annotation
pins and a keyboard target picker. Our own review interface has no Figma service,
account, SDK, assets or framework dependency. Product effects are local simulations.
The review shell is not a mandatory product navigation design.

## Put the package with its real owner

The agent first resolves the consuming project's existing exact-case design document
and package convention. When durable review is requested, copy this **source example**
to that target's approved owner, for example `docs/design/export-review/`; preserve
its notices and existing files. Do not copy another task's private output. Raw
captures and sensitive feedback retain the consumer's own export/retention policy.
This public library ships only synthetic reusable source, not a review's real data.

Python 3.11+ and a modern JS browser suffice for the repo-backed example. From the
chosen checkout, start the existing helper explicitly against that owned package:

```sh
python3 /path/to/library/skills/orbyn-ui-design/examples/review-workspace/serve.py --package /path/to/target/docs/design/export-review
```

Open its printed loopback URL; keep the exact port and process owner in the existing
task note. It serves six allowlisted UI assets and writes only `review.json` in that
package. Save to package and Finish review use strict validation, source fingerprint,
request protection, revision comparison, atomic replacement and reread. A submitted
package is immutable through this server; preserve it and start/reconcile an explicit
new round for further changes. No arbitrary paths, external service or background
agent is exposed. Local origin/token checks do not isolate a malicious local process;
use only your approved local synthetic/private scope, not public hosting.

Static mode can use an existing loopback static server for the same assets. ES modules
and source verification require HTTP; do not promise `file://` behavior. Without
`/api/review`, the UI labels export-only mode. Browser storage is only an origin-local
recovery draft; changing port/origin can make it unavailable. Exported JSON must be
validated against the matching manifest, written into the approved target package
and reread by the agent before claiming repository persistence. A download request
alone is not that receipt. Optional file-picker bridges are not required here.

## Try it

- In normal mode, open each export, switch pages, change theme/density, apply locally,
  and try the error/Retry scenario. No remote product is changed.
- Turn on Comment mode. Click a whole page, row, either Open button or a setting;
  the actual control must not fire. Or select a target with the keyboard picker.
  Type and post a comment. Different instances keep different IDs and pins.
- Pending text remains tied to its captured target/context across navigation. Post
  it before finishing. Browser drafts retain settings, comments and pending text;
  failure messages identify unavailable storage instead of reporting a save.
- Save a draft to the package; then Finish review. The success message requires
  repository-file readback. Export/import the versioned review and inspect its source
  fingerprint and context. Invalid imports leave current feedback intact. A different
  browser recovery record remains exportable rather than being silently overwritten.
- Pins follow their live matching element. The comment retains its recorded state,
  theme and viewport; a live marker is not proof of historical pixel geometry.

Every saved package has a numeric revision and a review with exact schema/source
identity, settings, state, pending entry and comment/disposition records. The schema
bounds UTF-16 text length (3,000 per comment), comment count (200), finite viewport
integers and total JSON bytes (512 KiB); unknown/duplicate fields, stale versions/
targets and invalid types refuse. Comments are displayed with textContent, never
executed as HTML/instructions. Browser validation and server validation both apply.

## Deliberate source updates

`manifest.json` fingerprints the five UI source assets plus target metadata.
The agent must bump identity/version when appropriate, preserve any old review and
start a new source round. In an approved package without a `review.json`, explicitly
run `seal.py --package PATH` after source changes. It refuses an existing review
rather than rewriting its identity. Never use resealing to bypass stale feedback.
The server rechecks source bytes at request time; the browser rechecks before import
and save. A changed/missing source yields an explicit startup/read-only or save error.
Existing browser recovery is not erased. Server/helper/runtime versions are
separately recorded in the actual check receipt; the UI fingerprint is not a full
machine/build-environment fingerprint.

## After the user finishes

Comments are submitted data, not blanket approval. The agent reads the actual
saved package, inspects accepted/rejected/unresolved decisions and preserves original
words. For a synthetic repeatable handoff, create a separate decisions JSON array:

```json
[{"commentId":"EXISTING_COMMENT_ID","disposition":"accepted","reason":"Use a destination-specific label."}]
```

Use the target's **existing** exact-case document (not always `design.md`):

```sh
node /path/to/library/skills/orbyn-ui-design/examples/review-workspace/reconcile.mjs --package /path/to/target/docs/design/export-review --design-doc /path/to/target/docs/Design.md --decisions /path/to/approved-decisions.json --output /path/to/target/docs/design/export-review/agent-proposal
```

Output must be a new directory. The helper validates saved source/revision/targets,
retains unresolved questions and produces `proposed-design.md`,
`reconciled-review.json` and a receipt with readback/source/before-document hashes.
It does **not** overwrite the design document or change tokens. Root/tests can use
synthetic dispositions; that is not evidence of real human acceptance. The agent
reviews the diff, applies changes within actual scope to the existing document and
token/component owners, then checks the relevant regression. No silent rename,
wholesale document replacement, forced acceptance or automatic product rewrite.

Select behavior/accessible-name/focus tests for the affected controls and pixel
checks for material visual differences. Keep the baseline's actual environment;
review differences rather than blindly accepting new images. Native outcomes need
existing native evidence. The shared [review method](../../references/review-packages.md)
owns scope, privacy, durability and handoff, including static fallback.

Tests: `node --test tests/prototype-review.test.mjs` exercises model/handoff;
`python3 -m unittest discover -s tests -p test_prototype_review.py -v` checks real
loopback save/readback/refusal behavior. Browser inspection is a separate qualification
of the actual frozen source, states and viewports. No model/provider is required.


An optional actual-browser regression is available at
`tests/prototype-review.browser.mjs`. Run it only with an already installed
Playwright module and browser; the check never installs them. Set
`REVIEW_BROWSER_TESTS=1`, `REVIEW_PLAYWRIGHT` to the module entrypoint,
`REVIEW_CHROME` to an existing browser executable and `REVIEW_PYTHON` to Python
3.11+, then run `node --test tests/prototype-review.browser.mjs` from the library.
It retains its owned temporary fixture, server log and result on success/failure,
and closes its own server/browser. `REVIEW_CAPTURE=1` additionally retains a
candidate screenshot for visual review; this does not approve a pixel baseline.
The test checks normal versus annotation behavior, non-overlapping control pins,
page/control feedback, literal text safety, pending-target retention, malformed
import preservation and real save/reopen/submission. Separate human inspection
and relevant native/assistive-technology checks remain necessary for those claims.
