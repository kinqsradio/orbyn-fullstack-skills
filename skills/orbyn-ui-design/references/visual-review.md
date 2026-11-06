# Review changed UI and hand it to a person

Use before capturing UI, briefing a visual inspector or presenting a preview.
Follow the consuming project's visual-review policy and the changed surface.

## Choose proportional evidence

Choose the [evidence surface](prototypes.md#choose-the-evidence-surface-before-building)
before building a harness or capturing UI. Identify the loaded candidate/window and
adapters, honoring actual-app intent or reporting its blocker. Use proportional
evidence, avoiding a blanket sweep for unrelated changes. Use tests/API evidence
for functional behavior and reuse valid prior UI evidence. For a material
layout/interaction risk or reproduced visual defect, inspect the relevant flow when
authorized.

Choose only cases relevant to the named risk, and leave unchanged states and screens
out of the matrix. Stop when those cases are checked. Verify actual CSS viewport,
zoom, and screenshot provenance before diagnosing a cropped or scaled image.

Inspect usability directly: review density, discoverability, and task completion as
well as containment, because passing builds, DOM dimensions and screenshot metadata
miss these. Check installed-native behavior on the native surface; browser review
does not cover it.

## Brief an independent inspector

If an independent visual role is requested, use the session/subagent topology in
[coordination](../../orbyn-workflow/references/project-policy.md#delegation-and-host-configuration).
Give that inspector the candidate checkout/ref, URLs, exact states, viewport sizes,
themes, and a Markdown report destination. Specify whether its assignment is
capture-only or includes analysis, following the user's current authorization.
Report delegated pixel review as delegated; do not label it personal inspection.

## Fix, recheck and report

Fix reproduced problems and request a targeted recheck. Retain failed attempts and
unverified states. If browser permission or export is rejected, report the blocked
action and use an allowed handoff; do not bypass it through another browser, port,
transport, or indirect export. Integrate a scoped checkpoint only when its
acceptance evidence supports it, and report it as a checkpoint rather than the whole
task.

## Deliver a preview the human can use

When presenting new or changed UI for human design review, offer or reuse the live
feedback method in [review packages](review-packages.md), without requiring a
separate invocation. Reuse an existing component preview for a small button change;
respect audit-only requests and avoid rebuilding unchanged pages. For requested
interactive comments, settings or durable records, deliver that path. Cover each
affected page, component/instance and control; bind feedback to actual source/state
and separate browser draft, submitted feedback, repo save and accepted design
decisions. Keep requested durable source/settings/reviews with the consuming design
owner, then reconcile its existing design document and focused regressions within
scope.

For a requested prototype or preview, produce the actual app route/story or a
self-contained HTML artifact as appropriate, open it with supported host tools when
possible, and provide the verified link plus states to try. Follow the
[prototype method](prototypes.md) for deterministic demo controls, simulation labels,
rendering evidence and transfer into the real frontend/backend.

For stateful flows, use [behavior preview](behavior-preview.md) to connect relevant
scenarios, state/rule IDs and actual checks. Hand lifecycle statecharts to `architect`
and critical property checks or drift to `tdd`; retain visual, model and
implementation evidence separately. Small visual work stays small.

Use the [artifact lifecycle](../../orbyn-workflow/references/artifact-lifecycle.md)
for storage, server lifetime and cleanup. Confirm the human can exercise the
interaction; a source file or screenshot alone leaves that open.

## Audit an existing surface from evidence

Use for "review/refine/clean up this UI" or a design handoff, not for a change
you are verifying. Read-only on product source: write nothing except a plan
folder the user names or approves, and record documentation changes in the plan
for its executor.

1. **Select the surface.** Honor the stated scope; otherwise one deployable app
   and one surface family for a main task. Say what you picked. Trace from routes
   and layouts through components, variants and resolved tokens. A link counts
   only if proven by render, import, props, config or inheritance; similar names
   or proximity do not.
2. **Reconstruct the product's own system.** Check the design document and local
   guidance. Use one only if it is current and governs this surface; drafts and
   migrations are intent. Resolve tokens and variants on the traced path. Missing
   documentation is not a finding. Note audited surface, sources, documented
   decisions, owners and consumers, explicit exceptions (`None documented` if no
   source names one).
3. **Prove each finding.** Candidates from search or repetition are not findings.
   Keep one only with all three: a binding rule for this property and scope (or a
   direct contradiction within one task); proof the owner or value reaches the
   surface at runtime; one correction the evidence determines, naming the token,
   variant or exemplar. Reject candidates that need invented intent or offer
   alternatives. Source proves token, type, colour, spacing, layout, copy and
   variant violations. Hierarchy, density, clarity and discoverability need a
   screenshot or user evidence. Drop functional bugs, accessibility semantics,
   routes and performance unless asked.
4. **Vet.** Re-open every cited line and try to falsify it. Delete a candidate
   when it mismatches the code, the rule does not govern it, a deliberate reason
   exists, several corrections fit or another finding shares its root cause.
5. **Report.** Top three at most, ordered by confidence, user impact, reach and
   cost: a table of problem, evidence, one proposed change, scope, confidence.
   Then one "improve first" pick, or "No supported findings were found." Ask
   which to plan; never implement unasked.
6. **Write plans** for selected findings, one per change. A plan is self-contained
   because its executor has not seen this audit: outcome, commit written against,
   evidence chain (surface, problem, design evidence, owner, affected surfaces,
   uncertainty), design decision, reuse (tokens, components, exemplar path; a new
   primitive only with proof the system cannot express it), numbered changes with
   path, change, what to preserve and how to verify, scope (inherit, verify,
   exclude), validation (task, states and viewports, reuse check, exact repository
   command), stop conditions, and the decision to record in design documentation
   after acceptance. Re-open sources first and reconcile an existing plan rather
   than duplicate it.

## Check for objective defects

Run `python3 scripts/ui_check.py <source>` from the skill folder before review. Exit 1 means
an image with no alternative text or disabled zoom. Everything else is a warning to read
against the code: focus rings removed, buttons and links with no name, clickable `div`s,
positive `tabIndex`, `transition: all` and missing reduced-motion support. The report lists
skipped files, and counts raw controls beside shared ones, which shows drift worth tidying.

It judges no taste, and a pass says nothing about how the screen looks, so it never replaces
this review. On one real application it gave no errors and 7 warnings, of which 4 were real
candidates: a focus style on a wrapper with a different name still reads as missing.
