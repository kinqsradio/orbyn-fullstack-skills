#!/usr/bin/env python3
"""Static discovery, links and local Git boundaries; no project-source execution."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

# Limits from skills/orbyn-skill-creator/references/authoring-standard.md.
MAX_ENTRYPOINT_WORDS = 1200
MAX_DESCRIPTION_CHARS = 300
MIN_POSITIVE_CASES = 2
AUTHORING_RULE_DATE = '2026-11-02'
# Licences we may modify and redistribute with credit as the only obligation. Copyleft
# asks for more than credit, so such sources are cited and never copied.
ALLOWED_LICENCES = {'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'Zlib', 'CC-BY-4.0', 'CC0-1.0', 'Unlicense'}
MAINTAINER_BOILERPLATE = ('historical source notices remain in provenance',)


def check_local_workspaces(root):
    """Inspect only the library's index/ignore rules, never nested project data."""
    errors = []
    top = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'],
                         capture_output=True, text=True)
    if top.returncode or Path(top.stdout.strip()).resolve() != root.resolve():
        return ['Workspace boundary check requires the actual library Git root']
    tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z', '--',
                                       'repo', 'openSrc', 'orbyn-references'], text=True)
    if tracked:
        errors.append('Local workspaces/reference data must not be tracked: '
                      + ', '.join(p for p in tracked.split('\0') if p))
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '--no-index',
                              '--quiet', '--', 'repo/__orbyn_workspace_probe__/file'],
                             capture_output=True)
    if ignored.returncode:
        errors.append('Library repo/ contribution workspace must be Git-ignored')
    if (root/'repo').is_symlink():
        errors.append('Default library repo/ workspace must not be a symlink')
    return errors


def headings(text):
    """GitHub-style slugs for ordinary authored ATX headings, including duplicates."""
    result = set()
    counts = {}
    body = re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)
    for title in re.findall(r'^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$', body, re.M):
        title = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', title)
        title = re.sub(r'<[^>]+>', '', title).lower()
        slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if count == 0 else f'{slug}-{count}')
    return result


def check_discovery(root, names, catalog):
    expected = {root/'skills'/name/'SKILL.md' for name in names}
    actual = set((root/'skills').rglob('SKILL.md'))
    errors = [f'Unexpected active skill entrypoint: {p.relative_to(root)}; reference data must use SOURCE.md'
              for p in sorted(actual - expected)]
    errors += [f'Missing active skill entrypoint: {p.relative_to(root)}' for p in sorted(expected - actual)]
    for entry in catalog:
        for related in entry.get('related', []):
            if related not in names:
                errors.append(f"{entry['name']}: unknown related skill {related}")
    return errors


def local_link_targets(text):
    """Read authored inline links and reference definitions outside fenced code."""
    body = re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)
    targets = re.findall(r'\[[^\]]*\]\(([^)]+)\)', body)
    targets += re.findall(r'^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)', body, re.M)
    for raw in targets:
        # An optional Markdown title is not part of the destination.
        match = re.fullmatch(r'(<[^>]+>|\S+?)(?:\s+["\'].*["\'])?', raw.strip())
        target = (match.group(1) if match else raw).strip('<>')
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            yield target


def check_links(root, path, snapshots=()):
    errors = []
    # Pinned source text has its own integrity checks and is never active routing.
    if path in snapshots:
        return errors
    for target in local_link_targets(path.read_text()):
        filename, _, fragment = target.partition('#')
        resolved = (path.parent/unquote(filename)).resolve() if filename else path.resolve()
        if not resolved.is_relative_to(root) or not resolved.exists():
            errors.append(f'Broken/escaping link: {path.relative_to(root)} -> {target}')
        elif fragment and resolved.suffix == '.md':
            # Explicit HTML anchors are supported alongside ordinary heading slugs.
            text = resolved.read_text()
            anchors = headings(text) | set(re.findall(r'<(?:a|[a-z]+)\s+[^>]*(?:id|name)=["\']([^"\']+)', text))
            if unquote(fragment) not in anchors:
                errors.append(f'Broken Markdown fragment: {path.relative_to(root)} -> {target}')
    return errors


def check_audit(root, names):
    """Prevent an old partial audit from silently masquerading as full coverage."""
    path = root/'docs/skill-audit.md'
    if not path.is_file():
        return ['Missing full-catalog audit']
    rows = re.findall(r'^\|\s+\[([a-z0-9-]+)\]\(\.\./skills/\1/SKILL\.md\)\s+\|', path.read_text(), re.M)
    if len(rows) != len(set(rows)) or set(rows) != names:
        return ['Full-catalog audit coverage differs from the catalog']
    return []


def check_entrypoint(name, text):
    """Hold the authoring standard's limits so entrypoints cannot silently regrow."""
    fenced = re.fullmatch(r'---\n(.*?\n)---\n(.*)', text, re.S)
    if not fenced:
        return [f'{name}: SKILL.md needs closed frontmatter fences']
    front, body = fenced.groups()
    errors = []
    description = re.search(r'^description:[ \t]*(.*)\n(?=([ \t]+\S)?)', front, re.M)
    if description:
        value = description.group(1).strip('"\' ')
        if not value or value[0] in '>|' or description.group(2):
            errors.append(f'{name}: description must be one literal line')
        elif len(value) > MAX_DESCRIPTION_CHARS:
            errors.append(f'{name}: description exceeds {MAX_DESCRIPTION_CHARS} characters')
    if len(body.split()) > MAX_ENTRYPOINT_WORDS:
        errors.append(f'{name}: SKILL.md exceeds {MAX_ENTRYPOINT_WORDS} words; move conditional detail to a reference')
    prose = re.sub(r'\s+', ' ', body).lower()
    errors += [f'{name}: maintainer note in SKILL.md belongs in provenance: {phrase}'
               for phrase in MAINTAINER_BOILERPLATE if phrase in prose]
    return errors


def check_licences(root, name, record):
    """Anything bundled or adapted must carry an allowed licence; others are cited, not copied."""
    errors = []
    if record.get('license') not in ALLOWED_LICENCES:
        errors.append(f"{name}: only licences that require nothing beyond credit may be bundled, found {record.get('license')}")
    for item in record.get('incorporated_material') or []:
        if item.get('license') not in ALLOWED_LICENCES:
            errors.append(f"{name}: incorporated material needs a licence that requires nothing beyond credit: {item.get('source')}")
    for path in sorted((root/'skills'/name).glob('references/upstream/*/snapshot.json')):
        license_name = json.loads(path.read_text()).get('license')
        if license_name not in ALLOWED_LICENCES:
            errors.append(f'{name}: bundled source needs a licence that requires nothing beyond credit, found {license_name}: {path.parent.name}')
    return errors


def check_authoring(name, record):
    """Each skill says which tools and models built it; history before this rule is unrecorded."""
    entries = record.get('authoring')
    if not isinstance(entries, list) or not entries:
        return [f'{name}: provenance needs an authoring list naming the tools and models used']
    errors = []
    for entry in entries:
        if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) and entry[k] for k in ('tool', 'model', 'date')):
            errors.append(f'{name}: authoring entries need tool, model and date')
        elif not re.fullmatch(r'\d{4}-\d{2}-\d{2}', entry['date']):
            errors.append(f'{name}: authoring date must be YYYY-MM-DD')
        elif entry['tool'] == 'unrecorded' and entry['date'] > AUTHORING_RULE_DATE:
            errors.append(f'{name}: work after {AUTHORING_RULE_DATE} must name its tool and model')
    return errors


def check_case_coverage(names, cases):
    """Every skill needs repeat development cases and a holdout it alone must pass."""
    positive = {name: 0 for name in names}
    holdout = set()
    for case in cases:
        if case['split'] == 'holdout':
            # A shared holdout passes when any expected skill is selected.
            holdout.update(case['expected_skills'] if len(case['expected_skills']) == 1 else ())
            continue
        for name in set(case['expected_skills']):
            positive[name] = positive.get(name, 0) + 1
    errors = [f'{name}: needs at least {MIN_POSITIVE_CASES} positive development cases'
              for name in sorted(names) if positive[name] < MIN_POSITIVE_CASES]
    errors += [f'{name}: needs a holdout case expecting only this skill' for name in sorted(names - holdout)]
    return errors


def check_portable_links(root, managed_files, snapshots=()):
    """Every authored Markdown dependency must survive the skills-only copy.

    Consumer instructions are discovered in place, not linked as bundled policy.
    Only byte-validated upstream snapshots may opt out of active link checks.
    """
    root = root.resolve()
    managed = {(root/name).resolve() for name in managed_files}
    errors = []
    for path in sorted(managed):
        if path.suffix != '.md' or path in snapshots:
            continue
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f'Missing/escaping distributed document: {path}')
            continue
        errors.extend(check_links(root, path))
        for target in local_link_targets(path.read_text()):
            filename = unquote(target.partition('#')[0])
            resolved = (path.parent/filename).resolve() if filename else path
            # Directory links are portable only when the export contains children.
            included = resolved in managed or (
                resolved.is_dir() and any(p.is_relative_to(resolved) for p in managed))
            if not resolved.is_relative_to(root) or not included:
                errors.append(f'Unexported dependency: {path.relative_to(root)} -> {target}')
    return errors


def check_incorporated_material(root, name, record):
    """Moved derived references keep portable source and license evidence."""
    errors = []
    owner = (root/'skills'/name).resolve()
    for item in record.get('incorporated_material', []):
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key]
                for key in ['source','revision','copyright','license','local_path','license_file','license_sha256']):
            errors.append(f'{name}: incomplete incorporated-material provenance')
            continue
        source = (root/item['local_path']).resolve()
        notice = (root/item['license_file']).resolve()
        if (not source.is_relative_to(owner) or not notice.is_relative_to(owner)
                or not source.is_file() or not notice.is_file()):
            errors.append(f'{name}: missing/escaping incorporated reference or license')
        elif item['copyright'] not in notice.read_text():
            errors.append(f'{name}: incorporated source copyright missing')
        elif hashlib.sha256(notice.read_bytes()).hexdigest() != item['license_sha256']:
            errors.append(f'{name}: incorporated license differs from pinned notice')
    return errors
