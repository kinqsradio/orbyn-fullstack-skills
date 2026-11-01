"""check-code-only.py on synthetic film folders.

Covered: media, fonts, models, archives and manifests by name; magic bytes, NUL bytes
and invalid UTF-8 anywhere in any file; data: URIs and long base64 runs; Lottie, glTF
and Spine JSON; vendored libraries by folder, filename and licence notice; static and
dynamic imports in scripts, inline <script>, Python and importlib; URLs in code, markup,
CSS, JSON, Python and plain text; paths that leave the folder; links.

Not covered, and listed in the report's `limits`: names and URLs built at run time,
aliases such as `const load = require`, bytes written as number arrays, renamed
libraries with their notices removed, the same data as a JavaScript object, and where
drawn shapes came from.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT/'skills/technical-illustration'
SCRIPT = SKILL/'scripts/check-code-only.py'


class CheckCodeOnlyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'film'
        self.root.mkdir()
        (self.root/'scene.mjs').write_text("import {walk} from './rig.mjs';\nimport fs from 'node:fs';\n")

    def run_check(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root), *args],
                                capture_output=True, text=True, timeout=30)
        return result.returncode, json.loads(result.stdout) if result.stdout else {}

    def problems(self):
        return ' | '.join(f"{f['file']}: {f['problem']}" for f in self.run_check()[1]['findings'])

    def write(self, name, text):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text) if isinstance(text, str) else path.write_bytes(text)
        return path

    def assert_fails(self, name, text, fragment):
        path = self.write(name, text)
        self.assertIn(fragment, self.problems(), name)
        path.unlink()

    def assert_clean(self, name, text):
        path = self.write(name, text)
        code, report = self.run_check()
        self.assertEqual((code, report['findings']), (0, []), name)
        path.unlink()

    def test_our_own_code_passes(self):
        (self.root/'index.html').write_text('<canvas></canvas><script type="module" src="./scene.mjs"></script>')
        (self.root/'drawn.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>')
        (self.root/'note.py').write_text('import json, math\n')
        self.assertEqual(self.run_check()[0], 0)

    def test_the_worked_examples_pass(self):
        for folder in ('code-only-film', 'image-puppet'):
            result = subprocess.run([sys.executable, str(SCRIPT), str(SKILL/'examples'/folder)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_media_fonts_and_models_fail(self):
        for name in ('cover.PNG', 'a.ttf', 'hero.glb', 'beat.wav', 'clip.mp4', 'walk.bvh', 'scan.ply', 'part.stl', 'still.ppm'):
            (self.root/name).write_bytes(b'x')
        code, report = self.run_check()
        self.assertEqual((code, len(report['findings'])), (1, 9))

    def test_real_media_bytes_fail_under_any_name(self):
        png = b'\x89PNG\r\n\x1a\n' + b'x' * 32
        self.assert_fails('sky.txt', png, 'PNG')
        self.assert_fails('sky.mjs', b'// a header\n' + png, 'PNG')
        self.assert_fails('sky.json', b'GIF89a' + b'x' * 32, 'GIF')
        self.assert_fails('clip.css', b'\0\0\0\x18ftypisom', 'MP4')
        self.assert_fails('song', b'RIFF\x24\0\0\0WAVEfmt ', 'WAVE')
        self.assert_fails('font.dat', b'wOF2' + b'y' * 32, 'WOFF2')

    def test_a_comment_naming_a_format_is_not_media(self):
        self.assert_clean('notes.mjs', '// The exporter writes GIF89a and PNG files.\nexport const a = 1;\n')

    def test_nul_and_invalid_text_are_found_past_the_first_kilobytes(self):
        self.assert_fails('late.mjs', b'a' * 5000 + b'\0' + b'b', 'binary file')
        self.assert_fails('late.txt', b'a' * 5000 + b'\xff', 'binary file')

    def test_data_payloads_fail_in_every_text_file(self):
        for name, text in (('a.mjs', "import x from 'data:text/javascript,export default 1';\n"),
                           ('b.css', 'body{background:url(data:image/png;base64,AAAA)}'),
                           ('c.html', '<img src="data:image/png;base64,AAAA">'),
                           ('d.txt', 'data:font/woff2;base64,AAAA'),
                           ('e.mjs', "// data:image/png;base64,AAAA\n"),
                           ('f.json', '{"a": "data:audio/wav;base64,AAAA"}')):
            self.assert_fails(name, text, 'data: payload')
        self.assert_fails('g.mjs', 'export const blob = "' + 'QUJD' * 300 + '";\n', 'base64')

    def test_data_as_a_property_name_is_code(self):
        self.assert_clean('a.mjs', 'export const box = {data: width / height, metadata: 1};\nconst metadata = {data:[1, 2]};\n')

    def test_lottie_gltf_and_spine_json_fail(self):
        self.assert_fails('walk.json', json.dumps({'v': '5.7', 'fr': 30, 'ip': 0, 'op': 60, 'layers': []}), 'Lottie')
        self.assert_fails('nested.json', json.dumps({'film': {'v': '5', 'fr': 30, 'ip': 0, 'op': 9, 'layers': []}}), 'Lottie')
        self.assert_fails('hero.json', json.dumps({'asset': {'version': '2.0'}, 'scenes': []}), 'glTF')
        self.assert_fails('hero.txt', json.dumps({'asset': {'version': '2.0'}, 'meshes': []}), 'glTF')
        self.assert_fails('rig.json', json.dumps({'skeleton': {}, 'bones': []}), 'Spine')
        self.assert_fails('broken.json', '{"v": ', 'does not parse')
        self.assert_clean('film.json', json.dumps({'version': 1, 'fps': 30, 'shots': [{'id': 'a'}]}))

    def test_vendored_libraries_fail_by_name_and_notice(self):
        for name in ('three.module.js', 'three.min.js', 'gsap.js', 'lottie.min.mjs', 'd3.v7.js', 'three-0.160.0.js', 'app.min.js', 'app.js.map'):
            self.assert_fails(name, 'export const a = 1;\n', 'vendored library')
        self.assert_fails('maths.mjs', '/**\n * @license\n * Copyright 2010-2024 Three.js Authors\n */\nexport const a = 1;\n', 'licence')
        self.assert_fails('b.mjs', '// SPDX-License-Identifier: MIT\n', 'licence')
        self.assert_fails('c.mjs', '/*! tween v1.2.3 */\nexport const a = 1;\n', 'licence')
        self.assert_fails('LICENSE', 'Permission is hereby granted, free of charge\n', 'licence')
        self.assert_fails('d.py', '# Licensed under the Apache License\nimport math\n', 'licence')

    def test_our_own_names_are_not_libraries(self):
        self.assert_clean('three-body.mjs', 'export const a = 1;\n')
        self.assert_clean('spine.mjs', 'export const a = 1;\n')
        self.assert_clean('credits.json', json.dumps({'line': 'Copyright 2026 the band'}))

    def test_vendored_folders_and_pycache_fail(self):
        self.assert_fails('node_modules/three/index.js', 'x', 'vendored package')
        self.assert_fails('bower_components/a/index.js', 'x', 'vendored package')
        self.assert_fails('lib/site-packages/a/b.py', 'x', 'vendored package')
        self.assert_fails('__pycache__/a.cpython-311.pyc', b'\xa7\r\r\n\0\0', 'binary file')
        self.assert_fails('__pycache__/a.mjs', "import 'three';\n", 'three')

    def test_only_the_root_git_folder_is_skipped(self):
        self.write('.git/objects/a', b'\0\0')
        self.assertEqual(self.run_check()[0], 0)
        self.assert_fails('nested/.git/objects/a', b'\0\0', 'binary file')

    def test_packages_fail_however_they_are_loaded(self):
        (self.root/'a.mjs').write_text("import * as T from 'three';\n")
        (self.root/'b.js').write_text("const g = require('gsap/all');\n")
        (self.root/'c.mjs').write_text("const m = await import('lottie-web');\n")
        for fragment in ('three', 'gsap/all', 'lottie-web'):
            self.assertIn(fragment, self.problems())

    def test_import_forms_and_message_text(self):
        (self.root/'a.mjs').write_text("import {\n  x,\n} from 'gsap';\nexport {y} from 'lodash';\nimport 'side-effect';\n")
        problems = self.problems()
        for fragment in ('gsap', 'lodash', 'side-effect'):
            self.assertIn(fragment, problems)
        (self.root/'a.mjs').write_text("throw Error('Expected a name from ' + list);\nconst s = 'pick from \"a\"';\n")
        self.assertEqual(self.run_check()[0], 0)

    def test_every_written_form_of_an_import(self):
        for label, text in (('backtick', 'await import(`three`);\n'), ('spaces', "await import ( 'three' );\n"),
                            ('require spaces', "require ( 'three' );\n"), ('require backtick', 'require(`three`);\n'),
                            ('multi-line', "import\n  a,\n  { b }\n  from\n  'three';\n"),
                            ('after semicolon', "const a = 1; import 'three';\n"), ('after comment', "/* hi */ import x from 'three';\n"),
                            ('escaped', "await import('\\x74hree');\n"), ('export star', "export * as t from 'three';\n"),
                            ('inside template', 'const a = `${await import("three")}`;\n'), ('scoped', "import x from '@pixi/core';\n")):
            with self.subTest(label):
                self.assert_fails('a.mjs', text, 'package import')

    def test_computed_module_names_fail(self):
        for text in ('await import(n);\n', "await import('thr' + 'ee');\n", 'await import(`./${n}.mjs`);\n', 'require(name);\n', 'importScripts(name);\n'):
            self.assert_fails('a.mjs', text, 'computed name')
        self.assert_fails('a.mjs', "eval('1');\n", 'eval')
        self.assert_fails('a.mjs', "new Function('return 1');\n", 'new Function')

    def test_code_that_looks_like_an_import_is_clean(self):
        self.assert_clean('a.mjs', "const a = import.meta.url;\nloader.import(n);\nconst s = \"import x from 'three'\";\nconst r = /import 'x'/;\n"
                                   "// import x from 'three'\n/* require('three') */\nexport {a};\nexport const from = 2;\n")

    def test_inline_module_scripts_are_read(self):
        self.assert_fails('a.html', "<script type=module>\nimport * as T from 'three';\n</script>", 'three')
        self.assert_fails('a.htm', "<script>import('gsap')</script>", 'gsap')
        self.assert_fails('a.vue', "<script setup>\nimport x from 'vue-thing';\n</script>", 'vue-thing')
        self.assert_clean('a.html', "<!-- <script src='https://cdn.example.com/x.js'></script> --><p>hi</p>")

    def test_remote_content_fails(self):
        (self.root/'index.html').write_text('<script src="https://cdn.example.com/x.js"></script>')
        (self.root/'a.css').write_text('body{background:url(//images.example.com/sky.jpg)}')
        (self.root/'b.mjs').write_text("fetch('https://api.example.com/generate');\n")
        for fragment in ('cdn.example.com', 'images.example.com', 'api.example.com'):
            self.assertIn(fragment, self.problems())

    def test_the_comment_skip_cannot_hide_code(self):
        self.assert_fails('a.css', '* { background: url(https://images.example.com/a.png) }\n', 'images.example.com')
        self.assert_fails('b.css', '#hero { background: url(https://images.example.com/b.png) }\n', 'images.example.com')
        self.assert_fails('c.css', '/* a */ body { background: url(https://images.example.com/c.png) }\n', 'images.example.com')
        self.assert_fails('d.mjs', "/* a */ fetch('https://api.example.com/d');\n", 'api.example.com')
        self.assert_fails('e.scss', '.a { b: url(https://images.example.com/e.png); } // note\n', 'images.example.com')

    def test_comments_may_cite_a_reference(self):
        self.assert_clean('a.mjs', '// See https://example.com/paper for the method.\n/* https://example.com/b */\n')
        self.assert_clean('a.py', '"""See https://example.com/paper."""\n# https://example.com/b\n')
        self.assert_clean('a.css', '/* https://example.com/c */\nbody { color: red }\n')

    def test_exempt_hosts_are_exact(self):
        self.assert_clean('a.mjs', "const n = 'http://www.w3.org/2000/svg', m = 'http://localhost:9000/a', o = 'http://127.0.0.1/b';\n")
        for url in ('https://evil.example/www.w3.org/', 'https://www.w3.org.evil.example/', 'https://localhost.evil.example/',
                    'https://evil.example/?a=localhost', 'https://notlocalhost/a'):
            self.assert_fails('a.mjs', f"fetch('{url}');\n", 'remote URL')

    def test_ip_and_userinfo_urls_fail(self):
        for url in ('http://203.0.113.9/a.png', 'http://[2001:db8::1]/a.png', 'http://2130706433/a', 'https://user:pw@example.com/a',
                    'http://localhost@evil.example/a', 'http://www.w3.org@evil.example/a', 'http://user@localhost/a', 'ftp://example.com/a', 'file:///etc/passwd'):
            self.assert_fails('a.mjs', f"fetch('{url}');\n", 'remote URL')

    def test_commented_out_code_is_not_a_url(self):
        self.assert_clean('a.mjs', 'const gl = 1;\n//gl.enable(gl.BLEND);\n')
        self.assert_clean('a.glsl', '#version 300 es\n//gl.position = a.b;\nfloat a = 1.;\n')
        self.assert_clean('a.txt', 'Notes\n//gl.enable(gl.BLEND);\n')

    def test_python_urls_and_dynamic_imports_fail(self):
        self.assert_fails('a.py', "url = 'https://api.example.com/x'\n", 'api.example.com')
        self.assert_fails('b.py', "import importlib\nimportlib.import_module('numpy')\n", 'numpy')
        self.assert_fails('c.py', "from importlib import import_module\nimport_module('torch.nn')\n", 'torch')
        self.assert_fails('d.py', "__import__('cv2')\n", 'cv2')
        self.assert_fails('e.py', 'import importlib\nname = "x"\nimportlib.import_module(name)\n', 'computed name')

    def test_sibling_python_modules_are_ours(self):
        self.write('helpers.py', 'A = 1\n')
        self.write('pack/__init__.py', 'B = 1\n')
        self.write('deep/run.py', 'import local\nimport helpers\nimport pack\n')
        self.write('deep/local.py', 'C = 1\n')
        self.assertEqual(self.run_check()[1]['findings'], [])
        self.assert_fails('e.py', 'import not_here\n', 'not_here')

    def test_paths_may_not_leave_the_folder(self):
        for name, text in (('a.mjs', "import x from '../other/x.mjs';\n"), ('b.mjs', "import('../other/x.mjs');\n"),
                           ('c.mjs', "import x from './sub/../../other.mjs';\n"), ('d.html', '<img src="../sky.jpeg">'),
                           ('e.html', '<a href="../../x">x</a>'), ('f.css', 'a{background:url(../sky.png)}'),
                           ('g.css', "@import '../theme.css';\n"), ('h.css', '@import url("../theme.css");\n'),
                           ('i.scss', "@use '../theme';\n"), ('j.mjs', "fetch('../art.bin');\n"), ('k.mjs', "import x from '/Users/me/x.mjs';\n")):
            with self.subTest(name):
                self.assert_fails(name, text, 'leaves the folder')

    def test_paths_inside_the_folder_are_fine(self):
        self.write('shared.mjs', 'export const a = 1;\n')
        self.write('sub/deep.css', 'a{background:url(../x.png)}\n@import "../y.css";\n')
        self.write('sub/deep.mjs', "import {a} from '../shared.mjs';\n")
        self.write('page.html', '<a href="#top">x</a><a href="./shared.mjs">y</a><script src="/shared.mjs"></script>')
        self.assertEqual(self.run_check()[1]['findings'], [])

    def test_extensions_ignore_case(self):
        self.assert_fails('A.MJS', "import 'three';\n", 'three')
        self.assert_fails('B.Py', 'import numpy\n', 'numpy')
        self.assert_fails('C.HTML', "<script src='https://cdn.example.com/a.js'></script>", 'cdn.example.com')
        self.assert_fails('D.Glb', b'x', 'media')

    def test_every_text_file_is_read(self):
        for name in ('a.txt', 'extensionless', 'a.htm', 'a.mts', 'a.vue', 'a.scss', 'a.md', 'a.yaml', 'a.sh', 'a.toml', 'a.wgsl'):
            with self.subTest(name):
                self.assert_fails(name, 'see url("https://cdn.example.com/x.js")\n', 'cdn.example.com')
        self.assert_fails('tool', "#!/usr/bin/env node\nimport(name);\n", 'computed name')
        self.assert_fails('tool', '#!/usr/bin/env python3\nimport numpy\n', 'numpy')
        self.assert_fails('script.txt', "import x from 'three';\n", 'three')
        self.assert_clean('prose.txt', 'A walk does not require (see above) any import of ideas.\n')

    def test_escaped_json_urls_fail(self):
        self.assert_fails('a.json', '{"src": "https:\\/\\/cdn.example.com\\/x.js"}', 'cdn.example.com')

    def test_manifests_vendored_code_and_links_fail(self):
        (self.root/'package.json').write_text('{}')
        (self.root/'node_modules/three').mkdir(parents=True)
        (self.root/'node_modules/three/index.js').write_text('x')
        (self.root/'link.mjs').symlink_to(self.root/'scene.mjs')
        problems = self.problems()
        for fragment in ('package manifest', 'vendored package', 'symbolic link'):
            self.assertIn(fragment, problems)

    def test_more_manifests_fail(self):
        for name in ('deno.json', 'Pipfile', 'Cargo.toml', 'poetry.lock', 'environment.yml', 'requirements-dev.txt', 'PACKAGE.JSON'):
            self.assert_fails(name, '{}', 'package manifest')

    def test_a_linked_folder_fails(self):
        outside = Path(self.temp.name)/'outside'
        outside.mkdir()
        (outside/'x.mjs').write_text('export const a = 1;\n')
        (self.root/'linked').symlink_to(outside, target_is_directory=True)
        self.assertIn('linked: symbolic link', self.problems())

    def test_a_link_to_an_allowed_file_still_fails(self):
        (self.root/'track.wav').write_bytes(b'x')
        (self.root/'alias.wav').symlink_to(self.root/'track.wav')
        code, report = self.run_check('--allow', 'track.wav')
        self.assertEqual((code, [f['file'] for f in report['findings']]), (1, ['alias.wav']))
        code, report = self.run_check('--allow', 'alias.wav', '--allow', 'track.wav')
        self.assertEqual((code, report['findings'][0]['problem']), (1, 'symbolic link'))

    def test_third_party_python_and_unknown_binaries_fail(self):
        (self.root/'a.py').write_text('import numpy as np\nfrom PIL import Image\n')
        (self.root/'blob.dat').write_bytes(b'\0\1\2')
        problems = self.problems()
        for fragment in ('numpy', 'PIL', 'binary file'):
            self.assertIn(fragment, problems)

    def test_allowances_are_exact_and_reported(self):
        (self.root/'track.wav').write_bytes(b'x')
        (self.root/'other.wav').write_bytes(b'x')
        (self.root/'a.py').write_text('import numpy\n')
        code, report = self.run_check('--allow', 'track.wav', '--allow-module', 'numpy')
        self.assertEqual(code, 1)
        self.assertEqual([f['file'] for f in report['findings']], ['other.wav'])
        self.assertEqual(report['allowed_paths'], ['track.wav'])
        self.assertEqual(report['allowed_modules'], ['numpy'])

    def test_bad_input_cannot_pass(self):
        self.assertEqual(self.run_check('--allow', 'missing.wav')[0], 2)
        self.assertEqual(self.run_check('--allow', '../scene.mjs')[0], 2)
        (self.root/'sub').mkdir()
        self.assertEqual(self.run_check('--allow', 'sub')[0], 2)
        self.root = self.root/'missing'
        self.assertEqual(self.run_check()[0], 2)

    def test_an_empty_folder_cannot_pass(self):
        (self.root/'scene.mjs').unlink()
        self.assertEqual(self.run_check()[0], 2)
        (self.root/'cover.png').write_bytes(b'x')
        self.assertEqual(self.run_check('--allow', 'cover.png')[0], 2)

    def test_the_report_lists_what_it_cannot_see(self):
        limits = ' '.join(self.run_check()[1]['limits'])
        for word in ('run time', 'alias', 'number arrays', 'renamed', 'JavaScript object', 'drawn'):
            self.assertIn(word, limits)


if __name__ == '__main__':
    unittest.main()
