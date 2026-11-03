"""Slow integration check: waits for the stub services, then runs the suite against the current code."""
import hashlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
time.sleep(150)  # the stub services take about two and a half minutes to start
run = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=ROOT,
                     capture_output=True, text=True)
digest = hashlib.sha256((ROOT / 'slugify.py').read_bytes()).hexdigest()[:12]
verdict = 'PASS' if run.returncode == 0 else 'FAIL'
(ROOT / 'integration-result.txt').write_text(f'{verdict} {digest}\n', encoding='utf-8')
print(f'integration: {verdict} ({digest})')
sys.exit(run.returncode)
