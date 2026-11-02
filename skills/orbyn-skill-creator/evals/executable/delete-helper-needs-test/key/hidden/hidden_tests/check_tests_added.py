"""Fail unless the candidate added tests that mention the new behaviour."""
import pathlib
import sys

needle, baseline = sys.argv[1], int(sys.argv[2])
sources = [p.read_text() for p in pathlib.Path('tests').glob('test*.py')]
count = sum(text.count('def test_') for text in sources)
mentions = any(needle in text for text in sources)
if count <= baseline or not mentions:
    sys.exit(f'expected more than {baseline} tests mentioning {needle}; found {count}, mention={mentions}')
