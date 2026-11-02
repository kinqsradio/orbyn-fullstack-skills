#!/usr/bin/env python3
"""Security workflow: threat model, audit, remediation, verification.

Checks the two entrypoints, the bundled threat-model references, their source records and the
record checker. Every rule is also run against a planted fault so the test fails when the rule
stops working. No network, no model calls and nothing from the pinned upstream is executed.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from skill_contracts import local_link_targets  # noqa: E402

AUDIT = ROOT/'skills/orbyn-security-audit'
REMEDIATION = ROOT/'skills/orbyn-security-remediation'
REFS = AUDIT/'references'
BUNDLE = REFS/'threat-model'
RECORDS = REFS/'upstream/grim-prompter'
AUDIT_RECORDS = REFS/'upstream/audit-records'
CONVERTER = AUDIT/'scripts/threats_to_ledger.py'
NODE = shutil.which('node')
REVISION = '14d7292ad60434f5bf96f1792412f07e1b7531ed'
PINNED = ROOT/'orbyn-references/grim-prompter'/REVISION
ARCHITECTURES = ['web', 'api', 'multi-tenant-saas', 'agentic-ai', 'rag', 'cicd-supply-chain',
                 'cli-developer-tools', 'desktop', 'mobile', 'serverless', 'microservices', 'data-platform']
HELPERS = ['architecture-selector', 'method-selector', 'evidence-guide', 'model-challenger',
           'change-reviewer', 'tool-credential-boundaries', 'artifact-contract', 'method-notes']

# Advice that belongs to the upstream host, not to this library.
INSTALL_ADVICE = re.compile(
    r'git clone|\bln -s\b|~/\.(?:claude|agents|codex)|GRIM_PROMPTER|LIBRARY_ROOT|(?:^|[\s`(])/threat-model\b'
    r'|\$threat-model|\b(?:npm|pnpm|yarn|pip3?|brew|apt(?:-get)?)\s+(?:i|install|add)\b|symlink', re.I | re.M)
# A run folder at a project root, instead of the ignored output folder.
UNIGNORED_RUN_FOLDER = re.compile(r'(?<![\w/-])threat-model/\d{4}|`threat-model/`|PROJECT_ROOT/threat-model')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split(text):
    return re.fullmatch(r'---\n(.*?\n)---\n(.*)', text, re.S).groups()


def description(text):
    return re.search(r'^description: "(.*)"$', split(text)[0], re.M).group(1)


def load_checker():
    spec = importlib.util.spec_from_file_location('check_threat_model', AUDIT/'scripts/check_threat_model.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def entrypoint_faults(audit, remediation):
    """Faults in the two entrypoint texts; an empty list means they meet the workflow contract."""
    faults = []
    for name, text, neighbours in (('audit', audit, ('orbyn-security-remediation', 'architect')),
                                   ('remediation', remediation, ('orbyn-security-audit',))):
        front, body = split(text)
        summary = description(text)
        if len(summary) > 300:
            faults.append(f'{name}: description over 300 characters')
        for neighbour in neighbours:
            if neighbour not in summary:
                faults.append(f'{name}: description must name {neighbour}')
        if len(body.split()) > 1200:
            faults.append(f'{name}: entrypoint over 1,200 words')
        if 'lead tier' not in body or 'never the scout tier' not in body:
            faults.append(f'{name}: security work must run on the lead tier, never the scout tier')
        if '### Worked failure' not in body:
            faults.append(f'{name}: missing worked failure')
        if INSTALL_ADVICE.search(text):
            faults.append(f'{name}: install or global-link advice')
        if re.search(r'Codex Security', text):
            faults.append(f'{name}: keep scanner references general')
    order = [audit.find(marker) for marker in ('1. **Threat model**', '2. **Audit**', '3. **Remediation**', '4. **Verification**')]
    if -1 in order or order != sorted(order):
        faults.append('audit: the four workflow stages must be listed in order')
    if 'Scouts may not touch security work' not in audit or 'scout may locate' in audit.lower():
        faults.append('audit: scouts may not touch security work')
    for token in ('tm:T1', '`closed`', '`still open`', '`regression`', 'threat-model.json', 'orbyn-security-remediation'):
        if token not in audit:
            faults.append(f'audit: missing handoff term {token}')
    for token in ('stage three', 'stage four', '`patched`', 'tm:T1', 'design_hypothesis', 'orbyn-security-audit',
                  'You do not grade your own fix', '`security_engineer` role at lead tier',
                  'fresh `security_verifier` at lead tier'):
        if token not in remediation:
            faults.append(f'remediation: missing handoff term {token}')
    for phrase in ('read-only', 'No scan or test against a live system', 'no exploitation',
                   'no use of credentials', 'no publication', 'never committed, uploaded or quoted'):
        if phrase not in audit:
            faults.append(f'audit: boundary statement missing: {phrase}')
    if 'output/threat-model/' not in audit or UNIGNORED_RUN_FOLDER.search(audit):
        faults.append('audit: artifacts must default to the ignored output/threat-model/ folder')
    return faults


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.audit = (AUDIT/'SKILL.md').read_text()
        self.remediation = (REMEDIATION/'SKILL.md').read_text()

    def test_entrypoints_meet_the_workflow_contract(self):
        self.assertEqual(entrypoint_faults(self.audit, self.remediation), [])

    def test_each_rule_fails_on_a_planted_fault(self):
        plants = {
            'tier': (self.audit.replace('lead tier', 'default tier'), self.remediation),
            'scout': (self.audit, self.remediation.replace('never the scout tier', 'never the slow tier')),
            'order': (self.audit.replace('2. **Audit**', '5. **Audit**').replace('1. **Threat model**', '6. **Threat model**'), self.remediation),
            'handoff': (self.audit.replace('tm:T1', 'id'), self.remediation),
            'back': (self.audit, self.remediation.replace('You do not grade your own fix', 'Grade your fix')),
            'install': (self.audit + '\nRun `git clone` and `ln -s` the folder.\n', self.remediation),
            'host command': (self.audit, self.remediation + '\nAsk with `/threat-model quick api`.\n'),
            'scanner': (self.audit, self.remediation.replace('hosted security scan', 'Codex Security scan')),
            'read-only': (self.audit.replace('read-only', 'careful'), self.remediation),
            'live': (self.audit.replace('No scan or test against a live system', 'Scan quickly'), self.remediation),
            'publication': (self.audit.replace('no publication', 'publish freely'), self.remediation),
            'folder': (self.audit.replace('output/threat-model/<date>', 'threat-model/2026-11-02'), self.remediation),
            'words': (self.audit + ' word' * 1300, self.remediation),
            'description': (self.audit.replace('Use orbyn-security-remediation to fix saved findings, architect for non-security design.', 'x' * 300), self.remediation),
            'neighbour': (self.audit, self.remediation.replace('Use orbyn-security-audit to find new ones.', '')),
            'failure': (self.audit.replace('### Worked failure', '### Example'), self.remediation),
            'scout locates': (self.audit.replace('Scouts may not touch security work', 'A scout may locate files'), self.remediation),
            'engineer tier': (self.audit, self.remediation.replace('`security_engineer` role at lead tier', 'assigned engineer')),
            'verifier tier': (self.audit, self.remediation.replace('fresh `security_verifier` at lead tier', 'reviewer')),
        }
        for label, (audit, remediation) in plants.items():
            with self.subTest(label):
                self.assertNotEqual(entrypoint_faults(audit, remediation), [], label)

    def test_threat_model_mode_stays_local_read_only_and_unpublished(self):
        method = (REFS/'threat-model.md').read_text()
        for phrase in ('Run nothing the target provides', 'unless the person authorizes that specific action',
                       'output/threat-model/', 'git check-ignore -q', 'Do not commit, upload, post, attach or quote it',
                       'Publication is a separate decision', 'Never overwrite another run'):
            self.assertIn(phrase, method)
        self.assertIsNone(UNIGNORED_RUN_FOLDER.search(method))
        self.assertIsNone(INSTALL_ADVICE.search(method))

    def test_default_run_folder_is_really_ignored(self):
        if not shutil.which('git'):
            self.skipTest('git is not available')
        probe = 'output/threat-model/2026-01-01-quick-probe/threat-model.json'
        ignored = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--no-index', probe])
        self.assertEqual(ignored.returncode, 0, 'the default run folder must be ignored by Git')
        exposed = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--no-index', 'threat-model/x/threat-model.json'])
        self.assertEqual(exposed.returncode, 1, 'a root-level threat-model folder must not be treated as ignored')


class BundleTests(unittest.TestCase):
    def documents(self):
        return [AUDIT/'SKILL.md', REMEDIATION/'SKILL.md', REFS/'threat-model.md', *sorted(BUNDLE.rglob('*.md'))]

    def test_expected_prompts_are_bundled_and_nothing_else(self):
        found = {path.relative_to(BUNDLE).as_posix() for path in BUNDLE.rglob('*') if path.is_file()}
        expected = {f'{name}.md' for name in HELPERS} | {f'architectures/{name}.md' for name in ARCHITECTURES}
        self.assertEqual(found, expected)
        for excluded in ('deep', 'methods', 'quick', 'helpers', 'reference'):
            self.assertFalse((AUDIT/excluded).exists() or (REFS/excluded).exists() or (BUNDLE/excluded).exists(), excluded)

    def test_every_link_resolves_and_every_prompt_is_reachable(self):
        reached, queue = set(), [AUDIT/'SKILL.md']
        while queue:
            page = queue.pop()
            if page in reached:
                continue
            reached.add(page)
            for target in local_link_targets(page.read_text()):
                filename = target.partition('#')[0]
                if not filename:
                    continue
                resolved = (page.parent/filename).resolve()
                self.assertTrue(resolved.is_file(), f'{page.relative_to(ROOT)} -> {target}')
                if resolved.suffix == '.md' and resolved.is_relative_to(AUDIT):
                    queue.append(resolved)
        for path in BUNDLE.rglob('*.md'):
            self.assertIn(path.resolve(), {p.resolve() for p in reached}, f'orphan prompt {path.relative_to(ROOT)}')

    def test_fragment_anchors_exist(self):
        for page in self.documents():
            for target in local_link_targets(page.read_text()):
                filename, _, fragment = target.partition('#')
                if not fragment or not filename.endswith('.md'):
                    continue
                heading = (page.parent/filename).read_text()
                slugs = {re.sub(r'[^a-z0-9 -]', '', h.lower()).strip().replace(' ', '-')
                         for h in re.findall(r'^#+ (.+)$', heading, re.M)}
                self.assertIn(fragment, slugs, f'{page.relative_to(ROOT)} -> {target}')

    def test_no_install_or_global_link_advice(self):
        for page in [*self.documents(), *sorted((AUDIT/'scripts').glob('*.py')), AUDIT/'references/protocol.md']:
            self.assertIsNone(INSTALL_ADVICE.search(page.read_text()), page.relative_to(ROOT))

    def test_every_architecture_check_keeps_verification_unrun(self):
        for name in ARCHITECTURES:
            text = (BUNDLE/'architectures'/f'{name}.md').read_text()
            self.assertTrue(text.startswith('# '), name)
            self.assertIn('not_run', text, name)
            self.assertNotRegex(text, r'(?i)\bverified that\b|\ball tests pass', name)
            self.assertLessEqual(len(text.split()), 700, name)

    def test_method_terms_name_their_owners(self):
        notes = (BUNDLE/'method-notes.md').read_text()
        for term in ('STRIDE', 'LINDDUN', 'Elevation of Privilege', 'ATT&CK', 'CAPEC', 'ATLAS', 'Cyber Kill Chain',
                     'CVSS', 'MAESTRO', 'trademark', 'CC BY 4.0', 'CC BY 3.0'):
            self.assertIn(term, notes)

    def test_agent_threats_are_covered(self):
        agentic = (BUNDLE/'architectures/agentic-ai.md').read_text()
        for term in ('Memory', 'Delegation', 'Approval binding', 'tool-credential-boundaries'):
            self.assertIn(term, agentic)
        tools = (BUNDLE/'tool-credential-boundaries.md').read_text()
        for term in ('Tool description poisoning', 'shared', 'confused-deputy'):
            self.assertIn(term, tools)
        self.assertIn('Instruction influence', (BUNDLE/'architectures/rag.md').read_text())
        self.assertIn('Dependency selection', (BUNDLE/'architectures/cicd-supply-chain.md').read_text())


class RecordTests(unittest.TestCase):
    def test_licence_and_records_pin_real_bytes(self):
        self.assertIn('Copyright (c) 2026 Jim Manico', (RECORDS/'LICENSE').read_text())
        self.assertIn('Copyright (c) 2026 Anh Dang and Orbyn contributors', (RECORDS/'LICENSE-Orbyn.txt').read_text())
        snapshot = json.loads((RECORDS/'snapshot.json').read_text())
        self.assertEqual(snapshot['revision'], REVISION)
        self.assertEqual(snapshot['repository'], 'https://github.com/jmanico/grim-prompter')
        self.assertEqual(set(snapshot['files']), {'LICENSE', 'LICENSE-Orbyn.txt', 'SOURCE.md', 'source-manifest.json'})
        for name, entry in snapshot['files'].items():
            self.assertEqual(sha256(RECORDS/name), entry['sha256'], name)
        actual = {p.name for p in RECORDS.iterdir()}
        self.assertEqual(actual, set(snapshot['files']) | {'snapshot.json'})

    def test_manifest_lists_every_maintained_file_with_both_hashes(self):
        manifest = json.loads((RECORDS/'source-manifest.json').read_text())
        self.assertEqual(manifest['revision'], REVISION)
        maintained = {p.relative_to(AUDIT).as_posix() for p in BUNDLE.rglob('*') if p.is_file()}
        maintained |= {'references/threat-model.md', 'scripts/check_threat_model.py'}
        self.assertEqual(set(manifest['files']), maintained)
        for name, entry in manifest['files'].items():
            self.assertEqual(sha256(AUDIT/name), entry['sha256'], name)
            if entry['relationship'] == 'maintained-adaptation':
                self.assertRegex(entry['original_sha256'], '^[0-9a-f]{64}$', name)
                self.assertNotEqual(entry['original_sha256'], entry['sha256'], name)
            else:
                self.assertIsNone(entry['original_sha256'], name)

    def test_original_hashes_match_the_pinned_source_when_present(self):
        if not PINNED.is_dir():
            self.skipTest('the pinned source is local reference material and is not present')
        manifest = json.loads((RECORDS/'source-manifest.json').read_text())
        self.assertEqual(sha256(PINNED/'LICENSE'), sha256(RECORDS/'LICENSE'))
        for name, entry in manifest['files'].items():
            if entry['original_sha256']:
                self.assertEqual(sha256(PINNED/entry['source_path']), entry['original_sha256'], name)
                for extra in entry.get('also_from', []):
                    self.assertEqual(sha256(PINNED/extra['source_path']), extra['original_sha256'], name)

    def test_a_changed_byte_is_detected(self):
        manifest = json.loads((RECORDS/'source-manifest.json').read_text())
        name = 'references/threat-model/architectures/web.md'
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)/'web.md'
            copy.write_bytes((AUDIT/name).read_bytes() + b' ')
            self.assertNotEqual(sha256(copy), manifest['files'][name]['sha256'])

    def test_source_record_states_what_was_excluded(self):
        source = (RECORDS/'SOURCE.md').read_text()
        for term in ('Excluded, never copied', 'six-stage deep chains', 'method prompts', 'MITRE', 'Lockheed Martin',
                     'not imported or activated', 'Jim Manico'):
            self.assertIn(term, source)


class CheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_checker()
        contract = (BUNDLE/'artifact-contract.md').read_text()
        cls.example = json.loads(re.findall(r'```json\n(.*?)```', contract, re.S)[0])

    def setUp(self):
        self.model = json.loads(json.dumps(self.example))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name).resolve()
        (self.target/'src/share').mkdir(parents=True)
        (self.target/'src/share/revoke.ts').write_text('\n'.join(f'line {n}' for n in range(1, 61)))
        (self.target/'src/share/stream.ts').write_text('\n'.join(f'line {n}' for n in range(1, 41)))

    def faults(self, model=None, root=True):
        return self.checker.check(model if model is not None else self.model, self.target if root else None)

    def test_the_contract_example_is_valid(self):
        self.assertEqual(self.faults(), [])
        self.assertEqual(self.faults(root=False), [])

    def test_planted_faults_are_caught(self):
        def mutate(change):
            model = json.loads(json.dumps(self.example))
            change(model)
            return model
        plants = {
            'invented file': lambda m: m['evidence'][0].update(locator='src/share/missing.ts:1-2'),
            'line beyond the file': lambda m: m['evidence'][0].update(locator='src/share/revoke.ts:40-900'),
            'reversed range': lambda m: m['evidence'][0].update(locator='src/share/revoke.ts:58-40'),
            'escaping path': lambda m: m['evidence'][0].update(locator='../outside.ts:1-2'),
            'absolute path': lambda m: m['evidence'][0].update(locator='/etc/hosts:1-2'),
            'no line numbers': lambda m: m['evidence'][0].update(locator='src/share/revoke.ts'),
            'excerpt not in lines': lambda m: m['evidence'][0].update(excerpt='authorize(user)'),
            'weakness on documentation only': lambda m: [m['evidence'][0].update(kind='documentation'),
                                                          m['evidence'][1].update(kind='caller_claim', locator='session:chat')],
            'unrun status claimed passed': lambda m: m['verification'][0].update(status='passed'),
            'missing fail criterion': lambda m: m['verification'][0].pop('fail'),
            'severity without rubric': lambda m: m['threats'][0].update(severity='high'),
            'duplicate id': lambda m: m['assets'].append({'id': 'A1', 'name': 'again'}),
            'dangling evidence ref': lambda m: m['threats'][0]['evidence_refs'].append('E9'),
            'wrong kind of ref': lambda m: m['threats'][0].update(actor='A1'),
            'no prerequisites': lambda m: m['threats'][0].update(prerequisites=[]),
            'no deciding observation': lambda m: m['threats'][0].update(decisive_observation=''),
            'no counterevidence': lambda m: m['threats'][0].update(counterevidence=''),
            'bad basis': lambda m: m['threats'][0].update(basis='confirmed'),
            'bad handoff': lambda m: m['threats'][0].update(handoff={'to': 'publish', 'ref': 'tm:T1'}),
            'handoff without id': lambda m: m['threats'][0].update(handoff={'to': 'audit', 'ref': 'T1'}),
            'protected without control': lambda m: m['threats'][0].update(basis='protected', existing_controls=[]),
            'no limitations': lambda m: m.update(limitations=[]),
            'complete is not a status word': lambda m: m.update(status='done'),
            'execution by caller claim path': lambda m: m['evidence'][0].update(kind='caller_claim'),
            'wrong schema': lambda m: m.update(schema='x'),
            'threat without a verification': lambda m: m['threats'][0].update(verification_refs=[]),
            'verification of another threat': lambda m: m['verification'][0].update(threat_ref='T2'),
            'verification not cited back': lambda m: m['verification'].append({**m['verification'][0], 'id': 'V2'}),
            'threat cites a foreign check': lambda m: [m['threats'].append({**m['threats'][0], 'id': 'T2', 'verification_refs': ['V2'],
                                                                             'handoff': {'to': 'audit', 'ref': 'tm:T2'}}),
                                                        m['verification'].append({**m['verification'][0], 'id': 'V2', 'threat_ref': 'T2'}),
                                                        m['threats'][0]['verification_refs'].append('V2')],
            'identical outcome text': lambda m: m['verification'][0].update({key: 'Same.' for key in ('pass', 'fail', 'inconclusive')}),
            'outcome text differs by case only': lambda m: m['verification'][0].update(fail=m['verification'][0]['pass'].upper()),
            'no threats key': lambda m: m.pop('threats'),
            'no evidence key': lambda m: m.pop('evidence'),
            'no verification key': lambda m: m.pop('verification'),
            'complete with no threats': lambda m: m.update(status='complete', threats=[]),
            'complete with no evidence': lambda m: m.update(status='complete', evidence=[]),
            'complete with no verification': lambda m: m.update(status='complete', verification=[]),
            'unrouted observed weakness': lambda m: m['threats'][0].update(handoff={'to': 'none'}),
            'protected control without evidence': lambda m: [m['threats'][0].update(basis='protected', handoff={'to': 'none'}),
                                                              m['controls'][0].update(evidence_refs=[])],
            'actor without capability': lambda m: m['actors'][0].pop('capability'),
            'unicode digit in an id': lambda m: m['assets'][0].update(id='A\u0661'),
            'leading zero in an id': lambda m: m['assets'][0].update(id='A01'),
            'capitalised rating field': lambda m: m['threats'][0].update(Severity='high'),
            'rating under a null rubric': lambda m: [m['threats'][0].update(severity='high'), m.update(rubric=None)],
        }
        for label, change in plants.items():
            with self.subTest(label):
                self.assertNotEqual(self.faults(mutate(change)), [], label)

    def test_rating_is_allowed_only_with_a_supplied_rubric(self):
        self.model['threats'][0]['severity'] = 'high'
        self.model['rubric'] = {'source': 'supplied by the person', 'scale': ['low', 'high']}
        self.assertEqual(self.faults(), [])

    def test_a_matching_excerpt_passes(self):
        self.model['evidence'][1]['excerpt'] = 'line 12 line 13'
        self.assertEqual(self.faults(), [])

    def test_symlink_out_of_the_target_is_refused(self):
        outside = Path(self.tmp.name).parent/f'outside-{self.target.name}.ts'
        outside.write_text('secret\n')
        self.addCleanup(outside.unlink)
        (self.target/'src/link.ts').symlink_to(outside)
        self.model['evidence'][0]['locator'] = 'src/link.ts:1'
        self.assertNotEqual(self.faults(), [])

    def test_locators_stay_contained_without_a_root(self):
        for locator in ('/etc/passwd:1', '../../x:1', 'src/../../x:1', '~/x:1', '..\\x:1', 'src/share/revoke.ts:58-40'):
            with self.subTest(locator):
                self.model['evidence'][0]['locator'] = locator
                self.assertNotEqual(self.faults(root=False), [])

    def test_a_partial_model_may_hold_empty_collections(self):
        self.model.update(threats=[], evidence=[], verification=[], controls=[], gaps=[])
        self.assertEqual(self.faults(root=False), [])

    def test_a_secret_looking_file_is_never_opened(self):
        (self.target/'.env').write_text('TOKEN=abc\n')
        (self.target/'src/config.txt').symlink_to(self.target/'.env')
        self.model['evidence'][0]['locator'] = '.env:900'
        self.assertEqual(self.faults(), [], 'a line range past the end proves the file was not read')
        self.model['evidence'][0]['locator'] = 'src/config.txt:900'
        self.assertEqual(self.faults(), [], 'a link to a secret file is not opened either')
        for locator in ('.env:1', 'src/config.txt:1', 'deploy/.ENV.production:1', 'keys/server.pem:1', '.ssh/config:1'):
            self.model['evidence'][0]['locator'] = locator
            answers = set()
            for guess in ('TOKEN=abc', 'wrong guess'):
                self.model['evidence'][0]['excerpt'] = guess
                answers.add(tuple(self.faults()))
            self.assertEqual(len(answers), 1, f'{locator}: the answer must not depend on the content')
            self.assertNotEqual(answers.pop(), (), locator)

    def test_ordinary_lookalikes_are_still_read(self):
        (self.target/'.env.example').write_text('TOKEN=\n')
        (self.target/'src/secrets.ts').write_text('const a = 1;\n')
        for locator, excerpt in (('.env.example:1', 'TOKEN='), ('src/secrets.ts:1', 'const a')):
            self.model['evidence'][0].update(locator=locator, excerpt=excerpt)
            self.assertEqual(self.faults(), [], locator)
            self.model['evidence'][0]['excerpt'] = 'absent'
            self.assertNotEqual(self.faults(), [], locator)

    def test_an_execution_locator_may_sit_in_the_run_folder(self):
        run = self.target.parent/f'run-{self.target.name}'
        run.mkdir()
        self.addCleanup(shutil.rmtree, run)
        (run/'out.txt').write_text('exit 1\n')
        self.model['evidence'].append({'id': 'E3', 'kind': 'execution', 'locator': 'out.txt:1', 'summary': 'Authorized run.', 'excerpt': 'exit 1'})
        self.assertNotEqual(self.checker.check(self.model, self.target), [], 'no run folder was named')
        self.assertEqual(self.checker.check(self.model, self.target, run=run), [])
        self.model['evidence'][-1]['kind'] = 'implementation'
        self.assertNotEqual(self.checker.check(self.model, self.target, run=run), [], 'only execution output lives there')
        self.model['evidence'][-1].update(kind='execution', locator='../out.txt:1')
        self.assertNotEqual(self.checker.check(self.model, self.target, run=run), [])
        outside = run.parent/f'outside-{run.name}.txt'
        outside.write_text('secret\n')
        self.addCleanup(outside.unlink)
        (run/'link.txt').symlink_to(outside)
        self.model['evidence'][-1]['locator'] = 'link.txt:1'
        self.assertNotEqual(self.checker.check(self.model, self.target, run=run), [])

    def test_command_line_exit_codes(self):
        script = str(AUDIT/'scripts/check_threat_model.py')
        good = self.target/'model.json'
        good.write_text(json.dumps(self.model))
        run = lambda *args: subprocess.run([sys.executable, '-I', script, *args], capture_output=True, text=True)
        self.assertEqual(run(str(good), '--root', str(self.target)).returncode, 0)
        self.model['verification'][0]['status'] = 'passed'
        bad = self.target/'bad.json'
        bad.write_text(json.dumps(self.model))
        failed = run(str(bad), '--root', str(self.target))
        self.assertEqual(failed.returncode, 1)
        self.assertIn('not_run', failed.stderr)
        duplicate = self.target/'dup.json'
        duplicate.write_text('{"schema": "a", "schema": "b"}')
        self.assertEqual(run(str(duplicate)).returncode, 2)
        self.assertEqual(run(str(self.target/'absent.json')).returncode, 2)

    def test_checker_reads_files_only(self):
        source = (AUDIT/'scripts/check_threat_model.py').read_text()
        self.assertIsNone(re.search(r'subprocess|os\.system|exec\(|eval\(|urllib|socket|requests', source))


def guide_names():
    return load_checker().guide_rows()


def contract_model():
    contract = (BUNDLE/'artifact-contract.md').read_text()
    return json.loads(re.findall(r'```json\n(.*?)```', contract, re.S)[0])


def join_faults(method, selector, guide, model):
    """Faults where the threat model and the boundary guide stop being one workflow."""
    faults = []
    for label, text in (('method', method), ('selector', selector)):
        if 'threat-boundaries.md' not in ' '.join(local_link_targets(text)):
            faults.append(f'{label}: does not link the boundary guide')
    names = load_checker().guide_rows_from(guide)
    for boundary in model['boundaries']:
        if boundary.get('guide') not in names:
            faults.append(f"{boundary['id']}: guide {boundary.get('guide')!r} is not a row of the boundary guide")
    return faults


class BoundaryJoinTests(unittest.TestCase):
    def setUp(self):
        self.method = (REFS/'threat-model.md').read_text()
        self.selector = (BUNDLE/'architecture-selector.md').read_text()
        self.guide = (REFS/'threat-boundaries.md').read_text()

    def test_threat_model_and_guide_are_one_workflow(self):
        self.assertEqual(join_faults(self.method, self.selector, self.guide, contract_model()), [])

    def test_each_join_rule_fails_on_a_planted_fault(self):
        model = contract_model()
        renamed = json.loads(json.dumps(model))
        renamed['boundaries'][0]['guide'] = 'Link holder to document stream'
        plants = {
            'method unlinked': (self.method.replace('threat-boundaries.md', 'elsewhere.md'), self.selector, self.guide, model),
            'selector unlinked': (self.method, self.selector.replace('threat-boundaries.md', 'elsewhere.md'), self.guide, model),
            'invented boundary name': (self.method, self.selector, self.guide, renamed),
            'row removed from guide': (self.method, self.selector, self.guide.replace('| Identity and resource authority |', '| Identity |'), model),
        }
        for label, args in plants.items():
            with self.subTest(label):
                self.assertNotEqual(join_faults(*args), [], label)

    def test_guide_covers_agent_tools_and_shared_credentials(self):
        names = guide_names()
        self.assertIn('AI and tool effects', names)
        self.assertIn('Tool definitions and shared credentials', names)
        self.assertEqual(len(names), len(set(names)))
        row = next(line for line in self.guide.splitlines() if line.startswith('| Tool definitions and shared credentials'))
        self.assertIn('tool-credential-boundaries.md', row)

    def test_every_guide_row_points_at_deeper_checks_that_exist(self):
        for line in self.guide.splitlines():
            if line.startswith('| ') and not line.startswith(('| Boundary', '| ---')):
                last = line.strip().strip('|').split('|')[-1]
                for target in local_link_targets(last):
                    self.assertTrue((REFS/target).is_file(), target)
                self.assertTrue(local_link_targets(last) or 'none bundled' in last, line[:40])

    def test_architecture_files_do_not_restate_the_guide_table(self):
        for page in sorted(BUNDLE.rglob('*.md')):
            self.assertNotIn('| Boundary | Questions to resolve', page.read_text(), page.name)


class HandoffTests(unittest.TestCase):
    """The threat model reaches the audit through a converter, a ledger and a fingerprint rule."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve()
        self.target = self.dir/'target'
        (self.target/'src/share').mkdir(parents=True)
        (self.target/'src/share/revoke.ts').write_text('\n'.join(f'line {n}' for n in range(1, 61)))
        (self.target/'src/share/stream.ts').write_text('\n'.join(f'line {n}' for n in range(1, 41)))
        (self.target/'src/agent').mkdir()
        (self.target/'src/agent/tools.ts').write_text('\n'.join(f'line {n}' for n in range(1, 31)))
        self.model = self.fixture()

    def fixture(self):
        model = contract_model()
        model['evidence'].append({'id': 'E3', 'kind': 'configuration', 'locator': 'src/agent/tools.ts:5-20',
                                  'summary': 'One service key serves the read and the write tool.'})
        model['boundaries'].append({'id': 'B2', 'name': 'Tool runtime to document store', 'guide': 'Tool definitions and shared credentials', 'owner': 'agentic-ai'})
        model['controls'].append({'id': 'C2', 'name': 'Write tool checks the caller role', 'evidence_refs': ['E3'], 'status': 'observed'})
        base = model['threats'][0]
        def threat(number, basis, boundary, **extra):
            record = json.loads(json.dumps(base))
            record.update(id=f'T{number}', title=f'Threat {number}', basis=basis, boundary=boundary,
                          handoff={'to': 'audit', 'ref': f'tm:T{number}'}, verification_refs=[f'V{number}'], **extra)
            model['verification'].append({**model['verification'][0], 'id': f'V{number}', 'threat_ref': f'T{number}'})
            return record
        model['threats'] += [threat(2, 'design_hypothesis', 'B2', evidence_refs=['E3']),
                             threat(10, 'observed_weakness', 'B2', evidence_refs=['E3']),
                             threat(3, 'protected', 'B2', evidence_refs=['E3'], existing_controls=['C2'])]
        model['threats'][-1]['handoff'] = {'to': 'none'}
        return model

    def write(self, model=None, name='threat-model.json'):
        path = self.dir/name
        path.write_text(json.dumps(self.model if model is None else model))
        return path

    def convert(self, *args):
        return subprocess.run([sys.executable, '-I', str(CONVERTER), *args], capture_output=True, text=True)

    def run_ok(self, model=None, out='coverage-ledger.json'):
        result = self.convert(str(self.write(model)), '--root', str(self.target), '--out', str(self.dir/out))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.dir/out).read_text())

    def test_converter_is_standard_library_only(self):
        imports = {alias.name.split('.')[0] for node in ast.walk(ast.parse(CONVERTER.read_text()))
                   for alias in (node.names if isinstance(node, ast.Import) else [])}
        imports |= {node.module.split('.')[0] for node in ast.walk(ast.parse(CONVERTER.read_text()))
                    if isinstance(node, ast.ImportFrom) and node.module}
        self.assertTrue(imports <= set(sys.stdlib_module_names), imports - set(sys.stdlib_module_names))

    def test_one_planned_unit_per_unprotected_threat(self):
        units = self.run_ok()
        self.assertEqual({unit['attack_class'] for unit in units}, {'tm:T1', 'tm:T2', 'tm:T10'})
        self.assertEqual({unit['status'] for unit in units}, {'planned'})
        by_id = {unit['attack_class']: unit for unit in units}
        self.assertEqual(by_id['tm:T1']['boundary'], 'Identity and resource authority')
        self.assertEqual(by_id['tm:T1']['starting_paths'], ['src/share/revoke.ts', 'src/share/stream.ts'])
        self.assertEqual(by_id['tm:T2']['boundary'], 'Tool definitions and shared credentials')
        self.assertEqual(by_id['tm:T2']['starting_paths'], ['src/agent/tools.ts'])

    def test_threat_ids_survive_into_the_coverage_identity(self):
        units = self.run_ok()
        for unit in units:
            self.assertEqual(unit['canonical_refs']['attack_class'], unit['attack_class'])
            self.assertTrue(unit['coverage_id'].endswith('::' + unit['attack_class'].replace(':', '%3A')), unit['coverage_id'])
        self.assertEqual([unit['coverage_id'] for unit in units], sorted(unit['coverage_id'] for unit in units))
        self.assertEqual(len({unit['coverage_id'] for unit in units}), len(units))

    @unittest.skipUnless(NODE, 'node is not available')
    def test_the_node_validator_accepts_the_ledger(self):
        self.run_ok()
        result = subprocess.run([NODE, str(AUDIT_RECORDS/'validate-coverage-ledger.cjs'), str(self.dir/'coverage-ledger.json')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PASS: 3 coverage units valid', result.stdout)

    @unittest.skipUnless(NODE, 'node is not available')
    def test_the_node_validator_still_rejects_a_damaged_ledger(self):
        units = self.run_ok()
        units[0]['coverage_id'] = 'edited'
        damaged = self.dir/'damaged.json'
        damaged.write_text(json.dumps(units))
        result = subprocess.run([NODE, str(AUDIT_RECORDS/'validate-coverage-ledger.cjs'), str(damaged)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_an_invalid_model_is_refused_and_writes_nothing(self):
        def mutate(change):
            model = json.loads(json.dumps(self.model))
            change(model)
            return model
        plants = {
            'unrun check claimed passed': lambda m: m['verification'][0].update(status='passed'),
            'invented guide row': lambda m: m['boundaries'][0].update(guide='Everything'),
            'missing guide row': lambda m: m['boundaries'][0].pop('guide'),
            'handoff id of another threat': lambda m: m['threats'][1].update(handoff={'to': 'audit', 'ref': 'tm:T1'}),
            'weakness without code evidence': lambda m: m['evidence'][2].update(kind='documentation'),
            'invented file': lambda m: m['evidence'][0].update(locator='src/share/missing.ts:1-2'),
        }
        for label, change in plants.items():
            with self.subTest(label):
                out = self.dir/f'refused-{abs(hash(label))}.json'
                result = self.convert(str(self.write(mutate(change))), '--root', str(self.target), '--out', str(out))
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertFalse(out.exists())

    def test_unreadable_input_exits_two(self):
        self.assertEqual(self.convert(str(self.dir/'absent.json'), '--out', str(self.dir/'x.json')).returncode, 2)
        duplicate = self.dir/'dup.json'
        duplicate.write_text('{"schema": "a", "schema": "b"}')
        self.assertEqual(self.convert(str(duplicate), '--out', str(self.dir/'x.json')).returncode, 2)

    def test_an_existing_output_is_never_overwritten(self):
        self.run_ok()
        first = (self.dir/'coverage-ledger.json').read_bytes()
        again = self.convert(str(self.write()), '--out', str(self.dir/'coverage-ledger.json'))
        self.assertEqual(again.returncode, 1)
        self.assertIn('never overwritten', again.stderr)
        self.assertEqual((self.dir/'coverage-ledger.json').read_bytes(), first)

    def test_a_link_at_the_output_path_is_not_followed(self):
        victim = self.dir/'victim.txt'
        victim.write_text('keep')
        (self.dir/'link.json').symlink_to(victim)
        result = self.convert(str(self.write()), '--out', str(self.dir/'link.json'))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(victim.read_text(), 'keep')
        dangling = self.dir/'dangling.json'
        dangling.symlink_to(self.dir/'not-there.txt')
        self.assertEqual(self.convert(str(self.write()), '--out', str(dangling)).returncode, 1)
        self.assertFalse((self.dir/'not-there.txt').exists())

    def test_output_needs_an_existing_folder(self):
        result = self.convert(str(self.write()), '--out', str(self.dir/'absent'/'ledger.json'))
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.dir/'absent').exists())

    def test_output_inside_an_unignored_git_folder_is_refused(self):
        if not shutil.which('git'):
            self.skipTest('git is not available')
        repo = self.dir/'repo'
        (repo/'output').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(repo)], check=True, capture_output=True)
        (repo/'.gitignore').write_text('output/\n')
        refused = self.convert(str(self.write()), '--out', str(repo/'ledger.json'))
        self.assertEqual(refused.returncode, 1)
        self.assertIn('not ignored', refused.stderr)
        self.assertFalse((repo/'ledger.json').exists())
        accepted = self.convert(str(self.write()), '--out', str(repo/'output/ledger.json'))
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_the_default_run_folder_stays_ignored_for_the_ledger(self):
        if not shutil.which('git'):
            self.skipTest('git is not available')
        probe = 'output/threat-model/2026-01-01-quick-probe/coverage-ledger.json'
        self.assertEqual(subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--no-index', probe]).returncode, 0)

    @unittest.skipUnless(NODE, 'node is not available')
    def test_a_finding_carries_its_threat_id_in_the_fingerprint(self):
        def finding(fingerprint):
            return {'verdict': 'needs_validation', 'fingerprint': fingerprint, 'title': 'Revoked link keeps streaming',
                    'description': 'A connected recipient may keep receiving after revocation.',
                    'claimed_root_cause': 'The stream reads the link once at connect.',
                    'trace': [{'kind': 'entrypoint', 'file': 'src/share/stream.ts', 'line': 12, 'scope': 'connect',
                               'description': 'The link is read once.'}],
                    'evidence': [{'file': 'src/share/stream.ts', 'line': 12, 'description': 'No later recheck was found.'}],
                    'blockers': ['The transport middleware was not supplied.'],
                    'validation_plan': {'local': 'Open a stream, revoke, read frames.', 'deployment': 'Repeat in an approved test deployment.'}}
        def validate(findings):
            path = self.dir/'findings.json'
            path.write_text(json.dumps(findings))
            return subprocess.run([NODE, str(AUDIT_RECORDS/'validate-findings.cjs'), str(path)], capture_output=True, text=True)
        good = validate([finding('tm:T1/revoked-link-streams'), finding('tm:T10')])
        self.assertEqual(good.returncode, 0, good.stderr + good.stdout)
        self.assertEqual(validate([finding('tm:T 1')]).returncode, 1)
        protocol = (REFS/'protocol.md').read_text()
        self.assertIn('exactly `tm:T<n>`, or `tm:T<n>/<slug>`', protocol)
        self.assertRegex('tm:T1/revoked-link-streams', r'^tm:T\d+(/[A-Za-z0-9._:@+-]+)?$')

    def test_the_audit_records_are_unchanged(self):
        snapshot = json.loads((AUDIT_RECORDS/'snapshot.json').read_text())
        for name, entry in snapshot['files'].items():
            self.assertEqual(sha256(AUDIT_RECORDS/name), entry['sha256'], name)

    def test_the_documents_give_the_real_commands_and_the_exact_id_rule(self):
        skill = (AUDIT/'SKILL.md').read_text()
        protocol = (REFS/'protocol.md').read_text()
        remediation = (REMEDIATION/'SKILL.md').read_text()
        for command in ('python3 scripts/threats_to_ledger.py', 'python3 scripts/check_threat_model.py',
                        'references/upstream/audit-records/validate-coverage-ledger.cjs'):
            self.assertIn(command, skill)
        for script in set(re.findall(r'scripts/\w+\.py', skill)):
            self.assertTrue((AUDIT/script).is_file(), script)
        for validator in set(re.findall(r'references/upstream/audit-records/[\w.-]+\.cjs', skill)):
            self.assertTrue((AUDIT/validator).is_file(), validator)
        self.assertIn('scripts/threats_to_ledger.py', protocol)
        self.assertIn('`fingerprint`', remediation)
        self.assertIn('`tm:T<n>/<slug>`', remediation)
        self.assertIn('never renumber', remediation)
        self.assertLessEqual(len(split(skill)[1].split()), 1200)

    def check_cli(self, *args):
        return subprocess.run([sys.executable, '-I', str(AUDIT/'scripts/check_threat_model.py'), *args], capture_output=True, text=True)

    def test_only_threats_still_open_are_seeded(self):
        model = self.fixture()
        retire = {'reason': 'The route was removed.', 'evidence_refs': ['E3']}
        fixed = {'status': 'resolved', 'evidence_refs': ['E3'], 'note': 'Fixed.'}
        partial = {'status': 'partly_resolved', 'evidence_refs': ['E3'], 'note': 'Half.', 'remaining': 'The read path.'}
        model['threats'][0]['retired'] = retire
        model['threats'][1]['resolution'] = fixed
        model['threats'][2]['resolution'] = partial
        for number, to in ((4, 'decision'), (5, 'none')):
            copy = json.loads(json.dumps(model['threats'][1]))
            copy.update(id=f'T{number}', verification_refs=[f'V{number}'], basis='design_hypothesis',
                        handoff={'to': to, 'ref': f'tm:T{number}'} if to != 'none' else {'to': 'none'})
            copy.pop('resolution')
            model['threats'].append(copy)
            model['verification'].append({**model['verification'][0], 'id': f'V{number}', 'threat_ref': f'T{number}'})
        result = self.convert(str(self.write(model)), '--root', str(self.target), '--out', str(self.dir/'seeded.json'))
        self.assertEqual(result.returncode, 0, result.stderr)
        units = json.loads((self.dir/'seeded.json').read_text())
        self.assertEqual({unit['attack_class'] for unit in units}, {'tm:T10'})
        for line in ('tm:T1 (retired)', 'tm:T2 (resolved)', 'tm:T3 (protected)', 'tm:T4 (decision)', 'tm:T5 (no handoff)'):
            self.assertIn(line, result.stdout)

    def test_retired_needs_a_reason_and_evidence(self):
        checker = load_checker()
        for label, value in (('flag', True), ('no reason', {'evidence_refs': ['E3']}), ('blank reason', {'reason': ' ', 'evidence_refs': ['E3']}),
                             ('no evidence', {'reason': 'Gone.', 'evidence_refs': []}), ('dangling', {'reason': 'Gone.', 'evidence_refs': ['E9']})):
            with self.subTest(label):
                model = self.fixture()
                model['threats'][0]['retired'] = value
                self.assertNotEqual(checker.check(model, self.target), [], label)
        model = self.fixture()
        model['threats'][0]['retired'] = {'reason': 'Gone.', 'evidence_refs': ['E3']}
        self.assertEqual(checker.check(model, self.target), [])

    def test_a_baseline_refuses_a_dropped_threat(self):
        old = self.fixture()
        old['revision'] = '1'
        for actor in old['actors']:
            actor.pop('capability', None)  # an older revision is read for ids, not held to today's rules
        baseline = self.write(old, 'baseline.json')
        new = self.fixture()
        new.update(revision='2', parent_revision='1')
        self.assertEqual(self.check_cli(str(self.write(new)), '--baseline', str(baseline)).returncode, 0)
        dropped = json.loads(json.dumps(new))
        dropped['threats'] = [t for t in dropped['threats'] if t['id'] != 'T2']
        dropped['verification'] = [v for v in dropped['verification'] if v['id'] != 'V2']
        result = self.check_cli(str(self.write(dropped)), '--baseline', str(baseline))
        self.assertEqual(result.returncode, 1)
        self.assertIn('T2', result.stderr)
        retired = json.loads(json.dumps(new))
        retired['threats'][1]['retired'] = {'reason': 'Gone.', 'evidence_refs': ['E3']}
        self.assertEqual(self.check_cli(str(self.write(retired)), '--baseline', str(baseline)).returncode, 0)
        for label, change in (('other model', {'model_id': 'else'}), ('other parent', {'parent_revision': '9'})):
            with self.subTest(label):
                self.assertEqual(self.check_cli(str(self.write({**new, **change})), '--baseline', str(baseline)).returncode, 1)

    def ledger_faults(self, units, findings):
        ledger = self.write(units, 'ledger.json')
        saved = self.write(findings, 'findings.json')
        return self.check_cli(str(self.write()), '--ledger', str(ledger), '--findings', str(saved))

    def test_finished_units_keep_their_threat_id(self):
        units = self.run_ok()
        planned = self.ledger_faults(units, [])
        self.assertEqual(planned.returncode, 0, planned.stderr)
        by_id = {unit['attack_class']: unit for unit in units}
        by_id['tm:T1'].update(status='candidate', result_fingerprints=['unrelated-id'])
        result = self.ledger_faults(units, [{'fingerprint': 'unrelated-id'}])
        self.assertEqual(result.returncode, 1)
        self.assertIn('tm:T1', result.stderr)
        by_id['tm:T1']['result_fingerprints'] = ['tm:T10/not-this-one']
        self.assertEqual(self.ledger_faults(units, [{'fingerprint': 'tm:T10/not-this-one'}]).returncode, 1)
        by_id['tm:T1']['result_fingerprints'] = ['tm:T1/revoked-link']
        self.assertEqual(self.ledger_faults(units, []).returncode, 1, 'the fingerprint has no finding')
        self.assertEqual(self.ledger_faults(units, [{'fingerprint': 'tm:T1/revoked-link'}]).returncode, 0)
        by_id['tm:T1'].update(status='covered', result_fingerprints=[])
        self.assertEqual(self.ledger_faults(units, []).returncode, 1, 'a covered unit keeps its outcome in findings too')
        self.assertEqual(self.ledger_faults(units, [{'fingerprint': 'tm:T1'}]).returncode, 0)
        by_id['tm:T1'].update(status='blocked')
        self.assertEqual(self.ledger_faults(units, []).returncode, 0, 'a blocked unit is not finished')
        extra = {**by_id['tm:T1'], 'attack_class': 'tm:T9'}
        self.assertEqual(self.ledger_faults(units + [extra], []).returncode, 1, 'a unit names no threat')
        self.assertEqual(self.ledger_faults(units[1:], []).returncode, 1, 'an open threat lost its unit')
        self.assertEqual(self.ledger_faults({'not': 'a list'}, []).returncode, 2)
        self.assertEqual(self.ledger_faults(units, [1]).returncode, 2)
        alone = self.check_cli(str(self.write()), '--ledger', str(self.dir/'ledger.json'))
        self.assertEqual(alone.returncode, 2, 'a ledger needs its findings')

    def repository(self, name='repo'):
        repo = self.dir/name
        (repo/'output').mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(repo)], check=True, capture_output=True)
        (repo/'.gitignore').write_text('output/\n')
        return repo

    def convert_without_git(self, out):
        return subprocess.run([sys.executable, '-I', str(CONVERTER), str(self.write()), '--out', str(out)],
                              capture_output=True, text=True, env={'PATH': str(self.dir/'no-tools')})

    def test_the_ignored_guard_fails_closed(self):
        if not shutil.which('git'):
            self.skipTest('git is not available')
        repo = self.repository()
        no_git = self.convert_without_git(repo/'ledger.json')
        self.assertEqual(no_git.returncode, 1, no_git.stderr)
        self.assertFalse((repo/'ledger.json').exists())
        self.assertEqual(self.convert_without_git(repo/'output/ledger.json').returncode, 1, 'an unanswered question is a refusal')
        (repo/'.git/config').write_text('not a config\n')
        broken = self.convert(str(self.write()), '--out', str(repo/'ledger.json'))
        self.assertEqual(broken.returncode, 1, broken.stderr)
        self.assertFalse((repo/'ledger.json').exists())

    def test_a_linked_folder_into_a_repository_does_not_open_the_guard(self):
        if not shutil.which('git'):
            self.skipTest('git is not available')
        repo = self.repository()
        (self.dir/'alias').symlink_to(repo)
        result = self.convert_without_git(self.dir/'alias/ledger.json')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse((repo/'ledger.json').exists())

    def test_outside_any_repository_an_unignored_path_is_allowed(self):
        (self.dir/'plain').mkdir()
        result = self.convert_without_git(self.dir/'plain/ledger.json')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_execution_output_is_not_a_starting_path(self):
        (self.dir/'out.txt').write_text('exit 1\n')
        model = self.fixture()
        model['evidence'].append({'id': 'E4', 'kind': 'execution', 'locator': 'out.txt:1', 'summary': 'Authorized run.'})
        model['threats'][0]['evidence_refs'].append('E4')
        result = {unit['attack_class']: unit for unit in self.run_ok(model)}
        self.assertEqual(result['tm:T1']['starting_paths'], ['src/share/revoke.ts', 'src/share/stream.ts'])

    def test_a_resolved_threat_needs_code_evidence(self):
        checker = load_checker()
        model = self.fixture()
        model['evidence'].append({'id': 'E4', 'kind': 'implementation', 'locator': 'src/share/stream.ts:30-40', 'summary': 'Each frame rechecks the link.'})
        model['threats'][0]['resolution'] = {'status': 'resolved', 'evidence_refs': ['E4'], 'note': 'Revoke now closes the stream.'}
        self.assertEqual(checker.check(model, self.target), [])
        model['evidence'][-1]['kind'] = 'documentation'
        self.assertNotEqual(checker.check(model, self.target), [])
        model['evidence'][-1]['kind'] = 'implementation'
        model['threats'][0]['resolution']['status'] = 'fixed'
        self.assertNotEqual(checker.check(model, self.target), [])
        model['threats'][0]['resolution']['status'] = 'partly_resolved'
        self.assertNotEqual(checker.check(model, self.target), [], 'a partial fix names what remains')
        model['threats'][0]['resolution']['remaining'] = 'The transport layer was not read.'
        self.assertEqual(checker.check(model, self.target), [])


class HostileInputTests(unittest.TestCase):
    """Any JSON at all yields named faults and exit 2 from both scripts, never a traceback."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve()

    def run_both(self, raw):
        path = self.dir/'model.json'
        path.write_text(raw, encoding='utf-8')
        for script, extra in ((AUDIT/'scripts/check_threat_model.py', []), (CONVERTER, ['--out', str(self.dir/'out.json')])):
            yield script.name, subprocess.run([sys.executable, '-I', str(script), str(path), *extra], capture_output=True, text=True)
        self.assertFalse((self.dir/'out.json').exists())

    def test_wrong_shapes_are_named_and_exit_two(self):
        def mutate(change):
            model = contract_model()
            change(model)
            return json.dumps(model)
        plants = {
            'list at the top': ('[]', 'object'),
            'number at the top': ('5', 'object'),
            'collection is a number': (mutate(lambda m: m.update(evidence=5)), 'evidence'),
            'collection is null': (mutate(lambda m: m.update(threats=None)), 'threats'),
            'record is a number': (mutate(lambda m: m.update(threats=[1])), 'threats[0]'),
            'id is a number': (mutate(lambda m: m['assets'][0].update(id=1)), 'assets[0]'),
            'kind is a list': (mutate(lambda m: m['evidence'][0].update(kind=['implementation'])), 'kind'),
            'objective is a list': (mutate(lambda m: m['threats'][0].update(objective=['A1'])), 'objective'),
            'handoff target is a list': (mutate(lambda m: m['threats'][0].update(handoff={'to': ['audit']})), 'to'),
            'refs is a number': (mutate(lambda m: m['threats'][0].update(evidence_refs=5)), 'evidence_refs'),
            'ref is a list': (mutate(lambda m: m['controls'][0].update(evidence_refs=[['E1']])), 'evidence_refs'),
            'resolution refs': (mutate(lambda m: m['threats'][0].update(resolution={'status': 'resolved', 'note': 'x', 'evidence_refs': 5})), 'evidence_refs'),
            'excerpt is a number': (mutate(lambda m: m['evidence'][0].update(excerpt=5)), 'excerpt'),
            'NUL in a locator': (mutate(lambda m: m['evidence'][0].update(locator='a\x00b:1')), 'locator'),
            'surrogate in a name': (mutate(lambda m: m['boundaries'][0].update(name='\ud800')), 'boundaries'),
            'surrogate in a key': (mutate(lambda m: m['threats'][0].update({'\ud800': 'x'})), 'threats'),
            'surrogate in a locator': (mutate(lambda m: m['evidence'][0].update(locator='\ud800:1')), 'evidence'),
            'deep nesting': ('[' * 200000, 'nest'),
            'deep nesting in a field': ('{"schema":' + '[' * 200000, 'nest'),
        }
        for label, (raw, named) in plants.items():
            for script, result in self.run_both(raw):
                with self.subTest(label, script=script):
                    self.assertEqual(result.returncode, 2, result.stderr[-400:])
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertIn(named, result.stderr)

    def test_an_endless_line_number_is_a_named_fault(self):
        model = contract_model()
        model['evidence'][0]['locator'] = 'a:' + '9' * 5000
        for script, result in self.run_both(json.dumps(model)):
            with self.subTest(script=script):
                self.assertEqual(result.returncode, 1, result.stderr[-400:])
                self.assertNotIn('Traceback', result.stderr)
                self.assertIn('E1', result.stderr)

    def test_nesting_that_parsed_cannot_overflow_the_shape_pass(self):
        checker = load_checker()
        deep, chain = [], {}
        for _ in range(100000):
            deep, chain = [deep], {'retired': chain}
        for model in ({'rubric': deep}, {'threats': [{'id': 'T1', 'retired': chain}]}):
            self.assertEqual(checker.shape(model), ['nesting is too deep'])
            self.assertEqual(checker.check(model), ['nesting is too deep'])

    def test_a_surrogate_in_a_path_cannot_reach_the_file_system(self):
        checker = load_checker()
        model = contract_model()
        model['evidence'][0]['locator'] = '\ud800:1'
        self.assertNotEqual(checker.check(model, self.dir), [])


if __name__ == '__main__':
    unittest.main()
