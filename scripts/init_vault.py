#!/usr/bin/env python3
"""Create a portable vault; existing files are always preserved."""
import argparse
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', required=True, type=Path)
    vault = parser.parse_args().vault.resolve()
    if vault == PACKAGE or PACKAGE.is_relative_to(vault) or vault.is_relative_to(PACKAGE):
        parser.error('Choose your own vault outside the share checkout.')
    for name in ['.raw', 'wiki/sources', 'wiki/meta', '_attachments', '_templates']:
        (vault / name).mkdir(parents=True, exist_ok=True)
    mapping = {
        'config/vault-agents.template.md': 'AGENTS.md',
        'config/vault-claude-md.template.md': 'CLAUDE.md',
        'requirements.txt': 'requirements.txt',
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
    for path in (PACKAGE / 'skills').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            rel = path.relative_to(PACKAGE).as_posix()
            mapping[rel] = rel
    for name in ['refresh-latest.py', 'vault_lint.py', 'provenance_query.py',
                 'note_integration_lock.py', 'check_bootstrap.py']:
        mapping['scripts/' + name] = 'scripts/' + name
    created = preserved = 0
    for source, destination in mapping.items():
        out = vault / destination
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            with out.open('xb') as handle:
                handle.write((PACKAGE / source).read_bytes())
            created += 1
        except FileExistsError:
            preserved += 1
    try:
        with (vault / '.raw/.manifest.json').open('x', encoding='utf-8') as handle:
            handle.write('{"sources": {}}\n')
        created += 1
    except FileExistsError:
        preserved += 1
    if not (vault / 'wiki/最新笔记.md').exists():
        subprocess.run([sys.executable, str(vault / 'scripts/refresh-latest.py')], check=True)
    print(f'created={created} preserved={preserved} vault={vault}')


if __name__ == '__main__':
    main()
