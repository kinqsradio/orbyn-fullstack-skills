#!/usr/bin/env python3
"""Summarise the labels of the last N merged pull requests. Read-only; posts nothing.

Feeds the self-improvement loop: where contributions come from, which tools build them,
how big they are and which skills keep needing fixes. Standard library plus the GitHub CLI.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pr_labels', HERE / 'pr_labels.py')
labels_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labels_module)


def summarise(prs):
    """prs: [{'labels': [names], 'skills': [updated skill names]}] -> counts by label group."""
    names = [set(pr.get('labels', [])) for pr in prs]
    count = Counter(label for labels in names for label in labels)

    def group(prefix):
        return {k[len(prefix):]: v for k, v in sorted(count.items()) if k.startswith(prefix)}

    updates = [pr for pr in prs if 'skill: update' in pr.get('labels', [])]
    per_skill = Counter(skill for pr in updates for skill in set(pr.get('skills', [])))
    return {
        'merged_prs': len(prs),
        'areas': {**group('area: '), **{k: count[k] for k in ('skill: new', 'skill: update', 'upstream adaptation') if count[k]}},
        'contributors': {'community': count['community'], 'maintainer': len(prs) - count['community'],
                         'first contribution': count['first contribution']},
        'built_with': {**group('built with: '), **({'human only': count['human only']} if count['human only'] else {})},
        'sizes': group('size: '),
        'needs': {'eval run': count['eval run'], 'agent hand-off': count['agent hand-off']},
        'skill_update_share': {skill: {'prs': n, 'share': round(n / len(updates), 3)}
                               for skill, n in sorted(per_skill.items(), key=lambda kv: (-kv[1], kv[0]))},
    }


def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True, timeout=60).stdout


def history(repo, limit):
    """Read-only: the last `limit` merged PRs with their labels and the skills they updated."""
    merged, page = [], 1
    while len(merged) < limit and page <= 10:
        rows = json.loads(gh('api', f'repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page={page}'))
        if not rows:
            break
        merged += [r for r in rows if r.get('merged_at')]
        page += 1
    merged = sorted(merged, key=lambda r: r['merged_at'], reverse=True)[:limit]
    out = []
    for row in merged:
        labels = [label['name'] for label in row.get('labels', [])]
        skills = []
        if 'skill: update' in labels:
            pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/pulls/{row["number"]}/files?per_page=100'))
            skills = labels_module.updated_skills([f for p in pages for f in p])
        out.append({'number': row['number'], 'labels': labels, 'skills': skills})
    return out


def markdown(summary):
    lines = [f"# Merged PR insights ({summary['merged_prs']} PRs)", '']
    for title, key in (('Areas', 'areas'), ('Contributors', 'contributors'), ('Built with', 'built_with'),
                       ('Sizes', 'sizes'), ('Needs', 'needs')):
        lines += [f'## {title}', '']
        lines += [f'- {name}: {value}' for name, value in summary[key].items()] or ['- none']
        lines.append('')
    lines += ['## Share of skill updates per skill', '']
    lines += [f"- {s}: {v['prs']} ({v['share']:.0%})" for s, v in summary['skill_update_share'].items()] or ['- none']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--repo', default=os.environ.get('GH_REPO', ''))
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    options = parser.parse_args()
    try:
        if not options.repo or options.limit < 1:
            raise ValueError('need --repo (or GH_REPO) and a positive --limit')
        summary = summarise(history(options.repo, options.limit))
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print(f'pr_insights: {error}', file=sys.stderr)
        return 2
    print(markdown(summary) if options.format == 'markdown' else json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
