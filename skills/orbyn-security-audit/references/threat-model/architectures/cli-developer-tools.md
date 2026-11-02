# CLI and developer-tool checks

Use for a tool that runs in a local workspace with configuration, an environment, subprocesses, plugins and remote services. Do not assume it builds or releases software. Environment and process behaviour depend on the platform: record what the evidence supports and leave the rest as gaps.

## Evidence questions

1. Who can change repository settings, user settings and environment values, and which wins for an actual invocation?
2. Which settings select commands, executable locations, working directories or plugins? What stops opening an unfamiliar project from granting it execution?
3. Which principal runs the tool, each subprocess and each plugin? Which credentials are inherited, passed on purpose, omitted or acquired later, and for what remote operation?
4. Where can sensitive values reach normal output, diagnostics, retained logs or uploaded artifacts, and who reads each, including after failure or cancellation?
5. What is the intended read and write set? How do absolute paths, parent components, symbolic links and targets changed between selection and use alter the object actually touched?
6. Which identities bind a selected input or output to a remote request? Where a build or release exists, which separate decision authorizes promotion or execution?
7. What survives interruption, retry, cleanup, revocation or a switch to another workspace? Who can resume pending work?

## Trace

Repository to configuration to effect; tool to plugins and subprocesses; environment and credential lifetime; output and log audiences; path selection to object access; local selection to remote decision; interruption and recovery. A workspace-trust label is not containment. Inspecting data is not permission to execute it. Name the allowed operation and the disallowed effect; mere configurability is not a defect.

## Scenario families

- A repository author influences a setting that reaches a command or file operation under greater local authority.
- A credential reaches a subprocess, plugin, reader or log outside its intended scope. An environment variable existing is not leakage, and output filtering is not proof a child never received it.
- A path or link causes an operation outside the authorized workspace. Separate the selected name from the accessed object.

## Checks to propose (all `not_run`)

- A disposable synthetic workspace with harmless inside and outside sentinels: a permitted operation, repository-selected command or file change, an outward symbolic link, a target changed between selection and use, an interrupted and resumed operation. Pass: the allowed effect occurs and each disallowed one is refused at its enforcing boundary.
- Synthetic scoped credential markers and an isolated receiver: follow environment, child and plugin access, output, logs, transmission and retry. Pass: no forbidden reader sees a marker. Upload acceptance alone says nothing about an unreached promotion boundary.
