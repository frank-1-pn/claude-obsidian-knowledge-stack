#!/usr/bin/env python3
"""Meaningful bootstrap safety/relocation checks, using disposable workspaces only."""
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
import io
from unittest.mock import patch

import bootstrap_rd_assistant

from bootstrap_rd_assistant import build_payload, copy_missing, PACKAGE
from check_rd_assistant import check


class RDBootstrapTests(unittest.TestCase):
    def test_obsidian_failure_is_partial_and_preserves_created_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / 'workspace'
            output = io.StringIO()
            with patch.object(bootstrap_rd_assistant.sys, 'argv', ['bootstrap', '--workspace', str(root)]), patch.object(bootstrap_rd_assistant, 'build_payload', return_value={'agent.md': b'role'}), patch('ensure_obsidian.ensure_obsidian', side_effect=RuntimeError('official installer not available')), redirect_stdout(output):
                status = bootstrap_rd_assistant.main()
            self.assertEqual(status, 2)
            report = json.loads(output.getvalue())
            self.assertEqual(report['status'], 'partial')
            self.assertIn('official installer not available', report['error'])
            self.assertEqual((root / 'agent.md').read_bytes(), b'role')

    def test_tampered_additional_license_is_rejected_before_copy(self):
        original = Path.read_bytes
        def altered(path):
            if path == PACKAGE / 'vendor/scientific-agent-skills/licenses/rdkit.txt':
                return b'corrupted-license'
            return original(path)
        with patch.object(Path, 'read_bytes', altered):
            with self.assertRaisesRegex(ValueError, 'Scientific snapshot hash mismatch: licenses/rdkit.txt'):
                build_payload(PACKAGE)

    def test_conflicting_existing_file_prevents_any_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'AGENTS.md').write_text('user-owned-rules', encoding='utf-8')
            report = copy_missing(root, {'agent.md': b'new-role', 'AGENTS.md': b'different-rules'})
            self.assertEqual(report['conflicts'][0]['path'], 'AGENTS.md')
            self.assertNotEqual(report['conflicts'][0]['actual_sha256'], report['conflicts'][0]['expected_sha256'])
            self.assertFalse((root / 'agent.md').exists())
            self.assertEqual((root / 'AGENTS.md').read_text(), 'user-owned-rules')

    def test_missing_only_idempotence_and_workspace_containment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            report = copy_missing(root, {'directory/file.md': b'a'})
            self.assertEqual(report['created'], ['directory/file.md'])
            second = copy_missing(root, {'directory/file.md': b'a'})
            self.assertFalse(second['created'])
            self.assertEqual(second['preserved'], ['directory/file.md'])
            with self.assertRaises(ValueError):
                copy_missing(root, {'../outside.md': b'unsafe'})

    def test_real_pack_relocation_and_tamper_detection(self):
        payload = build_payload(PACKAGE)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            report = copy_missing(root, payload)
            self.assertFalse(report['conflicts'])
            registry = json.loads((root / '.codebuddy/rd-stack-install.json').read_text(encoding='utf-8'))
            self.assertEqual(len(registry['skills']), 39)
            self.assertEqual(registry['mcp_enabled_by_bootstrap'], [])
            self.assertFalse(registry['workbuddy_verified'])
            for entry in registry['skills']:
                self.assertTrue((root / entry['installed'] / 'SKILL.md').is_file())
                self.assertTrue((root / entry['source']).exists())
            result = check(root)
            self.assertEqual(result['components']['note_write_mode'], 'single-session-serial')
            self.assertTrue(any('.venv not ready' in e for e in result['errors']))
            self.assertFalse(any('hash conflict' in e or 'unreadable' in e or 'relative link' in e for e in result['errors']))
            target = root / '.codebuddy/skills/pkpd-modeling/SKILL.md'
            target.write_text('tampered', encoding='utf-8')
            result = check(root)
            self.assertTrue(any('installed hash conflict: .codebuddy/skills/pkpd-modeling/SKILL.md' in e for e in result['errors']))
            self.assertEqual(result['status'], 'partial')
            self.assertFalse(result['workbuddy_verified'])

    def test_existing_completed_note_metadata_is_preserved_on_reinitialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            payload = build_payload(PACKAGE)
            copy_missing(root, payload)
            changed = {'wiki/index.md': b'user-index-with-completed-note',
                       'wiki/hot.md': b'current-user-state',
                       '.raw/.manifest.json': b'{"sources":{"already-ingested":{}}}\n',
                       '_templates/source.md': b'user-note-template'}
            for name, data in changed.items():
                (root / name).write_bytes(data)
            (root / 'wiki/sources/owned-user-note.md').write_bytes(b'user-owned-note-body')
            result = copy_missing(root, payload)
            self.assertFalse(result['conflicts'])
            for name, data in changed.items():
                self.assertEqual((root / name).read_bytes(), data)
            self.assertEqual((root / 'wiki/sources/owned-user-note.md').read_bytes(), b'user-owned-note-body')


if __name__ == '__main__':
    unittest.main()
