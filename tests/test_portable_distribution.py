"""Real skills-only copy boundaries; no network, model or consumer setup effects."""
import json
from pathlib import Path
import tempfile
import unittest

from test_tools import ROOT, module, sync

contracts = module('portable_contracts', ROOT/'scripts/skill_contracts.py')
sources = module('portable_sources', ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py')


class PortableDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def copy_distribution(self):
        files = sync.manifest(ROOT)
        sync.copy_changes(ROOT, self.root, files)
        return files

    def test_entire_authored_export_works_without_library_policy(self):
        files = self.copy_distribution()
        for excluded in ('AGENTS.md', 'docs', 'tools', 'provenance.json', 'scripts'):
            self.assertFalse((self.root/excluded).exists())
        snapshots = sources.check(self.root)
        self.assertEqual(contracts.check_portable_links(self.root, files, snapshots), [])
        self.assertEqual(sync.inventory(self.root), files)

    def test_existing_but_unexported_policy_does_not_hide_dependency(self):
        skill = self.root/'skills/example/SKILL.md'
        skill.parent.mkdir(parents=True)
        policy = self.root/'docs/agents/model-policy.md'
        policy.parent.mkdir(parents=True)
        policy.write_text('# Host policy\n')
        skill.write_text('[Required policy](../../docs/agents/model-policy.md)\n')
        self.assertEqual(contracts.check_links(self.root, skill), [])
        errors = contracts.check_portable_links(self.root, ['skills/example/SKILL.md'])
        self.assertTrue(any('Unexported dependency' in e for e in errors), errors)

    def test_missing_transitive_method_is_detected_in_copied_tree(self):
        files = self.copy_distribution()
        (self.root/'skills/how/references/impact-map.md').unlink()
        errors = contracts.check_portable_links(self.root, files, sources.check(self.root))
        self.assertTrue(any('impact-map.md' in e for e in errors), errors)

    def test_reference_style_dependency_and_titled_fragment_are_checked(self):
        skill = self.root/'skills/example/SKILL.md'
        skill.parent.mkdir(parents=True)
        guide = skill.parent/'guide with spaces.md'
        guide.write_text('# Known\n')
        skill.write_text('[Local](<guide with spaces.md#known> "Title")\n'
                         '[Missing policy][policy]\n\n'
                         '[policy]: ../../AGENTS.md "Consumer policy"\n'
                         '```md\n[Example](not-a-dependency.md)\n```\n')
        files = [str(p.relative_to(self.root)) for p in (skill, guide)]
        errors = contracts.check_portable_links(self.root, files)
        self.assertTrue(any('AGENTS.md' in e for e in errors), errors)
        self.assertFalse(any('guide with spaces.md' in e or 'not-a-dependency' in e
                             for e in errors), errors)

    def test_snapshot_exemption_requires_unchanged_bytes(self):
        self.copy_distribution()
        source = next((self.root/'skills').glob('*/references/upstream/*/SOURCE.md'))
        source.write_text(source.read_text() + '\nChanged imported instructions.\n')
        with self.assertRaisesRegex(ValueError, 'Changed/missing offline source bytes'):
            sources.check(self.root)

    def test_principle_notices_and_methods_survive_export_under_active_owners(self):
        files = self.copy_distribution()
        catalog = json.loads((self.root/'skills/catalog.json').read_text())
        provenance = json.loads((ROOT/'provenance.json').read_text())['skills']
        retired = {old: owner for old, owner in catalog['retired_skills'].items()
                   if old.startswith('principle-')}
        self.assertEqual(len(retired), 20)
        for old, owner in retired.items():
            with self.subTest(old=old):
                relative = f'skills/{owner}/references/principles/{old.removeprefix("principle-")}.md'
                self.assertIn(relative, files)
                self.assertFalse((self.root/'skills'/old).exists())
                self.assertEqual(contracts.check_incorporated_material(
                    self.root, owner, provenance[owner]), [])
                method = (self.root/relative).read_text()
                self.assertIn('## Decision in practice', method)
                self.assertIn('Concrete check:', method)
                self.assertIn('[original MIT notice](LICENSE.txt)', method)


if __name__ == '__main__':
    unittest.main()
