"""Strict portable record validation; no external services or dependencies."""
from datetime import datetime, timezone, timedelta
import json
import re
import uuid

VERSION = 1
# Leave one signed SQLite integer for the terminal forgetting revision.
MAX_REVISION = (1 << 63) - 2
CATEGORIES = ('preference', 'project-fact', 'decision', 'convention', 'workflow',
              'failure-pattern', 'solution-pattern', 'constraint', 'learning')
DOMAINS = ('architecture', 'backend', 'frontend', 'ui', 'ux', 'accessibility',
           'data', 'security', 'testing', 'performance', 'platform', 'operations',
           'delivery', 'developer-experience', 'technical-strategy')
STATUSES = ('proposed', 'active', 'conflicted', 'stale', 'superseded', 'archived')
LEVELS = ('user-stated', 'observed', 'reproduced', 'validated')
TAG = re.compile(r'(tech|topic|concern|platform|module):[a-z0-9]+(?:-[a-z0-9]+)*')
ID = re.compile(r'[a-z][a-z0-9_-]{0,79}')
ALIASES = {'tech:postgres': 'tech:postgresql', 'tech:js': 'tech:javascript',
           'tech:ts': 'tech:typescript'}
EDITABLE = {'title', 'statement', 'category', 'domains', 'tags', 'status',
            'evidence_level', 'sensitivity', 'applicability', 'evidence',
            'related_skills', 'relations', 'review_after', 'expires_at'}
SYSTEM = {'schema_version', 'id', 'revision', 'scope', 'created_at', 'updated_at'}


class Error(ValueError):
    """Expected validation, authorization or state conflict."""


def require(condition, message):
    if not condition:
        raise Error(message)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def timestamp(value):
    require(isinstance(value, str) and len(value) <= 40, 'Invalid UTC timestamp')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise Error('Invalid UTC timestamp') from exc
    require(result.utcoffset() == timedelta(0), 'Timestamp must include UTC offset')
    return result


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def decode(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Error('Non-finite JSON value')))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Error('Invalid JSON: ' + str(exc)) from exc


def text(value, label, maximum, empty=False):
    require(isinstance(value, str) and (empty or bool(value.strip())), f'{label} must be text')
    require(len(value) <= maximum and '\x00' not in value, f'{label} too long or contains NUL')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise Error(f'{label} is not valid UTF-8') from exc
    return value


def strings(value, label, maximum=12):
    require(isinstance(value, list) and len(value) <= maximum, f'Invalid {label} list')
    for item in value:
        text(item, label, 128)
    require(len(value) == len(set(value)), f'Duplicate {label}')
    return value


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value), 'Invalid identifier')
    return value


def operation_identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', value),
            'Operation ID must be 1-80 lowercase letters, digits, underscores or hyphens')
    return value


def tags(values, aliases=None):
    strings(values, 'tags')
    result = []
    for value in values:
        value = value.strip().lower()
        require(len(value) <= 64 and TAG.fullmatch(value), 'Invalid namespaced tag')
        value = (ALIASES if aliases is None else aliases).get(value, value)
        if value not in result:
            result.append(value)
    return sorted(result)


def validate(record, skills, aliases=None):
    require(isinstance(record, dict) and set(record) == EDITABLE | SYSTEM, 'Unknown or missing record fields')
    require(type(record['schema_version']) is int and record['schema_version'] == VERSION, 'Unsupported schema')
    identifier(record['id'])
    require(type(record['revision']) is int and 0 < record['revision'] <= MAX_REVISION, 'Invalid or exhausted revision')
    scope = record['scope']
    require(isinstance(scope, dict) and set(scope) == {'kind', 'owner_id'}, 'Invalid scope')
    require(scope['kind'] in ('personal', 'project', 'reusable'), 'Unsupported local scope')
    identifier(scope['owner_id'])
    text(record['title'], 'title', 200)
    text(record['statement'], 'statement', 8000)
    require(record['category'] in CATEGORIES, 'Unknown category')
    domains = strings(record['domains'], 'domains', len(DOMAINS))
    require(bool(domains) and set(domains) <= set(DOMAINS), 'Unknown or empty domains')
    record['tags'] = tags(record['tags'], aliases)
    require(record['status'] in STATUSES, 'Unknown status')
    require(record['evidence_level'] in LEVELS, 'Unknown evidence level')
    require(record['sensitivity'] in ('public', 'internal', 'restricted'), 'Unknown sensitivity')
    applicability = record['applicability']
    require(isinstance(applicability, dict) and set(applicability) <=
            {'modules', 'platforms', 'versions', 'branches'}, 'Invalid applicability')
    for key, values in applicability.items():
        strings(values, key)
    require(set(strings(record['related_skills'], 'related_skills')) <= set(skills), 'Unknown skill owner')
    evidence = record['evidence']
    require(isinstance(evidence, list) and len(evidence) <= 12, 'Invalid evidence')
    for item in evidence:
        require(isinstance(item, dict) and set(item) == {'kind', 'ref', 'revision'}, 'Invalid evidence fields')
        require(item['kind'] in ('user', 'test', 'source', 'observation'), 'Invalid evidence kind')
        text(item['ref'], 'evidence reference', 500)
        text(item['revision'], 'evidence revision', 128)
    if record['evidence_level'] in ('reproduced', 'validated'):
        require(bool(evidence), 'Reproduced/validated claims require evidence')
    relations = record['relations']
    require(isinstance(relations, list) and len(relations) <= 12, 'Invalid relations')
    for item in relations:
        require(isinstance(item, dict) and set(item) == {'kind', 'id'}, 'Invalid relation fields')
        require(item['kind'] in ('supports', 'contradicts', 'supersedes', 'derived-from'), 'Invalid relation kind')
        identifier(item['id'])
        require(item['id'] != record['id'], 'Self relation is not supported')
    # A later forget may remove each relation separately. Reserve enough revisions
    # for that cleanup so a dependent can never block its target's deletion.
    require(record['revision'] + len(relations) <= MAX_REVISION,
            'Insufficient revision headroom for relationship cleanup')
    created, updated = timestamp(record['created_at']), timestamp(record['updated_at'])
    require(updated >= created, 'Update predates creation')
    for key in ('review_after', 'expires_at'):
        if record[key] is not None:
            require(timestamp(record[key]) >= created, f'{key} predates creation')
    require(len(canonical(record).encode()) <= 32768, 'Record exceeds 32 KiB')
    return record


def make(payload, scope, skills, aliases=None):
    require(isinstance(payload, dict) and set(payload) <= EDITABLE, 'Only editable fields may be supplied')
    instant = now()
    record = dict(schema_version=VERSION, id='mem_' + uuid.uuid4().hex, revision=1,
                  scope=scope, created_at=instant, updated_at=instant,
                  tags=[], status='active', evidence_level='user-stated', sensitivity='internal',
                  applicability={}, evidence=[], related_skills=[], relations=[],
                  review_after=None, expires_at=None)
    record.update(payload)
    if 'review_after' not in payload and record.get('category') not in ('preference', 'decision'):
        record['review_after'] = (timestamp(instant) + timedelta(days=90)).isoformat().replace('+00:00', 'Z')
    return validate(record, skills, aliases)
