# Any task that is not code

Research, answering questions, writing, triage, reviews of other people's work: the
same rules apply as for code. With no target repository, resolve the harness for the
library itself (`harness.py resolve --target <library>`) to get the tiers, limits and
work mode.

## Delegate by volume, not by kind

A child starts with an empty context, so it costs more than it saves on small work.
Count what the task will read:

| The task reads | Do |
| --- | --- |
| A few files, pages or messages | Do it yourself. A simple question never needs a child |
| About five or more independent sources (threads, issues, pages, logs, files) | Give the reading to scouts on the cheapest tier, a batch each, within `max_children` |
| A finished draft or diff that matters | One reviewer child before it goes out |

The lead keeps the judgement: choosing what to read, deciding, writing the final
answer and anything that is posted, sent or merged. Scouts read and check; they never
post, send or decide.

## Brief a scout

Give each scout its batch (links or paths), what to check and the shape of its answer:
one short note per source with the verdict, the evidence (a link, a line, a command and
its result) and what it could not confirm. Raw pages stay in the scout's context; only
the notes come back, which is where the saving is.

## Example

Answering GitHub discussions: the lead searches and picks 20 candidate threads, sends
two scouts 10 threads each to read in full and check against source or docs, then
writes and posts the few answers worth posting from their notes. Reading all 20
threads in the lead's own context costs several times more.
