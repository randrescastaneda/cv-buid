"""CI mirror fallback is bounded and never hides dependency failures."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location('ci_tex', Path(__file__).resolve().parents[1] / 'scripts/ci_tex.py')
ci_tex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_tex)


class TexMirrorFallback(unittest.TestCase):
    def test_success_stops_after_install(self):
        run = Mock()
        ci_tex.configure(run)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(run.call_args.args[0], ['tlmgr', 'install', *ci_tex.PACKAGES])

    def test_stale_self_update_tries_another_mirror(self):
        run = Mock(side_effect=[None, subprocess.CalledProcessError(1, 'tlmgr'), None, None, None])
        ci_tex.configure(run)
        self.assertEqual(run.call_count, 5)
        self.assertEqual(run.call_args_list[2].args[0][-1], ci_tex.REPOSITORIES[1])

    def test_install_failure_tries_another_mirror(self):
        run = Mock(side_effect=[None, None, subprocess.CalledProcessError(1, 'tlmgr'), None, None, None])
        ci_tex.configure(run)
        self.assertEqual(run.call_count, 6)

    def test_all_timeouts_fail_closed(self):
        run = Mock(side_effect=subprocess.TimeoutExpired('tlmgr', 180))
        with self.assertRaisesRegex(RuntimeError, 'All TeX mirror attempts failed'):
            ci_tex.configure(run)
        self.assertEqual(run.call_count, len(ci_tex.REPOSITORIES))
