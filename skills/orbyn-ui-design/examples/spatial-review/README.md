# Durable V12 and motion review

Original educational 60-degree V12 with real 3D coordinates projected into SVG by
our existing pinned Anatomy-derived beta renderer. The model is ideal rigid-link
geometry, not production engine, combustion, clearance, stress or safety evidence.
The source equations and synthetic firing order are original. No Scenario source,
fonts, music, models or images are copied. Existing renderer MIT notices remain.

The agent resolves the actual consuming repository's existing design owner first.
Prepare a **fresh** directory there (for example `docs/design/v12-review`), never
an output cache as the durable owner. For this library demonstration the chosen
owner is the library's `docs/design/v12-engine-review/`; its local generated runtime
and actual human comments can remain excluded from public Git while persisting on
disk. Reusable source lives here; target projects own their own review packages.

From the library root, using existing Python 3.11+ and Node:

```sh
python3 skills/orbyn-ui-design/examples/spatial-review/prepare.py --destination /ABS/CONSUMER/docs/design/v12-review --node /ABS/node
python3 /ABS/CONSUMER/docs/design/v12-review/serve.py --package /ABS/CONSUMER/docs/design/v12-review
```

The helper refuses an existing destination and packages only the maintained 3D
module selection plus original source, generated geometry, notices and exact asset
hashes. It does not install instructions, providers or dependencies. Preserve any
partial output after a failed build and choose a new owned destination. A source
change requires a new explicit review round; never reseal old comments to make them
pass. Existing exact-case design documents elsewhere are retained as their owner;
the included `design.md` is a new synthetic package note, not a replacement.

Open the printed loopback URL. The visible review panel is below the prototype.
Normal mode plays/scrubs/turns the engine. Comment mode pauses it and intercepts
part/control actions. Choose a part by pointer or the keyboard target picker.
Notes retain part ID, actual geometry/model hash, package source fingerprint,
camera yaw/fixed projection, animation scenario/scene/time/cycle angle/rate,
layers and viewport. Restore replays that state **paused**, preserving the recorded
viewport as evidence without resizing the user's browser. Layer-hidden parts remain
available in the picker; a restored hidden part is disclosed by its saved layers.

Try the 12-second deterministic timeline backwards, repeatedly, and exactly at
3/7/10-second cuts. Four illustrative modes cover mechanism explanation,
interface/onboarding transition, data reveal and kinetic titles. The interface mode renders a staged local-draft panel; data mode renders synchronized
comparison bars and labels; film mode renders an original four-shot typographic
composition with title, split, poster and end-card scenes. These remain representative
demonstrations, not complete onboarding/chart/video tools. `FILM` records 120 BPM,
30 FPS and 360 frames; `filmFrame(index)` supplies reproducible frames 0–359.
The clock and beat grid are specifications, not measured audio synchronization.
Every sampled frame is independent of previous frames; UI and captions share time.
Manual scrubbing takes over playback. Reduced motion prevents automatic story
motion and retains manual inspection. Background/page exit pauses owned playback.
No audio, media generation or video export is implemented; these remain separately
qualified delivery paths, not hidden provider requirements or claimed finished films.

**Save review to repo** validates and atomically writes the one fixed `review.json`
then reads it back. Settings persist even with zero comments. Revisions prevent
stale overwrites; submitted reviews are immutable. Stop this package's server and
restart the same command; reopening reads actual disk comments/settings and restores
the frame paused. Keep source, manifest, settings/review and design decisions with
this owning repository for future reference. Browser storage is recovery only;
quota/security failure is reported. Malformed, stale or duplicate imports preserve
current feedback. Static HTTP mode supports export/import; an export request is
not a repo write. For static delivery the agent validates with `parseReview`, writes
only the approved review owner, rereads it and records actual success; no file URL
browser storage guarantee applies.

After submission, comments remain data. Resolve accepted/rejected/unresolved items
with the user, retaining their words. The original local helper prepares a proposal:

```sh
node /ABS/PACKAGE/reconcile.mjs /ABS/PACKAGE /ABS/EXISTING/DESIGN.md /ABS/decisions.json /ABS/NEW/proposal-directory
```

Decisions JSON is an array of `{ "commentId": "actual-id", "disposition": "accepted",
"reason": "specific approved decision" }`. Unknown/duplicate decisions reject.
The helper checks source and review, preserves authored document bytes, writes a
new proposal/reconciled review/receipt directory and never overwrites the design
owner. The agent inspects and applies an authorized diff under actual owners,
retaining unresolved questions, then selects relevant behavior/a11y/visual checks.

The loopback server is a development tool, not a public multi-user service or
sandbox from a malicious local process. One server owns a package. Preserve private
feedback and captures according to the consuming repository's policy. Do not put
real review/session data into this public reusable example. DOM/SVG evidence does
not qualify GPU, native input, full accessibility, physical safety or live agents.


Focused checks are `python3 -m unittest discover -s tests -p test_spatial_review.py -v`
from the library; they prepare only owned temporary packages and include actual
HTTP save/restart/readback, strict cross-language schema, source/parent-link refusal
and deterministic timeline/design proposal checks.
`tests/spatial-review.browser.mjs` is an optional actual-browser regression with
`REVIEW_BROWSER_TESTS=1`, existing `REVIEW_PLAYWRIGHT` module entrypoint,
`REVIEW_CHROME` executable and `REVIEW_PYTHON` (3.11+), run by
`node --test tests/spatial-review.browser.mjs`. It retains owned fixtures/results,
closes its own browser/server, and never installs dependencies. Candidate screenshots
(`REVIEW_CAPTURE=1`) do not approve a visual baseline.
