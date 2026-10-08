#!/usr/bin/env python3
"""Offline validation of an initialized vault and completed source entries."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import yaml


def check(vault):
    vault = vault.resolve()
    errors = []
    required = ['AGENTS.md', 'wiki/index.md', 'wiki/hot.md', 'wiki/log.md',
                'wiki/overview.md', 'wiki/最新笔记.md', 'wiki/sources/_index.md',
                'wiki/meta/notes-graph.md', 'wiki/meta/provenance.md', '.raw/.manifest.json',
                'scripts/refresh-latest.py', 'scripts/vault_lint.py', 'scripts/note_integration_lock.py']
    for name in required:
        if not (vault / name).is_file():
            errors.append('missing: ' + name)
    for name in ['wiki', 'wiki-ingest', 'wiki-query', 'wiki-lint', 'save', 'autoresearch',
                 'canvas', 'defuddle', 'obsidian-markdown', 'obsidian-bases']:
        if not (vault / 'skills' / name / 'SKILL.md').is_file():
            errors.append('missing skill: ' + name)
    try:
        sources = json.loads((vault / '.raw/.manifest.json').read_text(encoding='utf-8'))['sources']
        if not isinstance(sources, dict):
            raise ValueError('sources must be an object')
    except (OSError, ValueError, KeyError) as exc:
        errors.append('manifest: ' + str(exc))
        sources = {}
    registered = set()
    for raw, entry in sources.items():
        raw_file = (vault / raw).resolve()
        if not raw.startswith('.raw/') or not raw_file.is_relative_to(vault) or not raw_file.is_file():
            errors.append('manifest raw missing or outside vault: ' + raw)
            continue
        digest = hashlib.sha256(raw_file.read_bytes()).hexdigest()
        if not isinstance(entry, dict) or entry.get('hash') != digest:
            errors.append('manifest sha256 mismatch: ' + raw)
            continue
        pages = entry.get('pages_created', [])
        if not isinstance(pages, list) or any(not isinstance(x, str) for x in pages):
            errors.append('manifest pages_created must be paths: ' + raw)
        else:
            registered.update(pages)
    texts = {}
    stems = {}
    for path in (vault / 'wiki').rglob('*.md'):
        rel = path.relative_to(vault).as_posix()
        text = path.read_text(encoding='utf-8-sig')
        texts[rel] = text
        if path.name != '_index.md' and path.stem in stems:
            errors.append('duplicate filename: ' + path.stem)
        stems[path.stem] = path
        match = re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
        try:
            fm = yaml.safe_load(match.group(1)) if match else None
            if not isinstance(fm, dict):
                raise ValueError('frontmatter must be a mapping')
        except (yaml.YAMLError, ValueError) as exc:
            errors.append(f'{rel}: YAML {exc}')
            continue
        if not rel.startswith('wiki/sources/') or path.name == '_index.md':
            continue
        for field in ['type', 'title', 'created', 'updated', 'tags', 'raw_path', 'provenance']:
            if field not in fm:
                errors.append(f'{rel}: missing {field}')
        raw_paths = fm.get('raw_path', [])
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
        if not isinstance(raw_paths, list) or not raw_paths:
            errors.append(f'{rel}: raw_path must refer to archived material')
            raw_paths = []
        for raw in raw_paths:
            if not isinstance(raw, str):
                errors.append(f'{rel}: invalid raw_path')
                continue
            raw_file = (vault / raw).resolve()
            if not raw.startswith('.raw/') or not raw_file.is_relative_to(vault) or not raw_file.exists():
                errors.append(f'{rel}: missing raw {raw}')
        provenance = fm.get('provenance', {})
        if not isinstance(provenance, dict):
            provenance = {}
        if provenance.get('schema') != 'v1' or not provenance.get('model') or not isinstance(provenance.get('derived'), bool) or not provenance.get('recorded') or not isinstance(provenance.get('verified'), list):
            errors.append(f'{rel}: incomplete provenance')
        if rel not in registered:
            errors.append(f'{rel}: no completed manifest entry')
        if not re.search(r'^>\s*\[!abstract\]', text, re.M):
            errors.append(f'{rel}: missing retrieval abstract')
        for name in ['wiki/index.md', 'wiki/meta/notes-graph.md', 'wiki/log.md', 'wiki/最新笔记.md']:
            meta = vault / name
            if not meta.is_file() or path.stem not in meta.read_text(encoding='utf-8'):
                errors.append(f'{rel}: not recorded in {name}')
    for rel in registered:
        if rel not in texts or not rel.startswith('wiki/sources/') or rel.endswith('/_index.md'):
            errors.append('manifest note missing or invalid: ' + rel)
    for rel, text in texts.items():
        text = re.sub(r'^```.*?^```', '', text, flags=re.S | re.M)
        text = re.sub(r'`[^`\n]*`', '', text)
        for target in re.findall(r'!?\[\[([^\]|#]+)', text):
            target = target.rstrip('\\')
            base = Path(target).stem
            if base in stems or (vault / target).is_file() or (vault / '_attachments' / target).is_file():
                continue
            errors.append(f'{rel}: dead link {target}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path, default=Path(__file__).resolve().parents[1])
    errors = check(parser.parse_args().vault)
    for error in errors:
        print('FAIL:', error)
    print(f'vault-check: {len(errors)} errors')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
