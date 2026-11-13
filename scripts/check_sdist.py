"""Smoke-test source-distribution installation in an isolated environment."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def main():
    archive = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='cv-buid sdist ') as folder:
        root = Path(folder)
        runtime = root / 'runtime'
        venv.EnvBuilder(with_pip=True).create(runtime)
        python = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        env = dict(os.environ, PYTHONPATH='', PIP_DISABLE_PIP_VERSION_CHECK='1')
        subprocess.run([str(python), '-m', 'pip', 'install', '--no-deps', str(archive)], cwd=root, env=env, check=True)
        cli = [str(python), '-m', 'cv_buid.cli']
        project = root / 'fictional starter'
        subprocess.run(cli + ['init', str(project)], cwd=root, env=env, check=True)
        config = json.loads((project / 'cv-buid.json').read_text())
        assert config['renderer'] == 'builtin'
        assert 'Alex Example' in (project / 'private/quarto/resume.qmd').read_text()
        plan = root / 'upgrade.json'
        subprocess.run(cli + ['upgrade', '--project', str(project), '--out', str(plan)], cwd=root, env=env, check=True)
        assert json.loads(plan.read_text())['changes'] == []
        print('Source-distribution clean install, starter and no-op upgrade passed')


if __name__ == '__main__':
    main()
