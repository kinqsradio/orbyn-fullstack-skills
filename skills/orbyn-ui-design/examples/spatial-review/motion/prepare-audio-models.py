#!/usr/bin/env python3
"""Explicit optional English ASR/alignment profile acquisition, separate from runtime.

Downloads only pinned public weights/data; never installs a provider, token or app.
No downloaded Python source is executed. Keep output in task-owned ignored storage.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import urllib.request
import zipfile
from audio_tools import digest, new_output, write_json

MODELS = {
    'asr': ('Systran/faster-whisper-tiny.en', '0d3d19a32d3338f10357c0889762bd8d64bbdeba', 'mit',
            ['README.md', 'config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt']),
    'alignment': ('facebook/wav2vec2-base-960h', '22aad52d435eb6dbaf354bdad9b0da84ce7d6156', 'apache-2.0',
                  ['README.md', 'config.json', 'model.safetensors', 'preprocessor_config.json',
                   'special_tokens_map.json', 'tokenizer_config.json', 'vocab.json']),
}
NLTK_REVISION = '550b6625bcef1f2abff2ff770a5a0d272c9c6b2a'


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Orbyn-local-model-preparation'}), timeout=120)


def fetch(url, destination, expected_size, expected_hash=None, blob=None):
    if not 0 < expected_size <= 512 * 1024 * 1024:
        raise ValueError('Model file budget')
    sha = hashlib.sha256()
    git = hashlib.sha1(f'blob {expected_size}\0'.encode())
    size = 0
    with request(url) as source, destination.open('xb') as target:
        while chunk := source.read(1024 * 1024):
            size += len(chunk)
            if size > expected_size:
                raise ValueError('Model size exceeded metadata')
            target.write(chunk); sha.update(chunk); git.update(chunk)
    if size != expected_size or (expected_hash and sha.hexdigest() != expected_hash) or (blob and git.hexdigest() != blob):
        raise ValueError('Model byte identity differs from pinned metadata')
    return sha.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--download', action='store_true', help='Explicitly acquire the listed pinned local profile')
    args = parser.parse_args()
    if not args.download:
        raise ValueError('This separate preparation command requires explicit --download; runtime never downloads')
    if shutil.disk_usage(args.out.parent).free < 1024 * 1024 * 1024:
        raise ValueError('At least 1 GiB free is required for this optional profile')
    output = new_output(args.out)
    profile = {'version': 1, 'language': 'en', 'models': {}, 'nltk': {},
               'limits': ['English pilot profile only; other languages need their own explicit prepared profile.',
                          'Model estimates require correction; no diarization/singing/lip-sync guarantee.']}
    try:
        for role, (repo, revision, license_, files) in MODELS.items():
            with request(f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true') as source:
                metadata = json.load(source)
            if metadata['sha'] != revision or metadata.get('cardData', {}).get('license') != license_:
                raise ValueError('Model revision/license differs from reviewed profile')
            write_json(output / (role + '-source.json'), metadata)
            folder = output / role; folder.mkdir()
            entries = {entry['rfilename']: entry for entry in metadata['siblings']}
            hashes = {}
            for name in files:
                entry = entries[name]; lfs = entry.get('lfs') or {}
                hashes[name] = fetch(f'https://huggingface.co/{repo}/resolve/{revision}/{name}', folder / name,
                                     entry['size'], lfs.get('sha256') or lfs.get('oid'), None if lfs else entry.get('blobId'))
                print(role + '/' + name, flush=True)
            profile['models'][role] = {'path': role, 'repository': repo, 'revision': revision,
                                      'license': license_, 'files': hashes}
        url = f'https://raw.githubusercontent.com/nltk/nltk_data/{NLTK_REVISION}/packages/tokenizers/punkt_tab.zip'
        with request(url) as source:
            archive = source.read(20 * 1024 * 1024 + 1)
        if len(archive) > 20 * 1024 * 1024:
            raise ValueError('Tokenizer archive budget')
        files = {}
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            for info in zipped.infolist():
                path = PurePosixPath(info.filename)
                if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError('Unsafe tokenizer archive entry')
                if not info.is_dir() and (info.filename.startswith('punkt_tab/english/') or info.filename == 'punkt_tab/README'):
                    if info.file_size > 2 * 1024 * 1024:
                        raise ValueError('Tokenizer member budget')
                    name = 'tokenizers/' + info.filename
                    target = output / 'nltk' / name; target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zipped.read(info)); files[name] = digest(target)
        if len(files) < 4:
            raise ValueError('Incomplete English tokenizer')
        profile['nltk'] = {'path': 'nltk', 'repository': 'nltk/nltk_data', 'revision': NLTK_REVISION,
                           'archiveSha256': hashlib.sha256(archive).hexdigest(), 'files': files,
                           'notice': 'Tokenizer README retained; this local dependency data is not shipped in the skill library.'}
        write_json(output / 'models.json', profile)
        write_json(output / 'receipt.json', {'status': 'completed', 'toolSha256': digest(__file__),
                                            'profileSha256': digest(output / 'models.json')})
        print(output / 'models.json')
        return 0
    except (Exception, KeyboardInterrupt) as error:
        write_json(output / 'receipt.json', {'status': 'cancelled' if isinstance(error, KeyboardInterrupt) else 'failed', 'error': str(error)})
        print(str(error), file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
