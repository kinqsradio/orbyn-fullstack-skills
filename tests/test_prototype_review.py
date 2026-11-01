"""Real loopback/temporary-package checks, not consumer or live-model qualification."""
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "skills/orbyn-ui-design/examples/review-workspace"
spec = importlib.util.spec_from_file_location("review_package_server", EXAMPLE / "serve.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)


class PrototypeReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="review-package-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "package"
        shutil.copytree(EXAMPLE, self.root, ignore=shutil.ignore_patterns("__pycache__"))
        self.server = server_module.make_server(self.root)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        def stop():
            self.server.shutdown()
            self.server.server_close()
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
        self.addCleanup(stop)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        _, body, _ = self.request("GET", "/api/review")
        self.token = json.loads(body)["token"]
        self.doc = {"schemaVersion": 1, "prototype": json.loads((self.root / "manifest.json").read_text())["prototype"], "settings": {"theme": "light", "density": "comfortable", "notifications": True}, "state": "draft", "pending": None, "comments": [{"id": "one", "targetId": "work/alpha/open", "context": {"page": "work", "state": "default", "theme": "light", "density": "comfortable", "viewport": {"width": 1280, "height": 800}}, "text": "<img src=x onerror=alert(1)> original words", "disposition": "unresolved", "decision": ""}]}

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def save(self, doc, revision=0, headers=None):
        actual = {"Content-Type": "application/json", "Origin": self.origin, "X-Review-Token": self.token, "X-Review-Revision": str(revision)}
        actual.update(headers or {})
        return self.request("POST", "/api/review", json.dumps({"review": doc}), actual)

    def test_manifest_http_is_raw_json_and_assets_do_not_serialize_bytes(self):
        status, body, headers = self.request("GET", "/manifest.json")
        self.assertEqual(status, 200)
        self.assertEqual(body, (self.root / "manifest.json").read_bytes())
        self.assertIn("fingerprint", json.loads(body)["prototype"])
        self.assertIn("application/json", headers["Content-Type"])
        status, body, _ = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b'boot.mjs', body)
        self.assertEqual(self.request("GET", "/review.json")[0], 404)
        self.assertEqual(self.request("GET", "/../serve.py")[0], 404)

    def test_real_draft_save_readback_submit_and_immutable_submission(self):
        self.doc["settings"]["theme"] = "dark"
        status, body, _ = self.save(self.doc)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["readback"])
        saved = json.loads((self.root / "review.json").read_text())
        self.assertEqual(saved, {"revision": 1, "review": self.doc})
        self.doc["state"] = "submitted"
        self.assertEqual(self.save(self.doc, 1)[0], 200)
        altered = copy.deepcopy(self.doc)
        altered["comments"][0]["text"] = "replace"
        self.assertEqual(self.save(altered, 2)[0], 409)
        self.assertEqual(json.loads((self.root / "review.json").read_text())["review"], self.doc)

    def test_stale_writes_fail_but_identical_retry_is_idempotent(self):
        self.assertEqual(self.save(self.doc)[0], 200)
        next_doc = copy.deepcopy(self.doc)
        next_doc["settings"]["density"] = "compact"
        self.assertEqual(self.save(next_doc, 0)[0], 409)
        status, body, _ = self.save(self.doc, 0)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["revision"], 1)
        self.assertEqual(self.save(next_doc, 1)[0], 200)

    def test_non_ascii_token_is_refused_not_dropped(self):
        status, _, _ = self.save(self.doc, headers={"X-Review-Token": "café"})
        self.assertEqual(status, 403)
        self.assertFalse((self.root / "review.json").exists())

    def test_seal_is_stable_and_write_failure_keeps_the_manifest(self):
        path = self.root / "manifest.json"
        path.chmod(0o644)
        before = path.read_bytes()
        seal = EXAMPLE / "seal.py"
        program = ("import resource, signal, sys, importlib.util\n"
                   "spec = importlib.util.spec_from_file_location('seal', sys.argv[1])\n"
                   "module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n"
                   "signal.signal(signal.SIGXFSZ, signal.SIG_IGN)\n"
                   "resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))\n"
                   "module.seal(sys.argv[2])\n")
        result = subprocess.run([sys.executable, "-B", "-c", program, str(seal), str(self.root)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.root.glob(".manifest-*")), [])
        done = subprocess.run([sys.executable, "-B", str(seal), "--package", str(self.root)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), json.loads(path.read_text())["prototype"]["fingerprint"])
        self.assertEqual(path.stat().st_mode & 0o777, 0o644)

    def test_origin_host_and_request_token_required(self):
        self.assertEqual(self.save(self.doc, headers={"Origin": "https://elsewhere.example"})[0], 403)
        self.assertEqual(self.save(self.doc, headers={"X-Review-Token": "wrong"})[0], 403)
        self.assertEqual(self.request("GET", "/api/review", headers={"Host": "other.example"})[0], 403)
        self.assertEqual(self.save(self.doc, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertFalse((self.root / "review.json").exists())

    def test_unknown_fields_versions_targets_duplicates_and_nonfinite_reject(self):
        mutations = [lambda d: d.update(extra=True), lambda d: d["prototype"].update(version=2), lambda d: d["prototype"].update(fingerprint="0"*64), lambda d: d["comments"][0].update(targetId="removed"), lambda d: d["comments"].append(d["comments"][0]), lambda d: d["comments"][0]["context"]["viewport"].update(width=float("inf")), lambda d: d["settings"].update(notifications="yes"), lambda d: d["comments"][0]["context"]["viewport"].update(height=True)]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                doc = copy.deepcopy(self.doc)
                mutate(doc)
                self.assertEqual(self.save(doc)[0], 400)
        self.assertFalse((self.root / "review.json").exists())
        with self.assertRaises(ValueError):
            server_module.strict_json('{"x":1,"\\u0078":2}')
        with self.assertRaises(ValueError):
            server_module.strict_json('1e400')

    def test_source_mutation_blocks_live_save_get_and_restart(self):
        (self.root / "review.css").write_text("changed")
        self.assertEqual(self.save(self.doc)[0], 400)
        self.assertEqual(self.request("GET", "/api/review")[0], 409)
        with self.assertRaisesRegex(ValueError, "source asset changed"):
            server_module.make_server(self.root)
        self.assertFalse((self.root / "review.json").exists())

    def test_atomic_failure_never_reports_save_or_overwrites_existing(self):
        self.assertEqual(self.save(self.doc)[0], 200)
        before = (self.root / "review.json").read_bytes()
        doc = copy.deepcopy(self.doc)
        doc["settings"]["theme"] = "dark"
        with patch.object(server_module.os, "replace", side_effect=OSError("owned fixture failure")):
            self.assertEqual(self.save(doc, 1)[0], 400)
        self.assertEqual((self.root / "review.json").read_bytes(), before)
        self.assertEqual(list(self.root.glob('.review-*')), [])

    def test_output_symlink_is_not_followed(self):
        outside = self.root.parent / "outside.json"
        outside.write_text("retain this")
        try:
            (self.root / "review.json").symlink_to(outside)
        except OSError:
            self.skipTest("symlink privilege unavailable")
        self.assertEqual(self.save(self.doc)[0], 400)
        self.assertEqual(outside.read_text(), "retain this")

    @unittest.skipUnless(shutil.which("node"), "Node unavailable: JS model/handoff tests unrun")
    def test_javascript_model_and_agent_handoff(self):
        result = subprocess.run([shutil.which("node"), "--test", str(ROOT / "tests/prototype-review.test.mjs")], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
