# Mobile application checks

Use for a device owner, app storage, operating-system services, other apps and a backend. Do not infer an operating system, storage protection, credential mechanism or backend authorization from the label. OWASP MASVS control groups (storage, authentication and authorization, platform interaction, privacy) guide the questions; this is not a MASVS assessment. Device possession, an unlocked screen, the current app account and backend permission are four separate facts. A client check limits what the device shows or sends; the backend decides authorization. Offline replay and conflict handling have no bundled checks: record the synchronization boundary as a gap or a second architecture with its own owner.

## Trace

1. Local records, attachments, thumbnails and exports from creation to deletion. Separate a lost locked device, a lost unlocked device, an account switch and a restored copy. Name the read capability each needs.
2. Active account, record owner and entitlement before and after sign-out, account change and revoked assignment, including writes interrupted by shutdown. Hiding a screen, deleting locally and invalidating on the backend are different outcomes.
3. Links and shared content from external producer to entry point to navigation, lookup and backend operation. Which object, account and action fields can an attacker influence? Displaying an id grants no authority over it.
4. Push delivery, shown content and tap action are three things. Check stale notifications after account switch and restart against the current account, and whether a fresh authority decision precedes the action.
5. Each offline action's creator, resource, base revision and operation id from queue to upload, acknowledgement and retry. A successful upload does not show the right account or revision was authorized.
6. Credential refresh and revocation across disconnection. A refresh started for account A may finish after B is active; which request and queue item receives the result?
7. Sharing to other apps, backups, logs and screenshots, only where the design includes them.
8. Recovery: termination during cleanup or sync, restart with an old queue, a restored replica, an acknowledgement lost after a server write.

## Checks to propose (all `not_run`)

- Account switch, offline use and reconnect: inspect retained records and queue ownership.
- An external entry with an out-of-scope resource, beside an authorized positive case.
