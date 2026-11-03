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

## Hosts that cannot wake you

Only the host can give an idle agent another turn, so no script adds a wake-up
where the host has none. What a script can do is make a long wait cost one turn.
On any host with a shell, use [`bg.py`](../scripts/bg.py) (standard library only,
POSIX and Windows):

```sh
python3 <skill directory>/scripts/bg.py start --name tests -- python3 -m pytest
python3 <skill directory>/scripts/bg.py wait <job id> --max 540
```

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
