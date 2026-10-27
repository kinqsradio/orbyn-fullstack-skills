# A preview that starts with one useful task

Synthetic brief: let someone choose a task and add a focus session, while judging
hierarchy and recovery in a wide window and a narrow pane. This is a standalone
web interaction sketch, with no existing product components or backend attached.

## Open and try

Open the self-contained [preview](focus-session/preview.html) in a local browser.
No package install, server, network asset or account is needed. The agent should
open and inspect it using available authorized tools before reporting rendering
or interaction outcomes. Everything resets on reload; calendar actions are
simulated in memory and never reach the Orbyn application.

1. Select a task, choose a duration/start and add a focus block. Check that the
   planned item identifies the chosen task and can be removed.
2. Expand **Preview controls**, choose **First save fails, then retry works**, and
   add a session note. Submit and retry: the first attempt retains the draft and
   the retry adds one block. Scenario changes deliberately reset the workspace.
3. Choose **Slow save**, submit and reset before it finishes. The old response
   must not repopulate the reset view. Pending work disables duplicate submission.
4. Choose **No tasks yet** and add the sample tasks. Check keyboard selection,
   visible focus, long-title wrapping and access to the form in a narrow pane.

## Why this composition

Task choices and the session form have distinct roles. Selection is visible;
one submit action creates the block. Notes and reviewer scenario controls are
disclosed on demand. The action's simulation boundary stays visible. Neutral
surfaces, a small type hierarchy and one accent connect the composition; these
are example choices, not required tokens for another product. Narrow layout
stacks the same task and form, with a direct link to session details.

The example avoids a default dashboard of every feature, a graph requiring zoom,
decorative inactive actions and repeated status messages. Do not simplify away
the selected target, error, retained draft or real action consequences.

## State and implementation handoff

| State | Visible result | Contract |
| --- | --- | --- |
| Ready | Selected task and editable form | Target and details identifiable |
| Adding | Pending submit label | Prevent accidental repeat submission |
| Failed | Inline error and retry | Draft and target retained |
| Added | Planned block and status | One local effect for the completed submission |
| Reset | Fresh workspace | Earlier responses cannot change the new generation |
| Empty | No-task explanation and sample action | Submission unavailable until a task exists |

For production adoption, use the consuming product's existing tokens/components,
real task identities, calendar/time-zone semantics, server authority and durable
operation contract. Remove reviewer controls and connect actual adapters. Browser
exercise of this sample does not verify integration, native interaction,
screen-reader behavior, representative-user usability or deployed accessibility.
