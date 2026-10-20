import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cv_buid.quarto_project import draft_qmd, init_project, render_source


class QuartoOwnership(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[1]
        self.profile = json.loads((root / 'examples/profile.json').read_text())
        self.selection = json.loads((root / 'examples/selection.json').read_text())

    def test_seeding_never_replaces_authoritative_source_or_custom_styles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qmd = init_project(self.profile, self.selection, root, 'resume')
            qmd.write_text(qmd.read_text() + '\nOwner-reviewed wording\n')
            (root / 'styles/pdf-header.tex').write_text('customized PDF presentation')
            with self.assertRaises(ValueError): init_project(self.profile, self.selection, root, 'resume')
            init_project(self.profile, self.selection, root, 'full-cv')
            self.assertIn('Owner-reviewed wording', qmd.read_text())
            self.assertEqual((root / 'styles/pdf-header.tex').read_text(), 'customized PDF presentation')
            self.assertTrue((root / 'styles/reference.docx').is_file())

    def test_render_calls_quarto_on_the_existing_qmd_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            qmd = init_project(self.profile, self.selection, tmp, 'resume')
            qmd.write_text(qmd.read_text() + '\nA reviewed sentence.\n')
            before = hashlib.sha256(qmd.read_bytes()).hexdigest()
            with patch('cv_buid.quarto_project.subprocess.run') as run:
                render_source(qmd, 'pdf', 'mac')
                command = run.call_args.args[0]
                self.assertEqual(command[:3], ['quarto','render','resume.qmd'])
                self.assertIn('--no-execute', command)
                self.assertIn('--profile', command)
            self.assertEqual(hashlib.sha256(qmd.read_bytes()).hexdigest(), before)

    def test_qmd_seeding_preserves_fact_gates_and_renders_input_as_text(self):
        original = copy.deepcopy(self.profile)
        self.profile['entries']['research-role']['status'] = 'conflict'
        with self.assertRaises(ValueError): draft_qmd(self.profile, self.selection)
        self.profile = original
        self.profile['entries']['research-role']['fields']['title'] = "```{python}\nprint('execute')\n```"
        source = draft_qmd(self.profile, self.selection)
        self.assertNotIn('```{python}', source)
        self.assertIn('enabled: false', source)
        self.profile['entries']['research-role']['fields']['url'] = 'javascript:alert(1)'
        with self.assertRaises(ValueError): draft_qmd(self.profile, self.selection)
