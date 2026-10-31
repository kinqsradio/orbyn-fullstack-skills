#!/usr/bin/env python3
"""Run bounded local ASR/alignment using an explicitly prepared, hash-bound profile."""
import argparse
from pathlib import Path
import sys
from audio_tools import cancellation_signals, decode_audio, digest, new_output, read_json, receipt, regular_file, run, write_json
from speech_profile import verify_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['input', 'models', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--segments', type=Path, help='Optional caller-authored start/end/text segments instead of ASR')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    source = regular_file(args.input)
    if not 1 <= args.threads <= 8 or not 10 <= args.timeout <= 1800 or not 1 <= args.max_seconds <= 3600:
        raise ValueError('Invalid speech job budget')
    output = new_output(args.out)
    original = digest(source)
    receipt(output, 'preparing', source)
    try:
        profile, _roots = verify_profile(args.models)
        decoded, audio = decode_audio(source, output, args.ffmpeg, args.ffprobe, 16000, args.max_seconds)
        command = [sys.executable, str(Path(__file__).with_name('speech_worker.py')),
                   '--audio', str(decoded), '--audio-sha', original,
                   '--models', str(args.models.resolve()), '--out', str(output),
                   '--device', args.device, '--threads', str(args.threads)]
        if args.segments:
            segments = read_json(regular_file(args.segments, 8 * 1024 * 1024))
            write_json(output / 'segments-input.json', segments)
            command += ['--segments', str(output / 'segments-input.json')]
        run(command, output, 'speech-worker', timeout=args.timeout)
        if digest(source) != original:
            raise ValueError('Audio changed during alignment')
        receipt(output, 'completed', source, profileSha256=digest(args.models),
                toolSources={p.name: digest(p) for p in [Path(__file__), Path(__file__).with_name('audio_tools.py'), Path(__file__).with_name('speech_worker.py'), Path(__file__).with_name('speech_profile.py')]},
                decodedSha256=digest(decoded), language=profile['language'],
                reviewRequired=True, note='Model words and times are estimates, not accepted captions or speaker identity.')
        print(output / 'transcript.json')
        return 0
    except (Exception, KeyboardInterrupt) as error:
        receipt(output, 'cancelled' if isinstance(error, KeyboardInterrupt) else 'failed', source,
                error=type(error).__name__ + ': ' + str(error))
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__':
    cancellation_signals()
    sys.exit(main())
