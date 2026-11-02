#!/usr/bin/env python3
"""Run the unit-test modules in parallel, optionally only those a change can affect.

Each module runs in its own process, exactly as `python3 -m unittest discover -s tests`
would load it. `--changed-from <base>` selects modules by scanning each test module for
the paths and script names it references; it always adds a protected set and fails
closed to the whole suite when it cannot explain a changed path.
"""
import argparse
import ast
import concurrent.futures
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT/'tests'

# Guard destructive or security code; they run on every pull request.
PROTECTED = ('test_worktree_retire', 'test_security_workflow', 'test_pr_gate', 'test_harness', 'test_memory',
             'test_skill_contracts', 'test_portable_distribution', 'test_repository_workspaces')
# A change under these, or to the selection logic, cannot be mapped safely: run everything.
RUN_ALL_PREFIXES = ('scripts/', '.github/', 'distribution/')
SELECTION_FILES = ('scripts/run_tests.py', 'tests/test_run_tests.py')
CODE_SUFFIXES = {'.py', '.mjs', '.js', '.cjs', '.ts', '.tsx', '.sh'}
GENERIC = {'SKILL.md', 'README.md', 'LICENSE', 'LICENSE.md', 'index.md', 'package.json', 'catalog.json'}
MIN_STEM = 6  # shorter script stems are too generic to count as a reference


def discover(tests=TESTS):
    return sorted(p.stem for p in Path(tests).glob('test_*.py'))


def read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def has(text, key):
    return re.search(r'(?<![\w.-])' + re.escape(key) + r'(?![\w-])', text) is not None


def keys_for(path):
    """Strings a test could use to name this path: itself, its directories, script name and skill name."""
    parts = path.split('/')
    keys = {path} | ({parts[-1]} - GENERIC)
    keys.update('/'.join(parts[:n]) for n in range(2, len(parts)))
    stem = Path(parts[-1]).stem
    if Path(parts[-1]).suffix in CODE_SUFFIXES and len(stem) >= MIN_STEM:
        keys.add(stem)
    if len(parts) > 2 and parts[0] == 'skills':
        keys.add(parts[1])
    return keys


def code_files(root):
    found = {}
    for top in ('skills', 'scripts', 'tools'):
        base = Path(root)/top
        if base.is_dir():
            for p in base.rglob('*'):
                if p.suffix in CODE_SUFFIXES and p.is_file() and 'node_modules' not in p.parts and '__pycache__' not in p.parts:
                    found[p.relative_to(root).as_posix()] = None
    return found


def expand(changed, root):
    """Map each changed path, and every code file that references it (repeatedly), to the changed path it came from."""
    files, cache = code_files(root), {}

    def text(name):
        if name not in cache:
            cache[name] = read(Path(root)/name)
        return cache[name]

    origin = {c: c for c in changed}
    frontier = [c for c in changed if Path(c).suffix in CODE_SUFFIXES]
    while frontier:
        current = frontier.pop()
        stem = Path(current).stem
        for other in files:
            if other not in origin and (has(text(other), Path(current).name) or (len(stem) >= MIN_STEM and has(text(other), stem))):
                origin[other] = origin[current]
                frontier.append(other)
    return origin


def helper_modules(modules, tests=TESTS):
    """Test files other test files import: editing one affects every importer."""
    names = {m: read(Path(tests)/f'{m}.py') for m in modules}
    return {m for m in modules if any(o != m and re.search(rf'^\s*(from|import)\s+{re.escape(m)}\b', t, re.M) for o, t in names.items())}


def select(changed, modules, root=ROOT):
    """Return (chosen {module: reason}, run_all reason or None) for the changed repository paths."""
    tests = Path(root)/'tests'
    chosen = {m: 'protected set: guards destructive or security code' for m in PROTECTED if m in modules}
    helpers = helper_modules(modules, tests)
    changed = [c for c in changed if c]
    for path in changed:
        if path in SELECTION_FILES:
            return chosen, f'{path} is the selection logic'
        if path.startswith(RUN_ALL_PREFIXES):
            return chosen, f'{path} is shared infrastructure (scripts/, .github/ or distribution/)'
        if path.startswith('tests/'):
            name = Path(path).stem
            if path == f'tests/{name}.py' and name in modules and name not in helpers:
                chosen.setdefault(name, f'{path} changed')
                continue
            return chosen, f'{path} is a test helper or fixture'
    texts = {m: read(tests/f'{m}.py') for m in modules}
    changed = [c for c in changed if not c.startswith('tests/')]
    origin, mapped = expand(changed, root), set()
    for module in modules:
        for ref in sorted(origin):
            hit = next((k for k in sorted(keys_for(ref)) if has(texts[module], k)), None)
            if hit:
                mapped.add(origin[ref])
                via = '' if ref == origin[ref] else f' (via {ref}, which references it)'
                chosen.setdefault(module, f'{origin[ref]} changed; {module}.py references {hit!r}{via}')
                break
    for path in changed:
        if path not in mapped:
            return chosen, f'{path} maps to no test module'
    return chosen, None


def changed_paths(base, root=ROOT):
    """Committed changes since the merge base, working-tree edits and untracked files; None when Git cannot say."""
    def git(*args):
        done = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
        return None if done.returncode else [l for l in done.stdout.splitlines() if l]
    committed = git('diff', '--name-only', f'{base}...HEAD')
    if committed is None:
        committed = git('diff', '--name-only', base, 'HEAD')
    dirty, untracked = git('diff', '--name-only', 'HEAD'), git('ls-files', '--others', '--exclude-standard')
    if committed is None or dirty is None or untracked is None:
        return None
    return sorted(set(committed) | set(dirty) | set(untracked))


def shards(name, tests=TESTS):
    """Classes a module lists in a literal `SHARDS = [...]`, so its slowest module can run as parallel processes."""
    try:
        for node in ast.parse(read(Path(tests)/f'{name}.py')).body:
            if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'SHARDS' for t in node.targets):
                found = ast.literal_eval(node.value)
                if isinstance(found, (list, tuple)) and all(isinstance(c, str) for c in found):
                    return list(found)
    except (SyntaxError, ValueError):
        pass
    return []


def run_unit(unit, python, root=ROOT):
    """One process: a whole module, exactly as `unittest discover -s tests` loads it, or one shard class of it."""
    name, shard = unit
    started = time.monotonic()
    if shard:
        env = {**os.environ, 'PYTHONPATH': os.pathsep.join(filter(None, [str(Path(root)/'tests'), os.environ.get('PYTHONPATH')]))}
        command = [python, '-m', 'unittest', f'{name}.{shard}']
    else:
        env = None
        command = [python, '-m', 'unittest', 'discover', '-s', 'tests', '-p', f'{name}.py']
    done = subprocess.run(command, cwd=root, capture_output=True, text=True, env=env)
    output = done.stdout + done.stderr
    ran = re.search(r'^Ran (\d+) tests?', output, re.M)
    return {'module': name, 'unit': f'{name}.{shard}' if shard else name, 'seconds': time.monotonic() - started,
            'tests': int(ran.group(1)) if ran else 0, 'returncode': done.returncode, 'output': output}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 1, help='parallel processes (default: CPU count)')
    parser.add_argument('--changed-from', metavar='BASE', help='select only modules a change since BASE can affect')
    parser.add_argument('--slowest', type=int, default=5, help='how many slow modules to list')
    args = parser.parse_args(argv)
    modules = discover()
    if not modules:
        print('no test modules found', file=sys.stderr)
        return 2
    reasons = {m: 'full suite' for m in modules}
    if args.changed_from:
        changed = changed_paths(args.changed_from)
        if changed is None:
            print(f'cannot list changes from {args.changed_from}; running the full suite')
        else:
            print(f'{len(changed)} changed path(s) since {args.changed_from}')
            chosen, everything = select(changed, modules)
            if everything:
                print(f'running the full suite: {everything}')
            else:
                reasons = chosen
    for module in sorted(reasons):
        print(f'  {module}: {reasons[module]}')
    units = [(m, c) for m in reasons for c in (shards(m) or [None])]
    units.sort(key=lambda u: -(TESTS/f'{u[0]}.py').stat().st_size)  # biggest first keeps the workers busy
    started = time.monotonic()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for result in pool.map(lambda u: run_unit(u, sys.executable), units):
            results.append(result)
            if result['returncode']:
                print(f"\n=== FAILED {result['unit']} (exit {result['returncode']}) ===\n{result['output']}")
    failed = [r for r in results if r['returncode']]
    print(f"\n{len(reasons)} module(s), {sum(r['tests'] for r in results)} tests, {len(failed)} failed, "
          f"{time.monotonic() - started:.1f}s wall with {args.jobs} job(s)")
    print('slowest modules (a sharded module shows its slowest class):')
    for r in sorted(results, key=lambda r: -r['seconds'])[:args.slowest]:
        print(f"  {r['seconds']:7.1f}s  {r['tests']:4d} tests  {r['unit']}")
    if failed:
        print('failed: ' + ', '.join(r['unit'] for r in failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
