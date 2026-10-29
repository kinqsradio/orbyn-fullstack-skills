#!/usr/bin/env python3
"""Opt-in pinned statechart compiler; explicit local prerequisites, no bootstrap."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

TLC_SHA256 = '936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88'
COMPILER = Path(__file__).resolve().parents[1] / 'references/upstream/pstack-statechart/compiler/statechart.ts'


def identity(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f'Not a regular file: {path}')
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def compiler_identity():
    root = COMPILER.parent.parent
    snapshot = json.loads((root / 'snapshot.json').read_text())
    verified = {}
    for name, record in snapshot['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe compiler snapshot path')
        item = identity(root / relative)
        if not Path(item['path']).is_relative_to(root.resolve()) or item['sha256'] != record['sha256']:
            raise ValueError(f'Bundled compiler hash mismatch: {name}')
        verified[name] = item['sha256']
    actual = {str(p.relative_to(root)) for p in (root / 'compiler').rglob('*') if p.is_file()}
    if actual != {name for name in verified if name.startswith('compiler/')}:
        raise ValueError('Unmapped compiler runtime file')
    boundary = Path(__file__).resolve().parents[1] / 'package.json'
    if json.loads(boundary.read_text()).get('type') != 'module':
        raise ValueError('Architect runtime requires its local ESM package boundary')
    verified['orbyn:architect/package.json'] = identity(boundary)['sha256']
    return {'revision': snapshot['revision'], 'files': verified,
            'sha256': hashlib.sha256(json.dumps(verified, sort_keys=True).encode()).hexdigest()}


def capture(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise ValueError(f'Prerequisite failed: {command[0]}: {result.stderr[:1000]}')
    return (result.stdout + result.stderr).strip()


def doctor(args):
    if sys.platform not in ('darwin', 'linux') or not Path('/bin/sh').is_file():
        raise ValueError('Blocked: pinned compiler requires POSIX /bin/sh, process groups and signals; Windows is unsupported.')
    node, java, tlc = (identity(getattr(args, name)) for name in ['node', 'java', 'tlc'])
    compiler = compiler_identity()
    if tlc['sha256'] != TLC_SHA256:
        raise ValueError('Unsupported TLC jar identity; this compiler is pinned to tla2tools 1.7.4 SHA-256 ' + TLC_SHA256)
    node['version'] = capture([node['path'], '--version'])
    match = re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', node['version'])
    if not match:
        raise ValueError('Cannot identify Node version')
    major, minor, _ = map(int, match.groups())
    if not (major >= 24 or major == 23 and minor >= 6 or major == 22 and minor >= 18):
        raise ValueError('Node must support native TypeScript stripping: 22.18+, 23.6+, or 24+; no runtime is installed automatically.')
    java['version'] = capture([java['path'], '-version'])
    version = re.search(r'version "(\d+)', java['version'])
    if not version or int(version[1]) < 11:
        raise ValueError('Java 11 or later is required')
    probe = subprocess.run([java['path'], '-cp', tlc['path'], 'tlc2.TLC', '-help'], capture_output=True, text=True, timeout=10)
    text = (probe.stdout + probe.stderr).strip()
    if probe.returncode not in (0, 1) or 'TLC' not in text or 'model checking' not in text:
        raise ValueError('TLC help probe failed; expected TLC usage from the supplied jar')
    tlc['version'] = next(line.strip() for line in text.splitlines() if 'TLC' in line and 'Version' in line)
    return {'platform': sys.platform, 'node': node, 'java': java, 'tlc': tlc,
            'compiler': compiler, 'bootstrap': False,
            'qualification': 'Prerequisites observed; no model or platform compatibility claim.'}


def process_rows():
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,lstart='], capture_output=True, text=True, check=True)
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 3)
        if len(fields) == 4:
            rows[int(fields[0])] = (int(fields[1]), int(fields[2]), fields[3])
    return rows


def descendants(pid):
    rows = process_rows()
    owned = {pid}
    while True:
        more = {p for p, row in rows.items() if row[0] in owned}
        if more <= owned:
            return {p: rows[p][2] for p in owned if p in rows}
        owned |= more


def interpret(out, status):
    report = out / 'report.md'
    return {'model': 'read each requested property in report; exit 1 may include unchecked properties' if status in (0, 1) else 'incomplete/tool error',
            'projection': 'inspect report and chart independently' if report.is_file() else 'unavailable',
            'source_correspondence': 'not established by compiler', 'replay': 'not performed by compiler',
            'report': str(report) if report.is_file() else None}


def run(args):
    if not 0 < args.timeout <= 3600:
        raise ValueError('Timeout must be positive and at most 3600 seconds')
    # Refuse even empty/symlink destinations: every invocation gets a new owned pair.
    out = Path(args.out).absolute()
    if out.exists() or out.is_symlink():
        raise ValueError('Output must be new; existing output is preserved')
    out.parent.resolve(strict=True)
    records = out.with_name(out.name + '.run')
    records.mkdir()  # exclusive reservation; never overwrite a previous attempt
    receipt = {'status': 'preflight', 'output': str(out), 'records': str(records)}
    (records / 'stdout.txt').touch()
    (records / 'stderr.txt').touch()
    start = time.monotonic()
    child = None
    interrupted = []
    old_handlers = {}
    try:
        tools = doctor(args)
        receipt['tools'] = tools
        spec = identity(args.spec)
        if not spec['path'].endswith('.tla'):
            raise ValueError('Model must be a .tla file')
        config = identity(args.config or str(Path(spec['path']).with_suffix('.cfg')))
        receipt.update(spec=spec, config=config)
        command = [tools['node']['path'], '--disable-warning=ExperimentalWarning', str(COMPILER), spec['path'], '--config', config['path'], '--out', str(out)]
        if args.view:
            view = identity(args.view)
            receipt['trusted_executable_view'] = view
            guard = identity(Path(__file__).with_name('guard-statechart-view.mjs'))
            receipt['view_guard'] = guard
            wrapped = records / 'trusted-view.mjs'
            wrapped.write_text('import * as original from ' + json.dumps(Path(view['path']).as_uri()) + ';\n' +
                               'import { guardView } from ' + json.dumps(Path(guard['path']).as_uri()) + ';\n' +
                               'export const { state, step, group, colors, title } = guardView(original);\n')
            command += ['--view', str(wrapped)]
        receipt['command'] = command
        env = dict(os.environ, JAVA=tools['java']['path'], TLA2TOOLS=tools['tlc']['path'])
        scratch = records / 'tmp'
        scratch.mkdir()
        env['TMPDIR'] = str(scratch)
        for sig in (signal.SIGTERM, signal.SIGINT):
            old_handlers[sig] = signal.signal(sig, lambda number, frame: interrupted.append(number))
        with (records / 'stdout.txt').open('w') as stdout, (records / 'stderr.txt').open('w') as stderr:
            child = subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            receipt['pid'] = child.pid
            receipt['status'] = 'running'
            deadline = time.monotonic() + args.timeout
            while child.poll() is None:
                if interrupted or time.monotonic() >= deadline:
                    receipt['status'] = 'cancelled' if interrupted else 'timeout'
                    owned = descendants(child.pid)
                    child.send_signal(signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)
                    end = time.monotonic() + 5
                    while True:
                        rows = process_rows()
                        remaining = [p for p, birth in owned.items() if p in rows and rows[p][2] == birth]
                        if not remaining or time.monotonic() >= end:
                            break
                        time.sleep(.05)
                    receipt['remaining_observed_processes'] = remaining
                    break
                time.sleep(.05)
        receipt['exit'] = child.returncode
        if receipt['status'] == 'running':
            receipt['status'] = {0: 'completed', 1: 'violations', 2: 'tool_error', 143: 'cancelled'}.get(child.returncode, 'tool_error')
        receipt.update(interpret(out, child.returncode))
        if receipt['status'] in ('timeout', 'cancelled'):
            receipt['model'] = 'incomplete: interrupted check; no pass inferred from partial output'
        return 0 if receipt['status'] == 'completed' else 1 if receipt['status'] == 'violations' else 143 if receipt['status'] == 'cancelled' else 2
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        receipt.update(status='tool_error', error=str(error), model='not checked', projection='unavailable', source_correspondence='not established', replay='not performed')
        with (records / 'stderr.txt').open('a') as log:
            log.write(str(error) + '\n')
        print(str(error), file=sys.stderr)
        return 2
    finally:
        if child is not None and child.poll() is None:
            try:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
                receipt['exception_cleanup'] = 'owned parent settled; descendant cleanup not independently established'
            except (OSError, subprocess.SubprocessError) as error:
                receipt['exception_cleanup'] = 'unresolved: ' + str(error)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        receipt['duration_seconds'] = round(time.monotonic() - start, 3)
        (records / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for mode in ['doctor', 'check']:
        p = sub.add_parser(mode)
        for name in ['node', 'java', 'tlc']:
            p.add_argument('--' + name, required=True, help='Explicit trusted local path; never acquired automatically')
        if mode == 'check':
            p.add_argument('spec')
            p.add_argument('--config')
            p.add_argument('--view', help='Trusted JavaScript module; executes code')
            p.add_argument('--out', required=True)
            p.add_argument('--timeout', type=float, default=60)
    args = parser.parse_args()
    try:
        if args.mode == 'doctor':
            print(json.dumps(doctor(args), indent=2))
            return 0
        return run(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
