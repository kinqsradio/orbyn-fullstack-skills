#!/usr/bin/env python3
"""Check a threat-model JSON file against the artifact contract. Reads files only.

Usage:
  python3 check_threat_model.py MODEL.json [--root TARGET] [--baseline PREVIOUS.json]
                                   [--ledger LEDGER.json --findings FINDINGS.json]

Without --root it checks structure, ids, references and evidence rules. With --root
every path:start-end locator must name a regular file inside TARGET and a line range
that exists, and an optional excerpt must appear in the cited lines. An execution
locator may instead name a file in the model's own folder. A secret-looking file is
never opened: its range goes unchecked and an excerpt on it is a fault whatever it says.
--baseline refuses a threat id the previous revision had and this one dropped. --ledger
and --findings refuse a finished tm: unit whose id did not reach a finding fingerprint.
Nothing in the target is executed. Exits 1 and names each fault; exits 2 on unreadable
or wrongly shaped input, naming the fault there too.
"""
import argparse
import json
from pathlib import Path
import re
import sys

KINDS = {'implementation', 'configuration', 'documentation', 'caller_claim', 'proposed_design', 'execution'}
GROUNDED = {'implementation', 'configuration'}
BASES = {'observed_weakness', 'design_hypothesis', 'protected'}
HANDOFFS = {'audit', 'remediation', 'decision', 'none'}
CONFIDENCE = {'high', 'medium', 'low'}
RATING_KEYS = {'severity', 'rating', 'score', 'likelihood', 'cvss'}
LOCATOR = re.compile(r'(?P<path>[^:\s][^:]*):(?P<start>[1-9][0-9]{0,8})(?:-(?P<end>[1-9][0-9]{0,8}))?')
SESSION = re.compile(r'session:\S.*')
IDS = {'evidence': 'E', 'assets': 'A', 'actors': 'P', 'boundaries': 'B', 'flows': 'F',
       'controls': 'C', 'threats': 'T', 'verification': 'V', 'gaps': 'G'}
GUIDE = Path(__file__).resolve().parent.parent/'references/threat-boundaries.md'
THREAT_TEXT = ('title', 'objective', 'actor', 'boundary', 'counterevidence', 'decisive_observation',
               'confidence_rationale', 'proposed_outcome')
REQUIRED = ('threats', 'evidence', 'verification')
FINISHED = {'covered', 'candidate'}
SCALARS = {'kind', 'locator', 'excerpt', 'basis', 'objective', 'actor', 'boundary', 'guide', 'status',
           'threat_ref', 'limits', 'confidence', 'to'}
REF_LISTS = {'evidence_refs', 'existing_controls', 'gap_refs', 'verification_refs'}
NESTED = ('handoff', 'resolution', 'retired')
SURROGATE = re.compile('[\ud800-\udfff]')
SECRET_FILE = re.compile(r'\.env(?!\.(?:example|sample|template)$)(?:\..*)?|.*\.(?:pem|key|p12|pfx|jks|keystore)'
                         r'|id_(?:rsa|dsa|ecdsa|ed25519)|(?:credentials|secrets?)(?:\.(?:json|ya?ml|toml|ini|txt|env))?'
                         r'|\.(?:netrc|npmrc|pypirc|pgpass|git-credentials|ssh|aws|gnupg)', re.I)


def load(path):
    def pairs(items):
        keys = [key for key, _ in items]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate object key')
        return dict(items)

    def constant(name):
        raise ValueError(f'non-finite number {name}')
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except RecursionError:
        raise ValueError('nesting is too deep') from None


def field_faults(record, where):
    faults = []
    for key, value in record.items():
        if key in SCALARS and value is not None and not isinstance(value, str):
            faults.append(f'{where}.{key} must be a string')
        elif key in SCALARS and value is not None and '\0' in value:
            faults.append(f'{where}.{key} holds a NUL')
        elif key in REF_LISTS and not (isinstance(value, list) and all(isinstance(item, str) for item in value)):
            faults.append(f'{where}.{key} must be a list of strings')
        elif key in NESTED and isinstance(value, dict):
            faults += field_faults(value, f'{where}.{key}')
    return faults


def shape(model):
    """Faults that would stop the rules from reading the model at all; the rules trust this pass."""
    try:
        return shape_faults(model)
    except RecursionError:
        return ['nesting is too deep']


def shape_faults(model):
    if not isinstance(model, dict):
        return ['top level must be an object']
    faults = [f'{key!r} holds a lone surrogate' for key, value in model.items()
              if SURROGATE.search(json.dumps({key: value}, ensure_ascii=False))]
    for collection in IDS:
        records = model.get(collection, [])
        if not isinstance(records, list):
            faults.append(f'{collection} must be a list')
            continue
        for number, record in enumerate(records):
            where = f'{collection}[{number}]'
            if not isinstance(record, dict):
                faults.append(f'{where} must be an object')
            elif not isinstance(record.get('id'), str):
                faults.append(f'{where}.id must be a string')
            else:
                faults += field_faults(record, where)
    return faults


def read_model(path):
    """The model at path, or a ValueError naming every shape fault."""
    model = load(path)
    faults = shape(model)
    if faults:
        raise ValueError('\n'.join(faults))
    return model


def guide_rows(path=GUIDE):
    """The first-column names of the boundary guide table, which every model boundary must use."""
    return guide_rows_from(path.read_text(encoding='utf-8'))


def guide_rows_from(markdown):
    rows = []
    for line in markdown.splitlines():
        cells = [cell.strip() for cell in line.split('|')]
        if len(cells) > 2 and cells[0] == '' and cells[1] and not set(cells[1]) <= {'-', ' '} and cells[1] != 'Boundary':
            rows.append(cells[1])
    return rows


def text(value):
    return isinstance(value, str) and bool(value.strip())


def secret_looking(path):
    return any(SECRET_FILE.fullmatch(part) for part in Path(path).parts)


def parse_locator(locator, errors, label):
    """(path, start, end) for a contained, ordered locator; None after naming the fault."""
    match = LOCATOR.fullmatch(locator)
    if not match:
        errors.append(f'{label}: locator {locator!r} is not path:start-end')
        return None
    path, start = match['path'], int(match['start'])
    end = int(match['end'] or start)
    if path.startswith(('/', '\\', '~')) or '..' in path.replace('\\', '/').split('/'):
        errors.append(f'{label}: locator path must stay inside the target: {locator}')
        return None
    if start > end:
        errors.append(f'{label}: reversed line range in {locator}')
        return None
    return path, start, end


def check_locator(root, locator, excerpt, errors, label, run=None):
    parsed = parse_locator(locator, errors, label)
    if not parsed:
        return
    path, start, end = parsed
    refused = f'{label}: {path} looks like a secret file and is never opened; remove the excerpt'
    if excerpt is not None and secret_looking(path):
        errors.append(refused)
        return
    base = run if run is not None and (run/path).exists() else root
    try:
        resolved = (base/path).resolve(strict=True)
        if not resolved.is_relative_to(base) or not resolved.is_file():
            errors.append(f'{label}: {path} is not a regular file inside the target')
            return
        if secret_looking(path) or secret_looking(resolved.relative_to(base)):
            if excerpt is not None:
                errors.append(refused)
            return
        lines = resolved.read_text(encoding='utf-8', errors='replace').splitlines()
    except (OSError, ValueError):
        errors.append(f'{label}: no readable file at {path}')
        return
    if end > len(lines):
        errors.append(f'{label}: lines {start}-{end} outside {path} ({len(lines)} lines)')
        return
    if excerpt is not None:
        seen = re.sub(r'\s+', ' ', ' '.join(lines[start - 1:end]))
        if re.sub(r'\s+', ' ', excerpt).strip() not in seen:
            errors.append(f'{label}: excerpt not found in {locator}')


def check(model, root=None, guide=None, run=None):
    errors = shape(model)
    if errors:
        return errors
    guide = guide_rows() if guide is None else guide
    if model.get('schema') != 'orbyn-threat-model/1':
        errors.append('schema must be "orbyn-threat-model/1"')
    for key in ('model_id', 'revision', 'decision'):
        if not text(model.get(key)):
            errors.append(f'{key} is required')
    if model.get('status') not in ('complete', 'partial'):
        errors.append('status must be complete or partial')
    if model.get('depth') not in ('quick', 'deep'):
        errors.append('depth must be quick or deep')
    target = model.get('target')
    if not isinstance(target, dict) or not text(target.get('name')):
        errors.append('target.name is required')
    architectures = model.get('architectures')
    if not isinstance(architectures, dict) or not text(architectures.get('primary')):
        errors.append('architectures.primary is required')
    for collection in REQUIRED:
        if collection not in model:
            errors.append(f'{collection} is required')
        elif model.get('status') == 'complete' and not model[collection]:
            errors.append(f'a complete model needs {collection}')
    ids = {}
    for collection, prefix in IDS.items():
        for record in model.get(collection, []):
            record_id = record['id']
            if not re.fullmatch(prefix + '[1-9][0-9]*', record_id):
                errors.append(f'{collection}: id must look like {prefix}1, got {record_id!r}')
            elif record_id in ids:
                errors.append(f'duplicate id {record_id}')
            else:
                ids[record_id] = collection
    by_id = {record['id']: record for collection in IDS for record in model.get(collection, [])}

    def ref(value, collection, where):
        if ids.get(value) != collection:
            errors.append(f'{where}: {value!r} is not a {collection} id')

    for record in model.get('evidence', []):
        where = record.get('id', 'evidence')
        kind = record.get('kind')
        if kind not in KINDS:
            errors.append(f'{where}: kind {kind!r} is not allowed')
        if not text(record.get('summary')):
            errors.append(f'{where}: summary is required')
        locator = record.get('locator')
        if not text(locator):
            errors.append(f'{where}: locator is required')
        elif kind == 'caller_claim':
            if not SESSION.fullmatch(locator):
                errors.append(f'{where}: a caller claim uses session:<label>')
        elif root is not None:
            check_locator(root, locator, record.get('excerpt'), errors, where, run if kind == 'execution' else None)
        else:
            parse_locator(locator, errors, where)
    for record in model.get('controls', []):
        for item in record.get('evidence_refs', []):
            ref(item, 'evidence', record.get('id', 'control'))
    for record in model.get('actors', []):
        if not text(record.get('capability')):
            errors.append(f'{record["id"]}: capability is required')
    for record in model.get('boundaries', []):
        if not text(record.get('name')):
            errors.append(f'{record.get("id", "boundary")}: name is required')
        if record.get('guide') not in guide:
            errors.append(f'{record.get("id", "boundary")}: guide {record.get("guide")!r} is not a row of threat-boundaries.md')
    for record in model.get('threats', []):
        where = record.get('id', 'threat')
        basis = record.get('basis')
        if basis not in BASES:
            errors.append(f'{where}: basis {basis!r} is not allowed')
        for key in THREAT_TEXT:
            if not text(record.get(key)):
                errors.append(f'{where}: {key} is required')
        if record.get('confidence') not in CONFIDENCE:
            errors.append(f'{where}: confidence must be high, medium or low')
        if not isinstance(record.get('prerequisites'), list) or not record['prerequisites']:
            errors.append(f'{where}: prerequisites are required')
        ref(record.get('objective'), 'assets', f'{where}.objective')
        ref(record.get('actor'), 'actors', f'{where}.actor')
        ref(record.get('boundary'), 'boundaries', f'{where}.boundary')
        kinds = set()
        for item in record.get('evidence_refs', []):
            ref(item, 'evidence', f'{where}.evidence_refs')
            kinds.add(by_id.get(item, {}).get('kind'))
        if basis == 'observed_weakness' and not kinds & GROUNDED:
            errors.append(f'{where}: an observed weakness needs implementation or configuration evidence')
        if not record.get('evidence_refs'):
            errors.append(f'{where}: evidence_refs are required')
        controls = record.get('existing_controls', [])
        for item in controls:
            ref(item, 'controls', f'{where}.existing_controls')
        if basis == 'protected' and not any(by_id.get(item, {}).get('evidence_refs') for item in controls):
            errors.append(f'{where}: a protected record names its control and that control cites evidence')
        for item in record.get('gap_refs', []):
            ref(item, 'gaps', f'{where}.gap_refs')
        checks = record.get('verification_refs', [])
        if basis != 'protected' and not checks:
            errors.append(f'{where}: a threat that is not protected needs a verification')
        for item in checks:
            ref(item, 'verification', f'{where}.verification_refs')
            if ids.get(item) == 'verification' and by_id[item].get('threat_ref') != where:
                errors.append(f'{where}: {item} checks {by_id[item].get("threat_ref")!r}, not this threat')
        handoff = record.get('handoff')
        if not isinstance(handoff, dict) or handoff.get('to') not in HANDOFFS:
            errors.append(f'{where}: handoff.to must be one of {sorted(HANDOFFS)}')
        elif basis == 'protected' and handoff['to'] != 'none':
            errors.append(f'{where}: a protected record hands off to none')
        elif basis == 'observed_weakness' and handoff['to'] == 'none':
            errors.append(f'{where}: an observed weakness needs a routed handoff')
        elif handoff['to'] != 'none' and handoff.get('ref') != f'tm:{where}':
            errors.append(f'{where}: handoff.ref must be tm:{where}')
        resolution = record.get('resolution')
        if resolution is not None:
            if not isinstance(resolution, dict) or resolution.get('status') not in ('resolved', 'partly_resolved') \
                    or not text(resolution.get('note')):
                errors.append(f'{where}: resolution needs status "resolved" or "partly_resolved" and a note')
            elif resolution['status'] == 'partly_resolved' and not text(resolution.get('remaining')):
                errors.append(f'{where}: a partly resolved threat says what remains open')
            if isinstance(resolution, dict):
                proof = set()
                for item in resolution.get('evidence_refs', []):
                    ref(item, 'evidence', f'{where}.resolution')
                    proof.add(by_id.get(item, {}).get('kind'))
                if not proof & GROUNDED:
                    errors.append(f'{where}: a resolution needs implementation or configuration evidence')
        if 'retired' in record:
            retired = record['retired']
            if not isinstance(retired, dict) or not text(retired.get('reason')) or not retired.get('evidence_refs'):
                errors.append(f'{where}: retired needs a reason and evidence_refs')
            else:
                for item in retired['evidence_refs']:
                    ref(item, 'evidence', f'{where}.retired')
        if RATING_KEYS & {key.lower() for key in record} and not model.get('rubric'):
            errors.append(f'{where}: no rating without a rubric the person supplied')
    for record in model.get('verification', []):
        where = record.get('id', 'verification')
        if record.get('status') != 'not_run':
            errors.append(f'{where}: status must be not_run; this mode never runs the target')
        threat = record.get('threat_ref')
        ref(threat, 'threats', f'{where}.threat_ref')
        if ids.get(threat) == 'threats' and where not in by_id[threat].get('verification_refs', []):
            errors.append(f'{where}: {threat} does not cite this verification')
        for key in ('plan', 'pass', 'fail', 'inconclusive'):
            if not text(record.get(key)):
                errors.append(f'{where}: {key} is required')
        outcomes = [' '.join(str(record.get(key)).split()).casefold() for key in ('pass', 'fail', 'inconclusive')]
        if len(set(outcomes)) < 3:
            errors.append(f'{where}: pass, fail and inconclusive must each say something different')
    for record in model.get('gaps', []):
        where = record.get('id', 'gap')
        for key in ('text', 'smallest_observation'):
            if not text(record.get(key)):
                errors.append(f'{where}: {key} is required')
        if 'limits' in record:
            ref(record['limits'], 'boundaries', f'{where}.limits')
    if not isinstance(model.get('limitations'), list) or not model['limitations']:
        errors.append('limitations must say what this run did not do')
    return errors


def unseeded(threat):
    """Why a checked threat gets no coverage unit; None while it is still open for investigation."""
    if 'retired' in threat:
        return 'retired'
    if threat['basis'] == 'protected':
        return 'protected'
    if (threat.get('resolution') or {}).get('status') == 'resolved':
        return 'resolved'
    return {'decision': 'decision', 'none': 'no handoff'}.get(threat['handoff']['to'])


def check_baseline(model, baseline):
    """Faults where a new revision did not carry its parent forward."""
    errors = []
    if model.get('model_id') != baseline.get('model_id'):
        errors.append('model_id differs from the baseline')
    if model.get('parent_revision') != baseline.get('revision'):
        errors.append(f'parent_revision must be the baseline revision {baseline.get("revision")!r}')
    kept = {threat['id'] for threat in model.get('threats', [])}
    for threat in baseline.get('threats', []):
        if threat['id'] not in kept:
            errors.append(f'{threat["id"]}: dropped since the baseline; keep it and mark it retired')
    return errors


def objects(value, label):
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f'{label} must be a list of objects')
    return value


def check_ledger(model, ledger, findings):
    """Faults where a threat id did not survive from the checked model into the findings."""
    errors = []
    threats = {threat['id']: threat for threat in model['threats']}
    recorded = [item.get('fingerprint') for item in findings]
    seen = set()
    for unit in ledger:
        identity = unit.get('attack_class')
        if not isinstance(identity, str) or not identity.startswith('tm:'):
            continue
        seen.add(identity)
        if identity[3:] not in threats:
            errors.append(f'{identity}: no such threat in the model')
        if unit.get('status') not in FINISHED:
            continue
        family = [item for item in recorded if isinstance(item, str) and (item == identity or item.startswith(identity + '/'))]
        if not family:
            errors.append(f'{identity}: finished, but no finding fingerprint carries this id')
        named = unit.get('result_fingerprints')
        for item in named if isinstance(named, list) else []:
            if item not in family:
                errors.append(f'{identity}: fingerprint {item!r} has no finding under this id')
    for identity, threat in threats.items():
        if unseeded(threat) is None and f'tm:{identity}' not in seen:
            errors.append(f'tm:{identity}: open threat has no coverage unit')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('model', type=Path)
    parser.add_argument('--root', type=Path, help='target checkout, to verify locators and excerpts')
    parser.add_argument('--baseline', type=Path, help='previous revision of this model; no threat id may be dropped')
    parser.add_argument('--ledger', type=Path, help='coverage ledger to reconcile; needs --findings')
    parser.add_argument('--findings', type=Path, help='findings to reconcile; needs --ledger')
    args = parser.parse_args(argv)
    if bool(args.ledger) != bool(args.findings):
        parser.error('--ledger and --findings go together')
    try:
        model = read_model(args.model)
        root = args.root.resolve(strict=True) if args.root else None
        baseline = read_model(args.baseline) if args.baseline else None
        ledger = objects(load(args.ledger), 'the ledger') if args.ledger else None
        findings = objects(load(args.findings), 'the findings') if args.findings else None
        run = args.model.resolve(strict=True).parent
    except (OSError, ValueError) as error:
        print(f'cannot read input: {error}', file=sys.stderr)
        return 2
    errors = check(model, root, run=run)
    if baseline is not None:
        errors += check_baseline(model, baseline)
    if ledger is not None and not errors:
        errors = check_ledger(model, ledger, findings)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'OK: {args.model.name} meets the contract' + (' and its locators resolve' if root else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
