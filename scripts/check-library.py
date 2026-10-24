#!/usr/bin/env python3
"""Validate library structure and attribution; no network or model calls."""
import importlib.util
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 11):
        print('Python 3.11+ is required for library validation.', file=sys.stderr)
        return 1
    errors = []
    if subprocess.check_output(['git', 'ls-files', '--', 'openSrc/'], cwd=ROOT, text=True).strip():
        errors.append('openSrc is local research material and must not be tracked')
    if (ROOT/'project-skills').exists() or (ROOT/'project-skills').is_symlink():
        errors.append('Consumer-owned project-skills must stay in the consuming repository, outside the public library')
    def require(ok, message):
        if not ok:
            errors.append(message)
    catalog = json.loads((ROOT/'skills/catalog.json').read_text())
    provenance = json.loads((ROOT/'provenance.json').read_text())['skills']
    names = {entry['name'] for entry in catalog['skills']}
    require(names == set(provenance), 'Catalog/provenance coverage differs')
    for name in sorted(names):
        skill = ROOT/'skills'/name/'SKILL.md'
        text = skill.read_text()
        require(text.startswith('---\n'), f'{name}: missing frontmatter')
        front = text.split('---', 2)[1] if text.startswith('---\n') else ''
        require(f'\nname: {name}\n' in '\n'+front, f'{name}: mismatched name')
        require(bool(re.search(r'^description: \S.+$', front, re.M)), f'{name}: missing single-line description')
        require((skill.parent/'LICENSE').is_file(), f'{name}: missing portable license')
        record = provenance.get(name, {})
        require(bool(record.get('credit')) and bool(record.get('source')), f'{name}: incomplete attribution')
        require(record.get('relationship') in {'adapted','original','reference-adapter'}, f'{name}: unknown provenance relationship')
        if (skill.parent/'LICENSE').exists():
            require(record.get('copyright', '') in (skill.parent/'LICENSE').read_text(), f'{name}: source copyright missing')
    snapshots = runpy.run_path(str(ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py'))['check'](ROOT)
    docs = list(ROOT.glob('*.md')) + list((ROOT/'docs').rglob('*.md')) + list((ROOT/'skills').rglob('*.md')) + list((ROOT/'tools').rglob('*.md'))
    for path in docs:
        if path in snapshots:
            continue  # Immutable upstream text is checked byte-for-byte, not rewritten to local style.
        body = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body):
            target = target.split('#', 1)[0].strip('<>')
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            resolved = (path.parent/target).resolve()
            require(resolved.is_relative_to(ROOT) and resolved.exists(), f'Broken/escaping link: {path.relative_to(ROOT)} -> {target}')
        require('/'+'Users/' not in body and '/'+'home/' not in body, f'Local home path in public document: {path.relative_to(ROOT)}')
    for script in ['sync-agent-skills.py','sync-agent-models.py']:
        result = subprocess.run([sys.executable, str(ROOT/'scripts'/script), '--check'], capture_output=True, text=True)
        require(result.returncode == 0, result.stderr.strip() or f'{script} failed')
    result = subprocess.run([sys.executable, str(ROOT/'scripts/sync-public-skills.py'), 'manifest', '--root', str(ROOT)], capture_output=True, text=True)
    require(result.returncode == 0, result.stderr.strip() or 'Manifest failed')
    spec = importlib.util.spec_from_file_location('installer', ROOT/'scripts/install.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    try:
        installer.selection()  # Validate every preset against the catalog.
    except (ValueError, KeyError, TypeError) as error:
        errors.append(f'Invalid presets: {error}')
    result = subprocess.run([sys.executable, str(ROOT/'skills/orbyn-skill-creator/scripts/evaluate.py'), 'validate'], capture_output=True, text=True)
    require(result.returncode == 0, result.stderr.strip() or 'Evaluation suite failed')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'OK: {len(names)} skills, provenance/licenses, {len(docs)} Markdown documents, links, host assets, presets, evaluation cases and manifest.')
    print('Static expectations only; no live model, product, native or security qualification.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
