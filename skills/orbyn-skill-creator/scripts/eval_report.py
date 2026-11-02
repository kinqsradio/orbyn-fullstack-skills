#!/usr/bin/env python3
"""Report executable eval results like CI: a compact summary, a commit status, one PR comment, history and a dashboard.

Evals run locally on any host (Claude, Codex or another) with eval_run.py. This tool turns their run.json files into
a summary with no transcripts and no key text, and sends it to GitHub through the `gh` CLI. Standard library only;
it never starts a model. Nothing is sent unless --send is given; the default is a dry run that prints every write.
Reads (the PR head, the existing comment, history) still go through `gh api`.

Commands
  summarize --run run.json... --out summary.json [--pr N] [--main]
  publish   --summary summary.json (--pr N | --history-only) [--repo owner/name] [--send|--dry-run]
  dashboard --history DIR --out dashboard.html [--publish --repo owner/name [--send|--dry-run]]
  fetch     --repo owner/name --out DIR            read history/*.json from the eval-results branch
  affected  [--base origin/main] [--paths P...]    executable cases a diff affects

Exit status: 0 ok, 1 refused (wrong head, over a limit, bad input), 2 could not run (no gh, bad arguments).
"""
import argparse
import base64
import datetime
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXECUTABLE = ROOT / 'skills/orbyn-skill-creator/evals/executable'
BRANCH = 'eval-results'
CONTEXT = 'agent-evals'
MARKER = '<!-- orbyn-agent-evals -->'
COMMENT_LIMIT = 65536
STATUS_LIMIT = 140
SUMMARY_LIMIT = 1_000_000
RUN_LIMIT = 50_000_000
CONDITIONS = {'candidate': 'with', 'without-skills': 'without'}
TIER_ORDER = ['haiku', 'sonnet', 'opus', 'gpt-6-luna', 'gpt-6.1-terra', 'gpt-6.1-sol']
SHA = re.compile(r'[0-9a-f]{40}')
REPO = re.compile(r'[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}')
SAFE_PATH = re.compile(r'[A-Za-z0-9._/-]{1,200}')
CASE_ID = re.compile(r'[a-z0-9-]{1,80}')
PATH_KEYS = {'evidence', 'run_files'}
DEFAULT_DEPENDS = ('skills/orbyn-workflow/', 'docs/agents/models.json')


class Refused(Exception):
    """The input or the target breaks a rule; nothing is sent (exit 1)."""


class CannotRun(Exception):
    """The tool could not do its job (exit 2)."""


# ------------------------------------------------------------ sanitising

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b.?')
SECRETS = [
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)', re.S),
    re.compile(r'\b(?:sk|pk|rk)-[A-Za-z0-9_-]{8,}'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}'),
    re.compile(r'\bAKIA[0-9A-Z]{12,}'),
    re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}'),
    re.compile(r'\bAIza[0-9A-Za-z_-]{30,}'),
    re.compile(r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}'),
    re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}'),
]
LABELLED = re.compile(r'(?i)\b((?:api[_-]?key|secret|token|passw(?:or)?d|authorization|credential)s?\s*[:=]\s*)(?:"[^"]*"|\'[^\']*\'|\S+)')
LONG_TOKEN = re.compile(r'(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])')


def clean_text(value, limit=500, paths=False):
    """One line of printable text: ANSI and control characters removed, secret-looking text redacted, home folder hidden."""
    text = ANSI.sub('', str(value))
    text = ''.join(' ' if c in '\r\n\t' else c for c in text if c in '\r\n\t' or unicodedata.category(c) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn', 'Zl', 'Zp'))
    home = str(Path.home())
    if len(home) > 1:
        text = text.replace(home, '~')
    for pattern in SECRETS:
        text = pattern.sub('[redacted]', text)
    text = LABELLED.sub(lambda m: m.group(1) + '[redacted]', text)
    if not paths:
        text = LONG_TOKEN.sub(lambda m: m.group() if re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', m.group()) else '[redacted]', text)
    return text[:limit]


def clean_tree(value, key=None):
    if isinstance(value, str):
        return clean_text(value, 500, paths=key in PATH_KEYS)
    if isinstance(value, list):
        return [clean_tree(v, key) for v in value]
    if isinstance(value, dict):
        return {clean_text(k, 80): clean_tree(v, k) for k, v in value.items()}
    return value


def md(value, limit=80):
    """Text for a Markdown table cell: cleaned, one line, nothing that renders as markup, a mention or a link."""
    text = clean_text(value, limit).replace('@', '(at)')
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;')
    return re.sub(r'([\\`*_\[\]~#])', r'\\\1', text)


def number(value):
    return value if type(value) in (int, float) and value >= 0 else None


def total(values):
    known = [v for v in values if v is not None]
    return sum(known) if known else None


# ------------------------------------------------------------ summarize

def read_json(path, limit=RUN_LIMIT):
    path = Path(path)
    try:
        if path.stat().st_size > limit:
            raise Refused(f'{path.name} is larger than {limit} bytes')
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise Refused(f'{path}: cannot read as JSON ({error})')


def case_facts(run, case_id):
    """kind and holdout from the case's own case.json (never its key folder); None when the suite is not on disk."""
    folder = Path(run['suite_dir']) if isinstance(run.get('suite_dir'), str) else EXECUTABLE
    path = folder / case_id / 'case.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8')) if CASE_ID.fullmatch(case_id) and path.is_file() else {}
    except (OSError, ValueError):
        data = {}
    return (data.get('kind') if data.get('kind') in ('routing', 'outcome') else None,
            data.get('holdout') if type(data.get('holdout')) is bool else None)


def tier_rank(model):
    return (TIER_ORDER.index(model), model) if model in TIER_ORDER else (len(TIER_ORDER), model)


def stats_for(results):
    done = [r for r in results if r.get('status') == 'completed']
    passes = sum(r.get('outcome') == 'pass' for r in done)
    fresh = [r for r in results if not r.get('cached')]
    return {'runs': len(results), 'fresh_runs': len(fresh), 'completed': len(done), 'passes': passes,
            'errors': sum(r.get('outcome') == 'infra_error' for r in results),
            'pass_hat_k': bool(done) and passes == len(done) and len(done) == len(results),
            'tokens': total(number(r.get('total_tokens')) for r in fresh),
            'cost_usd': total(number(r.get('cost_usd')) for r in fresh),
            'cost_unreported': sum(number(r.get('cost_usd')) is None for r in fresh)}


def cheapest(tiers, condition):
    passed = [m for m, t in tiers.items() if t.get(condition) and t[condition]['pass_hat_k']]
    return min(passed, key=tier_rank) if passed else None


def condition_result(tiers, condition):
    seen = [t[condition] for t in tiers.values() if t.get(condition)]
    if not seen:
        return None
    if cheapest(tiers, condition):
        return 'pass'
    return 'fail' if any(s['completed'] for s in seen) else 'error'


def summarize(run_paths, pr=None, is_main=False):
    runs, names = [], []
    for path in run_paths:
        run = read_json(path)
        if not isinstance(run, dict) or run.get('schema_version') != 1 or not isinstance(run.get('results'), list):
            raise Refused(f'{path}: not an eval_run.py run.json (schema_version 1 with results)')
        if run.get('condition') not in CONDITIONS or not isinstance(run.get('model'), str):
            raise Refused(f'{path}: unknown condition or missing model')
        runs.append(run)
        parts = Path(path).resolve().parts
        names.append('/'.join(parts[-3:]) if len(parts) >= 3 else Path(path).name)
    if not runs:
        raise Refused('summarize needs at least one --run')
    commits = {r.get('revision') for r in runs}
    if len(commits) != 1 or not SHA.fullmatch(str(next(iter(commits)))):
        raise Refused('every run must come from one full 40-character commit')
    kinds = {str(r.get('host', '')).split(' ', 1)[0] for r in runs}
    if len(kinds) != 1:
        raise Refused('runs from different hosts must be summarized separately')
    versions = {str(r.get('host', '')).split(' ', 1)[1] if ' ' in str(r.get('host', '')) else '' for r in runs}
    cases = {}
    for run, name in zip(runs, names):
        condition = CONDITIONS[run['condition']]
        by_case = {}
        for result in run['results']:
            if isinstance(result, dict) and isinstance(result.get('case_id'), str) and CASE_ID.fullmatch(result['case_id']):
                by_case.setdefault(result['case_id'], []).append(result)
        for case_id, results in by_case.items():
            entry = cases.setdefault(case_id, {'tiers': {}, 'evidence': []})
            entry['tiers'].setdefault(run['model'], {})[condition] = stats_for(results)
            base = f'{name.rsplit("/", 1)[0]}'
            for result in results:
                for field in ('transcript', 'event_stream'):
                    if isinstance(result.get(field), str):
                        entry['evidence'].append(f'{base}/{result[field]}')
                entry['evidence'].extend(f'{base}/{a}' for a in result.get('artifacts', []) if isinstance(a, str))
            entry['run'] = run
    out_cases = []
    for case_id in sorted(cases):
        entry = cases[case_id]
        tiers = {m: entry['tiers'][m] for m in sorted(entry['tiers'], key=tier_rank)}
        kind, holdout = case_facts(entry['run'], case_id)
        with_result, without_result = condition_result(tiers, 'with'), condition_result(tiers, 'without')
        tier = cheapest(tiers, 'with')
        decider = tier or max((m for m in tiers if tiers[m].get('with')), key=tier_rank, default=None)
        deciding = tiers[decider]['with'] if decider else None
        if with_result in (None, 'error'):
            verdict = 'not run'
        elif without_result is None:
            verdict = 'no baseline'
        elif with_result == 'pass' and without_result == 'fail':
            verdict = 'helps'
        elif with_result == 'fail' and without_result == 'pass':
            verdict = 'regression'
        else:
            verdict = 'same'
        stats = [s for t in tiers.values() for s in t.values()]
        out_cases.append({
            'id': case_id, 'kind': kind, 'holdout': holdout, 'result': with_result or 'not_run', 'cheapest_tier': tier,
            'without': {'result': without_result, 'cheapest_tier': cheapest(tiers, 'without')}, 'verdict': verdict,
            'pass_hat_k': bool(deciding and deciding['pass_hat_k']),
            'pass_pow_k': f'{deciding["passes"]}/{deciding["completed"]}' if deciding else None,
            'tiers': tiers, 'runs': sum(s['fresh_runs'] for s in stats), 'tokens': total(s['tokens'] for s in stats),
            'cost_usd': total(s['cost_usd'] for s in stats), 'evidence': sorted(set(entry['evidence']))[:40]})
    stats = [s for c in out_cases for t in c['tiers'].values() for s in t.values()]
    errors = sum(c['result'] in ('error', 'not_run') for c in out_cases)
    summary = {
        'schema_version': 1, 'created': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'commit': next(iter(commits)), 'pr': pr, 'is_main': bool(is_main), 'library_dirty': any(r.get('library_dirty') for r in runs),
        'host': next(iter(kinds)), 'cli_version': sorted(versions)[0] if len(versions) == 1 else 'mixed',
        'models': sorted({r['model'] for r in runs}, key=tier_rank), 'suite_sha256': sorted({str(r.get('suite_sha256')) for r in runs})[0],
        'cases': out_cases, 'totals': {
            'cases': len(out_cases), 'passed': sum(c['result'] == 'pass' for c in out_cases),
            'failed': sum(c['result'] == 'fail' for c in out_cases), 'errors': errors,
            'runs': sum(s['fresh_runs'] for s in stats), 'cached_runs': sum(s['runs'] - s['fresh_runs'] for s in stats),
            'tokens': total(s['tokens'] for s in stats), 'cost_usd': total(s['cost_usd'] for s in stats),
            'runs_cost_unreported': sum(s['cost_unreported'] for s in stats)},
        'run_files': sorted(set(names)),
        'evidence_note': 'Paths are relative to the local eval output folder; evidence stays on the host that ran it.'}
    return validate_summary(summary)


def validate_summary(data):
    """A canonical, cleaned copy of a summary with only known keys and types; Refused when it is not one."""
    def need(ok, what):
        if not ok:
            raise Refused(f'summary: {what}')
    need(isinstance(data, dict) and data.get('schema_version') == 1, 'schema_version must be 1')
    need(isinstance(data.get('commit'), str) and SHA.fullmatch(data['commit']), 'commit must be a full 40-character hash')
    need(isinstance(data.get('created'), str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T[\d:]{8}Z', data['created']), 'created must be a UTC time')
    pr = data.get('pr')
    need(pr is None or (type(pr) is int and pr > 0), 'pr must be a positive integer or null')
    need(isinstance(data.get('cases'), list) and len(data['cases']) <= 500, 'cases must be a list of at most 500')
    need(isinstance(data.get('totals'), dict), 'totals missing')
    cases = []
    for c in data['cases']:
        need(isinstance(c, dict) and isinstance(c.get('id'), str) and CASE_ID.fullmatch(c['id']), 'case id must be lowercase letters, digits and dashes')
        need(c.get('result') in ('pass', 'fail', 'error', 'not_run'), f'{c["id"]}: unknown result')
        need(isinstance(c.get('tiers'), dict) and len(c['tiers']) <= 20, f'{c["id"]}: tiers must be an object')
        tiers = {}
        for model, by in c['tiers'].items():
            need(isinstance(by, dict), f'{c["id"]}: bad tier')
            tiers[model] = {}
            for cond in ('with', 'without'):
                s = by.get(cond)
                if s is None:
                    continue
                need(isinstance(s, dict) and all(type(s.get(k)) is int and s[k] >= 0 for k in ('runs', 'completed', 'passes')), f'{c["id"]}: bad run counts')
                tiers[model][cond] = {'runs': s['runs'], 'fresh_runs': s.get('fresh_runs') if type(s.get('fresh_runs')) is int else s['runs'],
                                      'completed': s['completed'], 'passes': s['passes'], 'errors': s.get('errors') if type(s.get('errors')) is int else 0,
                                      'pass_hat_k': s.get('pass_hat_k') is True, 'tokens': number(s.get('tokens')), 'cost_usd': number(s.get('cost_usd')),
                                      'cost_unreported': s.get('cost_unreported') if type(s.get('cost_unreported')) is int else 0}
        without = c.get('without') if isinstance(c.get('without'), dict) else {}
        cases.append({
            'id': c['id'], 'kind': c.get('kind') if c.get('kind') in ('routing', 'outcome') else None,
            'holdout': c.get('holdout') if type(c.get('holdout')) is bool else None, 'result': c['result'],
            'cheapest_tier': c.get('cheapest_tier') if isinstance(c.get('cheapest_tier'), str) else None,
            'without': {'result': without.get('result') if without.get('result') in ('pass', 'fail', 'error') else None,
                        'cheapest_tier': without.get('cheapest_tier') if isinstance(without.get('cheapest_tier'), str) else None},
            'verdict': c.get('verdict') if c.get('verdict') in ('helps', 'same', 'regression', 'no baseline', 'not run') else 'not run',
            'pass_hat_k': c.get('pass_hat_k') is True, 'pass_pow_k': c.get('pass_pow_k') if isinstance(c.get('pass_pow_k'), str) else None,
            'tiers': tiers, 'runs': c.get('runs') if type(c.get('runs')) is int else 0, 'tokens': number(c.get('tokens')),
            'cost_usd': number(c.get('cost_usd')),
            'evidence': [p for p in c.get('evidence', [])[:40] if isinstance(p, str) and SAFE_PATH.fullmatch(p) and '..' not in p]
            if isinstance(c.get('evidence'), list) else []})
    t = data['totals']
    totals = {k: t.get(k) if type(t.get(k)) is int and t[k] >= 0 else 0 for k in ('cases', 'passed', 'failed', 'errors', 'runs', 'cached_runs', 'runs_cost_unreported')}
    totals.update(tokens=number(t.get('tokens')), cost_usd=number(t.get('cost_usd')))
    clean = {
        'schema_version': 1, 'created': data['created'], 'commit': data['commit'], 'pr': pr, 'is_main': data.get('is_main') is True,
        'library_dirty': data.get('library_dirty') is True, 'host': data.get('host'), 'cli_version': data.get('cli_version'),
        'models': [m for m in data.get('models', []) if isinstance(m, str)][:20], 'suite_sha256': data.get('suite_sha256'),
        'cases': cases, 'totals': totals,
        'run_files': [p for p in data.get('run_files', [])[:40] if isinstance(p, str)] if isinstance(data.get('run_files'), list) else [],
        'evidence_note': data.get('evidence_note')}
    clean = clean_tree(clean)
    clean['host'] = re.sub(r'[^a-z0-9._-]', '', str(clean['host']).lower())[:30] or 'unknown'
    return clean


# ------------------------------------------------------------ gh

class Github:
    """Every GitHub call goes through here. Reads always run; writes only with send=True, else they are printed."""

    def __init__(self, repo, send, out=None):
        self.repo, self.send, self.out = repo, send, out or sys.stdout
        self.exe = os.environ.get('ORBYN_GH') or shutil.which('gh')
        if not self.exe:
            raise CannotRun('the gh CLI was not found; install it and run `gh auth login`')

    def run(self, args, body=None):
        try:
            return subprocess.run([self.exe, *args], input=None if body is None else json.dumps(body), capture_output=True,
                                  text=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as error:
            raise CannotRun(f'gh could not run: {error}')

    def read(self, path, jq=None, missing_ok=False, paginate=False):
        args = ['api', path] + (['--paginate'] if paginate else []) + (['--jq', jq] if jq else [])
        result = self.run(args)
        if result.returncode != 0:
            if missing_ok and ('404' in result.stderr or 'Not Found' in result.stderr):
                return None
            raise Refused(f'gh api {path} failed: {clean_text(result.stderr, 200)}')
        return result.stdout

    def read_json(self, path, missing_ok=False):
        text = self.read(path, missing_ok=missing_ok)
        if text is None:
            return None
        try:
            return json.loads(text)
        except ValueError:
            raise Refused(f'gh api {path} returned something that is not JSON')

    def write(self, method, path, body, label):
        shown = json.dumps(body, indent=2)
        if len(shown) > 3000:
            shown = shown[:3000] + f'\n... ({len(shown)} characters in all)'
        if not self.send:
            print(f'[dry run] would {label}: {method} {path}\n{shown}\n', file=self.out)
            return None
        result = self.run(['api', '-X', method, path, '--input', '-'], body)
        if result.returncode != 0:
            raise Refused(f'gh api {method} {path} failed: {clean_text(result.stderr, 200)}')
        print(f'sent: {label}', file=self.out)
        try:
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except ValueError:
            return {}


def pick_repo(value):
    if value:
        if not REPO.fullmatch(value):
            raise CannotRun('--repo must look like owner/name')
        return value
    exe = os.environ.get('ORBYN_GH') or shutil.which('gh')
    if not exe:
        raise CannotRun('the gh CLI was not found; install it and run `gh auth login`')
    result = subprocess.run([exe, 'repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner'], capture_output=True, text=True, timeout=60)
    name = result.stdout.strip()
    if result.returncode != 0 or not REPO.fullmatch(name):
        raise CannotRun('could not tell which repository this is; pass --repo owner/name')
    return name


# ------------------------------------------------------------ rendering

def status_for(summary):
    t = summary['totals']
    state = 'success'
    if t['failed']:
        state = 'failure'
    elif t['errors'] or not t['cases']:
        state = 'error'
    text = f'{t["passed"]}/{t["cases"]} cases pass, {t["runs"]} runs'
    if t['errors']:
        text += f', {t["errors"]} not run'
    return {'state': state, 'context': CONTEXT, 'description': text}


def money(value):
    return 'unknown' if value is None else f'${value:.2f}'


def count(value):
    return 'unknown' if value is None else f'{int(value):,}'


def outcome_text(result, tier):
    return {'pass': f'pass ({md(tier)})' if tier else 'pass', 'fail': 'fail', 'error': 'not run', 'not_run': 'not run', None: 'n/a'}[result]


def change_from_main(case, baseline):
    if baseline is None:
        return 'no main result'
    old = next((c for c in baseline['cases'] if c['id'] == case['id']), None)
    if old is None:
        return 'new case'
    if old['result'] == case['result']:
        if case['result'] == 'pass' and old['cheapest_tier'] != case['cheapest_tier']:
            return f'pass, tier {md(old["cheapest_tier"])} to {md(case["cheapest_tier"])}'
        return 'same'
    return {('fail', 'pass'): 'fixed', ('pass', 'fail'): 'regressed'}.get((old['result'], case['result']), f'was {md(old["result"])}')


def render_comment(summary, baseline=None):
    t = summary['totals']
    lines = [MARKER, f'### Agent evals: {t["passed"]}/{t["cases"]} cases pass', '',
             f'Advisory result from a local run, not a required check. Commit `{summary["commit"][:12]}`, '
             f'{md(summary["host"])} {md(summary["cli_version"])}, models: {md(", ".join(summary["models"]), 120)}.', '',
             '| Case | Tier passed | With / without skills | Change from main |', '| --- | --- | --- | --- |']
    for c in summary['cases']:
        flag = ' (holdout)' if c['holdout'] else ''
        both = f'{outcome_text(c["result"], None)} / {outcome_text(c["without"]["result"], None)}'
        lines.append(f'| `{c["id"]}`{flag} | {md(c["cheapest_tier"]) if c["cheapest_tier"] else "none"} | {both}, {md(c["verdict"])} | {change_from_main(c, baseline)} |')
    unreported = f' ({t["runs_cost_unreported"]} runs without a reported cost)' if t['runs_cost_unreported'] else ''
    lines += ['', f'Runs: {t["runs"]} ({t["cached_runs"]} cached baseline results reused). Tokens: {count(t["tokens"])}. '
                  f'Reported cost: {money(t["cost_usd"])}{unreported}.']
    if baseline:
        lines.append(f'Compared with the last main result, commit `{baseline["commit"][:12]}`.')
    lines.append('Evidence stays on the machine that ran the evals; this comment holds counts only.')
    return '\n'.join(lines) + '\n'


def history_name(summary):
    return f'{summary["created"][:10]}-{summary["commit"][:12]}-{summary["host"]}.json'


def render_history(summary):
    return json.dumps(summary, indent=2, sort_keys=True) + '\n'


# ------------------------------------------------------------ branch files

def branch_listing(gh, directory):
    listing = gh.read_json(f'repos/{gh.repo}/contents/{directory}?ref={BRANCH}' if directory else f'repos/{gh.repo}/contents?ref={BRANCH}', missing_ok=True)
    return {e['name']: e['sha'] for e in listing if isinstance(e, dict) and 'name' in e and 'sha' in e} if isinstance(listing, list) else {}


def branch_exists(gh):
    return gh.read(f'repos/{gh.repo}/git/ref/heads/{BRANCH}', missing_ok=True) is not None


def ensure_branch(gh):
    """Create eval-results from an orphan commit (an empty-parent commit with one README) when it does not exist."""
    if branch_exists(gh):
        return
    readme = ('# Agent eval results\n\nWritten by skills/orbyn-skill-creator/scripts/eval_report.py. `history/` holds one summary per '
              'evaluation (counts and local evidence paths only). `index.html` is the trend dashboard.\n')
    blob = gh.write('POST', f'repos/{gh.repo}/git/blobs', {'content': readme, 'encoding': 'utf-8'}, f'create the {BRANCH} branch (blob)') or {}
    tree = gh.write('POST', f'repos/{gh.repo}/git/trees', {'tree': [{'path': 'README.md', 'mode': '100644', 'type': 'blob', 'sha': blob.get('sha', '<blob sha>')}]},
                    f'create the {BRANCH} branch (tree)') or {}
    commit = gh.write('POST', f'repos/{gh.repo}/git/commits', {'message': 'Start the eval-results branch', 'tree': tree.get('sha', '<tree sha>'), 'parents': []},
                      f'create the {BRANCH} branch (orphan commit)') or {}
    gh.write('POST', f'repos/{gh.repo}/git/refs', {'ref': f'refs/heads/{BRANCH}', 'sha': commit.get('sha', '<commit sha>')}, f'create the {BRANCH} branch (ref)')


def put_file(gh, path, text, message, known=None):
    """Create or update one file on the eval-results branch through the contents API; the working tree is never used."""
    sha = (known or {}).get(Path(path).name)
    body = {'message': message, 'content': base64.b64encode(text.encode('utf-8')).decode('ascii'), 'branch': BRANCH}
    if sha:
        body['sha'] = sha
    gh.write('PUT', f'repos/{gh.repo}/contents/{path}', body, f'write {path} on {BRANCH}')


def read_branch_file(gh, path):
    data = gh.read_json(f'repos/{gh.repo}/contents/{path}?ref={BRANCH}', missing_ok=True)
    if not isinstance(data, dict) or not isinstance(data.get('content'), str):
        return None
    try:
        return base64.b64decode(data['content']).decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        return None


def last_main_result(gh, summary, listing):
    for name in sorted(listing, reverse=True)[:12]:
        text = read_branch_file(gh, f'history/{name}')
        try:
            old = validate_summary(json.loads(text)) if text else None
        except (ValueError, Refused):
            continue
        if old and old['is_main'] and old['host'] == summary['host'] and old['commit'] != summary['commit']:
            return old
    return None


# ------------------------------------------------------------ publish

def publish(args, out=None):
    out = out or sys.stdout
    summary_path = Path(args.summary)
    if summary_path.stat().st_size > SUMMARY_LIMIT:
        raise Refused(f'summary is larger than {SUMMARY_LIMIT} bytes')
    summary = validate_summary(read_json(summary_path, SUMMARY_LIMIT))
    if summary['library_dirty'] and not args.allow_dirty:
        raise Refused('the runs were made on a dirty library checkout, so they do not describe the commit; rerun clean or pass --allow-dirty')
    status, comment = status_for(summary), None
    if len(status['description']) > STATUS_LIMIT:
        raise Refused(f'status description is over GitHub\'s {STATUS_LIMIT} character limit')
    if not args.history_only:
        if summary['pr'] is not None and summary['pr'] != args.pr:
            raise Refused(f'the summary is for PR {summary["pr"]}, not PR {args.pr}')
    gh = Github(pick_repo(args.repo), args.send, out)
    listing = branch_listing(gh, 'history')
    if args.history_only:
        if not summary['is_main']:
            raise Refused('--history-only is for results from main; summarize with --main')
    else:
        pull = gh.read_json(f'repos/{gh.repo}/pulls/{args.pr}')
        head = pull.get('head', {}).get('sha') if isinstance(pull, dict) and isinstance(pull.get('head'), dict) else None
        if not isinstance(head, str) or head != summary['commit']:
            raise Refused(f'the summary is for commit {summary["commit"][:12]} but PR {args.pr} head is {clean_text(head, 12)}; '
                          'rerun the evals on the PR head')
        baseline = last_main_result(gh, summary, listing)
        comment = render_comment(summary, baseline)
        if len(comment) > COMMENT_LIMIT:
            raise Refused(f'the PR comment would be {len(comment)} characters, over GitHub\'s {COMMENT_LIMIT} limit')
    name = history_name(summary)
    print(f'{"SENDING" if args.send else "DRY RUN (nothing is sent; pass --send to publish)"}: {status["description"]} -> {status["state"]}', file=out)
    ensure_branch(gh)
    put_file(gh, f'history/{name}', render_history(summary), f'Add eval result {name[:-5]}', listing)
    if args.history_only:
        return summary
    gh.write('POST', f'repos/{gh.repo}/statuses/{summary["commit"]}', status, f'set the {CONTEXT} status')
    mine = gh.read('user', jq='.login').strip()
    found = None
    pages = gh.read(f'repos/{gh.repo}/issues/{args.pr}/comments?per_page=100', jq='.[] | {id: .id, login: .user.login, body: .body}', paginate=True) or ''
    for line in pages.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get('login') == mine and MARKER in str(item.get('body', '')):
            found = item['id']
    if found:
        gh.write('PATCH', f'repos/{gh.repo}/issues/comments/{found}', {'body': comment}, 'update the PR comment')
    else:
        gh.write('POST', f'repos/{gh.repo}/issues/{args.pr}/comments', {'body': comment}, 'create the PR comment')
    return summary


# ------------------------------------------------------------ dashboard

def load_history(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise Refused(f'history folder not found: {folder}')
    found, skipped = [], []
    for path in sorted(folder.glob('**/*.json')):
        try:
            found.append(validate_summary(read_json(path, SUMMARY_LIMIT)))
        except Refused as error:
            skipped.append(f'{path.name}: {error}')
    found.sort(key=lambda s: (s['created'], s['commit']))
    return found, skipped


def passed_at(case, model, condition):
    t = case['tiers'].get(model, {}).get(condition)
    return None if not t or not t['completed'] else t['pass_hat_k']


def observations(history):
    """(summary index, case id, host, model, condition) -> bool for every tier that completed a run."""
    out = {}
    for i, s in enumerate(history):
        for c in s['cases']:
            for model in c['tiers']:
                for cond in ('with', 'without'):
                    value = passed_at(c, model, cond)
                    if value is not None:
                        out[(i, c['id'], s['host'], model, cond)] = value
    return out


def non_discriminating(history):
    """Cases whose outcome never differs with or without skills, at any tier, over at least two paired observations."""
    flagged = {}
    pairs = {}
    for (i, case, host, model, cond), value in observations(history).items():
        pairs.setdefault((case, i, host, model), {})[cond] = value
    by_case = {}
    for (case, i, host, model), both in pairs.items():
        if len(both) == 2:
            by_case.setdefault(case, []).append(both)
    for case, rows in by_case.items():
        values = {v for both in rows for v in both.values()}
        if len(rows) >= 2 and len(values) == 1:
            flagged[case] = (f'{"passes" if values == {True} else "fails"} with and without skills in all {len(rows)} paired observations')
    return flagged


CSS = """
:root{--bg:#f7f7f4;--card:#fff;--ink:#1d2321;--muted:#5b6560;--line:#dcdfd8;--pass:#1f7a4d;--passbg:#dff2e6;--fail:#b3261e;--failbg:#f9e1de;--none:#8a918c;--nonebg:#ebece8;--accent:#2b5f9e;--warn:#8a5a00;--warnbg:#fbefcf}
@media (prefers-color-scheme:dark){:root{--bg:#141817;--card:#1d2321;--ink:#e8ece9;--muted:#9aa49e;--line:#323a37;--pass:#6fd09a;--passbg:#18382a;--fail:#ff8a80;--failbg:#431c19;--none:#9aa49e;--nonebg:#2a312e;--accent:#8ab4f0;--warn:#f0c25a;--warnbg:#41330f}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:1.5rem;margin:8px 0}h2{font-size:1.1rem;margin:0 0 4px}p{margin:4px 0}.muted{color:var(--muted)}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:14px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px}.card b{display:block;font-size:1.4rem}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{font-weight:600;color:var(--muted);white-space:nowrap}td.n{text-align:right;font-variant-numeric:tabular-nums}
code{font:.85em ui-monospace,Menlo,monospace}
.strip{display:inline-flex;gap:2px;flex-wrap:nowrap}
.dot{width:18px;height:18px;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700}
.pass{background:var(--passbg);color:var(--pass)}.fail{background:var(--failbg);color:var(--fail)}.none{background:var(--nonebg);color:var(--none)}
.bar{display:inline-block;height:8px;border-radius:4px;background:var(--accent);vertical-align:middle;min-width:2px}
.track{display:inline-block;width:70px;height:8px;border-radius:4px;background:var(--nonebg);vertical-align:middle;margin-right:6px}
.track .bar{display:block}
.flag{background:var(--warnbg);color:var(--warn);border-radius:6px;padding:1px 6px;font-size:.8rem}
svg{width:100%;height:auto;display:block}svg text{fill:var(--muted);font-size:11px}svg .grid{stroke:var(--line)}
.legend span{margin-right:12px}.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px}
@media (max-width:600px){main{padding:12px}section{padding:10px}h1{font-size:1.25rem}}
"""
LINE_COLOURS = ['var(--accent)', 'var(--pass)', 'var(--warn)', 'var(--fail)']


def e(value):
    return html.escape(str(value), quote=True)


def pct(passes, total_):
    return None if not total_ else round(100 * passes / total_)


def table(headers, rows, numeric=()):
    head = ''.join(f'<th scope="col">{e(h)}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td{" class=n" if i in numeric else ""}>{cell}</td>' for i, cell in enumerate(row)) + '</tr>' for row in rows)
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def dot(value, label):
    kind, glyph = {True: ('pass', '&#10003;'), False: ('fail', '&#10007;'), None: ('none', '&ndash;')}[value]
    return f'<span class="dot {kind}" title="{e(label)}" role="img" aria-label="{e(label)}">{glyph}</span>'


def share(passes, total_):
    if not total_:
        return '<span class="muted">no data</span>'
    p = round(100 * passes / total_)
    return f'<span class="track"><span class="bar" style="width:{p}%"></span></span>{passes}/{total_} ({p}%)'


def line_chart(history):
    hosts = sorted({s['host'] for s in history})
    width, height, left, bottom = 640, 220, 34, 28
    n = max(len(history) - 1, 1)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Share of cases passing with skills, by evaluation">']
    for tick in (0, 50, 100):
        y = height - bottom - (height - bottom - 12) * tick / 100
        parts.append(f'<line class="grid" x1="{left}" x2="{width - 8}" y1="{y:.1f}" y2="{y:.1f}"/><text x="2" y="{y + 4:.1f}">{tick}%</text>')
    legend = []
    for k, host in enumerate(hosts):
        points = []
        for i, s in enumerate(history):
            if s['host'] == host and s['totals']['cases']:
                x = left + (width - left - 12) * (i / n if len(history) > 1 else 0.5)
                y = height - bottom - (height - bottom - 12) * (s['totals']['passed'] / s['totals']['cases'])
                points.append((x, y))
        colour = LINE_COLOURS[k % len(LINE_COLOURS)]
        if len(points) > 1:
            parts.append(f'<polyline fill="none" stroke="{colour}" stroke-width="2" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}"/>')
        parts.extend(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{colour}"/>' for x, y in points)
        legend.append(f'<span><i class="sw" style="background:{colour}"></i>{e(host)}</span>')
    first, last = history[0]['created'][:10], history[-1]['created'][:10]
    parts.append(f'<text x="{left}" y="{height - 8}">{e(first)}</text><text x="{width - 8}" y="{height - 8}" text-anchor="end">{e(last)}</text></svg>')
    return ''.join(parts) + f'<p class="legend muted">{"".join(legend)}</p>'


def render_dashboard(history, skipped=()):
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    if not history:
        body = '<section><h2>No results yet</h2><p class="muted">The history folder has no evaluation summaries. Run eval_run.py, then eval_report.py summarize and publish.</p></section>'
        return page(body, now, skipped)
    obs = observations(history)
    latest = history[-1]
    cost = total(s['totals']['cost_usd'] for s in history)
    flagged = non_discriminating(history)
    cards = [('Evaluations', len(history)), ('Latest', f'{latest["totals"]["passed"]}/{latest["totals"]["cases"]} pass'),
             ('Runs used', sum(s['totals']['runs'] for s in history)), ('Reported cost', money(cost)), ('Flagged cases', len(flagged))]
    parts = ['<div class="cards">' + ''.join(f'<div class="card"><span class="muted">{e(k)}</span><b>{e(v)}</b></div>' for k, v in cards) + '</div>']
    parts.append('<section><h2>Pass rate over time</h2><p class="muted">Share of cases that passed with skills, one point per evaluation.</p>' + line_chart(history) + '</section>')
    case_ids = sorted({c['id'] for s in history for c in s['cases']})
    rows = []
    for cid in case_ids:
        cells, wins = [], 0
        for i, s in enumerate(history[-30:], start=len(history) - len(history[-30:])):
            c = next((c for c in s['cases'] if c['id'] == cid), None)
            value = None if c is None or c['result'] in ('error', 'not_run') else c['result'] == 'pass'
            wins += value is True
            label = f'{s["created"][:10]} {s["host"]} commit {s["commit"][:7]}: ' + ('not run' if value is None else 'pass' if value else 'fail')
            cells.append(dot(value, label))
        ran = sum(1 for s in history[-30:] for c in s['cases'] if c['id'] == cid and c['result'] in ('pass', 'fail'))
        flag = ' <span class="flag">non-discriminating</span>' if cid in flagged else ''
        rows.append([f'<code>{e(cid)}</code>{flag}', f'<span class="strip">{"".join(cells)}</span>', share(wins, ran)])
    parts.append('<section><h2>Pass rate by case over time</h2><p class="muted">Oldest on the left, with skills. A check is a pass, a cross a fail, a dash means the case did not run.</p>'
                 + table(['Case', 'Evaluations', 'Pass rate'], rows) + '</section>')
    combos = sorted({(h, m) for (_, _, h, m, _) in obs}, key=lambda hm: (hm[0], tier_rank(hm[1])))
    rows = []
    for cid in case_ids:
        row = [f'<code>{e(cid)}</code>']
        for host, model in combos:
            seen = [v for (i, c, h, m, cond), v in obs.items() if c == cid and h == host and m == model and cond == 'with']
            row.append(share(sum(seen), len(seen)))
        rows.append(row)
    parts.append('<section><h2>By tier and host</h2><p class="muted">With skills, the share of evaluations where the case passed at that tier. Compare the same case across columns, such as sonnet and terra.</p>'
                 + table(['Case'] + [f'{h} / {m}' for h, m in combos], rows) + '</section>')
    rows = []
    for cid in case_ids:
        w = [v for (i, c, h, m, cond), v in obs.items() if c == cid and cond == 'with']
        wo = [v for (i, c, h, m, cond), v in obs.items() if c == cid and cond == 'without']
        delta = '<span class="muted">no baseline</span>' if not wo or not w else f'{pct(sum(w), len(w)) - pct(sum(wo), len(wo)):+d} points'
        rows.append([f'<code>{e(cid)}</code>', share(sum(w), len(w)), share(sum(wo), len(wo)), delta])
    parts.append('<section><h2>With versus without skills</h2><p class="muted">Pass rate over every tier observed. A case that scores the same both ways says little about the skills.</p>'
                 + table(['Case', 'With skills', 'Without skills', 'Difference'], rows) + '</section>')
    peak = max((s['totals']['runs'] for s in history), default=1) or 1
    rows = [[e(s['created'][:10]), f'<code>{e(s["commit"][:7])}</code>', e(f'#{s["pr"]}' if s['pr'] else ('main' if s['is_main'] else '')),
             e(f'{s["host"]} / {", ".join(s["models"])}'), f'{s["totals"]["passed"]}/{s["totals"]["cases"]}',
             f'<span class="bar" style="width:{max(2, round(60 * s["totals"]["runs"] / peak))}px"></span> {s["totals"]["runs"]}',
             count(s['totals']['tokens']), money(s['totals']['cost_usd'])] for s in reversed(history)]
    parts.append('<section><h2>Runs and cost per evaluation</h2><p class="muted">Cost is what the CLI reported; unknown means it reported none and nothing is estimated.</p>'
                 + table(['Date', 'Commit', 'PR', 'Host / models', 'Pass', 'Runs', 'Tokens', 'Cost'], rows, numeric=(4, 6, 7)) + '</section>')
    if flagged:
        items = ''.join(f'<li><code>{e(cid)}</code> {e(why)}</li>' for cid, why in sorted(flagged.items()))
        parts.append(f'<section><h2>Non-discriminating cases</h2><p class="muted">These do not separate skills from no skills. Consider retiring or hardening them.</p><ul>{items}</ul></section>')
    return page(''.join(parts), now, skipped)


def page(body, now, skipped):
    note = f'<p class="muted">Skipped unreadable files: {e(", ".join(skipped[:5]))}</p>' if skipped else ''
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="light dark"><title>Agent eval trends</title>'
            f'<style>{CSS}</style></head><body><main><h1>Agent eval trends</h1>'
            f'<p class="muted">Local evaluations reported through eval_report.py. Generated {e(now)}. This page makes no network requests.</p>{body}{note}</main></body></html>\n')


# ------------------------------------------------------------ affected cases

def affected_cases(changed, cases_dir=EXECUTABLE):
    """Executable case ids whose dependencies a list of repo-relative changed paths touches.

    A case's case.json may declare `depends_on` (paths; a folder matches everything below it). Without it, a case depends
    on its expected skill's folder, the orbyn-workflow skill and the model registry. A case always depends on its own folder."""
    changed = [re.sub(r'^(\./)+', '', str(p).replace('\\', '/')) for p in changed]
    out = []
    for path in sorted(Path(cases_dir).iterdir()):
        try:
            case = json.loads((path / 'case.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        declared = case.get('depends_on')
        if isinstance(declared, list) and all(isinstance(d, str) and d for d in declared):
            depends = declared
        else:
            depends = list(DEFAULT_DEPENDS) + ([f'skills/{case["expected_skill"]}/'] if case.get('expected_skill') else [])
        try:
            own = path.resolve().relative_to(ROOT).as_posix() + '/'
        except ValueError:
            own = f'skills/orbyn-skill-creator/evals/executable/{path.name}/'
        depends = [re.sub(r'^(\./)+', '', d.replace('\\', '/')) for d in depends] + [own]
        if any(p == d.rstrip('/') or p.startswith(d.rstrip('/') + '/') for p in changed for d in depends):
            out.append(path.name)
    return out


def git_changed(base):
    result = subprocess.run(['git', '-C', str(ROOT), 'diff', '--name-only', f'{base}...HEAD'], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise CannotRun(f'git diff against {base} failed: {clean_text(result.stderr, 200)}')
    return [line for line in result.stdout.splitlines() if line]


# ------------------------------------------------------------ cli

def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('summarize', help='compact summary of run.json files')
    s.add_argument('--run', action='append', required=True, help='a run.json from eval_run.py (repeatable)')
    s.add_argument('--out', required=True)
    s.add_argument('--pr', type=int)
    s.add_argument('--main', action='store_true', help='mark the result as from main, the baseline later PRs compare with')
    p = sub.add_parser('publish', help='status, PR comment and history (dry run unless --send)')
    p.add_argument('--summary', required=True)
    p.add_argument('--pr', type=int)
    p.add_argument('--history-only', action='store_true', help='write only the history file (for a --main summary)')
    p.add_argument('--repo')
    p.add_argument('--allow-dirty', action='store_true')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--send', action='store_true')
    mode.add_argument('--dry-run', action='store_true', help='the default')
    d = sub.add_parser('dashboard', help='single-file HTML trend dashboard')
    d.add_argument('--history', required=True)
    d.add_argument('--out', required=True)
    d.add_argument('--publish', action='store_true', help='also write index.html to the eval-results branch')
    d.add_argument('--repo')
    mode = d.add_mutually_exclusive_group()
    mode.add_argument('--send', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    f = sub.add_parser('fetch', help='copy history/*.json from the eval-results branch')
    f.add_argument('--repo')
    f.add_argument('--out', required=True)
    a = sub.add_parser('affected', help='executable cases a diff affects')
    a.add_argument('--base', default='origin/main')
    a.add_argument('--paths', nargs='*', help='changed paths instead of a git diff')
    a.add_argument('--cases-dir', default=str(EXECUTABLE))
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == 'summarize':
            summary = summarize(args.run, args.pr, args.main)
            text = render_history(summary)
            if len(text) > SUMMARY_LIMIT:
                raise Refused('summary is over the size limit')
            Path(args.out).write_text(text, encoding='utf-8')
            t = summary['totals']
            print(f'wrote {args.out}: {t["passed"]}/{t["cases"]} cases pass, {t["runs"]} runs, commit {summary["commit"][:12]}')
        elif args.command == 'publish':
            if not args.history_only and not args.pr:
                raise CannotRun('publish needs --pr N (or --history-only for a main result)')
            if args.pr is not None and args.pr < 1:
                raise CannotRun('--pr must be a positive number')
            publish(args)
        elif args.command == 'dashboard':
            history, skipped = load_history(args.history)
            text = render_dashboard(history, skipped)
            Path(args.out).write_text(text, encoding='utf-8')
            print(f'wrote {args.out} from {len(history)} evaluations')
            if args.publish:
                gh = Github(pick_repo(args.repo), args.send)
                ensure_branch(gh)
                put_file(gh, 'index.html', text, 'Update the eval dashboard', branch_listing(gh, ''))
        elif args.command == 'fetch':
            gh = Github(pick_repo(args.repo), False)
            listing = branch_listing(gh, 'history')
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            for name in sorted(listing):
                if re.fullmatch(r'[A-Za-z0-9._-]+\.json', name):
                    text = read_branch_file(gh, f'history/{name}')
                    if text:
                        (out / name).write_text(text, encoding='utf-8')
            print(f'fetched {len(list(out.glob("*.json")))} summaries into {out}')
        elif args.command == 'affected':
            changed = args.paths if args.paths is not None else git_changed(args.base)
            for case_id in affected_cases(changed, args.cases_dir):
                print(case_id)
    except Refused as error:
        print(f'refused: {error}', file=sys.stderr)
        return 1
    except CannotRun as error:
        print(f'error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
