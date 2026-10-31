#!/usr/bin/env python3
"""Generate original deterministic click/silence fixtures using only stdlib."""
import argparse
import math
from pathlib import Path
import struct
import wave
from audio_tools import digest, new_output, write_json


def generate(output):
    sample_rate, duration = 22050, 8
    beats = [i / 2 for i in range(1, 16)]
    for name in ['clicks', 'silence']:
        with wave.open(str(output / (name + '.wav')), 'wb') as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(sample_rate)
            frames = bytearray()
            for sample in range(sample_rate * duration):
                t = sample / sample_rate
                previous = math.floor(t * 2) / 2
                elapsed = t - previous
                amplitude = .8 * math.exp(-elapsed * 110) * math.sin(2 * math.pi * 1000 * elapsed) if name == 'clicks' and .5 <= previous <= 7.5 and elapsed < .08 else 0
                frames.extend(struct.pack('<h', round(amplitude * 32767)))
            target.writeframes(frames)
    write_json(output / 'truth.json', {'sampleRate': sample_rate, 'duration': duration,
               'tempo': 120, 'beats': beats, 'source': 'Original synthetic pulses; not a musical quality benchmark',
               'files': {name: digest(output / name) for name in ['clicks.wav', 'silence.wav']}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    generate(new_output(parser.parse_args().out))
