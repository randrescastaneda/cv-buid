"""Run an existing private renderer's fixture suite through the toolkit CLI.

Usage: PYTHONPATH=src python tests/check_project_renderer.py /path/to/private/CV
No career data are imported: the external suite creates synthetic temp files.
On Windows its native sharing, Unicode scratch and process cleanup cases run.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

from cv_buid.project import adopt_project


def main():
    root = Path(sys.argv[1]).resolve()
    spec = importlib.util.spec_from_file_location('private_renderer_tests', root / 'tests/test_render.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class ToolkitRendering(module.LocalRendering):
        def setUp(self):
            super().setUp()
            (self.root / 'profile.json').write_text(json.dumps({'person': {'name': 'Alex Example'}}))
            adopt_project(self.root, 'render.py', 'profile.json', ['private/quarto/resume.qmd', 'private/quarto/full-cv.qmd'])
            self.command = [sys.executable, '-m', 'cv_buid.cli', 'build', '--project', str(self.root), '--profile', 'test']
            self.env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ToolkitRendering))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
