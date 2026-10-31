"""Contracts for explicit illustrated charts, not model-checking qualification."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/architect/scripts/illustrate-statechart.py'
ADAPTER = ROOT/'skills/architect/examples/leased-job/illustrate-replay.py'
SPACEPORT = ROOT/'skills/architect/examples/illustrated-statechart/spaceport.json'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


art = load('chart_art', SCRIPT)
replay_art = load('replay_art', ADAPTER)


def chart():
    return {'title':'Bread / proof then bake', 'subtitle':'A bakery design, not a formal check.',
            'evidence':'Unchecked design. Oven temperature and allergen handling are outside this drawing.',
            'width':1000, 'height':700,
            'nodes':[{'id':'dough', 'title':'Dough is ready', 'x':70,'y':260,'width':300,'height':220,'start':True,
                      'lines':['One prepared batch'], 'details':{'recipe':'flour & water'}},
                     {'id':'oven','title':'In the oven','x':620,'y':260,'width':300,'height':220,
                      'lines':['Timer running']}],
            'edges':[{'id':'bake','from':'dough','to':'oven','label':'Baker.Bake','guard':'oven is hot',
                      'points':[[380,390],[610,390]],'labelX':400,'labelY':315,'labelWidth':190}],
            'trace':[{'step':0,'node':'dough'},{'step':1,'node':'oven','edge':'bake'}]}


def sample_replay():
    initial={'phase':'ready','generation':0,'owner':0,'tokens':[0,0],'result':None,'published':[],'lateCancel':False}
    leased={'phase':'leased','generation':1,'owner':1,'tokens':[1,0],'result':None,'published':[],'lateCancel':False}
    return {'initial':initial, 'traceSteps':1, 'events':[{'step':1,'action':'Claim','accepted':True,'state':leased}]}


class IllustratedChartTests(unittest.TestCase):
    def test_two_domains_preserve_semantics_and_geometry(self):
        for source in [chart(), json.loads(SPACEPORT.read_text())]:
            with self.subTest(title=source['title']):
                plain = ET.fromstring(art.render(source, overlay=True))
                illustrated = ET.fromstring(art.render(source))
                for attr, expected in [('data-node-id', {row['id'] for row in source['nodes']}),
                                       ('data-edge-id', {row['id'] for row in source['edges']}),
                                       ('data-group-id', {row['id'] for row in source.get('groups',[])})]:
                    self.assertEqual({row.attrib[attr] for row in illustrated.iter() if attr in row.attrib}, expected)
                    self.assertEqual({row.attrib[attr] for row in plain.iter() if attr in row.attrib}, expected)
                for row in source['edges']:
                    self.assertIn(row['label'], ''.join(illustrated.itertext()))
                    self.assertIn(row.get('guard',''), ' '.join(illustrated.itertext()))
                paths = lambda svg:{row.attrib['data-edge-id']:row.find('{http://www.w3.org/2000/svg}path').attrib['d'] for row in svg.iter() if 'data-edge-id' in row.attrib}
                self.assertEqual(paths(plain), paths(illustrated))
        spaceport=json.loads(SPACEPORT.read_text())
        self.assertEqual({row['kind'] for row in spaceport['groups']},{'parent','parallel','region'})
        self.assertGreater(sum(row['from']=='lock.cycling' for row in spaceport['edges']),1)
        self.assertTrue(any(row['to']=='lock.sealed' for row in spaceport['edges']))

    def test_routes_bind_declared_endpoints_and_source_bytes_match_rendered_records(self):
        source=chart(); source['edges'][0]['points'].reverse()
        with self.assertRaisesRegex(ValueError,'declared node boundary'):
            art.render(source)
        source=chart(); source['edges'][0]['points'][0]=[500,500]
        with self.assertRaisesRegex(ValueError,'declared node boundary'):
            art.render(source)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'art'
            wrong=chart(); wrong['nodes'][0]['details']={'claimed':True}
            intended=copy.deepcopy(wrong); intended['nodes'][0]['details']={'claimed':1}
            with self.assertRaisesRegex(ValueError,'Source bytes'):
                art.publish(intended,out,json.dumps(wrong).encode())
            self.assertFalse(out.exists())
        workflow=json.loads((ROOT/'skills/architect/examples/illustrated-statechart/workflow.json').read_text())
        self.assertIn('checkout',next(n for n in workflow['nodes'] if n['id']=='build')['lines'][0])
        self.assertIn('commit within task authority',next(e for e in workflow['edges'] if e['id']=='checks.pass')['details']['fullGuard'])
        art.render(workflow)

    def test_art_is_deterministic_and_is_not_a_checker_verdict(self):
        source=chart()
        self.assertEqual(art.render(source), art.render(copy.deepcopy(source)))
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'art'
            art.publish(source,out)
            self.assertEqual(json.loads((out/'chart.json').read_text()),source)
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertEqual(receipt['status'],'rendered; behavior unverified')
            self.assertIn('does not infer independence',(out/'index.html').read_text())

    def test_plain_text_is_escaped_without_template_rescanning(self):
        source=chart()
        source['title']='TITLE <script>alert(1)</script>'
        source['nodes'][0]['details']={'payload':'<img src=x onerror=alert(1)> EVIDENCE ROWS TRACE'}
        source['edges'][0]['label']='Baker.<Bake>'
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'art'; art.publish(source,out)
            svg=(out/'chart.svg').read_text(); page=(out/'index.html').read_text()
            self.assertNotIn('<script>',svg); self.assertNotIn('<img src=x',page)
            self.assertIn('&lt;script&gt;',svg); self.assertIn('&lt;img',page)
            self.assertIn('EVIDENCE ROWS TRACE',page)
            self.assertEqual(json.loads((out/'chart.json').read_text()),source)

    def test_trace_occurrences_retain_revisits_and_reject_invented_highlights(self):
        source=chart()
        source['edges'].append({'id':'repeat','from':'oven','to':'oven','label':'Timer.Tick','points':[[930,310],[970,310],[970,450],[930,450]],'labelX':640,'labelY':550,'labelWidth':200})
        for index in range(2,13):
            source['trace'].append({'step':index,'node':'oven','edge':'repeat'})
        result=art.render(source)
        self.assertIn('>1+</text>',result)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'art'; art.publish(source,out)
            self.assertEqual(len(json.loads((out/'chart.json').read_text())['trace']),13)
        source['trace']=source['trace'][:2]; source['edges'][1]['trace']=True
        with self.assertRaisesRegex(ValueError,'actual trace'):
            art.render(source)
        source['edges'][1]['trace']=False
        source['trace']=[]; source['edges'][0]['trace']=True
        with self.assertRaisesRegex(ValueError,'actual trace'):
            art.render(source)
        source=chart(); source['trace'][1]['edge']='missing'
        with self.assertRaisesRegex(ValueError,'connect consecutive'):
            art.render(source)

    def test_invalid_geometry_does_not_silently_drop_content(self):
        variants=[]
        source=chart(); source['nodes'][1]['x']=100; variants.append(source)
        source=chart(); source['nodes'][0]['lines']=['long '*30]*12; variants.append(source)
        source=chart(); source['edges'][0]['labelX']=100; source['edges'][0]['labelY']=350; variants.append(source)
        source=chart(); source['nodes'][0]['parent']='missing'; variants.append(source)
        source=chart(); source['nodes'][0]['x']=float('nan'); variants.append(source)
        source=chart(); source['edges'][0]['points']=[[1,2],[30000,4]]; variants.append(source)
        source=chart(); source['theme']={'ink':'red\" onload=\"x'}; variants.append(source)
        source=chart(); source['unexpected']='ignored?'; variants.append(source)
        for source in variants:
            with self.subTest(source=source), self.assertRaises((ValueError,TypeError)):
                art.render(source)

    def test_art_primitives_stay_in_reserved_zones(self):
        source=json.loads(SPACEPORT.read_text())
        result=art.render(source)
        self.assertIn('data-decoration-id="orbital-station"',result)
        source['decorations'][0]['x']=50; source['decorations'][0]['y']=300
        with self.assertRaisesRegex(ValueError,'reserved area'):
            art.render(source)
        source=json.loads(SPACEPORT.read_text())
        duplicate=copy.deepcopy(source['decorations'][0]); duplicate['id']='overlap'
        source['decorations'].append(duplicate)
        with self.assertRaisesRegex(ValueError,'reserved area|boxes overlap'):
            art.render(source)
        source=json.loads(SPACEPORT.read_text())
        source['decorations'][0]['shapes'][0]['kind']='script'
        with self.assertRaisesRegex(ValueError,'primitive'):
            art.render(source)
        source=json.loads(SPACEPORT.read_text())
        source['decorations'][0]['shapes'][0]['width']=5000
        with self.assertRaisesRegex(ValueError,'reserved box'):
            art.render(source)

    def test_cli_refuses_overwrite_symlink_oversize_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'chart.json'; source.write_text(json.dumps(chart())); out=root/'art'
            def run():
                return subprocess.run([sys.executable,str(SCRIPT),'--input',str(source),'--out',str(out)],capture_output=True,text=True)
            self.assertEqual(run().returncode,0)
            before=(out/'chart.svg').read_bytes()
            self.assertEqual(run().returncode,2)
            self.assertEqual((out/'chart.svg').read_bytes(),before)
            other=root/'other'; other.mkdir(); out=root/'link'; out.symlink_to(other,target_is_directory=True)
            self.assertEqual(run().returncode,2); self.assertEqual(list(other.iterdir()),[])
            out=root/'new'
            source.write_text(' '*262145); self.assertEqual(run().returncode,2); self.assertFalse(out.exists())
            source.write_text('{"x":NaN}'); self.assertEqual(run().returncode,2); self.assertFalse(out.exists())
            source.write_text('{"title":"first","title":"second"}'); self.assertEqual(run().returncode,2); self.assertFalse(out.exists())
            self.assertIn('Duplicate JSON key',run().stderr)

    def test_replay_adapter_preserves_initial_exact_snapshots_and_observed_acceptance(self):
        source=sample_replay(); result=replay_art.build_chart(source)
        self.assertEqual([row['details'] for row in result['nodes']],[source['initial'],source['events'][0]['state']])
        self.assertNotIn('guard',result['edges'][0])
        self.assertEqual(result['edges'][0]['details'],{'action':'Claim','accepted':True})
        self.assertTrue(result['nodes'][0]['start'])
        rendered=art.render(result)
        self.assertIn('DELIVERIES / W1 E1',rendered)
        self.assertEqual(len(result['decorations']),2)
        del source['initial']
        with self.assertRaisesRegex(ValueError,'initial snapshot'):
            replay_art.build_chart(source)


if __name__=='__main__':
    unittest.main()
