#!/usr/bin/env python3
"""Screen a rendered video against the WCAG 2.2 three-flashes thresholds.

Reads the video through ffmpeg/ffprobe, writes nothing, and prints a JSON report.
Exit 0: at most three flashes in every second. Exit 1: a threshold was exceeded.
Exit 2: the check could not run. A pass is a screen, not a certified analysis.
"""
import argparse
from collections import deque
import json
import subprocess
import sys

COLS, ROWS = 63, 36
# 341x256 of a 1024x768 screen is a third of each side and estimates a 10 degree field.
WINDOW_COLS, WINDOW_ROWS = COLS // 3, ROWS // 3
MAX_AREA_CELLS = WINDOW_COLS * WINDOW_ROWS // 4
MAX_FLASHES = 3
SWING = .1
DARK_LIMIT = .8
RED_RATIO = .8
RED_CHROMA = .2
D65_UV = (.1978, .4683)
LINEAR = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in (v / 255 for v in range(256))]


def color_state(packed):
    r, g, b = LINEAR[packed >> 16], LINEAR[packed >> 8 & 255], LINEAR[packed & 255]
    x, y, z = .4124 * r + .3576 * g + .1805 * b, .2126 * r + .7152 * g + .0722 * b, .0193 * r + .1192 * g + .9505 * b
    d = x + 15 * y + 3 * z
    total = r + g + b
    return y, (4 * x / d, 9 * y / d) if d > 1e-6 else D65_UV, total > 1e-6 and r / total >= RED_RATIO


class Scene:
    """Tracks opposing transitions per cell, then groups concurrent cells into windows."""

    def __init__(self, fps):
        self.fps = fps
        self.coincidence = max(1, round(fps / 20))
        self.index = 0
        self.colors = {}
        self.general = [[None, None, 0] for _ in range(COLS * ROWS)]  # low, high, direction
        self.red = [[None, 0] for _ in range(COLS * ROWS)]  # reference state, direction
        self.tracks = {'general': Track(self), 'red': Track(self)}

    def add(self, frame):
        rising, falling, toward, away = [], [], [], []
        for cell in range(COLS * ROWS):
            at = cell * 3
            packed = frame[at] << 16 | frame[at + 1] << 8 | frame[at + 2]
            state = self.colors.get(packed)
            if state is None:
                state = self.colors[packed] = color_state(packed)
            value, chroma, saturated = state

            general = self.general[cell]
            if general[0] is None:
                general[0] = general[1] = value
            if value < general[0]:
                general[0] = value
            if value > general[1]:
                general[1] = value
            if general[2] <= 0 and value - general[0] >= SWING and general[0] < DARK_LIMIT:
                general[1] = value
                general[2] = 1
                rising.append(cell)
            elif general[2] >= 0 and general[1] - value >= SWING and value < DARK_LIMIT:
                general[0] = value
                general[2] = -1
                falling.append(cell)

            red = self.red[cell]
            if red[0] is None:
                red[0] = state
            reference = red[0]
            if (saturated or reference[2]) and ((chroma[0] - reference[1][0]) ** 2 + (chroma[1] - reference[1][1]) ** 2) ** .5 > RED_CHROMA:
                direction = 1 if saturated else -1
                red[0] = state
                if direction != red[1]:
                    red[1] = direction
                    (toward if saturated else away).append(cell)
        self.tracks['general'].add(rising, falling)
        self.tracks['red'].add(toward, away)
        self.index += 1


class Track:
    def __init__(self, scene):
        self.scene = scene
        self.recent = (deque(), deque())
        self.last = {}
        self.history = {}
        self.worst = 0
        self.worst_frame = None
        self.worst_window = None

    def add(self, first, second):
        for direction, cells in ((1, first), (-1, second)):
            recent = self.recent[direction < 0]
            recent.append(cells)
            if len(recent) > self.scene.coincidence:
                recent.popleft()
            if cells and sum(map(len, recent)) > MAX_AREA_CELLS:
                self.windows(direction, recent)

    def windows(self, direction, recent):
        marks = bytearray(COLS * ROWS)
        for cells in recent:
            for cell in cells:
                marks[cell] = 1
        # A summed-area table prices each of the sliding windows at four lookups.
        table = [[0] * (COLS + 1) for _ in range(ROWS + 1)]
        for row in range(ROWS):
            above, line, total = table[row], table[row + 1], 0
            for col in range(COLS):
                total += marks[row * COLS + col]
                line[col + 1] = above[col + 1] + total
        for top in range(ROWS - WINDOW_ROWS + 1):
            high, low = table[top], table[top + WINDOW_ROWS]
            for left in range(COLS - WINDOW_COLS + 1):
                area = low[left + WINDOW_COLS] - low[left] - high[left + WINDOW_COLS] + high[left]
                if area > MAX_AREA_CELLS and self.last.get((top, left)) != direction:
                    self.transition((top, left), direction)

    def transition(self, window, direction):
        self.last[window] = direction
        times = self.history.setdefault(window, deque())
        times.append(self.scene.index)
        while self.scene.index - times[0] >= self.scene.fps:
            times.popleft()
        flashes = len(times) // 2
        if flashes > self.worst:
            self.worst, self.worst_frame, self.worst_window = flashes, times[0], window

    def report(self, fps):
        return {
            'worstFlashesPerSecond': self.worst,
            'startsAtSeconds': None if self.worst_frame is None else round(self.worst_frame / fps, 3),
            'windowCell': None if self.worst_window is None else {'row': self.worst_window[0], 'column': self.worst_window[1]},
        }


def frame_rate(ffprobe, path):
    result = subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=avg_frame_rate', '-of', 'json', path], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('ffprobe failed: ' + result.stderr.strip())
    streams = json.loads(result.stdout).get('streams', [])
    numerator, _, denominator = (streams[0]['avg_frame_rate'] if streams else '0/1').partition('/')
    fps = float(numerator) / float(denominator or 1) if float(denominator or 1) else 0
    if fps <= 0:
        raise RuntimeError('No video stream with a frame rate')
    return fps


def check(path, ffmpeg='ffmpeg', ffprobe='ffprobe'):
    fps = frame_rate(ffprobe, path)
    scene = Scene(fps)
    size = COLS * ROWS * 3
    decoder = subprocess.Popen([ffmpeg, '-v', 'error', '-i', path, '-map', '0:v:0', '-vf', f'scale={COLS}:{ROWS}:flags=area,format=rgb24', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while True:
            frame = decoder.stdout.read(size)
            if not frame:
                break
            if len(frame) != size:
                raise RuntimeError('Decoder returned a partial frame')
            scene.add(frame)
    finally:
        decoder.stdout.close()
        errors = decoder.stderr.read().decode(errors='replace').strip()
        decoder.stderr.close()
        code = decoder.wait()
    if code:
        raise RuntimeError('ffmpeg failed: ' + errors)
    if not scene.index:
        raise RuntimeError('No decoded frames')
    general, red = scene.tracks['general'], scene.tracks['red']
    return {
        'status': 'pass' if max(general.worst, red.worst) <= MAX_FLASHES else 'exceeds-three-flashes',
        'frames': scene.index,
        'fps': round(fps, 3),
        'limit': MAX_FLASHES,
        'general': general.report(fps),
        'red': red.report(fps),
        'method': f'{COLS}x{ROWS} area-averaged grid; more than 25% of any third-by-third window, moving together within {scene.coincidence} frames',
        'limits': ['Screening only, not a Harding or PEAT certification', 'Averaging hides patterns finer than a grid cell', 'Saturated-red ratio uses linear RGB', 'Assumes the frame is the whole screen'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('video')
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    options = parser.parse_args()
    try:
        report = check(options.video, options.ffmpeg, options.ffprobe)
    except (OSError, RuntimeError, ValueError) as error:
        print(f'flash-check: {error}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
