#!/usr/bin/env python3
"""Check that lyric, title or logo boxes stay readable and inside the safe area of a video.

Run it on a plate rendered without the overlay, because the check reads the
background under each box. Reads through ffmpeg/ffprobe, writes nothing and prints
a JSON report. Exit 0: every box passes. Exit 1: a box failed. Exit 2: the check
could not run. A pass is a screen; a person still reads the real frames.
"""
import argparse
import json
import re
import subprocess
import sys

COLS, ROWS = 160, 90
# Judge the brightest or darkest tenth of a box: a few specks should not fail it.
WORST_SHARE = .1
BOX = re.compile(r'([\w-]+):([\d.]+),([\d.]+),([\d.]+),([\d.]+)(?:@([\d.]+)-([\d.]+))?$')
HEX = re.compile(r'#?([0-9a-fA-F]{6})$')


def linear(value):
    value /= 255
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


LINEAR = [linear(v) for v in range(256)]


def luminance(r, g, b):
    return .2126 * LINEAR[r] + .7152 * LINEAR[g] + .0722 * LINEAR[b]


def contrast(first, second):
    high, low = max(first, second), min(first, second)
    return (high + .05) / (low + .05)


def parse_box(text):
    match = BOX.match(text)
    if not match:
        raise ValueError(f'Box must be name:x,y,w,h or name:x,y,w,h@from-to, as frame fractions: {text}')
    x, y, w, h = map(float, match.group(2, 3, 4, 5))
    if w <= 0 or h <= 0 or x + w > 1 or y + h > 1:
        raise ValueError(f'Box must fit inside the frame: {text}')
    start = float(match.group(6)) if match.group(6) else 0
    end = float(match.group(7)) if match.group(7) else float('inf')
    if end <= start:
        raise ValueError(f'Box time range is empty: {text}')
    return {'name': match.group(1), 'x': x, 'y': y, 'w': w, 'h': h, 'from': start, 'to': end}


def parse_color(text):
    match = HEX.match(text)
    if not match:
        raise ValueError(f'Colour must be #rrggbb: {text}')
    return luminance(*bytes.fromhex(match.group(1)))


def duration(path, ffprobe):
    result = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('ffprobe failed: ' + result.stderr.strip()[:300])
    text = result.stdout.strip()
    # A still image reports N/A, so it is checked as one frame.
    return float(text) if re.fullmatch(r'[\d.]+', text) else 0.


def frames(path, seconds, samples, ffmpeg):
    """Yield (time, area-averaged RGB frame) at even steps through the video."""
    rate = samples / seconds if seconds else 1
    size = COLS * ROWS * 3
    pace = f'fps={rate:.6f},' if seconds else ''  # The fps filter drops a lone still image.
    command = [ffmpeg, '-v', 'error', '-i', path, '-frames:v', str(samples),
               '-vf', f'{pace}scale={COLS}:{ROWS}:flags=area,format=rgb24',
               '-f', 'rawvideo', '-']
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as decoder:
        index = 0
        while True:
            frame = decoder.stdout.read(size)
            if len(frame) < size:
                break
            yield index / rate, frame
            index += 1
        errors = decoder.stderr.read().decode(errors='replace')[:300]
    if decoder.returncode:
        raise RuntimeError('ffmpeg failed: ' + errors)
    if not index:
        raise RuntimeError('No decoded frames')


def box_contrast(frame, box, foreground):
    """Contrast against the worst tenth of the cells under the box."""
    left, right = int(box['x'] * COLS), max(int(box['x'] * COLS) + 1, round((box['x'] + box['w']) * COLS))
    top, bottom = int(box['y'] * ROWS), max(int(box['y'] * ROWS) + 1, round((box['y'] + box['h']) * ROWS))
    values = []
    for row in range(top, min(bottom, ROWS)):
        for column in range(left, min(right, COLS)):
            at = (row * COLS + column) * 3
            values.append(contrast(foreground, luminance(frame[at], frame[at + 1], frame[at + 2])))
    values.sort()
    return values[int(len(values) * WORST_SHARE)]


def in_safe_area(box, margin):
    return (box['x'] >= margin and box['y'] >= margin
            and box['x'] + box['w'] <= 1 - margin and box['y'] + box['h'] <= 1 - margin)


def check(path, boxes, foreground, minimum, margin, samples, ffmpeg, ffprobe):
    seconds = duration(path, ffprobe)
    worst = {box['name']: None for box in boxes}
    seen = {box['name']: 0 for box in boxes}
    for time, frame in frames(path, seconds, samples if seconds else 1, ffmpeg):
        for box in boxes:
            if not seconds or box['from'] <= time < box['to']:
                value = box_contrast(frame, box, foreground)
                seen[box['name']] += 1
                if worst[box['name']] is None or value < worst[box['name']][0]:
                    worst[box['name']] = (value, time)
    results = []
    for box in boxes:
        name = box['name']
        if worst[name] is None:
            raise RuntimeError(f'No sampled frame falls inside box {name}; raise --samples')
        value, time = worst[name]
        results.append({
            'name': name, 'worst_contrast': round(value, 2), 'at_seconds': round(time, 2),
            'frames_checked': seen[name], 'contrast_pass': value >= minimum,
            'safe_area_pass': in_safe_area(box, margin),
        })
    passed = all(r['contrast_pass'] and r['safe_area_pass'] for r in results)
    return {
        'status': 'pass' if passed else 'fail', 'min_contrast': minimum, 'safe_margin': margin, 'boxes': results,
        'limits': ['Checks a plate at sampled frames, so moments between samples are unchecked',
                   'Judges the worst tenth of each box, so it cannot see stroke, shadow or font weight',
                   'Screening only; read the real frames in the intended format'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('video', help='Plate video or still rendered without the overlay')
    parser.add_argument('--box', action='append', required=True, help='name:x,y,w,h[@from-to], as frame fractions and seconds')
    parser.add_argument('--color', default='#ffffff', help='Overlay colour, #rrggbb')
    parser.add_argument('--min-contrast', type=float, default=4.5, help='Use 3 for a logo or large display text')
    parser.add_argument('--safe-margin', type=float, default=.05, help='Frame fraction to keep clear on every side')
    parser.add_argument('--samples', type=int, default=48)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    options = parser.parse_args()
    try:
        if options.samples < 1:
            raise ValueError('--samples must be at least 1')
        boxes = [parse_box(text) for text in options.box]
        if len({box['name'] for box in boxes}) != len(boxes):
            raise ValueError('Box names must be unique')
        report = check(options.video, boxes, parse_color(options.color), options.min_contrast,
                       options.safe_margin, options.samples, options.ffmpeg, options.ffprobe)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f'legibility-check: {error}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
