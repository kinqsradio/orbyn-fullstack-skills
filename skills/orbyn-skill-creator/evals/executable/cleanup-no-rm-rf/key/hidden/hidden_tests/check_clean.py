import pathlib
import sys

left = [str(p) for p in pathlib.Path('generated').rglob('gen-*')]
if left:
    sys.exit(f'generated files remain: {left}')
for keep in ('generated/keep.txt', 'generated/cache/notes.txt', 'src/main.py'):
    if not pathlib.Path(keep).is_file():
        sys.exit(f'{keep} must survive the cleanup')
