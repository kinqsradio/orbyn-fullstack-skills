#!/usr/bin/env python3
"""Contract for stack-diagram. The core needs no network and no browser."""
import base64
import contextlib
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import urllib.error
import urllib.request
import urllib.response
from email.message import Message

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT/'skills/stack-diagram'
RECORD = SKILL/'references/upstream/stack-diagram'
SCRIPTS = SKILL/'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(f'stack_diagram_{name}', SCRIPTS/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sanitise = load('sanitise_svg')
fetch = load('fetch_icons')
build = load('build')
render = load('render_png')
guard = load('repo_guard')


def chrome_ready():
    try:
        return bool(render.find_browser())
    except render.RenderError:
        return False


CHROME_READY = chrome_ready()

HOSTILE = b'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 10 10" onload="alert(1)" xml:base="https://evil.example/">
  <script>alert(2)</script>
  <defs><linearGradient id="g"><stop stop-color="#123456"/></linearGradient></defs>
  <foreignObject><body xmlns="http://www.w3.org/1999/xhtml"><img src="x" onerror="alert(3)"/></body></foreignObject>
  <html:script xmlns:html="http://www.w3.org/1999/xhtml">alert(4)</html:script>
  <set attributeName="href" to="javascript:alert(5)"/>
  <animate attributeName="onload" to="alert(6)"/>
  <a href="javascript:alert(7)"><text>x</text></a>
  <image href="https://evil.example/track.png" width="1" height="1"/>
  <image xlink:href="//evil.example/track.png" width="1" height="1"/>
  <use href="https://evil.example/sprite.svg#a"/>
  <use href="#keep"/>
  <path id="keep" d="M0 0h10" fill="url(#g)" onclick="alert(8)" ONMOUSEOVER="alert(9)"/>
  <rect width="1" height="1" fill="url(https://evil.example/a.svg#x)"/>
</svg>'''
HOSTILE_WORDS = (b'script', b'alert', b'foreignObject', b'evil.example', b'onload', b'onclick',
                 b'onmouseover', b'<a', b'<set', b'<animate', b'xml:base')


class Sanitiser(unittest.TestCase):
    def test_planted_hostile_svg_loses_every_active_or_external_part(self):
        clean, removed = sanitise.sanitise_svg(HOSTILE)
        lowered = clean.lower()
        for word in HOSTILE_WORDS:
            self.assertNotIn(word.lower(), lowered)
        self.assertIn('element:script', removed)
        self.assertIn('element:foreignObject', removed)
        self.assertIn('attribute:onload', removed)

    def test_drawing_and_local_references_survive(self):
        clean, _ = sanitise.sanitise_svg(HOSTILE)
        self.assertIn(b'url(#g)', clean)
        self.assertIn(b'href="#keep"', clean)
        self.assertIn(b'#123456', clean)

    def test_clean_output_is_stable(self):
        once, _ = sanitise.sanitise_svg(HOSTILE)
        twice, removed = sanitise.sanitise_svg(once)
        self.assertEqual(twice, once)
        self.assertEqual(removed, [])

    def test_entities_are_refused_in_any_encoding(self):
        bomb = ('<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;">]>'
                '<svg xmlns="http://www.w3.org/2000/svg"><text>&b;</text></svg>')
        external = ('<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
                    '<svg xmlns="http://www.w3.org/2000/svg"><text>&x;</text></svg>')
        for raw in (bomb.encode(), external.encode(), bomb.encode('utf-16')):
            with self.assertRaises(sanitise.UnsafeSvg):
                sanitise.sanitise_svg(raw)

    def test_a_plain_doctype_is_dropped_and_the_mark_kept(self):
        raw = (b'<?xml version="1.0"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
               b'"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>')
        clean, _ = sanitise.sanitise_svg(raw)
        self.assertNotIn(b'DOCTYPE', clean)
        self.assertIn(b'<path', clean)

    def test_non_svg_roots_and_broken_xml_are_rejected(self):
        for raw in (b'<html><script>alert(1)</script></html>', b'<svg', b'<svg><path></svg>',
                    b'<svg xmlns="http://www.w3.org/1999/xhtml"></svg>'):
            with self.assertRaises(sanitise.UnsafeSvg):
                sanitise.sanitise_svg(raw)

    def test_oversized_svg_is_rejected_before_parsing(self):
        with self.assertRaises(sanitise.UnsafeSvg):
            sanitise.sanitise_svg(b'<svg>' + b' ' * sanitise.MAX_SVG_BYTES + b'</svg>')

    def test_css_that_reaches_outside_is_removed_and_flagged(self):
        for css in ('@import url(https://evil.example/a.css);', '.a{fill:url(https://evil.example/x)}',
                    '.a{background:image-set("https://evil.example/x.png" 1x)}', '.a{fill:u\\72l(https://evil.example/x)}',
                    '@font-face{src:url(https://evil.example/f)}'):
            raw = f'<svg xmlns="http://www.w3.org/2000/svg"><style>{css}</style><path d="M0 0"/></svg>'.encode()
            clean, removed = sanitise.sanitise_svg(raw)
            self.assertNotIn(b'evil.example', clean, css)
            self.assertIn('style', removed)
        raw = b'<svg xmlns="http://www.w3.org/2000/svg"><path style="fill:url(https://evil.example/x)" d="M0 0"/></svg>'
        clean, removed = sanitise.sanitise_svg(raw)
        self.assertNotIn(b'evil.example', clean)
        self.assertIn('style', removed)

    def test_ordinary_logo_styling_is_kept(self):
        raw = (b'<svg xmlns="http://www.w3.org/2000/svg"><style>.cls-1{fill:#ff6600;}.b{fill:url(#g);opacity:.5}'
               b'</style><path class="cls-1" d="M0 0"/></svg>')
        clean, removed = sanitise.sanitise_svg(raw)
        self.assertIn(b'#ff6600', clean)
        self.assertEqual(removed, [])

    def test_embedded_raster_is_kept_but_embedded_svg_is_not(self):
        png = b'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,iVBORw0KGgo="/></svg>'
        nested = b'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/svg+xml;base64,PHN2Zz4="/></svg>'
        self.assertIn(b'data:image/png', sanitise.sanitise_svg(png)[0])
        self.assertNotIn(b'data:image/svg', sanitise.sanitise_svg(nested)[0])

    def test_every_bundled_pictogram_passes_unchanged_in_content(self):
        for path in (SKILL/'assets/generic').glob('*.svg'):
            _, removed = sanitise.sanitise_svg(path.read_bytes())
            self.assertEqual(removed, [], path.name)


class Endless(io.RawIOBase):
    """A body that never ends, counting what the client pulled."""

    def __init__(self):
        self.pulled = 0

    def readable(self):
        return True

    def read(self, size=-1):
        size = 64 * 1024 if size is None or size < 0 else size
        self.pulled += size
        return b'x' * size


class StubHttps(urllib.request.HTTPSHandler):
    """Answers https through urllib's real pipeline, so redirects run the real handler."""

    def __init__(self, routes):
        super().__init__()
        self.routes = routes
        self.requested = []
        self.timeouts = []

    def https_open(self, request):
        url = request.full_url
        self.requested.append(url)
        self.timeouts.append(request.timeout)
        route = self.routes.get(url)
        if route is None:
            raise urllib.error.URLError('no route')
        status, headers, body = route
        message = Message()
        for key, value in headers.items():
            message[key] = value
        stream = body if hasattr(body, 'read') else io.BytesIO(body)
        response = urllib.response.addinfourl(stream, message, url, status)
        response.msg = 'stub'
        return response


LOGO = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#123456" d="M0 0h24v24H0z"/></svg>'
LOGO_URL = 'https://logo.example/logo.svg'


@contextlib.contextmanager
def stub(routes):
    handler = StubHttps(routes)
    with mock.patch.object(fetch, 'OPENER', fetch.make_opener(handler)):
        yield handler


def quiet(function, *args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = function(*args)
    return result, output.getvalue()


class FetchLimits(unittest.TestCase):
    def test_get_returns_a_small_body_and_sets_a_timeout(self):
        with stub({LOGO_URL: (200, {}, LOGO)}) as handler:
            self.assertEqual(fetch.get(LOGO_URL), LOGO)
        self.assertEqual(handler.timeouts, [fetch.SOCKET_TIMEOUT])

    def test_only_https_is_requested(self):
        for url in ('http://logo.example/a.svg', 'file:///etc/passwd', 'ftp://logo.example/a.svg',
                    'data:image/svg+xml,<svg/>', 'https://user:secret@logo.example/a.svg'):
            with stub({}) as handler, self.assertRaises(fetch.FetchRefused):
                fetch.get(url)
            self.assertEqual(handler.requested, [])

    def test_a_drip_cannot_outlast_the_deadline(self):
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen()
        self.addCleanup(server.close)
        port = server.getsockname()[1]

        def drip(headers_only):
            connection, _ = server.accept()
            with connection:
                connection.recv(4096)
                try:
                    connection.sendall(b'HTTP/1.1 200 OK\r\n' if headers_only else b'HTTP/1.1 200 OK\r\nContent-Length: 100000\r\n\r\n')
                    for _ in range(100):
                        connection.sendall(b'x: y\r\n' if headers_only else b'x')
                        time.sleep(.1)
                except OSError:
                    pass

        class Plain(http.client.HTTPConnection):
            def connect(self):
                super().connect()
                fetch.FETCH_STATE.sockets.append(self.sock)

        class PlainHandler(urllib.request.HTTPHandler):
            def http_open(self, req):
                return self.do_open(Plain, req)

        for headers_only in (False, True):
            thread = threading.Thread(target=drip, args=(headers_only,), daemon=True)
            thread.start()
            url = f'http://127.0.0.1:{port}/a.svg'
            with mock.patch.object(fetch, 'OPENER', fetch.make_opener(PlainHandler)), mock.patch.object(fetch, 'require_https'):
                started = time.monotonic()
                with self.assertRaises(fetch.FetchRefused):
                    fetch.get(url, deadline=1)
                self.assertLess(time.monotonic() - started, 4)

    def test_forms_that_embed_a_private_address_are_refused(self):
        for host in ('10.0.0.1', '100.64.0.1', '198.18.0.1', '240.0.0.1', '2130706433', '0x7f.0.0.1', '0177.0.0.1',
                     '::ffff:127.0.0.1', '64:ff9b::7f00:1', '64:ff9b::a9fe:a9fe', '2002:7f00:1::', '2002:a00:1::'):
            with self.assertRaises(fetch.FetchRefused, msg=host):
                fetch.require_public_host(host)
        self.assertTrue(fetch.is_public('8.8.8.8'))
        self.assertTrue(fetch.is_public('64:ff9b::808:808'))

    def test_a_literal_is_judged_before_any_lookup(self):
        with mock.patch.object(fetch.socket, 'getaddrinfo', return_value=[(0, 0, 0, '', ('2405:6e00:64::a00:1', 443, 0, 0))]) as lookup:
            with self.assertRaises(fetch.FetchRefused):
                fetch.require_public_host('10.0.0.1')
        lookup.assert_not_called()

    def test_the_connected_address_is_checked_too(self):
        sock = mock.Mock()
        sock.getpeername.return_value = ('169.254.169.254', 443)
        with self.assertRaises(fetch.FetchRefused):
            fetch.require_public_peer(sock)
        sock.close.assert_called_once()
        sock.getpeername.return_value = ('8.8.8.8', 443)
        fetch.require_public_peer(sock)

    def test_private_and_local_addresses_are_refused(self):
        for url in ('https://127.0.0.1/a.svg', 'https://169.254.169.254/latest', 'https://10.0.0.8/a.svg',
                    'https://192.168.1.1/a.svg', 'https://[::1]/a.svg', 'https://localhost/a.svg'):
            with stub({}) as handler, self.assertRaises(fetch.FetchRefused):
                fetch.get(url)
            self.assertEqual(handler.requested, [])

    def test_a_redirect_to_a_private_address_is_refused(self):
        routes = {LOGO_URL: (302, {'Location': 'https://169.254.169.254/latest'}, b'')}
        with stub(routes) as handler:
            with self.assertRaises((fetch.FetchRefused, urllib.error.HTTPError)):
                fetch.get(LOGO_URL)
        self.assertEqual(handler.requested, [LOGO_URL])

    def test_icon_sources_are_pinned(self):
        for url in [u for _, u, _ in fetch.sources('lucide/clock')]:
            self.assertIn(f'lucide-static@{fetch.LUCIDE_VERSION}', url)
        with mock.patch.object(fetch, 'svgl_lookup', return_value=None):
            urls = [u for _, u, _ in fetch.sources('hono')]
        self.assertTrue(all('@' in u for u in urls), urls)

    def test_a_redirect_to_non_https_is_rejected(self):
        for target in ('http://logo.example/a.svg', 'file:///etc/passwd', 'ftp://logo.example/a.svg'):
            routes = {LOGO_URL: (302, {'Location': target}, b'')}
            with stub(routes) as handler:
                with self.assertRaises((fetch.FetchRefused, urllib.error.HTTPError)):
                    fetch.get(LOGO_URL)
            self.assertEqual(handler.requested, [LOGO_URL])

    def test_a_redirect_between_https_hosts_is_followed_and_bounded(self):
        final = 'https://cdn.example/logo.svg'
        with stub({LOGO_URL: (302, {'Location': final}, b''), final: (200, {}, LOGO)}):
            self.assertEqual(fetch.get(LOGO_URL), LOGO)
        loop = {f'https://a.example/{i}': (302, {'Location': f'https://a.example/{i + 1}'}, b'') for i in range(9)}
        with stub(loop), self.assertRaises(urllib.error.HTTPError):
            fetch.get('https://a.example/0')

    def test_an_oversized_body_stops_early_without_trusting_the_headers(self):
        body = Endless()
        with stub({LOGO_URL: (200, {}, body)}), self.assertRaises(fetch.FetchRefused):
            fetch.get(LOGO_URL)
        self.assertLessEqual(body.pulled, fetch.MAX_ICON_BYTES + 256 * 1024)

    def test_a_lying_short_length_header_does_not_help(self):
        body = Endless()
        with stub({LOGO_URL: (200, {'Content-Length': '10'}, body)}), self.assertRaises(fetch.FetchRefused):
            fetch.get(LOGO_URL)

    def test_a_declared_oversized_body_is_refused_before_reading(self):
        body = Endless()
        headers = {'Content-Length': str(fetch.MAX_ICON_BYTES + 1)}
        with stub({LOGO_URL: (200, headers, body)}), self.assertRaises(fetch.FetchRefused):
            fetch.get(LOGO_URL)
        self.assertEqual(body.pulled, 0)

    def test_a_trickling_body_hits_the_total_deadline(self):
        with stub({LOGO_URL: (200, {}, Endless())}), self.assertRaises(fetch.FetchRefused):
            fetch.get(LOGO_URL, limit=10**12, deadline=0)

    def test_type_comes_from_bytes_never_the_url(self):
        page = b'<!DOCTYPE html><html><script>alert(1)</script>' + b' ' * 60 + b'</html>'
        for url in ('https://logo.example/logo.png', 'https://logo.example/logo.svg'):
            with stub({url: (200, {}, page)}), self.assertRaises(fetch.FetchRefused):
                fetch.admit(fetch.get(url))

    def test_aws_member_size_is_checked_before_extraction(self):
        package = fetch.AwsPackage()
        package.archive = mock.Mock()
        package.archive.getinfo.return_value = mock.Mock(file_size=fetch.MAX_ICON_BYTES + 1)
        with self.assertRaises(fetch.FetchRefused):
            package.read('huge.svg')
        package.archive.read.assert_not_called()


class FetchRun(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)/'icons'

    def manifest(self):
        return json.loads((self.out/'manifest.json').read_text())

    def test_hostile_svg_is_stored_sanitised(self):
        # An external paint alone would be refused, because removing it recolours the mark.
        drawable = HOSTILE.replace(b'<rect width="1" height="1" fill="url(https://evil.example/a.svg#x)"/>', b'')
        with stub({LOGO_URL: (200, {}, drawable)}):
            code, output = quiet(fetch.main, [str(self.out), f'hono={LOGO_URL}', '--allow-network'])
        self.assertEqual(code, 0)
        stored = (self.out/'hono.svg').read_bytes().lower()
        for word in HOSTILE_WORDS:
            self.assertNotIn(word.lower(), stored)
        self.assertIn('element:script', self.manifest()['hono']['sanitised'])
        self.assertIn('sanitised', output)

    def test_oversized_body_falls_back_and_stores_nothing_from_it(self):
        with stub({LOGO_URL: (200, {}, Endless())}):
            code, output = quiet(fetch.main, [str(self.out), f'hono={LOGO_URL}~server', '--allow-network'])
        self.assertEqual(code, 0)
        self.assertIn('REFUSED hono', output)
        self.assertIn('FALLBACK hono', output)
        self.assertEqual((self.out/'hono.svg').read_bytes(), (SKILL/'assets/generic/server.svg').read_bytes())
        self.assertTrue(self.manifest()['hono']['fallback'])

    def test_svg_whose_styling_cannot_stay_is_skipped_so_the_mark_is_never_recoloured(self):
        restyled = b'<svg xmlns="http://www.w3.org/2000/svg"><style>@import url(https://evil.example/a.css);.a{fill:red}</style><path class="a" d="M0 0h24"/></svg>'
        with stub({LOGO_URL: (200, {}, restyled)}):
            _, output = quiet(fetch.main, [str(self.out), f'hono={LOGO_URL}', '--allow-network'])
        self.assertIn('FALLBACK hono', output)
        self.assertEqual(self.manifest()['hono']['source'], 'generic')

    def test_without_the_flag_nothing_touches_the_network(self):
        with stub({}) as handler:
            code, output = quiet(fetch.main, [str(self.out), 'hono~server', 'stripe:stripe', f'a={LOGO_URL}', 'b:aws/s3', 'c:lucide/clock'])
        self.assertEqual(code, 0)
        self.assertEqual(handler.requested, [])
        self.assertEqual(output.count('FALLBACK'), 5)
        self.assertIn('neutral pictograms, not logos', output)
        manifest = self.manifest()
        self.assertTrue(all(entry['fallback'] and entry['source'] == 'generic' for entry in manifest.values()))
        self.assertEqual(manifest['hono']['pictogram'], 'server')
        self.assertEqual(manifest['stripe']['pictogram'], 'box')

    def test_network_failure_falls_back_and_says_so(self):
        def unavailable(*_, **__):
            raise urllib.error.URLError('offline')
        with mock.patch.object(fetch.OPENER, 'open', unavailable):
            code, output = quiet(fetch.main, [str(self.out), 'hono~server', '--allow-network'])
        self.assertEqual(code, 0)
        self.assertIn('FALLBACK hono', output)
        self.assertIn('offline', self.manifest()['hono']['reason'])

    def test_a_name_matching_a_pictogram_picks_it_without_a_suffix(self):
        quiet(fetch.main, [str(self.out), 'browser'])
        self.assertEqual(self.manifest()['browser']['pictogram'], 'browser')

    def test_explicit_generic_spec_is_not_a_fallback(self):
        _, output = quiet(fetch.main, [str(self.out), 'client:generic/user'])
        self.assertNotIn('FALLBACK', output)
        self.assertNotIn('fallback', self.manifest()['client'])

    def test_a_refetch_replaces_an_older_suffix_and_leaves_other_files(self):
        self.out.mkdir()
        (self.out/'hono.png').write_bytes(b'old')
        (self.out/'hono.html').write_text('diagram draft')
        quiet(fetch.main, [str(self.out), 'hono'])
        self.assertFalse((self.out/'hono.png').exists())
        self.assertTrue((self.out/'hono.html').exists())

    def test_names_and_slugs_cannot_escape(self):
        for spec in ('../evil', 'a/b', 'name:../../evil', 'name:a/b/c', 'name:a b', 'name:generic/nope'):
            with self.subTest(spec), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as stop:
                    fetch.main([str(self.out), spec])
                self.assertEqual(stop.exception.code, 2)

    def test_a_corrupt_manifest_stops_the_run(self):
        self.out.mkdir()
        (self.out/'manifest.json').write_text('{broken')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stop:
            fetch.main([str(self.out), 'hono'])
        self.assertEqual(stop.exception.code, 2)

    @unittest.skipUnless(shutil.which('git'), 'git unavailable')
    def test_logos_refuse_a_folder_that_git_would_commit(self):
        repo = Path(self.directory.name)/'repo'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        (repo/'.gitignore').write_text('output/\n')
        with stub({LOGO_URL: (200, {}, LOGO)}):
            with self.assertRaises(SystemExit) as stop:
                quiet(fetch.main, [str(repo/'skills/logos'), f'hono={LOGO_URL}', '--allow-network'])
            self.assertIn('would be committed', str(stop.exception.code))
            self.assertFalse((repo/'skills/logos/hono.svg').exists())
            code, _ = quiet(fetch.main, [str(repo/'output/logos'), f'hono={LOGO_URL}', '--allow-network'])
        self.assertEqual(code, 0)
        self.assertTrue((repo/'output/logos/hono.svg').exists())


class Build(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.icons = self.root/'icons'
        self.icons.mkdir()
        self.out = self.root/'out.html'

    def draft(self, text):
        path = self.root/'draft.html'
        path.write_text(text)
        return path

    def run_build(self, draft):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            try:
                build.main([str(draft), str(self.icons), str(self.out)])
            except SystemExit as stop:
                return stop.code, stderr.getvalue()
        return 0, stderr.getvalue()

    def test_group_labels_get_their_dark_logo_automatically(self):
        draft = ('<div class="g-label"><img src="%%ICON_vercel%%" alt="">Vercel</div>'
                 '<div class="g-label"><img src="%%ICON_plain%%" alt="">Plain</div>'
                 '<div class="tile"><img src="%%ICON_vercel%%" alt=""></div>')
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        icons = Path(temp.name)
        for name in ('vercel', 'vercel_dark', 'plain'):
            (icons/f'{name}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>')
        paired = build.pair_group_labels(draft, icons)
        self.assertIn('class="dk" src="%%ICON_vercel_dark%%"', paired)
        self.assertIn('<div class="g-label"><img class="lt" src="%%ICON_vercel%%"', paired)
        self.assertIn('<div class="g-label"><img src="%%ICON_plain%%"', paired)
        self.assertIn('<div class="tile"><img src="%%ICON_vercel%%"', paired)

    def test_the_view_time_check_reads_markup_not_prose(self):
        for html in ('<img srcset="http://x/a.png 1x">', '<svg><image href="http://x/a.png"/></svg>', '<object data="http://x/a"></object>',
                     '<video poster="http://x/a.png"></video>', '<div style="background:image-set(\'x.png\' 1x)"></div>',
                     '<script>fetch("https://x")</script>', '<script src="local.js"></script>', '<link rel="stylesheet" href="a.css">',
                     '<style>@import "a.css";</style>', '<style>p{background:url(https://x/a.png)}</style>', '<img src="/local.png" onerror="x()">'):
            self.assertTrue(build.view_time_loads(html), html)
        for html in ('<p>Sass @import pipeline</p>', '<div data-src="//cdn/x"></div>', '<a href="https://example.com">site</a>',
                     '<img src="data:image/png;base64,AA" alt="">', '<path marker-end="url(#ar)"/>', '<style>p{fill:url(#a)}</style>'):
            self.assertEqual(build.view_time_loads(html), [], html)

    def test_fetched_logos_cannot_build_into_a_tracked_folder(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.icons/'vercel.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>')
        (self.icons/'manifest.json').write_text(json.dumps({'vercel': {'source': 'svgl', 'file': 'vercel.svg'}}))
        draft = self.draft('<html><head></head><img src="%%ICON_vercel%%" alt=""><i>%%CREDITS%%</i></html>')
        code, message = self.run_build(draft)
        self.assertEqual(code, 1)
        self.assertIn('would be committed', message)
        self.assertFalse(self.out.exists())
        (self.root/'.gitignore').write_text('*.html\n*.png\n*.svg\n*.webp\nmanifest.json\n')
        self.assertEqual(self.run_build(draft)[0], 0)
        self.assertIn('stack-diagram-logos', self.out.read_text())

    def test_unresolved_tokens_fail_and_write_nothing(self):
        for token in ('%%ICON_missing%%', '%%TITLE%%', '%%FONT_DISPLAY%%'):
            code, message = self.run_build(self.draft(f'<p>{token}</p><i>%%CREDITS%%</i>'))
            self.assertEqual(code, 1, token)
            self.assertIn(token, message)
            self.assertFalse(self.out.exists())

    def test_a_draft_without_a_credit_slot_fails(self):
        code, message = self.run_build(self.draft('<p>hello</p>'))
        self.assertEqual(code, 1)
        self.assertIn('%%CREDITS%%', message)

    def test_a_view_time_load_fails(self):
        for piece in ('<img src="https://cdn.example/a.png">', '<img src=//cdn.example/a.png>',
                      '<link rel="stylesheet" href="a.css">', '<style>@import "a.css";</style>',
                      '<style>a{background:url(https://cdn.example/a.png)}</style>'):
            code, message = self.run_build(self.draft(piece + '%%CREDITS%%'))
            self.assertEqual(code, 1, piece)
            self.assertIn('self-contained', message)

    def test_the_fonts_option_is_gone(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stop:
            build.main(['a', 'b', 'c', '--fonts', 'd'])
        self.assertEqual(stop.exception.code, 2)

    def test_template_builds_from_pictograms_with_system_fonts(self):
        template = (SKILL/'assets/template.html').read_text()
        self.assertNotRegex(template, r'%%FONT|@font-face|woff2|Geist|JetBrains')
        self.assertIn('system-ui', template)
        self.assertIn('ui-monospace', template)
        for name in ('vendor', 'tool1', 'tool2', 'client', 'app', 'api'):
            shutil.copy(SKILL/'assets/generic/box.svg', self.icons/f'{name}.svg')
        filled = template.replace('%%TITLE%%', 'T').replace('%%KICKER%%', 'K').replace('%%LEDE%%', 'L').replace('%%FOOT%%', 'F')
        code, message = self.run_build(self.draft(filled))
        self.assertEqual(code, 0, message)
        built = self.out.read_text()
        self.assertNotRegex(built, r'%%[A-Za-z0-9_-]+%%')
        self.assertIn('data:image/svg+xml;base64,', built)
        self.assertNotIn('made with', built)
        ordinary = self.root/'ordinary.txt'
        ordinary.write_text('')
        self.assertEqual(self.out.stat().st_mode, ordinary.stat().st_mode)  # A temp-file mode would hide it from others.

    def test_the_unfilled_template_fails(self):
        code, _ = self.run_build(SKILL/'assets/template.html')
        self.assertEqual(code, 1)

    def test_a_hand_placed_hostile_svg_is_sanitised_at_build(self):
        (self.icons/'x.svg').write_bytes(HOSTILE)
        code, _ = self.run_build(self.draft('<img src="%%ICON_x%%">%%CREDITS%%'))
        self.assertEqual(code, 0)
        uri = re.search(r'base64,([A-Za-z0-9+/=]+)', self.out.read_text()).group(1)
        embedded = base64.b64decode(uri).lower()
        for word in HOSTILE_WORDS:
            self.assertNotIn(word.lower(), embedded)

    def test_a_symlinked_icon_is_not_embedded(self):
        secret = self.root/'secret.png'
        secret.write_bytes(b'private')
        (self.icons/'x.png').symlink_to(secret)
        code, message = self.run_build(self.draft('<img src="%%ICON_x%%">%%CREDITS%%'))
        self.assertEqual(code, 1)
        self.assertIn('%%ICON_x%%', message)

    def test_credits_name_used_sources_and_the_trademark_notice(self):
        for name in ('a', 'b', 'c', 'd'):
            shutil.copy(SKILL/'assets/generic/box.svg', self.icons/f'{name}.svg')
        (self.icons/'manifest.json').write_text(json.dumps({
            'a': {'source': 'svgl'}, 'b': {'source': 'generic', 'fallback': True},
            'c': {'source': 'explicit', 'url': 'https://brand.example/logo.svg'}, 'd': {'source': 'devicon'}}))
        code, _ = self.run_build(self.draft('%%ICON_a%% %%ICON_b%% %%ICON_c%% <footer>%%CREDITS%%</footer>'))
        self.assertEqual(code, 0)
        footer = re.search(r'<footer>(.*)</footer>', self.out.read_text()).group(1)
        self.assertIn('svgl', footer)
        self.assertIn('brand.example', footer)
        self.assertIn('neutral pictograms', footer)
        self.assertIn('1 logo unavailable', footer)
        self.assertIn('logos remain the trademarks of their owners', footer)
        self.assertNotIn('devicon', footer)

    def test_a_pictogram_only_diagram_makes_no_trademark_claim(self):
        shutil.copy(SKILL/'assets/generic/box.svg', self.icons/'a.svg')
        (self.icons/'manifest.json').write_text(json.dumps({'a': {'source': 'generic'}}))
        self.run_build(self.draft('%%ICON_a%%<i>%%CREDITS%%</i>'))
        self.assertIn('<i>icons: neutral pictograms</i>', self.out.read_text())

    def test_credit_text_from_a_manifest_is_escaped(self):
        shutil.copy(SKILL/'assets/generic/box.svg', self.icons/'a.svg')
        (self.icons/'manifest.json').write_text(json.dumps({'a': {'source': '<script>alert(1)</script>'}}))
        self.run_build(self.draft('%%ICON_a%%%%CREDITS%%'))
        self.assertNotIn('<script>', self.out.read_text())


class Library(unittest.TestCase):
    def skill_text(self):
        return (SKILL/'SKILL.md').read_text()

    def test_entrypoint_meets_the_authoring_standard(self):
        text = self.skill_text()
        front, body = re.fullmatch(r'---\n(.*?\n)---\n(.*)', text, re.S).groups()
        description = re.search(r'^description: "(.*)"$', front, re.M).group(1)
        self.assertLessEqual(len(description), 300)
        for neighbour in ('architect', 'technical-illustration', 'product-illustration'):
            self.assertIn(neighbour, description)
        self.assertLessEqual(len(body.split()), 1200)
        self.assertIn('## Method', body)
        self.assertIn('## Read when needed', body)

    def test_no_font_binary_or_branded_file_ships(self):
        files = [path for path in SKILL.rglob('*') if path.is_file() and '__pycache__' not in path.parts]
        self.assertFalse([path for path in files if path.suffix in {'.woff', '.woff2', '.ttf', '.otf', '.png', '.jpg', '.webp'}])
        self.assertFalse([path for path in files if path.name.startswith('OFL')])
        self.assertEqual({path.parent for path in files if path.suffix == '.svg'}, {SKILL/'assets/generic'})
        for path in (SKILL/'assets/generic').glob('*.svg'):
            self.assertIn('stroke="#3d4660"', path.read_text(), path.name)

    def test_no_install_or_host_advice_ships(self):
        banned = re.compile(r'npx skills|pip install|playwright install|apt-get|npm install|--global|\bartifact\b|claude\.ai', re.I)
        for path in SKILL.rglob('*'):
            if path.is_file() and path.parent != RECORD and '__pycache__' not in path.parts:
                self.assertIsNone(banned.search(path.read_text()), path)

    def test_the_renderer_keeps_the_sandbox_and_installs_nothing(self):
        source = (SCRIPTS/'render_png.py').read_text()
        self.assertNotIn('--no-sandbox', source)
        self.assertNotIn('.install', source)

    def test_license_is_upstream_mit(self):
        text = (SKILL/'LICENSE').read_text()
        self.assertIn('Copyright (c) 2026 caru-ini', text)
        self.assertEqual((SKILL/'LICENSE').read_bytes(), (RECORD/'LICENSE').read_bytes())
        self.assertNotIn('assets/fonts', text)

    def test_snapshot_pins_the_record_bytes(self):
        snapshot = json.loads((RECORD/'snapshot.json').read_text())
        self.assertEqual(snapshot['revision'], '75dbd3e3c6fe28844322e6064d3a947b870a6c61')
        self.assertEqual(set(snapshot['files']), {path.name for path in RECORD.iterdir()} - {'snapshot.json'})
        for name, entry in snapshot['files'].items():
            self.assertEqual(hashlib.sha256((RECORD/name).read_bytes()).hexdigest(), entry['sha256'], name)

    def test_source_manifest_lists_every_file_with_true_hashes(self):
        manifest = json.loads((RECORD/'source-manifest.json').read_text())
        for name, entry in manifest['files'].items():
            digest = hashlib.sha256((SKILL/name).read_bytes()).hexdigest()
            self.assertEqual(digest, entry['sha256'], f'{name}: refresh source-manifest.json and snapshot.json')
        record = 'references/upstream/stack-diagram/'
        shipped = {path.relative_to(SKILL).as_posix() for path in SKILL.rglob('*')
                   if path.is_file() and '__pycache__' not in path.parts}
        self.assertEqual(set(manifest['files']), {name for name in shipped
                                                  if name not in {record+'snapshot.json', record+'source-manifest.json'}})


def existing_chrome():
    try:
        return render.find_browser()
    except render.RenderError:
        return None


def png_size(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', f'{path} is not a PNG'
    return struct.unpack('>II', raw[16:24])


class BrowserLookup(unittest.TestCase):
    def test_a_bad_chrome_path_fails_instead_of_picking_another_browser(self):
        with mock.patch.dict(os.environ, {'CHROME_PATH': '/nonexistent/chrome'}):
            with self.assertRaisesRegex(render.RenderError, 'CHROME_PATH'):
                render.find_browser()

    def test_no_browser_is_a_named_failure(self):
        with mock.patch.dict(os.environ, {'CHROME_PATH': ''}), mock.patch.object(render, 'playwright_browser', lambda: None), \
                mock.patch.object(render, 'BINARIES', ()), mock.patch.object(render, 'INSTALLED', ()), \
                mock.patch.object(render, 'PLAYWRIGHT_CACHES', ()):
            with self.assertRaisesRegex(render.RenderError, 'Set CHROME_PATH'):
                render.find_browser()


@unittest.skipUnless(existing_chrome(), 'Existing Chrome unavailable; set CHROME_PATH to run the render test')
class BrowserRender(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def page(self, extra=''):
        path = self.root/'page.html'
        path.write_text('<!doctype html><html><head><style>html{background:#fff}[data-theme=dark]{background:#000}'
                        '.canvas{width:300px;height:120px;background:#eee}[data-theme=dark] .canvas{background:#111}'
                        f'</style></head><body><div class="page"><div class="canvas">{extra}</div>'
                        '<div class="legend">legend</div></div></body></html>')
        return path

    def test_both_themes_render_at_the_requested_scale(self):
        out = self.root/'nested/out.png'
        self.assertEqual(quiet(render.main, [str(self.page()), str(out), '--selector', '.canvas', '--scale', '2'])[0], 0)
        dark = out.with_name('out-dark.png')
        self.assertEqual(png_size(out), (600, 240))
        self.assertEqual(png_size(dark), (600, 240))
        self.assertNotEqual(out.read_bytes(), dark.read_bytes())
        self.assertEqual([path.name for path in out.parent.iterdir() if path.suffix != '.png'], [])

    def test_the_default_capture_keeps_the_legend_with_the_drawing(self):
        out = self.root/'page.png'
        quiet(render.main, [str(self.page()), str(out), '--single', '--scale', '1'])
        self.assertGreater(png_size(out)[1], 120)

    def test_a_missing_selector_fails(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit) as stop:
            render.main([str(self.page()), str(self.root/'o.png'), '--selector', '.nope'])
        self.assertEqual(stop.exception.code, 1)
        self.assertIn('.nope', stderr.getvalue())

    def test_a_page_that_reaches_the_network_fails(self):
        extra = '<img src="https://cdn.example/a.png">'
        with contextlib.redirect_stderr(io.StringIO()) as stderr, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as stop:
                render.main([str(self.page(extra)), str(self.root/'o.png')])
        self.assertEqual(stop.exception.code, 1)
        self.assertIn('not self-contained', stderr.getvalue())

    def test_an_svg_script_inside_an_image_never_runs(self):
        uri = base64.b64encode(sanitise.sanitise_svg(HOSTILE)[0]).decode()
        page = self.page(f'<img src="data:image/svg+xml;base64,{uri}">')
        self.assertEqual(quiet(render.main, [str(page), str(self.root/'o.png'), '--single'])[0], 0)


class GuardFailsClosed(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def test_a_pattern_that_spares_real_names_is_refused(self):
        for rules in ('.*\n!.gitignore\n', 'out/**\n!out/**/\n!*.png\n'):
            (self.root/'.gitignore').write_text(rules)
            with self.assertRaises(guard.NotIgnored, msg=rules):
                guard.require_ignored(self.root/'out')

    def test_missing_git_inside_a_repository_is_refused(self):
        (self.root/'.gitignore').write_text('out/\n')
        with mock.patch.dict(os.environ, {'PATH': str(self.root/'nowhere')}), self.assertRaises(guard.NotIgnored):
            guard.require_ignored(self.root/'out')
        guard.require_ignored(self.root/'out')

    def test_a_stray_git_dir_changes_nothing(self):
        with mock.patch.dict(os.environ, {'GIT_DIR': '/nonexistent'}), self.assertRaises(guard.NotIgnored):
            guard.require_ignored(self.root/'out')

    def test_outside_any_repository_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            guard.require_ignored(Path(folder)/'out')


class InlineSafety(unittest.TestCase):
    PREFIX = '<svg xmlns="http://www.w3.org/2000/svg">'

    def clean(self, inner):
        return sanitise.sanitise_svg((self.PREFIX+inner+'</svg>').encode())

    def test_text_after_a_child_of_style_cannot_carry_a_rule(self):
        data, removed = self.clean('<style><desc/>rect{fill:url(http://x/p.svg)}</style><rect/>')
        self.assertNotIn(b'http://x', data)
        self.assertIn('style', removed)

    def test_a_sheet_cannot_reach_the_page(self):
        for rule in ('body{display:none}', 'html,rect{fill:red}', '*{display:none}', 'div{color:red}'):
            self.assertIn('style', self.clean(f'<style>{rule}</style><rect/>')[1], rule)
        for rule in ('rect{fill:red}', '.a,.b{fill:#000}', 'path.a{fill:url(#g)}', '@media (prefers-color-scheme: dark){.a{fill:#fff}}'):
            self.assertNotIn('style', self.clean(f'<style>{rule}</style><rect/>')[1], rule)

    def test_title_and_desc_keep_text_only(self):
        data, _ = self.clean('<title>Logo<image srcset="http://x/a.png"/></title><desc><image href="#a" srcset="http://x/b"/></desc>')
        self.assertNotIn(b'image', data)
        self.assertIn(b'Logo', data)

    def test_attributes_are_allowlisted(self):
        data, removed = self.clean('<image href="#a" srcset="http://x/a.png" ping="http://x"/><rect data-x="1" fill="red"/>')
        for text in (b'srcset', b'ping', b'data-x'):
            self.assertNotIn(text, data)
        self.assertIn(b'fill="red"', data)
        self.assertIn('attribute:srcset', removed)

    def test_deep_nesting_is_a_refusal_not_a_crash(self):
        for depth in (100, 5000):
            with self.assertRaises(sanitise.UnsafeSvg):
                self.clean('<g>'*depth+'</g>'*depth)
        self.clean('<g>'*40+'</g>'*40)

    def test_quoted_local_paints_survive(self):
        for paint in ('url(#a)', "url('#a')", 'url("#a")'.replace('"', '&quot;')):
            data, removed = self.clean(f'<path fill="{paint}"/>')
            self.assertEqual(removed, [], paint)
            self.assertIn(b'fill=', data)

    def test_an_icon_that_loses_a_paint_is_refused(self):
        raw = (self.PREFIX+'<path fill="url(http://x/p.svg)" d="M0 0L1 1"/><rect width="1" height="1"/></svg>').encode()
        with self.assertRaises(fetch.UnsafeSvg):
            fetch.admit(raw)

    def test_deep_json_does_not_stop_the_run(self):
        self.assertIn(RecursionError, fetch.FETCH_ERRORS)


class SvgPolicy(unittest.TestCase):
    def test_only_the_neutral_pictogram_folder_may_ship_svg(self):
        spec = importlib.util.spec_from_file_location('manifest_policy', ROOT/'scripts/library_manifest.py')
        manifest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manifest)
        names = manifest.inventory(ROOT)
        self.assertIn('skills/stack-diagram/assets/generic/box.svg', names)
        stray = SKILL/'references/stray.svg'
        stray.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.addCleanup(stray.unlink)
        with self.assertRaisesRegex(ValueError, 'Unexpected skill asset type'):
            manifest.inventory(ROOT)


class ManifestShape(unittest.TestCase):
    def test_a_manifest_that_is_not_an_object_is_exit_2(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'manifest.json').write_text('[]')
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                fetch.main([folder, 'x:lucide/clock'])
            self.assertEqual(caught.exception.code, 2)


class RenderWritesLast(unittest.TestCase):
    @unittest.skipUnless(CHROME_READY, 'Existing Chrome unavailable')
    def test_a_page_with_a_remote_request_leaves_no_image(self):
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder)/'p.html'
            page.write_text('<div class="page">diagram<img src="http://127.0.0.1:9/a.png" alt=""></div>')
            out = Path(folder)/'p.png'
            result = subprocess.run([sys.executable, str(SCRIPTS/'render_png.py'), str(page), str(out), '--single'],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn('not self-contained', result.stderr)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
