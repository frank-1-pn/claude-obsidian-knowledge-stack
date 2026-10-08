#!/usr/bin/env python3
"""Check share-package privacy boundaries, templates and skill frontmatter."""
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    for name in ['wiki', '.raw', '_attachments', '.obsidian', '.claude',
                 'scripts/feishu-bridge', 'scripts/wechat-fetch',
                 'setup/03-feishu-bot.md', 'setup/05-wechat-mcp.md']:
        if (ROOT / name).exists():
            errors.append('excluded path present: ' + name)
    count = 0
    for path in ROOT.rglob('*'):
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts:
            continue
        if path.suffix not in {'.md', '.html', '.py', '.ps1', '.json', '.txt'} and path.name != '.gitignore':
            continue
        count += 1
        text = path.read_text(encoding='utf-8-sig')
        patterns = [r'C:[/\\]+Users[/\\]+(?!you(?:[/\\]|\b)|<)[\w.-]+',
                    r'/c/Users/(?!you(?:/|\b)|<)[\w.-]+', r'\b(?:cli|oc|ou)_[0-9a-f]{12,}\b',
                    r'\bsk-[A-Za-z0-9_-]{20,}\b']
        for pattern in patterns:
            if re.search(pattern, text):
                errors.append('private literal: ' + rel)
        if path.suffix == '.json':
            try:
                json.loads(text)
            except ValueError:
                errors.append('invalid JSON: ' + rel)
        if path.name == 'SKILL.md' or rel.startswith('vault/skeletons/'):
            m = re.match(r'^---\r?\n(.*?)\r?\n---', text, re.S)
            try:
                fm = yaml.safe_load(m.group(1)) if m else None
                if not isinstance(fm, dict):
                    raise ValueError('missing mapping')
                if path.name == 'SKILL.md' and (not fm.get('name') or not fm.get('description')):
                    raise ValueError('skill missing name/description')
            except (yaml.YAMLError, ValueError):
                errors.append('invalid frontmatter: ' + rel)
    for error in errors:
        print('FAIL:', error)
    print(f'share-check: {count} text files; {len(errors)} errors')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
