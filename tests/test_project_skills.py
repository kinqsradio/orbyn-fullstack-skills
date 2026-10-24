"""Company-owned content stays local while both hosts discover it."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, installer, module

local = module('local_skill_tools', ROOT/'skills/orbyn-setup/scripts/project_skills.py')


def make_skill(root, namespace='acme', name='acme-release'):
    target = root/'project-skills'/namespace/name
    target.mkdir(parents=True)
    (target/'SKILL.md').write_text(f'---\nname: {name}\ndescription: Internal company release process\n---\nConsumer-only material.\n')
    (target/'LICENSE').write_text('Existing company license; preserve.')
    (target/'references').mkdir()
    (target/'references/checklist.md').write_text('Internal company checklist.')
    return target


class ProjectSkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_explicit_install_registers_local_and_shared_without_rewriting_content(self):
        target = make_skill(self.root)
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()}
        (self.root/'AGENTS.md').write_text('Company policy')
        self.assertEqual(installer.install(self.root, 'both', ['how']), 2)
        self.assertFalse((self.root/'.agents/skills/acme-release').exists())
        self.assertEqual(installer.install(self.root, 'both', ['how'], project_skills=True, dry_run=True), 2)
        self.assertFalse((self.root/'.claude/skills/acme-release').exists())
        self.assertEqual(installer.install(self.root, 'both', ['how'], project_skills=True), 2)
        for host in ['.agents', '.claude']:
            link = self.root/host/'skills/acme-release'
            self.assertEqual(link.resolve(), target.resolve())
            self.assertFalse(os.path.isabs(os.readlink(link)))
        self.assertEqual(installer.install(self.root, 'both', ['how'], project_skills=True), 0)
        self.assertEqual(before, {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()})
        self.assertEqual((self.root/'AGENTS.md').read_text(), 'Company policy')

    def test_local_link_only_cli_is_idempotent_and_dry_run_does_not_write(self):
        target = make_skill(self.root)
        cli = [sys.executable, str(ROOT/'skills/orbyn-setup/scripts/project_skills.py')]
        def run(command, *args):
            return subprocess.run(cli+[command, '--project', str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(run('link', '--dry-run').returncode, 0)
        self.assertFalse((self.root/'.agents').exists())
        self.assertEqual(run('check').returncode, 1)
        self.assertEqual(run('link').returncode, 0)
        self.assertEqual(run('check').returncode, 0)
        self.assertIn('0 discovery links created', run('link').stdout)
        self.assertEqual((self.root/'.claude/skills/acme-release').resolve(), target.resolve())
        self.assertFalse((self.root/'skills').exists())

    def test_collision_or_foreign_host_target_preflights_before_writing_either_host(self):
        make_skill(self.root, 'orbyn', 'orbyn-workflow')
        with self.assertRaisesRegex(ValueError, 'collision'):
            installer.install(self.root, 'both', ['how'], project_skills=True)
        self.assertFalse((self.root/'.agents').exists())
        shutil.rmtree(self.root/'project-skills')
        make_skill(self.root)
        path = self.root/'.claude/skills/acme-release'
        path.mkdir(parents=True)
        marker = path/'SKILL.md'
        marker.write_text('Existing foreign installation')
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            installer.install(self.root, 'both', ['how'], project_skills=True)
        self.assertFalse((self.root/'.agents').exists())
        self.assertEqual(marker.read_text(), 'Existing foreign installation')

    def test_invalid_local_name_frontmatter_and_source_symlinks_are_refused(self):
        target = make_skill(self.root)
        source = target/'SKILL.md'
        source.write_text('---\nname: different\ndescription: Internal release process\n---\n')
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            local.inventory(self.root)
        source.unlink()
        outside = self.root/'outside.md'
        outside.write_text('Preserve outside source')
        source.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'regular SKILL'):
            local.inventory(self.root)
        shutil.rmtree(self.root/'project-skills')
        make_skill(self.root, name='release')
        with self.assertRaisesRegex(ValueError, 'namespaced'):
            local.inventory(self.root)
        self.assertEqual(outside.read_text(), 'Preserve outside source')

    def test_symlinked_namespace_and_host_parent_are_refused(self):
        target = make_skill(self.root)
        host = self.root/'.agents'
        host.symlink_to(self.root/'project-skills', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlinked host'):
            local.plan_links(self.root, local.inventory(self.root), ['.agents', '.claude'])
        host.unlink()
        target.rename(self.root/'moved')
        (self.root/'project-skills/acme/acme-release').symlink_to(self.root/'moved', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlinked project skill'):
            local.inventory(self.root)
        self.assertFalse((self.root/'.claude').exists())

    def test_vendored_discovery_keeps_local_skills_out_of_shared_index(self):
        make_skill(self.root)
        (self.root/'scripts').mkdir()
        shutil.copy2(ROOT/'scripts/sync-agent-skills.py', self.root/'scripts/sync-agent-skills.py')
        tools = self.root/'skills/orbyn-setup/scripts'
        tools.mkdir(parents=True)
        shutil.copy2(ROOT/'skills/orbyn-setup/scripts/project_skills.py', tools/'project_skills.py')
        (self.root/'skills/orbyn-setup/SKILL.md').write_text('---\nname: orbyn-setup\ndescription: Fixture setup\n---\n')
        (self.root/'skills/catalog.json').write_text(json.dumps({'categories':['Setup'], 'skills':[{'name':'orbyn-setup','category':'Setup'}]}))
        cli = [sys.executable, str(self.root/'scripts/sync-agent-skills.py')]
        first = subprocess.run(cli+['--write'], capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(subprocess.run(cli+['--check'], capture_output=True).returncode, 0)
        self.assertNotIn('- [acme-release]', (self.root/'skills/README.md').read_text())
        self.assertTrue((self.root/'.agents/skills/acme-release/SKILL.md').is_file())
        foreign = self.root/'.claude/skills/legacy-company-skill'
        foreign.mkdir()
        (foreign/'SKILL.md').write_text('Do not delete or silently adopt')
        self.assertNotEqual(subprocess.run(cli+['--write'], capture_output=True).returncode, 0)
        self.assertTrue((foreign/'SKILL.md').is_file())


class ExistingProjectMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base/'project'
        self.root.mkdir()
        self.sources = []
        for host in ['.agents', '.claude']:
            path = self.root/host/'skills/release'
            path.mkdir(parents=True)
            (path/'SKILL.md').write_text('---\nname: release\ndescription: Internal release process\n---\nRead [steps](references/steps.md).\n')
            (path/'references').mkdir()
            (path/'references/steps.md').write_text('Existing company steps')
            (path/'LICENSE').write_text('Retain original credit')
            self.sources.append(path)
        (self.root/'docs').mkdir()
        (self.root/'docs/architecture.md').write_text('Company architecture')
        (self.root/'AGENTS.md').write_text('Existing project instructions')
        (self.root/'.claude/settings.json').write_text('{"existing": true}')

    def install(self, **kwargs):
        return installer.install(self.root, 'both', ['how'], migrate_skills=['release'], namespace='acme', **kwargs)

    def test_dry_run_then_migrate_existing_copies_preserves_docs_assets_and_backups(self):
        self.install(dry_run=True)
        self.assertFalse((self.root/'project-skills').exists())
        self.assertEqual(list(self.base.iterdir()), [self.root])
        for path in self.sources:
            self.assertFalse(path.is_symlink())
        self.install()
        target = self.root/'project-skills/acme/acme-release'
        self.assertIn('name: acme-release', (target/'SKILL.md').read_text())
        self.assertEqual((target/'LICENSE').read_text(), 'Retain original credit')
        self.assertEqual((target/'references/steps.md').read_text(), 'Existing company steps')
        self.assertEqual((self.root/'AGENTS.md').read_text(), 'Existing project instructions')
        self.assertEqual((self.root/'docs/architecture.md').read_text(), 'Company architecture')
        self.assertEqual((self.root/'.claude/settings.json').read_text(), '{"existing": true}')
        for host in ['.agents', '.claude']:
            self.assertFalse((self.root/host/'skills/release').exists())
            self.assertEqual((self.root/host/'skills/acme-release').resolve(), target)
            self.assertEqual((self.root/host/'skills/how').resolve(), ROOT/'skills/how')
        backup, = self.base.glob('project-skill-migration-*')
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertIn('name: release', (backup/'originals/0-0/SKILL.md').read_text())
        self.assertEqual(json.loads((backup/'receipt.json').read_text())['status'], 'complete')
        self.assertEqual(installer.install(self.root, 'both', ['how'], project_skills=True), 0)

    def test_different_host_copies_refuse_before_mutation_or_backup(self):
        (self.sources[1]/'references/steps.md').write_text('Different local work')
        with self.assertRaisesRegex(ValueError, 'Conflicting host copies'):
            self.install()
        self.assertFalse((self.root/'project-skills').exists())
        self.assertFalse(list(self.base.glob('project-skill-migration-*')))
        self.assertEqual((self.sources[1]/'references/steps.md').read_text(), 'Different local work')

    def test_write_failure_rolls_back_legacy_entries_and_removes_partial_install(self):
        original = installer.PROJECT_SKILLS['write_links']
        calls = 0
        def fail_after_one(pending):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('Synthetic filesystem failure')
            original(pending)
        with mock.patch.dict(installer.PROJECT_SKILLS, {'write_links': fail_after_one}):
            with self.assertRaisesRegex(RuntimeError, 'rolled back'):
                self.install()
        for path in self.sources:
            self.assertFalse(path.is_symlink())
            self.assertIn('name: release', (path/'SKILL.md').read_text())
        self.assertFalse((self.root/'project-skills/acme/acme-release').exists())
        self.assertFalse((self.root/'.agents/skills/acme-release').exists())
        backup, = self.base.glob('project-skill-migration-*')
        self.assertEqual(json.loads((backup/'receipt.json').read_text())['status'], 'rolled_back')

    def test_external_relative_reference_stops_before_moving(self):
        (self.sources[0]/'SKILL.md').write_text('---\nname: release\ndescription: Internal release\n---\n[Neighbor](../other/SKILL.md)\n')
        with self.assertRaisesRegex(ValueError, 'Rebase external relative'):
            self.install()
        self.assertFalse((self.root/'project-skills').exists())
        self.assertFalse(self.sources[0].is_symlink())


class OfflineSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.checker = module('offline_sources', ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py')
        source = ROOT/'skills/social-content/references/upstream/marketingskills-social'
        self.base = self.root/'skills/social-content/references/upstream/marketingskills-social'
        shutil.copytree(source, self.base)

    def test_snapshot_check_and_install_work_with_sockets_disabled(self):
        project = self.root/'company'
        project.mkdir()
        with mock.patch.object(socket, 'socket', side_effect=AssertionError('Network forbidden')):
            files = self.checker.check(self.root)
            self.assertGreater(len(files), 1)
            self.assertEqual(installer.install(project, 'both', ['social-content']), 2)
        self.assertEqual((project/'.agents/skills/social-content/references/upstream/marketingskills-social/LICENSE').read_bytes(), (self.base/'LICENSE').read_bytes())

    def test_research_must_be_ignored_and_never_staged(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        for name in ['openSrc', 'orbyn-references']:
            with self.subTest(root=name):
                source = self.root/name/'vendor/source.py'
                source.parent.mkdir(parents=True)
                source.write_text('Unexecuted research source')
                ignore = self.root/'.gitignore'
                ignore.write_text('')
                with self.assertRaisesRegex(ValueError, 'Exclude'):
                    self.checker.check(self.root)
                ignore.write_text('/openSrc/\n/orbyn-references/\n')
                self.checker.check(self.root)
                subprocess.run(['git', '-C', str(self.root), 'add', '-f', '--', str(source)], check=True)
                with self.assertRaisesRegex(ValueError, 'tracked or staged'):
                    self.checker.check(self.root)
                self.assertEqual(source.read_text(), 'Unexecuted research source')
                subprocess.run(['git', '-C', str(self.root), 'rm', '--cached', '-q', '--', str(source)], check=True)

    def test_reference_root_cannot_follow_a_symlink(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        (self.root/'.gitignore').write_text('/orbyn-references/\n')
        (self.root/'orbyn-references').symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'real directory'):
            self.checker.check(self.root)

    def test_ignore_exception_cannot_expose_a_reference_file(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        source = self.root/'orbyn-references/source.py'
        source.parent.mkdir()
        source.write_text('Unexecuted research source')
        (self.root/'.gitignore').write_text('/orbyn-references/*\n!/orbyn-references/source.py\n')
        with self.assertRaisesRegex(ValueError, 'Unignored files'):
            self.checker.check(self.root)

    def test_tampered_source_missing_license_and_extra_file_are_rejected(self):
        source = self.base/'SKILL.md'
        before = source.read_bytes()
        source.write_bytes(before+b'changed')
        with self.assertRaisesRegex(ValueError, 'Changed/missing'):
            self.checker.check(self.root)
        source.write_bytes(before)
        license_file = self.base/'LICENSE'
        original = license_file.read_bytes()
        license_file.unlink()
        with self.assertRaisesRegex(ValueError, 'Changed/missing'):
            self.checker.check(self.root)
        license_file.write_bytes(original)
        (self.base/'extra.md').write_text('Undeclared material')
        with self.assertRaisesRegex(ValueError, 'Undeclared'):
            self.checker.check(self.root)

    def test_snapshot_manifest_cannot_escape_or_omit_license(self):
        path = self.base/'snapshot.json'
        original = json.loads(path.read_text())
        data = dict(original)
        data['files'] = dict(original['files'], **{'../../outside.md': {'sha256':'0'*64}})
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.checker.check(self.root)
        data = dict(original)
        data['license_files'] = []
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'license'):
            self.checker.check(self.root)
