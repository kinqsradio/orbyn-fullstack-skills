#!/usr/bin/env python3
"""Draw this sample's observed replay as an original, offline dispatch-board plate.

This is a trace renderer, not a Mermaid parser, model checker or replay verifier.
It neither executes input nor accepts arbitrary artwork/HTML from the receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

LIMIT = 262144
FIELDS = {'phase', 'generation', 'owner', 'tokens', 'result', 'published', 'lateCancel'}
ACTIONS = {'Claim', 'Expire', 'Complete', 'Cancel', 'LateCancel', 'Publish', 'Terminal'}


def integer(value, low=0, high=2):
    return type(value) is int and low <= value <= high


def payload(value, published=False):
    expected = {'worker', 'generation', 'payload'} | ({'key'} if published else set())
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError('Invalid result/publication fields')
    if not integer(value['worker'], 1) or not integer(value['generation'], 1):
        raise ValueError('Invalid result/publication identity')
    for key in ['payload'] + (['key'] if published else []):
        if not isinstance(value[key], str) or len(value[key]) > 512:
            raise ValueError('Result text must be at most 512 characters')


def state(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError('Invalid sample state fields; an explicit initial snapshot is required')
    if value['phase'] not in ['ready', 'leased', 'done', 'cancelled']:
        raise ValueError('Unknown sample phase')
    if not integer(value['generation']) or not integer(value['owner']):
        raise ValueError('Invalid generation/owner')
    if not isinstance(value['tokens'], list) or len(value['tokens']) != 2 or not all(integer(x) for x in value['tokens']):
        raise ValueError('Expected two bounded delivery tokens')
    if type(value['lateCancel']) is not bool:
        raise ValueError('Invalid lateCancel')
    if value['result'] is not None:
        payload(value['result'])
    if not isinstance(value['published'], list) or len(value['published']) > 1:
        raise ValueError('Expected zero or one publication')
    for item in value['published']:
        payload(item, published=True)
    return value


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Expected a replay object')
    initial = state(data.get('initial'))
    events = data.get('events')
    if not isinstance(events, list) or not 1 <= len(events) <= 20:
        raise ValueError('Expected 1..20 observed events')
    if not integer(data.get('traceSteps'), 1, 20) or data['traceSteps'] != len(events):
        raise ValueError('traceSteps must match events')
    for index, event in enumerate(events, 1):
        if not isinstance(event, dict) or set(event) != {'step', 'action', 'accepted', 'state'}:
            raise ValueError('Invalid event fields')
        if type(event['step']) is not int or event['step'] != index or event['action'] not in ACTIONS:
            raise ValueError('Expected sequential steps and known sample actions')
        if type(event['accepted']) is not bool:
            raise ValueError('Invalid accepted value')
        state(event['state'])
    return [initial] + [event['state'] for event in events]


def build_chart(data):
    states = validate(data)
    nodes, edges, trace, decorations = [], [], [], []
    def point(index):
        row, column = divmod(index, 2)
        if row % 2:
            column = 1-column
        return 100+column*650, 260+row*480
    for index, item in enumerate(states):
        x,y = point(index)
        result = item['result']
        labels = []
        if result is not None and result['generation'] != item['generation']:
            labels.append('FreshResult mismatch')
        if any(row['generation'] != item['generation'] for row in item['published']):
            labels.append('PublishedFresh mismatch')
        node = {'id':f's{index}', 'title':f'Job / {item["phase"]}', 'x':x,'y':y,'width':450,'height':360,
                'lines':[f'Current epoch: {item["generation"]}', f'Lease owner: W{item["owner"]}' if item['owner'] else 'Lease owner: none',

                         f'Result: W{result["worker"]}/E{result["generation"]}' if result else 'Result: none',
                         f'Published: {len(item["published"])} · late cancel: {str(item["lateCancel"]).lower()}'],
                'details':item,'artHeight':100}
        if index==0:
            node['start']=True
        if item['published'] or item['phase']=='cancelled':
            node['terminal']=True
        if labels:
            node['warning']=' / '.join(labels)
        nodes.append(node)
        shapes=[]
        for worker,epoch in enumerate(item['tokens']):
            ex=20+worker*210
            colour='#996e3c' if worker==0 else '#426a5b'
            shapes += [{'kind':'rect','x':ex,'y':40,'width':150,'height':45,'fill':'#fffaf0','stroke':colour,'strokeWidth':1.8},
                       {'kind':'polyline','points':[[ex,40],[ex+75,68],[ex+150,40]],'stroke':colour},
                       {'kind':'polyline','points':[[ex,85],[ex+50,60]],'stroke':colour},
                       {'kind':'polyline','points':[[ex+150,85],[ex+100,60]],'stroke':colour}]
            if epoch:
                shapes.append({'kind':'circle','cx':ex+131,'cy':54,'r':7,'fill':colour,'stroke':colour})
                for tick in range(epoch):
                    shapes.append({'kind':'polyline','points':[[ex+65+tick*12,76],[ex+65+tick*12,82]],'stroke':colour,'strokeWidth':2})
            else:
                shapes += [{'kind':'polyline','points':[[ex+59,45],[ex+89,80]],'stroke':colour},
                           {'kind':'polyline','points':[[ex+89,45],[ex+59,80]],'stroke':colour}]
        token_labels=[f'W{worker} E{epoch}' if epoch else f'W{worker} none' for worker,epoch in enumerate(item['tokens'],1)]
        decorations.append({'id':f'delivery-art-{index}','node':f's{index}','title':'DELIVERIES / '+' · '.join(token_labels),
                            'x':x+10,'y':y+260,'width':430,'height':90,'shapes':shapes})
        occurrence={'step':index,'node':f's{index}'}
        if index:
            occurrence['edge']=f'e{index}'
            event=data['events'][index-1]
            px,py=point(index-1)
            if py==y:
                right=x>px
                points=[[px+450+8 if right else px-8,py+160],[x-12 if right else x+450+12,y+160]]
                lx,ly=min(x,px)+470,y+100
                label_width=170
            else:
                points=[[px+225,py+370],[x+225,y-20]]
                lx,ly=px+245,py+417
                label_width=185
            edges.append({'id':f'e{index}','from':f's{index-1}','to':f's{index}','label':event['action']+' · '+('accepted' if event['accepted'] else 'rejected'),
                          'details':{'action':event['action'],'accepted':event['accepted']},'points':points,'labelX':lx,'labelY':ly,'labelWidth':label_width,'trace':True})
        trace.append(occurrence)
    return {'title':'The late delivery','subtitle':'A dispatch board: the lease expires, but an old delivery can still arrive.',
            'evidence':'Supplied serialized leased-job replay snapshots. The adapter does not execute or verify their origin. Paper tickets retain exact snapshots; envelopes are token slots, not independent worker machines. Generation mismatches describe supplied data, not a new TLC verdict. When produced by the checked demo, its separate reports retain checker and source-correspondence evidence.',
            'width':1320,'height':260+((len(states)+1)//2)*480,'nodes':nodes,'edges':edges,'trace':trace,'decorations':decorations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        if not args.replay.is_file() or args.replay.stat().st_size > LIMIT:
            raise ValueError('Replay must be a regular JSON file up to 256 KiB')
        source = args.replay.read_bytes()
        if len(source)>LIMIT:
            raise ValueError('Replay exceeds 256 KiB')
        import importlib.util
        spec=importlib.util.spec_from_file_location('illustrate_statechart', Path(__file__).resolve().parents[2]/'scripts/illustrate-statechart.py')
        renderer=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        chart=build_chart(renderer.strict_json(source))
        print(renderer.publish(chart,args.out))
        with (args.out/'replay.json').open('xb') as target:
            target.write(source)
        receipt_path=args.out/'receipt.json'
        receipt=json.loads(receipt_path.read_text())
        receipt['replaySha256']=hashlib.sha256(source).hexdigest()
        receipt['adapterSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        receipt['outputs']['replay.json']=receipt['replaySha256']
        receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
        return 0
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as error:
        print(str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
