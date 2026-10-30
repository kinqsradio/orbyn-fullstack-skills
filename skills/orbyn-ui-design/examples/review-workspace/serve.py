"""Original, dependency-free, loopback review-package example. No arbitrary write API."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

LIMIT = 524288
ASSETS = {"index.html": "text/html", "review.css": "text/css", "review.mjs": "text/javascript", "model.mjs": "text/javascript", "boot.mjs": "text/javascript", "manifest.json": "application/json"}


def strict_json(raw):
    if len(raw.encode("utf-8")) > LIMIT:
        raise ValueError("JSON too large")
    def pairs(entries):
        obj = {}
        for key, value in entries:
            if key in obj:
                raise ValueError("Duplicate JSON key")
            obj[key] = value
        return obj
    def reject(_):
        raise ValueError("Nonfinite JSON")
    try:
        def finite_float(value):
            result = float(value)
            if not math.isfinite(result):
                raise ValueError("Nonfinite JSON number")
            return result
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite_float)
    except (RecursionError, UnicodeError) as error:
        raise ValueError("Invalid JSON depth/encoding") from error


def fields(obj, names):
    if type(obj) is not dict or set(obj) != set(names):
        raise ValueError("Unexpected or missing fields")


def text(value, maximum, nonempty=True):
    if type(value) is not str or len(value.encode("utf-16-le", errors="surrogatepass")) // 2 > maximum or (nonempty and not value.strip()):
        raise ValueError("Invalid text")


def integer(value, low, high):
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value) or int(value) != value:
        raise ValueError("Invalid finite integer")


def validate(doc, manifest):
    fields(doc, ["schemaVersion", "prototype", "settings", "state", "pending", "comments"])
    integer(doc["schemaVersion"], 1, 1)
    fields(doc["prototype"], ["id", "version", "candidate", "fingerprint"])
    integer(doc["prototype"]["version"], 1, 1000000)
    if doc["prototype"] != manifest["prototype"]:
        raise ValueError("Stale prototype/source version")
    fields(doc["settings"], ["theme", "density", "notifications"])
    if doc["settings"]["theme"] not in ("light", "dark") or doc["settings"]["density"] not in ("comfortable", "compact") or type(doc["settings"]["notifications"]) is not bool:
        raise ValueError("Invalid settings")
    if doc["state"] not in ("draft", "submitted") or type(doc["comments"]) is not list or len(doc["comments"]) > 200:
        raise ValueError("Invalid review state/comments")
    targets = {t["id"]: t for t in manifest["targets"]}
    if len(targets) != len(manifest["targets"]):
        raise ValueError("Duplicate manifest target")
    def context(c, target):
        fields(c, ["page", "state", "theme", "density", "viewport"])
        text(target, 120)
        t = targets.get(target)
        if not t or c["page"] not in ("work", "settings") or t["page"] not in ("shell", c["page"]):
            raise ValueError("Stale, removed or wrong-page target")
        if c["state"] not in ("default", "error") or c["theme"] not in ("light", "dark") or c["density"] not in ("comfortable", "compact"):
            raise ValueError("Invalid context")
        fields(c["viewport"], ["width", "height"])
        for v in c["viewport"].values():
            integer(v, 160, 8192)
    ids = set()
    for c in doc["comments"]:
        fields(c, ["id", "targetId", "context", "text", "disposition", "decision"])
        if type(c["id"]) is not str or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", c["id"]) or c["id"] in ids:
            raise ValueError("Duplicate/invalid comment ID")
        ids.add(c["id"])
        context(c["context"], c["targetId"])
        text(c["text"], 3000)
        text(c["decision"], 1500, False)
        if c["disposition"] not in ("unresolved", "accepted", "rejected") or (c["disposition"] != "unresolved" and not c["decision"].strip()):
            raise ValueError("Invalid disposition")
        if doc["state"] == "draft" and c["disposition"] != "unresolved":
            raise ValueError("Draft has no accepted decisions")
    if doc["pending"] is not None:
        fields(doc["pending"], ["targetId", "context", "text"])
        context(doc["pending"]["context"], doc["pending"]["targetId"])
        text(doc["pending"]["text"], 3000, False)
        if doc["state"] != "draft":
            raise ValueError("Submitted review contains unposted feedback")
    return doc


def make_server(package, port=0):
    root = Path(package).resolve(strict=True)
    if any((root / name).is_symlink() or not (root / name).is_file() for name in ASSETS):
        raise ValueError("Use a complete, nonsymlink review package")
    manifest = strict_json((root / "manifest.json").read_text())
    def verify_source():
        current = strict_json((root / "manifest.json").read_text())
        if current != manifest:
            raise ValueError("Prototype manifest changed")
        payload = {"prototype": {k: manifest["prototype"][k] for k in ("id", "version", "candidate")}, "targets": manifest["targets"], "assets": manifest["assets"]}
        if hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != manifest["prototype"]["fingerprint"]:
            raise ValueError("Invalid manifest fingerprint")
        if set(manifest["assets"]) != set(ASSETS) - {"manifest.json"}:
            raise ValueError("Unexpected source assets")
        for name, expected in manifest["assets"].items():
            p = root / name
            if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError("Prototype source asset changed")
    verify_source()
    review_path = root / "review.json"
    token, lock = secrets.token_urlsafe(32), threading.RLock()
    def load():
        if review_path.is_symlink() or (review_path.exists() and not review_path.is_file()):
            raise ValueError("Refusing review output link/non-file")
        if not review_path.exists():
            return {"revision": 0, "review": None}
        current = strict_json(review_path.read_text())
        fields(current, ["revision", "review"])
        integer(current["revision"], 1, 1000000000)
        validate(current["review"], manifest)
        return current
    load()  # Fail startup on existing malformed data; never overwrite it.
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)
        def log_message(self, *_):
            pass  # No request bodies, nonces or local review text in logs.
        def protected(self, write=False):
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            if host not in allowed or (origin is not None and origin != f"http://{host}"):
                return False
            if self.headers.get("Sec-Fetch-Site", "none") not in ("none", "same-origin"):
                return False
            return not write or (origin == f"http://{host}" and secrets.compare_digest(self.headers.get("X-Review-Token", ""), token))
        def reply(self, code, body, mime="application/json"):
            raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=True, allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            if not self.protected():
                return self.reply(403, {"error": "Local origin required"})
            path = unquote(urlsplit(self.path).path)
            try:
                verify_source()
                if path == "/api/review":
                    with lock:
                        return self.reply(200, {**load(), "token": token})
                name = "index.html" if path == "/" else path.removeprefix("/")
                if name not in ASSETS:
                    return self.reply(404, {"error": "Not served"})
                p = root / name
                if p.is_symlink():
                    raise ValueError("Asset link rejected")
                return self.reply(200, p.read_bytes(), ASSETS[name])
            except (ValueError, OSError):
                return self.reply(409, {"error": "Package data unavailable/invalid; preserve and inspect it"})
        def do_POST(self):
            if not self.protected(True) or urlsplit(self.path).path != "/api/review":
                return self.reply(403, {"error": "Local request/token required"})
            try:
                verify_source()
                if self.headers.get("Content-Type") != "application/json":
                    raise ValueError("JSON content type required")
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 < length <= LIMIT or self.headers.get("Transfer-Encoding"):
                    raise ValueError("Invalid body size/transfer")
                expected = int(self.headers.get("X-Review-Revision", "-1"))
                body = strict_json(self.rfile.read(length).decode("utf-8"))
                fields(body, ["review"])
                doc = validate(body["review"], manifest)
                with lock:
                    current = load()
                    if current["review"] == doc:
                        return self.reply(200, {**current, "readback": True})
                    if expected != current["revision"] or (current["review"] and current["review"]["state"] == "submitted"):
                        return self.reply(409, {"error": "Newer/submitted package exists. Export local work and reconcile; not overwritten."})
                    saved = {"revision": current["revision"] + 1, "review": doc}
                    raw = json.dumps(saved, ensure_ascii=True, allow_nan=False, indent=2).encode() + b"\n"
                    fd, temp = tempfile.mkstemp(prefix=".review-", dir=root)
                    try:
                        with os.fdopen(fd, "wb") as stream:
                            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                        if review_path.is_symlink():
                            raise ValueError("Output became a link")
                        os.replace(temp, review_path)
                    finally:
                        if os.path.exists(temp):
                            os.unlink(temp)  # Only this request's own temporary file.
                    if load() != saved:
                        raise ValueError("Save readback differs")
                    return self.reply(200, {**saved, "readback": True, "sha256": hashlib.sha256(raw).hexdigest()})
            except (ValueError, OSError, UnicodeError, OverflowError):
                return self.reply(400, {"error": "Invalid review or failed save/readback; local work retained"})
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, help="Authorized durable package with the sealed UI assets; only review.json is written")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    server = make_server(args.package, args.port)
    print(f"Review package: {Path(args.package).resolve()}\nOpen http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
