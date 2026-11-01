"""Skill consolidation upgrades known links without deleting foreign work."""
import json
import os
import runpy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, selection, module

local = module('retirement_tools', ROOT/'scripts/discovery_links.py')
OLD = 'typescript-best-practices'
NEW = 'language-best-practices'


class SkillRetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root/'AGENTS.md').write_text('Existing company policy')

    def old_links(self):
        for host in ['.agents','.claude']:
            link=self.root/host/'skills'/OLD
            link.parent.mkdir(parents=True,exist_ok=True)
            link.symlink_to(os.path.relpath(ROOT/'skills'/OLD,link.parent))

    def test_discovery_link_loop_is_a_conflict_not_a_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            source = base/'skills/how'
            source.mkdir(parents=True)
            (source/'SKILL.md').write_text('fixture')
            link = base/'.claude/skills/how'
            link.parent.mkdir(parents=True)
            link.symlink_to('how')
            with self.assertRaisesRegex(ValueError, 'Conflicting discovery entry'):
                local.plan_links(base, {'how': source}, ['.claude'])

    def test_old_explicit_selection_maps_to_one_owner(self):
        self.assertEqual(selection.selection([OLD]),{NEW})
        self.assertNotIn(OLD,selection.selection(all_skills=True))






    def test_library_generator_retires_known_links_and_refuses_foreign_entries(self):
        (self.root/'scripts').mkdir()
        shutil.copy2(ROOT/'scripts/sync-agent-skills.py',self.root/'scripts/sync-agent-skills.py')
        setup=self.root/'skills/orbyn-setup';setup.mkdir(parents=True)
        shutil.copy2(ROOT/'scripts/discovery_links.py',self.root/'scripts/discovery_links.py')
        for name in ['orbyn-setup',NEW]:
            base=self.root/'skills'/name;base.mkdir(exist_ok=True)
            (base/'SKILL.md').write_text(f'---\nname: {name}\ndescription: Synthetic current owner\n---\n')
        (self.root/'skills/catalog.json').write_text(json.dumps({'categories':['Setup'],'skills':[{'name':n,'category':'Setup'} for n in ['orbyn-setup',NEW]],'retired_skills':{OLD:NEW}}))
        for host in ['.agents','.claude']:
            link=self.root/host/'skills'/OLD;link.parent.mkdir(parents=True)
            link.symlink_to(os.path.relpath(self.root/'skills'/OLD,link.parent))
        cli=[sys.executable,str(self.root/'scripts/sync-agent-skills.py')]
        self.assertNotEqual(subprocess.run(cli+['--check'],capture_output=True).returncode,0)
        run=subprocess.run(cli+['--write'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(subprocess.run(cli+['--check'],capture_output=True).returncode,0)
        self.assertFalse((self.root/'.agents/skills'/OLD).is_symlink())
        foreign=self.root/'.claude/skills'/OLD;foreign.mkdir();(foreign/'SKILL.md').write_text('Retain')
        self.assertNotEqual(subprocess.run(cli+['--write'],capture_output=True).returncode,0)
        self.assertEqual((foreign/'SKILL.md').read_text(),'Retain')

    def test_bad_retirement_map_cannot_create_cycles_or_unknown_owners(self):
        for retired in [{OLD:'missing'},{NEW:NEW},['not-a-map']]:
            with self.subTest(retired=retired),self.assertRaises(ValueError):
                local.retirements({'skills':[{'name':NEW}],'retired_skills':retired})

    def test_foreign_replacement_after_preflight_is_preserved(self):
        self.old_links()
        pending = local.plan_retired_links(self.root,ROOT,{OLD:NEW},{NEW:ROOT/'skills'/NEW},['.agents','.claude'])
        changed = self.root/'.claude/skills'/OLD
        changed.unlink()
        foreign = self.root/'foreign-new-owner';foreign.mkdir()
        (foreign/'SKILL.md').write_text('New company work')
        changed.symlink_to(foreign)
        with self.assertRaisesRegex(ValueError,'changed after preflight'):
            local.remove_retired_links(pending)
        self.assertTrue((self.root/'.agents/skills'/OLD).is_symlink())
        self.assertEqual(changed.resolve(),foreign)
        self.assertEqual((foreign/'SKILL.md').read_text(),'New company work')

    def test_generator_keeps_retired_links_when_replacement_creation_fails(self):
        scripts = self.root/'scripts'; scripts.mkdir()
        shutil.copy2(ROOT/'scripts/sync-agent-skills.py', scripts/'sync-agent-skills.py')
        helper = self.root/'skills/orbyn-setup'; helper.mkdir(parents=True)
        shutil.copy2(ROOT/'scripts/discovery_links.py', scripts/'discovery_links.py')
        for name in ['orbyn-setup', NEW]:
            base = self.root/'skills'/name; base.mkdir(exist_ok=True)
            (base/'SKILL.md').write_text(f'---\nname: {name}\ndescription: Synthetic owner\n---\n')
        (self.root/'skills/catalog.json').write_text(json.dumps({
            'categories':['Setup'], 'skills':[{'name':n,'category':'Setup'} for n in ['orbyn-setup',NEW]],
            'retired_skills':{OLD:NEW}}))
        for host in ['.agents', '.claude']:
            link = self.root/host/'skills'/OLD; link.parent.mkdir(parents=True)
            link.symlink_to(os.path.relpath(self.root/'skills'/OLD, link.parent))
        cli = scripts/'sync-agent-skills.py'
        with mock.patch.object(sys, 'argv', [str(cli), '--write']), \
                mock.patch.object(Path, 'symlink_to', side_effect=OSError('Injected filesystem failure')):
            with self.assertRaisesRegex(OSError, 'Injected filesystem failure'):
                runpy.run_path(str(cli), run_name='__main__')
        for host in ['.agents', '.claude']:
            self.assertTrue((self.root/host/'skills'/OLD).is_symlink())
        self.assertFalse((self.root/'skills/README.md').exists())
        retry = subprocess.run([sys.executable, str(cli), '--write'], capture_output=True, text=True)
        self.assertEqual(retry.returncode, 0, retry.stderr)
        for host in ['.agents', '.claude']:
            self.assertTrue((self.root/host/'skills'/NEW/'SKILL.md').is_file())
            self.assertFalse((self.root/host/'skills'/OLD).is_symlink())
