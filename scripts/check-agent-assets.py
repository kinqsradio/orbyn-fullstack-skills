#!/usr/bin/env python3
"""Compatibility entrypoint for the shared skill-maintenance instructions."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('check-library.py')), run_name='__main__')
