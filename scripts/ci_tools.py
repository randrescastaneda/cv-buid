"""Install pinned official Quarto into an ephemeral Actions runner only."""
import hashlib
import os
from pathlib import Path
import platform
import sys
import tarfile
import urllib.request
import zipfile

VERSION = '1.9.37'


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('CI-only installer; configure tools explicitly on your own machine.')
    if '--tex-path' in sys.argv:
        roots = [Path.home() / 'Library/TinyTeX', Path.home() / '.TinyTeX',
                 Path(os.environ.get('APPDATA', str(Path.home()))) / 'TinyTeX']
        names = ['tlmgr.bat'] if os.name == 'nt' else ['tlmgr']
        found = [p for root in roots if root.is_dir() for n in names for p in root.rglob(n)]
        if not found:
            raise SystemExit('Managed TinyTeX package manager not found.')
        binary = found[0].parent
    else:
        system = platform.system()
        suffix = 'win.zip' if system == 'Windows' else 'macos.tar.gz' if system == 'Darwin' else 'linux-amd64.tar.gz'
        filename = f'quarto-{VERSION}-{suffix}'
        base = f'https://github.com/quarto-dev/quarto-cli/releases/download/v{VERSION}/'
        root = Path(os.environ['RUNNER_TEMP']) / 'cv-buid-quarto'
        root.mkdir(exist_ok=True)
        archive = root / filename
        with urllib.request.urlopen(base + f'quarto-{VERSION}-checksums.txt', timeout=60) as response:
            checksums = response.read().decode()
        expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1].lstrip('*') == filename)
        with urllib.request.urlopen(base + filename, timeout=120) as response:
            archive.write_bytes(response.read())
        if hashlib.sha256(archive.read_bytes()).hexdigest().lower() != expected.lower():
            raise SystemExit('Official Quarto checksum mismatch.')
        destination = root / 'tool'
        destination.mkdir(exist_ok=True)
        if suffix.endswith('.zip'):
            with zipfile.ZipFile(archive) as z:
                if any(not (destination / n).resolve().is_relative_to(destination.resolve()) for n in z.namelist()):
                    raise SystemExit('Unsafe archive member.')
                z.extractall(destination)
            binary = next(destination.rglob('quarto.cmd')).parent
        else:
            with tarfile.open(archive) as t:
                t.extractall(destination, filter='data')
            binary = next(p for p in destination.rglob('quarto') if p.is_file() and p.parent.name == 'bin').parent
    with open(os.environ['GITHUB_PATH'], 'a', encoding='utf-8') as stream:
        stream.write(str(binary) + '\n')
    print('Tool directory:', binary)


if __name__ == '__main__':
    main()
