"""Real SQLite/CLI contracts with synthetic records and disposable repositories."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone, timedelta
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'skills/reflect/scripts/learning'
spec = importlib.util.spec_from_file_location('orbyn_learning_tests', PACKAGE / '__init__.py',
                                             submodule_search_locations=[str(PACKAGE)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
from orbyn_learning_tests import artifacts, schema, store

CLI = ROOT / 'skills/reflect/scripts/memory.py'
SKILLS = {r['name'] for r in json.loads((ROOT / 'skills/catalog.json').read_text())['skills']}


def payload(**changes):
    result = dict(title='Retain pending edits', statement='A late save response must preserve newer unsaved input.',
                  category='failure-pattern', domains=['frontend', 'backend', 'ux'],
                  tags=['tech:react', 'topic:async-save'], related_skills=['orbyn-ui-design'])
    result.update(changes)
    return result


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'private-memory'
        self.project = self.base / 'project'
        self.project.mkdir()
        store.init(self.root, 'manual')
        self.selection = {'project': self.project}
        self.binding = store.register(self.root, self.selection)
        self.memory = store.Memory(self.root, self.selection, SKILLS)
        self.addCleanup(self.memory.conn.close)

    def create(self, **changes):
        result = self.memory.create(payload(**changes), 'create_' + str(self.memory.conn.total_changes))
        return next(iter(result['records']))

    def write(self, name, value):
        path = self.base / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def command(self, *args):
        return [sys.executable, str(CLI), '--root', str(self.root), '--project', str(self.project), *map(str, args)]

    def git(self, path, *args):
        result = subprocess.run(['git', '-C', str(path), *args], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def brief(self, **changes):
        result = dict(title='Pending edits', skill='orbyn-ui-design', base_revision='a' * 40,
                      problem='Late response loses input.', proposed_change='Keep submitted and current drafts separate.',
                      synthetic_case='Hold response, type more, release.', counterexample='No new edit: mark saved.',
                      validation_plan='Run failing-before and adjacent cases.', delivery='manual')
        result.update(changes)
        return result

    def test_crud_tags_categories_and_archive(self):
        rid = self.create(tags=['Tech:Postgres', 'topic:writer-fencing'])
        record = self.memory.show(rid)
        self.assertIn('tech:postgresql', record['tags'])
        self.assertEqual(self.memory.find(tag='tech:postgres')['matches'], 1)
        self.memory.update_many({rid: 1}, {'category': 'solution-pattern', 'tags': ['concern:data-loss']}, 'correct')
        self.assertEqual(self.memory.find(category='solution-pattern')['records'][0]['revision'], 2)
        self.assertEqual(self.memory.find(tag='tech:postgresql')['matches'], 0)
        self.memory.update_many({rid: 2}, {'status': 'archived'}, 'archive')
        self.assertEqual(self.memory.find()['matches'], 0)
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 1)
        result = self.memory.forget(rid, 3, 'forget')
        self.assertTrue(result['logical_removal'])
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 0)
        with self.assertRaisesRegex(schema.Error, 'forgotten'):
            self.memory.show(rid)

    def test_invalid_records_leave_no_effect(self):
        for change in ({'category': 'invented'}, {'tags': ['postgres']}, {'domains': []},
                       {'domains': ['frontend', 'frontend']}, {'evidence_level': 'validated'},
                       {'status': 'published'}, {'related_skills': ['missing-skill']},
                       {'statement': '\ud800'}, {'expires_at': '2026-10-25'},
                       {'revision': 99}, {'scope': {'kind': 'personal'}}):
            with self.subTest(change=change), self.assertRaises((schema.Error, ValueError)):
                self.memory.create(payload(**change), 'invalid')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 0)
        self.assertEqual(self.memory.conn.execute('SELECT count(*) FROM data.operations').fetchone()[0], 0)

    def test_idempotency_retries_and_conflicting_payload(self):
        first = self.memory.create(payload(), 'same')
        second = self.memory.create(payload(), 'same')
        self.assertEqual(first['records'], second['records'])
        self.assertTrue(second['replayed'])
        with self.assertRaisesRegex(schema.Error, 'payload conflict'):
            self.memory.create(payload(statement='Different'), 'same')
        self.assertEqual(self.memory.find()['matches'], 1)

    def test_standard_uuid_operation_id_starting_with_digit(self):
        operation = '01234567-89ab-4cde-8fab-0123456789ab'
        result = self.memory.create(payload(), operation)
        retry = self.memory.create(payload(), operation)
        self.assertEqual(result['records'], retry['records'])
        self.assertTrue(retry['replayed'])

    def test_forget_removes_payload_from_operations_and_candidates(self):
        secret = 'synthetic-private-needle-517'
        rid = self.create(statement=secret)
        cid = artifacts.propose(self.memory, self.brief(problem=secret), {rid: 1}, 'proposal')['candidate_id']
        self.memory.forget(rid, 1, 'forget')
        with self.assertRaisesRegex(schema.Error, 'forgotten'):
            self.memory.create(payload(statement=secret), 'create_0')
        with self.assertRaisesRegex(schema.Error, 'not found'):
            artifacts.candidate(self.memory, cid)
        data = '\n'.join(self.memory.conn.iterdump())
        self.assertNotIn(secret, data)
        raw = (self.root / 'stores' / self.binding['store_id'] / 'memory.sqlite3').read_bytes()
        self.assertNotIn(secret.encode(), raw)  # Ordinary-table secure-delete, not forensic erasure.

    def test_atomic_bulk_update_and_tag_alias_merge(self):
        a, b = self.create(tags=['tech:react']), self.create(tags=['tech:react'])
        with self.assertRaisesRegex(schema.Error, 'conflict'):
            self.memory.update_many({a: 1, b: 9}, {'category': 'decision'}, 'bad-bulk')
        self.assertEqual(self.memory.show(a)['revision'], 1)
        with self.assertRaisesRegex(schema.Error, 'selection changed'):
            self.memory.merge_tag('tech:react', 'tech:reactjs', {a: 1}, 'bad-alias')
        self.memory.merge_tag('tech:react', 'tech:reactjs', {a: 1, b: 1}, 'alias')
        self.assertEqual(self.memory.find(tag='tech:react')['matches'], 2)
        self.assertEqual(self.memory.show(b)['tags'], ['tech:reactjs'])
        self.assertEqual(self.memory.show(b)['revision'], 2)

    def test_merging_seeded_and_created_aliases_moves_canonical_records(self):
        a = self.create(tags=['tech:postgres'])
        b = self.create(tags=['tech:postgresql'])
        with self.assertRaisesRegex(schema.Error, 'selection changed'):
            self.memory.merge_tag('tech:postgres', 'tech:sqlite', {}, 'empty-redirect')
        self.assertEqual(self.memory.aliases()['tech:postgres'], 'tech:postgresql')
        self.memory.merge_tag('tech:postgres', 'tech:sqlite', {a: 1, b: 1}, 'seeded-alias')
        for name in ['tech:postgres', 'tech:postgresql', 'tech:sqlite']:
            self.assertEqual(self.memory.find(tag=name)['matches'], 2)
        self.memory.merge_tag('tech:postgres', 'tech:duckdb', {a: 2, b: 2}, 'created-alias')
        for name in ['tech:postgres', 'tech:postgresql', 'tech:sqlite', 'tech:duckdb']:
            self.assertEqual(self.memory.find(tag=name)['matches'], 2)
        self.assertEqual(self.memory.show(a)['tags'], ['tech:duckdb'])
        self.assertEqual(self.memory.show(b)['revision'], 3)
        with self.assertRaisesRegex(schema.Error, 'canonical'):
            self.memory.merge_tag('tech:postgres', 'tech:duckdb', {}, 'already-merged')

    def test_alias_merge_preserves_other_scope_and_refuses_stale_selection(self):
        rid = self.create(tags=['tech:postgres'])
        other = self.base / 'other-alias'
        other.mkdir()
        store.register(self.root, {'project': other})
        with store.Memory(self.root, {'project': other}, SKILLS) as second:
            second.create(payload(tags=['tech:postgres']), 'other-create')
            with self.assertRaisesRegex(schema.Error, 'selection changed'):
                self.memory.merge_tag('tech:postgres', 'tech:sqlite', {rid: 2}, 'stale-selection')
            with self.assertRaisesRegex(schema.Error, 'integer'):
                self.memory.merge_tag('tech:postgres', 'tech:sqlite', {rid: True}, 'boolean-selection')
            self.memory.merge_tag('tech:postgres', 'tech:sqlite', {rid: 1}, 'merge')
            self.assertEqual(second.find(tag='tech:postgresql')['matches'], 1)
            self.assertEqual(second.find(tag='tech:sqlite')['matches'], 0)
            self.assertEqual(second.aliases()['tech:postgres'], 'tech:postgresql')

    def test_project_scope_and_facets_do_not_leak(self):
        rid = self.create(tags=['module:private-editor'])
        other = self.base / 'other'
        other.mkdir()
        with self.assertRaisesRegex(schema.Error, 'not registered'):
            store.Memory(self.root, {'project': other}, SKILLS)
        store.register(self.root, {'project': other})
        with store.Memory(self.root, {'project': other}, SKILLS) as second:
            self.assertEqual(second.find()['facets']['tags'], {})
            with self.assertRaisesRegex(schema.Error, 'selected scope'):
                second.show(rid)
            with self.assertRaisesRegex(schema.Error, 'selected scope'):
                second.create(payload(relations=[{'kind': 'supports', 'id': rid}]), 'cross-relation')

    def test_worktrees_share_binding_but_clones_do_not(self):
        repo = self.base / 'git-project'
        repo.mkdir()
        self.git(repo, 'init', '-b', 'main')
        self.git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-m', 'fixture')
        linked = self.base / 'linked'
        self.git(repo, 'worktree', 'add', '-b', 'fixture', str(linked))
        a = store.register(self.root, {'project': repo})
        b = store.register(self.root, {'project': linked})
        self.assertEqual(a['store_id'], b['store_id'])
        clone = self.base / 'clone'
        self.git(self.base, 'clone', str(repo), str(clone))
        self.assertNotEqual(store.register(self.root, {'project': clone})['store_id'], a['store_id'])

    def test_disabled_mode_rejects_existing_handles(self):
        rid = self.create()
        store.set_mode(self.root, 'off')
        with self.assertRaisesRegex(schema.Error, 'off'):
            self.memory.show(rid)
        with self.assertRaisesRegex(schema.Error, 'off'):
            self.memory.create(payload(), 'disabled')
        store.set_mode(self.root, 'manual')
        self.assertEqual(self.memory.show(rid)['revision'], 1)

    def test_root_under_git_and_host_configuration_is_refused(self):
        (self.project / '.git').mkdir()
        for root in (self.project / 'memory', self.base / '.codex' / 'memories'):
            with self.subTest(root=root), self.assertRaises(schema.Error):
                store.init(root)
        self.assertFalse((self.project / 'memory').exists())

    def test_expiry_inactive_applicability_and_context_budget(self):
        self.create(status='proposed')
        self.create(status='stale')
        self.create(applicability={'modules': ['billing']})
        rid = self.create(statement='x' * 100)
        found = self.memory.find(budget=17)
        self.assertEqual(found['matches'], 1)
        self.assertEqual(len(found['records'][0]['statement']), 17)
        self.assertTrue(found['records'][0]['recall']['truncated'])
        self.assertEqual(self.memory.find(applicability={'modules': ['billing']})['matches'], 2)
        record = self.memory.show(rid)
        self.memory.update_many({rid: 1}, {'expires_at': record['created_at']}, 'expire')
        self.assertEqual(self.memory.find()['matches'], 0)

    def test_stale_receipt_after_update_and_delete(self):
        rid = self.create()
        receipt = self.memory.find()['receipt']
        self.assertTrue(self.memory.revalidate(receipt)['valid'])
        self.memory.update_many({rid: 1}, {'statement': 'Corrected.'}, 'correct')
        with self.assertRaisesRegex(schema.Error, 'stale'):
            self.memory.revalidate(receipt)
        receipt = self.memory.find()['receipt']
        self.memory.forget(rid, 2, 'forget')
        with self.assertRaisesRegex(schema.Error, 'stale'):
            self.memory.revalidate(receipt)

    def test_receipt_expires_without_an_intervening_write(self):
        self.create(expires_at='2099-01-01T00:00:00Z')
        receipt = self.memory.find()['receipt']
        with mock.patch.object(store, 'now', return_value='2100-01-01T00:00:00Z'):
            with self.assertRaisesRegex(schema.Error, 'expired'):
                self.memory.revalidate(receipt)

    def test_record_expiring_during_lock_wait_is_not_recalled(self):
        expiry = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat().replace('+00:00', 'Z')
        self.create(expires_at=expiry)
        hold = sqlite3.connect(self.root / 'registry.sqlite3')
        hold.execute('BEGIN IMMEDIATE')
        started, results = threading.Event(), {}
        def reader():
            try:
                with store.Memory(self.root, self.selection, SKILLS) as other:
                    started.set()
                    results.update(other.find())
            except Exception as exc:
                results['error'] = str(exc)
        worker = threading.Thread(target=reader)
        worker.start()
        try:
            self.assertTrue(started.wait(5))
            self.assertLess(datetime.now(timezone.utc), schema.timestamp(expiry))
            time.sleep(1.1)
        finally:
            hold.rollback()
            hold.close()
            worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self.assertNotIn('error', results)
        self.assertEqual(results['matches'], 0)
        self.assertEqual(results['facets']['categories'], {})

    def test_malformed_recall_receipts_are_structured_validation_errors(self):
        self.create()
        receipt = self.memory.find()['receipt']
        for patch in ({'revisions': []}, {'generation': True}, {'revisions': {'mem_other': True}}, {'extra': 1}):
            with self.subTest(patch=patch), self.assertRaises(schema.Error):
                self.memory.revalidate(dict(receipt, **patch))

    def test_interrupted_export_is_registered_for_cleanup(self):
        rid = self.create()
        aid, path = artifacts.reserve(self.memory, 'export', {rid: 1}, 'json')
        def fail(destination):
            destination.write_text('synthetic partial export')
            raise OSError('simulated write failure')
        with self.assertRaises(OSError):
            artifacts.materialize(self.memory, aid, path, fail)
        self.assertTrue(path.exists())
        self.assertEqual(self.memory.cleanup()['artifacts'][0]['state'], 'removed')
        self.assertFalse(path.exists())

    def test_export_reservation_cannot_run_after_forget(self):
        rid = self.create()
        aid, path = artifacts.reserve(self.memory, 'export', {rid: 1}, 'json')
        self.memory.forget(rid, 1, 'forget')
        with self.assertRaisesRegex(schema.Error, 'reservation'):
            artifacts.materialize(self.memory, aid, path, lambda p: p.write_text('must not appear'))
        self.assertFalse(path.exists())

    def test_delete_blocks_stale_update_and_retry(self):
        rid = self.create()
        self.memory.forget(rid, 1, 'forget')
        with self.assertRaisesRegex(schema.Error, 'forgotten'):
            self.memory.update_many({rid: 1}, {'statement': 'resurrect'}, 'stale-update')
        again = self.memory.forget(rid, 1, 'forget')
        self.assertTrue(again['replayed'])
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 0)

    def test_boolean_revisions_and_malformed_filter_are_refused(self):
        rid = self.create()
        with self.assertRaises(schema.Error):
            self.memory.update_many({rid: True}, {'statement': 'bad revision'}, 'bad-revision')
        with self.assertRaises(schema.Error):
            artifacts.export(self.memory, {rid: True})
        with self.assertRaises(schema.Error):
            self.memory.find(applicability={'modules': 'billing'})

    def test_import_atomicity_and_cross_scope_rejection(self):
        rid = self.create()
        good = self.memory.show(rid)
        good['id'] = 'mem_import_a'
        bad = copy.deepcopy(good)
        bad.update(id='mem_import_b', category='unknown')
        bundle = {'schema_version': 1, 'store_id': self.binding['store_id'], 'records': [good, bad]}
        with self.assertRaises(schema.Error):
            artifacts.import_records(self.memory, bundle, 'bad-import')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 1)
        bundle.update(store_id='store_other', records=[good])
        with self.assertRaisesRegex(schema.Error, 'Cross-scope'):
            artifacts.import_records(self.memory, bundle, 'cross-import')

    def test_future_dated_import_is_rejected_atomically_without_poisoning_recall(self):
        rid = self.create()
        good = self.memory.show(rid)
        good['id'] = 'mem_import_good'
        future = copy.deepcopy(good)
        future.update(id='mem_future', created_at='2099-01-01T00:00:00Z',
                      updated_at='2099-01-01T00:00:00Z', review_after=None)
        bundle = {'schema_version': 1, 'store_id': self.binding['store_id'], 'records': [future]}
        with self.assertRaisesRegex(schema.Error, 'predates creation'):
            artifacts.import_records(self.memory, bundle, 'future-only')
        bundle['records'] = [good, future]
        with self.assertRaisesRegex(schema.Error, 'predates creation'):
            artifacts.import_records(self.memory, bundle, 'mixed-future')
        self.assertEqual(self.memory.find()['matches'], 1)
        self.assertEqual(self.memory.show(rid)['revision'], 1)
        self.assertEqual(self.memory.conn.execute('SELECT count(*) FROM data.records').fetchone()[0], 1)
        self.assertEqual(self.memory.conn.execute('SELECT count(*) FROM data.operations').fetchone()[0], 1)
        self.memory.forget(rid, 1, 'forget-original')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 0)

    def test_future_dated_restore_cannot_commit_an_invalid_transformation(self):
        rid = self.create()
        future = self.memory.show(rid)
        future.update(created_at='2099-01-01T00:00:00Z', updated_at='2099-01-01T00:00:00Z', review_after=None)
        with self.memory.transaction():
            self.memory.conn.execute('UPDATE data.records SET body=? WHERE id=?', (schema.canonical(future), rid))
        snapshot = artifacts.backup(self.memory)
        with self.memory.transaction():
            self.memory.conn.execute('DELETE FROM data.records WHERE id=?', (rid,))
        generation = self.memory.find()['receipt']['generation']
        with self.assertRaisesRegex(schema.Error, 'predates creation'):
            artifacts.restore(self.memory, snapshot['artifact_id'], generation, 'future-restore')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 0)

    def test_oversized_import_revision_and_exhausted_update_have_no_effect(self):
        rid = self.create()
        record = self.memory.show(rid)
        record.update(id='mem_large_revision', revision=10**40)
        bundle = {'schema_version': 1, 'store_id': self.binding['store_id'], 'records': [record]}
        with self.assertRaisesRegex(schema.Error, 'revision'):
            artifacts.import_records(self.memory, bundle, 'overflow')
        record['revision'] = schema.MAX_REVISION
        with self.assertRaisesRegex(schema.Error, 'revision'):
            artifacts.import_records(self.memory, bundle, 'no-headroom')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 1)
        record['revision'] = schema.MAX_REVISION - 1
        artifacts.import_records(self.memory, bundle, 'last-revision')
        with self.assertRaisesRegex(schema.Error, 'revision'):
            self.memory.update_many({record['id']: schema.MAX_REVISION}, {'status': 'active'}, 'exhausted')
        self.memory.forget(record['id'], schema.MAX_REVISION, 'forget-exhausted')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 1)

    def test_malformed_candidate_skill_is_a_structured_cli_error(self):
        rid = self.create()
        brief = self.write('brief.json', self.brief(skill=[]))
        selection = self.write('brief-selection.json', {rid: 1})
        result = subprocess.run(self.command('propose', '--input', brief, '--selection', selection, '--op', 'bad-brief'),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stderr)['ok'])
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(self.memory.conn.execute('SELECT count(*) FROM data.candidates').fetchone()[0], 0)

    def test_dependent_revision_headroom_preserves_target_and_own_forgetting(self):
        targets = [self.create(title=f'Target {i}') for i in range(3)]
        dependent = self.memory.show(targets[0])
        dependent.update(id='mem_dependent', revision=schema.MAX_REVISION - 1,
                         relations=[{'kind': 'supports', 'id': targets[0]}])
        bundle = {'schema_version': 1, 'store_id': self.binding['store_id'], 'records': [dependent]}
        with self.assertRaisesRegex(schema.Error, 'headroom'):
            artifacts.import_records(self.memory, bundle, 'unrepairable-dependent')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 3)
        dependent.update(revision=schema.MAX_REVISION - 4,
                         relations=[{'kind': 'supports', 'id': rid} for rid in targets])
        artifacts.import_records(self.memory, bundle, 'bounded-dependent')
        for index, rid in enumerate(targets):
            previous = self.memory.show(dependent['id'])['revision']
            self.memory.forget(rid, 1, f'forget-target-{index}')
            survivor = self.memory.show(dependent['id'])
            self.assertEqual(survivor['revision'], previous + 1)
            self.assertEqual(survivor['status'], 'stale')
            self.assertEqual(len(survivor['relations']), 2 - index)
            with self.assertRaisesRegex(schema.Error, 'forgotten'):
                self.memory.show(rid)
            with self.assertRaisesRegex(schema.Error, 'Revision conflict'):
                self.memory.update_many({dependent['id']: previous}, {'status': 'active'}, f'stale-dependent-{index}')
        self.assertEqual(survivor['revision'], schema.MAX_REVISION)
        self.memory.forget(dependent['id'], schema.MAX_REVISION, 'forget-terminal-dependent')
        self.assertEqual(self.memory.find(include_inactive=True)['matches'], 0)

    def test_forget_dependency_cleanup_survives_wall_clock_rollback(self):
        target = self.create()
        dependent = self.create(title='Dependent', relations=[{'kind': 'derived-from', 'id': target}])
        original_time = self.memory.show(dependent)['updated_at']
        with mock.patch.object(store, 'now', return_value='2000-01-01T00:00:00Z'):
            self.memory.forget(target, 1, 'forget-after-clock-rollback')
        record = self.memory.show(dependent)
        self.assertEqual(record['revision'], 2)
        self.assertEqual(record['status'], 'stale')
        self.assertEqual(record['relations'], [])
        self.assertEqual(record['updated_at'], original_time)

    def test_changed_backup_selection_cannot_leave_untracked_content(self):
        self.create()
        original = artifacts.materialize
        def interleaved(memory, aid, path, producer):
            self.create(statement='Created between reservation and snapshot')
            return original(memory, aid, path, producer)
        with mock.patch.object(artifacts, 'materialize', side_effect=interleaved):
            with self.assertRaisesRegex(schema.Error, 'selection changed'):
                artifacts.backup(self.memory)
        self.assertTrue(self.memory.cleanup()['artifacts'])

    def test_concurrent_real_cli_writers_have_one_winner(self):
        rid = self.create()
        selection = self.write('selection.json', {rid: 1})
        patch = self.write('patch.json', {'statement': 'Concurrent correction'})
        processes = [subprocess.Popen(self.command('update', '--selection', selection, '--input', patch,
                                                  '--op', f'writer_{i}'), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) for i in range(2)]
        results = [p.communicate(timeout=15) for p in processes]
        self.assertEqual(sorted(p.returncode for p in processes), [0, 1], results)
        self.assertEqual(self.memory.show(rid)['revision'], 2)
        self.assertTrue(any('Revision conflict' in err for _, err in results))

    def test_killed_uncommitted_writer_rolls_back(self):
        rid = self.create()
        path = self.root / 'stores' / self.binding['store_id'] / 'memory.sqlite3'
        script = """import sqlite3,sys,time
c=sqlite3.connect(sys.argv[1]); c.execute('BEGIN IMMEDIATE')
c.execute('DELETE FROM records'); print('ready',flush=True); time.sleep(30)
"""
        child = subprocess.Popen([sys.executable, '-c', script, str(path)], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'ready')
        finally:
            child.kill()
            child.wait(timeout=5)
            child.stdout.close()
        self.assertEqual(self.memory.show(rid)['revision'], 1)

    def test_export_json_html_escape_and_forget_cleanup(self):
        rid = self.create(title='<script>alert(1)</script>', statement='</script><img src=x onerror=alert(1)>')
        output = artifacts.export(self.memory, {rid: 1}, 'html')
        path = Path(output['path'])
        self.assertIn('&lt;script&gt;', path.read_text())
        self.assertNotIn('<img src=x', path.read_text())
        exported = artifacts.export(self.memory, {rid: 1})
        self.assertEqual(artifacts.read_json(Path(exported['path']))['records'][0]['id'], rid)
        result = self.memory.forget(rid, 1, 'forget')
        self.assertFalse(path.exists())
        self.assertFalse(Path(exported['path']).exists())
        self.assertTrue(all(a['state'] == 'removed' for a in result['cleanup']['artifacts']))

    def test_changed_artifact_path_stays_pending_and_never_deletes_foreign_file(self):
        rid = self.create()
        output = artifacts.export(self.memory, {rid: 1})
        path = Path(output['path'])
        path.unlink()
        foreign = self.base / 'foreign.txt'
        foreign.write_text('preserve')
        path.symlink_to(foreign)
        result = self.memory.forget(rid, 1, 'forget')
        self.assertEqual(result['cleanup']['artifacts'][0]['state'], 'pending')
        self.assertEqual(foreign.read_text(), 'preserve')
        self.assertEqual(self.memory.find()['matches'], 0)

    def test_import_no_overwrite_no_resurrection_and_quarantines(self):
        rid = self.create()
        bundle = {'schema_version': 1, 'store_id': self.binding['store_id'], 'records': [self.memory.show(rid)]}
        with self.assertRaisesRegex(schema.Error, 'overwrite'):
            artifacts.import_records(self.memory, bundle, 'overwrite')
        fresh = copy.deepcopy(bundle)
        fresh['records'][0]['id'] = 'mem_new_import'
        result = artifacts.import_records(self.memory, fresh, 'import')
        self.assertEqual(result['state'], 'imported-proposed')
        self.assertEqual(self.memory.show('mem_new_import')['status'], 'proposed')
        self.memory.forget(rid, 1, 'forget')
        with self.assertRaisesRegex(schema.Error, 'forgotten'):
            artifacts.import_records(self.memory, bundle, 'old-import')
        bad = copy.deepcopy(fresh)
        bad['records'][0]['id'] = 'mem_invalid'
        bad['records'][0]['category'] = 'unknown-category'
        with self.assertRaisesRegex(schema.Error, 'category'):
            artifacts.import_records(self.memory, bad, 'bad-import')

    def test_backup_restore_uses_ledger_and_keeps_newer_live_state(self):
        a, b = self.create(), self.create()
        backup = artifacts.backup(self.memory)
        # Model loss of live records, while the separate deletion ledger survives.
        with self.memory.transaction():
            self.memory.conn.execute('INSERT INTO deleted VALUES (?,?,?)', (self.binding['store_id'], a, 2))
            self.memory.conn.execute('DELETE FROM data.records WHERE id=?', (a,))
            self.memory.conn.execute('DELETE FROM data.records WHERE id=?', (b,))
        generation = self.memory.find()['receipt']['generation']
        result = artifacts.restore(self.memory, backup['artifact_id'], generation, 'restore')
        self.assertEqual(result['suppressed_ids'], [a])
        self.assertEqual(self.memory.show(b)['status'], 'proposed')
        self.assertEqual(self.memory.find()['matches'], 0)
        generation = self.memory.find()['receipt']['generation']
        self.memory.update_many({b: 2}, {'statement': 'Newer restored state.'}, 'newer')
        with self.assertRaisesRegex(schema.Error, 'changed'):
            artifacts.restore(self.memory, backup['artifact_id'], generation, 'old-generation')
        generation = self.memory.find()['receipt']['generation']
        result = artifacts.restore(self.memory, backup['artifact_id'], generation, 'restore-again')
        self.assertEqual(result['records'], {})
        self.assertEqual(self.memory.show(b)['statement'], 'Newer restored state.')

    def test_candidate_invalidation_after_source_correction(self):
        rid = self.create()
        cid = artifacts.propose(self.memory, self.brief(), {rid: 1}, 'propose')['candidate_id']
        self.memory.update_many({rid: 1}, {'statement': 'Revised lesson.'}, 'correct')
        self.assertEqual(artifacts.candidate(self.memory, cid)['state'], 'invalidated')

    def test_restore_never_reuses_revision_seen_by_an_old_writer(self):
        rid = self.create()
        backup = artifacts.backup(self.memory)
        self.memory.update_many({rid: 1}, {'statement': 'Second revision'}, 'second')
        self.memory.update_many({rid: 2}, {'statement': 'Third revision'}, 'third')
        with self.memory.transaction():
            self.memory.conn.execute('DELETE FROM data.records WHERE id=?', (rid,))
        generation = self.memory.find()['receipt']['generation']
        artifacts.restore(self.memory, backup['artifact_id'], generation, 'restore')
        self.assertEqual(self.memory.show(rid)['revision'], 4)
        for stale in (1, 2, 3):
            with self.assertRaisesRegex(schema.Error, 'Revision conflict'):
                self.memory.update_many({rid: stale}, {'statement': 'Stale editor'}, f'stale_{stale}')

    def test_source_freshness_checks_real_file_and_rejects_escape(self):
        source = self.project / 'rules.txt'
        source.write_text('version one')
        digest = 'sha256:' + hashlib.sha256(source.read_bytes()).hexdigest()
        rid = self.create(evidence=[{'kind': 'source', 'ref': 'rules.txt', 'revision': digest}])
        checked = artifacts.check_sources(self.memory, rid, 1, self.project, 'check')
        self.assertTrue(checked['checks'][0]['matched'])
        source.write_text('version two')
        artifacts.check_sources(self.memory, rid, 1, self.project, 'changed')
        self.assertEqual(self.memory.show(rid)['status'], 'stale')
        bad = self.create(evidence=[{'kind': 'source', 'ref': '../outside', 'revision': digest}])
        with self.assertRaisesRegex(schema.Error, 'Unsafe'):
            artifacts.check_sources(self.memory, bad, 1, self.project, 'escape')

    def test_schema_version_fences_old_writer(self):
        rid = self.create()
        self.memory.conn.execute("UPDATE data.meta SET value='2' WHERE key='version'")
        with self.assertRaisesRegex(schema.Error, 'schema'):
            self.memory.update_many({rid: 1}, {'statement': 'Unsafe old writer'}, 'old-writer')

    def test_cli_offline_end_to_end_and_duplicate_json_rejection(self):
        input_path = self.write('input.json', payload())
        result = subprocess.run(self.command('remember', '--input', input_path, '--op', 'cli-create'),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        rid = next(iter(json.loads(result.stdout)['result']['records']))
        result = subprocess.run(self.command('find', '--tag', 'tech:react'), text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout)['result']['matches'], 1)
        result = subprocess.run(self.command('forget', rid, '--revision', '1', '--op', 'cli-forget'),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        input_path.write_text('{"title":"one","title":"two"}')
        result = subprocess.run(self.command('remember', '--input', input_path, '--op', 'duplicate'),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Duplicate JSON', result.stderr)

    def test_portable_skill_helper_has_no_repository_root_import(self):
        copied = self.base / 'portable/skills'
        shutil.copytree(ROOT / 'skills/reflect', copied / 'reflect', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(ROOT / 'skills/catalog.json', copied / 'catalog.json')
        command = self.command('taxonomy')
        command[1] = str(copied / 'reflect/scripts/memory.py')
        result = subprocess.run(command, cwd=self.base, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('failure-pattern', json.loads(result.stdout)['result']['categories'])

    def test_manual_patch_is_allowlisted_base_bound_and_never_commits(self):
        repo = self.base / 'skill-candidate'
        (repo / 'skills/orbyn-ui-design').mkdir(parents=True)
        path = repo / 'skills/orbyn-ui-design/SKILL.md'
        path.write_text('Original method.\n')
        self.git(repo, 'init', '-b', 'main')
        self.git(repo, 'add', 'skills')
        self.git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture')
        head = self.git(repo, 'rev-parse', 'HEAD')
        path.write_text('Improved method.\n')
        (repo / 'private.txt').write_text('never export')
        rid = self.create()
        cid = artifacts.propose(self.memory, self.brief(base_revision=head, delivery='fork-branch'),
                                {rid: 1}, 'propose')['candidate_id']
        with self.assertRaisesRegex(schema.Error, 'allowlist'):
            artifacts.prepare_patch(self.memory, cid, repo, ['private.txt'], True)
        injected = 'skills/orbyn-ui-design/legit\n--- /dev/null\n+++ b/outside.txt'
        malicious = repo / injected
        malicious.parent.mkdir(parents=True, exist_ok=True)
        malicious.write_text('would escape the allowed patch path\n')
        with self.assertRaisesRegex(schema.Error, 'portable'):
            artifacts.prepare_patch(self.memory, cid, repo, [injected], True)
        self.assertFalse((repo / 'outside.txt').exists())
        result = artifacts.prepare_patch(self.memory, cid, repo, ['skills/orbyn-ui-design/SKILL.md'], True)
        patch = Path(result['path']).read_text()
        self.assertIn('+Improved method.', patch)
        self.assertNotIn(rid, patch)
        self.assertEqual(self.git(repo, 'rev-parse', 'HEAD'), head)
        self.assertFalse(result['committed'])
        self.assertFalse(result['pushed'])
        path.write_text('Original method.\n')
        self.git(repo, 'apply', '--check', result['path'])
        self.git(repo, 'apply', result['path'])
        self.assertEqual(path.read_text(), 'Improved method.\n')


if __name__ == '__main__':
    unittest.main()
