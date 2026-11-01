# Dependencies, packaging and maintenance

The bundled selected support is a maintained MIT adaptation of Anatomy revision
`1482e8469b0a9e0d8cc18ea2740a01423d29ae80`. Original source hashes and maintained
hashes have different meanings. Read the source record, source manifest and
snapshot before changing the selection. Preserve Ryan's MIT notice and source
lineage; authored guidance does not erase the imported code's origin.

## Runtime and peers

Core drawing/Node helpers use built-in modules. Browser capture additionally needs
an existing Chrome/CDP and a Node runtime with supported WebSocket behavior. A
source-declared minimum is not a tested platform matrix. Record actual executable
paths/versions rather than rely on login-shell PATH. The maintained browser path
requires native WebSocket and does not auto-respawn with experimental flags. The
qualified local runtime is Node 22.16.0; upstream Node 20 and React 18 minimums are
not runtime qualification of those versions. Denied browser/OS surfaces
remain blocked; no global install or automatic privilege change.

React drawing requires consumer-owned React/ReactDOM/compiler/bundler versions.
The qualification fixture has its own exact peer lock, separate from library or
application dependencies. Use the actual consuming lock in a real project. Npm
lifecycle scripts and runtime downloads are not implicitly authorized; a prepared
lock does not prove installed bytes or browser hydration. PDF inspection requires
an existing permitted renderer; WebGL needs its recorded renderer/context.
`scripts/still_to_layers.py` is opt-in: it needs OpenCV in the project's environment,
which only the user can approve for a job, and it exits
with the install command when it is missing.

## Package an authorized artifact

The local `scripts/package_figure.py` helper (relative to the skill root) can copy
a selected core/react/print/webgl/3d/full module set into a fresh explicitly owned
destination. Use its `--help` and choose the actual mode; `--input LABEL=PATH`
records separate model/style/asset hashes without copying those files or private
absolute paths. Existing destinations and unsafe source paths are rejected.

Select only needed drawing modules and their recursive relative imports, file
reads and spawned helpers. Preserve relative paths and CSS/model/assets. Do not
copy this skill's instructions/catalog or source research into the target. Check
for escapes, symlinks, existing output and incompatible source before writing.
Stage or use a fresh destination; never erase an existing artifact to simplify
replacement. Keep a recoverable previous output when replacement is selected.

The kit fingerprint covers its declared kit/inline scope only. Separately hash the
reference/method revision, model, style, fonts/assets, build, host/runtime and chosen
inputs. A matching kit hash cannot prove those values, an immutable cache, complete
source correspondence or image quality. Experimental/publisher/history helpers
are excluded and must not enter a package through a latent export/import.

## Update with evidence

Use upstream-review for a fresh pinned comparison, selected closure and licenses.
Keep raw downloads ignored. Read imports, dynamic read/spawn paths and applicable
tests/fixtures before adoption. Record original/adapted hashes and exact changes;
refresh both source and distribution manifests through their actual owners.
Run bad and legitimate controls for changed helper semantics, then relevant core,
React, browser, print, GPU and beta checks at the claimed surfaces. Preserve first
failures and unrun cells. Do not update a source pin to imply tests that never ran.

A local package/build success, library check, browser artifact, OS/renderer matrix
and agent trial are separate evidence. Deliver exact scope, reproducible commands,
owned output, verified controls and remaining blocks. No publisher, Git auth,
force-push, automatic session extraction or external write follows from an
illustration request.
