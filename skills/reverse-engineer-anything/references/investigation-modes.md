# Select the evidence path

Use available local schemas/help to determine exact operations and fields. Names
below identify REA capabilities when present, not a requirement to install them.
Use [local tools](local-tools.md) for the first bounded observation when the host
already has a suitable reader. Continue into a REA mode only for a missing fact,
retained-evidence need or authorized runtime observation. Preserve the same target
digest, selection and unknowns across that handoff.

| Question / target | First useful observation | Deeper work and boundary |
| --- | --- | --- |
| Unknown package or container | `inspect_artifact` identity, inventory and coverage | Inspect selected entries. Extract only into owned storage with path/size controls; do not run extracted code. An omitted or unreadable child stays unknown. |
| Native executable | `open_binary` and relevant format/provider availability | Select procedures, imports or sections before analysis. Preserve architecture, address space and load mapping; a static call relationship is not an execution trace. |
| Electron, ASAR or JavaScript bundle | Artifact inventory and selected local sources | Use supported JavaScript analysis/reconstruction. Keep source maps and source correspondence explicit. Reconstruction is not original source identity or successful execution. |
| APK | Package metadata and selected resources/code | Use supported Android inspection. Permission declarations do not prove use; signing metadata or digest consistency does not establish publisher trust. Device interaction is separate runtime scope. |
| Two artifact versions | Identity and comparable inventory for each side | Compare equivalent scopes and retained records. Equal observed root bytes do not establish equal runtime behavior or equal unexamined container contents. |
| Runtime-only behavior | Exact process/device and allowed effects | Choose launch, attach, debugger, network or UI capture according to the question. Plan capture bounds and cleanup; a working connection is not target ownership. |

For JavaScript, select files/chunks relevant to the question and account for
lazy, inaccessible or omitted sources. If the server supports route inventories,
request only relevant paths and page retained facts. Call them **static route
candidates**. Do not request those URLs or claim application-wide coverage from
that inventory. A compact view reduces delivery, not necessarily analysis work.

For native analysis, keep file offsets, virtual addresses and image-relative
addresses distinct. Account for same-address aliases, unresolved indirect calls
and provider limitations. Engine-free metadata inspection, when supported, can
answer a narrower question without starting a decompiler. Parsing bytecode or
certificate tables does not by itself decompile, execute or verify signatures.

For runtime capture, record executable identity and capture conditions. Attaching
to a user-owned process generally owns the connection, not permission to kill
that process. Launch ownership and target side effects must come from the actual
operation contract. Path selection and working directories are not sandboxes.
UI observation and UI actions have different effects. Cleanup must address the
resources acquired without undoing or killing unrelated user work.

If a tool reports partial results, preserve them and their limitations. Seek one
specific missing observation when it changes the answer; avoid an unbounded
catalog dump, whole-application decompilation or runtime session by default.

See [evidence and recovery](evidence-and-recovery.md) before retrying or comparing.

## Task for an exported desktop-application environment

When asked for a task on an exported desktop-application environment, work from a
capture's described net change, a CLI-only flow. Check the installed commands first.

- Only files under the owned paths can be graded; read what changed between the
  first and last version of each.
- Write the prompt in the user's words and the app's terms, never file formats,
  paths, keys or the checks themselves.
- Keep checks that state only what the user did. Drop changes that follow from how
  the app saves (format rewrites, renumbered lines, counters) and values it stamps
  (times, assigned ids, window sizes). Prefer a few robust checks: whole lines over
  positions, rows by meaningful columns, "at least" when more is allowed.
- A valid task fails on the seed and passes on the captured end state. A refusal
  names the check to fix; do not weaken it to pass.
- Do not fetch a vendor package yourself; ask the user for the file they installed
  from. The seed is the user's real data: keep it local, and run no agents unless
  asked.
