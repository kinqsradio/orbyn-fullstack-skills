"""The interface check flags objective defects and stays quiet on legitimate code."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/orbyn-ui-design/scripts/ui_check.py'


class UiCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_check(self, **files):
        for name, text in files.items():
            (self.root/name.replace('__', '.')).write_text(text)
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], capture_output=True, text=True, timeout=30)
        return result.returncode, json.loads(result.stdout) if result.stdout else {}

    def rules(self, **files):
        return self.run_check(**files)[1]['rules']

    def test_removed_focus_ring_without_a_replacement_fails(self):
        code, report = self.run_check(a__css='button:focus { outline: none; }')
        self.assertEqual((code, report['rules']), (0, {'focus-ring-removed': 1}))

    def test_focus_ring_with_a_replacement_passes(self):
        self.assertEqual(self.rules(a__css='button:focus { outline: none; box-shadow: 0 0 0 2px blue; }'), {})
        self.assertEqual(self.rules(b__css='.x:focus { outline: 0 } .x:focus-visible { outline: 2px solid; }'), {})
        self.assertEqual(self.rules(c__css='.panel { outline: none; }'), {})

    def test_script_focus_targets_are_left_alone(self):
        self.assertEqual(self.rules(a__css='h1:focus { outline: none; } main:focus { outline: 0; }'), {})
        self.assertEqual(self.rules(a__css='[tabindex="-1"]:focus { outline: none; }'), {})

    def test_a_class_selector_only_warns(self):
        code, report = self.run_check(a__css='.main:focus { outline: none; }')
        self.assertEqual((code, report['rules']), (0, {'focus-ring-removed': 1}))
        self.assertEqual(report['errors'], 0)

    def test_tailwind_focus_ring(self):
        self.assertIn('focus-ring-removed', self.rules(a__tsx='<a className="outline-none p-2" href="/x">Go</a>'))
        self.assertNotIn('focus-ring-removed',
                         self.rules(a__tsx='<a className="outline-none focus-visible:ring-2" href="/x">Go</a>'))

    def test_icon_only_button_needs_a_name(self):
        code, report = self.run_check(a__tsx='<button onClick={() => go()}><svg viewBox="0 0 1 1"><path/></svg></button>')
        self.assertEqual((code, report['rules']), (0, {'control-without-name': 1}))
        self.assertEqual(self.rules(a__tsx='<button aria-label="Close"><CloseIcon /></button>'), {})
        for child in ('<X size={16}/>', '<IconX/>', '<i class="fa fa-x"></i>', '<span></span>', '<img src="/x.png" alt="">', '&nbsp;'):
            self.assertEqual(self.rules(a__tsx=f'<button>{child}</button>'), {'control-without-name': 1}, child)

    def test_text_expressions_and_spreads_are_not_accused(self):
        self.assertEqual(self.rules(a__tsx='<button>Save</button>'), {})
        self.assertEqual(self.rules(a__tsx='<button onClick={() => a > b}>{label}</button>'), {})
        self.assertEqual(self.rules(a__tsx='<button {...props}><Icon /></button>'), {})

    def test_images_need_alt_and_empty_alt_is_legitimate(self):
        self.assertEqual(self.rules(a__tsx='<img src="/a.png" />'), {'image-without-alt': 1})
        self.assertEqual(self.rules(a__tsx='<img src="/a.png" alt="" />'), {})

    def test_zoom_lock_fails(self):
        html = '<meta name="viewport" content="width=device-width, user-scalable=no">'
        self.assertEqual(self.rules(a__html=html), {'zoom-disabled': 1})
        self.assertEqual(self.rules(a__html='<meta name="viewport" content="width=device-width">'), {})

    def test_warnings_do_not_fail_the_run(self):
        code, report = self.run_check(a__tsx='<div onClick={go}>x</div>', b__css='.a { transition: all .2s; }')
        self.assertEqual(code, 0)
        self.assertEqual(report['rules'], {'clickable-div': 1, 'transition-all': 1})

    def test_clickable_div_with_a_role_passes(self):
        self.assertEqual(self.rules(a__tsx='<div role="button" tabIndex={0} onClick={go}>x</div>'), {})

    def test_positive_tabindex(self):
        self.assertEqual(self.rules(a__tsx='<input tabIndex={3} aria-label="x" />'), {'positive-tabindex': 1})
        self.assertEqual(self.rules(a__tsx='<input tabIndex={0} aria-label="x" />'), {})

    def test_reduced_motion_is_a_project_level_warning(self):
        keyframes = '@keyframes spin { to { rotate: 1turn; } }'
        self.assertEqual(self.rules(a__css=keyframes), {'reduced-motion-missing': 1})
        self.assertEqual(self.rules(b__css='@media (prefers-reduced-motion: reduce) { * { animation: none; } }'), {})

    def test_taste_is_never_judged(self):
        tasteful = ('<h1 className="font-black bg-gradient-to-r from-purple-500">Welcome back, Alex!</h1>'
                    '<p>🚀 Ship Faster</p><span>{name.toLowerCase()}</span>')
        self.assertEqual(self.rules(a__tsx=tasteful), {})

    def test_comments_tests_and_vendored_code_are_ignored(self):
        self.assertEqual(self.rules(a__css='/* button:focus { outline: none; } */'), {})
        self.assertEqual(self.rules(a__test__tsx='<img src="/a.png" />'), {})
        (self.root/'node_modules').mkdir()
        (self.root/'node_modules/x.tsx').write_text('<img src="/a.png" />')
        self.assertEqual(self.rules(b__tsx='<p>hi</p>'), {})

    def test_inventory_counts_shared_and_raw_controls(self):
        report = self.run_check(a__tsx='<Button>a</Button><button>b</button><button>c</button>')[1]
        self.assertEqual((report['inventory']['raw button'], report['inventory']['shared Button']), (2, 1))

    def test_only_two_rules_can_fail_a_run(self):
        code, report = self.run_check(a__tsx='<button><Icon/></button><div onClick={go}/>', b__css='a:focus{outline:none} .x{transition:all 1s}')
        self.assertEqual((code, report['errors']), (0, 0))
        self.assertEqual(self.run_check(c__tsx='<img src="/a.png" />')[0], 1)

    def test_comments_and_markup_in_strings_are_not_findings(self):
        for source in ('{/* <img src="/a.png" /> */}', '// <img src="/a.png" />', '<!-- <img src="/a.png"> -->',
                       'const html = `<img src="/a.png">`;', 'const html = "<img src=x>";', '/* <meta name="viewport" content="user-scalable=no"> */'):
            self.assertEqual(self.rules(a__tsx=source), {}, source)

    def test_real_markup_next_to_quotes_is_still_read(self):
        source = '<p className="x"><a href="/y"><Icon/></a><img src="/a.png" /></p>\n<div className="a">it\'s</div><button onClick={go}>Go</button>'
        report = self.run_check(a__tsx=source)[1]
        self.assertEqual(report['rules'], {'control-without-name': 1, 'image-without-alt': 1})
        self.assertEqual(report['inventory']['raw button'], 1)

    def test_scss_line_comments_are_ignored(self):
        self.assertEqual(self.rules(a__scss='// button:focus { outline: none; }\n.a { color: red; }'), {})

    def test_script_focus_elements_with_tailwind_are_left_alone(self):
        for tag in ('<div role="dialog" tabIndex={-1} className="outline-none">x</div>', '<h1 tabIndex={-1} className="outline-none">x</h1>'):
            self.assertEqual(self.rules(a__tsx=tag), {}, tag)

    def test_tailwind_focus_replacements_are_recognised(self):
        for classes in ('outline-none data-[focus-visible]:ring-2', 'outline-none focus-visible:outline', 'outline-none focus-within:ring-2'):
            self.assertNotIn('focus-ring-removed', self.rules(a__tsx=f'<a className="{classes}" href="/x">Go</a>'), classes)

    def test_classnames_through_a_helper_are_read(self):
        self.assertIn('focus-ring-removed', self.rules(a__tsx='<button className={cn("outline-none", x)}>Go</button>'))

    def test_css_focus_decisions(self):
        for css in ('input{outline:none} input:focus{box-shadow:0 0 0 2px blue}', '.menu button:focus-visible{background:#eee;outline:none}',
                    '.search input{outline:none} .search:focus-within{color:black}', 'button{outline:none} :focus-visible{outline:2px solid}',
                    'div:focus-within{outline:none}', 'button:active{outline:none}', 'a:hover{outline:none}', '@media print{button{outline:none}}'):
            self.assertNotIn('focus-ring-removed', self.rules(a__css=css), css)
        for css in ('button{border:none;background:none;outline:none;cursor:pointer}', 'button:focus{outline:none;border:none}',
                    'a:focus{outline:none} .card:focus-visible{outline:2px solid}', 'a:focus{outline:0px}', 'a:focus{outline-width:0}', ':focus{outline:none}'):
            self.assertIn('focus-ring-removed', self.rules(a__css=css), css)

    def test_framework_attribute_forms(self):
        for source in ('<img {src} {alt} />', '<img :src="s" :alt="a" />', '<img v-bind="attrs" />', '<img aria-label="Acme" src="/a.png" />',
                       '<img role="presentation" src="/a.png" />'):
            self.assertEqual(self.rules(a__svelte=source), {}, source)
        self.assertEqual(self.rules(a__tsx='<button><svg><title>Close</title></svg></button>'), {})
        self.assertEqual(self.rules(a__tsx='<button><svg aria-label="Close"/></button>'), {})
        self.assertEqual(self.rules(a__tsx='<a href="/x" aria-hidden="true" tabIndex={-1}><Icon/></a>'), {})

    def test_lookalike_attributes_do_not_count(self):
        self.assertEqual(self.rules(a__tsx='<img data-alt="x" src="/a.png" />'), {'image-without-alt': 1})
        self.assertEqual(self.rules(a__tsx='<button data-title="x"><Icon/></button>'), {'control-without-name': 1})

    def test_zoom_forms(self):
        self.assertEqual(self.rules(a__html='<meta content="width=device-width, maximum-scale=1" name="viewport">'), {'zoom-disabled': 1})
        self.assertEqual(self.rules(a__html='<meta name="viewport" content="maximum-scale=1.5">'), {})
        self.assertEqual(self.rules(a__tsx='export const viewport = { userScalable: false };'), {'zoom-disabled': 1})

    def test_a_comment_with_an_apostrophe_cannot_hide_a_tag(self):
        self.assertEqual(self.rules(a__tsx='<img\n  // do not lazy load\n  // don\'t\n  src="/a.png"\n/>'), {'image-without-alt': 1})

    def test_folder_names_are_judged_below_the_root_and_skips_are_reported(self):
        (self.root/'build').mkdir()
        target = self.root/'build'/'page.tsx'
        target.write_text('<img src="/a.png" />')
        result = subprocess.run([sys.executable, str(SCRIPT), str(target)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 1, 'an explicit file is always read')
        report = self.run_check(ok__tsx='<p>x</p>')[1]
        self.assertEqual(report['skipped_count'], 1)
        self.assertIn('build', report['skipped'][0]['reason'])
        (self.root/'big.tsx').write_text('x' * 2_100_000)
        report = self.run_check()[1]
        self.assertIn('over 2 MB', [item['reason'] for item in report['skipped']])

    def test_embedded_styles_report_their_real_line(self):
        report = self.run_check(a__vue='<template>\n<p/>\n</template>\n<style>\nbutton:focus { outline: none; }\n</style>')[1]
        self.assertEqual(report['findings'][0]['line'], 5)

    def test_nothing_to_check_is_not_a_pass(self):
        (self.root/'notes.md').write_text('x')
        self.assertEqual(self.run_check()[0], 2)
        result = subprocess.run([sys.executable, str(SCRIPT), '/no/such/path'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
