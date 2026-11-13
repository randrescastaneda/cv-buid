"""Build one review wheel with checksums and source provenance; never release."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'dist/review-wheel';out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    epoch = subprocess.check_output(['git', 'show', '-s', '--format=%ct', 'HEAD'], cwd=ROOT, text=True).strip()
    env = dict(os.environ, SOURCE_DATE_EPOCH=epoch, PIP_DISABLE_PIP_VERSION_CHECK='1')
    subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--wheel-dir', str(out), '.'], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, '-c', "from setuptools.build_meta import build_sdist; build_sdist('dist/review-wheel')"], cwd=ROOT, env=env, check=True)
    wheels = list(out.glob('*.whl'))
    if len(wheels) != 1: raise RuntimeError('Use a clean review-wheel directory')
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as z:
        required = ['cv_buid/engine.py', 'cv_buid/upgrade.py', 'cv_buid/assets/starter/.gitignore',
                    'cv_buid/assets/starter/private/quarto/resume.qmd',
                    'cv_buid/assets/starter/private/quarto/styles/reference.docx']
        assert all(name in z.namelist() for name in required)
        profile = json.loads(z.read('cv_buid/assets/starter/private/profile.json'))
        assert profile['person']['name'] == 'Alex Example'
        assert all(not e.get('public') for e in profile['entries'].values())
        assert any(name.endswith('/licenses/LICENSE') for name in z.namelist())
        assert any(name.endswith('/licenses/THIRD_PARTY_NOTICES.md') for name in z.namelist())
    sha = hashlib.sha256(wheel.read_bytes()).hexdigest()
    archives = [wheel, *out.glob('*.tar.gz')]
    (out / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in archives))
    (out / 'requirements.txt').write_text('./' + wheel.name + ' --hash=sha256:' + sha + '\n')
    (out / 'INSTALL.txt').write_text('Extract all files together, then run:\npython3 -m pip install --no-index --no-deps --require-hashes -r requirements.txt\nOn Windows replace python3 with py -3.\nThis is a review wheel, not a public release.\n')
    (out / 'BUILD-INFO.json').write_text(json.dumps({'commit': commit, 'wheel': wheel.name, 'sha256': sha,
                                                   'source_date_epoch': epoch, 'release': False}, indent=2) + '\n')
    print('Private review wheel:', wheel.name, sha)


if __name__ == '__main__': main()
