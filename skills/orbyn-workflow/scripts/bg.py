#!/usr/bin/env python3
"""Run a long command in the background and wait for it in one blocking call, on any host with a shell.

`start` returns at once with a job id. `wait` blocks inside this script until the job exits or `--max` seconds
pass, so a long wait costs one model turn instead of one per poll. `status` reads a job without waiting.
Standard library only; POSIX and Windows.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time

RUNNING = 3  # `wait` exit code while the job is still running; a finished job returns its own exit code
LOST = 4  # the supervisor died before recording an exit code


def default_root():
    if os.environ.get('ORBYN_BG_ROOT'):
        return Path(os.environ['ORBYN_BG_ROOT'])
    user = os.environ.get('USER') or os.environ.get('USERNAME') or 'user'
    return Path(tempfile.gettempdir()) / f'orbyn-bg-{user}'


def write_json(path, data):
    """Write atomically, so a reader never sees half a file."""
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        try:
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def detach_flags():
    if os.name == 'nt':
        return {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {'start_new_session': True}


def job_dir(root, job):
    path = root / job
    if not job or '/' in job or '\\' in job or job.startswith('.') or not (path / 'job.json').is_file():
        raise SystemExit(f'bg: no job {job!r} under {root}')
    return path


def tail(path, lines):
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''
    return '\n'.join(text.splitlines()[-lines:]) if lines > 0 else ''


def state(path):
    """The job's current state: done (with its exit code), running, lost or starting."""
    job = read_json(path / 'job.json') or {}
    done = read_json(path / 'exit.json')
    if done is not None:
        return {**job, **done, 'state': 'done'}
    supervisor = read_json(path / 'supervisor.json')
    if supervisor is None:
        started = job.get('created', 0)
        return {**job, 'state': 'starting' if time.time() - started < 30 else 'lost'}
    if alive(supervisor.get('pid')):
        return {**job, **supervisor, 'state': 'running'}
    if (path / 'exit.json').is_file():  # finished between the two reads
        return {**job, **read_json(path / 'exit.json'), 'state': 'done'}
    return {**job, **supervisor, 'state': 'lost'}


def report(path, info, lines):
    info = {**info, 'elapsed_seconds': round((info.get('ended') or time.time()) - info.get('created', time.time()), 1),
            'log': str(path / 'output.log'), 'tail': tail(path / 'output.log', lines)}
    print(json.dumps(info, indent=2))
    if info['state'] == 'done':
        return info['exit_code'] if isinstance(info.get('exit_code'), int) and 0 <= info['exit_code'] < 256 else 1
    return LOST if info['state'] == 'lost' else RUNNING


def cmd_start(args):
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise SystemExit('bg: give the command after --')
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    job = time.strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(3)
    if args.name:
        job += '-' + ''.join(c if c.isalnum() or c in '-_' else '-' for c in args.name)[:40]
    path = root / job
    path.mkdir()
    cwd = str(Path(args.cwd or os.getcwd()).resolve())
    write_json(path / 'job.json', {'id': job, 'command': command, 'cwd': cwd, 'on_done': args.on_done,
                                   'created': time.time()})
    subprocess.Popen([sys.executable, '-I', str(Path(__file__).resolve()), '_supervise', str(path)],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     close_fds=True, **detach_flags())
    print(json.dumps({'id': job, 'root': str(root), 'log': str(path / 'output.log'),
                      'wait': f'bg.py wait {job}'}, indent=2))
    return 0


def cmd_supervise(args):
    """Runs detached: start the command, record its exit code, then run the optional on-done command."""
    path = Path(args.path)
    job = read_json(path / 'job.json')
    with open(path / 'output.log', 'ab') as log:
        try:
            child = subprocess.Popen(job['command'], cwd=job['cwd'], stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT)
        except OSError as error:
            log.write(f'bg: could not start: {error}\n'.encode())
            write_json(path / 'exit.json', {'exit_code': 127, 'ended': time.time(), 'error': str(error)})
            return 0
        write_json(path / 'supervisor.json', {'pid': os.getpid(), 'child_pid': child.pid, 'started': time.time()})
        code = child.wait()
    write_json(path / 'exit.json', {'exit_code': code, 'ended': time.time()})
    if job.get('on_done'):
        env = {**os.environ, 'BG_JOB_ID': job['id'], 'BG_EXIT_CODE': str(code), 'BG_LOG': str(path / 'output.log')}
        with open(path / 'on_done.log', 'ab') as log:
            subprocess.run(job['on_done'], shell=True, cwd=job['cwd'], env=env, stdin=subprocess.DEVNULL,
                           stdout=log, stderr=subprocess.STDOUT)
    return 0


def cmd_wait(args):
    path = job_dir(Path(args.root), args.job)
    deadline = time.monotonic() + max(0.0, args.max)
    while True:
        info = state(path)
        if info['state'] in ('done', 'lost') or time.monotonic() >= deadline:
            return report(path, info, args.tail)
        time.sleep(min(args.interval, max(0.05, deadline - time.monotonic())))


def cmd_status(args):
    path = job_dir(Path(args.root), args.job)
    return report(path, state(path), args.tail)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', default=str(default_root()), help='job folder (default $ORBYN_BG_ROOT or a temp folder)')
    sub = parser.add_subparsers(dest='action', required=True)
    start = sub.add_parser('start', help='start a command detached and print its job id')
    start.add_argument('--name', help='a readable suffix for the job id')
    start.add_argument('--cwd', help='working directory for the command (default: here)')
    start.add_argument('--on-done', help='shell command to run when the job ends; gets BG_JOB_ID, BG_EXIT_CODE, BG_LOG')
    start.add_argument('command', nargs=argparse.REMAINDER, help='-- then the command and its arguments')
    wait = sub.add_parser('wait', help='block until the job ends or --max seconds pass')
    wait.add_argument('job')
    wait.add_argument('--max', type=float, default=540, help='seconds to block; keep it under the host tool timeout')
    wait.add_argument('--tail', type=int, default=40, help='log lines to print')
    wait.add_argument('--interval', type=float, default=1.0, help=argparse.SUPPRESS)
    status = sub.add_parser('status', help='print the job state without waiting')
    status.add_argument('job')
    status.add_argument('--tail', type=int, default=40)
    supervise = sub.add_parser('_supervise', help=argparse.SUPPRESS)
    supervise.add_argument('path')
    args = parser.parse_args(argv)
    return {'start': cmd_start, 'wait': cmd_wait, 'status': cmd_status, '_supervise': cmd_supervise}[args.action](args)


if __name__ == '__main__':
    sys.exit(main())
