# Shell: contracts to preserve

## Resolve the target

Resolve the shebang, actual shell/version and OS utilities. POSIX sh, Bash and zsh differ. macOS ships Bash 3.2 and BSD utilities: `sed -i` and `date` flags differ from GNU/Linux.

## Apply at the affected boundary

- Pass arguments as separate quoted words or native arrays, and preserve `"$@"`. Never treat JSON escaping as shell quoting or eval untrusted text.
- Inspect every external effect and its exit status. `set -e` has conditional and pipeline exceptions. POSIX.1-2024 adds `pipefail`, but check the deployed shell rather than assuming every sh provides it.
- Own temporary paths with `mktemp`, and trap cleanup only for resources you created. Validate destructive destinations: `rm -rf "${dir:?}/build"` stops on an empty value. Check `cd` too: `cd "$dir" || exit 1`.
- Do not reset or clean arbitrary Git work, or remove a user's or another worker's output, to make a retry succeed.
- Keep credentials out of traces, logs and command-substitution output. Use structured APIs or body files for multiline content.

## Worked failure and correction

Preserve a filename containing spaces as one argument, and stop option parsing:

```sh
if ! cp -- "$source_path" "$destination_path"; then
    printf '%s\n' 'Copy failed' >&2
    exit 1
fi
```

Check that the actual utility supports `--`. Quoting alone does not stop a leading
dash being read as an option.

## Traps to check

- Do not loop over `$(ls)` or `$(find ...)`: filenames split on whitespace and glob. Use a glob, or `find ... -print0 | xargs -0` where supported.
- Read lines with `while IFS= read -r line`. In `cmd | while ...`, the loop usually runs in a subshell, so its variables vanish afterwards; redirect from a file instead.
- Use `printf` for data: `echo` varies on backslashes and leading dashes.
- Use `curl --fail` when a script depends on the response. By default an HTTP 500 exits 0.
- Separate declarations from status-bearing substitutions: `local value=$(cmd)` and `export value=$(cmd)` report the builtin's status, not cmd's. Declare, assign and check, then export. `local` is not POSIX sh.

## Evidence to report

Run syntax checks for the actual interpreter, ShellCheck where configured, and authorized disposable failure/recovery fixtures. bash -n does not execute the path, prove portability or validate a remote deployment.

For CLI input/help/stdin/result design or real PTY prompt/resize/signal checks,
use the [CLI contract](../../architect/references/cli-contract.md). Shell quoting
alone does not qualify that interface.

## Primary references

Reviewed 24 October 2026: [GNU Bash quoting](https://www.gnu.org/software/bash/manual/html_node/Quoting.html), [GNU Bash set builtin](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html).

Focused semantics reviewed 30 October 2026: [ShellCheck SC2155](https://www.shellcheck.net/wiki/SC2155).

Reviewed 1 November 2026: [POSIX.1-2024 pipelines](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html).
