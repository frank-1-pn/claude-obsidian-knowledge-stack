#!/usr/bin/env python3
"""Reuse installed Obsidian, otherwise install the official desktop release."""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

RELEASE_API = 'https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest'
DOWNLOAD_PREFIX = 'https://github.com/obsidianmd/obsidian-releases/releases/download/'


def windows_registered_paths():
    import winreg
    candidates = []
    for hive in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        for view in [winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY]:
            try:
                with winreg.OpenKey(hive, r'Software\Microsoft\Windows\CurrentVersion\Uninstall', 0, winreg.KEY_READ | view) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, index)) as entry:
                                if winreg.QueryValueEx(entry, 'DisplayName')[0] != 'Obsidian':
                                    continue
                                try:
                                    location = winreg.QueryValueEx(entry, 'InstallLocation')[0]
                                    if location:
                                        candidates.append(Path(os.path.expandvars(location)) / 'Obsidian.exe')
                                except OSError:
                                    pass
                                try:
                                    icon = winreg.QueryValueEx(entry, 'DisplayIcon')[0]
                                    candidates.append(Path(os.path.expandvars(icon.rsplit(',', 1)[0].strip('"'))))
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except OSError:
                continue
    return candidates


def find_installed(system=None):
    system = system or platform.system()
    candidates = []
    command = shutil.which('Obsidian.exe' if system == 'Windows' else 'obsidian')
    if command:
        candidates.append(Path(command))
    if system == 'Windows':
        for variable, suffix in [('LOCALAPPDATA', 'Obsidian/Obsidian.exe'),
                                 ('LOCALAPPDATA', 'Programs/Obsidian/Obsidian.exe'),
                                 ('ProgramFiles', 'Obsidian/Obsidian.exe'),
                                 ('ProgramFiles(x86)', 'Obsidian/Obsidian.exe')]:
            if os.environ.get(variable):
                candidates.append(Path(os.environ[variable]) / suffix)
        candidates.extend(windows_registered_paths())
    elif system == 'Darwin':
        candidates.extend([Path('/Applications/Obsidian.app/Contents/MacOS/Obsidian'),
                           Path.home() / 'Applications/Obsidian.app/Contents/MacOS/Obsidian'])
    elif system == 'Linux':
        candidates.extend([Path('/opt/Obsidian/obsidian'), Path('/opt/obsidian/obsidian'),
                           Path.home() / '.local/opt/obsidian/Obsidian.AppImage'])
        for tool, args in [('flatpak', ['info', 'md.obsidian.Obsidian']),
                           ('snap', ['list', 'obsidian'])]:
            binary = shutil.which(tool)
            if binary and subprocess.run([binary, *args], capture_output=True, timeout=30).returncode == 0:
                return f'{tool}:obsidian'
    for candidate in candidates:
        if candidate.is_file() and (system == 'Windows' or os.access(candidate, os.X_OK)):
            return str(candidate)
    return None


def download_release(system, directory):
    request = urllib.request.Request(RELEASE_API, headers={'User-Agent': 'knowledge-stack-setup', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    if system == 'Windows':
        pattern = r'Obsidian-[0-9.]+\.exe'
    elif system == 'Darwin':
        pattern = r'Obsidian-[0-9.]+\.dmg'
    elif system == 'Linux':
        machine = platform.machine().lower()
        if machine in {'arm64', 'aarch64'}:
            pattern = r'Obsidian-[0-9.]+-arm64\.AppImage'
        elif machine in {'x86_64', 'amd64'}:
            pattern = r'Obsidian-[0-9.]+\.AppImage'
        else:
            raise RuntimeError(f'Unsupported Linux architecture: {machine}')
    else:
        raise RuntimeError(f'Unsupported desktop platform: {system}')
    if release.get('draft') or release.get('prerelease'):
        raise RuntimeError('The release is not a stable public release.')
    assets = [a for a in release.get('assets', []) if re.fullmatch(pattern, a.get('name', ''))]
    if len(assets) != 1:
        raise RuntimeError('No unique official installer for this platform.')
    asset = assets[0]
    url = asset.get('browser_download_url', '')
    digest = asset.get('digest', '') or ''
    if not url.startswith(DOWNLOAD_PREFIX) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise RuntimeError('Official download URL or SHA-256 metadata is missing.')
    installer = directory / asset['name']
    print(f'Downloading official Obsidian {release.get("tag_name", "release")}...')
    request = urllib.request.Request(url, headers={'User-Agent': 'knowledge-stack-setup'})
    hasher = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=60) as response, installer.open('xb') as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)
            hasher.update(chunk)
    if hasher.hexdigest() != digest.removeprefix('sha256:'):
        raise RuntimeError('Installer SHA-256 mismatch; installation stopped.')
    return installer


def install_release(system, installer, directory):
    if system == 'Windows':
        subprocess.run([str(installer), '/S', '/currentuser'], check=True, timeout=600)
    elif system == 'Darwin':
        mount = directory / 'mounted'
        mount.mkdir()
        subprocess.run(['hdiutil', 'attach', str(installer), '-nobrowse', '-quiet', '-mountpoint', str(mount)], check=True, timeout=120)
        try:
            bundle = mount / 'Obsidian.app'
            if not (bundle / 'Contents/MacOS/Obsidian').is_file():
                raise RuntimeError('Mounted image does not contain Obsidian.app.')
            destination = Path.home() / 'Applications/Obsidian.app'
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(bundle, destination, symlinks=True)
        finally:
            subprocess.run(['hdiutil', 'detach', str(mount), '-quiet'], check=True, timeout=120)
    elif system == 'Linux':
        destination = Path.home() / '.local/opt/obsidian/Obsidian.AppImage'
        destination.parent.mkdir(parents=True, exist_ok=True)
        with installer.open('rb') as source, destination.open('xb') as output:
            shutil.copyfileobj(source, output)
        destination.chmod(0o755)
        launcher = Path.home() / '.local/bin/obsidian'
        launcher.parent.mkdir(parents=True, exist_ok=True)
        if not launcher.exists() and not launcher.is_symlink():
            launcher.symlink_to(destination)


def ensure_obsidian(check_only=False):
    system = platform.system()
    installed = find_installed(system)
    if installed:
        print(f'Obsidian installed: {installed}')
        return installed
    if check_only:
        raise RuntimeError('Obsidian is not installed.')
    if system not in {'Windows', 'Darwin', 'Linux'}:
        raise RuntimeError(f'Unsupported desktop platform: {system}')
    print('Obsidian missing; installing for the current user...')
    with tempfile.TemporaryDirectory(prefix='obsidian-setup-') as temporary:
        directory = Path(temporary)
        installer = download_release(system, directory)
        install_release(system, installer, directory)
    installed = find_installed(system)
    if not installed:
        raise RuntimeError('Installer finished, but no installed Obsidian program was found.')
    print(f'Obsidian installation verified: {installed}')
    return installed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Inspect without downloading or installing.')
    try:
        ensure_obsidian(parser.parse_args().check_only)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Obsidian setup failed: {exc}\n')


if __name__ == '__main__':
    main()
