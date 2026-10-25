# Claude Code

Read [AGENTS.md](AGENTS.md), then only the shared skills relevant to the task.
Canonical skills are linked at this outer workspace's `.claude/skills`. Resolve
the nested target and read its own root/nested instructions and local skills in
place, including any future project-owned AGENT.md or AGENTS.md. Target rules,
user scope and host permissions govern their applicable boundaries; resolve real
conflicts before dependent work. No shared skills are installed into targets.
Workspace setup does not apply optional model presets or configure MCP providers.
