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

A host without background jobs runs the command in the foreground with a timeout
long enough for it to finish. Do not split one wait into many short sleeps.
