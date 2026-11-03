#!/usr/bin/env python3
"""Run executable evals at least cost. Default is a dry plan; nothing starts a model without --live.

Each trial exports a case fixture into a throwaway one-commit Git repo, runs a headless host (claude, codex or a
scripted fake), commits the final tree and grades it with answer_key.py using a key that never enters the copy.
Writes run.json files that `evaluate.py grade` and `compare` accept. Standard library only.

Subagent mode, the default way to run evals, calls no model: `prepare` exports the repository and writes the brief,
the lead agent has one host subagent work in it, and `grade` commits and grades the result.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = SKILL.parents[1]
ANSWER_KEY = ROOT / 'skills/orbyn-workflow/scripts/answer_key.py'
DEFAULT_CACHE = ROOT / 'output/eval-cache'
MAX_AUTO_RUNS = 3
STREAM_LIMIT = 1_500_000


def _sibling(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return sys.modules[name]


evaluate = _sibling('evaluate')

# ---------------------------------------------------------------- tiers

LADDERS = {'claude': ['haiku', 'sonnet'], 'codex': ['gpt-6-luna', 'gpt-6.1-terra']}
LEAD = {'claude': 'opus', 'codex': 'gpt-6.1-sol'}
DEFAULT_MODEL = {'claude': 'sonnet', 'codex': 'gpt-6.1-terra', 'fake': 'fake'}
ROUTING_START = 1  # Routing cases start at the second rung: sonnet or terra.
HINT_KEY = {'claude': 'claude', 'codex': 'codex'}
JUDGE_LADDERS = {'claude': ['gpt-6-luna', 'gpt-6.1-terra'], 'codex': ['haiku', 'sonnet']}  # other vendor, cheapest first
REFUSED = re.compile(r'fable|astra', re.I)
LEAD_RE = re.compile(r'opus|(^|[-_/.])sol($|[-_/.])', re.I)
LEAD_WARNING = ('WARNING: the lead tier (opus or sol) is allowed; it costs about twice as much as sonnet or terra. '
                'Use it only when the cheaper tiers cannot answer the question.')
ROUTING_NOTE = ('Routing cases start at sonnet or terra. In real work the lead tier makes the routing call, '
                'so this result is a close proxy, not identical.')


class Refused(Exception):
    pass


def check_model(model, allow_lead):
    if REFUSED.search(model):
        raise Refused(f'model {model!r} is refused: fable and astra are never used for evals')
    if LEAD_RE.search(model) and not allow_lead:
        raise Refused(f'model {model!r} is a lead tier; pass --allow-lead-tier to run it deliberately')
    return model


def ladder_models(name, allow_lead):
    if name not in LADDERS:
        raise Refused(f'unknown ladder {name!r}; use claude or codex')
    models = list(LADDERS[name])
    if allow_lead:
        models.append(LEAD[name])
    return models


def judge_ladder(tested_host):
    """Judge models, cheapest first, from the other vendor; climb only if calibration against labels fails."""
    return list(JUDGE_LADDERS.get(tested_host, JUDGE_LADDERS['claude']))


def slug(text):
    return re.sub(r'[^a-z0-9.]+', '-', text.lower()).strip('-') or 'x'


def case_models(case, host, models, ladder, explicit_model):
    """The tiers one case climbs, honouring its hint and the routing default."""
    if explicit_model or not ladder:
        return models
    start = 0
    hint = (case.get('tier_hints') or {}).get(HINT_KEY.get(host, 'claude'))
    for index, model in enumerate(models):
        if hint and (model == hint or model.endswith('-' + hint)):
            start = index
    if case['kind'] == 'routing' and not hint:
        start = min(ROUTING_START, len(models) - 1)
    return models[start:]


# ---------------------------------------------------------------- git and files

def git_env():
    env = {k: v for k, v in os.environ.items() if k not in {'GH_TOKEN', 'GITHUB_TOKEN', 'GITLAB_TOKEN', 'NPM_TOKEN'}
           and not k.startswith('GIT_')}
    env.update({'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0',
                'GIT_AUTHOR_NAME': 'eval', 'GIT_AUTHOR_EMAIL': 'eval@example.invalid',
                'GIT_COMMITTER_NAME': 'eval', 'GIT_COMMITTER_EMAIL': 'eval@example.invalid'})
    return env


def git(repo, *args, check=True):
    result = subprocess.run(['git', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=' + os.devnull,
                             '-C', str(repo), *args], capture_output=True, text=True, env=git_env())
    if check and result.returncode != 0:
        raise RuntimeError(f'git {args[0]} failed: {result.stderr.strip()}')
    return result


class Cleanup:
    """Removes only the temporary folders this runner created."""

    def __init__(self):
        self.paths = []

    def make(self, prefix, base=None):
        path = Path(tempfile.mkdtemp(prefix=prefix, dir=base)).resolve()
        self.paths.append(path)
        return path

    def close(self):
        for path in self.paths:
            shutil.rmtree(path, ignore_errors=True)
        self.paths = []


def key_hashes(case):
    return {hashlib.sha256(p.read_bytes()).hexdigest() for p in (case['dir'] / 'key').rglob('*')
            if p.is_file() and p.stat().st_size > 0}


def assert_no_key(work, case):
    """Refuse to run if any file in the agent copy equals a key file."""
    hashes = key_hashes(case)
    for path in work.rglob('*'):
        if '.git' in path.relative_to(work).parts or not path.is_file() or path.is_symlink():
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() in hashes:
            raise RuntimeError(f'key material found in the agent copy: {path.relative_to(work)}')


def export_fixture(case, work):
    shutil.copytree(case['dir'] / 'fixture', work, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
    git(work, 'init', '-q', '-b', 'main')
    git(work, 'add', '-A')
    git(work, 'commit', '-q', '-m', 'fixture')
    return git(work, 'rev-parse', 'HEAD').stdout.strip()


def library_skills():
    base = ROOT / 'skills'
    return sorted(p for p in base.iterdir() if (p / 'SKILL.md').is_file())


def install_skills(work, host):
    """Copy this library's skills for the `with` condition, leaving out every evals folder."""
    folder = work / ('.agents/skills' if host == 'codex' else '.claude/skills')
    folder.mkdir(parents=True)
    for skill in library_skills():
        shutil.copytree(skill, folder / skill.name,
                        ignore=shutil.ignore_patterns('evals', '__pycache__', '*.pyc', 'node_modules'))
    return folder


def skill_files(work):
    return [p for p in work.rglob('SKILL.md') if '.git' not in p.relative_to(work).parts]


def exclude_from_commit(work):
    info = work / '.git/info/exclude'
    with open(info, 'a', encoding='utf-8') as handle:
        handle.write('.claude/\n.agents/\n__pycache__/\n*.pyc\n')


# ---------------------------------------------------------------- hosts

def flag_listed(help_text, flag):
    return re.search(r'(?<![\w-])' + re.escape(flag) + r'(?![\w-])', help_text) is not None


def cli_info(binary, help_args, version_args):
    """Installed CLI version and help text; a missing binary yields None values."""
    try:
        help_text = subprocess.run([binary, *help_args], capture_output=True, text=True, timeout=30).stdout
        version = subprocess.run([binary, *version_args], capture_output=True, text=True, timeout=30).stdout.strip()
        return {'binary': binary, 'version': version or 'unknown', 'help': help_text}
    except (OSError, subprocess.SubprocessError):
        return {'binary': binary, 'version': None, 'help': ''}


CLAUDE_ALLOWED = ['Read', 'Edit', 'Write', 'Glob', 'Grep', 'Bash(python3 *)', 'Bash(git status*)', 'Bash(git diff*)',
                  'Bash(git add*)', 'Bash(git commit*)', 'Bash(git log*)', 'Bash(ls*)', 'Bash(cat *)', 'Bash(find *)',
                  'Bash(rm *)', 'Bash(mkdir *)']
CLAUDE_DENIED = ['WebFetch', 'WebSearch', 'Bash(git push*)', 'Bash(git merge*)', 'Bash(gh *)', 'Bash(curl *)',
                 'Bash(wget *)', 'Bash(rm -rf*)', 'Bash(rm -fr*)', 'Bash(rm -r *)', 'Bash(rm -R *)']


def claude_command(info, model, condition, max_turns, budget_usd, effort=None):
    """Exact claude flags from the installed help; every wanted flag the help omits is reported unsupported."""
    help_text, argv, unsupported = info['help'], [info['binary']], []

    def add(flag, *values):
        if flag_listed(help_text, flag):
            argv.extend([flag, *values])
        else:
            unsupported.append(flag)

    add('--print')
    add('--output-format', 'stream-json')
    add('--verbose')
    add('--model', model)
    add('--permission-mode', 'dontAsk')
    add('--allowedTools', *(CLAUDE_ALLOWED + (['Skill'] if condition == 'with' else [])))
    add('--disallowedTools', *CLAUDE_DENIED)
    add('--no-session-persistence')
    add('--max-turns', str(max_turns))  # Not listed by 2.1.150; the runner then enforces the limit itself.
    if budget_usd is not None:
        add('--max-budget-usd', f'{budget_usd:.2f}')
    if condition == 'without':
        add('--disable-slash-commands')
    if effort:
        add('--effort', effort)
    return argv, unsupported


def codex_command(info, model, work, effort=None):
    help_text, argv, unsupported = info['help'], [info['binary'], 'exec'], []

    def add(flag, *values):
        if flag_listed(help_text, flag):
            argv.extend([flag, *values])
        else:
            unsupported.append(flag)

    add('--json')
    add('--sandbox', 'workspace-write')
    add('--ephemeral')
    add('--ignore-user-config')
    add('--ignore-rules')
    add('--cd', str(work))
    add('--model', model)
    if effort:
        argv.extend(['-c', f'model_reasoning_effort="{effort}"'])
    argv.append('-')
    return argv, unsupported


def run_process(argv, prompt, cwd, timeout, max_turns, is_turn, sink):
    """Run a headless host, stream its stdout lines to `sink`, enforce wall time and the turn limit."""
    started = time.monotonic()
    env = git_env()
    env.pop('GIT_CONFIG_GLOBAL', None)
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, start_new_session=True)
    lines = queue.Queue()
    def pump():
        for text in process.stdout:
            lines.put(text)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    try:
        process.stdin.write(prompt)
        process.stdin.close()
    except OSError:
        pass
    reason, turns = None, 0
    while True:
        if time.monotonic() - started > timeout:
            reason = 'timeout'
        elif turns > max_turns:
            reason = 'max_turns'
        if reason:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass
            break
        try:
            line = lines.get(timeout=0.5)
        except queue.Empty:
            continue
        if line is None:
            break
        sink(line)
        try:
            turns += 1 if is_turn(json.loads(line)) else 0
        except ValueError:
            pass
    process.wait()
    return {'exit_code': process.returncode, 'reason': reason, 'seconds': time.monotonic() - started}


def is_turn_claude(event):
    return isinstance(event, dict) and event.get('type') == 'assistant'


def is_turn_codex(event):
    item = event.get('item') if isinstance(event, dict) else None
    return (isinstance(event, dict) and event.get('type') == 'item.completed' and isinstance(item, dict)
            and item.get('type') not in {'reasoning', None})


class RealHost:
    def __init__(self, kind, binary=None, effort=None):
        self.kind, self.effort = kind, effort
        binary = binary or kind
        if kind == 'claude':
            self.info = cli_info(binary, ['--help'], ['--version'])
        else:
            self.info = cli_info(binary, ['exec', '--help'], ['--version'])

    @property
    def version(self):
        return self.info['version']

    def command(self, model, condition, max_turns, budget_usd, work):
        if self.kind == 'claude':
            return claude_command(self.info, model, condition, max_turns, budget_usd, self.effort)
        return codex_command(self.info, model, work, self.effort)

    def execute(self, case, work, condition, model, limits, stream_path):
        if self.version is None:
            raise RuntimeError(f'{self.kind} CLI not found')
        argv, unsupported = self.command(model, condition, case['max_turns'], limits.get('budget_usd'), work)
        with open(stream_path, 'w', encoding='utf-8') as out:
            outcome = run_process(argv, case['prompt'], work, limits['timeout'], case['max_turns'],
                                  is_turn_claude if self.kind == 'claude' else is_turn_codex, out.write)
        return {**outcome, 'unsupported_flags': unsupported, 'argv': argv}


class FakeHost:
    """Replays scripted streams and file changes. For tests; never calls a model."""
    kind = 'fake'
    version = 'fake-1'
    info = {'binary': 'fake', 'version': 'fake-1', 'help': ''}

    def __init__(self, agent='good', fake_dir=None):
        self.agent, self.fake_dir = agent, fake_dir

    def script(self, case, model):
        base = Path(self.fake_dir) / case['id'] if self.fake_dir else case['dir'] / 'fake'
        data = json.loads((base / f'{self.agent}.json').read_text(encoding='utf-8'))
        if 'by_model' in data:
            data = data['by_model'].get(model, data.get('default'))
            if data is None:
                raise RuntimeError(f'no scripted agent for model {model}')
        return data

    def execute(self, case, work, condition, model, limits, stream_path):
        script = self.script(case, model)
        for name, text in script.get('files', {}).items():
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
        for name in script.get('delete', []):
            target = work / name
            shutil.rmtree(target) if target.is_dir() else target.unlink(missing_ok=True)
        events = [e for e in script['events'] if condition == 'with' or not e.get('only_with')]
        with open(stream_path, 'w', encoding='utf-8') as out:
            for event in events:
                out.write(json.dumps({k: v for k, v in event.items() if k != 'only_with'}) + '\n')
        return {'exit_code': 0, 'reason': None, 'seconds': 0.0, 'unsupported_flags': [], 'argv': ['fake', self.agent]}


# ---------------------------------------------------------------- event analysis

SKILL_PATH = re.compile(r'skills/([a-z0-9-]+)/SKILL\.md')
PATTERNS = {
    'test': re.compile(r'\b(unittest|pytest|nosetests|tox)\b|\b(npm|pnpm|yarn)\s+(run\s+)?test\b|\bcargo\s+test\b|\bgo\s+test\b'),
    'push': re.compile(r'\bgit\s+(-\S+\s+)*push\b|\bgh\s+pr\s+create\b'),
    'merge': re.compile(r'\bgit\s+(-\S+\s+)*merge\b|\bgh\s+pr\s+merge\b'),
    'network': re.compile(r'\b(curl|wget|ssh|scp|nc)\b|\bpip3?\s+install\b|\bnpm\s+(install|i)\b|\bgit\s+(clone|fetch|pull)\b'),
    'rm_rf': re.compile(r'\brm\s+(-\w*[rR]\w*[fF]|-\w*[fF]\w*[rR]|-[rR]\s+-f|-f\s+-[rR]|--recursive)'),
    'write': re.compile(r'(?<![>\d&])>{1,2}(?!&)\s*\S|\btee\b|\bsed\s+-i|\bmv\b|\bcp\b|\btouch\b|\bmkdir\b|\brm\b|-delete\b'),
}
WRITE_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
NETWORK_TOOLS = {'WebFetch', 'WebSearch'}


def tool_calls(events):
    """Normalise Claude (`assistant` tool_use) and Codex (`item.completed`) events to simple calls."""
    calls = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get('type') == 'assistant':
            for block in (event.get('message') or {}).get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'tool_use':
                    inp = block.get('input') or {}
                    calls.append({'name': block.get('name', ''), 'command': inp.get('command', '') or '',
                                  'path': inp.get('file_path') or inp.get('path') or '', 'skill': inp.get('skill')})
        elif event.get('type') == 'item.completed' and isinstance(event.get('item'), dict):
            item = event['item']
            kind = item.get('type')
            if kind == 'command_execution':
                calls.append({'name': 'Bash', 'command': item.get('command', '') or '', 'path': '', 'skill': None})
            elif kind == 'file_change':
                for change in item.get('changes') or [{}]:
                    calls.append({'name': 'Edit', 'command': '', 'path': change.get('path', ''), 'skill': None})
            elif kind == 'web_search':
                calls.append({'name': 'WebSearch', 'command': '', 'path': '', 'skill': None})
    return calls


def under(path, protected, work_prefix=''):
    if path.startswith('/'):  # An absolute path counts only when it is inside the agent copy.
        for prefix in {work_prefix, work_prefix.removeprefix('/private')} - {''}:
            if path.startswith(prefix.rstrip('/') + '/'):
                path = path[len(prefix.rstrip('/')) + 1:]
                break
        else:
            return False
    return any(path == spec or path.startswith(spec.rstrip('/') + '/') for spec in protected)


def derive(events, protected=(), work_prefix=''):
    """Skills loaded, action categories, turns, tokens and cost. Missing usage stays None, never estimated."""
    calls = tool_calls(events)
    skills, actions = set(), set()
    for call in calls:
        name, command = call['name'], call['command']
        if name == 'Skill' and call['skill']:
            skills.add(str(call['skill']).split(':')[-1])
        for text in (command, call['path']):
            skills.update(SKILL_PATH.findall(text or ''))
        if name in WRITE_TOOLS:
            actions.add('write')
            if call['path'] and under(call['path'], protected, work_prefix):
                actions.add('edit_protected')
        if name in NETWORK_TOOLS:
            actions.add('network')
        if name == 'Bash':
            for category, pattern in PATTERNS.items():
                if pattern.search(command):
                    actions.add(category)
    usage = {}
    cost, turns, answer, num_turns, assistant = None, 0, '', None, 0
    for event in events:
        if not isinstance(event, dict):
            continue
        kind = event.get('type')
        if kind == 'result':
            if isinstance(event.get('total_cost_usd'), (int, float)):
                cost = event['total_cost_usd']
            if isinstance(event.get('num_turns'), int):
                num_turns = event['num_turns']
            if isinstance(event.get('result'), str):
                answer = event['result']
            for key, value in (event.get('usage') or {}).items():
                if type(value) is int:
                    usage[key] = usage.get(key, 0) + value
        elif kind == 'assistant':
            assistant += 1
        elif kind == 'turn.completed':
            for key, value in (event.get('usage') or {}).items():
                if type(value) is int:
                    usage[key] = usage.get(key, 0) + value
        elif kind == 'item.completed' and isinstance(event.get('item'), dict):
            item = event['item']
            if item.get('type') == 'agent_message' and isinstance(item.get('text'), str):
                answer = item['text']
            if item.get('type') not in {'reasoning', None}:
                turns += 1
    if not answer:  # The last assistant text block when no result event carried the answer.
        for event in reversed(events):
            blocks = (event.get('message') or {}).get('content') if isinstance(event, dict) else None
            texts = [b.get('text', '') for b in blocks or [] if isinstance(b, dict) and b.get('type') == 'text']
            if texts:
                answer = texts[-1]
                break
    # Claude cache tokens are additive; Codex `cached_input_tokens` is already inside `input_tokens`.
    counted = {k: v for k, v in usage.items() if k in {'input_tokens', 'output_tokens', 'cache_creation_input_tokens',
                                                        'cache_read_input_tokens'}}
    total = sum(counted.values()) if counted else None
    return {'skills': sorted(skills), 'actions': sorted(actions), 'turns': num_turns if num_turns is not None else (
        assistant or turns or None), 'tokens': total, 'usage': usage or None, 'cost_usd': cost, 'answer': answer}


def render_transcript(events):
    lines = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get('type') == 'assistant':
            for block in (event.get('message') or {}).get('content') or []:
                if block.get('type') == 'tool_use':
                    detail = block['input'].get('command') or block['input'].get('file_path') or block['input'].get('skill') or ''
                    lines.append(f"[tool] {block['name']}: {detail}")
                elif block.get('type') == 'text':
                    lines.append(f"[assistant] {block.get('text', '')}")
        elif event.get('type') == 'item.completed':
            item = event.get('item') or {}
            lines.append(f"[{item.get('type')}] {item.get('command') or item.get('text') or ''}")
        elif event.get('type') == 'result':
            lines.append(f"[result] {event.get('result', '')}")
    text = '\n'.join(lines) or '(no output)'
    return text[:STREAM_LIMIT]


def read_events(path):
    events = []
    for line in Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def init_skills(events):
    """Skill names a Claude init event advertises, or None when the stream does not say."""
    for event in events:
        if isinstance(event, dict) and event.get('type') == 'system' and event.get('subtype') == 'init':
            value = event.get('skills')
            return list(value) if isinstance(value, list) else None
    return None


# ---------------------------------------------------------------- grading

def run_key(args, cwd):
    result = subprocess.run([sys.executable, '-I', str(ANSWER_KEY), *args], capture_output=True, text=True, cwd=cwd,
                            env=git_env())
    try:
        report = json.loads(result.stdout) if result.stdout.strip() else None
    except ValueError:
        report = None
    return result.returncode, report, result.stderr.strip()


def protected_mode(case):
    """restore (the default) or strict; a key without a mode is strict only where editing it is forbidden."""
    mode = case['key'].get('protected_mode')
    return mode or ('strict' if 'edit_protected' in case['forbidden_actions'] else 'restore')


def strict_paths(case):
    """Protected paths whose change counts as the forbidden action `edit_protected`."""
    return list(case['key'].get('protected') or []) if protected_mode(case) == 'strict' else []


def restore_protected(clone, base, names):
    """Commit the base version of each named protected file on top of the candidate, so the checks judge its code."""
    names = [n for n in names if git(clone, 'cat-file', '-e', f'{base}:{n}', check=False).returncode == 0]
    if names:
        git(clone, 'checkout', '-q', base, '--', *names)
        git(clone, 'commit', '-q', '--allow-empty', '--no-verify', '-m', 'restore protected files')


def grade_candidate(case, work, base, final, grade_dir, timeout=120):
    """Grade the committed final tree. The key and the hidden tests live only in `grade_dir`, outside the copy.

    Protected paths are restored to their base version before the checks run (strict: any change fails), and
    a change to one is reported as `protected_changed` for information."""
    key = case['key']
    clone = grade_dir / 'repo'
    git(grade_dir, 'clone', '-q', '--no-hardlinks', str(work), str(clone))
    report = {'result': 'pass', 'protected': {'status': 'pass', 'changed': []}, 'protected_changed': [], 'checks': []}
    if git(clone, 'merge-base', '--is-ancestor', base, final, check=False).returncode != 0:
        return {'result': 'unusable', 'error': 'the candidate does not descend from the fixture commit'}
    protected, restored = key.get('protected') or [], []
    if protected:
        mode = protected_mode(case)
        git(clone, 'checkout', '-q', '--detach', base)
        code, _, err = run_key(['freeze', '--repo', str(clone), '--task', case['id'], '--check', 'true',
                                '--protect-strict' if mode == 'strict' else '--protect',
                                *protected, '--out', str(grade_dir / 'protected.json')], grade_dir)
        if code != 0:
            return {'result': 'unusable', 'error': err}
        code, found, err = run_key(['check', '--key', str(grade_dir / 'protected.json'), '--candidate', final], grade_dir)
        if code == 2 or not found:
            return {'result': 'unusable', 'error': err}
        report['protected'] = found['protected']
        report['protected_changed'] = found.get('protected_changed', [])
        if code != 0:
            report['result'] = 'fail'
            return report
        restored = [c['path'] for c in report['protected_changed'] if c['reason'] in ('modified', 'missing')]
    git(clone, 'checkout', '-q', '--detach', final)
    restore_protected(clone, base, restored)
    hidden = case['dir'] / 'key' / key.get('hidden', 'hidden')
    if hidden.is_dir():
        shutil.copytree(hidden, clone, dirs_exist_ok=True)
        git(clone, 'add', '-A', '-f')
        git(clone, 'commit', '-q', '--allow-empty', '-m', 'hidden checks')
    head = git(clone, 'rev-parse', 'HEAD').stdout.strip()
    expect = [x for spec in key.get('expect_files') or [] for x in ['--expect-file', spec]]
    code, _, err = run_key(['freeze', '--repo', str(clone), '--task', case['id'], *sum((['--check', c] for c in key['checks']), []),
                            *expect, '--out', str(grade_dir / 'key.json')], grade_dir)
    if code != 0:
        return {'result': 'unusable', 'error': err}
    code, found, err = run_key(['check', '--key', str(grade_dir / 'key.json'), '--candidate', head, '--timeout', str(timeout)], grade_dir)
    if code == 2 or not found:
        return {'result': 'unusable', 'error': err}
    report['checks'] = found['checks']
    report['result'] = 'pass' if code == 0 else 'fail'
    return report


def answer_ok(case, answer):
    must = all(re.search(p, answer) for p in case.get('answer_must_match') or [])
    never = not any(re.search(p, answer) for p in case.get('answer_must_not_match') or [])
    return must and never


# ---------------------------------------------------------------- budget, cache, observations

class Budget:
    def __init__(self, max_runs=None, max_usd=None, per_run_usd=None):
        self.max_runs, self.max_usd, self.per_run_usd = max_runs, max_usd, per_run_usd
        self.runs, self.usd, self.unreported = 0, 0.0, 0

    def allows(self):
        return ((self.max_runs is None or self.runs < self.max_runs)
                and (self.max_usd is None or self.max_usd - self.usd > 0.005))

    def run_cap(self):
        if self.max_usd is None:
            return None
        remaining = self.max_usd - self.usd
        return round(min(remaining, self.per_run_usd) if self.per_run_usd else remaining, 4)

    def spend(self, cost):
        self.runs += 1
        if cost is not None:
            self.usd += cost
        elif self.max_usd is not None:  # Unknown cost: count the cap against the budget, report it as unknown.
            self.usd += self.run_cap() or 0
            self.unreported += 1


class Cache:
    def __init__(self, folder):
        self.folder = Path(folder)

    def key(self, case, host, model, version):
        text = '|'.join([case['id'], case['digest'], host, model, str(version)])
        return hashlib.sha256(text.encode()).hexdigest()[:24]

    def load(self, case, host, model, version):
        path = self.folder / 'baseline' / self.key(case, host, model, version) / 'entry.json'
        try:
            return json.loads(path.read_text(encoding='utf-8')), path.parent
        except (OSError, ValueError):
            return None, None

    def store(self, case, host, model, version, results, run_dir):
        entry_dir = self.folder / 'baseline' / self.key(case, host, model, version)
        shutil.rmtree(entry_dir, ignore_errors=True)
        (entry_dir / 'evidence').mkdir(parents=True)
        for result in results:
            for name in [result['transcript'], *result['artifacts'], result['event_stream']]:
                target = entry_dir / 'evidence' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(run_dir) / name, target)
        (entry_dir / 'entry.json').write_text(json.dumps({'results': results}, indent=2) + '\n', encoding='utf-8')

    def observations_path(self):
        return self.folder / 'observations.json'

    def observations(self):
        try:
            return json.loads(self.observations_path().read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}

    def observe(self, case, host, condition, model, outcome):
        data = self.observations()
        rows = [r for r in data.get(case['id'], []) if r.get('digest') == case['digest']]
        rows = [r for r in rows if (r['host'], r['condition'], r['model']) != (host, condition, model)]
        rows.append({'digest': case['digest'], 'host': host, 'condition': condition, 'model': model, 'outcome': outcome})
        data[case['id']] = rows
        self.folder.mkdir(parents=True, exist_ok=True)
        self.observations_path().write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

    def non_discriminating(self, case, host):
        rows = [r for r in self.observations().get(case['id'], []) if r.get('digest') == case['digest'] and r['host'] == host]
        return (len({r['condition'] for r in rows}) == 2 and len({r['model'] for r in rows}) >= 2
                and len({r['outcome'] for r in rows}) == 1)


# ---------------------------------------------------------------- runner

class Runner:
    def __init__(self, host, cases, out, cache, budget, cleanup, tmp_base=None, timeout=900, hook=None,
                 refresh_baseline=False, key_timeout=120):
        self.host, self.cases, self.out, self.cache, self.budget = host, cases, Path(out), cache, budget
        self.cleanup, self.tmp_base, self.timeout, self.hook = cleanup, tmp_base, timeout, hook
        self.refresh, self.key_timeout = refresh_baseline, key_timeout
        self.results = {}  # (condition, model) -> list of result dicts
        self.summary = {'cases': {}, 'skipped': [], 'cached': []}
        self.flags = {'unsupported': set()}
        self.stopped = False

    # one trial -------------------------------------------------------------
    def trial(self, case, condition, model, number):
        run_dir = self.out / condition / slug(model)
        for sub in ('events', 'transcripts', 'grades'):
            (run_dir / sub).mkdir(parents=True, exist_ok=True)
        stem = f'{case["id"]}-t{number}'
        work = self.cleanup.make('orbyn-eval-work-', self.tmp_base) / 'repo'
        grade_dir = self.cleanup.make('orbyn-eval-grade-', self.tmp_base)
        base = export_fixture(case, work)
        exclude_from_commit(work)
        assert_no_key(work, case)
        if condition == 'with':
            install_skills(work, self.host.kind if self.host.kind in {'claude', 'codex'} else 'claude')
            if not skill_files(work):
                raise RuntimeError('the with condition has no skills installed')
        elif skill_files(work) or (work / '.claude').exists() or (work / '.agents').exists():
            raise RuntimeError('the without condition must contain no skills')
        if self.hook:
            self.hook('ready', work=work, case=case, condition=condition)
        limits = {'timeout': self.timeout, 'budget_usd': self.budget.run_cap()}
        stream = run_dir / 'events' / f'{stem}.jsonl'
        started = time.monotonic()
        outcome = self.host.execute(case, work, condition, model, limits, stream)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        self.flags['unsupported'].update(outcome.get('unsupported_flags', []))
        events = read_events(stream)
        final = None
        try:
            git(work, 'add', '-A')
            git(work, 'commit', '-q', '--allow-empty', '--no-verify', '-m', 'final tree')
            final = git(work, 'rev-parse', 'HEAD').stdout.strip()
            changed = git(work, 'diff', '--name-only', base, final).stdout.split()
        except RuntimeError:
            changed = []
        protected = strict_paths(case)
        facts = derive(events, protected, str(work))
        if any(under(name, protected) for name in changed):
            facts['actions'] = sorted(set(facts['actions']) | {'edit_protected'})
        report = grade_candidate(case, work, base, final, grade_dir, self.key_timeout) if final else {
            'result': 'unusable', 'error': 'the final tree could not be committed'}
        forbidden = sorted(set(facts['actions']) & set(case['forbidden_actions']))
        key_ok = report['result'] == 'pass'
        answer_pass = answer_ok(case, facts['answer'])
        known = {e['name'] for e in evaluate.read(ROOT / 'skills/catalog.json')['skills']}
        selected = [s for s in facts['skills'] if s in known]
        routing_ok = (case['expected_skill'] in selected) if case['expected_skill'] else True
        passed = key_ok and answer_pass and not forbidden and (routing_ok or case['kind'] != 'routing')
        infra = (outcome['exit_code'] not in (0, None) and outcome['reason'] != 'max_turns' and self.host.kind != 'fake'
                 and not any(e.get('type') == 'result' for e in events if isinstance(e, dict)))
        isolation = None
        advertised = init_skills(events)
        if condition == 'without' and advertised:
            isolation = 'contaminated: init event lists skills'
        evidence = {'answer_key_result': report['result'], 'answer_check_result': 'pass' if answer_pass else 'fail',
                    'forbidden_actions': forbidden, 'unmet_routing': not routing_ok, 'report': report}
        grade_path = run_dir / 'grades' / f'{stem}.json'
        grade_path.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        transcript = run_dir / 'transcripts' / f'{stem}.txt'
        transcript.write_text(render_transcript(events), encoding='utf-8')
        rubric = {'answer_key': {'status': 'pass' if key_ok else 'fail', 'evidence': f'"answer_key_result": "{report["result"]}"'}}
        if case.get('answer_must_match') or case.get('answer_must_not_match'):
            rubric['answer_check'] = {'status': 'pass' if answer_pass else 'fail',
                                      'evidence': f'"answer_check_result": "{"pass" if answer_pass else "fail"}"'}
        self.budget.spend(facts['cost_usd'])
        result = {'case_id': case['id'], 'trial': number, 'status': 'not_run' if infra else 'completed',
                  'selected_skills': selected, 'actions': facts['actions'],
                  'transcript': f'transcripts/{stem}.txt', 'artifacts': [f'grades/{stem}.json'],
                  'reviewer': 'eval_run.py with answer_key.py (code grading)', 'rubric': rubric,
                  'duration_ms': elapsed_ms, 'total_tokens': facts['tokens'],
                  'event_stream': f'events/{stem}.jsonl', 'outcome': 'infra_error' if infra else ('pass' if passed else 'fail'),
                  'cost_usd': facts['cost_usd'], 'usage': facts['usage'], 'turns': facts['turns'],
                  'forbidden': forbidden, 'host_exit': outcome['exit_code'], 'stopped_for': outcome['reason'],
                  'other_skills': [s for s in facts['skills'] if s not in known], 'isolation': isolation,
                  'cli_version': self.host.version, 'final_commit': final}
        if infra:
            result['transcript'], result['artifacts'] = None, []
        return result

    def safe_trial(self, case, condition, model, number):
        work_count = len(self.cleanup.paths)
        try:
            return self.trial(case, condition, model, number)
        finally:  # Remove this trial's temporary folders as soon as its evidence is saved.
            for path in self.cleanup.paths[work_count:]:
                shutil.rmtree(path, ignore_errors=True)
            del self.cleanup.paths[work_count:]

    # one case at one tier --------------------------------------------------
    def tier(self, case, condition, model, trials):
        results, cached = [], False
        wanted = MAX_AUTO_RUNS if trials == 'auto' else trials
        if condition == 'without' and not self.refresh:
            entry, folder = self.cache.load(case, self.host.kind, model, self.host.version)
            if entry and (trials == 'auto' or len(entry['results']) >= trials):
                rows = entry['results'][:wanted]
                run_dir = self.out / condition / slug(model)
                for row in rows:
                    for name in [row['transcript'], *row['artifacts'], row['event_stream']]:
                        (run_dir / name).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(folder / 'evidence' / name, run_dir / name)
                self.summary['cached'].append({'case': case['id'], 'model': model})
                return [dict(r, cached=True) for r in rows]
        while len(results) < wanted:
            if not self.budget.allows():
                self.stopped = True
                break
            result = self.safe_trial(case, condition, model, len(results) + 1)
            results.append(result)
            if result['outcome'] == 'infra_error':
                break
            if trials == 'auto' and all(r['outcome'] == 'pass' for r in results):
                break  # one clean pass is enough; repeat only an unclear result
        if condition == 'without' and results and all(r['status'] == 'completed' for r in results) and not self.stopped:
            self.cache.store(case, self.host.kind, model, self.host.version, results, self.out / condition / slug(model))
        return results

    def run_case(self, case, condition, models, trials):
        info = {'tiers': [], 'cheapest_passed': None}
        for model in models:
            results = self.tier(case, condition, model, trials)
            if not results:
                break
            self.results.setdefault((condition, model), []).extend(results)
            done = [r for r in results if r['status'] == 'completed']
            passes = sum(r['outcome'] == 'pass' for r in done)
            tier = {'model': model, 'runs': len(results), 'passes': passes,
                    'outcomes': [r['outcome'] for r in results],
                    'pass_hat_k': bool(done) and passes == len(done) and len(done) == len(results),
                    'cached': any(r.get('cached') for r in results)}
            if len(results) > 1:
                tier['pass_pow_k'] = f'{passes}/{len(done)}'
            info['tiers'].append(tier)
            if done:
                self.cache.observe(case, self.host.kind, condition, model, 'pass' if tier['pass_hat_k'] else 'fail')
            if tier['pass_hat_k']:
                info['cheapest_passed'] = model
                break
            if any(r['outcome'] == 'infra_error' for r in results) or self.stopped:
                break
        self.summary['cases'].setdefault(case['id'], {})[condition] = info
        return info

    # output ------------------------------------------------------------------
    def finish(self, trials, ladder_name, models_plan):
        digest = evaluate.executable_suite(self.cases_dir)[1] if self.cases_dir else None
        revision = git(ROOT, 'rev-parse', 'HEAD').stdout.strip()
        dirty = bool(git(ROOT, 'status', '--porcelain').stdout.strip())
        written = []
        for (condition, model), results in sorted(self.results.items()):
            run_dir = self.out / condition / slug(model)
            ids = sorted({r['case_id'] for r in results})
            fixtures = {c['id']: c['digest'] for c in self.cases if c['id'] in ids}
            protocol = {'runner': 'eval_run.py', 'host': self.host.kind, 'cli_version': self.host.version, 'model': model,
                        'cases': fixtures, 'max_turns': {c['id']: c['max_turns'] for c in self.cases if c['id'] in ids},
                        'timeout_seconds': self.timeout,
                        'unsupported_flags': sorted(self.flags['unsupported']),
                        'isolation': 'with: library skills copied (evals excluded); without: none, verified by file scan',
                        'effects': 'no remote, no network or push permitted where the CLI allows'}
            protocol_bytes = (json.dumps(protocol, indent=2, sort_keys=True) + '\n').encode()
            (run_dir / 'protocol.json').write_bytes(protocol_bytes)
            counts = {i: max([r['trial'] for r in results if r['case_id'] == i]) for i in ids}
            run = {'schema_version': 1, 'suite': 'executable', 'suite_sha256': digest,
                   'suite_dir': str(self.cases_dir) if self.cases_dir != evaluate.EXECUTABLE else None,
                   'revision': revision, 'library_dirty': dirty,
                   'host': f'{self.host.kind} {self.host.version}', 'model': model,
                   'condition': 'candidate' if condition == 'with' else 'without-skills',
                   'trials': max(counts.values()), 'trials_by_case': counts, 'case_ids': ids,
                   'protocol_sha256': hashlib.sha256(protocol_bytes).hexdigest(),
                   'results': results}
            if not run['suite_dir']:
                del run['suite_dir']
            (run_dir / 'run.json').write_text(json.dumps(run, indent=2) + '\n', encoding='utf-8')
            written.append(str(run_dir / 'run.json'))
        self.summary.update({'run_files': written, 'runs_used': self.budget.runs, 'budget_usd_counted': round(self.budget.usd, 4),
                             'runs_with_unreported_cost': self.budget.unreported, 'cli_version': self.host.version,
                             'unsupported_flags': sorted(self.flags['unsupported']), 'stopped_by_budget': self.stopped,
                             'ladder': ladder_name, 'models': models_plan, 'trials': trials})
        (self.out / 'summary.json').write_text(json.dumps(self.summary, indent=2) + '\n', encoding='utf-8')
        return self.summary

    cases_dir = None


# ---------------------------------------------------------------- subagent mode
# The lead agent spawns one host subagent per trial (its own Agent tool or Codex spawn_agent) and Python never calls a
# model: `prepare` builds the repository and the brief, the subagent works in it, `grade` commits and grades it.

SUBAGENT_HOST = 'subagent'
UNCLEAN = 'not clean, subagents see the workspace skills and instructions'
SUBAGENT_NOTE = 'Work only inside that folder. Do not push anything.'


def utc_now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def subagent_case(args):
    cases = evaluate.load_executable(args.cases_dir)
    found = [c for c in cases if c['id'] == args.case]
    if not found:
        raise Refused(f'unknown case: {args.case}')
    return found[0]


def subagent_prepare(args):
    case = subagent_case(args)
    model = check_model(args.model, args.allow_lead_tier)
    out = Path(args.out).expanduser().resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refused(f'--out must be new or empty: {out}')
    out.mkdir(parents=True, exist_ok=True)
    repo = out / 'repo'
    base = export_fixture(case, repo)
    exclude_from_commit(repo)
    assert_no_key(repo, case)  # The key and the hidden tests never go inside the agent's repository.
    brief = f'{case["prompt"].rstrip()}\n\nThe repository is at {repo}. {SUBAGENT_NOTE}\n'
    (out / 'brief.txt').write_text(brief, encoding='utf-8')
    trial = {'schema_version': 1, 'host': SUBAGENT_HOST, 'case': case['id'], 'case_digest': case['digest'],
             'condition': args.condition, 'model': model, 'base': base, 'created': utc_now(), 'repo': str(repo),
             'cases_dir': None if Path(args.cases_dir).resolve() == evaluate.EXECUTABLE.resolve() else str(Path(args.cases_dir).resolve()),
             'isolation': UNCLEAN if args.condition == 'without' else None}
    (out / 'trial.json').write_text(json.dumps(trial, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'trial': str(out), 'brief': str(out / 'brief.txt'), 'repo': str(repo), 'case': case['id'],
                      'condition': args.condition, 'model': model, 'isolation': trial['isolation']}, indent=2))
    return 0


def read_transcript(path):
    """Events when the file is JSON lines of host events, else the lead's plain text, which is the final answer."""
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    events = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            return [], text
        events.append(value)
    return ([e for e in events if isinstance(e, dict)], '') if events and all(isinstance(e, dict) for e in events) else ([], text)


def subagent_grade(args):
    trial_dir = Path(args.trial).expanduser().resolve()
    try:
        trial = json.loads((trial_dir / 'trial.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise Refused(f'cannot read trial.json: {error}')
    if trial.get('host') != SUBAGENT_HOST or not all(isinstance(trial.get(k), str) for k in ('case', 'condition', 'model', 'base')):
        raise Refused('trial.json is not a subagent trial')
    cases_dir = Path(trial['cases_dir']) if trial.get('cases_dir') else evaluate.EXECUTABLE
    case = next((c for c in evaluate.load_executable(cases_dir) if c['id'] == trial['case']), None)
    if case is None or case['digest'] != trial.get('case_digest'):
        raise Refused('the case changed since prepare; prepare the trial again')
    work, base, condition = trial_dir / 'repo', trial['base'], trial['condition']
    if not (work / '.git').is_dir() or git(work, 'cat-file', '-e', f'{base}^{{commit}}', check=False).returncode != 0:
        raise Refused('the trial repository is missing or lost its base commit')
    git(work, 'add', '-A')
    git(work, 'commit', '-q', '--allow-empty', '--no-verify', '-m', 'final tree')  # fixed identity, hooks disabled
    final = git(work, 'rev-parse', 'HEAD').stdout.strip()
    changed = git(work, 'diff', '--name-only', base, final).stdout.split()
    events, answer_text = read_transcript(args.transcript) if args.transcript else ([], '')
    protected = strict_paths(case)
    facts = derive(events, protected, str(work))
    if changed:
        facts['actions'] = sorted(set(facts['actions']) | {'write'})
    if any(under(name, protected) for name in changed):
        facts['actions'] = sorted(set(facts['actions']) | {'edit_protected'})
    answer = facts['answer'] or answer_text
    known = {e['name'] for e in evaluate.read(ROOT / 'skills/catalog.json')['skills']}
    reported = [s.strip() for s in (args.skills or '').split(',') if s.strip()]
    skills = sorted(set(facts['skills']) | set(reported))
    selected = [s for s in skills if s in known]
    grade_dir = Path(tempfile.mkdtemp(prefix='orbyn-eval-grade-'))
    try:
        report = grade_candidate(case, work, base, final, grade_dir)
    finally:
        shutil.rmtree(grade_dir, ignore_errors=True)
    if report['result'] == 'unusable':
        raise RuntimeError(f'grading could not run: {report.get("error")}')
    forbidden = sorted(set(facts['actions']) & set(case['forbidden_actions']))
    key_ok = report['result'] == 'pass'
    answer_pass = answer_ok(case, answer)
    routing_ok = (case['expected_skill'] in selected) if case['expected_skill'] else True
    passed = key_ok and answer_pass and not forbidden and (routing_ok or case['kind'] != 'routing')
    stem = f'{case["id"]}-t1'
    for sub in ('transcripts', 'grades', 'events'):
        (trial_dir / sub).mkdir(exist_ok=True)
    observed = 'transcript events and the final tree diff' if events else 'the final tree diff only (no event transcript)'
    note = (f'[subagent trial] case {case["id"]}, model {trial["model"]}, condition {condition}\n'
            f'[observed] actions come from {observed}; skills as reported by the lead: {", ".join(reported) or "none"}\n')
    transcript = trial_dir / 'transcripts' / f'{stem}.txt'
    transcript.write_text(note + (render_transcript(events) if events else (answer_text or '(no transcript supplied)')),
                          encoding='utf-8')
    event_stream = None
    if events:
        event_stream = f'events/{stem}.jsonl'
        shutil.copy2(args.transcript, trial_dir / event_stream)
    evidence = {'answer_key_result': report['result'], 'answer_check_result': 'pass' if answer_pass else 'fail',
                'forbidden_actions': forbidden, 'unmet_routing': not routing_ok, 'report': report}
    (trial_dir / 'grades' / f'{stem}.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    rubric = {'answer_key': {'status': 'pass' if key_ok else 'fail', 'evidence': f'"answer_key_result": "{report["result"]}"'}}
    if case.get('answer_must_match') or case.get('answer_must_not_match'):
        rubric['answer_check'] = {'status': 'pass' if answer_pass else 'fail',
                                  'evidence': f'"answer_check_result": "{"pass" if answer_pass else "fail"}"'}
    tokens = args.tokens if args.tokens is not None else facts['tokens']  # as reported by the lead; never estimated
    isolation = trial.get('isolation')
    result = {'case_id': case['id'], 'trial': 1, 'status': 'completed', 'selected_skills': selected,
              'actions': facts['actions'], 'transcript': f'transcripts/{stem}.txt', 'artifacts': [f'grades/{stem}.json'],
              'reviewer': 'eval_run.py subagent grade with answer_key.py (code grading)', 'rubric': rubric,
              'duration_ms': None, 'total_tokens': tokens, 'event_stream': event_stream,
              'outcome': 'pass' if passed else 'fail', 'cost_usd': facts['cost_usd'], 'usage': facts['usage'],
              'turns': facts['turns'], 'forbidden': forbidden, 'host_exit': None, 'stopped_for': None,
              'other_skills': [s for s in skills if s not in known], 'isolation': isolation, 'cli_version': None,
              'final_commit': final, 'protected_changed': report.get('protected_changed', [])}
    digest = evaluate.executable_suite(cases_dir)[1]
    protocol = {'runner': 'eval_run.py subagent', 'host': SUBAGENT_HOST, 'model': trial['model'],
                'cases': {case['id']: case['digest']}, 'max_turns': {case['id']: case['max_turns']},
                'isolation': 'the repository copy holds no skills; the subagent sees the lead workspace skills and instructions',
                'effects': 'no remote in the copy; actions are observed from the final tree and any transcript supplied'}
    protocol_bytes = (json.dumps(protocol, indent=2, sort_keys=True) + '\n').encode()
    (trial_dir / 'protocol.json').write_bytes(protocol_bytes)
    run = {'schema_version': 1, 'suite': 'executable', 'suite_sha256': digest,
           'revision': git(ROOT, 'rev-parse', 'HEAD').stdout.strip(),
           'library_dirty': bool(git(ROOT, 'status', '--porcelain').stdout.strip()),
           'host': SUBAGENT_HOST, 'model': trial['model'],
           'condition': 'candidate' if condition == 'with' else 'without-skills', 'trials': 1,
           'trials_by_case': {case['id']: 1}, 'case_ids': [case['id']],
           'protocol_sha256': hashlib.sha256(protocol_bytes).hexdigest(), 'results': [result]}
    if cases_dir != evaluate.EXECUTABLE:
        run['suite_dir'] = str(cases_dir)
    if isolation:
        run['isolation'] = isolation
    (trial_dir / 'run.json').write_text(json.dumps(run, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'run': str(trial_dir / 'run.json'), 'case': case['id'], 'outcome': result['outcome'],
                      'answer_key_result': report['result'], 'protected_changed': result['protected_changed'],
                      'forbidden': forbidden, 'total_tokens': tokens, 'isolation': isolation}, indent=2))
    return 0


def subagent_parser():
    p = argparse.ArgumentParser(prog='eval_run.py', description='Prepare and grade a trial a host subagent runs. No model is called.')
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('prepare', help='export the fixture and write brief.txt and trial.json')
    a.add_argument('--case', required=True)
    a.add_argument('--condition', choices=['with', 'without'], required=True)
    a.add_argument('--model', required=True, help='the model the subagent will run on (haiku, sonnet, luna, terra)')
    a.add_argument('--out', type=Path, required=True)
    a.add_argument('--cases-dir', type=Path, default=evaluate.EXECUTABLE)
    a.add_argument('--allow-lead-tier', action='store_true')
    g = sub.add_parser('grade', help='commit the final tree, grade it and write run.json')
    g.add_argument('--trial', type=Path, required=True)
    g.add_argument('--transcript', type=Path, help='the subagent transcript (JSON lines) or its final answer as text')
    g.add_argument('--skills', help='comma-separated skills the subagent loaded, as the lead observed them')
    g.add_argument('--tokens', type=int, help='total tokens the subagent result reported; omit when it reported none')
    return p


def subagent_main(argv):
    args = subagent_parser().parse_args(argv)
    try:
        if args.command == 'grade' and args.tokens is not None and args.tokens < 0:
            raise Refused('--tokens must not be negative')
        return subagent_prepare(args) if args.command == 'prepare' else subagent_grade(args)
    except Refused as error:
        print(f'eval_run: refused: {error}', file=sys.stderr)
        return 2
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f'eval_run: {error}', file=sys.stderr)
        return 2


# ---------------------------------------------------------------- plan and cli

def build_host(args):
    if args.host == 'fake':
        return FakeHost(args.fake_agent, args.fake_dir)
    return RealHost(args.host, args.claude_bin if args.host == 'claude' else args.codex_bin, args.effort)


def resolve_models(args):
    explicit = bool(args.model)
    if args.model and args.ladder:
        raise Refused('use --model or --ladder, not both')
    if args.model:
        models = [check_model(m, args.allow_lead_tier) for m in args.model.split(',')]
    elif args.ladder:
        models = ladder_models(args.ladder, args.allow_lead_tier)
    else:
        models = [DEFAULT_MODEL[args.host]]
    for model in models:
        check_model(model, args.allow_lead_tier)
    return models, explicit


def selected_cases(args):
    cases = evaluate.load_executable(args.cases_dir)
    if args.case:
        unknown = set(args.case) - {c['id'] for c in cases}
        if unknown:
            raise Refused(f'unknown case: {", ".join(sorted(unknown))}')
        cases = [c for c in cases if c['id'] in args.case]
    elif args.split != 'all':
        cases = [c for c in cases if c['holdout'] == (args.split == 'holdout')]
    return cases


def make_plan(args, cases, cache, models, explicit):
    conditions = ['with', 'without'] if args.condition == 'both' else [args.condition]
    trials = 'auto' if args.trials == 'auto' else int(args.trials)
    per_case = MAX_AUTO_RUNS if trials == 'auto' else trials
    plan = {'host': args.host, 'conditions': conditions, 'models': models, 'trials': trials, 'cases': [], 'skipped': [],
            'max_runs': 0, 'max_budget_usd': args.max_budget_usd, 'max_runs_cap': args.max_runs, 'notes': []}
    if args.allow_lead_tier and any(LEAD_RE.search(m) for m in models):
        plan['notes'].append(LEAD_WARNING)
    for case in cases:
        if not args.include_non_discriminating and cache.non_discriminating(case, args.host):
            plan['skipped'].append({'case': case['id'], 'reason': 'non-discriminating in a recorded run'})
            continue
        tiers = case_models(case, args.host, models, bool(args.ladder), explicit)
        if case['kind'] == 'routing' and args.ladder and not explicit:
            plan['notes'].append(f'{case["id"]}: {ROUTING_NOTE}')
        plan['cases'].append({'id': case['id'], 'kind': case['kind'], 'holdout': case['holdout'], 'tiers': tiers})
        plan['max_runs'] += len(tiers) * per_case * len(conditions)
    plan['notes'] = list(dict.fromkeys(plan['notes']))
    return plan


def print_plan(plan, live):
    print('Dry plan. No model is started.' if not live else 'Plan.')
    print(f"host: {plan['host']}  conditions: {', '.join(plan['conditions'])}  trials: {plan['trials']}")
    for entry in plan['cases']:
        print(f"  {entry['id']} ({entry['kind']}{', holdout' if entry['holdout'] else ''}): tiers {' -> '.join(entry['tiers'])}")
    for skipped in plan['skipped']:
        print(f"  skipped {skipped['case']}: {skipped['reason']}")
    print(f"models: {', '.join(plan['models'])}")
    print(f"maximum run count: {plan['max_runs']} (before cached baselines and early stops)")
    cap = []
    if plan['max_budget_usd'] is not None:
        cap.append(f"${plan['max_budget_usd']:.2f}")
    if plan['max_runs_cap'] is not None:
        cap.append(f"{plan['max_runs_cap']} runs")
    print('budget cap: ' + (', '.join(cap) if cap else 'none set; --live is refused without one'))
    for note in plan['notes']:
        print(note)


def live_refusal(args):
    if not args.live:
        return None
    if args.max_runs is None and args.max_budget_usd is None:
        return '--live needs --max-runs (any host) or --max-budget-usd (claude)'
    if args.max_budget_usd is not None and args.host != 'claude':
        return '--max-budget-usd applies to claude only; use --max-runs'
    if not args.out:
        return '--live needs --out'
    return None


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--host', choices=['claude', 'codex', 'fake'], required=True)
    p.add_argument('--condition', choices=['with', 'without', 'both'], default='with')
    p.add_argument('--model', help='model id or alias (comma-separated for several); opus, sol, fable, astra are refused')
    p.add_argument('--ladder', choices=['claude', 'codex'], help='climb haiku->sonnet or luna->terra on failure')
    p.add_argument('--allow-lead-tier', action='store_true', help='also allow opus or sol (about twice the cost); fable and astra never')
    p.add_argument('--trials', default='auto', help='auto (1 run, repeat up to 3 only when unclear) or a number')
    p.add_argument('--cases-dir', type=Path, default=evaluate.EXECUTABLE)
    p.add_argument('--case', action='append', default=[])
    p.add_argument('--split', choices=['development', 'holdout', 'all'], default='development')
    p.add_argument('--out', type=Path)
    p.add_argument('--live', action='store_true', help='actually run; without it only a dry plan is printed')
    p.add_argument('--max-budget-usd', type=float)
    p.add_argument('--max-runs', type=int)
    p.add_argument('--run-budget-usd', type=float, help='per-run cap passed to claude (default: total / planned runs)')
    p.add_argument('--timeout', type=int, default=900)
    p.add_argument('--cache-dir', type=Path, default=DEFAULT_CACHE)
    p.add_argument('--refresh-baseline', action='store_true')
    p.add_argument('--include-non-discriminating', action='store_true')
    p.add_argument('--effort', help='effort level passed to the host when its help lists the flag')
    p.add_argument('--claude-bin')
    p.add_argument('--codex-bin')
    p.add_argument('--fake-agent', default='good')
    p.add_argument('--fake-dir', type=Path)
    p.add_argument('--tmp-dir', type=Path, help='parent for temporary trial folders')
    return p


def main(argv=None, hook=None):
    raw = sys.argv[1:] if argv is None else list(argv)
    if raw and raw[0] in {'prepare', 'grade'}:
        return subagent_main(raw)
    args = build_parser().parse_args(argv)
    try:
        if args.trials != 'auto' and (not args.trials.isdigit() or not 1 <= int(args.trials) <= 20):
            raise Refused('--trials must be auto or 1-20')
        models, explicit = resolve_models(args)
        cases = selected_cases(args)
        cache = Cache(args.cache_dir)
        plan = make_plan(args, cases, cache, models, explicit)
        print_plan(plan, args.live)
        if not args.live:
            return 0
        reason = live_refusal(args)
        if reason:
            raise Refused(reason)
        if args.out.exists() and any(args.out.iterdir()):
            raise Refused(f'--out must be new or empty: {args.out}')
        args.out.mkdir(parents=True, exist_ok=True)
        host = build_host(args)
        if args.host != 'fake' and host.version is None:
            raise Refused(f'{args.host} CLI not found')
        planned = max(plan['max_runs'], 1)
        per_run = args.run_budget_usd or (args.max_budget_usd / planned if args.max_budget_usd else None)
        runner = Runner(host, cases, args.out, cache, Budget(args.max_runs, args.max_budget_usd, per_run), Cleanup(),
                        args.tmp_dir, args.timeout, hook, args.refresh_baseline)
        runner.cases_dir = args.cases_dir
        by_id = {c['id']: c for c in cases}
        conditions = plan['conditions']
        try:
            for condition in conditions:
                for entry in plan['cases']:
                    if runner.stopped:
                        break
                    runner.run_case(by_id[entry['id']], condition, entry['tiers'],
                                    'auto' if plan['trials'] == 'auto' else plan['trials'])
        finally:
            runner.cleanup.close()
        summary = runner.finish(plan['trials'], args.ladder, models)
        print(json.dumps({k: summary[k] for k in ('runs_used', 'budget_usd_counted', 'run_files', 'stopped_by_budget')}, indent=2))
        return 0
    except Refused as error:
        print(f'eval_run: refused: {error}', file=sys.stderr)
        return 2
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f'eval_run: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
