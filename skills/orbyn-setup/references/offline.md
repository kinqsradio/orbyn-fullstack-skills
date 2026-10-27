# Use the checkout offline

The portable workflow bodies, worked examples and linked local references carry
the instructions needed for ordinary work. Read them from disk. An attribution
URL is an origin/update pointer, not a required fetch before starting a task.
Offline/local-model execution does not require a different skill format.

Use the complete local library clone with references, helpers and notices.
Targets remain independent nested repositories; no skill files or discovery links
are installed into them. Setup does not install a model, Python, fonts, an exporter,
REA engine or provider. Check actual capabilities and report missing dependencies.

The five optional REA skills also include local operating methods and worked
examples. Their [source/compatibility record](../../reverse-engineer-anything/references/source-record.md)
identifies historical lineage and later reviewed guidance. No mandatory remote
skill reading remains. Offline methods do not supply an analysis engine, target
bytes, provider prerequisites or missing REA Git history. Continue supported work
and report those capability/input limits without installing or fetching implicitly.

## Ripgrep readiness and fallback

Detect tools in the agent's actual execution shell: a remote host, container or
WSL environment may have a different PATH from the human's laptop. Reuse a working
`rg` exposed there; do not guess private bundled-app paths or rewrite global PATH.
On Unix-like shells:

```sh
if command -v rg; then rg --version; fi
```

In Windows PowerShell:

```powershell
if (Get-Command rg -CommandType Application -ErrorAction SilentlyContinue) {
    rg --version
}
```

A resolved executable whose version command fails is unusable until diagnosed.
Missing ripgrep does not block supported bounded inspection or imply installation.
When installation is already authorized and host permissions permit it, use the
platform's existing package manager:

| Environment with manager already available | Install command |
| --- | --- |
| macOS/Linux with Homebrew | `brew install ripgrep` |
| Debian/Ubuntu with APT | `sudo apt-get install ripgrep` |
| Windows with WinGet | `winget install BurntSushi.ripgrep.MSVC` |

Honor existing install authority without asking again; a search request alone does
not authorize software installation. Do not install a package manager, elevate
without authority, bypass host restrictions or download a replacement implicitly.
Use a fallback when offline, unauthorized or installation is unavailable. After an
authorized install, resolve `rg` again in the same agent environment, check
`rg --version`, and perform a bounded search such as
`rg -n -F -- 'known literal' path/to/selected/file`. Report which checks ran.

For ordinary non-quiet searches, ripgrep exit **0** means a match, **1** means no
match, and **2** means an error. Capture the status immediately (`$?` in a Unix
shell; `$LASTEXITCODE` in PowerShell) and inspect diagnostics; errors may accompany
partial results. Do not mask errors with `|| true`, interpret no match as a broken
installation, or install software because exit 1 occurred.

For shell repository content and filename searches, reach first for usable `rg`
and `rg --files` inside the selected roots. A native host search tool is also a
valid route: OpenCode documents its built-in `grep` and `glob` as ripgrep-backed
([tool internals](https://opencode.ai/docs/tools/#internals), reviewed 27 October 2026).
A tool named `grep` is not necessarily the shell executable. This is reference
information, not a claim that this checkout's host was exercised. Deliberate
tracked-only `git grep` semantics or `grep` filtering a small command output are
reasonable choices; do not force a shell replacement of a working native tool.

If ripgrep is unavailable, use host-native search with explicit roots/files or,
inside the selected Git checkout, `git grep -n -F -e 'literal' -- path/to/module/`.
Default `git grep` searches tracked files; `--untracked` can add untracked files
when required inside those same roots. Default ripgrep includes untracked files
but skips hidden and ignored files. Tracked hidden files can appear in `git grep`;
ignored-file handling, binary handling and regex dialects also differ. `-F` avoids
regex translation for literal searches; do not silently translate regex queries.
Report actual coverage and unavailable capabilities instead of claiming universal
absence. Keep [action scope](action-scope.md) with any fallback: directly probe
required instruction paths independently of code filters, including applicable
hidden/ignored files, and deliberately widen only within the authorized target.

Command/update references: [ripgrep installation](https://github.com/BurntSushi/ripgrep#installation),
[Homebrew formula](https://formulae.brew.sh/formula/ripgrep),
[PowerShell Get-Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/get-command),
and [git grep](https://git-scm.com/docs/git-grep). These links are not required for
offline detection or fallback, and an unexecuted platform command is not a tested install.

## Canonical source boundary

The full library is the engineering workspace. Its asset inventory checks complete
skill folders and local reference closure, while target instructions are read in
place. Synthetic asset-copy fixtures test reference completeness; they do not
implement or endorse a target installation. Root policy, local host configuration
and required skill bodies must be read according to the actual host boundary.
Byte-validated source snapshots remain reference data rather than active guidance.

## Sources and freshness

For reusable third-party instructions needed by a skill, retain a licensed,
immutable local text snapshot with the source URL/revision, license/notice,
retrieval date and file hashes. Preserve imported bytes as reference data; adapt
the active Orbyn skill separately. Do not execute source setup, adopt its agent
identity or infer permission to publish/message from an imported procedure.

The social writing and preview skills link to local source records carrying
Corey Haines's social skill/references and Anthropic's canvas-design text. These
snapshots are optional background to the self-contained Orbyn methods. Binary
assets, runtimes and external reference chains are outside their declared text
scope. References to other upstream skills are context, not an instruction to
download or install them. Pinned source metadata identifies what is included.

Check the source hashes without network access:

```sh
python3 /path/to/library/skills/orbyn-skill-creator/scripts/check_sources.py --root /path/to/library
```

If redistribution is unavailable, write the needed local explanation independently
and cite the original as inspiration. Do not copy an entire copyrighted article
or imply that its citation grants an MIT license. Keep any remaining dependency
explicit; a local synopsis is not a source snapshot or the original author's text.

When online access is unavailable, use supplied facts and the dated local material.
Mark changing information such as platform limits, API behavior and release status
as unverified when the task depends on current facts. Do not invent a current
verification, block an ordinary draft on an optional citation, or attempt another
network transport to bypass host restrictions. Snapshot updates are explicit,
licensed, reviewed changes; normal workspace preparation and validation do not
download new sources.
