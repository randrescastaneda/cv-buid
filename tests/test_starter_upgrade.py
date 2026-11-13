import copy
import json
from importlib.resources import files
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cv_buid.cli import main, validate
from cv_buid.project import read_project, build_project
from cv_buid.starter import init_project
from cv_buid.upgrade import plan_upgrade, apply_upgrade


class StarterAndUpgrade(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='starter Alex 測試 ')
        self.addCleanup(self.temp.cleanup)
        self.root = init_project(Path(self.temp.name) / 'private workspace')

    def test_starter_is_synthetic_complete_and_refuses_existing_directories(self):
        root, config = read_project(self.root)
        self.assertEqual(config['renderer'], 'builtin')
        validate(json.loads((root / 'private/profile.json').read_text()))
        self.assertIn('Alex Example', (root / 'private/quarto/resume.qmd').read_text())
        self.assertTrue((root / '.gitignore').is_file())
        before = (root / 'AGENTS.md').read_bytes()
        with self.assertRaises(FileExistsError): init_project(root)
        self.assertEqual(before, (root / 'AGENTS.md').read_bytes())

    def test_builtin_dispatch_uses_existing_qmd_without_regeneration(self):
        before = (self.root / 'private/quarto/resume.qmd').read_bytes()
        with patch('cv_buid.engine.run', return_value=0) as run:
            self.assertEqual(build_project(self.root, watch=True), 0)
            self.assertEqual(run.call_args.args[2], ['resume', 'full-cv'])
            self.assertEqual(run.call_args.args[3], ['--watch'])
        self.assertEqual(before, (self.root / 'private/quarto/resume.qmd').read_bytes())

    def test_upgrade_is_a_noop_for_current_starter(self):
        plan = plan_upgrade(self.root)
        self.assertEqual(plan['changes'], [])
        self.assertEqual(apply_upgrade(self.root, plan)['changed'], [])

    def old_skill(self):
        path = self.root / '.agents/skills/cv-project/SKILL.md'
        path.write_bytes(files('cv_buid').joinpath('assets/project-skill-v1.md').read_bytes())
        return path

    def test_generated_skill_upgrade_has_diff_backup_and_preserves_qmd_instructions(self):
        skill = self.old_skill();old = skill.read_bytes()
        protected = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file() and p != skill}
        plan = plan_upgrade(self.root)
        self.assertEqual(plan['changes'][0]['path'], '.agents/skills/cv-project/SKILL.md')
        self.assertTrue(plan['changes'][0]['diff'])
        result = apply_upgrade(self.root, plan)
        self.assertEqual((Path(result['backup']) / '.agents/skills/cv-project/SKILL.md').read_bytes(), old)
        for name, data in protected.items(): self.assertEqual((self.root / name).read_bytes(), data)
        self.assertEqual(plan_upgrade(self.root)['changes'], [])

    def test_crlf_checkout_and_generated_skills_upgrade_consistently(self):
        assets = Path(self.temp.name) / 'crlf package' / 'assets'
        assets.mkdir(parents=True)
        for name in ['project-skill.md', 'project-skill-v1.md']:
            data = files('cv_buid').joinpath('assets/' + name).read_bytes().replace(b'\r\n', b'\n')
            (assets / name).write_bytes(data.replace(b'\n', b'\r\n'))
        for crlf in [False, True]:
            skill = self.old_skill()
            data = skill.read_bytes().replace(b'\r\n', b'\n')
            skill.write_bytes(data.replace(b'\n', b'\r\n') if crlf else data)
            with patch('cv_buid.upgrade.files', return_value=assets.parent):
                plan = plan_upgrade(self.root)
                apply_upgrade(self.root, plan)
                self.assertNotIn(b'\r\n', skill.read_bytes())
                self.assertEqual(plan_upgrade(self.root)['changes'], [])

    def test_customized_skill_is_never_overwritten(self):
        skill = self.old_skill();skill.write_text('Custom owner instructions')
        plan = plan_upgrade(self.root)
        self.assertEqual(plan['manual_review'], ['.agents/skills/cv-project/SKILL.md'])
        apply_upgrade(self.root, plan)
        self.assertEqual(skill.read_text(), 'Custom owner instructions')

    def test_stale_and_tampered_plans_are_rejected(self):
        skill = self.old_skill();plan = plan_upgrade(self.root)
        skill.write_text('New user edit')
        with self.assertRaisesRegex(ValueError, 'Stale'): apply_upgrade(self.root, plan)
        self.assertEqual(skill.read_text(), 'New user edit')
        skill = self.old_skill();plan = plan_upgrade(self.root)
        bad = copy.deepcopy(plan);bad['changes'][0]['path'] = 'private/quarto/resume.qmd'
        with self.assertRaises(ValueError): apply_upgrade(self.root, bad)
        bad = copy.deepcopy(plan);bad['changes'][0]['after'] += 'tampered'
        with self.assertRaises(ValueError): apply_upgrade(self.root, bad)

    def test_apply_rejects_a_forged_plan_for_custom_instructions(self):
        skill = self.old_skill(); plan = plan_upgrade(self.root)
        skill.write_text('Custom instructions')
        import hashlib
        plan['changes'][0]['before_sha256'] = hashlib.sha256(skill.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'Customized'):
            apply_upgrade(self.root, plan)
        self.assertEqual(skill.read_text(), 'Custom instructions')

    def test_interrupt_after_atomic_replace_restores_original(self):
        skill = self.old_skill(); before = skill.read_bytes(); plan = plan_upgrade(self.root)
        import os
        real = os.replace; calls = []
        def interrupt(source, target):
            real(source, target); calls.append(target)
            if len(calls) == 1: raise KeyboardInterrupt
        with patch('cv_buid.upgrade.os.replace', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            apply_upgrade(self.root, plan)
        self.assertEqual(skill.read_bytes(), before)

    def test_config_candidate_requires_review_and_keeps_paths_inside_project(self):
        path = self.root / 'candidate.json'
        config = json.loads((self.root / 'cv-buid.json').read_text())
        config['instructions'] = []
        path.write_text(json.dumps(config))
        plan = plan_upgrade(self.root, path)
        self.assertEqual(plan['changes'][0]['path'], 'cv-buid.json')
        self.assertEqual(read_project(self.root)[1]['instructions'], ['AGENTS.md'])
        apply_upgrade(self.root, plan)
        self.assertEqual(read_project(self.root)[1]['instructions'], [])
        config['evidence_profile'] = '../outside.json';path.write_text(json.dumps(config))
        with self.assertRaises(ValueError): plan_upgrade(self.root, path)

    def test_partial_apply_rolls_back_and_keeps_backups(self):
        skill = self.old_skill()
        cfg = self.root / 'cv-buid.json';original = cfg.read_bytes();cfg.write_text(json.dumps(json.loads(original)))
        plan = plan_upgrade(self.root)
        import os
        replace = os.replace
        calls = []
        def fail_second(source, target):
            calls.append(target)
            if len(calls) == 2: raise PermissionError('fixture lock')
            return replace(source, target)
        before = {p: p.read_bytes() for p in [skill, cfg]}
        with patch('cv_buid.upgrade.os.replace', side_effect=fail_second), self.assertRaises(PermissionError):
            apply_upgrade(self.root, plan)
        for p, data in before.items(): self.assertEqual(p.read_bytes(), data)
        self.assertTrue(list((self.root / '.cv-buid-upgrades').rglob('SKILL.md')))


if __name__ == '__main__': unittest.main()
