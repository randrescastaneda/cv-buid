"""Editable single-column Word output. Conversion and publication are external."""
from __future__ import annotations

import copy
import re
from pathlib import Path

from .cli import select

PROFESSIONAL = {
    "font": "Calibri", "name_pt": 18, "heading_pt": 11.5, "body_pt": 11,
    "contact_pt": 9.5, "side_margin_cm": 1.9, "vertical_margin_cm": 1.65,
    "line_spacing": 1.06, "paragraph_after_pt": 4,
    "heading_before_pt": 11, "heading_after_pt": 5,
    "entry_before_pt": 3, "support_indent_cm": 0.42, "bullet_indent_cm": 0.78,
    "bullet_hanging_cm": 0.34, "italic": False,
}


def export_docx(profile, selection, destination, style=None):
    """Render a content selection with no tables, columns, images or text boxes."""
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import WD_BREAK, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Inches, Pt, RGBColor

    rows = select(profile, selection)
    policy = copy.deepcopy(PROFESSIONAL)
    if style:
        if set(style) - set(policy):
            raise ValueError("Unknown style fields: " + ", ".join(sorted(set(style) - set(policy))))
        policy.update(style)
    if policy["italic"] is not False:
        raise ValueError("The professional style does not use italics")
    if not 10 <= policy["body_pt"] <= 12 or not 9 <= policy["contact_pt"] <= 12:
        raise ValueError("Use readable body and contact sizes; select content before shrinking")

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.left_margin = section.right_margin = Cm(policy["side_margin_cm"])
    section.top_margin = section.bottom_margin = Cm(policy["vertical_margin_cm"])
    width = section.page_width - section.left_margin - section.right_margin
    for s in doc.styles:
        if hasattr(s, "font"):
            s.font.name = policy["font"]
            s.font.color.rgb = RGBColor(0, 0, 0)
            s.font.italic = False
            s.font.bold = False
            s.font.underline = False
            fonts = s.element.get_or_add_rPr().get_or_add_rFonts()
            for key in ["asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"]:
                fonts.attrib.pop(qn("w:" + key), None)
            for key in ["ascii", "hAnsi", "eastAsia", "cs"]:
                fonts.set(qn("w:" + key), policy["font"])
    normal = doc.styles["Normal"]
    normal.font.size = Pt(policy["body_pt"])
    normal.paragraph_format.line_spacing = policy["line_spacing"]
    normal.paragraph_format.space_after = Pt(policy["paragraph_after_pt"])
    normal.paragraph_format.widow_control = True
    for name in ["CV Contact", "CV Support", "CV Bullet", "CV Entry"]:
        doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH).base_style = normal
    doc.styles["Title"].font.size = Pt(policy["name_pt"])
    doc.styles["Title"].font.bold = True
    doc.styles["Title"].paragraph_format.space_after = Pt(4)
    doc.styles["Title"].paragraph_format.keep_with_next = True
    heading = doc.styles["Heading 1"]
    heading.font.size = Pt(policy["heading_pt"])
    heading.font.bold = True
    heading.paragraph_format.space_before = Pt(policy["heading_before_pt"])
    heading.paragraph_format.space_after = Pt(policy["heading_after_pt"])
    heading.paragraph_format.keep_with_next = True
    doc.styles["CV Contact"].font.size = Pt(policy["contact_pt"])
    doc.styles["CV Contact"].paragraph_format.space_after = Pt(2)
    doc.styles["CV Contact"].paragraph_format.keep_with_next = True
    doc.styles["CV Support"].paragraph_format.left_indent = Cm(policy["support_indent_cm"])
    bullet = doc.styles["CV Bullet"].paragraph_format
    bullet.left_indent = Cm(policy["bullet_indent_cm"])
    bullet.first_line_indent = Cm(-policy["bullet_hanging_cm"])
    bullet.space_after = Pt(policy["paragraph_after_pt"])
    entry = doc.styles["CV Entry"].paragraph_format
    entry.space_before = Pt(policy["entry_before_pt"])
    entry.space_after = Pt(1)
    entry.keep_with_next = True

    # Real Word numbering; bullets remain editable and extract in reading order.
    numbering = doc.part.numbering_part.element
    abstract = OxmlElement("w:abstractNum"); abstract.set(qn("w:abstractNumId"), "77")
    level = OxmlElement("w:lvl"); level.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start"); start.set(qn("w:val"), "1"); level.append(start)
    fmt = OxmlElement("w:numFmt"); fmt.set(qn("w:val"), "bullet"); level.append(fmt)
    label = OxmlElement("w:lvlText"); label.set(qn("w:val"), "•"); level.append(label)
    pp = OxmlElement("w:pPr")
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), str(Cm(policy["bullet_indent_cm"]).twips))
    ind.set(qn("w:hanging"), str(Cm(policy["bullet_hanging_cm"]).twips))
    pp.append(ind); level.append(pp)
    abstract.append(level); numbering.append(abstract)
    num = OxmlElement("w:num"); num.set(qn("w:numId"), "77")
    aid = OxmlElement("w:abstractNumId"); aid.set(qn("w:val"), "77"); num.append(aid); numbering.append(num)

    def link(paragraph, label, url, bold=False):
        if not re.fullmatch(r"(?:https://|mailto:|tel:)[^\s<>]+", url):
            raise ValueError("Unsupported link target")
        relation = paragraph.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
        h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), relation)
        r = OxmlElement("w:r"); props = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts")
        for key in ["ascii", "hAnsi", "eastAsia", "cs"]: fonts.set(qn("w:" + key), policy["font"])
        props.append(fonts)
        color = OxmlElement("w:color"); color.set(qn("w:val"), "000000"); props.append(color)
        italic = OxmlElement("w:i"); italic.set(qn("w:val"), "0"); props.append(italic)
        if bold:
            b = OxmlElement("w:b"); props.append(b)
        r.append(props); t = OxmlElement("w:t"); t.text = label; r.append(t); h.append(r); paragraph._p.append(h)

    def lead(title, when="", bold=False, url=None):
        p = doc.add_paragraph(style="CV Entry")
        p.paragraph_format.tab_stops.add_tab_stop(width, WD_TAB_ALIGNMENT.RIGHT)
        if url: link(p, title, url, bold)
        else: p.add_run(title).bold = bold
        if when: p.add_run("\t" + when)
        return p

    person = profile["person"]
    doc.add_paragraph(person["name"], style="Title")
    # Contact information belongs in normal body paragraphs, never a header.
    contact_rows = selection.get("contact_rows") or [selection.get("contact_fields", [])]
    for keys in contact_rows:
        p = doc.add_paragraph(style="CV Contact")
        values = [(k, str(person[k])) for k in keys if person.get(k)]
        for index, (key, value) in enumerate(values):
            if index: p.add_run("  |  ")
            url = "mailto:" + value if key == "email" else "tel:" + value.replace(" ", "") if key == "phone" else value
            link(p, value, url)
    for config, entries in rows:
        heading = doc.add_paragraph(config["title"].upper(), style="Heading 1")
        if config.get("page_break_before"): heading.paragraph_format.page_break_before = True
        last_org = None
        for entry_id, f in entries:
            kind = profile["entries"][entry_id]["kind"]
            title, org, date = (f.get(k, "") for k in ["title", "organization", "when"])
            if kind == "experience":
                employer, _, department = org.partition("|")
                employer = employer.strip(); department = department.strip()
                if employer and employer != last_org:
                    lead(employer)
                last_org = employer
                lead(title, date, bold=True, url=f.get("url"))
                if department: doc.add_paragraph(department, style="CV Support")
            elif kind == "education":
                lead(title, date)
                if org: doc.add_paragraph(org, style="CV Support")
            elif title:
                # Bibliographic dates belong to the citation. Right date tabs
                # are reserved for employment and education, where they scan
                # consistently without breaking long publication titles.
                label = title + (" | " + org if kind == "software" and org else "")
                if date: label += " (" + date + ")"
                p = lead(label)
                if f.get("url"):
                    p.clear(); link(p, label, f["url"])
                if org and kind != "software": doc.add_paragraph(org, style="CV Support")
            if f.get("description"):
                p = doc.add_paragraph(f["description"], style="CV Support" if title else "Normal")
                p.paragraph_format.keep_with_next = False
            for item in f.get("highlights", []):
                p = doc.add_paragraph(str(item), style="CV Bullet")
                p.paragraph_format.left_indent = Cm(policy["bullet_indent_cm"])
                p.paragraph_format.first_line_indent = Cm(-policy["bullet_hanging_cm"])
                n = OxmlElement("w:numPr"); ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0")
                nid = OxmlElement("w:numId"); nid.set(qn("w:val"), "77"); n.extend([ilvl, nid]); p._p.get_or_add_pPr().append(n)
            # Entries with no supporting content must not form a keep-with-next chain.
            if not f.get("description") and not f.get("highlights") and doc.paragraphs:
                doc.paragraphs[-1].paragraph_format.keep_with_next = False
    # Remove unused inherited italic formatting, not just direct body italics.
    for node in doc.styles.element.iter():
        if node.tag in {qn("w:i"), qn("w:iCs")}:
            node.set(qn("w:val"), "0")
    for root in [doc.styles.element, doc.element]:
        for border in list(root.iter(qn("w:pBdr"))):
            border.getparent().remove(border)
    doc.core_properties.title = selection.get("name", "Professional CV")
    doc.core_properties.subject = selection.get("purpose", "Professional experience and qualifications")
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    out = Path(destination); out.parent.mkdir(parents=True, exist_ok=True); doc.save(out)
    return out
