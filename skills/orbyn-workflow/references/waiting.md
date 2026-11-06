# Wait without polling

Run a command likely to outlast the foreground limit in the background where the
host supports it; a host may also move a long call there by itself. The host
reports the result when the job finishes.

Never poll a background job or child with `sleep`, `ps`, `pgrep`, `top` or
repeated reads of its output. Each check is a full model turn that learns
nothing, and in a long autonomous run those turns are most of the waste. Instead:

- do other independent work while the job runs, or
- end the reply and let the host wake you with the result.

Read the output once, when the host says the job has finished. A host-native
watch that wakes you on a condition (for example an until-loop monitor) is not
polling, because it costs no model turns while it waits.

Poll only external state the host cannot report, such as a CI run or a deploy, at
the pace that state actually changes: one check near the expected finish time,
not one a minute. The [PR iteration playbook](../playbooks/pr-iteration.md) covers CI watches.

## Commands that run long

Start these in the background from the first call, with the host's background run or
`bg.sh start` (`bg.py` on Windows), then do other work:

- The library test suite: `scripts/run_tests.py` (about two minutes, longer under load)
- Live evals: `eval_run.py --live`, and subagent eval trials
- CI watches: `gh pr checks <n> --watch`
- A project's full build, test or end-to-end suite, and anything else likely to pass
  the host's foreground limit

Run `bg.sh wait` itself in the foreground: it is the one blocking wait.

## Pick the wait by what the host can do

This works on every host: Claude, Codex, DeepSeek, Gemini, OpenCode or any other.
Check what the host's tools offer, top row first:

| The host can | Wait like this | Seen on |
| --- | --- | --- |
| Wake you when a background job or child ends | Start it in the background, then do other work or end the reply | Claude Code (`run_in_background`, task notifications) |
| Wait on a running command or child with a timeout | One wait call with the longest timeout the host allows, not many short ones | Codex (`write_stdin` with no input, up to 5 minutes; `wait_agent`, up to 1 hour) |
| Only run shell commands | `bg.sh` (or `bg.py`), below | Any host with a shell |

When you cannot tell which row fits, use the native helper. A host's own instruction, such as a
cap on wait length, wins over this table.

## The native helper

Only the host can give an idle agent another turn, so no script adds a wake-up
where the host has none. What a script can do is make a long wait cost one turn.
The helper is a native shell script, so no Python is needed: [`bg.sh`](../scripts/bg.sh)
(POSIX sh under bash, dash or zsh; macOS, Linux and Git Bash on Windows). On Windows
without Git Bash, use `bg.py`. `harness.py resolve` prints the commands for
this platform with the absolute path, so an agent in any repository can run them:

```sh
sh <skill directory>/scripts/bg.sh start --name tests -- python3 -m pytest
sh <skill directory>/scripts/bg.sh wait <job id> --max 540
```

[`bg.py`](../scripts/bg.py) (standard library only) has the same interface and stays as
the fallback where a shell script cannot run.

`start` runs the command detached and prints a job id at once; do other work. `wait`
blocks inside the script until the job ends or `--max` seconds pass. It prints JSON
with the state, exit code and the end of the log, and exits with the job's own code,
`3` while it is still running or `4` if its supervisor died. Set `--max` just under
the host's tool timeout; when it returns `3`, call `wait` once more. `status` reads a
job without waiting. `--on-done '<shell command>'` runs when the job ends, with
`BG_JOB_ID`, `BG_EXIT_CODE` and `BG_LOG` set, for an unattended runner that resumes
the agent's session through its own CLI. Jobs live under `$ORBYN_BG_ROOT` or a
per-user temporary folder.

Where the host wakes you itself, use its own background run instead. Where the
command fits inside the tool timeout, run it in the foreground. Never split one
wait into many short sleeps.
