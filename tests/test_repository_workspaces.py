"""Independent nested Git roots and local-only setup, using synthetic repositories."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_tools import ROOT, module, sync

contracts = module('workspace_contracts', ROOT/'scripts/skill_contracts.py')
workspace = module('nested_workspace', ROOT/'skills/orbyn-setup/scripts/workspace.py')


class RepositoryWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()/'library'
        self.root.mkdir()
        self.git(self.root, 'init', '-b', 'main')
        self.git(self.root, 'config', 'core.excludesFile', '/dev/null')
        (self.root/'.gitignore').write_bytes((ROOT/'.gitignore').read_bytes())
        (self.root/'AGENTS.md').write_text('Library policy')
        (self.root/'skills').mkdir()
        (self.root/'skills/catalog.json').write_bytes((ROOT/'skills/catalog.json').read_bytes())
        self.git(self.root, 'add', '.gitignore', 'AGENTS.md', 'skills/catalog.json')
        self.commit(self.root)

    def git(self, root, *args):
        return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(root),*args], text=True,
                                       stderr=subprocess.PIPE).strip()

    def commit(self, root):
        self.git(root, '-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                 '-c','core.hooksPath=/dev/null','commit','-m','Synthetic baseline')

    def target(self):
        root = self.root/'repo/widget';root.mkdir(parents=True)
        self.git(root, 'init', '-b', 'main')
        files = {'AGENT.md':'Target-specific guide pointers', 'AGENTS.md':'Target instructions', 'CLAUDE.md':'Target Claude rules',
                 'codex.md':'Target agent defaults', '.cursorrules':'Target Cursor policy',
                 '.cursor/rules/style.mdc':'Target nested rule',
                 '.claude/settings.json':'{"target":"retained"}',
                 '.agents/skills/upstream-check/SKILL.md':'Upstream-owned skill',
                 '.claude/skills/upstream-check/SKILL.md':'Upstream Claude skill'}
        for name,text in files.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        self.git(root, 'add', '.');self.commit(root)
        return root, {p:(root/p).read_bytes() for p in files}

    def test_setup_preserves_all_target_rules_skills_and_git_excludes(self):
        target, original = self.target()
        exclude = target/self.git(target,'rev-parse','--git-path','info/exclude')
        initial=exclude.read_bytes()
        before=self.git(target,'status','--porcelain')
        result=workspace.prepare(self.root)
        report=workspace.check(self.root,target)
        self.assertFalse(result['target_files_changed'])
        self.assertEqual(report['host_discovery'],'not_observed')
        self.assertIn('AGENTS.md',report['target_instructions'])
        self.assertIn('AGENT.md',report['target_instructions'])
        for path,data in original.items():self.assertEqual((target/path).read_bytes(),data)
        self.assertEqual(exclude.read_bytes(),initial)
        self.assertEqual(self.git(target,'status','--porcelain'),before)
        self.assertEqual(self.git(self.root,'status','--porcelain'),'')
        self.assertFalse((target/'skills').exists())
        self.assertFalse((target/'.agents/skills/language-best-practices').exists())

    def test_worktree_retains_own_root_dirty_changes_and_common_metadata(self):
        target,_=self.target();tree=self.root/'repo/widget-wt/bug-fix'
        self.git(target,'worktree','add','-b','fix/fixture',str(tree),'HEAD')
        (tree/'AGENTS.md').write_text('Unfinished target change')
        report=workspace.check(self.root,tree)
        self.assertEqual(report['target'],str(tree))
        self.assertIn('AGENTS.md',report['target_status'])
        self.assertEqual((tree/'AGENTS.md').read_text(),'Unfinished target change')
        self.assertEqual((target/'AGENTS.md').read_text(),'Target instructions')
        self.assertEqual(self.git(self.root,'status','--porcelain'),'')

    def test_same_name_target_skills_are_reported_and_preserved(self):
        target,original=self.target()
        foreign=target/'.agents/skills/how';foreign.mkdir()
        (foreign/'SKILL.md').write_text('Target owns how')
        report=workspace.check(self.root,target)
        self.assertIn('.agents/skills/how',report['same_name_target_skills'])
        self.assertEqual((foreign/'SKILL.md').read_text(),'Target owns how')
        self.assertFalse((target/'.claude/skills/how').exists())
        for path,data in original.items():self.assertEqual((target/path).read_bytes(),data)

    def test_external_and_ancestor_targets_are_refused_without_changes(self):
        target,_=self.target()
        outside=self.root.parent/'outside';outside.mkdir()
        with self.assertRaisesRegex(ValueError,'must be nested'):
            workspace.check(self.root,outside)
        with self.assertRaisesRegex(ValueError,'Git root'):
            workspace.check(self.root,target/'.agents')
        with self.assertRaisesRegex(ValueError,'must be nested'):
            workspace.check(self.root,self.root/'repo')
        self.assertEqual(list(outside.iterdir()),[])

    def test_external_linked_worktree_is_not_a_migrated_primary_clone(self):
        external=self.root.parent/'external';external.mkdir()
        self.git(external,'init','-b','main')
        (external/'README.md').write_text('Source outside library')
        self.git(external,'add','.');self.commit(external)
        tree=self.root/'repo/external-wt/fix'
        self.git(external,'worktree','add','-b','fix/fixture',str(tree),'HEAD')
        with self.assertRaisesRegex(ValueError,'metadata belongs outside'):
            workspace.check(self.root,tree)
        self.assertTrue((tree/'README.md').is_file())

    def test_symlink_target_refused_without_following_or_modifying_it(self):
        target,_=self.target();alias=self.root/'repo/alias'
        alias.symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Symlinked'):
            workspace.check(self.root,alias)
        self.assertTrue(alias.is_symlink())

    def test_prepare_is_idempotent_and_never_executes_target_hooks(self):
        target,_=self.target()
        marker=self.root/'hook-ran'
        hook=target/'.git/hooks/post-checkout'
        hook.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\n');hook.chmod(0o755)
        workspace.prepare(self.root);workspace.prepare(self.root)
        workspace.check(self.root,target)
        self.assertFalse(marker.exists())

    def test_cli_check_and_legacy_install_flags_leave_target_unchanged(self):
        target,original=self.target()
        cli=[sys.executable,str(ROOT/'skills/orbyn-setup/scripts/workspace.py')]
        result=subprocess.run(cli+['check','--library',str(self.root),'--target',str(target)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(json.loads(result.stdout)['target_files_changed'])
        result=subprocess.run(cli+['prepare','--library',str(self.root),'--project',str(target),'--host','all'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        for name,data in original.items():self.assertEqual((target/name).read_bytes(),data)

    def test_forced_nested_gitlink_is_rejected(self):
        self.target();self.git(self.root,'add','-f','repo/widget')
        self.assertTrue(self.git(self.root,'ls-files','--stage','repo').startswith('160000'))
        self.assertIn('repo/widget',' '.join(contracts.check_local_workspaces(self.root)))

    def test_forced_reference_files_are_rejected(self):
        for folder in ['openSrc','orbyn-references']:
            path=self.root/folder/'reference.txt';path.parent.mkdir();path.write_text('Private reference')
            self.git(self.root,'add','-f',str(path.relative_to(self.root)))
        errors=' '.join(contracts.check_local_workspaces(self.root))
        self.assertIn('openSrc/reference.txt',errors)
        self.assertIn('orbyn-references/reference.txt',errors)

    def test_missing_ignore_and_symlink_workspace_are_refused(self):
        (self.root/'.gitignore').write_text('')
        self.assertIn('must be Git-ignored',' '.join(contracts.check_local_workspaces(self.root)))
        (self.root/'.gitignore').write_bytes((ROOT/'.gitignore').read_bytes())
        outside=self.root.parent/'outside';outside.mkdir()
        marker=outside/'private.txt';marker.write_text('Preserve')
        (self.root/'repo').symlink_to(outside,target_is_directory=True)
        self.assertIn('must not be a symlink',' '.join(contracts.check_local_workspaces(self.root)))
        self.assertEqual(marker.read_text(),'Preserve')

    def test_managed_inventory_never_reads_nested_target_assets(self):
        target,_=self.target()
        private=target/'skills/private/SKILL.md';private.parent.mkdir(parents=True);private.write_text('Target-only content')
        base=self.root/'skills/example';base.mkdir(parents=True)
        (base/'SKILL.md').write_text('Example');(base/'LICENSE').write_text('MIT fixture')
        (self.root/'skills/catalog.json').write_text(json.dumps({'skills':[{'name':'example'}]}))
        (self.root/'skills/README.md').write_text('Fixture index')
        self.assertEqual(len(sync.inventory(self.root)),4)
        with self.assertRaisesRegex(ValueError,'outside skills allowlist'):
            sync.safe_path(self.root,'repo/widget/skills/private/SKILL.md')
        self.assertEqual(private.read_text(),'Target-only content')
