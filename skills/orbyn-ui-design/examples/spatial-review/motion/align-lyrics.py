#!/usr/bin/env python3
"""Time explicitly supplied lyrics from a local model or a heard-word list; displays only supplied text."""
import argparse
import importlib.metadata
from pathlib import Path
import re
import sys
from audio_tools import cancellation_signals, decode_audio, digest, new_output, read_json, receipt, regular_file, run, write_json
from known_lyrics import REPEAT_THRESHOLD, align_supplied, lyric_prompt, mark_collapsed, parse_lyrics, repair_repeats, validate_heard
from lyrics_worker import read_samples


def heard_words(args, lines, output, decoded):
    """Return heard words and the runtime record that says where they came from."""
    if args.asr_words:
        path = regular_file(args.asr_words, 8 * 1024 * 1024)
        data = read_json(path)
        if not isinstance(data, dict) or set(data) != {'producedBy', 'words'} or not isinstance(data['producedBy'], str) or not data['producedBy'].strip():
            raise ValueError('Word list needs producedBy and words')
        return data['words'], {'kind': 'supplied-asr-words', 'modelRun': False, 'producedBy': data['producedBy'], 'sha256': digest(path)}
    prompt = output / 'prompt.txt'
    prompt.write_text(lyric_prompt(lines))
    run([sys.executable, str(Path(__file__).with_name('lyrics_worker.py')), '--audio', str(decoded), '--prompt', str(prompt),
         '--model-dir', str(args.model_dir.resolve()), '--out', str(output), '--language', args.language,
         '--device', args.device, '--threads', str(args.threads)], output, 'lyrics-worker', timeout=args.timeout)
    return read_json(output / 'raw-asr.json')['words'], read_json(output / 'asr-runtime.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['input', 'lyrics', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    source_of_times = parser.add_mutually_exclusive_group(required=True)
    source_of_times.add_argument('--model-dir', type=Path, help='Local converted faster-whisper model, such as small.en')
    source_of_times.add_argument('--asr-words', type=Path, help='JSON {producedBy, words} from another runtime or a manual pass')
    parser.add_argument('--repeat-threshold', type=float, default=REPEAT_THRESHOLD)
    parser.add_argument('--language', default='en')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--timeout', type=int, default=1200)
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    source = regular_file(args.input)
    args.lyrics = regular_file(args.lyrics, 1024 * 1024)
    if not 1 <= args.threads <= 8 or not 10 <= args.timeout <= 3600 or not 1 <= args.max_seconds <= 3600 or not 0 < args.repeat_threshold <= 1 or not re.fullmatch('[a-z]{2,3}', args.language):
        raise ValueError('Invalid lyric timing budget')
    output = new_output(args.out)
    original = digest(source)
    receipt(output, 'preparing', source)
    try:
        lines = parse_lyrics(args.lyrics.read_text())
        decoded, _audio = decode_audio(source, output, args.ffmpeg, args.ffprobe, 16000, args.max_seconds)
        samples = read_samples(decoded)
        duration = len(samples) / 16000
        heard, asr_runtime = heard_words(args, lines, output, decoded)
        words, rejected = align_supplied(lines, validate_heard(heard, duration))
        collapsed = mark_collapsed(words)
        repeats = repair_repeats(samples, 16000, words, lines, args.repeat_threshold)
        runtimes = {'asr': asr_runtime,
                    'repeats': {'kind': 'numpy-waveform-correlation', 'numpy': importlib.metadata.version('numpy'), 'threshold': args.repeat_threshold}}
        fields = ['id', 'text', 'start', 'end', 'status', 'score']
        write_json(output / 'transcript.json', {
            'version': 1, 'audioSha256': original, 'duration': duration, 'language': args.language, 'revision': 1,
            'words': [{k: w[k] for k in fields} for w in words], 'history': [],
            'model': {'origin': 'Supplied lyric text; timing from ' + asr_runtime['kind'],
                      'timingMeaning': 'Estimates until corrected. Text is supplied, so a timed word does not prove it was sung.',
                      'lyricsSha256': digest(args.lyrics), 'runtimes': runtimes}})
        write_json(output / 'lyric-timing.json', {
            'version': 1, 'audioSha256': original, 'lines': [{'id': l['id'], 'text': l['text']} for l in lines],
            'words': [{**w, 'timingRuntime': 'repeats' if w['id'] in repeats['provenance'] else 'asr' if w['start'] is not None else None,
                       **repeats['provenance'].get(w['id'], {})} for w in words],
            'asrRejected': rejected, 'collapsed': collapsed, 'repeats': {k: repeats[k] for k in ['repaired', 'unresolved']}, 'runtimes': runtimes})
        if digest(source) != original:
            raise ValueError('Audio changed during lyric timing')
        receipt(output, 'completed', source, lyricsSha256=digest(args.lyrics), decodedSha256=digest(decoded),
                modelRun=asr_runtime['modelRun'], reviewRequired=True,
                toolSources={p.name: digest(p) for p in [Path(__file__), *(Path(__file__).with_name(n) for n in ['audio_tools.py', 'known_lyrics.py', 'lyrics_worker.py'])]},
                note='Timing is an estimate. Heard words outside the supplied lyrics are retained for review and never displayed.')
        print(output / 'transcript.json')
        return 0
    except (Exception, KeyboardInterrupt) as error:
        receipt(output, 'cancelled' if isinstance(error, KeyboardInterrupt) else 'failed', source,
                error=type(error).__name__ + ': ' + str(error))
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    cancellation_signals()
    sys.exit(main())
