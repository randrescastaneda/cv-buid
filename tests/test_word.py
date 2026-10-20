import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from cv_buid.cli import select
from cv_buid.word import export_docx

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class WordBoundaries(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((Path(__file__).parents[1] / "examples/profile.json").read_text())
        self.selection = {"name": "Synthetic Resume", "contact_fields": ["website"], "sections": [{"title": "Experience", "entry_ids": ["research-role"]}]}

    def test_variant_overrides_do_not_mutate_or_approve_canonical_facts(self):
        original = copy.deepcopy(self.profile)
        self.selection["field_overrides"] = {"research-role": {"description": "Selected short description"}}
        rows = select(self.profile, self.selection)
        self.assertEqual(rows[0][1][0][1]["description"], "Selected short description")
        self.assertEqual(self.profile, original)
        self.selection["field_overrides"]["research-role"]["status"] = "confirmed"
        with self.assertRaises(ValueError): select(self.profile, self.selection)
        self.selection["field_overrides"] = {"research-role": {"title": "Short title"}}
        self.profile["entries"]["research-role"]["status"] = "proposed"
        with self.assertRaises(ValueError): select(self.profile, self.selection)
        self.assertIn("owner review pending", select(self.profile, self.selection, True)[0][1][0][1]["title"])

    def test_word_has_editable_body_links_right_tabs_and_no_layout_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cv.docx"
            export_docx(self.profile, self.selection, path)
            with zipfile.ZipFile(path) as z:
                body = ET.fromstring(z.read("word/document.xml"))
                styles = ET.fromstring(z.read("word/styles.xml"))
                self.assertFalse(body.findall(".//w:tbl", NS))
                self.assertFalse(body.findall(".//w:txbxContent", NS))
                self.assertFalse(body.findall(".//w:drawing", NS))
                tabs = body.findall(".//w:tab", NS)
                self.assertTrue(any(t.get("{" + NS["w"] + "}val") == "right" for t in tabs))
                self.assertTrue(body.findall(".//w:hyperlink", NS))
                for root in [body, styles]:
                    for tag in ["i", "iCs"]:
                        self.assertTrue(all(e.get("{" + NS["w"] + "}val") in {"0", "false", "off"} for e in root.findall(".//w:" + tag, NS)))

    def test_style_change_preserves_selected_text_and_fact_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            texts = []
            for font in ["Calibri", "Arial"]:
                path = Path(tmp) / (font + ".docx")
                export_docx(self.profile, self.selection, path, {"font": font})
                with zipfile.ZipFile(path) as z:
                    root = ET.fromstring(z.read("word/document.xml"))
                    texts.append([n.text for n in root.findall(".//w:t", NS)])
            self.assertEqual(*texts)
            self.profile["entries"]["research-role"]["status"] = "conflict"
            with self.assertRaises(ValueError): export_docx(self.profile, self.selection, Path(tmp) / "blocked.docx")

    def test_professional_style_rejects_tiny_type_and_unsafe_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cv.docx"
            for style in [{"body_pt": 8}, {"italic": True}]:
                with self.assertRaises(ValueError): export_docx(self.profile, self.selection, out, style)
            self.profile["entries"]["research-role"]["fields"]["url"] = "javascript:alert(1)"
            with self.assertRaises(ValueError): export_docx(self.profile, self.selection, out)


if __name__ == "__main__":
    unittest.main()
