#!/usr/bin/env python3
"""Check workspace assets and pinned local dependencies; never claims WorkBuddy acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def check(workspace):
    workspace = workspace.resolve()
    errors, components = [], {}
    for name in ('agent.md', 'AGENTS.md', 'CODEBUDDY.md', 'docs/rd-assistant-implementation-plan.md',
                 'wiki/hot.md', 'wiki/index.md', 'wiki/meta/notes-graph.md', '.raw/.manifest.json'):
        if not (workspace / name).is_file():
            errors.append('missing: ' + name)
    try:
        registry = json.loads((workspace / '.codebuddy/rd-stack-install.json').read_text(encoding='utf-8'))
        for relative, expected in registry['files'].items():
            path = (workspace / relative).resolve()
            if not path.is_relative_to(workspace) or not path.is_file():
                errors.append('missing installed file: ' + relative)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append('installed hash conflict: ' + relative)
        names = []
        for entry in registry['skills']:
            names.append(entry['name'])
            skill = workspace / entry['installed'] / 'SKILL.md'
            source = workspace / entry['source']
            if not source.exists() or not skill.is_file():
                errors.append('unreadable skill source: ' + entry['name'])
            if skill.is_file():
                text = skill.read_text(encoding='utf-8')
                if not re.search(r'^name:\s*[\"\']?' + re.escape(entry['name']) + r'[\"\']?\s*$', text, re.M):
                    errors.append('skill frontmatter name mismatch: ' + entry['name'])
                for link in re.findall(r'\]\((\.\./[^)]+)\)', text):
                    target = (skill.parent / link.split('#')[0]).resolve()
                    if not target.is_relative_to(workspace) or not target.exists():
                        errors.append('broken installed relative link: ' + entry['name'] + ': ' + link)
        if len(names) != len(set(names)):
            errors.append('duplicate skill name')
        components['skills'] = {'installed_count': len(names), 'names': names, 'execution_verified': False}
        if registry.get('mcp_enabled_by_bootstrap') != []:
            errors.append('bootstrap must not enable MCP connections')
    except (OSError, KeyError, ValueError, TypeError) as exc:
        errors.append('install registry: ' + str(exc))
    from bootstrap_rd_assistant import environment_python
    python = environment_python(workspace)
    expected = {}
    for relative in ('requirements.txt', 'integrations/scientific/requirements-demo.txt',
                     'integrations/presentation/requirements-demo.txt', 'config/rd-project/dependencies.lock.txt'):
        req = workspace / relative
        if not req.is_file():
            errors.append('pinned requirements missing: ' + relative)
            continue
        for line in req.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if not re.fullmatch(r'[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+', line):
                errors.append('dependency is not pinned: ' + line)
                continue
            name, version = line.split('==')
            if name in expected and expected[name] != version:
                errors.append('dependency pin conflict: ' + name)
            expected[name] = version
    if python.is_file():
        code = '''import importlib, importlib.metadata, json, sys
out = {}
aliases = {'pyyaml': 'yaml', 'pillow': 'PIL', 'python-pptx': 'pptx', 'xlsxwriter': 'xlsxwriter',
           'rpds-py': 'rpds', 'lxml': 'lxml.etree'}
for name in json.loads(sys.argv[1]):
    try:
        version = importlib.metadata.version(name)
        importlib.import_module(aliases.get(name.lower(), name.lower().replace('-', '_')))
        out[name] = version
    except Exception as exc:
        out[name] = {'error': type(exc).__name__ + ': ' + str(exc)}
print(json.dumps(out))
'''
        try:
            result = subprocess.run([str(python), '-c', code, json.dumps(list(expected))],
                                    check=True, capture_output=True, text=True)
            actual = json.loads(result.stdout)
            for name, version in expected.items():
                if actual.get(name) != version:
                    errors.append('dependency version: ' + name + ' expected=' + version + ' actual=' + str(actual.get(name)))
            components['dependencies'] = actual
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            errors.append('dependency probe failed: ' + str(exc))
    else:
        errors.append('isolated .venv not ready; rerun bootstrap with --install-deps and compatible --python')
    components['note_write_mode'] = 'cross-session-lock' if (workspace / '.git').exists() else 'single-session-serial'
    components['professional_connections'] = {'patsnap': 'design-only', 'email': 'design-only'}
    return {'status': 'partial' if errors else 'prepared', 'errors': errors, 'components': components,
            'workbuddy_verified': False, 'desktop_obsidian_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    result = check(args.workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result['errors'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
