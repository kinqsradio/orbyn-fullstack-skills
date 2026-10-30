# Shell: contracts to preserve

## Resolve the target

Resolve the shebang, actual shell/version and OS utilities. POSIX sh, Bash and zsh differ; macOS utilities and older Bash may differ from GNU/Linux.

## Apply at the affected boundary

- Pass arguments as separate quoted words or native arrays; preserve "$@". Never treat JSON escaping as shell quoting or eval untrusted text.
- Inspect every external effect and its exit status. set -e has conditional/pipeline exceptions; check pipefail support in the actual deployed shell rather than assuming all sh implementations provide it.
- Own temporary paths, validate destructive destinations and trap cleanup only for created resources. Do not reset/clean arbitrary Git work or remove a user's output to make a retry succeed.
- Keep credentials out of traces/logs and command substitution output. Use structured APIs or body files for multiline content; account for filename newlines and utility-specific option parsing.

## Worked failure and correction

Preserve a filename containing spaces as one argument:

```sh
if ! cp "$source_path" "$destination_path"; then
    printf '%s\n' 'Copy failed' >&2
    exit 1
fi
```

Validate option-like filenames or use a supported -- delimiter for the actual
utility. Quoting alone does not stop option parsing.

## Evidence to report

Run syntax checks for the actual interpreter and authorized disposable failure/recovery fixtures. bash -n does not execute the path, prove portability or validate a remote deployment.

## Maintainability and checks

Separate declarations from status-bearing substitutions: in supporting shells,
`local value=$(cmd)`, `export value=$(cmd)` or `readonly value=$(cmd)` can report the
builtin's status instead of cmd's failure. Declare, assign with an explicit status
check, then export/mark readonly as needed. A literal export is legitimate;
local is not portable POSIX sh. Check the actual shell, and never let a failed
retry erase another worker's output or checkout.

## Primary references

Reviewed 24 October 2026. These independently written instructions and synthetic
examples are usable offline. The links identify semantics and update evidence;
verify compatibility with the project's target before using newer APIs.

[GNU Bash quoting](https://www.gnu.org/software/bash/manual/html_node/Quoting.html), [GNU Bash set builtin](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html).

For CLI input/help/stdin/result design or real PTY prompt/resize/signal checks,
use the [CLI contract](../../architect/references/cli-contract.md). Shell quoting
alone does not qualify that interface.

Focused semantics reviewed 30 October 2026: [ShellCheck SC2155](https://www.shellcheck.net/wiki/SC2155).
