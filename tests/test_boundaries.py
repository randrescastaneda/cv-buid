import copy
import json
import tempfile
import unittest
from pathlib import Path
from cv_buid.cli import inspect_source, public_export, quarto, validate


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((Path(__file__).parents[1] / "examples/profile.json").read_text())

    def test_export_is_explicit_and_contains_no_evidence_or_notes(self):
        exported = public_export(self.profile, {"fields": ["/person/name", "/entries/research-role/fields/title"]})
        self.assertEqual(exported, {"person": {"name": "Alex Example"}, "entries": {"research-role": {"fields": {"title": "Research Analyst"}}}})
        self.assertEqual(public_export(self.profile, {"fields": []}), {})

    def test_export_rejects_whole_objects_private_context_and_unapproved_entries(self):
        for pointer in ["/person", "/entries/research-role/fields", "/entries/research-role/notes", "/sources/user-cv", "/person/*"]:
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                public_export(self.profile, {"fields": [pointer]})
        for status, public in [("proposed", True), ("imported", True), ("confirmed", False)]:
            self.profile["entries"]["research-role"].update(status=status, public=public)
            with self.assertRaises(ValueError):
                public_export(self.profile, {"fields": ["/entries/research-role/fields/title"]})

    def test_conflicted_or_unsupported_facts_cannot_enter_selected_cv(self):
        selection = {"sections": [{"title": "Experience", "entry_ids": ["research-role"]}]}
        for status in ["conflict", "proposed"]:
            self.profile["entries"]["research-role"]["status"] = status
            with self.assertRaises(ValueError):
                quarto(self.profile, selection)
        self.profile["entries"]["research-role"]["evidence"][0]["source_id"] = "missing"
        with self.assertRaises(ValueError):
            validate(self.profile)

    def test_import_preserves_source_and_does_not_execute_latex(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.tex"
            content = b"\\documentclass{resume}\n\\input{companion}\n\\immediate\\write18{touch forbidden}\n"
            source.write_bytes(content)
            record = inspect_source(source, root / "import")
            self.assertEqual(Path(record["source_file"]).read_bytes(), content)
            self.assertEqual(source.read_bytes(), content)
            self.assertEqual(record["companion_references"], ["resume", "companion"])
            self.assertFalse((root / "forbidden").exists())
            self.assertFalse(record["executed"])

    def test_markup_in_profile_is_rendered_as_text(self):
        self.profile["entries"]["research-role"]["fields"]["title"] = "```{python}\nprint('run')\n```"
        output = quarto(self.profile, {"sections": [{"title": "Experience", "entry_ids": ["research-role"]}]})
        self.assertNotIn("```{python}", output)
        self.assertIn("enabled: false", output)

    def test_review_candidates_are_explicit_labeled_and_stay_unapproved(self):
        selection = {"sections": [{"title": "Experience", "entry_ids": ["research-role"]}]}
        entry = self.profile["entries"]["research-role"]
        entry["status"] = "proposed"
        with self.assertRaises(ValueError):
            quarto(self.profile, selection)
        output = quarto(self.profile, selection, review_candidates=True)
        self.assertIn("owner review pending", output)
        self.assertEqual(entry["status"], "proposed")
        self.assertNotIn("owner review", entry["fields"]["title"])
        with self.assertRaises(ValueError):
            public_export(self.profile, {"fields": ["/entries/research-role/fields/title"]})
        entry["status"] = "conflict"
        with self.assertRaises(ValueError):
            quarto(self.profile, selection, review_candidates=True)


if __name__ == "__main__":
    unittest.main()
