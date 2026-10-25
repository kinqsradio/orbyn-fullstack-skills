#!/usr/bin/env python3
"""Read existing project-owned context pointers. Never execute commands or copy document content."""
import argparse
import json
from pathlib import Path, PurePosixPath

CONTEXT = '.agents/orbyn-context.json'


def local_path(project, value, file_only=False):
    if not isinstance(value, str) or not value:
        raise ValueError('Context paths must be non-empty strings')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '\\' in value or ':' in value:
        raise ValueError(f'Expected a project-relative path: {value}')
    target = (project / value).resolve(strict=True)
    if not target.is_relative_to(project) or (file_only and not target.is_file()):
        raise ValueError(f'Context path leaves the project or has the wrong kind: {value}')
    return target


def context_path(project):
    for path in [project / '.agents', project / CONTEXT]:
        if path.is_symlink():
            raise ValueError('Refusing a symlinked context destination')
    return project / CONTEXT


def check(project):
    project = project.resolve(strict=True)
    data = json.loads(context_path(project).read_text())
    if (not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('project_name'), str)
            or not data['project_name'].strip()):
        raise ValueError('Expected context schema 1 and a project name')
    if set(data) - {'schema_version', 'project_name', 'documents', 'owners'}:
        raise ValueError('Unknown context fields; commands and credentials do not belong here')
    for group in ['documents', 'owners']:
        values = data.get(group)
        if not isinstance(values, dict):
            raise ValueError(f'{group} must map names to existing project-relative paths')
        for name, value in values.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Context entries need a name')
            local_path(project, value, file_only=group == 'documents')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check'])
    parser.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    try:
        check(args.project)
        print('Existing project pointers validated; no files changed.')
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f'Project context stopped: {error}\n')


if __name__ == '__main__':
    main()
