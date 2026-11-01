#!/usr/bin/env python3
"""Validate library structure and attribution; no network or model calls."""
import importlib.util
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys

from skill_contracts import check_audit, check_case_coverage, check_discovery, check_entrypoint, check_incorporated_material, check_links, check_local_workspaces, check_portable_links

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 11):
        print('Python 3.11+ is required for library validation.', file=sys.stderr)
        return 1
    errors = []
    errors.extend(check_local_workspaces(ROOT))
    if (ROOT/'project-skills').exists() or (ROOT/'project-skills').is_symlink():
        errors.append('Consumer-owned project-skills must stay in the consuming repository, outside the public library')
    def require(ok, message):
        if not ok:
            errors.append(message)
    catalog = json.loads((ROOT/'skills/catalog.json').read_text())
    provenance = json.loads((ROOT/'provenance.json').read_text())['skills']
    names = {entry['name'] for entry in catalog['skills']}
    require(names == set(provenance), 'Catalog/provenance coverage differs')
    errors.extend(check_discovery(ROOT, names, catalog['skills']))
    errors.extend(check_audit(ROOT, names))
    errors.extend(check_case_coverage(names, json.loads((ROOT/'skills/orbyn-skill-creator/evals/cases.json').read_text())['cases']))
    for name in sorted(names):
        skill = ROOT/'skills'/name/'SKILL.md'
        text = skill.read_text()
        require(text.startswith('---\n'), f'{name}: missing frontmatter')
        front = text.split('---', 2)[1] if text.startswith('---\n') else ''
        require(f'\nname: {name}\n' in '\n'+front, f'{name}: mismatched name')
        require(bool(re.search(r'^description: \S.+$', front, re.M)), f'{name}: missing single-line description')
        errors.extend(check_entrypoint(name, text))
        require((skill.parent/'LICENSE').is_file(), f'{name}: missing portable license')
        record = provenance.get(name, {})
        errors.extend(check_incorporated_material(ROOT, name, record))
        require(bool(record.get('credit')) and bool(record.get('source')), f'{name}: incomplete attribution')
        require(record.get('relationship') in {'adapted','original','reference-adapter'}, f'{name}: unknown provenance relationship')
        if (skill.parent/'LICENSE').exists():
            require(record.get('copyright', '') in (skill.parent/'LICENSE').read_text(), f'{name}: source copyright missing')
    snapshots = runpy.run_path(str(ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py'))['check'](ROOT)
    distributed = runpy.run_path(str(ROOT/'scripts/library_manifest.py'))['inventory'](ROOT)
    errors.extend(check_portable_links(ROOT, distributed, snapshots))
    docs = list(ROOT.glob('*.md')) + list((ROOT/'docs').rglob('*.md')) + list((ROOT/'skills').rglob('*.md')) + list((ROOT/'tools').rglob('*.md'))
    for path in docs:
        if path in snapshots:
            continue  # Immutable upstream text is checked byte-for-byte, not rewritten to local style.
        body = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        errors.extend(check_links(ROOT, path, snapshots))
        require('/'+'Users/' not in body and '/'+'home/' not in body, f'Local home path in public document: {path.relative_to(ROOT)}')
    for script in ['sync-agent-skills.py','sync-agent-models.py']:
        result = subprocess.run([sys.executable, str(ROOT/'scripts'/script), '--check'], capture_output=True, text=True)
        require(result.returncode == 0, result.stderr.strip() or f'{script} failed')
    result = subprocess.run([sys.executable, str(ROOT/'scripts/library_manifest.py'), '--root', str(ROOT)], capture_output=True, text=True)
    require(result.returncode == 0, result.stderr.strip() or 'Manifest failed')
    spec = importlib.util.spec_from_file_location('reading_groups', ROOT/'scripts/skill_selection.py')
    groups = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(groups)
    try:
        groups.selection()  # Validate every preset against the catalog.
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
