"""Skills-only contribution resources and synthetic evaluation contracts.

No target code, hosted PR, model or network request is executed here.
"""
import json
from pathlib import Path
import re
import socket
import tempfile
import unittest
from unittest import mock
from urllib.parse import unquote

from test_tools import ROOT, module, sync

contracts = module('contribution_links', ROOT/'scripts/skill_contracts.py')
evaluator = module('contribution_evaluator', ROOT/'skills/orbyn-skill-creator/scripts/evaluate.py')

# Required operational documents for the public contribution milestone, not
# consumer-owned policy. The real copy boundary must include every one.
SUPPORT = {
    'skills/orbyn-workflow/playbooks/contribution-intake.md',
    'skills/orbyn-workflow/playbooks/pr-iteration.md',
    'skills/orbyn-workflow/playbooks/bug-fix.md',
    'skills/orbyn-workflow/playbooks/opening-a-pr.md',
    'skills/orbyn-workflow/references/contribution-examples.md',
    'skills/orbyn-workflow/references/contribution-sources.md',
    'skills/how/references/reproduction.md',
}
ENTRYPOINTS = {'skills/orbyn-workflow/SKILL.md', 'skills/how/SKILL.md', 'skills/tdd/SKILL.md'}


def support_errors(root):
    """Check support reachability and local links without root policy documents."""
    errors = []
    seen = set()
    pending = list(ENTRYPOINTS)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        path = root/name
        if not path.is_file():
            errors.append(f'Missing contribution resource: {name}')
            continue
        if name in SUPPORT:
            errors.extend(contracts.check_links(root, path))
        body = re.sub(r'```.*?```|~~~.*?~~~', '', path.read_text(), flags=re.S)
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body):
            filename = unquote(target.strip('<>').partition('#')[0])
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', filename):
                continue
            linked = (path.parent/filename).resolve()
            if linked.is_relative_to(root):
                relative = linked.relative_to(root).as_posix()
                if relative in SUPPORT | ENTRYPOINTS:
                    pending.append(relative)
    errors.extend(f'Unreachable contribution resource: {name}' for name in sorted(SUPPORT - seen))
    return errors


class ContributionDistributionTests(unittest.TestCase):

    def test_missing_shipped_resource_is_detected_after_real_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory).resolve()
            sync.copy_changes(ROOT, consumer, sync.manifest(ROOT))
            self.assertEqual(support_errors(consumer), [])
            missing = consumer/'skills/how/references/reproduction.md'
            missing.unlink()
            errors = support_errors(consumer)
            self.assertTrue(any('reproduction.md' in error for error in errors), errors)

    def test_disconnected_resource_is_not_mistaken_for_installed_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory).resolve()
            sync.copy_changes(ROOT, consumer, sync.manifest(ROOT))
            examples = 'references/contribution-examples.md'
            for name in SUPPORT | ENTRYPOINTS:
                path = consumer/name
                # Remove all incoming links, while leaving the actual asset present.
                text = path.read_text()
                text = re.sub(r'\[[^\]]*\]\([^)]*' + re.escape(examples) + r'\)', 'unlinked example', text)
                path.write_text(text)
            self.assertTrue((consumer/'skills/orbyn-workflow'/examples).is_file())
            self.assertIn('Unreachable contribution resource: skills/orbyn-workflow/' + examples,
                          support_errors(consumer))


class ContributionEvaluationTests(unittest.TestCase):
    def test_prepared_development_cases_remain_unverified_and_hide_rubrics(self):
        cases = [c for c in evaluator.suite()[0]['cases'] if c['id'].startswith('contribution-')]
        self.assertTrue(cases)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            protocol = folder/'input.json'
            protocol.write_text('{"evidence": "synthetic tooling fixture; no agent run"}\n')
            run = evaluator.prepare(folder/'trial', 'a'*40, 'fixture host', 'fixture model',
                                    'fixture', case_ids=[c['id'] for c in cases], protocol=protocol)
            tasks = json.loads((folder/'trial/tasks.json').read_text())
            self.assertTrue(all(set(task) == {'case_id', 'trial', 'prompt'} for task in tasks))
            self.assertTrue(all(result['status'] == 'not_run' for result in run['results']))
            report = evaluator.grade(folder/'trial/run.json')
            self.assertEqual(report['counts'], {'pass': 0, 'fail': 0, 'unverified': len(cases)})

    def test_pr_trial_needs_all_rubric_evidence_and_respects_effect_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            protocol = folder/'protocol.json'
            protocol.write_text('{"fixture": true}')
            case_id = 'contribution-pr-effect-boundaries'
            run = evaluator.prepare(folder/'trial', 'a'*40, 'fixture host', 'fixture model',
                                    'fixture', case_ids=[case_id], protocol=protocol)
            record = run['results'][0]
            evidence = 'SYNTHETIC validator fixture. Local scope preserved; replies unperformed.'
            (folder/'trial/transcript.txt').write_text(evidence)
            (folder/'trial/answer.md').write_text(evidence)
            record.update(status='completed', selected_skills=['orbyn-workflow'],
                          transcript='transcript.txt', artifacts=['answer.md'],
                          reviewer='Synthetic fixture observer',
                          rubric={'progress': {'status': 'pass', 'evidence': evidence}})
            path = folder/'trial/run.json'
            path.write_text(json.dumps(run))
            self.assertEqual(evaluator.grade(path)['counts']['unverified'], 1)
            record['rubric']['effects'] = {'status': 'pass', 'evidence': evidence}
            record['actions'] = ['message']
            path.write_text(json.dumps(run))
            report = evaluator.grade(path)
            self.assertEqual(report['counts']['fail'], 1)
            self.assertEqual(report['results'][0]['forbidden_actions'], ['message'])


if __name__ == '__main__':
    unittest.main()
