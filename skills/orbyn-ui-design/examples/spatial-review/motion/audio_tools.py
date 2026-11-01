"""Local audio CLI support; imports no analysis/model package at startup."""
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Nonfinite JSON constant: ' + value)


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Nonfinite JSON number')
    return number


def read_json(path, limit=8 * 1024 * 1024):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Expected a bounded local JSON file')
    return json.loads(path.read_bytes(), object_pairs_hook=unique_fields,
                      parse_constant=reject_constant, parse_float=finite_float)


def write_json(path, value, compact=False):
    options = {'separators': (',', ':')} if compact else {'indent': 2}
    Path(path).write_text(json.dumps(value, allow_nan=False, **options) + '\n')


def new_output(path):
    result = Path(path).absolute()
    if not result.parent.is_dir() or result.parent.resolve() != result.parent:
        raise ValueError('Output requires an existing real owner directory')
    result.mkdir()  # Exclusive; failed attempts are retained, never reused.
    return result


def regular_file(path, max_bytes=512 * 1024 * 1024):
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError('Expected an explicitly selected bounded regular file')
    return path


def stop(child):
    if child.poll() is not None:
        return
    try:
        if os.name == 'posix':
            os.killpg(child.pid, signal.SIGTERM)
        else:
            child.terminate()
    except ProcessLookupError:
        return
    try:
        child.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == 'posix':
            os.killpg(child.pid, signal.SIGKILL)
        else:
            child.kill()
        child.communicate(timeout=5)


def cancellation_signals():
    """Only CLI-owned processes install handlers, never importing applications."""
    def cancel(_signum, _frame):
        raise KeyboardInterrupt('Audio job cancelled')
    signal.signal(signal.SIGTERM, cancel)


def run(command, output, label, timeout=120):
    # Keep stdout separate: ffprobe JSON must never include diagnostic stderr.
    stdout_path, stderr_path = output / (label + '.stdout'), output / (label + '.log')
    with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                 start_new_session=os.name == 'posix')
        started = time.monotonic()
        try:
            while child.poll() is None:
                if time.monotonic() - started > timeout:
                    raise subprocess.TimeoutExpired(command, timeout)
                if stdout_path.stat().st_size + stderr_path.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError('Command diagnostic budget exceeded')
                try:
                    child.wait(timeout=.05)
                except subprocess.TimeoutExpired:
                    pass
            if stdout_path.stat().st_size + stderr_path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError('Command diagnostic budget exceeded')
            if child.returncode:
                raise ValueError(label + ' failed; inspect retained logs')
            return stdout_path.read_text()
        finally:
            stop(child)
            write_json(output / (label + '.command.json'),
                       {'command': command, 'exit': child.returncode})


def decode_audio(source, output, ffmpeg, ffprobe, sample_rate, max_seconds):
    probe = json.loads(run([ffprobe, '-v', 'error', '-protocol_whitelist', 'file,pipe',
                           '-show_streams', '-show_format', '-of', 'json', str(source)],
                          output, 'probe'))
    streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
    duration = float(probe.get('format', {}).get('duration', 0))
    if not streams or not 0 < duration <= max_seconds:
        raise ValueError('Missing audio stream or duration outside declared budget')
    allowed = {'wav', 'mp3', 'flac', 'ogg', 'aac', 'mov,mp4,m4a,3gp,3g2,mj2', 'matroska,webm', 'aiff'}
    if probe.get('format', {}).get('format_name') not in allowed:
        raise ValueError('Unsupported local audio container')
    decoded = output / 'analysis.wav'
    run([ffmpeg, '-v', 'error', '-nostdin', '-n', '-protocol_whitelist', 'file,pipe',
         '-i', str(source), '-map', '0:a:0', '-t', str(max_seconds), '-ac', '1',
         '-ar', str(sample_rate), '-c:a', 'pcm_s16le', str(decoded)], output, 'decode')
    return decoded, {'sha256': digest(source), 'bytes': source.stat().st_size,
                     'duration': duration, 'sourceSampleRate': int(streams[0]['sample_rate']),
                     'sourceChannels': int(streams[0]['channels'])}


def receipt(output, status, source, **extra):
    value = {'status': status, 'inputSha256': digest(source), **extra}
    if status == 'completed':
        value['outputs'] = {p.name: digest(p) for p in output.iterdir()
                            if p.is_file() and p.name != 'receipt.json'}
    write_json(output / 'receipt.json', value)
    return value
