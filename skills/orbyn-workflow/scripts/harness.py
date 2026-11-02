#!/usr/bin/env python3
"""Resolve per-repository agent harness settings (read-only; standard library only).

Commands
  resolve --target PATH [--host claude|codex] [--json] [--explain]
  validate FILE
  check [--root DIR]

Precedence, highest first: user instruction (--set), the target's own
.orbyn/harness.json at its Git root, a local Git-ignored file
<workspace>/repo/.harness/<target-slug>.json, then the library defaults in
references/harness-defaults.json. The target file is repository data: it may only
lower cost or tighten, and delegation numbers above the default are clamped. The
local file is the owner's and may raise delegation limits. Neither file can change
a lead tier or a locked security role; only --set can. This tool reads files and
prints results. It never writes settings into a target, never starts a model and
never runs a check that a harness file lists.

Exit status: 0 ok, 1 invalid file or drift, 2 could not run (bad target, bad
--set, unreadable defaults or arguments).
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
DEFAULTS_PATH = SCRIPT.parent.parent / 'references' / 'harness-defaults.json'
MAX_BYTES = 65536
PROVIDERS = ('claude', 'codex')
TIERS = ('lead', 'worker', 'scout')
EFFORTS = ('low', 'medium', 'high')
ROLE_KEYS = ('lead', 'architect', 'reviewer', 'security', 'security_verifier', 'security_engineer', 'engineer',
             'engineer_complex', 'investigator', 'verifier', 'mechanical', 'tiny_edit')
LOCKED_ROLES = ('lead', 'security', 'security_verifier', 'security_engineer')
FILE_KEYS = {'schema_version', 'tiers', 'delegation', 'routing', 'verification', 'notes'}
DEFAULTS_KEYS = {'generated_from', 'agents', 'escalation', 'allowed_models', 'effort_caps', 'claude_minimum_versions',
                 'human_only'}
DELEGATION_RANGES = {'max_children': (0, 8), 'max_depth': (1, 3), 'read_only_children_extra': (0, 8)}
MODEL_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,63}')
SLUG_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')
HUMAN_ONLY_TOKENS = ('astra', 'fable')
ACCELERATED_TOKENS = ('fast', 'priority', 'ultra')
HOST_BINARIES = {'claude': 'claude', 'codex': 'codex'}
RULES = {
    'delegation.max_children': 'Most children one owner may have active at once; 0 means no delegation.',
    'delegation.max_depth': 'Spawn depth below the lead; 1 means children never spawn.',
    'delegation.read_only_children_extra': 'Extra read-only children allowed above max_children; ignored when max_children is 0.',
    'verification.required_checks': 'Checks the repository asks for. Data only: running one still needs ordinary authority.',
}


class Invalid(Exception):
    """A settings file or value breaks the schema (exit 1)."""

    def __init__(self, errors):
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        super().__init__('; '.join(self.errors))


class CannotRun(Exception):
    """The tool could not do its job (exit 2)."""


def is_int(value):
    return type(value) is int


def reject_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f'duplicate key {key!r}')
        seen[key] = value
    return seen


def reject_constant(name):
    raise ValueError(f'unsupported constant {name}')


def parse_json(raw, label):
    try:
        text = raw.decode('utf-8')
        data = json.loads(text, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except RecursionError:
        raise Invalid(f'{label}: nesting is too deep')
    except (UnicodeDecodeError, ValueError) as error:
        raise Invalid(f'{label}: not valid JSON ({error})')
    if not isinstance(data, dict):
        raise Invalid(f'{label}: top level must be an object')
    return data


def read_file(path, label, required=False):
    """Return parsed JSON, or None when the file is absent. Refuse links and large files."""
    path = Path(path)
    for part in (path.parent, path):
        try:
            info = os.lstat(part)
        except FileNotFoundError:
            if required:
                raise CannotRun(f'{label}: file not found: {path}')
            return None
        except NotADirectoryError:
            raise Invalid(f'{label}: {part} is not a directory')
        except OSError as error:
            raise CannotRun(f'{label}: cannot inspect {part}: {error.strerror}')
        if stat.S_ISLNK(info.st_mode):
            raise Invalid(f'{label}: refusing symbolic link {part}')
    if not stat.S_ISREG(info.st_mode):
        raise Invalid(f'{label}: not a regular file')
    if info.st_size > MAX_BYTES:
        raise Invalid(f'{label}: larger than {MAX_BYTES} bytes')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, 'rb') as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as error:
        raise Invalid(f'{label}: cannot read ({error.strerror})')
    if len(raw) > MAX_BYTES:
        raise Invalid(f'{label}: larger than {MAX_BYTES} bytes')
    return parse_json(raw, label)


def is_human_only(model, human_only):
    lowered = model.lower()
    return lowered in {name.lower() for name in human_only} or any(t in lowered for t in HUMAN_ONLY_TOKENS)


def is_accelerated(model):
    return any(t in model.lower() for t in ACCELERATED_TOKENS)


def bad_char(char):
    """Control characters, line separators and lone surrogates have no place in one-line text."""
    code = ord(char)
    return code < 32 or 127 <= code < 160 or 0xD800 <= code <= 0xDFFF or char in '\u2028\u2029'


def model_allowlist(defaults):
    """Models a file may name per provider and tier: the tier's own and every cheaper tier's."""
    return {provider: {tier: {name for lower in TIERS[index:] for name in defaults['allowed_models'][provider][lower]}
                       for index, tier in enumerate(TIERS)} for provider in PROVIDERS}


def expanded_caps(defaults):
    """Effort caps by model name, with every alias and full id of a capped model inheriting its cap."""
    caps = {k.lower(): v for k, v in defaults['effort_caps'].items()}
    for by_tier in defaults['allowed_models'].values():
        for names in by_tier.values():
            if names[0].lower() in caps:
                caps.update({alias.lower(): caps[names[0].lower()] for alias in names[1:]})
    return caps


def allowed_model_errors(allowed, tier_models, human_only):
    """Errors for the registry's allowed_models: each tier lists its own model first, then ids."""
    if not isinstance(allowed, dict) or set(allowed) != set(PROVIDERS):
        return ['allowed_models must list claude and codex']
    errors = []
    for provider in PROVIDERS:
        by_tier = allowed[provider]
        if not isinstance(by_tier, dict) or set(by_tier) != set(TIERS):
            errors.append(f'allowed_models.{provider} must list lead, worker and scout')
            continue
        for tier, names in by_tier.items():
            where = f'allowed_models.{provider}.{tier}'
            if (not isinstance(names, list) or not names or len(set(names)) != len(names)
                    or not all(isinstance(n, str) and MODEL_PATTERN.fullmatch(n) for n in names)):
                errors.append(f'{where} must be a list of distinct plain model names')
            elif names[0] != tier_models[provider][tier]['model']:
                errors.append(f'{where} must start with the tier model {tier_models[provider][tier]["model"]!r}')
            elif any(is_human_only(n, human_only) or is_accelerated(n) for n in names):
                errors.append(f'{where} lists a human-only or accelerated model')
    return errors


def effort_rank(effort):
    return EFFORTS.index(effort)


def over_cap(model, effort, caps):
    cap = caps.get(str(model).lower())
    return cap if cap and effort in EFFORTS and effort_rank(effort) > effort_rank(cap) else None


def raised(flat, base):
    """Keys of a layer that cost more than the default: higher effort or a more capable routing tier."""
    return [key for key, value in flat.items() if key in base and (
        (key.endswith('.effort') and EFFORTS.index(value) > EFFORTS.index(base[key]))
        or (key.startswith('routing.') and TIERS.index(value) < TIERS.index(base[key])))]


def cap_errors(layer, caps, base_tiers):
    """Errors for efforts above a model's cap, judged on the layer's model or the default one."""
    errors = []
    for provider, by_tier in layer.get('tiers', {}).items():
        if not isinstance(by_tier, dict) or provider not in PROVIDERS:
            continue
        for tier, setting in by_tier.items():
            if not isinstance(setting, dict) or tier not in TIERS or 'effort' not in setting:
                continue
            model = setting.get('model') or base_tiers.get(provider, {}).get(tier, {}).get('model')
            cap = over_cap(model, setting['effort'], caps)
            if cap:
                errors.append(f'tiers.{provider}.{tier}.effort: {setting["effort"]!r} is above the {cap} cap for {model}; '
                              'only an explicit user instruction can exceed it')
    return errors


def validate_layer(data, human_only=(), complete=False, allowed=None, is_file=False):
    """Return a list of schema errors for one settings layer.

    A file layer (is_file) also gets the allowlist of models per provider and tier and loses the
    lead tiers and the locked roles, which only the user's --set can change."""
    errors = []
    if not isinstance(data, dict):
        return ['top level must be an object']
    for key in sorted(set(data) - FILE_KEYS - (DEFAULTS_KEYS if complete else set())):
        errors.append(f'unknown key {key!r}')
    if not is_int(data.get('schema_version')) or data.get('schema_version') != 1:
        errors.append('schema_version must be the integer 1')
    if 'tiers' in data:
        tiers = data['tiers']
        if not isinstance(tiers, dict):
            errors.append('tiers must be an object')
        else:
            for provider, by_tier in tiers.items():
                if provider not in PROVIDERS:
                    errors.append(f'tiers: unknown provider {provider!r}')
                    continue
                if not isinstance(by_tier, dict):
                    errors.append(f'tiers.{provider} must be an object')
                    continue
                for tier, setting in by_tier.items():
                    where = f'tiers.{provider}.{tier}'
                    if tier not in TIERS:
                        errors.append(f'{where}: unknown tier (use lead, worker or scout)')
                        continue
                    if not isinstance(setting, dict):
                        errors.append(f'{where} must be an object')
                        continue
                    for key in sorted(set(setting) - {'model', 'effort'}):
                        errors.append(f'{where}: unknown key {key!r}')
                    if is_file and tier == 'lead':
                        errors.append(f'{where}: a file cannot change the lead tier; only the user\'s --set can')
                    if 'model' in setting:
                        model = setting['model']
                        if not isinstance(model, str) or not MODEL_PATTERN.fullmatch(model):
                            errors.append(f'{where}.model must be a plain model name')
                        elif is_accelerated(model) or (human_only and is_human_only(model, human_only)):
                            errors.append(f'{where}.model: {model!r} is human-only or accelerated and cannot be a tier')
                        elif allowed is not None and model not in allowed[provider][tier]:
                            errors.append(f'{where}.model: {model!r} is not in the allowlist for this tier '
                                          f'({", ".join(sorted(allowed[provider][tier]))})')
                    if 'effort' in setting and setting['effort'] not in EFFORTS:
                        errors.append(f'{where}.effort must be one of {", ".join(EFFORTS)}')
                    if complete and set(setting) != {'model', 'effort'}:
                        errors.append(f'{where} needs model and effort')
            if complete:
                for provider in PROVIDERS:
                    for tier in TIERS:
                        if tier not in tiers.get(provider, {}):
                            errors.append(f'tiers.{provider}.{tier} is missing')
    elif complete:
        errors.append('tiers is missing')
    if 'delegation' in data:
        delegation = data['delegation']
        if not isinstance(delegation, dict):
            errors.append('delegation must be an object')
        else:
            for key in sorted(set(delegation) - set(DELEGATION_RANGES)):
                errors.append(f'delegation: unknown key {key!r}')
            for key, (low, high) in DELEGATION_RANGES.items():
                if key in delegation:
                    value = delegation[key]
                    if not is_int(value):
                        errors.append(f'delegation.{key} must be an integer')
                    elif not low <= value <= high:
                        errors.append(f'delegation.{key} must be in {low}..{high}')
            if complete:
                for key in DELEGATION_RANGES:
                    if key not in delegation:
                        errors.append(f'delegation.{key} is missing')
    elif complete:
        errors.append('delegation is missing')
    if 'routing' in data:
        routing = data['routing']
        if not isinstance(routing, dict):
            errors.append('routing must be an object')
        else:
            for role, value in routing.items():
                if role not in ROLE_KEYS:
                    errors.append(f'routing: unknown role {role!r}')
                    continue
                if isinstance(value, dict):
                    pairs = list(value.items())
                    for provider, _ in pairs:
                        if provider not in PROVIDERS:
                            errors.append(f'routing.{role}: unknown provider {provider!r}')
                    pairs = [(p, t) for p, t in pairs if p in PROVIDERS]
                    if complete and {p for p, _ in pairs} != set(PROVIDERS):
                        errors.append(f'routing.{role} needs claude and codex')
                else:
                    pairs = [(None, value)]
                for provider, tier in pairs:
                    where = f'routing.{role}' + (f'.{provider}' if provider else '')
                    if tier not in TIERS:
                        errors.append(f'{where}: unknown tier {tier!r}')
                    elif role in LOCKED_ROLES and tier != 'lead':
                        errors.append(f'{where}: {role} work cannot be routed below the lead tier')
                    elif role in ('architect', 'reviewer', 'engineer_complex') and tier == 'scout':
                        errors.append(f'{where}: a scout never designs, reviews or builds complex changes')
                    elif is_file and role == 'engineer_complex' and provider != 'claude' and tier != 'lead':
                        errors.append(f'{where}: complex Codex engineering stays on the lead tier in a file')
            if complete:
                for role in ROLE_KEYS:
                    if role not in routing:
                        errors.append(f'routing.{role} is missing')
    elif complete:
        errors.append('routing is missing')
    if 'verification' in data:
        verification = data['verification']
        if not isinstance(verification, dict):
            errors.append('verification must be an object')
        else:
            for key in sorted(set(verification) - {'required_checks'}):
                errors.append(f'verification: unknown key {key!r}')
            checks = verification.get('required_checks', [])
            if not isinstance(checks, list) or len(checks) > 32:
                errors.append('verification.required_checks must be a list of at most 32 strings')
            else:
                for index, item in enumerate(checks):
                    if not isinstance(item, str) or not 1 <= len(item) <= 200 or any(bad_char(c) for c in item):
                        errors.append(f'verification.required_checks[{index}] must be one line of 1..200 characters')
    if 'notes' in data:
        notes = data['notes']
        if not isinstance(notes, str) or len(notes) > 2000 or any(bad_char(c) for c in notes):
            errors.append('notes must be one line of at most 2000 characters without control characters')
    return errors


def flatten(layer):
    out = {}
    for provider, by_tier in layer.get('tiers', {}).items():
        for tier, setting in by_tier.items():
            for key, value in setting.items():
                out[f'tiers.{provider}.{tier}.{key}'] = value
    for key, value in layer.get('delegation', {}).items():
        out[f'delegation.{key}'] = value
    for role, value in layer.get('routing', {}).items():
        for provider in PROVIDERS:
            out[f'routing.{role}.{provider}'] = value[provider] if isinstance(value, dict) and provider in value else (
                None if isinstance(value, dict) else value)
    out = {k: v for k, v in out.items() if v is not None}
    if 'verification' in layer:
        out['verification.required_checks'] = list(layer['verification'].get('required_checks', []))
    if 'notes' in layer:
        out['notes'] = layer['notes']
    return out


def load_defaults(path=DEFAULTS_PATH):
    try:
        data = read_file(path, 'library defaults', required=True)
    except Invalid as error:
        raise CannotRun(f'library defaults are unreadable: {error}')
    errors = validate_layer(data, complete=True)
    human = data.get('human_only', {})
    if not isinstance(human, dict) or not all(isinstance(human.get(p), list) for p in PROVIDERS):
        errors.append('human_only must list models per provider')
    if errors:
        raise CannotRun('library defaults are corrupt: ' + '; '.join(errors))
    flat_human = [m for p in PROVIDERS for m in human[p]]
    errors = validate_layer(data, flat_human, complete=True)
    errors.extend(allowed_model_errors(data.get('allowed_models'), data['tiers'], flat_human))
    caps = data.get('effort_caps')
    if not isinstance(caps, dict) or not all(v in EFFORTS for v in caps.values()):
        errors.append('effort_caps must map model names to an effort')
    elif not errors:
        errors.extend(cap_errors(data, expanded_caps(data), {}))
    if errors:
        raise CannotRun('library defaults are corrupt: ' + '; '.join(errors))
    return data


def defaults_from_registry(registry):
    """Build the portable defaults document from docs/agents/models.json."""
    tiers = {provider: {} for provider in PROVIDERS}
    agents = {}
    for name, agent in registry['agents'].items():
        agents[agent['tier']] = name
        for provider in PROVIDERS:
            tiers[provider][agent['tier']] = {'model': agent[provider]['model'], 'effort': agent[provider]['effort']}
    ordered = {provider: {tier: tiers[provider][tier] for tier in TIERS} for provider in PROVIDERS}
    return {
        'schema_version': 1,
        'generated_from': 'docs/agents/models.json by scripts/sync-agent-models.py; do not edit',
        'tiers': ordered,
        'agents': {tier: agents[tier] for tier in TIERS},
        'delegation': dict(registry['delegation']),
        'routing': {role: registry['routing'][role] for role in ROLE_KEYS},
        'escalation': dict(registry['escalation']),
        'allowed_models': {p: {t: list(registry['allowed_models'][p][t]) for t in TIERS} for p in PROVIDERS},
        'effort_caps': dict(registry['effort_caps']),
        'claude_minimum_versions': dict(registry['claude_minimum_versions']),
        'human_only': {provider: [registry['human_only'][provider]['model']] for provider in PROVIDERS},
    }


def render_defaults(defaults):
    return json.dumps(defaults, indent=2) + '\n'


# ---------------------------------------------------------------- location

def git_root(target):
    target = Path(target)
    try:
        start = target.resolve(strict=True)
    except (OSError, RuntimeError):
        raise CannotRun(f'target does not exist: {target}')
    if not start.is_dir():
        start = start.parent
    for candidate in (start, *start.parents):
        if (candidate / '.git').exists():
            return candidate
    raise CannotRun(f'target is not inside a Git checkout: {target}')


def primary_clone(root):
    """The primary clone of a linked worktree, from its Git common directory; root otherwise.

    The link must point back at this worktree, so a copied .git file cannot borrow another clone."""
    marker = root / '.git'
    if marker.is_file():
        try:
            gitdir = (root / marker.read_text().splitlines()[0].split(':', 1)[1].strip()).resolve()
            common = (gitdir / (gitdir / 'commondir').read_text().strip()).resolve()
            if Path((gitdir / 'gitdir').read_text().strip()).resolve() == marker.resolve() and common.name == '.git':
                return common.parent
        except (OSError, IndexError, ValueError):
            pass
    return root


def is_library(path):
    return (path / 'skills' / 'catalog.json').is_file() and (path / 'scripts' / 'sync-agent-models.py').is_file()


def find_workspace(primary, explicit):
    """The outer workspace: the one --workspace names, else the outermost repo/ above the clone that holds this library."""
    if explicit:
        workspace = Path(explicit)
        if not workspace.is_dir():
            raise CannotRun(f'workspace is not a directory: {explicit}')
        return workspace.resolve()
    for parent in reversed(primary.parents):
        if parent.name == 'repo' and is_library(parent.parent):
            return parent.parent
    return None


def target_slug(primary, workspace, explicit):
    """The local file name for a clone inside workspace/repo, or None when it has no safe one.

    Parts join with a double dash and no part may contain one, so two clones never share a slug."""
    if explicit is not None and (not SLUG_PATTERN.fullmatch(explicit) or '..' in explicit):
        raise CannotRun(f'invalid target slug {explicit!r}: use letters, digits, dot, underscore and dash')
    try:
        parts = primary.relative_to(workspace / 'repo').parts
    except ValueError:
        return None
    if explicit is not None:
        return explicit if parts else None
    if not parts or not all(SLUG_PATTERN.fullmatch(p) and not re.search(r'--|\.\.|-$', p) for p in parts):
        return None
    slug = '--'.join(parts)
    return slug if SLUG_PATTERN.fullmatch(slug) else None


def parse_sets(items):
    layer = {'schema_version': 1}
    for item in items:
        path, sep, raw = item.partition('=')
        if not sep or not path:
            raise CannotRun(f'--set needs path=value, got {item!r}')
        try:
            value = json.loads(raw, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
        except (ValueError, RecursionError):
            value = raw
        cursor = layer
        keys = path.split('.')
        for key in keys[:-1]:
            cursor = cursor.setdefault(key, {})
            if not isinstance(cursor, dict):
                raise CannotRun(f'--set conflicts at {path}')
        cursor[keys[-1]] = value
    return layer


# ------------------------------------------------------------------ resolve

def version_tuple(text):
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', text or '')
    return tuple(int(x) for x in match.groups()) if match else None


def probe_version(host):
    """The version of the host CLI that runs this session (CLAUDE_CODE_EXECPATH), else the one on PATH."""
    binary = os.environ.get('CLAUDE_CODE_EXECPATH') if host == 'claude' else None
    if not binary or not os.access(binary, os.X_OK):
        binary = shutil.which(HOST_BINARIES[host])
    if not binary:
        return None, f'{host} CLI not found; version unchecked'
    try:
        result = subprocess.run([binary, '--version'], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None, f'{host} version could not be read'
    found = version_tuple(result.stdout)
    return (found, None) if found else (None, f'{host} version could not be read')


def file_layer(data, label, human, allowed, caps, defaults, defaults_flat, target, notices):
    """Validate one repository file and return its flat values.

    The target file is repository data: tiers and routing may only get cheaper and delegation
    numbers above the default are clamped. The owner's local file may raise them, with a notice."""
    errors = validate_layer(data, human, allowed=allowed, is_file=True) + cap_errors(data, caps, defaults['tiers'])
    flat = flatten(data) if not errors else {}
    if target and not errors:
        errors = [f'{key}: a target file may only lower cost or tighten, not raise the default {defaults_flat[key]!r}'
                  for key in raised(flat, defaults_flat)]
    if errors:
        raise Invalid([f'{label}: {e}' for e in errors])
    for key in DELEGATION_RANGES:
        key = f'delegation.{key}'
        if key in flat and flat[key] > defaults_flat[key]:
            if target:
                notices.append(f'{label} asks for {key} {flat[key]}; clamped to the default {defaults_flat[key]}. '
                               'Only the owner\'s local file or the user can raise it')
                flat[key] = defaults_flat[key]
            else:
                notices.append(f'{label} raises {key} from {defaults_flat[key]} to {flat[key]}: '
                               'a resource limit only; the file authorises no effect and does not change host settings')
    if not target:
        notices.extend(f'{label} raises {key} above the default {defaults_flat[key]!r}: it costs more, authorises no effect'
                       for key in raised(flat, defaults_flat))
    return flat


def resolve(target, hosts, sets=(), workspace=None, slug=None, defaults_path=DEFAULTS_PATH,
            versions=None, probe=True):
    defaults = load_defaults(defaults_path)
    human = [m for p in PROVIDERS for m in defaults['human_only'][p]]
    caps, allowed = expanded_caps(defaults), model_allowlist(defaults)
    root = git_root(target)
    primary = primary_clone(root)
    ws = find_workspace(primary, workspace)
    defaults_flat = flatten(defaults)
    layers = [('library default', 'references/harness-defaults.json', defaults_flat, 'used')]
    notices, warnings = [], []
    local_name = target_slug(primary, ws, slug) if ws is not None else None
    if ws is None:
        layers.append(('local file', 'no workspace found', {}, 'not configured'))
    elif local_name is None:
        layers.append(('local file', 'target is not a plain clone name inside the workspace repo/ folder', {}, 'not configured'))
        notices.append('local per-target file skipped: the target is outside the workspace repo/ folder or its name gives no '
                       'safe slug; pass --slug for a clone inside it')
    else:
        where = f'repo/.harness/{local_name}.json'
        data = read_file(ws / 'repo' / '.harness' / f'{local_name}.json', f'local file {where}')
        flat = None if data is None else file_layer(data, f'local file {where}', human, allowed, caps, defaults,
                                                    defaults_flat, False, notices)
        layers.append(('local file', where, flat or {}, 'absent' if data is None else 'used'))
    label = 'target file .orbyn/harness.json'
    data = read_file(root / '.orbyn' / 'harness.json', label)
    flat = None if data is None else file_layer(data, label, human, allowed, caps, defaults, defaults_flat, True, notices)
    layers.append(('target file', '.orbyn/harness.json', flat or {}, 'absent' if data is None else 'used'))
    user_flat = {}
    if sets:
        data = parse_sets(sets)
        errors = validate_layer(data, ())
        if errors:
            raise CannotRun('--set rejected: ' + '; '.join(errors))
        user_flat = flatten(data)
        layers.append(('user instruction', '--set', user_flat, 'used'))
    else:
        layers.append(('user instruction', '--set', {}, 'none given'))

    chains = {}
    for name, where, flat, status in layers:
        for key, value in flat.items():
            chains.setdefault(key, []).append({'source': f'{name} ({where})', 'layer': name, 'value': value})
    effective = {}
    for key, chain in chains.items():
        winner = chain[-1]
        effective[key] = {'value': winner['value'], 'source': winner['source'],
                          'overridden': [{'source': c['source'], 'value': c['value']} for c in reversed(chain[:-1])]}
    extra_key = 'delegation.read_only_children_extra'
    if 'delegation.max_children' in user_flat and extra_key not in user_flat:
        if not effective[extra_key]['source'].startswith('library default'):
            notices.append('read_only_children_extra from a file is ignored because the user set max_children')
            effective[extra_key] = {'value': defaults_flat[extra_key], 'source': 'library default (file value ignored)',
                                    'overridden': [{'source': effective[extra_key]['source'], 'value': effective[extra_key]['value']}]}
    for host in hosts:
        for tier in TIERS:
            model = effective[f'tiers.{host}.{tier}.model']
            effort = effective[f'tiers.{host}.{tier}.effort']
            if model['source'].startswith('user instruction') and is_human_only(model['value'], human):
                notices.append(f'{host} {tier}: {model["value"]} is human-only; used only because the user selected it explicitly')
            cap = over_cap(model['value'], effort['value'], caps)
            if cap and effort['source'].startswith('user instruction'):
                notices.append(f'{host} {tier}: effort {effort["value"]} is above the {cap} cap for {model["value"]}; '
                               'allowed only because the user asked for it explicitly')
            elif cap:
                raise Invalid(f'{effort["source"]}: tiers.{host}.{tier}.effort {effort["value"]!r} is above the {cap} cap for {model["value"]}')
    children = effective['delegation.max_children']['value']
    extra = effective[extra_key]['value']
    if children == 0 and extra:
        notices.append('read_only_children_extra is ignored because max_children is 0 (no delegation)')
    cap = 0 if children == 0 else children + extra
    if cap > 8:
        cap = 8
        notices.append('max_children plus read_only_children_extra is capped at 8')

    result = {
        'target': str(root), 'slug': local_name, 'workspace': str(ws) if ws else None,
        'layers': [{'name': n, 'where': w, 'status': s} for n, w, _, s in layers],
        'delegation': {k: effective[f'delegation.{k}'] for k in DELEGATION_RANGES},
        'read_only_cap': cap,
        'escalation': defaults['escalation'],
        'verification': {'required_checks': effective.get('verification.required_checks',
                                                          {'value': [], 'source': 'library default (none)', 'overridden': []})},
        'notes': effective.get('notes'),
        'hosts': {}, 'notices': notices, 'warnings': warnings,
        'rules': RULES,
    }
    minimums = {k: version_tuple(v) for k, v in defaults['claude_minimum_versions'].items()}
    for host in hosts:
        tiers = {}
        for tier in TIERS:
            tiers[tier] = {key: effective[f'tiers.{host}.{tier}.{key}'] for key in ('model', 'effort')}
            tiers[tier]['agent'] = defaults['agents'][tier]
        found, note = (versions or {}).get(host), None
        if found is None and probe:
            found, note = probe_version(host)
        if note:
            warnings.append(note)
        routing = {role: effective[f'routing.{role}.{host}'] for role in ROLE_KEYS}
        entry = {'tiers': tiers, 'routing': routing, 'version': '.'.join(map(str, found)) if found else None}
        if host == 'claude' and found:
            for tier, setting in tiers.items():
                need = minimums.get(setting['model']['value'])
                if need and found < need:
                    warnings.append(f'claude {entry["version"]} is below {".".join(map(str, need))}, the minimum for '
                                    f'{setting["model"]["value"]} ({tier} tier); that tier may be unavailable')
        if cap == 0:
            entry['host_settings_not_written'] = {'note': 'no host equivalent for max_children 0; policy only'}
        elif host == 'claude':
            entry['host_settings_not_written'] = {'env': {
                'CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS': str(cap),
                'CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH': str(effective['delegation.max_depth']['value'])}}
        else:
            entry['host_settings_not_written'] = {
                'agents.max_concurrent_threads_per_session': cap,
                'note': 'max_threads is an older name for the same limit; depth is policy only on Codex'}
        result['hosts'][host] = entry
    return result


def render_text(result, explain):
    lines = [f'Harness for {result["target"]}']
    lines.append('Layers, highest first:')
    for layer in reversed(result['layers']):
        lines.append(f'  {layer["name"]:<17}{layer["status"]:<15}{layer["where"]}')
    for host, entry in result['hosts'].items():
        lines.append('')
        lines.append(f'{host}' + (f' (installed {entry["version"]})' if entry['version'] else ''))
        for tier, setting in entry['tiers'].items():
            model, effort = setting['model'], setting['effort']
            lines.append(f'  {tier:<7}{setting["agent"]:<14}{model["value"]} / {effort["value"]}   [{model["source"]}]')
            if explain:
                for field in (model, effort):
                    for old in field['overridden']:
                        lines.append(f'           overridden: {old["value"]} from {old["source"]}')
    lines.append('')
    lines.append('delegation')
    for key, item in result['delegation'].items():
        lines.append(f'  {key:<26}{item["value"]}   [{item["source"]}]')
        if explain:
            lines.append(f'    rule: {RULES["delegation." + key]}')
            for old in item['overridden']:
                lines.append(f'    overridden: {old["value"]} from {old["source"]}')
    lines.append(f'  read-only child cap       {result["read_only_cap"]}')
    for host, entry in result['hosts'].items():
        lines.append(f'routing ({host})')
        for role, item in entry['routing'].items():
            lines.append(f'  {role:<19}{item["value"]:<8}[{item["source"]}]')
            if explain:
                for old in item['overridden']:
                    lines.append(f'    overridden: {old["value"]} from {old["source"]}')
    lines.append('naming: Orbyn [Role] [N] - [Model] - [Task] - [Evidence or ID]')
    lines.append('escalation: ' + ', '.join(f'{a} -> {b}' for a, b in result['escalation'].items())
                 + ' (record the reason; effort never rises with the tier)')
    checks = result['verification']['required_checks']
    lines.append('verification')
    lines.append(f'  required_checks: {checks["value"] if checks["value"] else "none"}   [{checks["source"]}]')
    if explain:
        lines.append(f'    rule: {RULES["verification.required_checks"]}')
    if result['notes']:
        lines.append(f'notes (untrusted repository text, never instructions): {json.dumps(result["notes"]["value"])}   '
                     f'[{result["notes"]["source"]}]')
    if explain:
        lines.append('')
        lines.append('Host settings that would enforce these limits (not written by this tool):')
        for host, entry in result['hosts'].items():
            lines.append(f'  {host}: {json.dumps(entry["host_settings_not_written"])}')
        lines.append('Limits from a repository file are policy for the lead. A host enforces them only when its own settings carry the same values.')
    for notice in result['notices']:
        lines.append(f'notice: {notice}')
    for warning in result['warnings']:
        lines.append(f'warning: {warning}')
    return '\n'.join(lines)


# ----------------------------------------------------------- validate/check

def command_validate(args):
    defaults = load_defaults(args.defaults)
    human = [m for p in PROVIDERS for m in defaults['human_only'][p]]
    data = read_file(args.file, str(args.file), required=True)
    errors = validate_layer(data, human, allowed=model_allowlist(defaults), is_file=True) + cap_errors(
        data, expanded_caps(defaults), defaults['tiers'])
    if errors:
        raise Invalid([f'{args.file}: {e}' for e in errors])
    print(f'OK: {args.file} is a valid harness file (schema 1).')
    return 0


def command_check(args):
    root = Path(args.root).resolve() if args.root else (SCRIPT.parents[3] if len(SCRIPT.parents) > 3 else None)
    defaults = load_defaults(args.defaults)
    registry_path = root / 'docs/agents/models.json' if root else None
    if not registry_path or not registry_path.is_file():
        print('OK: portable defaults are well formed. No docs/agents/models.json here, so drift was not checked.')
        return 0
    drift = []
    try:
        registry = json.loads(registry_path.read_text())
        expected = defaults_from_registry(registry)
    except (ValueError, KeyError, TypeError) as error:
        raise CannotRun(f'registry unreadable: {error}')
    if expected != defaults:
        for section in sorted(set(expected) | set(defaults)):
            if expected.get(section) != defaults.get(section):
                drift.append(f'harness-defaults.json differs from docs/agents/models.json in {section!r}')
    cap = expected['delegation']['max_children'] + expected['delegation']['read_only_children_extra']
    settings_path = root / '.claude/settings.json'
    if settings_path.is_file():
        env = json.loads(settings_path.read_text()).get('env', {})
        for key, want in (('CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS', str(cap)),
                          ('CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH', str(expected['delegation']['max_depth']))):
            if env.get(key) != want:
                drift.append(f'.claude/settings.json env {key} is {env.get(key)!r}, expected {want!r}')
    try:
        import tomllib
    except ImportError:
        print('skipped: the .codex/config.toml and agent definition checks need Python 3.11+ (tomllib); '
              'run this check with a newer python3 before delivery', file=sys.stderr)
        tomllib = None
    config_path = root / '.codex/config.toml'
    if tomllib and config_path.is_file():
        config = tomllib.loads(config_path.read_text()).get('agents', {})
        if config.get('max_concurrent_threads_per_session') != cap:
            drift.append(f'.codex/config.toml agents.max_concurrent_threads_per_session is '
                         f'{config.get("max_concurrent_threads_per_session")!r}, expected {cap}')
        if 'max_threads' in config:
            drift.append('.codex/config.toml still sets max_threads next to max_concurrent_threads_per_session')
    sync_path = root / 'scripts/sync-agent-models.py'
    if tomllib and sync_path.is_file():
        spec = importlib.util.spec_from_file_location('orbyn_sync', sync_path)
        sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sync)
        drift.extend(sync.agent_problems(root, registry))
    if drift:
        for item in drift:
            print(f'drift: {item}', file=sys.stderr)
        print('Run python3 scripts/sync-agent-models.py --write', file=sys.stderr)
        return 1
    print('OK: portable defaults and host limits match docs/agents/models.json' + ('.' if tomllib else ' (TOML checks skipped).'))
    return 0


def command_resolve(args):
    hosts = [args.host] if args.host else list(PROVIDERS)
    versions = None
    if args.host_version:
        if not args.host:
            raise CannotRun('--host-version needs --host')
        found = version_tuple(args.host_version)
        if not found:
            raise CannotRun(f'--host-version is not a version: {args.host_version!r}')
        versions = {args.host: found}
    result = resolve(args.target, hosts, sets=args.set, workspace=args.workspace, slug=args.slug,
                     defaults_path=args.defaults, versions=versions, probe=not args.no_probe)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text(result, args.explain))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    res = sub.add_parser('resolve', help='print effective settings with the source of every value')
    res.add_argument('--target', required=True)
    res.add_argument('--host', choices=PROVIDERS)
    res.add_argument('--json', action='store_true')
    res.add_argument('--explain', action='store_true')
    res.add_argument('--set', action='append', default=[], metavar='PATH=JSON',
                     help="the user's explicit instruction, for example delegation.max_children=1")
    res.add_argument('--workspace', help='outer workspace holding repo/.harness (default: found from the target)')
    res.add_argument('--slug', help='local file name without .json (default: derived from the target)')
    res.add_argument('--host-version', help='installed host version to compare with minimums (needs --host)')
    res.add_argument('--no-probe', action='store_true', help='do not run <host> --version')
    res.add_argument('--defaults', default=DEFAULTS_PATH, help=argparse.SUPPRESS)
    val = sub.add_parser('validate', help='validate one harness file')
    val.add_argument('file')
    val.add_argument('--defaults', default=DEFAULTS_PATH, help=argparse.SUPPRESS)
    chk = sub.add_parser('check', help='report drift between portable defaults, the registry and host limits')
    chk.add_argument('--root', help='library checkout (default: this script\'s checkout)')
    chk.add_argument('--defaults', default=DEFAULTS_PATH, help=argparse.SUPPRESS)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return {'resolve': command_resolve, 'validate': command_validate, 'check': command_check}[args.command](args)
    except Invalid as error:
        for item in error.errors:
            print(f'invalid: {item}', file=sys.stderr)
        return 1
    except CannotRun as error:
        print(f'cannot run: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
