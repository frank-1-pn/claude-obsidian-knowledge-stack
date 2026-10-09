#!/usr/bin/env python3
"""Prepare an isolated WorkBuddy R&D workspace, preserving every existing file."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]
BASE_SKILLS = ('wiki', 'wiki-ingest', 'wiki-query', 'wiki-lint', 'save',
               'autoresearch', 'canvas', 'defuddle', 'obsidian-markdown', 'obsidian-bases')
BASE_SCRIPTS = ('refresh-latest.py', 'vault_lint.py', 'provenance_query.py',
                'note_integration_lock.py', 'check_bootstrap.py', 'ensure_obsidian.py',
                'bootstrap_rd_assistant.py', 'check_rd_assistant.py')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def environment_python(workspace):
    return workspace / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def add_tree(payload, root, destination):
    if not root.is_dir():
        raise ValueError('Missing component directory: ' + str(root))
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Refuse symlink in distributable source: ' + str(path))
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            payload[(Path(destination) / path.relative_to(root)).as_posix()] = path.read_bytes()


def adapter(name, description, source):
    # The relative path is resolved from .codebuddy/skills/<name>/SKILL.md.
    return ('---\nname: ' + name + '\ndescription: ' + json.dumps(description, ensure_ascii=False) +
            '\n---\n\n# ' + name + '\n\n'
            '完整读取本工作区原始适配入口 [`SKILL.md`](../../../' + source + ') 后执行。\n\n'
            '源入口与其 scripts、templates、vendor 保持仓库布局。该链接相对于当前技能文件；'
            '原始入口内的相对引用按原始入口位置解析。不要把此薄入口当成完整方法。\n').encode('utf-8')


def build_payload(package=PACKAGE):
    payload, skills = {}, []
    for vendor in ('superpowers', 'ppt-master'):
        root = package / 'vendor' / vendor
        snapshot = json.loads((root / 'snapshot.json').read_text(encoding='utf-8'))
        if len(snapshot['revision']) != 40:
            raise ValueError('Upstream revision must be immutable: ' + vendor)
        for relative, expected in snapshot['files_sha256'].items():
            path = (root / relative).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path.read_bytes()) != expected:
                raise ValueError('Upstream snapshot hash mismatch: ' + vendor + '/' + relative)
    scientific_lock = json.loads((package / 'integrations/scientific/upstream-lock.json').read_text(encoding='utf-8'))
    scientific_root = package / 'vendor/scientific-agent-skills'
    if len(scientific_lock['revision']) != 40:
        raise ValueError('Scientific revision must be immutable')
    for entry in scientific_lock['files'] + scientific_lock.get('additional_license_texts', []):
        path = (scientific_root / entry['path']).resolve()
        if not path.is_relative_to(scientific_root.resolve()) or not path.is_file() or digest(path.read_bytes()) != entry['sha256']:
            raise ValueError('Scientific snapshot hash mismatch: ' + entry['path'])
    fixed = {
        'config/vault-agents.template.md': 'AGENTS.md',
        'config/vault-claude-md.template.md': 'CLAUDE.md',
        'config/rd-project/CODEBUDDY.template.md': 'CODEBUDDY.md',
        'config/rd-project/gitignore.template': '.gitignore',
        'LICENSE': 'LICENSE',
        'ATTRIBUTION.md': 'ATTRIBUTION.md',
        '.gitattributes': '.gitattributes',
        'agent.md': 'agent.md',
        'docs/rd-assistant-implementation-plan.md': 'docs/rd-assistant-implementation-plan.md',
        'config/rd-project/requirements.txt': 'requirements.txt',
        'vault/skeletons/index.template.md': 'wiki/index.md',
        'vault/skeletons/hot.template.md': 'wiki/hot.md',
        'vault/skeletons/log.template.md': 'wiki/log.md',
        'vault/skeletons/overview.template.md': 'wiki/overview.md',
        'vault/skeletons/sources-index.template.md': 'wiki/sources/_index.md',
        'vault/skeletons/notes-graph.template.md': 'wiki/meta/notes-graph.md',
        'vault/skeletons/provenance.template.md': 'wiki/meta/provenance.md',
        'vault/skeletons/source-note.template.md': '_templates/source.md',
        'vault/skeletons/synthesis-note.template.md': '_templates/synthesis.md',
    }
    for source, destination in fixed.items():
        payload[destination] = (package / source).read_bytes()
    payload['.raw/.manifest.json'] = b'{"sources": {}}\n'
    for script in BASE_SCRIPTS:
        payload['scripts/' + script] = (package / 'scripts' / script).read_bytes()
    add_tree(payload, package / 'config/rd-project', 'config/rd-project')
    for family in ('scientific', 'workflow', 'presentation', 'email', 'patsnap', 'daily-briefing'):
        add_tree(payload, package / 'integrations' / family, 'integrations/' + family)
    add_tree(payload, package / 'examples/pipeline', 'examples/pipeline')
    add_tree(payload, package / 'docs/email', 'docs/email')
    for vendor in ('scientific-agent-skills', 'superpowers', 'ppt-master'):
        add_tree(payload, package / 'vendor' / vendor, 'vendor/' + vendor)
    for name in BASE_SKILLS:
        add_tree(payload, package / 'skills' / name, 'skills/' + name)
        add_tree(payload, package / 'skills' / name, '.codebuddy/skills/' + name)
        skills.append({'name': name, 'source': 'skills/' + name, 'installed': '.codebuddy/skills/' + name})
    catalog = json.loads((package / 'integrations/scientific/catalog.json').read_text(encoding='utf-8'))
    if len(catalog['skills']) != catalog['count']:
        raise ValueError('Scientific catalog count mismatch')
    for entry in catalog['skills']:
        source = Path(entry['vendor_path'])
        if source.is_absolute() or '..' in source.parts:
            raise ValueError('Scientific source path escapes package')
        name = entry['name']
        if name in [x['name'] for x in skills] or Path(name).name != name or name in ('.', '..'):
            raise ValueError('Skill name collision or invalid name: ' + name)
        add_tree(payload, package / source, '.codebuddy/skills/' + name)
        skills.append({'name': name, 'source': source.as_posix(), 'installed': '.codebuddy/skills/' + name})
    for name, source, description in (
        ('pharma-research-workflow', 'integrations/workflow/SKILL.md', '研发调研：brainstorming、计划、执行与证据核验'),
        ('pharma-presentation', 'integrations/presentation/SKILL.md', '将已核实科研结果转成可编辑PPT并渲染检查'),
    ):
        if not (package / source).is_file():
            raise ValueError('Adapter not ready: ' + source)
        payload['.codebuddy/skills/' + name + '/SKILL.md'] = adapter(name, description, source)
        skills.append({'name': name, 'source': source, 'installed': '.codebuddy/skills/' + name})
    for name in ('mail-triage', 'daily-email-brief', 'urgent-email-alert'):
        source = 'integrations/email/skills/' + name
        add_tree(payload, package / source, '.codebuddy/skills/' + name)
        skills.append({'name': name, 'source': source, 'installed': '.codebuddy/skills/' + name,
                       'connection_status': 'design-only'})
    # Keep cross-skill references such as ../wiki/references readable.
    for item in skills:
        if item['installed'] + '/SKILL.md' not in payload:
            raise ValueError('Installed skill lacks SKILL.md: ' + item['name'])
    registry = {'schema': 1, 'skills': skills, 'mcp_enabled_by_bootstrap': [], 'workbuddy_verified': False,
                'files': {path: digest(data) for path, data in sorted(payload.items())
                          if not path.startswith(('wiki/', '.raw/', '_templates/'))
                          and path not in ('AGENTS.md', 'CLAUDE.md', 'agent.md', 'CODEBUDDY.md')}}
    payload['.codebuddy/rd-stack-install.json'] = (json.dumps(registry, ensure_ascii=False, indent=2) + '\n').encode()
    return payload


def copy_missing(workspace, payload):
    conflicts, created, preserved = [], [], []
    for relative, data in payload.items():
        out = workspace / relative
        if not out.resolve().is_relative_to(workspace):
            raise ValueError('Destination escapes workspace: ' + relative)
        if out.exists():
            if out.is_file() and relative.startswith(('wiki/', '.raw/', '_templates/')):
                preserved.append(relative)
                continue
            if not out.is_file() or digest(out.read_bytes()) != digest(data):
                conflicts.append({'path': relative, 'expected_sha256': digest(data),
                                  'actual_sha256': digest(out.read_bytes()) if out.is_file() else None})
            else:
                preserved.append(relative)
    if conflicts:
        return {'created': [], 'preserved': preserved, 'conflicts': conflicts}
    for relative, data in payload.items():
        out = workspace / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            with out.open('xb') as handle:
                handle.write(data)
            created.append(relative)
        except FileExistsError:
            if out.is_file() and relative.startswith(('wiki/', '.raw/', '_templates/')):
                continue
            if digest(out.read_bytes()) != digest(data):
                raise ValueError('Concurrent file conflict: ' + relative)
    return {'created': created, 'preserved': preserved, 'conflicts': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--skip-obsidian', action='store_true')
    parser.add_argument('--install-deps', action='store_true', help='Create local venv and install exact pinned demo requirements.')
    parser.add_argument('--python', dest='python_executable', help='Python executable for isolated venv, normally Python 3.12/3.13.')
    parser.add_argument('--git', action='store_true', help='Explicitly initialize a local Git repository for cross-session locks. No commit/push.')
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if workspace == PACKAGE or workspace.is_relative_to(PACKAGE) or PACKAGE.is_relative_to(workspace):
        parser.error('Choose a workspace outside the share checkout.')
    report = {'workspace': str(workspace), 'status': 'partial', 'workbuddy_verified': False}
    try:
        payload = build_payload()
        workspace.mkdir(parents=True, exist_ok=True)
        copied = copy_missing(workspace, payload)
        report.update({'created_count': len(copied['created']), 'preserved_count': len(copied['preserved']),
                       'conflicts': copied['conflicts']})
        if report['conflicts']:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2
        if not args.skip_obsidian:
            from ensure_obsidian import ensure_obsidian
            report['obsidian'] = str(ensure_obsidian())
        else:
            report['obsidian'] = 'skipped-by-explicit-flag'
        if args.git and not (workspace / '.git').exists():
            subprocess.run(['git', 'init', str(workspace)], check=True, capture_output=True, text=True)
        if args.install_deps:
            executable = args.python_executable or sys.executable
            probe = subprocess.run([executable, '-c', 'import json,sys; print(json.dumps(list(sys.version_info[:2])))'],
                                   check=True, capture_output=True, text=True)
            version = json.loads(probe.stdout)
            if version not in ([3, 12], [3, 13]):
                raise ValueError('Pinned demo environment requires Python 3.12/3.13; select an installed interpreter with --python')
            if not (workspace / '.venv').resolve().is_relative_to(workspace):
                raise ValueError('Refuse environment symlink outside workspace')
            if not environment_python(workspace).exists():
                subprocess.run([executable, '-m', 'venv', str(workspace / '.venv')], check=True)
            reqs = [workspace / 'requirements.txt', workspace / 'integrations/scientific/requirements-demo.txt',
                    workspace / 'integrations/presentation/requirements-demo.txt']
            if any(not req.is_file() for req in reqs):
                raise ValueError('Pinned requirements not ready for all selected demos')
            command = [str(environment_python(workspace)), '-m', 'pip', 'install', '--disable-pip-version-check']
            command.extend(['-c', str(workspace / 'config/rd-project/dependencies.lock.txt')])
            for req in reqs:
                command.extend(['-r', str(req)])
            subprocess.run(command, check=True)
        if not (workspace / 'wiki/最新笔记.md').exists():
            subprocess.run([sys.executable, str(workspace / 'scripts/refresh-latest.py')], check=True, cwd=workspace)
        from check_rd_assistant import check
        report['checks'] = check(workspace)
        report['status'] = report['checks']['status']
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'prepared' else 2


if __name__ == '__main__':
    raise SystemExit(main())
