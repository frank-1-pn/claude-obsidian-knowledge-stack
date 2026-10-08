"""Installer tests use isolated files and mocks; never install host software."""
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import ensure_obsidian as installer
import init_vault


class InstallationTests(unittest.TestCase):
    def test_existing_installation_never_downloads(self):
        with patch.object(installer, 'find_installed', return_value='installed-program'), patch.object(installer, 'download_release') as download:
            self.assertEqual(installer.ensure_obsidian(), 'installed-program')
            download.assert_not_called()

    def test_check_only_missing_never_downloads(self):
        with patch.object(installer, 'find_installed', return_value=None), patch.object(installer, 'download_release') as download:
            with self.assertRaisesRegex(RuntimeError, 'not installed'):
                installer.ensure_obsidian(check_only=True)
            download.assert_not_called()

    def test_windows_detection_finds_existing_user_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'Obsidian/Obsidian.exe'
            target.parent.mkdir()
            target.write_bytes(b'MZfixture')
            with patch.dict(os.environ, {'LOCALAPPDATA': temporary}, clear=True), patch.object(installer.shutil, 'which', return_value=None), patch.object(installer, 'windows_registered_paths', return_value=[]):
                self.assertEqual(installer.find_installed('Windows'), str(target))

    def release(self, data, digest=None, url=None):
        return {'tag_name': 'v2.0.0', 'assets': [{
            'name': 'Obsidian-2.0.0.exe',
            'browser_download_url': url or installer.DOWNLOAD_PREFIX + 'v2.0.0/Obsidian-2.0.0.exe',
            'digest': digest or 'sha256:' + hashlib.sha256(data).hexdigest(),
        }]}

    def test_official_download_hash_and_installer_parameters(self):
        data = b'MZ installer test fixture'
        responses = [io.BytesIO(json.dumps(self.release(data)).encode()), io.BytesIO(data)]
        with tempfile.TemporaryDirectory() as temporary, patch.object(installer.urllib.request, 'urlopen', side_effect=responses), patch.object(installer.subprocess, 'run') as run:
            folder = Path(temporary)
            path = installer.download_release('Windows', folder)
            self.assertEqual(path.read_bytes(), data)
            installer.install_release('Windows', path, folder)
            self.assertEqual(run.call_args.args[0], [str(path), '/S', '/currentuser'])
            self.assertTrue(run.call_args.kwargs['check'])

    def test_tampered_download_is_rejected(self):
        metadata = self.release(b'original')
        responses = [io.BytesIO(json.dumps(metadata).encode()), io.BytesIO(b'tampered')]
        with tempfile.TemporaryDirectory() as temporary, patch.object(installer.urllib.request, 'urlopen', side_effect=responses):
            with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
                installer.download_release('Windows', Path(temporary))

    def test_nonofficial_asset_never_downloads(self):
        response = io.BytesIO(json.dumps(self.release(b'fixture', url='https://example.com/installer.exe')).encode())
        with tempfile.TemporaryDirectory() as temporary, patch.object(installer.urllib.request, 'urlopen', return_value=response) as fetch:
            with self.assertRaisesRegex(RuntimeError, 'Official download URL'):
                installer.download_release('Windows', Path(temporary))
            self.assertEqual(fetch.call_count, 1)

    def test_success_requires_post_install_detection(self):
        with patch.object(installer, 'find_installed', side_effect=[None, 'new-program']), patch.object(installer, 'download_release', return_value=Path('fixture.exe')), patch.object(installer, 'install_release') as install:
            self.assertEqual(installer.ensure_obsidian(), 'new-program')
            install.assert_called_once()
        with patch.object(installer, 'find_installed', return_value=None), patch.object(installer, 'download_release', return_value=Path('fixture.exe')), patch.object(installer, 'install_release'):
            with self.assertRaisesRegex(RuntimeError, 'no installed Obsidian'):
                installer.ensure_obsidian()

    def test_installer_failure_is_not_reported_as_success(self):
        with patch.object(installer, 'find_installed', return_value=None), patch.object(installer, 'download_release', return_value=Path('fixture.exe')), patch.object(installer, 'install_release', side_effect=subprocess.CalledProcessError(1, 'fixture')):
            with self.assertRaises(subprocess.CalledProcessError):
                installer.ensure_obsidian()

    def test_linux_installs_executable_and_launcher_in_user_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / 'fixture.AppImage'
            source.write_bytes(b'AppImage fixture')
            with patch.object(installer.Path, 'home', return_value=folder), patch.object(installer.Path, 'symlink_to') as link:
                installer.install_release('Linux', source, folder)
                program = folder / '.local/opt/obsidian/Obsidian.AppImage'
                self.assertEqual(program.read_bytes(), source.read_bytes())
                link.assert_called_once_with(program)
                if os.name != 'nt':
                    self.assertTrue(program.stat().st_mode & 0o111)

    def test_initializer_checks_obsidian_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / 'vault'
            with patch.object(init_vault.sys, 'argv', ['init_vault.py', '--vault', str(vault)]), patch.object(init_vault, 'ensure_obsidian', return_value='installed-program') as ensure:
                init_vault.main()
                ensure.assert_called_once()
                self.assertTrue((vault / 'scripts/ensure_obsidian.py').is_file())

    def test_initializer_does_not_create_vault_when_installation_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / 'vault'
            with patch.object(init_vault.sys, 'argv', ['init_vault.py', '--vault', str(vault)]), patch.object(init_vault, 'ensure_obsidian', side_effect=RuntimeError('install failed')):
                with self.assertRaises(SystemExit) as error:
                    init_vault.main()
                self.assertEqual(error.exception.code, 1)
                self.assertFalse(vault.exists())

    def test_mac_copies_app_and_detaches_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            home = folder / 'home'
            expected = folder / 'mounted/Obsidian.app/Contents/MacOS/Obsidian'
            def mount_or_detach(command, **kwargs):
                if command[1] == 'attach':
                    expected.parent.mkdir(parents=True)
                    expected.write_bytes(b'app fixture')
            with patch.object(installer.Path, 'home', return_value=home), patch.object(installer.subprocess, 'run', side_effect=mount_or_detach) as run:
                installer.install_release('Darwin', folder / 'fixture.dmg', folder)
                self.assertTrue((home / 'Applications/Obsidian.app/Contents/MacOS/Obsidian').is_file())
                self.assertEqual(run.call_args.args[0][1], 'detach')


if __name__ == '__main__':
    unittest.main()
