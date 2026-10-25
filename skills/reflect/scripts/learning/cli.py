"""Natural-language agents call this explicit CLI; it never captures chats or pushes Git."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from . import artifacts, store
from .schema import CATEGORIES, DOMAINS, Error, VERSION, require


def parser():
    p = argparse.ArgumentParser(description='Opt-in local engineering memory (Python 3.11+). No daemon or remote effects.')
    p.add_argument('--root', type=Path, required=True, help='Explicit private data directory outside Git')
    scope = p.add_mutually_exclusive_group()
    scope.add_argument('--project', type=Path)
    scope.add_argument('--personal', action='store_true')
    scope.add_argument('--reusable', action='store_true')
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('init', 'mode'):
        s = sub.add_parser(command)
        s.add_argument('--mode', choices=['off', 'manual'], default='off')
    sub.add_parser('register')
    sub.add_parser('taxonomy')
    sub.add_parser('cleanup')
    sub.add_parser('backup')
    for command in ('remember', 'import'):
        s = sub.add_parser(command)
        s.add_argument('--input', required=True, type=Path)
        s.add_argument('--op', required=True)
    for command in ('find', 'list'):
        s = sub.add_parser(command)
        s.add_argument('--query', default='')
        s.add_argument('--category', choices=CATEGORIES)
        s.add_argument('--domain', choices=DOMAINS)
        s.add_argument('--tag')
        s.add_argument('--include-inactive', action='store_true')
        s.add_argument('--applicability', type=Path, help='JSON of modules/platforms/versions/branches')
        s.add_argument('--limit', type=int, default=5)
        s.add_argument('--budget', type=int, default=4000)
    s = sub.add_parser('show')
    s.add_argument('id')
    s = sub.add_parser('revalidate')
    s.add_argument('--input', type=Path, required=True)
    s = sub.add_parser('update', help='Correct, retag or recategorize a frozen selection')
    s.add_argument('--selection', type=Path, required=True, help='JSON object mapping IDs to expected revisions')
    s.add_argument('--input', type=Path, required=True, help='JSON patch of editable fields')
    s.add_argument('--op', required=True)
    for command in ('archive', 'forget', 'check-sources'):
        s = sub.add_parser(command)
        s.add_argument('id')
        s.add_argument('--revision', type=int, required=True)
        s.add_argument('--op', required=True)
    s = sub.add_parser('merge-tag')
    s.add_argument('--old', required=True)
    s.add_argument('--new', required=True)
    s.add_argument('--selection', type=Path, required=True)
    s.add_argument('--op', required=True)
    s = sub.add_parser('export')
    s.add_argument('--selection', type=Path, required=True)
    s.add_argument('--format', choices=['json', 'markdown', 'html'], default='json')
    s = sub.add_parser('restore')
    s.add_argument('--artifact', required=True)
    s.add_argument('--generation', type=int, required=True)
    s.add_argument('--op', required=True)
    s = sub.add_parser('propose')
    s.add_argument('--input', type=Path, required=True)
    s.add_argument('--selection', type=Path, required=True)
    s.add_argument('--op', required=True)
    s = sub.add_parser('candidate')
    s.add_argument('id')
    s = sub.add_parser('prepare-patch')
    s.add_argument('id')
    s.add_argument('--checkout', type=Path, required=True)
    s.add_argument('--files', nargs='+', required=True)
    s.add_argument('--reviewed', action='store_true', help='Exact outgoing content has been reviewed within user scope')
    return p


def dispatch(args):
    selection = dict(project=args.project, personal=args.personal, reusable=args.reusable)
    if args.command == 'init':
        return store.init(args.root, args.mode)
    if args.command == 'mode':
        return store.set_mode(args.root, args.mode)
    if args.command == 'register':
        return store.register(args.root, selection)
    # Resolve the catalog relative to this package, so host discovery symlinks work.
    catalog = Path(__file__).resolve().parents[3] / 'catalog.json'
    skills = {r['name'] for r in artifacts.read_json(catalog)['skills']}
    with store.Memory(args.root, selection, skills) as memory:
        read = artifacts.read_json
        cmd = args.command
        if cmd == 'taxonomy':
            return {'schema_version': VERSION, 'categories': CATEGORIES, 'domains': DOMAINS, 'aliases': memory.aliases()}
        if cmd == 'remember':
            return memory.create(read(args.input, 32768), args.op)
        if cmd == 'import':
            return artifacts.import_records(memory, read(args.input), args.op)
        if cmd in ('find', 'list'):
            return memory.find(args.query, args.category, args.domain, args.tag, args.include_inactive,
                               read(args.applicability) if args.applicability else None, args.limit, args.budget)
        if cmd == 'show':
            return memory.show(args.id)
        if cmd == 'revalidate':
            return memory.revalidate(read(args.input))
        if cmd == 'update':
            return memory.update_many(read(args.selection), read(args.input, 32768), args.op)
        if cmd == 'archive':
            return memory.update_many({args.id: args.revision}, {'status': 'archived'}, args.op)
        if cmd == 'forget':
            return memory.forget(args.id, args.revision, args.op)
        if cmd == 'merge-tag':
            return memory.merge_tag(args.old, args.new, read(args.selection), args.op)
        if cmd == 'cleanup':
            return memory.cleanup()
        if cmd == 'export':
            return artifacts.export(memory, read(args.selection), args.format)
        if cmd == 'backup':
            return artifacts.backup(memory)
        if cmd == 'restore':
            return artifacts.restore(memory, args.artifact, args.generation, args.op)
        if cmd == 'propose':
            return artifacts.propose(memory, read(args.input), read(args.selection), args.op)
        if cmd == 'candidate':
            return artifacts.candidate(memory, args.id)
        if cmd == 'check-sources':
            return artifacts.check_sources(memory, args.id, args.revision, args.project, args.op)
        if cmd == 'prepare-patch':
            return artifacts.prepare_patch(memory, args.id, args.checkout, args.files, args.reviewed)
    raise Error('Unsupported command')


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        require(sys.version_info >= (3, 11), 'Python 3.11+ required')
        result = dispatch(args)
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False, indent=2))
        return 0
    except (Error, OSError, sqlite3.Error, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
        return 1
