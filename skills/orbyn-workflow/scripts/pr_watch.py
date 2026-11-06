#!/usr/bin/env python3
"""Wake the agent when a pull request its person owns needs attention. Read-only: it only calls `gh` to read.

Owner rule. A PR is owned by LOGIN when (a) its author is LOGIN (case-insensitive), or (b) an issue the PR closes
(its `closingIssuesReferences`, the Development sidebar) has LOGIN among its assignees. Nothing else counts: not
review requests, commits or PR assignees. The reason is "author" or "assigned #N".

`scope` lists the login, repo, merge authority and each owned open PR. `wait` fetches one snapshot per cycle,
compares it with the saved state and exits 0 with one line per event; with no event it sleeps and repeats until
`--max` seconds pass, then exits 3 (still waiting, call again). Exit 2 means a `gh` or API error. The first
`wait` has no saved state, so the open PRs become the silent baseline; use `scope` for what already exists.

Required checks. Per base branch the names come from the ruleset (`required_status_checks`) and classic branch
protection, as a union. When names are known, CI events judge only those checks: an optional failure is listed as
`optional failing: X` and never makes `ci_failed`, and a required check absent from the rollup counts as pending; when it is still absent after `--no-ci-after`
and nothing else runs, `ci_missing` names it.
With no known names every check counts as required.

Readiness (`ready=` on every event line, plus a `ready` event once per head and value):
yes = mergeStateStatus CLEAN (or HAS_HOOKS/UNSTABLE with every required check passed) and the person may merge;
owner = BLOCKED only by the approval GitHub will not let an admin give their own PR (required checks passed, no
conflict, REVIEW_REQUIRED, no unresolved threads, role admin, author is the person); no = anything else.
The helper never merges. `owner` is a decision for the person, never an automatic admin merge.

Event line: `<kind> #<n> <sha> <detail> authority=yes|no ready=yes|owner|no state=<mergeStateStatus>`. Kinds:
new_pr, new_head, ci_passed, ci_failed, ci_missing, review_threads, conflict, changes_requested, ready, closed.
Standard library only; POSIX and Windows.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

STILL_WAITING = 3  # same convention as bg.py wait: nothing happened yet, call again
GH_ERROR = 2
MERGE_ROLES = {'admin', 'maintain', 'write'}
FAIL_CONCLUSIONS = {'FAILURE', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED', 'STARTUP_FAILURE'}
FAIL_STATUSES = {'FAILURE', 'ERROR'}
PENDING_STATUSES = {'PENDING', 'EXPECTED'}

QUERY = '''
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: OPEN, first: 50, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url isDraft headRefOid baseRefName mergeable mergeStateStatus reviewDecision
        author { login }
        reviewThreads(first: 100) { nodes { id isResolved } }
        latestReviews(first: 30) { nodes { author { login } state submittedAt } }
        closingIssuesReferences(first: 10) { nodes { number assignees(first: 20) { nodes { login } } } }
        commits(last: 1) { nodes { commit { oid committedDate statusCheckRollup { state contexts(first: 100) { nodes {
          __typename
          ... on CheckRun { name status conclusion }
          ... on StatusContext { context state }
        } } } } } }
      }
    }
  }
}
'''


class GhError(Exception):
    """A `gh` call failed or returned something unreadable."""


def run_gh(args):
    """The one place that calls `gh`. Returns stdout; tests replace this function."""
    try:
        result = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GhError(f'gh {args[0]}: {error}') from error
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip().splitlines()
        raise GhError(f'gh {" ".join(args[:2])}: {message[0] if message else "exit " + str(result.returncode)}')
    return result.stdout


def gh_json(args):
    try:
        return json.loads(run_gh(args))
    except ValueError as error:
        raise GhError(f'gh {" ".join(args[:2])}: unreadable JSON') from error


def default_repo():
    return gh_json(['repo', 'view', '--json', 'nameWithOwner'])['nameWithOwner']


def default_login():
    return run_gh(['api', 'user', '--jq', '.login']).strip()


def merge_authority(repo, login):
    """Whether LOGIN may merge, from the collaborator role. A refused lookup means no authority."""
    try:
        data = gh_json(['api', f'repos/{repo}/collaborators/{login}/permission'])
    except GhError as error:
        return {'can_merge': False, 'role': None, 'reason': f'permission unknown ({error})'}
    role = (data.get('role_name') or data.get('permission') or '').lower()
    return {'can_merge': role in MERGE_ROLES, 'role': role or None,
            'reason': f'role {role}' if role else 'no role reported'}


def branch_rules(repo, base):
    """Rules on a base branch: {'types': sorted rule types or None when unknown, 'required': sorted check names}.

    Required names are the union of the ruleset and classic protection; a refused lookup there means none."""
    types, required = None, set()
    try:
        data = gh_json(['api', f'repos/{repo}/rules/branches/{base}'])
        rules = [rule for rule in data if isinstance(rule, dict)]
        types = sorted({rule['type'] for rule in rules if rule.get('type')})
        for rule in rules:
            if rule.get('type') == 'required_status_checks':
                for check in (rule.get('parameters') or {}).get('required_status_checks') or []:
                    if check.get('context'):
                        required.add(check['context'])
    except GhError:
        pass
    try:
        data = gh_json(['api', f'repos/{repo}/branches/{base}/protection/required_status_checks'])
        required.update(name for name in data.get('contexts') or [] if name)
        required.update(check['context'] for check in data.get('checks') or [] if check.get('context'))
    except (GhError, AttributeError):
        pass
    return {'types': types, 'required': sorted(required)}


def fetch_nodes(repo):
    """Every open PR node, following pagination."""
    owner, _, name = repo.partition('/')
    nodes, cursor = [], None
    while True:
        args = ['api', 'graphql', '-f', f'query={QUERY}', '-f', f'owner={owner}', '-f', f'name={name}']
        if cursor:
            args += ['-f', f'cursor={cursor}']
        data = gh_json(args)
        if data.get('errors'):
            raise GhError(f'graphql: {data["errors"][0].get("message", "error")}')
        try:
            page = data['data']['repository']['pullRequests']
        except (KeyError, TypeError) as error:
            raise GhError(f'graphql: no repository {repo}') from error
        nodes += page.get('nodes') or []
        if not page['pageInfo']['hasNextPage']:
            return nodes
        cursor = page['pageInfo']['endCursor']


def nodes_of(value):
    return [item for item in ((value or {}).get('nodes') or []) if item]


def login_of(user):
    return ((user or {}).get('login') or '')


def owner_reason(node, login):
    """'author', 'assigned #N[, #M]' or None. See the owner rule in the module docstring."""
    if login_of(node.get('author')).lower() == login.lower():
        return 'author'
    issues = [issue['number'] for issue in nodes_of(node.get('closingIssuesReferences'))
              if any(login_of(a).lower() == login.lower() for a in nodes_of(issue.get('assignees')))]
    return 'assigned ' + ', '.join(f'#{n}' for n in issues) if issues else None


def read_checks(node):
    """The checks of the current head: [{'name', 'pending', 'failed'}]."""
    commits = nodes_of(node.get('commits'))
    rollup = (commits[0].get('commit') or {}).get('statusCheckRollup') if commits else None
    checks = []
    for item in nodes_of((rollup or {}).get('contexts')):
        if item.get('__typename') == 'CheckRun':
            checks.append({'name': item.get('name') or 'check', 'pending': item.get('status') != 'COMPLETED',
                           'failed': item.get('conclusion') in FAIL_CONCLUSIONS})
        else:
            status = item.get('state')
            checks.append({'name': item.get('context') or 'status', 'pending': status in PENDING_STATUSES,
                           'failed': status in FAIL_STATUSES})
    return checks


def owned_records(nodes, login):
    """Pure: GraphQL PR nodes -> records of the PRs LOGIN owns, ordered by number."""
    records = []
    for node in nodes:
        reason = owner_reason(node, login)
        if reason is None:
            continue
        reviews = [f'{login_of(r.get("author"))}|{r.get("submittedAt")}'
                   for r in nodes_of(node.get('latestReviews')) if r.get('state') == 'CHANGES_REQUESTED']
        records.append({
            'number': node['number'], 'title': node.get('title') or '', 'url': node.get('url') or '',
            'author': login_of(node.get('author')), 'reason': reason, 'draft': bool(node.get('isDraft')), 'head': node.get('headRefOid') or '',
            'base': node.get('baseRefName') or '', 'mergeable': node.get('mergeable'),
            'merge_state': node.get('mergeStateStatus') or 'UNKNOWN', 'review_decision': node.get('reviewDecision'),
            'unresolved': sum(1 for t in nodes_of(node.get('reviewThreads')) if not t.get('isResolved')),
            'change_requests': sorted(reviews), 'checks': read_checks(node)})
    return sorted(records, key=lambda r: r['number'])


def event(kind, record, detail, ctx):
    return {'kind': kind, 'number': record['number'], 'sha': record['head'][:7], 'detail': detail,
            'authority': 'yes' if ctx['authority']['can_merge'] else 'no', 'ready': record.get('ready', 'no'),
            'state': record['merge_state'], 'url': record['url'], 'title': record['title']}


def format_event(item):
    parts = [item['kind'], f'#{item["number"]}', item['sha'], item['detail'],
             f'authority={item["authority"]}', f'ready={item["ready"]}', f'state={item["state"]}']
    return ' '.join(part for part in parts if part)


def ci_status(record, required):
    """The CI verdict for a record's head against the required check names ({} or empty: every check counts).

    Returns {'verdict': none|pending|passed|failed, 'failed': [...], 'optional_failed': [...], 'count': n}.
    'none' means no required check is registered yet; a required check absent from the rollup is pending and is
    named in 'missing'."""
    checks = record['checks']
    names = set(required)
    if not names:
        judged, optional, missing = checks, [], []
    else:
        judged = [c for c in checks if c['name'] in names]
        optional = [c for c in checks if c['name'] not in names]
        missing = sorted(names - {c['name'] for c in judged})
    failed = [c['name'] for c in judged if c['failed']]
    optional_failed = [c['name'] for c in optional if c['failed']]
    if not judged:
        verdict = 'none'
    elif missing or any(c['pending'] for c in judged):
        verdict = 'pending'
    else:
        verdict = 'failed' if failed else 'passed'
    return {'verdict': verdict, 'failed': failed, 'optional_failed': optional_failed, 'count': len(judged),
            'missing': missing, 'running': any(c['pending'] for c in judged)}


def readiness(record, ci, ctx):
    """yes, owner or no. See the module docstring; the helper only reports, it never merges."""
    authority = ctx['authority']
    if authority['can_merge'] and (record['merge_state'] == 'CLEAN' or (
            record['merge_state'] in ('HAS_HOOKS', 'UNSTABLE') and ci['verdict'] == 'passed')):
        return 'yes'
    if (record['merge_state'] == 'BLOCKED' and ci['verdict'] == 'passed' and record['mergeable'] != 'CONFLICTING'
            and record['review_decision'] == 'REVIEW_REQUIRED' and record['unresolved'] == 0
            and authority.get('role') == 'admin' and record['author'].lower() == ctx['login'].lower()):
        return 'owner'
    return 'no'


def compare(previous, records, ctx):
    """Pure: saved state (None for the first run) + current records -> (events, new state).

    ctx: now (seconds), authority ({'can_merge', 'role'}), login, required ({base: names}), no_ci_after.
    The first run only records a baseline, so it returns no events. A PR missing from the records is reported as
    closed and dropped from the state."""
    old = (previous or {}).get('prs', {})
    now = ctx['now']
    events, prs = [], {}
    for record in records:
        number, head = record['number'], record['head']
        ci = ci_status(record, ctx['required'].get(record['base']) or ())
        record = {**record, 'ready': readiness(record, ci, ctx)}
        seen = old.get(str(number))
        entry = dict(seen) if seen else {
            'head': head, 'first_seen_head_at': now, 'ci_reported_for_head': None, 'ci_result': None,
            'ci_missing_for_head': None, 'unresolved_count': record['unresolved'], 'conflict_reported_head': None,
            'seen_change_request': list(record['change_requests']), 'review_decision': record['review_decision'],
            'ready_reported': None}
        if not seen:
            events.append(event('new_pr', record, f'{record["reason"]}: {record["title"]}', ctx))
        elif entry['head'] != head:
            events.append(event('new_head', record, f'was {entry["head"][:7]}', ctx))
            entry.update(head=head, first_seen_head_at=now, ci_reported_for_head=None, ci_result=None,
                         ci_missing_for_head=None)
        events += ci_events(entry, record, ci, ctx)
        if seen and record['unresolved'] > entry['unresolved_count']:
            added = record['unresolved'] - entry['unresolved_count']
            events.append(event('review_threads', record, f'{record["unresolved"]} unresolved (+{added})', ctx))
        entry['unresolved_count'] = record['unresolved']
        if record['mergeable'] == 'CONFLICTING':
            if entry['conflict_reported_head'] != head:
                events.append(event('conflict', record, 'merge conflict with base', ctx))
                entry['conflict_reported_head'] = head
        elif record['mergeable'] == 'MERGEABLE':
            entry['conflict_reported_head'] = None
        fresh = [key for key in record['change_requests'] if key not in entry['seen_change_request']]
        newly_decided = (record['review_decision'] == 'CHANGES_REQUESTED'
                         and entry['review_decision'] != 'CHANGES_REQUESTED')
        if seen and (fresh or newly_decided):
            who = ', '.join(sorted({key.split('|')[0] for key in fresh})) or 'review decision'
            events.append(event('changes_requested', record, who, ctx))
        entry['seen_change_request'] = sorted(set(entry['seen_change_request']) | set(record['change_requests']))
        entry['review_decision'] = record['review_decision']
        mark = f'{head}:{record["ready"]}'
        if record['ready'] != 'no' and entry['ready_reported'] != mark:
            detail = ('ready to merge' if record['ready'] == 'yes'
                      else 'needs owner decision: approval required, own PR')
            events.append(event('ready', record, detail, ctx))
            entry['ready_reported'] = mark
        prs[str(number)] = entry
    for key, entry in old.items():
        if key not in prs:
            gone = {'number': int(key), 'head': entry['head'], 'merge_state': 'UNKNOWN', 'url': '', 'title': ''}
            events.append(event('closed', gone, 'no longer open or owned', ctx))
    events.sort(key=lambda e: (e['number'], e['kind']))
    return ([] if previous is None else events), {'prs': prs}


def ci_events(entry, record, ci, ctx):
    """CI result for the current head, once per head and result; never from zero or pending required checks."""
    head, verdict = record['head'], ci['verdict']
    if verdict == 'none':
        if ctx['now'] - entry['first_seen_head_at'] >= ctx['no_ci_after'] and entry['ci_missing_for_head'] != head:
            entry['ci_missing_for_head'] = head
            return [event('ci_missing', record, f'no checks after {int(ctx["no_ci_after"])}s', ctx)]
        return []
    if verdict == 'pending':
        late = (ci['missing'] and not ci['running'] and ctx['now'] - entry['first_seen_head_at'] >= ctx['no_ci_after']
                and entry['ci_missing_for_head'] != head)
        if late:  # e.g. a required check whose workflow never ran for this change
            entry['ci_missing_for_head'] = head
            return [event('ci_missing', record, f'required not reported: {", ".join(ci["missing"])}', ctx)]
        return []
    if entry['ci_reported_for_head'] == head and entry['ci_result'] == verdict:
        return []
    entry['ci_reported_for_head'], entry['ci_result'] = head, verdict
    optional = f'optional failing: {", ".join(ci["optional_failed"])}' if ci['optional_failed'] else ''
    if verdict == 'failed':
        return [event('ci_failed', record, ' '.join(filter(None, [','.join(ci['failed']), optional])), ctx)]
    return [event('ci_passed', record, ' '.join(filter(None, [f'{ci["count"]} checks', optional])), ctx)]


def state_path(args, repo, login):
    root = Path(args.state_root) if args.state_root else default_root()
    slug = re.sub(r'[^A-Za-z0-9_.-]+', '-', f'{repo}-{login}').strip('-').lower()
    return Path(args.state) if args.state else root / f'{slug}.json'


def default_root():
    if os.environ.get('ORBYN_PR_WATCH_ROOT'):
        return Path(os.environ['ORBYN_PR_WATCH_ROOT'])
    user = os.environ.get('USER') or os.environ.get('USERNAME') or 'user'
    return Path(tempfile.gettempdir()) / f'orbyn-pr-watch-{user}'


def read_state(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get('prs'), dict) else None


def write_state(path, data):
    """Write atomically, so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


def resolve_identity(args):
    return args.repo or default_repo(), args.login or default_login()


def required_by_base(repo, records, cache):
    """Rules per base branch, read once per run."""
    for base in {r['base'] for r in records}:
        if base not in cache:
            cache[base] = branch_rules(repo, base)
    return cache


def cmd_scope(args, **_):
    repo, login = resolve_identity(args)
    authority = merge_authority(repo, login)
    records = owned_records(fetch_nodes(repo), login)
    rules = required_by_base(repo, records, {})
    ctx = {'now': time.time(), 'authority': authority, 'login': login, 'no_ci_after': 600,
           'required': {base: set(info['required']) for base, info in rules.items()}}
    ready = {r['number']: readiness(r, ci_status(r, ctx['required'].get(r['base']) or ()), ctx) for r in records}
    if args.json:
        print(json.dumps({'login': login, 'repo': repo, 'merge_authority': authority,
                          'branch_rules': {b: {'types': i['types'], 'required_checks': i['required'] or None}
                                           for b, i in rules.items()},
                          'prs': [{**{k: r[k] for k in ('number', 'title', 'url', 'reason', 'draft', 'base', 'head',
                                                        'merge_state', 'mergeable', 'review_decision', 'unresolved')},
                                   'ready': ready[r['number']]} for r in records]}, indent=2))
        return 0
    print(f'login: {login}\nrepo: {repo}')
    print(f'merge authority: {"yes" if authority["can_merge"] else "no"} ({authority["reason"]})')
    for base, info in rules.items():
        types = ', '.join(info['types'] or ['none']) if info['types'] is not None else 'rules unknown'
        names = ', '.join(info['required']) if info['required'] else 'unknown'
        print(f'rules on {base}: {types}\n  required: {names}')
    print(f'owned open PRs: {len(records)}')
    for r in records:
        flags = ' draft' if r['draft'] else ''
        print(f'  #{r["number"]} {r["title"]} [{r["reason"]}] state={r["merge_state"]} ready={ready[r["number"]]}{flags}')
    return 0


def cmd_wait(args, sleep=time.sleep, clock=time.monotonic, wall=time.time):
    repo, login = resolve_identity(args)
    path = state_path(args, repo, login)
    authority = merge_authority(repo, login)
    rules = {}
    started = clock()
    while True:
        records = owned_records(fetch_nodes(repo), login)
        previous = read_state(path)
        known = args.pr is not None and str(args.pr) in (previous or {}).get('prs', {})
        if args.pr is not None and not known and not any(r['number'] == args.pr for r in records):
            print(f'pr_watch: #{args.pr} is not an open PR owned by {login}', file=sys.stderr)
            return GH_ERROR
        required_by_base(repo, records, rules)
        ctx = {'now': wall(), 'authority': authority, 'login': login, 'no_ci_after': args.no_ci_after,
               'required': {base: set(info['required']) for base, info in rules.items()}}
        scoped = records if args.pr is None else [r for r in records if r['number'] == args.pr]
        before = previous
        if previous is not None and args.pr is not None:
            before = {'prs': {k: v for k, v in previous['prs'].items() if k == str(args.pr)}}
        events, after = compare(before, scoped, ctx)
        if previous is not None and args.pr is not None:
            after = {'prs': {**{k: v for k, v in previous['prs'].items() if k != str(args.pr)}, **after['prs']}}
        write_state(path, after)
        if events:
            for item in events:
                print(json.dumps(item) if args.json else format_event(item))
            return 0
        remaining = args.max - (clock() - started)
        if remaining <= 0:
            return STILL_WAITING
        sleep(min(args.interval, remaining))


def interval_type(text):
    value = float(text)
    if value < 30:
        raise argparse.ArgumentTypeError('--interval must be at least 30 seconds')
    return value


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--repo', help='OWNER/NAME (default: the current directory\'s repository)')
    parser.add_argument('--login', help='GitHub login (default: the authenticated user)')
    parser.add_argument('--json', action='store_true', help='machine-readable output')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('scope', help='print the owned open PRs and merge authority')
    wait = sub.add_parser('wait', help='exit 0 with event lines, or 3 when nothing happened within --max')
    wait.add_argument('--interval', type=interval_type, default=120, help='seconds between checks (min 30, default 120)')
    wait.add_argument('--max', type=float, default=3300, help='seconds to wait in total (default 3300)')
    wait.add_argument('--pr', type=int, help='watch only this owned PR')
    wait.add_argument('--state', help='state file (default under $ORBYN_PR_WATCH_ROOT or a per-user temp folder)')
    wait.add_argument('--no-ci-after', type=float, default=600,
                      help='report ci_missing when a head has no checks after this many seconds (default 600)')
    parser.add_argument('--state-root', help=argparse.SUPPRESS)
    return parser


def main(argv=None, **hooks):
    args = build_parser().parse_args(argv)
    handler = {'scope': cmd_scope, 'wait': cmd_wait}[args.action]
    args.state = getattr(args, 'state', None)
    try:
        return handler(args, **hooks)
    except GhError as error:
        print(f'pr_watch: {error}', file=sys.stderr)
        return GH_ERROR


if __name__ == '__main__':
    sys.exit(main())
