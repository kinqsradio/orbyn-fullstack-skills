"""Private, transactional stores with explicit project bindings and deletion ledger."""
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import uuid
from urllib.parse import quote

from .schema import (ALIASES, EDITABLE, Error, VERSION, canonical, decode, identifier,
                     make, now, operation_identifier, require, tags, timestamp, validate)

SCHEMA = '''
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE records (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);
CREATE TABLE aliases (name TEXT PRIMARY KEY, target TEXT NOT NULL);
CREATE TABLE operations (id TEXT PRIMARY KEY, fingerprint TEXT, result TEXT NOT NULL);
CREATE TABLE operation_records (operation_id TEXT, record_id TEXT,
  PRIMARY KEY(operation_id, record_id));
CREATE TABLE artifacts (id TEXT PRIMARY KEY, kind TEXT NOT NULL, path TEXT NOT NULL,
  state TEXT NOT NULL, refs TEXT NOT NULL);
CREATE TABLE candidates (id TEXT PRIMARY KEY, body TEXT NOT NULL, state TEXT NOT NULL);
'''


def safe_path(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'Symlink paths are not supported')
    return path


def private_file(path):
    path = safe_path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)


def connection(path):
    path = safe_path(path)
    require(path.is_file() and path.stat().st_nlink == 1, 'Missing or linked database')
    conn = sqlite3.connect('file:' + quote(str(path)) + '?mode=rw', uri=True, timeout=5,
                           isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA trusted_schema=OFF')
    conn.execute('PRAGMA secure_delete=ON')
    conn.execute('PRAGMA synchronous=FULL')
    return conn


def root_path(root):
    root = safe_path(root)
    for parent in (root, *root.parents):
        require(not (parent / '.git').exists(), 'Memory root must be outside Git checkouts')
    require(not any(name in {'.codex', '.claude'} for name in root.parts),
            'Choose an independent data root, not host-owned memory/configuration')
    return root


def init(root, mode='off'):
    root = root_path(root)
    require(mode in ('off', 'manual'), 'Supported modes: off, manual')
    require(not root.exists() or (root.is_dir() and not any(root.iterdir())),
            'Initialization requires a new or empty directory')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    path = root / 'registry.sqlite3'
    private_file(path)
    conn = connection(path)
    try:
        conn.executescript('''
        BEGIN IMMEDIATE;
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE stores (id TEXT PRIMARY KEY, kind TEXT NOT NULL, identity TEXT NOT NULL,
          UNIQUE(kind, identity));
        CREATE TABLE deleted (store_id TEXT NOT NULL, record_id TEXT NOT NULL,
          revision INTEGER NOT NULL, PRIMARY KEY(store_id, record_id));
        CREATE TABLE versions (store_id TEXT NOT NULL, record_id TEXT NOT NULL,
          revision INTEGER NOT NULL, PRIMARY KEY(store_id, record_id));
        ''')
        conn.executemany('INSERT INTO settings VALUES (?,?)',
                         [('version', str(VERSION)), ('mode', mode), ('secret', secrets.token_hex(32))])
        conn.commit()
    finally:
        conn.close()
    return {'root': str(root), 'mode': mode, 'schema_version': VERSION}


def control(root):
    conn = connection(root_path(root) / 'registry.sqlite3')
    try:
        require(conn.execute("SELECT value FROM settings WHERE key='version'").fetchone()[0]
                == str(VERSION), 'Unsupported registry schema')
        return conn
    except BaseException:
        conn.close()
        raise


def set_mode(root, mode):
    require(mode in ('off', 'manual'), 'Supported modes: off, manual')
    conn = control(root)
    try:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute("UPDATE settings SET value=? WHERE key='mode'", (mode,))
        conn.commit()
    finally:
        conn.close()
    return {'mode': mode, 'records_deleted': False}


def identity(project=None, personal=False, reusable=False):
    require(sum([project is not None, bool(personal), bool(reusable)]) == 1,
            'Select exactly one project, personal or reusable scope')
    if personal or reusable:
        return ('personal' if personal else 'reusable'), 'local-user'
    path = safe_path(project)
    require(path.is_dir(), 'Project directory does not exist')
    result = subprocess.run(['git', '-C', str(path), 'rev-parse', '--path-format=absolute',
                             '--git-common-dir'], text=True, capture_output=True, timeout=10)
    return 'project', ('git:' + str(Path(result.stdout.strip()).resolve()) if result.returncode == 0
                       else 'directory:' + str(path))


def register(root, selection):
    kind, target = identity(**selection)
    root = root_path(root)
    conn = control(root)
    try:
        conn.execute('BEGIN IMMEDIATE')
        require(conn.execute("SELECT value FROM settings WHERE key='mode'").fetchone()[0] != 'off',
                'Memory is off')
        row = conn.execute('SELECT id FROM stores WHERE kind=? AND identity=?', (kind, target)).fetchone()
        if row:
            return {'store_id': row[0], 'kind': kind, 'existing': True}
        sid = 'store_' + uuid.uuid4().hex
        folder = root / 'stores' / sid
        folder.mkdir(parents=True, mode=0o700)
        path = folder / 'memory.sqlite3'
        private_file(path)
        database = connection(path)
        try:
            database.executescript(SCHEMA)
            database.executemany('INSERT INTO meta VALUES (?,?)',
                                 [('version', str(VERSION)), ('store_id', sid), ('generation', '0')])
            database.executemany('INSERT INTO aliases VALUES (?,?)', ALIASES.items())
        finally:
            database.close()
        conn.execute('INSERT INTO stores VALUES (?,?,?)', (sid, kind, target))
        conn.commit()
        return {'store_id': sid, 'kind': kind, 'existing': False}
    finally:
        conn.close()


class Memory:
    def __init__(self, root, selection, skills):
        self.root = root_path(root)
        self.skills = skills
        self.conn = control(root)
        try:
            self._enabled()
            kind, target = identity(**selection)
            row = self.conn.execute('SELECT id FROM stores WHERE kind=? AND identity=?',
                                    (kind, target)).fetchone()
            require(row is not None, 'Scope is not registered; explicitly register this project first')
            self.sid, self.kind = row[0], kind
            path = safe_path(self.root / 'stores' / self.sid / 'memory.sqlite3')
            require(path.is_file() and path.stat().st_nlink == 1, 'Missing or linked store')
            self.conn.execute('ATTACH DATABASE ? AS data', ('file:' + quote(str(path)) + '?mode=rw',))
            self.conn.execute('PRAGMA data.secure_delete=ON')
            self.conn.execute('PRAGMA data.synchronous=FULL')
            self._version()
        except BaseException:
            self.conn.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.conn.close()

    def _enabled(self):
        require(self.conn.execute("SELECT value FROM settings WHERE key='mode'").fetchone()[0] == 'manual',
                'Memory is off')

    def _version(self):
        meta = dict(self.conn.execute('SELECT key,value FROM data.meta'))
        require(meta.get('version') == str(VERSION) and meta.get('store_id') == self.sid,
                'Unsupported or mismatched store schema')
        require(self.conn.execute('PRAGMA main.journal_mode').fetchone()[0] == 'delete' and
                self.conn.execute('PRAGMA data.journal_mode').fetchone()[0] == 'delete',
                'Registry/store require rollback journals for atomic deletion-ledger writes')

    @contextmanager
    def transaction(self):
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            self._enabled()
            self._version()
            yield
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def aliases(self):
        return dict(self.conn.execute('SELECT name,target FROM data.aliases'))

    def _get(self, rid):
        identifier(rid)
        require(not self.conn.execute('SELECT 1 FROM deleted WHERE store_id=? AND record_id=?',
                                     (self.sid, rid)).fetchone(), 'Record was forgotten')
        row = self.conn.execute('SELECT body FROM data.records WHERE id=?', (rid,)).fetchone()
        require(row is not None, 'Record not found in selected scope')
        record = validate(decode(row[0]), self.skills, self.aliases())
        require(record['scope'] == {'kind': self.kind, 'owner_id': self.sid}, 'Mismatched record scope')
        return record

    def _check_relations(self, record):
        for relation in record['relations']:
            self._get(relation['id'])

    def _save(self, record):
        validate(record, self.skills, self.aliases())
        self._check_relations(record)
        self.conn.execute('INSERT INTO data.records VALUES (?,?,?) ON CONFLICT(id) DO UPDATE '
                          'SET revision=excluded.revision,body=excluded.body',
                          (record['id'], record['revision'], canonical(record)))
        self.conn.execute('INSERT INTO versions VALUES (?,?,?) ON CONFLICT(store_id,record_id) '
                          'DO UPDATE SET revision=MAX(revision,excluded.revision)',
                          (self.sid, record['id'], record['revision']))
        self._invalidate(record['id'])

    def _invalidate(self, rid):
        for row in self.conn.execute('SELECT id,body FROM data.candidates').fetchall():
            if rid in decode(row['body'])['sources']:
                self.conn.execute("UPDATE data.candidates SET state='invalidated' WHERE id=?", (row['id'],))
        for row in self.conn.execute("SELECT id,refs FROM data.artifacts WHERE kind='candidate'").fetchall():
            if rid in decode(row['refs']):
                self.conn.execute("UPDATE data.artifacts SET state='pending' WHERE id=?", (row['id'],))

    def mutate(self, operation, request, action):
        operation_identifier(operation)
        with self.transaction():
            secret = bytes.fromhex(self.conn.execute("SELECT value FROM settings WHERE key='secret'").fetchone()[0])
            fingerprint = hmac.new(secret, canonical(request).encode(), hashlib.sha256).hexdigest()
            existing = self.conn.execute('SELECT * FROM data.operations WHERE id=?', (operation,)).fetchone()
            if existing:
                require(existing['fingerprint'] is not None, 'Operation refers to forgotten content')
                require(hmac.compare_digest(existing['fingerprint'], fingerprint), 'Operation ID payload conflict')
                return dict(decode(existing['result']), replayed=True)
            result = action()
            result.update(operation_id=operation, replayed=False)
            self.conn.execute('INSERT INTO data.operations VALUES (?,?,?)',
                              (operation, fingerprint, canonical(result)))
            for rid in result.get('records', {}):
                self.conn.execute('INSERT INTO data.operation_records VALUES (?,?)', (operation, rid))
            self.conn.execute("UPDATE data.meta SET value=CAST(value AS INTEGER)+1 WHERE key='generation'")
            return result

    def create(self, payload, operation):
        def action():
            require(self.conn.execute('SELECT count(*) FROM data.records').fetchone()[0] < 10000,
                    'Local store limit is 10,000 records')
            record = make(payload, {'kind': self.kind, 'owner_id': self.sid}, self.skills, self.aliases())
            duplicates = []
            for row in self.conn.execute('SELECT body FROM data.records'):
                other = decode(row[0])
                if (other['title'], other['statement']) == (record['title'], record['statement']):
                    duplicates.append(other['id'])
            self._save(record)
            return {'records': {record['id']: 1}, 'state': 'created', 'possible_duplicates': duplicates}
        return self.mutate(operation, {'action': 'create', 'payload': payload}, action)

    def update_many(self, revisions, patch, operation):
        require(isinstance(revisions, dict) and 0 < len(revisions) <= 100, 'Select 1-100 IDs with expected revisions')
        require(isinstance(patch, dict) and bool(patch) and set(patch) <= EDITABLE, 'Invalid update fields')
        def action():
            records = []
            for rid, revision in revisions.items():
                record = self._get(rid)
                require(type(revision) is int and record['revision'] == revision, 'Revision conflict; reread record')
                record.update(patch)
                record.update(revision=revision + 1, updated_at=now())
                records.append(validate(record, self.skills, self.aliases()))
            for record in records:
                self._save(record)
            return {'records': {r['id']: r['revision'] for r in records}, 'state': 'updated'}
        return self.mutate(operation, {'action': 'update', 'revisions': revisions, 'patch': patch}, action)

    def show(self, rid):
        with self.transaction():
            return self._get(rid)

    def find(self, query='', category=None, domain=None, tag=None, include_inactive=False,
             applicability=None, limit=5, budget=4000):
        require(type(limit) is int and 1 <= limit <= 100, 'Limit must be 1-100')
        require(type(budget) is int and 1 <= budget <= 32000, 'Budget must be 1-32000 characters')
        require(isinstance(query, str) and len(query) <= 500, 'Query too long')
        if applicability is not None:
            require(isinstance(applicability, dict) and set(applicability) <= {'modules', 'platforms', 'versions', 'branches'},
                    'Invalid applicability filter')
            from .schema import strings
            for key, values in applicability.items():
                strings(values, key)
        with self.transaction():
            instant = timestamp(now())
            selected = []
            wanted_tag = tags([tag], self.aliases())[0] if tag else None
            for row in self.conn.execute('SELECT id FROM data.records ORDER BY id').fetchall():
                record = self._get(row[0])
                expired = record['expires_at'] is not None and timestamp(record['expires_at']) <= instant
                if not include_inactive and (record['status'] != 'active' or expired):
                    continue
                if category and record['category'] != category:
                    continue
                if domain and domain not in record['domains']:
                    continue
                if wanted_tag and wanted_tag not in record['tags']:
                    continue
                conditions = record['applicability']
                mismatch = any(values and not (set(values) & set((applicability or {}).get(key, [])))
                               for key, values in conditions.items())
                if mismatch and not include_inactive:
                    continue
                haystack = ' '.join([record['title'], record['statement'], *record['tags']]).casefold()
                words = query.casefold().split()
                score = sum(haystack.count(word) for word in words)
                if words and not all(word in haystack for word in words):
                    continue
                record['recall'] = {'expired': expired, 'applicability_unmatched': mismatch,
                                    'review_due': record['review_after'] is not None and
                                    timestamp(record['review_after']) <= instant,
                                    'source_check': 'not-performed', 'score': score}
                selected.append(record)
            # Lock acquisition and a long scan can cross an expiry boundary.
            # Refresh eligibility before facets/snippets are returned as well.
            instant = timestamp(now())
            for record in selected:
                record['recall']['expired'] = record['expires_at'] is not None and timestamp(record['expires_at']) <= instant
                record['recall']['review_due'] = record['review_after'] is not None and timestamp(record['review_after']) <= instant
            if not include_inactive:
                selected = [record for record in selected if not record['recall']['expired']]
            selected.sort(key=lambda r: (-r['recall']['score'], r['id']))
            facets = {key: {} for key in ('categories', 'domains', 'tags')}
            for record in selected:
                for key, values in (('categories', [record['category']]), ('domains', record['domains']), ('tags', record['tags'])):
                    for value in values:
                        facets[key][value] = facets[key].get(value, 0) + 1
            results = []
            for record in selected[:limit]:
                remaining = max(0, budget - sum(len(r['statement']) for r in results))
                if not remaining:
                    break
                record['recall']['truncated'] = len(record['statement']) > remaining
                record['statement'] = record['statement'][:remaining]
                results.append(record)
            generation = self.conn.execute("SELECT value FROM data.meta WHERE key='generation'").fetchone()[0]
            return {'records': results, 'facets': facets, 'matches': len(selected),
                    'receipt': {'store_id': self.sid, 'generation': int(generation),
                                'revisions': {r['id']: r['revision'] for r in results}}}

    def revalidate(self, receipt):
        with self.transaction():
            require(isinstance(receipt, dict) and set(receipt) == {'store_id', 'generation', 'revisions'}, 'Invalid recall receipt')
            require(receipt['store_id'] == self.sid, 'Wrong receipt scope')
            require(type(receipt['generation']) is int and receipt['generation'] >= 0 and
                    isinstance(receipt['revisions'], dict) and len(receipt['revisions']) <= 100,
                    'Invalid recall receipt generation/revisions')
            generation = int(self.conn.execute("SELECT value FROM data.meta WHERE key='generation'").fetchone()[0])
            require(generation == receipt.get('generation'), 'Recall is stale; retrieve again')
            for rid, revision in receipt.get('revisions', {}).items():
                require(type(revision) is int and revision > 0, 'Invalid recall receipt revision')
                record = self._get(rid)
                require(record['revision'] == revision and record['status'] == 'active', 'Recall is stale or inactive; retrieve again')
                require(record['expires_at'] is None or timestamp(record['expires_at']) > timestamp(now()),
                        'Recall expired; retrieve again')
            return {'valid': True, 'source_check': 'not-performed'}

    def forget(self, rid, revision, operation):
        def action():
            record = self._get(rid)
            require(type(revision) is int and record['revision'] == revision, 'Revision conflict; reread record')
            self.conn.execute('INSERT INTO deleted VALUES (?,?,?)', (self.sid, rid, revision + 1))
            self.conn.execute('DELETE FROM data.records WHERE id=?', (rid,))
            self.conn.execute('UPDATE data.operations SET fingerprint=NULL,result=? WHERE id IN '
                              '(SELECT operation_id FROM data.operation_records WHERE record_id=?)',
                              (canonical({'state': 'forgotten'}), rid))
            self._invalidate(rid)
            for row in self.conn.execute('SELECT id,body FROM data.candidates').fetchall():
                if rid in decode(row['body'])['sources']:
                    self.conn.execute('DELETE FROM data.candidates WHERE id=?', (row['id'],))
            for row in self.conn.execute('SELECT id,refs FROM data.artifacts').fetchall():
                if rid in decode(row['refs']):
                    self.conn.execute("UPDATE data.artifacts SET state='pending' WHERE id=?", (row['id'],))
            for row in self.conn.execute('SELECT id,body FROM data.records').fetchall():
                other = decode(row['body'])
                relations = [r for r in other['relations'] if r['id'] != rid]
                if relations != other['relations']:
                    other.update(relations=relations, status='stale', revision=other['revision'] + 1,
                                 updated_at=max(now(), other['updated_at'], key=timestamp))
                    self._save(other)
            return {'records': {rid: revision + 1}, 'state': 'forgotten', 'logical_removal': True}
        result = self.mutate(operation, {'action': 'forget', 'id': rid, 'revision': revision}, action)
        result['cleanup'] = self.cleanup()
        return result

    def cleanup(self):
        results = []
        with self.transaction():
            for row in self.conn.execute("SELECT * FROM data.artifacts WHERE state='pending'").fetchall():
                try:
                    path = safe_path(self.root / row['path'])
                    require(path.is_relative_to(self.root / 'artifacts'), 'Artifact path escapes owned storage')
                    if path.exists():
                        require(path.is_file() and path.stat().st_nlink == 1, 'Artifact was replaced or linked')
                        path.unlink()
                    self.conn.execute("UPDATE data.artifacts SET state='removed' WHERE id=?", (row['id'],))
                    results.append({'id': row['id'], 'state': 'removed'})
                except (OSError, Error):
                    results.append({'id': row['id'], 'state': 'pending'})
        return {'artifacts': results, 'outside_control': ['unmanaged copies', 'published Git history',
                                                       'host chat context', 'filesystem snapshots']}

    def merge_tag(self, old, new, revisions, operation):
        old, new = tags([old], {}), tags([new], {})
        old, new = old[0], new[0]
        require(old != new, 'Alias must change a tag')
        require(isinstance(revisions, dict) and len(revisions) <= 10000 and
                all(type(revision) is int and revision > 0 for revision in revisions.values()),
                'Select exact IDs with integer expected revisions')
        def action():
            aliases = self.aliases()
            source = aliases.get(old, old)
            target = aliases.get(new, new)
            require(target != source, 'Tags already share a canonical tag')
            records = [self._get(r[0]) for r in self.conn.execute('SELECT id FROM data.records').fetchall()]
            affected = [r for r in records if source in r['tags']]
            require({r['id']: r['revision'] for r in affected} == revisions,
                    'Affected tag selection changed; preview and retry')
            self.conn.execute('UPDATE data.aliases SET target=? WHERE target=?', (target, source))
            self.conn.execute('INSERT INTO data.aliases VALUES (?,?) ON CONFLICT(name) DO UPDATE SET target=excluded.target',
                              (source, target))
            for record in affected:
                record.update(tags=tags(record['tags'], self.aliases()), revision=record['revision'] + 1, updated_at=now())
                self._save(record)
            return {'state': 'tag-merged', 'records': {r['id']: r['revision'] for r in affected}}
        return self.mutate(operation, {'action': 'merge-tag', 'old': old, 'new': new, 'revisions': revisions}, action)
