#!/usr/bin/env python3
"""Generate host pointer files that defer to AGENTS.md; default is a read-only check."""
import argparse
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
tools = runpy.run_path(str(ROOT / 'scripts/host_instructions.py'))
parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--write', action='store_true', help='write the pointer files')
mode.add_argument('--check', action='store_true', help='report drift without writing (default)')
args = parser.parse_args()
if args.write:
    tools['write'](ROOT)
    print(f"Updated {len(tools['FILES'])} host instruction files.")
errors = tools['problems'](ROOT)
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
if not args.write:
    print(f"OK: {len(tools['FILES'])} host instruction files match the generated text.")
