#!/usr/bin/env python3
"""One table of host instruction pointer files; AGENTS.md stays the only rule set."""
from pathlib import Path

CLAUDE_BODY = '''# Claude Code

Read [AGENTS.md](AGENTS.md) and resolve the harness first (its top section), then only the shared skills relevant to the task.
Canonical skills are linked at this outer workspace's `.claude/skills`. Resolve
the nested target and read its own root/nested instructions and local skills in
place, including any future project-owned AGENT.md or AGENTS.md. Target rules,
user scope and host permissions govern their applicable boundaries; resolve real
conflicts before dependent work. No shared skills are installed into targets.
Workspace setup does not apply optional model presets or configure MCP providers.
'''

# path -> exact generated text. Pointers defer to AGENTS.md; none copies its rules.
FILES = {
    'CLAUDE.md': '@AGENTS.md\n\n' + CLAUDE_BODY,
    'GEMINI.md': '''# Gemini CLI

Generated pointer. The one rule set for this library is AGENTS.md, imported below.

@./AGENTS.md
''',
    '.github/copilot-instructions.md': '''# Copilot instructions

Generated pointer. Read `AGENTS.md` at the repository root and follow it; it holds
the rules for this library. This file exists because some chat hosts (JetBrains,
Visual Studio, Xcode) cannot import it.

Most important rules:

- Resolve the harness first, as the top section of AGENTS.md describes.
- Never commit, push, merge or publish without the user's explicit approval.
- Credit every source, tool and model, and fill in the Agent disclosure honestly.
''',
    '.aider.conf.yml': 'read: AGENTS.md\n',
    '.continue/rules/agents.md': '''---
name: Orbyn Engineering rules
alwaysApply: true
---

Generated pointer. Read `AGENTS.md` at the repository root and follow it; it is the
one rule set for this library. Resolve the harness first, and never commit, push,
merge or publish without the user's explicit approval.
''',
}

# Files that would shadow AGENTS.md in Zed or Junie; they must never exist.
FORBIDDEN = ['.rules', '.cursorrules', '.windsurfrules', '.clinerules', '.junie/AGENTS.md']


def problems(root):
    """Return drift messages; empty means every pointer file matches the table."""
    root = Path(root)
    errors = []
    for name, text in FILES.items():
        path = root / name
        if not path.is_file():
            errors.append(f'Missing host instruction file: {name}')
        elif path.read_text() != text:
            errors.append(f'Host instruction file differs from generated text: {name}')
    for name in FORBIDDEN:
        if (root / name).exists() or (root / name).is_symlink():
            errors.append(f'Forbidden file shadows AGENTS.md: {name}')
    return errors


def write(root):
    root = Path(root)
    for name, text in FILES.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
