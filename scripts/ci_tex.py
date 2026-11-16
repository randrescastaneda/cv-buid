"""Configure CI TinyTeX, falling back when a CTAN mirror is stale/unavailable."""
import os
import subprocess

REPOSITORIES = (
    'https://ctan.math.illinois.edu/systems/texlive/tlnet',
    'https://mirrors.mit.edu/CTAN/systems/texlive/tlnet',
    'https://mirror.ctan.org/systems/texlive/tlnet',
)
PACKAGES = ('titlesec', 'enumitem', 'needspace', 'psnfss', 'helvetic')


def configure(run=subprocess.run):
    for repository in REPOSITORIES:
        print(f'Configuring TeX from {repository}', flush=True)
        try:
            # Persist the successful mirror for Quarto's later package installs.
            run(['tlmgr', 'option', 'repository', repository], check=True, timeout=180)
            run(['tlmgr', 'update', '--self'], check=True, timeout=180)
            run(['tlmgr', 'install', *PACKAGES], check=True, timeout=180)
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            print(f'TeX mirror attempt failed: {error}; trying next mirror.', flush=True)
    raise RuntimeError('All TeX mirror attempts failed; rendering acceptance must not be skipped.')


if __name__ == '__main__':
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('CI-only installer; configure tools explicitly on your own machine.')
    configure()
