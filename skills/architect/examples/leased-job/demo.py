#!/usr/bin/env python3
"""Run the finite leased-job example, replay its bug, and render an offline preview."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import signal
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OWNER = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(command, folder, label, expected=(0,), cwd=None):
    record = {'command': command, 'expected_exit': list(expected), 'cwd': str(cwd or Path.cwd())}
    child = None
    try:
        with (folder/(label+'.stdout.txt')).open('w') as stdout, (folder/(label+'.stderr.txt')).open('w') as stderr:
            child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True, cwd=cwd)
            try:
                child.wait(timeout=110)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                child.send_signal(signal.SIGTERM)
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=5)
                raise
        record['exit'] = child.returncode
        if child.returncode not in expected:
            raise ValueError(f'{label} failed: exit {child.returncode}; inspect retained logs in {folder}')
    except BaseException as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        (folder/(label+'.command.json')).write_text(json.dumps(record, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['node', 'java', 'tlc', 'pele', 'out']:
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    out = Path(args.out).absolute()
    out.mkdir()  # exclusive; earlier output is never reused
    commands = out/'commands'; commands.mkdir()
    receipt = {'status': 'incomplete', 'output': str(out)}
    try:
        tools = [item for key in ['node', 'java', 'tlc'] for item in ['--'+key, str(Path(getattr(args, key)).resolve(strict=True))]]
        adapter = OWNER/'scripts/check-statechart.py'
        execute([sys.executable, str(adapter), 'doctor', *tools], commands, 'doctor')
        for variant in ['broken', 'fixed']:
            execute([sys.executable, str(adapter), 'check', str(HERE/'LeasedJob.tla'), '--config', str(HERE/(variant+'.cfg')), '--view', str(HERE/'view.mjs'), '--out', str(out/variant), '--timeout', '90', *tools], commands, variant, (1,) if variant=='broken' else (0,))
        broken = (out/'broken/report.md').read_text(); fixed = (out/'fixed/report.md').read_text()
        for rule in ['FreshResult', 'PublishedFresh']:
            if rule+' breaks' not in broken: raise ValueError('Expected broken '+rule+' evidence missing')
        if 'breaks' in fixed or 'Rules not checked' in fixed: raise ValueError('Fixed model has a violation or unchecked rule')
        for rule in ['TypeOK', 'FreshResult', 'PublishedFresh', 'CancelledHasNoResult', 'NoDeadlock', 'EventuallyTerminal']:
            if rule not in fixed: raise ValueError('Missing fixed check '+rule)
        # Compiler can omit extra raw traces when every bug is drawn. Obtain an
        # explicit single-property plain-TLC trace rather than inventing that file.
        published_cfg = out/'published-only.cfg'
        published_cfg.write_text('CONSTANT Broken = TRUE\nSPECIFICATION Spec\nINVARIANT PublishedFresh\n')
        shutil.copyfile(HERE/'LeasedJob.tla', out/'LeasedJob.tla')
        execute([str(Path(args.java).resolve()), '-cp', str(Path(args.tlc).resolve()), 'tlc2.TLC', '-workers', '1', '-fp', '0', '-lncheck', 'final', '-metadir', str(out/'published-meta'), '-config', published_cfg.name, 'LeasedJob.tla'], commands, 'plain-published', (12,), cwd=out)
        for name, trace in [('fresh', out/'broken/tlc.out'), ('published', commands/'plain-published.stdout.txt')]:
            execute([args.node, str(HERE/'replay.mjs'), str(trace)], commands, 'replay-'+name)
        replay = json.loads((commands/'replay-published.stdout.txt').read_text())
        (out/'replay.json').write_text(json.dumps(replay, indent=2)+'\n')
        story = ['stateDiagram-v2', '  direction LR', '  [*] --> s0', '  s0: Ready · epoch 0']
        for row in replay['events']:
            i = row['step']; state = row['state']
            label = f"{state['phase']} · epoch {state['generation']}"
            if state['result']: label += f" · result {state['result']['generation']}"
            if state['published']: label += ' · published'
            story += [f'  s{i}: {i}. {label}', f'  s{i-1} --> s{i}: {row["action"]}']
        story += ['  classDef breaks fill:#ffe8e8,stroke:#c82f3b,color:#8b1720', '  class s4,s5 breaks']
        (out/'failure-path.mmd').write_text('\n'.join(story)+'\n')
        for name, model in [('failure-path', out/'failure-path.mmd'), ('broken-graph', out/'broken/chart.mmd'), ('fixed-graph', out/'fixed/chart.mmd')]:
            execute([args.node, str(OWNER/'scripts/render-statechart.mjs'), '--input', str(model), '--output', str(out/(name+'.svg')), '--pele', str(Path(args.pele).resolve(strict=True))], commands, 'render-'+name)
        steps = ''.join(f'<li><strong>{html.escape(row["action"])}</strong> — {html.escape(str(row["state"]))}</li>' for row in replay['events'])
        # Rendered artifacts and detailed reports remain local; no remote assets.
        page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lease-fenced job · checked example</title>
<style>body{font:16px/1.6 system-ui;color:#18312e;background:#f3f6f3;margin:0}main{max-width:1100px;margin:auto;padding:56px 24px}h1{font-size:clamp(34px,5vw,58px);line-height:1.08;max-width:850px}h2{margin-top:40px}small,.muted{color:#516962}.tag{display:inline-block;border:1px solid #b7cbc0;border-radius:20px;padding:4px 12px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}.card,details,figure{background:white;border:1px solid #d2e0d7;border-radius:16px;padding:22px;margin:20px 0}figure{overflow:auto}img{max-width:100%;min-width:600px}li{margin:10px 0;overflow-wrap:anywhere}pre{overflow:auto;white-space:pre-wrap;font-size:13px}details figure img{max-width:none;width:auto;min-width:100%}a{color:#17664a}summary{cursor:pointer;font-weight:650}strong.bad{color:#a32737}.good{color:#17664a}</style>
<main><span class="tag">Synthetic · TLC checked · real public-method replay</span><h1>Two workers.<br>One stale result.</h1><p class="muted">A lease expires. Another worker takes over. The old completion arrives late. The generation fence decides whether it can commit.</p>
<div class="cards"><section class="card"><strong class="bad">Broken guard</strong><p>Worker 1 commits epoch 1 into a job already leased at epoch 2. The stale result can then be published.</p></section><section class="card"><strong class="good">Fixed boundary</strong><p>The old delivery is consumed and rejected. Worker 2 remains the owner, commits epoch 2, and publishes once even when delivery repeats.</p></section><section class="card"><strong>Cancellation has a boundary</strong><p>Before commit: no result or publish. After commit: cancellation is too late and cannot undo the result.</p></section></div>
<h2>The failure TLC found</h2><p>Five steps to a stale publication. This path is derived from the actual counterexample and replayed against the broken implementation; it is not an unchecked overview.</p><figure><img src="failure-path.svg" alt="Claim epoch 1, expire, claim epoch 2, stale completion commits, publish stale result"></figure>
<h2>Four separate evidence results</h2><ul><li><strong>Model:</strong> broken invariants fail; fixed bounded model checks all six rules.</li><li><strong>Projection:</strong> checked compiler Mermaid and rendered SVG; any correlated-region fallback is recorded below.</li><li><strong>Correspondence:</strong> explicit action-to-method mapping and source digests; no automatic proof that all code implements the model.</li><li><strong>Replay:</strong> both bug traces reproduce through public methods. Fixed stale completion is rejected without losing the current lease; duplicate publish and pre/postcommit cancellation assertions pass.</li></ul>
<details><summary>Full corrected generated graph</summary><p><a href="fixed-graph.svg" target="_blank" rel="noopener">Open corrected SVG at full size</a></p><figure><img src="fixed-graph.svg" alt="Full fixed bounded model projection"></figure></details><details><summary>Full broken generated graph</summary><p><a href="broken-graph.svg" target="_blank" rel="noopener">Open broken SVG at full size</a></p><figure><img src="broken-graph.svg" alt="Full broken bounded model projection with violation markings"></figure></details>
<details><summary>Fixed model report</summary><pre>FIXED_REPORT</pre></details><details><summary>Broken model report and numbered traces</summary><pre>BROKEN_REPORT</pre></details><details><summary>Actual replay states</summary><ol>STEPS</ol></details>
<h2>What this demonstrates</h2><p>One job, two workers, at most two lease generations, serialized public methods and an in-memory idempotency ledger. Expiry can occur only before the final bounded generation. Liveness assumes weak fairness of completion/cancellation/publish progress. No claim of distributed database, external publication, crash durability, production scheduling or unbounded retry correctness.</p><p><a href="receipt.json">Run/source identities</a> · <a href="replay.json">Replay observations</a> · <a href="failure-path.mmd">Failure-path Mermaid</a> · <a href="fixed/chart.mmd">Fixed Mermaid</a> · <a href="broken/chart.mmd">Broken Mermaid</a></p></main></html>'''
        (out/'index.html').write_text(page.replace('FIXED_REPORT', html.escape(fixed)).replace('BROKEN_REPORT', html.escape(broken)).replace('STEPS', steps))
        receipt.update(status='completed', model='fixed six rules hold within bounds; broken FreshResult/PublishedFresh fail', projection='compiler checked and renderer executed; layout inspection is separate', source_correspondence='explicit mapping, not general code conformance', replay='both counterexamples and fixed rejection/control assertions passed', tools=json.loads((commands/'doctor.stdout.txt').read_text()), renderer={'path': str(Path(args.pele).resolve()), 'sha256': sha(args.pele)}, sources={p.name:sha(p) for p in HERE.iterdir() if p.is_file()}, outputs={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        print(out/'index.html')
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        receipt['error'] = str(error); print(str(error), file=sys.stderr)
        return 2
    finally:
        (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    sys.exit(main())
