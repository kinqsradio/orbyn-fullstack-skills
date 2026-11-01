"""Regression checks for discovered source aliases and broken handoffs."""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, module

contracts = module('skill_contracts', ROOT/'scripts/skill_contracts.py')


class SkillContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.skill = self.root/'skills/example/SKILL.md'
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text('# Example\n\n## Actual step\n\n## Actual step\n')

    def test_entrypoint_limits_reject_regrowth_and_maintainer_notes(self):
        ok = '---\nname: example\ndescription: "Do one thing."\n---\n\n# Example\n'
        self.assertEqual(contracts.check_entrypoint('example', ok), [])
        long_body = ok + 'word ' * (contracts.MAX_ENTRYPOINT_WORDS + 1)
        self.assertIn('exceeds', contracts.check_entrypoint('example', long_body)[0])
        long_text = ok.replace('Do one thing.', 'x' * (contracts.MAX_DESCRIPTION_CHARS + 1))
        self.assertIn('description', contracts.check_entrypoint('example', long_text)[0])
        folded = ok.replace('"Do one thing."', '>-')
        self.assertIn('one literal line', contracts.check_entrypoint('example', folded)[0])
        continued = ok.replace('"Do one thing."\n', 'Short\n  ' + 'x' * 400 + '\n')
        self.assertIn('one literal line', contracts.check_entrypoint('example', continued)[0])
        self.assertIn('one literal line', contracts.check_entrypoint('example', ok.replace('"Do one thing."', '  '))[0])
        self.assertIn('closed frontmatter', contracts.check_entrypoint('example', ok.replace('---\n\n#', '--- \n\n#'))[0])
        self.assertIn('closed frontmatter', contracts.check_entrypoint('example', '---\nname: example\n' + 'word ' * 5000)[0])
        self.assertIn('provenance', contracts.check_entrypoint('example', ok + 'Historical source notices remain in provenance.\n')[0])
        wrapped = ok + 'It is ours; historical source notices\nremain in provenance.\n'
        self.assertIn('provenance', contracts.check_entrypoint('example', wrapped)[0])

    def test_case_coverage_requires_repeat_positives_and_a_holdout(self):
        case = lambda split, *more: {'expected_skills': ['example', *more], 'split': split}
        development = [case('development')] * 2
        self.assertEqual(contracts.check_case_coverage({'example'}, [*development, case('holdout')]), [])
        self.assertIn('holdout', contracts.check_case_coverage({'example'}, development)[0])
        self.assertIn('positive', contracts.check_case_coverage({'example'}, [case('development'), case('holdout')])[0])
        doubled = [case('development', 'example'), case('holdout')]
        self.assertIn('positive', contracts.check_case_coverage({'example'}, doubled)[0])
        shared = [*development, case('holdout', 'other')]
        self.assertIn('holdout', contracts.check_case_coverage({'example'}, shared)[0])

    def test_nested_upstream_entrypoint_is_rejected_even_with_valid_canonical_skill(self):
        source = self.skill.parent/'references/upstream/vendor/SKILL.md'
        source.parent.mkdir(parents=True)
        source.write_text('---\nname: foreign-alias\n---\nUse a missing upstream skill.')
        self.assertIn('Unexpected active', '\n'.join(contracts.check_discovery(self.root, {'example'}, [])))
        source.rename(source.with_name('SOURCE.md'))
        self.assertEqual(contracts.check_discovery(self.root, {'example'}, []), [])

    def test_missing_related_owner_is_rejected(self):
        self.assertIn('unknown related skill ghost', '\n'.join(contracts.check_discovery(
            self.root, {'example'}, [{'name':'example','related':['ghost']} ])))

    def test_links_validate_fragments_duplicates_and_escaping_paths(self):
        guide = self.root/'guide.md'
        guide.write_text('[Good](skills/example/SKILL.md#actual-step-1)\n[Wrong](skills/example/SKILL.md#missing)\n[Escape](../secret.md)\n[Remote](https://example.com/#absent)\n')
        errors = contracts.check_links(self.root, guide)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any('fragment' in e for e in errors))
        self.assertTrue(any('escaping' in e for e in errors))



    def test_source_checker_rejects_discoverable_filename_even_with_valid_hash(self):
        import shutil
        base = self.root/'skills/social-content/references/upstream/vendor'
        shutil.copytree(ROOT/'skills/social-content/references/upstream/marketingskills-social', base)
        manifest = base/'snapshot.json'
        data = json.loads(manifest.read_text())
        data['files']['SKILL.md'] = data['files'].pop('SOURCE.md')
        (base/'SOURCE.md').rename(base/'SKILL.md')
        manifest.write_text(json.dumps(data))
        checker = module('source_discovery_guard', ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py')
        with self.assertRaisesRegex(ValueError, 'active SKILL.md'):
            checker.check(self.root)

    def test_audit_must_cover_current_catalog_once(self):
        docs = self.root/'docs'
        docs.mkdir()
        audit = docs/'skill-audit.md'
        row = '| [example](../skills/example/SKILL.md) | Reviewed | Input → result | Limit |\n'
        audit.write_text(row)
        self.assertEqual(contracts.check_audit(self.root, {'example'}), [])
        audit.write_text(row.replace(') |', ')       |'))
        self.assertEqual(contracts.check_audit(self.root, {'example'}), [])
        self.assertTrue(contracts.check_audit(self.root, {'example','new-skill'}))
        audit.write_text(row+row)
        self.assertTrue(contracts.check_audit(self.root, {'example'}))

    def test_release_handoff_has_local_reference_closure(self):
        import re
        import shutil
        consumer = self.root/'consumer'
        shutil.copytree(ROOT/'skills', consumer/'skills')
        self.assertFalse((consumer/'docs/synchronization.md').exists())
        for name in ['orbyn-skill-creator','orbyn-upstream-review']:
            entry = consumer/'skills'/name/'SKILL.md'
            links = re.findall(r'\]\(([^)]+release-handoff\.md)\)', entry.read_text())
            self.assertTrue(links, name)
            for target in links:
                method = (entry.parent/target).resolve()
                self.assertTrue(method.is_relative_to(consumer))
                self.assertTrue(method.is_file())
                self.assertEqual(contracts.check_links(consumer, method), [])

    def test_moved_material_requires_its_own_portable_license(self):
        source = self.skill.parent/'references/moved.md'
        source.parent.mkdir(); source.write_text('Moved maintained guidance')
        notice = source.with_name('moved-LICENSE.txt')
        original_notice = 'Copyright Original Author\nMIT\nPermission and conditions retained.\n'
        record = {'incorporated_material':[{'source':'https://example.com/source',
            'revision':'a'*40, 'copyright':'Copyright Original Author','license':'MIT',
            'local_path':str(source.relative_to(self.root)), 'license_file':str(notice.relative_to(self.root)),
            'license_sha256':hashlib.sha256(original_notice.encode()).hexdigest()}]}
        self.assertTrue(contracts.check_incorporated_material(self.root,'example',record))
        notice.write_text(original_notice)
        self.assertEqual(contracts.check_incorporated_material(self.root,'example',record),[])
        notice.write_text('Copyright Original Author\nMIT')
        self.assertIn('differs from pinned notice',' '.join(contracts.check_incorporated_material(self.root,'example',record)))
        notice.write_text('Removed notice')
        self.assertIn('copyright missing',' '.join(contracts.check_incorporated_material(self.root,'example',record)))
        notice.write_text(original_notice)
        del record['incorporated_material'][0]['revision']
        self.assertIn('incomplete',' '.join(contracts.check_incorporated_material(self.root,'example',record)))
