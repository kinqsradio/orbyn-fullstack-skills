"""Explicit authoring step: refresh source hashes for a deliberate prototype revision.

Never run to make stale comments pass. Preserve old review.json and start/reconcile
an explicit review round before resealing changed prototype source.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def seal(root):
    root = Path(root).resolve(strict=True)
    path = root / "manifest.json"
    if path.is_symlink() or (root / "review.json").exists() or (root / "review.json").is_symlink():
        raise ValueError("Preserve/reconcile the existing review in its old package; seal a new source round")
    manifest = json.loads(path.read_text())
    prototype = {k: manifest["prototype"][k] for k in ("id", "version", "candidate")}
    assets = {}
    for name in ("index.html", "review.css", "review.mjs", "model.mjs", "boot.mjs"):
        p = root / name
        if p.is_symlink():
            raise ValueError("Source link rejected")
        assets[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    payload = {"prototype": prototype, "targets": manifest["targets"], "assets": assets}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # Authored targets live only here: a failed write must leave the old manifest intact.
    mode = path.stat().st_mode & 0o777
    fd, temp = tempfile.mkstemp(prefix=".manifest-", dir=root)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(json.dumps({**payload, "prototype": {**prototype, "fingerprint": fingerprint}}, indent=2) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)  # Only this run's own temporary file.
    return fingerprint


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    print(seal(parser.parse_args().package))
