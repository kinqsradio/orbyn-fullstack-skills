#!/usr/bin/env python3
"""Select conservative CI scope from complete Git changes and project-owned policy."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

SHA = re.compile(r'[0-9a-f]{40}')
LISTS = ('docs_files', 'docs_prefixes', 'skills_files', 'skills_prefixes',
         'deployment_files', 'deployment_prefixes', 'application_jobs')
PROTECTED = ('.github/', 'skills/orbyn-ci-design/scripts/')


def safe_path(value):
    return (isinstance(value, str) and bool(value) and not value.startswith(('/', './'))
            and '\\' not in value and not any(ord(c) < 32 for c in value)
            and '..' not in PurePosixPath(value).parts)


def validate_policy(policy):
    if (not isinstance(policy, dict) or type(policy.get('schema_version')) is not int
            or policy['schema_version'] != 1):
        raise ValueError('Expected scope policy schema_version 1')
    for key in LISTS:
        entries = policy.get(key)
        if not isinstance(entries, list) or not all(isinstance(x, str) for x in entries):
            raise ValueError(f'Expected a string list: {key}')
        if len(entries) != len(set(entries)):
            raise ValueError(f'Duplicate scope entries: {key}')
        for value in entries:
            if key == 'application_jobs':
                valid = bool(re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_-]*', value))
            else:
                valid = safe_path(value) and (value.endswith('/') == key.endswith('_prefixes'))
            if not valid:
                raise ValueError(f'Invalid scope policy entry: {key}')
    if not policy['application_jobs'] or 'changes' in policy['application_jobs']:
        raise ValueError('Application job list must be nonempty and exclude changes')
    return policy


def matches(path, policy, group):
    return path in policy[group+'_files'] or any(path.startswith(p) for p in policy[group+'_prefixes'])


def classify(paths, policy, complete=True):
    validate_policy(policy)
    if not complete or not all(safe_path(p) for p in paths):
        return dict(scope='full', run_app=True, deploy=False, complete=False,
                    reason='Incomplete change evidence; full checks and no automatic deployment')
    kinds = []
    for path in paths:
        if path.startswith(PROTECTED):
            kinds.append('full')
        elif matches(path, policy, 'skills'):
            kinds.append('skills')
        elif (path in policy['docs_files'] or
              (any(path.startswith(p) for p in policy['docs_prefixes'])
               and PurePosixPath(path).suffix.lower() in {'.md', '.rst', '.txt'})):
            kinds.append('docs')
        else:
            kinds.append('full')
    scope = 'full' if 'full' in kinds else 'skills' if 'skills' in kinds else 'docs'
    deploy = any(matches(p, policy, 'deployment') for p in paths)
    if deploy:
        scope = 'full'  # A deployment input can never take the lightweight lane.
    return dict(scope=scope, run_app=scope == 'full', deploy=deploy, complete=True,
                reason='Changed paths mapped to project-owned checks')


def changed_paths(root, base, head, event):
    if not SHA.fullmatch(base or '') or base == '0'*40 or not SHA.fullmatch(head or ''):
        return [], False
    comparison = base + ('..' if event == 'push' else '...') + head
    result = subprocess.run(['git', '-C', str(root), 'diff', '--no-renames', '--name-only',
                             '-z', comparison, '--'], capture_output=True)
    if result.returncode:
        return [], False
    try:
        return [p for p in result.stdout.decode('utf-8').split('\0') if p], True
    except UnicodeDecodeError:
        return [], False


def check_gate(needs, policy):
    validate_policy(policy)
    if not isinstance(needs, dict):
        raise ValueError('Expected job result data')
    selection = needs.get('changes', {})
    run_app = selection.get('outputs', {}).get('run_app')
    if selection.get('result') != 'success' or run_app not in {'true', 'false'}:
        raise ValueError('Change classification failed or did not produce a decision')
    for name in policy['application_jobs']:
        outcome = needs.get(name, {}).get('result')
        allowed = {'success'} if run_app == 'true' else {'success', 'skipped'}
        if outcome not in allowed:
            raise ValueError(f'Required application job did not satisfy selected scope: {name}')


def deployment_allowed(record, head, repository):
    if (not isinstance(record, dict) or record.get('schema_version') != 1
            or record.get('event') != 'push' or record.get('head') != head
            or not SHA.fullmatch(head or '') or record.get('repository') != repository
            or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository)
            or record.get('scope') not in {'docs', 'skills', 'full'}
            or any(type(record.get(k)) is not bool for k in ['complete', 'deploy', 'run_app'])):
        raise ValueError('Deployment decision does not match the successful trusted push')
    if record['deploy'] and (not record['complete'] or not record['run_app'] or record['scope'] != 'full'):
        raise ValueError('Automatic deployment requires complete runtime-change evidence')
    return record['deploy']


def glob_match(path, pattern):
    """A path glob where `**` spans folders and `*` stays within one."""
    regex = re.escape(pattern).replace(r'\*\*/', '(?:.*/)?').replace(r'\*\*', '.*').replace(r'\*', '[^/]*')
    return re.fullmatch(regex, path) is not None


def validate_services(manifest):
    services = manifest.get('services') if isinstance(manifest, dict) else None
    if manifest.get('schema_version') != 1 or not isinstance(services, dict) or not services:
        raise ValueError('Expected a services manifest, schema_version 1, with at least one service')
    for name, spec in services.items():
        if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_-]*', name) or not isinstance(spec, dict):
            raise ValueError(f'Invalid service: {name}')
        if not spec.get('paths') or not all(isinstance(p, str) and safe_path(p.replace('*', 'x')) for p in spec['paths']):
            raise ValueError(f'{name}: paths must be a nonempty list of repository-relative globs')
        for env, target in (spec.get('deploy') or {}).items():
            if not isinstance(target, dict) or not isinstance(target.get('target'), str):
                raise ValueError(f'{name}: deploy.{env} needs a target')
    shared = manifest.get('shared_paths', [])
    if not isinstance(shared, list) or not all(isinstance(p, str) for p in shared):
        raise ValueError('shared_paths must be a list of globs')
    return manifest


def services_matrix(paths, manifest, environment, complete=True):
    """One entry per affected service, with its checks and, for `environment`, its deploy target and approval.

    Unknown or incomplete changes select every service: a path no service owns could affect any of them."""
    validate_services(manifest)
    services, shared = manifest['services'], manifest.get('shared_paths', [])
    reasons = {}
    touched_shared = [p for p in paths if any(glob_match(p, g) for g in shared)]
    unowned = [p for p in paths if p not in touched_shared
               and not any(glob_match(p, g) for s in services.values() for g in s['paths'])
               and not any(glob_match(p, g) for g in manifest.get('ignored_paths', []))]
    if not complete or unowned or touched_shared:
        why = 'incomplete change evidence' if not complete else (
            f'shared path {touched_shared[0]}' if touched_shared else f'unowned path {unowned[0]}')
        reasons = {name: why for name in services}
    else:
        for name, spec in services.items():
            hit = next((p for p in paths if any(glob_match(p, g) for g in spec['paths'])), None)
            if hit:
                reasons[name] = f'changed {hit}'
    matrix = []
    for name in sorted(reasons):
        spec, deploy = services[name], (services[name].get('deploy') or {}).get(environment) if environment else None
        matrix.append({'service': name, 'checks': spec.get('checks', []), 'reason': reasons[name],
                       'environment': environment if deploy else None, 'target': (deploy or {}).get('target'),
                       'approval': (deploy or {}).get('approval') == 'required'})
    return matrix


def output(path, values):
    if path:
        with path.open('a') as stream:
            for key, value in values.items():
                stream.write(f'{key}={str(value).lower() if type(value) is bool else value}\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    select = subs.add_parser('select')
    select.add_argument('--root', type=Path, default=Path.cwd())
    select.add_argument('--config', type=Path, required=True)
    select.add_argument('--base', default='')
    select.add_argument('--head', required=True)
    select.add_argument('--event', choices=['pull_request', 'push', 'workflow_dispatch'], required=True)
    select.add_argument('--repository', required=True)
    select.add_argument('--force-full', action='store_true')
    select.add_argument('--record', type=Path, required=True)
    select.add_argument('--github-output', type=Path)
    gate = subs.add_parser('gate')
    gate.add_argument('--config', type=Path, required=True)
    gate.add_argument('--needs-json', required=True)
    deploy = subs.add_parser('deployment')
    deploy.add_argument('--record', type=Path, required=True)
    deploy.add_argument('--head', required=True)
    deploy.add_argument('--repository', required=True)
    deploy.add_argument('--github-output', type=Path)
    plan = subs.add_parser('services', help='per-service matrix from a services manifest and the change set')
    plan.add_argument('--root', type=Path, default=Path.cwd())
    plan.add_argument('--manifest', type=Path, required=True)
    plan.add_argument('--base', default='')
    plan.add_argument('--head', required=True)
    plan.add_argument('--event', choices=['pull_request', 'push', 'workflow_dispatch'], required=True)
    plan.add_argument('--environment', help='deploy environment to plan for; omit for checks only')
    plan.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'select':
            if not SHA.fullmatch(args.head):
                raise ValueError('Expected a full candidate commit')
            policy = validate_policy(json.loads(args.config.read_text()))
            paths, complete = changed_paths(args.root, args.base, args.head, args.event)
            record = classify(paths, policy, complete)
            if args.force_full:
                record.update(scope='full', run_app=True, reason='Explicit full-check override')
            record.update(schema_version=1, event=args.event, head=args.head,
                          base=args.base, repository=args.repository)
            args.record.write_text(json.dumps(record, indent=2)+'\n')
            output(args.github_output, {k: record[k] for k in ['scope', 'run_app']})
            print(json.dumps(record, sort_keys=True))
        elif args.command == 'services':
            paths, complete = changed_paths(args.root, args.base, args.head, args.event)
            matrix = services_matrix(paths, json.loads(args.manifest.read_text()), args.environment, complete)
            output(args.github_output, {'matrix': json.dumps({'include': matrix}, separators=(',', ':')),
                                        'any': bool(matrix)})
            print(json.dumps({'include': matrix}, indent=2))
        elif args.command == 'gate':
            check_gate(json.loads(args.needs_json), json.loads(args.config.read_text()))
            print('Selected CI scope satisfied; intentionally skipped jobs are not test passes.')
        else:
            allowed = deployment_allowed(json.loads(args.record.read_text()), args.head, args.repository)
            output(args.github_output, {'deploy': allowed})
            print('Automatic deployment selected.' if allowed else 'No runtime deployment selected.')
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f'CI scope check failed: {error}\n')


if __name__ == '__main__':
    main()
