import copy
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

from cv_buid.cli import main
from cv_buid.project import adopt_project, build_project, local_path, read_project


class PrivateProject(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cv project Alex 測試 & space ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'content').mkdir()
        (self.root / 'content/resume.qmd').write_text('# Owner-reviewed prose\n', encoding='utf-8')
        (self.root / 'profile.json').write_text('{"person":{"name":"Alex Example"}}')
        (self.root / 'AGENTS.md').write_text('Owner instructions: preserve the reviewed source.')
        (self.root / 'render.py').write_text(
            'from pathlib import Path\nimport sys\n'
            "Path('invocation.json').write_text(__import__('json').dumps(sys.argv[1:]))\n"
            'raise SystemExit(0)\n')

    def adopt(self, **options):
        return adopt_project(self.root, 'render.py', 'profile.json', ['content/resume.qmd'], **options)

    def test_adoption_dry_run_writes_nothing_and_records_source_ownership(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        plan = self.adopt(dry_run=True)
        self.assertEqual(plan['config']['qmd'], ['content/resume.qmd'])
        self.assertEqual(plan['config']['evidence_profile'], 'profile.json')
        self.assertEqual(plan['config']['instructions'], ['AGENTS.md'])
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_adoption_preserves_reviewed_sources_and_existing_instructions(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        plan = self.adopt()
        self.assertEqual(set(plan['files']), {'cv-buid.json', '.agents/skills/cv-project/SKILL.md'})
        self.assertTrue((self.root / '.agents/skills/cv-project/SKILL.md').is_file())
        for name, data in before.items():
            self.assertEqual((self.root / name).read_bytes(), data)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.adopt()

    def test_preexisting_project_skill_blocks_entire_adoption(self):
        skill = self.root / '.agents/skills/cv-project/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('Private customized agent workflow')
        with self.assertRaises(ValueError):
            self.adopt()
        self.assertFalse((self.root / 'cv-buid.json').exists())
        self.assertEqual(skill.read_text(), 'Private customized agent workflow')

    def test_partial_write_failure_rolls_back_only_new_files(self):
        real_open = Path.open
        def deny_skill(path, *args, **kwargs):
            if path.name == 'SKILL.md':
                raise PermissionError('fixture denial')
            return real_open(path, *args, **kwargs)
        with patch.object(Path, 'open', deny_skill), self.assertRaises(PermissionError):
            self.adopt()
        self.assertFalse((self.root / 'cv-buid.json').exists())
        self.assertEqual((self.root / 'AGENTS.md').read_text(), 'Owner instructions: preserve the reviewed source.')

    def test_portable_path_guards_reject_posix_windows_and_symlink_escapes(self):
        for value in ['/tmp/outside', '../outside', 'content/../../outside', r'C:\outside',
                      'C:/outside', 'C:outside', '//server/share/a', r'content\resume.qmd',
                      'profile.json:stream', '', None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                local_path(self.root, value)
        self.assertEqual(local_path(self.root, 'content/resume.qmd'), self.root / 'content/resume.qmd')
        try:
            (self.root / 'escape').symlink_to(self.root.parent, target_is_directory=True)
        except OSError:
            return  # Creating symlinks may require an unavailable Windows privilege.
        with self.assertRaises(ValueError):
            local_path(self.root, 'escape/outside')

    def test_invalid_configs_fail_before_running_a_project_script(self):
        self.adopt()
        path = self.root / 'cv-buid.json'
        original = json.loads(path.read_text())
        for change in [{'schema_version': True}, {'schema_version': 2}, {'renderer': '../script.py'},
                       {'renderer': 'not-here.py'}, {'qmd': []}, {'qmd': ['profile.json']},
                       {'qmd': ['content/resume.qmd', 'content/resume.qmd']},
                       {'instructions': ['missing.md']}, {'shell_command': 'unsafe'}]:
            with self.subTest(change=change):
                path.write_text(json.dumps(dict(copy.deepcopy(original), **change)))
                with self.assertRaises(ValueError):
                    build_project(self.root)
                self.assertFalse((self.root / 'invocation.json').exists())

    def test_build_forwards_options_without_a_shell_and_preserves_source(self):
        self.adopt()
        source = self.root / 'content/resume.qmd'
        before = source.read_bytes()
        self.assertEqual(build_project(self.root, watch=True, profile='default'), 0)
        self.assertEqual(json.loads((self.root / 'invocation.json').read_text()), ['--watch', '--profile', 'default'])
        self.assertEqual(source.read_bytes(), before)
        for profile in ['bad profile', '--watch', 'test;command']:
            with self.assertRaises(ValueError):
                build_project(self.root, profile=profile)

    def test_build_restores_cwd_arguments_import_path_and_signal_handlers_on_failure(self):
        self.adopt()
        renderer = self.root / 'render.py'
        renderer.write_text('import signal\nsignal.signal(signal.SIGTERM, lambda *_: None)\nraise RuntimeError("fixture error")\n')
        before = (Path.cwd(), sys.argv, sys.path[:], signal.getsignal(signal.SIGTERM))
        with self.assertRaisesRegex(RuntimeError, 'fixture error'):
            build_project(self.root)
        self.assertEqual((Path.cwd(), sys.argv, sys.path[:], signal.getsignal(signal.SIGTERM)), before)

    def test_build_preserves_renderer_exit_codes_including_failure_and_interrupt(self):
        self.adopt()
        for code in [0, 1, 2, 130]:
            (self.root / 'render.py').write_text(f'raise SystemExit({code})\n')
            self.assertEqual(build_project(self.root), code)
        (self.root / 'render.py').write_text('raise SystemExit(2)\n')
        self.assertEqual(main(['build', '--project', str(self.root)]), 2)

    def test_legacy_export_cannot_overwrite_authoritative_qmd(self):
        source = self.root / 'content/resume.qmd'
        before = source.read_bytes()
        examples = Path(__file__).parents[1] / 'examples'
        with self.assertRaises(SystemExit) as error:
            main(['quarto', str(examples / 'profile.json'), str(examples / 'selection.json'), '--out', str(source)])
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
