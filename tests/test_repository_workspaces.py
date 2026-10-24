"""Independent nested Git roots and local-only setup, using synthetic repositories."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_tools import ROOT, installer, module, sync

contracts = module('workspace_contracts', ROOT/'scripts/skill_contracts.py')


class RepositoryWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()/'library'
        self.root.mkdir()
        self.git(self.root, 'init', '-b', 'main')
        self.git(self.root, 'config', 'core.excludesFile', '/dev/null')
        (self.root/'.gitignore').write_bytes((ROOT/'.gitignore').read_bytes())
        self.git(self.root, 'add', '.gitignore')
        self.commit(self.root)

    def git(self, root, *args):
        return subprocess.check_output(['git','-C',str(root),*args], text=True,
                                       stderr=subprocess.PIPE).strip()

    def commit(self, root):
        self.git(root, '-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                 '-c','core.hooksPath=/dev/null','commit','-m','Synthetic baseline')

    def target(self):
        root = self.root/'repo/widget';root.mkdir(parents=True)
        self.git(root, 'init', '-b', 'main')
        files = {'AGENTS.md':'Target instructions', 'CLAUDE.md':'Target Claude rules',
                 'codex.md':'Target agent defaults', '.cursorrules':'Target Cursor policy',
                 '.cursor/rules/style.mdc':'Target nested rule',
                 '.claude/settings.json':'{"target":"retained"}',
                 '.agents/skills/upstream-check/SKILL.md':'Upstream-owned skill',
                 '.claude/skills/upstream-check/SKILL.md':'Upstream Claude skill'}
        for name,text in files.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        self.git(root, 'add', '.');self.commit(root)
        return root, {p:(root/p).read_bytes() for p in files}

    def test_local_install_preserves_target_rules_and_keeps_its_pr_clean(self):
        target, original = self.target()
        exclude = target/self.git(target,'rev-parse','--git-path','info/exclude')
        initial=exclude.read_text();exclude.write_text(initial+'\n/cache/\n')
        initial=exclude.read_text()
        installer.install(target,'both',['language-best-practices'])
        additions='\n/.agents/skills/language-best-practices\n/.claude/skills/language-best-practices\n'
        exclude.write_text(exclude.read_text()+additions)
        self.assertTrue(exclude.read_text().startswith(initial))
        for path,data in original.items():self.assertEqual((target/path).read_bytes(),data)
        self.assertEqual(self.git(target,'status','--porcelain'),'')
        self.assertEqual(self.git(self.root,'status','--porcelain'),'')
        self.assertEqual(contracts.check_local_workspaces(self.root),[])
        for host in ['.agents','.claude']:
            self.assertTrue((target/host/'skills/language-best-practices/references/typescript.md').is_file())

    def test_worktree_resolves_target_root_and_shared_local_exclusion(self):
        target,_=self.target();worktree=self.root/'repo/widget-wt/bug-fix'
        self.git(target,'worktree','add','-b','fix/fixture',str(worktree),'HEAD')
        self.assertEqual(Path(self.git(worktree,'rev-parse','--show-toplevel')),worktree)
        def exclude(root):
            return (root/self.git(root,'rev-parse','--git-path','info/exclude')).resolve()
        self.assertEqual(exclude(target),exclude(worktree))
        self.assertEqual((worktree/'AGENTS.md').read_bytes(),(target/'AGENTS.md').read_bytes())
        installer.install(worktree,'both',['language-best-practices'])
        self.assertFalse((target/'.agents/skills/language-best-practices').exists())
        self.assertTrue((worktree/'.claude/skills/language-best-practices/SKILL.md').is_file())
        local_exclude=exclude(worktree)
        local_exclude.write_text(local_exclude.read_text()+'\n/.agents/skills/language-best-practices\n/.claude/skills/language-best-practices\n')
        (worktree/'AGENTS.md').write_text('Unfinished target change')
        self.assertIn('AGENTS.md',self.git(worktree,'status','--short'))
        self.assertNotIn('language-best-practices',self.git(worktree,'status','--short'))
        self.assertEqual(self.git(self.root,'status','--porcelain'),'')
        self.assertEqual(contracts.check_local_workspaces(self.root),[])

    def test_foreign_name_collision_is_refused_without_mutation(self):
        target, original=self.target()
        foreign=target/'.agents/skills/how';foreign.mkdir()
        (foreign/'SKILL.md').write_text('Target owns how')
        with self.assertRaisesRegex(ValueError,'Conflicting discovery'):
            installer.install(target,'both',['how'])
        self.assertEqual((foreign/'SKILL.md').read_text(),'Target owns how')
        self.assertFalse((target/'.claude/skills/how').exists())
        for path,data in original.items():self.assertEqual((target/path).read_bytes(),data)

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
