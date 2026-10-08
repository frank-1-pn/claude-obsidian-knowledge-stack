#!/usr/bin/env python3
"""Exercise the share package in a disposable vault, including failure cases."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ENV = dict(os.environ, PYTHONUTF8='1')


def run(*args, cwd=None, success=True):
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=ENV,
                            capture_output=True, text=True, encoding='utf-8')
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    return result.stdout


def main():
    with tempfile.TemporaryDirectory(prefix='knowledge-stack-smoke-') as directory:
        vault = Path(directory) / '朋友的测试笔记库'
        run(sys.executable, PACKAGE / 'scripts/init_vault.py', '--vault', vault)
        agent = vault / 'AGENTS.md'
        agent.write_text(agent.read_text(encoding='utf-8') + '\n用户自定义规则。\n', encoding='utf-8')
        before = {p.relative_to(vault): p.read_bytes() for p in vault.rglob('*') if p.is_file()}
        run(sys.executable, PACKAGE / 'scripts/init_vault.py', '--vault', vault)
        assert all((vault / rel).read_bytes() == content for rel, content in before.items()), 'initializer overwrote an existing file'
        run(sys.executable, vault / 'scripts/check_bootstrap.py', '--vault', vault)
        run('git', 'init', '--quiet', vault)
        helper = vault / 'scripts/note_integration_lock.py'
        def lock(*args, success=True):
            return run(sys.executable, helper, '--repo', vault, *args, success=success)
        acquired = json.loads(lock('acquire', '--owner', 'share-smoke', '--job-id', 'offline-fixture'))
        token = acquired['token']
        lock('acquire', '--owner', 'another-session', '--job-id', 'collision', success=False)
        lock('expect', '--token', token, '--item-id', 'fixture')
        lock('release', '--token', token, success=False)
        raw_rel = '.raw/webfetch/2026-10-08_example.md'
        raw = vault / raw_rel
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text('# 示例来源\n\n一个来源对应一篇笔记，原料先归档。\n', encoding='utf-8')
        title = '示例来源与单篇笔记归档'
        note_rel = f'wiki/sources/测试/{title}.md'
        note = vault / note_rel
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f'''---
type: source
title: "{title}"
created: 2026-10-08
updated: 2026-10-08
tags: [example]
status: developing
related: []
raw_path: {raw_rel}
provenance:
  schema: v1
  model: unrecorded
  derived: false
  recorded: 2026-10-08
  verified: [raw-archived]
---

# {title}

> [!abstract] 检索摘要
>
> 这份测试材料说明单来源单笔记的归档方式：原始文件先保存，整理笔记再记录原料位置和实际核实方式，关系与入口集中维护。它用于验证文件落盘、中文路径、来源回溯、最新笔记生成和逐篇验收。这里只使用合成材料，不代表 WorkBuddy 的连接器或模型质量已经实测。

## 来源内容

一个来源对应一篇笔记，原料先归档。
''', encoding='utf-8')
        phases = ['verify-local', 'graph-index', 'log', 'hot-latest', 'validate', 'manifest']
        def checkpoint(phase, state):
            lock('checkpoint', '--token', token, '--item-id', 'fixture', '--phase', phase, '--state', state)
        checkpoint('verify-local', 'started')
        assert raw.is_file() and note.is_file()
        checkpoint('verify-local', 'done')
        checkpoint('graph-index', 'started')
        for name in ['wiki/index.md', 'wiki/sources/_index.md', 'wiki/meta/notes-graph.md']:
            with (vault / name).open('a', encoding='utf-8') as handle:
                handle.write(f'\n- [[{title}]]：原料归档与逐篇验收测试。\n')
        checkpoint('graph-index', 'done')
        checkpoint('log', 'started')
        with (vault / 'wiki/log.md').open('a', encoding='utf-8') as handle:
            handle.write(f'\n## [2026-10-08] ingest | {title}\n\n- Output：[[{title}]]\n- 原始物：{raw_rel}\n')
        checkpoint('log', 'done')
        checkpoint('hot-latest', 'started')
        with (vault / 'wiki/hot.md').open('a', encoding='utf-8') as handle:
            handle.write(f'\n本次测试新增 [[{title}]]。\n')
        run(sys.executable, vault / 'scripts/refresh-latest.py', cwd=Path(directory))
        assert title in (vault / 'wiki/最新笔记.md').read_text(encoding='utf-8')
        checkpoint('hot-latest', 'done')
        checkpoint('validate', 'started')
        report = Path(directory) / 'lint.md'
        run(sys.executable, vault / 'scripts/vault_lint.py', report, '--vault', vault)
        checkpoint('validate', 'done')
        # A source with no final manifest must be detected as incomplete.
        result = run(sys.executable, vault / 'scripts/check_bootstrap.py', '--vault', vault, success=False)
        assert 'no completed manifest entry' in result
        checkpoint('manifest', 'started')
        manifest = vault / '.raw/.manifest.json'
        manifest.write_text(json.dumps({'sources': {raw_rel: {
            'hash': hashlib.sha256(raw.read_bytes()).hexdigest(),
            'ingested_at': '2026-10-08', 'pages_created': [note_rel],
            'pages_updated': ['wiki/index.md', 'wiki/meta/notes-graph.md', 'wiki/log.md']
        }}}, ensure_ascii=False, indent=2), encoding='utf-8')
        run(sys.executable, vault / 'scripts/check_bootstrap.py', '--vault', vault)
        checkpoint('manifest', 'done')
        lock('release', '--token', token)
        # Detect raw tampering and unresolved links, then prove recovery.
        saved_raw = raw.read_bytes()
        raw.write_bytes(saved_raw + b'changed')
        result = run(sys.executable, vault / 'scripts/check_bootstrap.py', '--vault', vault, success=False)
        assert 'sha256 mismatch' in result
        raw.write_bytes(saved_raw)
        saved_note = note.read_bytes()
        with note.open('a', encoding='utf-8') as handle:
            handle.write('\n[[missing-target]]\n')
        result = run(sys.executable, vault / 'scripts/check_bootstrap.py', '--vault', vault, success=False)
        assert 'dead link' in result
        note.write_bytes(saved_note)
        run(sys.executable, vault / 'scripts/check_bootstrap.py', '--vault', vault)
        stats = run(sys.executable, vault / 'scripts/provenance_query.py', '--stats')
        assert 'unrecorded' in stats
        print('PASS: portable initialization, existing-file preservation, Chinese paths, raw/note/index/graph/log/hot/latest/manifest closure, lock conflict and unfinished release protection, missing-manifest/raw-tamper/dead-link failures, provenance query')


if __name__ == '__main__':
    main()
