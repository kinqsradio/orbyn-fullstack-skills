#!/usr/bin/env python3
"""Render an explicit illustrated chart record, without parsing or checking a model.

JSON contract (all geometry is explicit SVG viewBox coordinates):
  title, subtitle?, evidence (plain text; never a tool verdict), width, height;
  nodes: [{id, title, x, y, width, height, lines?, details?, parent?, warning?}];
  edges: [{id, from, to, label, guard?, points:[[x,y],...], labelX, labelY,
           labelWidth?, trace?}];
  groups?: [{id, title, kind:parent|parallel|region, x,y,width,height,parent?}];
  trace?: [{step,node,edge?}]; theme?: {paper,ink,accent,warning} hex colours.
  decorations?: [{id,title,x,y,width,height,shapes:[{kind:rect|circle|polyline,
    x?,y?,width?,height?,cx?,cy?,r?,points?,closed?,fill?,stroke?,strokeWidth?}]}].
Decorations occupy reserved boxes outside headers, groups, nodes and edge bounds.
Nodes may carry start/terminal booleans, preserved as explicit text labels.
Optional node artHeight reserves a bottom band; a decoration may name node:id
to occupy only that band. Edge details is inert JSON (e.g. observed acceptance).
Optional node lines are plain text. details is inert JSON retained exactly in
HTML. trace records occurrences, so revisiting one node does not erase a step.
Containment and routes are author-owned layout, not inferred graph semantics.
This finite renderer accepts arbitrary domains, not arbitrary executable artwork.
"""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys
import textwrap

LIMIT = 262144
COLOURS = {'paper': '#f5efdf', 'ink': '#293c36', 'accent': '#426a5b', 'warning': '#a44234'}


def escape(value):
    return html.escape(str(value), quote=True)


def string(value, label, limit=180):
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ValueError(f'{label} must be nonempty text up to {limit} characters')
    if any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise ValueError(f'{label} contains control characters')
    return value


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise ValueError('Missing or unknown record fields')


def number(value, label):
    if type(value) not in (int, float) or not 0 <= value <= 20000 or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite coordinate in 0..20000')
    return value


def box(record, width, height):
    for key in ['x', 'y', 'width', 'height']:
        number(record[key], key)
    if record['width'] < 160 or record['height'] < 70 or record['x'] + record['width'] > width or record['y'] + record['height'] > height:
        raise ValueError('Box is too small or outside the canvas')


def validate(chart):
    json.dumps(chart, allow_nan=False)
    fields(chart, ['title', 'evidence', 'width', 'height', 'nodes', 'edges'], ['subtitle', 'groups', 'trace', 'theme', 'decorations'])
    string(chart['title'], 'title', 100)
    string(chart['evidence'], 'evidence', 1000)
    if 'subtitle' in chart:
        string(chart['subtitle'], 'subtitle', 180)
    width, height = number(chart['width'], 'width'), number(chart['height'], 'height')
    if width < 400 or height < 300:
        raise ValueError('Canvas must be at least 400 by 300')
    for key, maximum in [('nodes', 100), ('edges', 250), ('groups', 30), ('trace', 250), ('decorations', 20)]:
        value = chart.get(key, [])
        if not isinstance(value, list) or len(value) > maximum:
            raise ValueError(f'{key} exceeds its finite drawing budget')
    if not chart['nodes']:
        raise ValueError('At least one node is required')
    palette = chart.get('theme', {})
    fields(palette, [], COLOURS)
    if any(not isinstance(colour, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', colour) for colour in palette.values()):
        raise ValueError('Theme colours must be six-digit hex')
    ids, nodes, groups = set(), {}, {}
    for group in chart.get('groups', []):
        fields(group, ['id', 'title', 'kind', 'x', 'y', 'width', 'height'], ['parent'])
        if group['kind'] not in ['parent', 'parallel', 'region']:
            raise ValueError('Unknown group kind')
        groups[string(group['id'], 'group id', 80)] = group
    for node in chart['nodes']:
        fields(node, ['id', 'title', 'x', 'y', 'width', 'height'], ['lines', 'details', 'parent', 'warning', 'start', 'terminal', 'artHeight'])
        string(node['title'], 'node title', 100)
        for flag in ['start', 'terminal']:
            if flag in node and type(node[flag]) is not bool:
                raise ValueError('Start/terminal flags must be boolean')
        if 'warning' in node:
            string(node['warning'], 'warning', 180)
        if 'artHeight' in node and not 70 <= number(node['artHeight'],'artHeight') <= node['height']-70:
            raise ValueError('Invalid reserved node artwork height')
        lines = node.get('lines', [])
        if not isinstance(lines, list) or len(lines) > 12:
            raise ValueError('A node supports at most twelve text lines')
        for line in lines:
            string(line, 'node line', 180)
        nodes[string(node['id'], 'node id', 80)] = node
    for record in chart.get('groups', []) + chart['nodes']:
        identity = record['id']
        if identity in ids:
            raise ValueError('Duplicate node/group id')
        ids.add(identity)
        string(record['title'], 'record title', 100)
        box(record, width, height)
        parent = record.get('parent')
        if parent is not None:
            string(parent, 'parent', 80)
            if parent not in groups or parent == identity:
                raise ValueError('Unknown/self parent')
            owner = groups[parent]
            if not (owner['x'] <= record['x'] and owner['y']+35 <= record['y'] and record['x']+record['width'] <= owner['x']+owner['width'] and record['y']+record['height'] <= owner['y']+owner['height']):
                raise ValueError('Child must fit within its parent below the heading')
            seen = {identity}
            while parent:
                if parent in seen or parent not in groups:
                    raise ValueError('Cyclic or missing parent')
                seen.add(parent)
                parent = groups[parent].get('parent')
    edge_ids = set()
    for edge in chart['edges']:
        fields(edge, ['id', 'from', 'to', 'label', 'points', 'labelX', 'labelY'], ['guard', 'labelWidth', 'trace', 'details'])
        identity = string(edge['id'], 'edge id', 80)
        if identity in edge_ids:
            raise ValueError('Duplicate edge id')
        edge_ids.add(identity)
        if edge['from'] not in nodes or edge['to'] not in nodes:
            raise ValueError('Edge endpoint missing')
        string(edge['label'], 'edge label', 180)
        if 'guard' in edge:
            string(edge['guard'], 'guard', 180)
        if 'trace' in edge and type(edge['trace']) is not bool:
            raise ValueError('trace highlight must be boolean')
        points = edge['points']
        if not isinstance(points, list) or not 2 <= len(points) <= 32:
            raise ValueError('A route requires 2..32 points')
        for point in points:
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError('Invalid route point')
            if number(point[0], 'point x') > width or number(point[1], 'point y') > height:
                raise ValueError('Route outside canvas')
        for endpoint, point in [('from', points[0]), ('to', points[-1])]:
            owner = nodes[edge[endpoint]]
            dx = max(owner['x']-point[0], 0, point[0]-owner['x']-owner['width'])
            dy = max(owner['y']-point[1], 0, point[1]-owner['y']-owner['height'])
            if not 0 < math.hypot(dx, dy) <= 32:
                raise ValueError('Route endpoint must sit outside and within 32 units of its declared node boundary')
        for key, bound in [('labelX', width), ('labelY', height)]:
            if number(edge[key], key) > bound:
                raise ValueError('Label outside canvas')
        if not 80 <= number(edge.get('labelWidth', 180), 'labelWidth') <= 600:
            raise ValueError('Label width must be 80..600')
    previous = None
    edges = {edge['id']: edge for edge in chart['edges']}
    for index, occurrence in enumerate(chart.get('trace', [])):
        fields(occurrence, ['step', 'node'], ['edge'])
        if type(occurrence['step']) is not int or occurrence['step'] != index or occurrence['node'] not in nodes:
            raise ValueError('Trace occurrences must be numbered from zero and reference nodes')
        if index == 0 and 'edge' in occurrence:
            raise ValueError('Initial occurrence cannot have an incoming edge')
        if index:
            edge = edges.get(occurrence.get('edge'))
            if not edge or edge['from'] != previous or edge['to'] != occurrence['node']:
                raise ValueError('Trace edge must connect consecutive occurrences')
        previous = occurrence['node']
    for index,node in enumerate(chart['nodes']):
        for other in chart['nodes'][index+1:]:
            if node['x'] < other['x']+other['width'] and other['x'] < node['x']+node['width'] and node['y'] < other['y']+other['height'] and other['y'] < node['y']+node['height']:
                raise ValueError('Semantic node boxes overlap; repair the explicit layout')
    trace_edges = {item.get('edge') for item in chart.get('trace', [])}
    for edge in chart['edges']:
        if edge.get('trace') and edge['id'] not in trace_edges:
            raise ValueError('Trace highlight requires an actual trace occurrence')
    header_lines = len(wrapped(chart['title'], width-100, 42))
    header_bottom = 113+(header_lines-1)*50
    if chart.get('subtitle'):
        header_bottom += 40+len(wrapped(chart['subtitle'], width-100, 18))*24
    for record in chart.get('groups', [])+chart['nodes']:
        if record['y'] < header_bottom+20:
            raise ValueError('Semantic box overlaps the title/subtitle area')
    def intersects(a,b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
    reserved = [(0,0,width,header_bottom+20)]
    reserved += [(row['x']-20,row['y']-15,row['x']+row['width']+8,row['y']+row['height']+8) for row in chart.get('groups', [])+chart['nodes']]
    for edge in chart['edges']:
        xs,ys=zip(*edge['points'])
        reserved.append((min(xs)-8,min(ys)-8,max(xs)+8,max(ys)+8))
        label_width=edge.get('labelWidth',180)
        lines=wrapped(edge['label'],label_width-12,16)+(wrapped('['+edge['guard']+']',label_width-12,14) if edge.get('guard') else [])
        label_bounds=(edge['labelX']-5,edge['labelY']-20,edge['labelX']+label_width,edge['labelY']+len(lines)*22)
        if any(intersects(label_bounds,(node['x'],node['y'],node['x']+node['width'],node['y']+node['height'])) for node in chart['nodes']):
            raise ValueError('Edge label overlaps a semantic node box')
        reserved.append(label_bounds)
    decoration_regions=[]
    for decoration in chart.get('decorations',[]):
        fields(decoration,['id','title','x','y','width','height','shapes'],['node'])
        identity=string(decoration['id'],'decoration id',80)
        if identity in ids:
            raise ValueError('Duplicate decoration id')
        ids.add(identity)
        string(decoration['title'],'decoration title',100)
        box(decoration,width,height)
        bounds=(decoration['x'],decoration['y'],decoration['x']+decoration['width'],decoration['y']+decoration['height'])
        if 'node' in decoration:
            owner=nodes.get(decoration['node'])
            if not owner or not owner.get('artHeight') or not (owner['x']+8<=bounds[0] and owner['y']+owner['height']-owner['artHeight']<=bounds[1] and bounds[2]<=owner['x']+owner['width']-8 and bounds[3]<=owner['y']+owner['height']-8):
                raise ValueError('Node decoration must fit its explicitly reserved artwork band')
        elif any(intersects(bounds,other) for other in reserved):
            raise ValueError('Decoration must occupy a reserved area outside semantic geometry')
        if any(intersects(bounds,other) for other in decoration_regions):
            raise ValueError('Decoration boxes overlap')
        decoration_regions.append(bounds)
        reserved.append(bounds)
        shapes=decoration['shapes']
        if not isinstance(shapes,list) or len(shapes)>100:
            raise ValueError('Decoration shape budget exceeded')
        for shape in shapes:
            fields(shape,['kind'],['x','y','width','height','cx','cy','r','points','closed','fill','stroke','strokeWidth'])
            kind=shape['kind']
            geometry={'rect':{'x','y','width','height'},'circle':{'cx','cy','r'},'polyline':{'points'}}.get(kind)
            if geometry is None or not geometry<=set(shape) or set(shape)-{'kind','fill','stroke','strokeWidth','closed'} != geometry:
                raise ValueError('Invalid decoration primitive geometry')
            for colour_key in ['fill','stroke']:
                colour=shape.get(colour_key,'none')
                if not isinstance(colour,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}|none',colour):
                    raise ValueError('Decoration colours must be hex or none')
            if not 0<number(shape.get('strokeWidth',1.5),'strokeWidth')<=8:
                raise ValueError('Invalid decoration stroke width')
            if 'closed' in shape and (kind!='polyline' or type(shape['closed']) is not bool):
                raise ValueError('Only polylines support boolean closed')
            if kind=='rect':
                px,py,pw,ph=[number(shape[key],key) for key in ['x','y','width','height']]
                extents=(px,py,px+pw,py+ph)
            elif kind=='circle':
                cx,cy,r=[number(shape[key],key) for key in ['cx','cy','r']]
                extents=(cx-r,cy-r,cx+r,cy+r)
            else:
                points=shape['points']
                if not isinstance(points,list) or not 2<=len(points)<=100 or any(not isinstance(point,list) or len(point)!=2 for point in points):
                    raise ValueError('Invalid decoration polyline')
                xs=[number(point[0],'point x') for point in points]; ys=[number(point[1],'point y') for point in points]
                extents=(min(xs),min(ys),max(xs),max(ys))
            margin=shape.get('strokeWidth',1.5)/2
            if extents[0]<margin or extents[1]<35+margin or extents[2]>decoration['width']-margin or extents[3]>decoration['height']-margin:
                raise ValueError('Decoration primitive exceeds its reserved box')
    return chart


def text(x, y, value, size=18, fill='#293c36', extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(value)}</text>'


def wrapped(value, width, size):
    # Conservative serif advance budget; final visual inspection remains required.
    return textwrap.wrap(value, max(5, int(width / (size * .65))), break_long_words=True, break_on_hyphens=False) or ['']


def render(chart, overlay=False):
    validate(chart)
    colours = COLOURS | chart.get('theme', {})
    ink, accent, warning, paper = [colours[key] for key in ['ink', 'accent', 'warning', 'paper']]
    width, height = chart['width'], chart['height']
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc">',
              f'<title id="chart-title">{escape(chart["title"])}</title><desc id="chart-desc">{escape(chart["evidence"])}</desc>',
              f'<defs><pattern id="paper" width="19" height="19" patternUnits="userSpaceOnUse"><path d="M2 4h1M12 15h1" stroke="{ink}" stroke-opacity=".09"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="{warning}" stroke-width="1.8"/></marker><marker id="normal-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="{accent}" stroke-width="1.8"/></marker></defs>',
              f'<rect width="{width}" height="{height}" fill="{paper}"/>',
              f'<rect width="{width}" height="{height}" fill="url(#paper)"/>', '<g font-family="Georgia,serif">',
              text(50, 53, 'STATECHART / ILLUSTRATED FIELD NOTES', 13, accent, 'letter-spacing="2"'),
              ]
    title_lines=wrapped(chart['title'], width-100, 42)
    for index,line in enumerate(title_lines):
        result.append(text(48,113+index*50,line,42,ink))
    header_y=113+(len(title_lines)-1)*50
    if chart.get('subtitle'):
        for index, line in enumerate(wrapped(chart['subtitle'], width-100, 18)):
            result.append(text(50, header_y+40+index*24, line, 18, ink))
    # Parents are drawn before children even when records arrive in another order.
    def depth(group):
        parents = {item['id']: item for item in chart.get('groups', [])}
        count, parent = 0, group.get('parent')
        while parent:
            count += 1
            parent = parents[parent].get('parent')
        return count
    for group in sorted(chart.get('groups', []), key=depth):
        x, y, w, h = [group[key] for key in ['x', 'y', 'width', 'height']]
        dash = 'stroke-dasharray="7 6"' if group['kind'] in ['parallel', 'region'] else ''
        group_label=f'{group["title"]} / {group["kind"]}'
        if len(wrapped(group_label,w-30,15))>1:
            raise ValueError('Group heading exceeds its reserved band; widen group or shorten display title')
        result += [f'<g data-group-id="{escape(group["id"])}" data-group-kind="{group["kind"]}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{paper}" fill-opacity=".75" stroke="{accent}" stroke-width="1.4" {dash}/>',
                   text(x+15, y+25, f'{group["title"]} / {group["kind"]}', 15, accent), '</g>']
    occurrences = {}
    for occurrence in chart.get('trace', []):
        occurrences.setdefault(occurrence['node'], []).append(occurrence['step'])
    for node in chart['nodes']:
        x, y, w, h = [node[key] for key in ['x', 'y', 'width', 'height']]
        colour = warning if node.get('warning') else accent
        result.append(f'<g data-node-id="{escape(node["id"])}">')
        if not overlay:
            result += [f'<rect x="{x+5}" y="{y+7}" width="{w}" height="{h}" rx="4" fill="{ink}" opacity=".10"/>',
                       f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#fffdf5" stroke="{colour}" stroke-width="1.8"/>',
                       f'<rect x="{x+w/2-40}" y="{y-9}" width="80" height="18" fill="{accent}" opacity=".18" transform="rotate(-3 {x+w/2} {y})"/>']
        else:
            result.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#246cad" stroke-width="2"/>')
        cursor = y+35
        flags=' / '.join(flag.upper() for flag in ['start','terminal'] if node.get(flag))
        for line in wrapped(node['title'], w-38, 23):
            result.append(text(x+19, cursor, line, 23, colour)); cursor += 29
        result.append(f'<path d="M{x+18} {cursor-13}H{x+w-18}" stroke="{accent}" stroke-opacity=".25" stroke-dasharray="4 5"/>')
        cursor += 12
        if flags:
            result.append(text(x+19,cursor,flags,13,colour)); cursor+=23
        for value in node.get('lines', []):
            for line in wrapped(value, w-38, 17):
                result.append(text(x+19, cursor, line, 17, ink)); cursor += 24
        if node.get('warning'):
            cursor += 5
            for line in wrapped(node['warning'], w-38, 15):
                result.append(text(x+19, cursor, line, 15, warning)); cursor += 20
        if cursor > y+h-node.get('artHeight',0)-12:
            raise ValueError(f'Node text exceeds its box: {node["id"]}; enlarge layout or shorten display text, retaining details')
        if node['id'] in occurrences:
            badge=','.join(map(str,occurrences[node['id']]))
            if len(badge)>4:
                badge=f'{occurrences[node["id"]][0]}+'
            result += [f'<circle cx="{x-15}" cy="{y+25}" r="17" fill="{colour}"/>', text(x-15, y+30, badge, 13, '#ffffff', 'text-anchor="middle"')]
        result.append('</g>')
    for edge in chart['edges']:
        highlighted=edge['id'] in {item.get('edge') for item in chart.get('trace',[])}
        colour = warning if highlighted else accent
        marker = 'arrow' if highlighted else 'normal-arrow'
        route = 'M'+'L'.join(f'{x} {y}' for x,y in edge['points'])
        result.append(f'<g data-edge-id="{escape(edge["id"])}" data-edge-from="{escape(edge["from"])}" data-edge-to="{escape(edge["to"])}"><path d="{route}" fill="none" stroke="{colour if not overlay else "#246cad"}" stroke-width="2.4" stroke-linejoin="round" marker-end="url(#{marker})"/>')
        label_width = edge.get('labelWidth', 180)
        lines = wrapped(edge['label'], label_width-12, 16)
        if edge.get('guard'):
            lines += wrapped('['+edge['guard']+']', label_width-12, 14)
        x,y = edge['labelX'], edge['labelY']
        if x+label_width > width or y-20 < 0 or y+22*len(lines) > height:
            raise ValueError('Edge label text exceeds canvas')
        result.append(f'<rect x="{x-5}" y="{y-18}" width="{label_width}" height="{len(lines)*22+4}" fill="{paper}"/>')
        for index,line in enumerate(lines):
            result.append(text(x, y+index*22, line, 16, colour))
        result.append('</g>')
    for decoration in chart.get('decorations',[]):
        result.append(f'<g data-decoration-id="{escape(decoration["id"])}" transform="translate({decoration["x"]} {decoration["y"]})" aria-hidden="true">')
        for index,line in enumerate(wrapped(decoration['title'],decoration['width']-10,14)):
            if index:
                raise ValueError('Decoration heading exceeds its reserved band')
            result.append(text(5,23,line,14,accent))
        for shape in decoration['shapes']:
            style=f'fill="{shape.get("fill","none")}" stroke="{shape.get("stroke",accent)}" stroke-width="{shape.get("strokeWidth",1.5)}" stroke-linecap="round" stroke-linejoin="round"'
            if shape['kind']=='rect':
                result.append(f'<rect x="{shape["x"]}" y="{shape["y"]}" width="{shape["width"]}" height="{shape["height"]}" {style}/>')
            elif shape['kind']=='circle':
                result.append(f'<circle cx="{shape["cx"]}" cy="{shape["cy"]}" r="{shape["r"]}" {style}/>')
            else:
                tag='polygon' if shape.get('closed') else 'polyline'
                points=' '.join(f'{x},{y}' for x,y in shape['points'])
                result.append(f'<{tag} points="{points}" {style}/>')
        result.append('</g>')
    result += ['</g></svg>']
    return ''.join(result)


def publish(chart, out, source=None):
    if source is not None:
        canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)
        if canonical(strict_json(source)) != canonical(chart):
            raise ValueError('Source bytes do not match the rendered chart record')
    svg, overlay = render(chart), render(chart, overlay=True)
    raw = source if source is not None else (json.dumps(chart, indent=2, ensure_ascii=False)+'\n').encode()
    rows = ''.join('<tr><th scope="row">'+escape(item['id'])+'</th><td><pre>'+escape(json.dumps(item, indent=2, ensure_ascii=False))+'</pre></td></tr>' for item in chart.get('groups', [])+chart['nodes']+chart['edges']+chart.get('decorations', []))
    trace = escape(json.dumps(chart.get('trace', []), indent=2, ensure_ascii=False))
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TITLE</title><style>body{margin:0;background:#e8e2d4;color:#293c36;font:17px/1.6 system-ui}main{max-width:1200px;margin:auto;padding:32px 20px}h1{font:42px Georgia,serif}a{color:#325b4b}figure{margin:24px 0;overflow:auto;border:1px solid #cec4ae;background:#f5efdf}img{display:block;width:100%;min-width:760px}figcaption{padding:12px 20px;font-size:14px}summary{cursor:pointer;padding:16px 0}table{width:100%;border-collapse:collapse}th,td{border:1px solid #b9b7a6;padding:12px;text-align:left;vertical-align:top}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}section{overflow:auto}a:focus-visible,summary:focus-visible{outline:3px solid #9c503e;outline-offset:4px}@media print{body{background:white}img{min-width:0}main{padding:0}}</style><main><p>ORBYN / ILLUSTRATED STATECHART STUDY</p><h1>TITLE</h1><p>EVIDENCE</p><p><strong>Renderer boundary:</strong> supplied records are inert drawing data, not verified model results. Groups, guards and traces retain the author's explicit meaning; this renderer does not infer independence, reachable states or a checker verdict.</p><p><a href="chart.svg">Full-size art</a> · <a href="overlay.svg">Same-geometry layout</a> · <a href="chart.json">Editable chart record</a> · <a href="receipt.json">Render hashes</a></p><figure><img src="chart.svg" alt="TITLE; complete node, edge and trace records follow below."><figcaption>Paper tickets, numbered trace occurrences and explicit warning labels. Colour is not the only signal. Large charts scroll horizontally at narrow widths.</figcaption></figure><details><summary>Plain geometry for checking the artwork</summary><figure><img src="overlay.svg" alt="Same nodes, groups and routes with plain blue geometry"></figure></details><details open><summary>Exact semantic and layout records</summary><section><table><thead><tr><th>ID</th><th>Exact record</th></tr></thead><tbody>ROWS</tbody></table></section><h2>Trace occurrences</h2><pre>TRACE</pre></details></main></html>'''
    # Replace only template tokens in one pass; user strings are never rescanned.
    replacements = {'TITLE': escape(chart['title']), 'EVIDENCE': escape(chart['evidence']), 'ROWS': rows, 'TRACE': trace}
    page = re.sub(r'TITLE|EVIDENCE|ROWS|TRACE', lambda match: replacements[match.group()], page)
    outputs = {'chart.svg':svg.encode(), 'overlay.svg':overlay.encode(), 'index.html':page.encode(), 'chart.json':raw}
    out.mkdir()
    for name, content in outputs.items():
        with (out/name).open('xb') as target:
            target.write(content)
    receipt = {'status':'rendered; behavior unverified', 'inputSha256':hashlib.sha256(raw).hexdigest(), 'rendererSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'nodes':len(chart['nodes']), 'edges':len(chart['edges']), 'groups':len(chart.get('groups',[])), 'decorations':len(chart.get('decorations',[])), 'traceOccurrences':len(chart.get('trace',[])),
               'outputs':{name:hashlib.sha256(content).hexdigest() for name,content in outputs.items()}}
    with (out/'receipt.json').open('x') as target:
        target.write(json.dumps(receipt,indent=2)+'\n')
    return out/'index.html'


def reject_constant(value):
    raise ValueError('Nonfinite JSON constant: '+value)


def unique_fields(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: '+key)
        result[key]=value
    return result


def strict_json(source):
    return json.loads(source,parse_constant=reject_constant,object_pairs_hook=unique_fields)


def main():
    parser=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        if not args.input.is_file() or args.input.stat().st_size>LIMIT:
            raise ValueError('Input must be a regular JSON file up to 256 KiB')
        source=args.input.read_bytes()
        if len(source)>LIMIT:
            raise ValueError('Input exceeds 256 KiB')
        print(publish(strict_json(source),args.out,source))
        return 0
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as error:
        print(str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
