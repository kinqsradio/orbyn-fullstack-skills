"""Owned portable exports, consistent snapshots and explicit local lesson drafts."""
import hashlib
import html
from pathlib import Path
import sqlite3
import subprocess
import difflib
import re
import uuid

from .schema import (EDITABLE, Error, VERSION, canonical, decode, identifier, make,
                     now, require, timestamp, validate)
from .store import connection, private_file, safe_path


def read_json(path, maximum=1048576):
    path = safe_path(path)
    require(path.is_file() and path.stat().st_size <= maximum, 'Input missing or exceeds size limit')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'Input exceeds size limit')
    try:
        return decode(raw.decode('utf-8'))
    except UnicodeError as exc:
        raise Error('Input is not UTF-8') from exc


def reserve(memory, kind, revisions, suffix):
    aid = 'artifact_' + uuid.uuid4().hex
    relative = f'artifacts/{memory.sid}/{aid}.{suffix}'
    with memory.transaction():
        for rid, rev in revisions.items():
            require(type(rev) is int and memory._get(rid)['revision'] == rev, 'Artifact source revision changed')
        memory.conn.execute('INSERT INTO data.artifacts VALUES (?,?,?,?,?)',
                            (aid, kind, relative, 'pending', canonical(revisions)))
    return aid, safe_path(memory.root / relative)


def materialize(memory, aid, path, producer):
    # A durable reservation precedes file creation: interrupted artifacts are known
    # to cleanup. Serialize validation, creation and completion against forgetting.
    with memory.transaction():
        row = memory.conn.execute('SELECT * FROM data.artifacts WHERE id=?', (aid,)).fetchone()
        require(row and row['state'] == 'pending', 'Artifact reservation is no longer available')
        for rid, rev in decode(row['refs']).items():
            require(memory._get(rid)['revision'] == rev, 'Artifact source revision changed')
        safe_path(path.parent).mkdir(parents=True, exist_ok=True, mode=0o700)
        private_file(path)
        producer(path)
        memory.conn.execute("UPDATE data.artifacts SET state='ready' WHERE id=?", (aid,))
    return {'artifact_id': aid, 'path': str(path), 'state': 'ready'}


def html_report(records):
    esc = lambda value: html.escape(str(value), quote=True)
    categories = sorted({r['category'] for r in records})
    domains = sorted({d for r in records for d in r['domains']})
    labels = sorted({t for r in records for t in r['tags']})
    def options(values):
        return ''.join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in values)
    cards = []
    for r in records:
        cards.append(f'''<article data-category="{esc(r['category'])}"
          data-domain="{esc(' '.join(r['domains']))}" data-tag="{esc(' '.join(r['tags']))}">
          <h2>{esc(r['title'])}</h2><p class="body">{esc(r['statement'])}</p>
          <p>{esc(r['category'])} · {esc(', '.join(r['domains']))}</p>
          <p class="tags">{esc(' · '.join(r['tags']))}</p>
          <p class="meta">{esc(r['id'])} · revision {r['revision']} · {esc(r['status'])}
          · {esc(r['evidence_level'])} · {esc(r['sensitivity'])}</p>
          <details><summary>Evidence and applicability</summary><pre>{esc(canonical({'evidence': r['evidence'], 'applicability': r['applicability']}))}</pre></details>
          </article>''')
    scope = records[0]['scope'] if records else {'kind': 'empty', 'owner_id': ''}
    return '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Engineering memory review</title><style>
body{font:16px/1.5 system-ui,sans-serif;margin:0;background:#f5f3ee;color:#1d2b31}
main{max-width:960px;margin:auto;padding:32px 20px}h1{font-size:2rem;margin-bottom:8px}
.notice{border-left:4px solid #486c65;padding-left:16px}section{display:flex;gap:14px;flex-wrap:wrap}
label{display:grid;gap:5px;flex:1;min-width:180px}input,select{font:inherit;padding:10px;border:1px solid #8c9894;border-radius:5px;min-width:0}
article{background:white;border:1px solid #ccd3cd;border-radius:8px;padding:20px;margin:18px 0}
h2{font-size:1.2rem;margin-top:0}.body{white-space:pre-wrap}.meta{font-size:.85rem;overflow-wrap:anywhere}
.tags{color:#30574f}pre{white-space:pre-wrap;overflow-wrap:anywhere}article p{overflow-wrap:anywhere}
:focus-visible{outline:3px solid #185c98;outline-offset:3px}[hidden]{display:none!important}
</style><main><h1>Engineering memory</h1><p class="meta">Scope: ''' + esc(scope['kind']) + ' · ' + esc(scope['owner_id']) + '''</p>
<p class="notice">Private, read-only snapshot. Changes and forgetting use the local memory helper.
This export can become stale; verify the live record before applying it. Do not publish this file.</p>
<section aria-label="Filter memories"><label>Search<input id="search" type="search"></label>
<label>Category<select id="category"><option value="">All categories</option>''' + options(categories) + '''</select></label>
<label>Domain<select id="domain"><option value="">All domains</option>''' + options(domains) + '''</select></label>
<label>Tag<select id="tag"><option value="">All tags</option>''' + options(labels) + '''</select></label></section>
<p id="count" role="status" aria-live="polite"></p><div id="records">''' + ''.join(cards) + '''</div></main>
<script>const fields=['search','category','domain','tag'].map(x=>document.getElementById(x));
function filter(){let count=0;for(const card of document.querySelectorAll('article')){
const [q,c,d,t]=fields.map(x=>x.value.toLowerCase());
const shown=card.textContent.toLowerCase().includes(q)&&(!c||card.dataset.category===c)&&
(!d||card.dataset.domain.split(' ').includes(d))&&(!t||card.dataset.tag.split(' ').includes(t));
card.hidden=!shown;if(shown)count++;}document.getElementById('count').textContent=count+' memories shown';}
fields.forEach(x=>x.addEventListener('input',filter));filter();</script></html>'''


def export(memory, revisions, format='json'):
    require(format in ('json', 'markdown', 'html'), 'Unsupported export format')
    require(isinstance(revisions, dict) and 0 < len(revisions) <= 100, 'Select 1-100 records')
    suffix = {'json': 'json', 'markdown': 'md', 'html': 'html'}[format]
    aid, path = reserve(memory, 'export', revisions, suffix)
    def produce(destination):
        records = [memory._get(rid) for rid in revisions]
        if format == 'json':
            value = canonical({'schema_version': VERSION, 'store_id': memory.sid, 'records': records})
        elif format == 'markdown':
            # Inert fenced JSON, not executable Markdown sourced from the record.
            value = '# Private memory snapshot\n\nRead-only export; use IDs/revisions to edit the live store.\n\n'
            for record in records:
                body = canonical(record)
                fence = '`' * max(3, max((len(part) for part in re.findall(r'`+', body)), default=0) + 1)
                value += f'{fence}json\n{body}\n{fence}\n\n'
        else:
            value = html_report(records)
        destination.write_text(value + '\n', encoding='utf-8')
    return materialize(memory, aid, path, produce)


def import_records(memory, bundle, operation):
    require(isinstance(bundle, dict) and set(bundle) == {'schema_version', 'store_id', 'records'}, 'Invalid import envelope')
    require(type(bundle['schema_version']) is int and bundle['schema_version'] == VERSION, 'Unsupported import version')
    require(bundle['store_id'] == memory.sid, 'Cross-scope import refused; prepare an independently reviewed new record')
    records = bundle['records']
    require(isinstance(records, list) and 0 < len(records) <= 100, 'Import must contain 1-100 records')
    def action():
        require(all(isinstance(r, dict) for r in records), 'Import records must be objects')
        require(memory.conn.execute('SELECT count(*) FROM data.records').fetchone()[0] + len(records) <= 10000,
                'Local store limit is 10,000 records')
        validated = [validate(dict(r), memory.skills, memory.aliases()) for r in records]
        require(len({r['id'] for r in validated}) == len(validated), 'Duplicate import IDs')
        ids = {r['id'] for r in validated}
        for record in validated:
            rid = record['id']
            require(record['scope'] == {'kind': memory.kind, 'owner_id': memory.sid}, 'Mismatched imported scope')
            require(not memory.conn.execute('SELECT 1 FROM deleted WHERE store_id=? AND record_id=?',
                                            (memory.sid, rid)).fetchone(), 'Import contains forgotten ID')
            require(not memory.conn.execute('SELECT 1 FROM data.records WHERE id=?', (rid,)).fetchone(),
                    'Import cannot overwrite an existing ID; use revision-checked update')
            require(not memory.conn.execute('SELECT 1 FROM versions WHERE store_id=? AND record_id=?',
                                            (memory.sid, rid)).fetchone(), 'Previously known ID requires checked restore')
            for relation in record['relations']:
                if relation['id'] not in ids:
                    memory._get(relation['id'])
        for record in validated:
            record.update(status='proposed', revision=record['revision'] + 1, updated_at=now())
            validate(record, memory.skills, memory.aliases())
        for record in validated:
            memory.conn.execute('INSERT INTO data.records VALUES (?,?,?)',
                                (record['id'], record['revision'], canonical(record)))
            memory.conn.execute('INSERT INTO versions VALUES (?,?,?)', (memory.sid, record['id'], record['revision']))
        return {'state': 'imported-proposed', 'records': {r['id']: r['revision'] for r in validated}}
    return memory.mutate(operation, {'action': 'import', 'bundle': bundle}, action)


def backup(memory):
    with memory.transaction():
        revisions = {r['id']: r['revision'] for r in memory.conn.execute('SELECT id,revision FROM data.records')}
    aid, path = reserve(memory, 'backup', revisions, 'sqlite3')
    def produce(destination):
        require({r['id']: r['revision'] for r in memory.conn.execute('SELECT id,revision FROM data.records')} == revisions,
                'Backup selection changed; retry')
        source = connection(memory.root / 'stores' / memory.sid / 'memory.sqlite3')
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
        finally:
            source.close()
            target.close()
    return materialize(memory, aid, path, produce)


def restore(memory, artifact_id, generation, operation):
    identifier(artifact_id)
    def action():
        current = int(memory.conn.execute("SELECT value FROM data.meta WHERE key='generation'").fetchone()[0])
        require(type(generation) is int and current == generation, 'Store changed; reread generation before restore')
        row = memory.conn.execute('SELECT * FROM data.artifacts WHERE id=?', (artifact_id,)).fetchone()
        require(row and row['kind'] == 'backup' and row['state'] == 'ready', 'Backup unavailable or pending deletion')
        path = safe_path(memory.root / row['path'])
        require(path.is_relative_to(memory.root / 'artifacts'), 'Invalid backup path')
        conn = connection(path)
        try:
            conn.execute('PRAGMA trusted_schema=OFF')
            require(conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Backup is corrupt')
            meta = dict(conn.execute('SELECT key,value FROM meta'))
            require(meta.get('version') == str(VERSION) and meta.get('store_id') == memory.sid, 'Wrong backup scope/version')
            rows = conn.execute('SELECT body FROM records').fetchall()
            require(len(rows) <= 10000, 'Backup exceeds restore limit')
            records = [validate(decode(row[0]), memory.skills, memory.aliases()) for row in rows]
        finally:
            conn.close()
        restored, suppressed = {}, []
        for record in records:
            rid = record['id']
            require(record['scope'] == {'kind': memory.kind, 'owner_id': memory.sid}, 'Wrong backup record scope')
            if memory.conn.execute('SELECT 1 FROM deleted WHERE store_id=? AND record_id=?', (memory.sid, rid)).fetchone():
                suppressed.append(rid)
                continue
            if memory.conn.execute('SELECT 1 FROM data.records WHERE id=?', (rid,)).fetchone():
                continue  # Existing live state always wins over an old snapshot.
            highwater = memory.conn.execute('SELECT revision FROM versions WHERE store_id=? AND record_id=?',
                                             (memory.sid, rid)).fetchone()
            next_revision = max(record['revision'], highwater[0] if highwater else 0) + 1
            record.update(status='proposed', revision=next_revision, updated_at=now(), relations=[])
            memory._save(record)
            restored[rid] = record['revision']
        return {'state': 'restored-proposed', 'records': restored, 'suppressed_ids': suppressed}
    return memory.mutate(operation, {'action': 'restore', 'artifact': artifact_id, 'generation': generation}, action)


def propose(memory, brief, revisions, operation):
    fields = {'title', 'skill', 'base_revision', 'problem', 'proposed_change', 'synthetic_case',
              'counterexample', 'validation_plan', 'delivery'}
    require(isinstance(brief, dict) and set(brief) == fields, 'Invalid lesson brief')
    require(isinstance(brief['skill'], str) and brief['skill'] in memory.skills, 'Unknown skill owner')
    require(brief['delivery'] in ('manual', 'local-branch', 'fork-branch'), 'Unsupported delivery mode')
    require(isinstance(brief['base_revision'], str) and re.fullmatch('[0-9a-f]{40}', brief['base_revision']), 'Use full library base SHA')
    from .schema import text
    for key in fields - {'delivery', 'base_revision', 'skill'}:
        text(brief[key], key, 8000)
    require(isinstance(revisions, dict) and 0 < len(revisions) <= 12, 'Select 1-12 source revisions')
    def action():
        for rid, rev in revisions.items():
            record = memory._get(rid)
            require(type(rev) is int and record['revision'] == rev and record['status'] == 'active', 'Candidate source is not current/active')
            require(record['expires_at'] is None or timestamp(record['expires_at']) > timestamp(now()), 'Candidate source expired')
        cid = 'candidate_' + uuid.uuid4().hex
        body = dict(brief, sources=revisions, created_at=now())
        memory.conn.execute('INSERT INTO data.candidates VALUES (?,?,?)', (cid, canonical(body), 'draft'))
        return {'state': 'draft', 'candidate_id': cid, 'records': revisions}
    return memory.mutate(operation, {'action': 'propose', 'brief': brief, 'sources': revisions}, action)


def candidate(memory, cid):
    with memory.transaction():
        identifier(cid)
        row = memory.conn.execute('SELECT * FROM data.candidates WHERE id=?', (cid,)).fetchone()
        require(row is not None, 'Candidate not found')
        return {'id': cid, 'state': row['state'], **decode(row['body'])}


def check_sources(memory, rid, revision, project, operation):
    require(project is not None and memory.kind == 'project', 'Source checking requires the registered project')
    project = safe_path(project)
    def action():
        record = memory._get(rid)
        require(type(revision) is int and record['revision'] == revision, 'Revision conflict; reread record')
        checks = []
        for evidence in record['evidence']:
            if evidence['kind'] != 'source':
                continue
            ref = Path(evidence['ref'])
            require(not ref.is_absolute() and '..' not in ref.parts and '\\' not in str(ref), 'Unsafe source reference')
            path = safe_path(project / ref)
            require(path.is_relative_to(project), 'Source escapes project')
            expected = evidence['revision']
            require(re.fullmatch(r'sha256:[0-9a-f]{64}', expected), 'Source checker requires sha256 evidence revisions')
            if not path.is_file():
                matched = False
            else:
                require(path.stat().st_size <= 1048576, 'Source file exceeds 1 MiB check limit')
                matched = 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest() == expected
            checks.append({'matched': matched})
        if checks and not all(c['matched'] for c in checks):
            record.update(status='stale', revision=revision + 1, updated_at=now())
            memory._save(record)
        return {'records': {rid: record['revision']}, 'state': 'sources-checked' if checks else 'no-checkable-sources',
                'checks': checks}
    return memory.mutate(operation, {'action': 'check-sources', 'id': rid, 'revision': revision}, action)


def prepare_patch(memory, cid, checkout, files, reviewed):
    require(reviewed, 'Review exact outgoing content and destination within user scope before preparing delivery')
    record = candidate(memory, cid)
    require(record['state'] == 'draft', 'Candidate is invalidated or unavailable')
    checkout = safe_path(checkout)
    def git(*args):
        result = subprocess.run(['git', '-C', str(checkout), *args], capture_output=True, timeout=20)
        require(result.returncode == 0, 'Cannot read selected Git candidate')
        return result.stdout
    require(git('rev-parse', 'HEAD').decode().strip() == record['base_revision'], 'Candidate HEAD differs from frozen base')
    require(git('rev-parse', '--show-toplevel').decode().strip() == str(checkout), 'Select the candidate Git root')
    require(isinstance(files, list) and 0 < len(files) <= 50 and len(set(files)) == len(files), 'Select 1-50 unique paths')
    special = {'skills/catalog.json', 'skills/README.md', 'distribution/manifest.json', 'docs/skill-audit.md',
               'skills/orbyn-skill-creator/evals/cases.json'}
    patches = []
    for name in files:
        # Unified diff headers interpret tabs/newlines as syntax. Reject ambiguous
        # filenames rather than allowing an allowlisted name to inject other paths.
        require(isinstance(name, str) and bool(re.fullmatch(r'[A-Za-z0-9_./-]+', name)),
                'Contribution paths must use unambiguous portable characters')
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in name and
                not any(part.startswith('.') for part in path.parts), 'Unsafe contribution path')
        require(name in special or name.startswith(f"skills/{record['skill']}/"), 'Path outside selected skill allowlist')
        destination = safe_path(checkout / path)
        require(destination.is_relative_to(checkout) and destination.is_file(), 'Selected contribution must be a regular file')
        require(destination.stat().st_size <= 1048576, 'Contribution file exceeds 1 MiB')
        entry = git('ls-tree', record['base_revision'], '--', name).decode()
        require(not entry or entry.startswith('100644 blob '), 'Patch helper supports ordinary non-executable text files only')
        require(not destination.stat().st_mode & 0o111, 'Patch helper does not change executable modes')
        result = subprocess.run(['git', '-C', str(checkout), 'show', record['base_revision'] + ':' + name],
                                capture_output=True, timeout=20)
        require(result.returncode in (0, 128), 'Cannot read base file')
        before = result.stdout.decode('utf-8') if result.returncode == 0 else ''
        after = destination.read_text(encoding='utf-8')
        require('\x00' not in before + after, 'Binary patches are unsupported')
        require((not before or before.endswith('\n')) and (not after or after.endswith('\n')),
                'Normalize final newlines before preparing the patch')
        if before == after:
            continue
        patches.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                           fromfile='a/' + name if result.returncode == 0 else '/dev/null', tofile='b/' + name))
    patch = ''.join(patches)
    require(bool(patch) and len(patch.encode()) <= 2097152, 'Patch is empty or exceeds 2 MiB')
    aid, path = reserve(memory, 'candidate', record['sources'], 'patch')
    def produce(destination):
        current = memory.conn.execute('SELECT state FROM data.candidates WHERE id=?', (cid,)).fetchone()
        require(current and current[0] == 'draft', 'Candidate changed during preparation')
        for rid in record['sources']:
            source = memory._get(rid)
            require(source['status'] == 'active' and (source['expires_at'] is None or
                    timestamp(source['expires_at']) > timestamp(now())), 'Candidate source expired or inactive')
        destination.write_text(patch, encoding='utf-8')
    result = materialize(memory, aid, path, produce)
    result.update(base_revision=record['base_revision'], patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
                  delivery=record['delivery'], branch=f"fix/learning-{record['skill']}",
                  validation='prepared-not-evaluated', committed=False, pushed=False,
                  next_action='Inspect/apply the exact patch in an owned candidate, run library checks and failure/adjacent cases. '
                              'Use existing worktree/contribution policy for any authorized fork commit or push.')
    return result
