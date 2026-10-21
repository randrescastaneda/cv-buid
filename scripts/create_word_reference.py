"""Create a new content-free Quarto DOCX reference; never overwrite one."""
import argparse
from pathlib import Path
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_TAB_ALIGNMENT, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

parser = argparse.ArgumentParser()
parser.add_argument('output')
args = parser.parse_args()
path = Path(args.output)
if path.exists(): raise SystemExit('Reference already exists; edit it or choose a new path')
doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.left_margin = section.right_margin = Cm(1.9)
section.top_margin = section.bottom_margin = Cm(1.65)
for style in doc.styles:
    if hasattr(style, 'font'):
        style.font.name = 'Calibri'
        style.font.italic = False
        style.font.bold = False
        style.font.underline = False
        style.font.color.rgb = RGBColor(0, 0, 0)
        fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
        for key in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']: fonts.attrib.pop(qn('w:'+key), None)
        for key in ['ascii','hAnsi','eastAsia','cs']: fonts.set(qn('w:'+key),'Calibri')
normal = doc.styles['Normal']
normal.font.size = Pt(11)
normal.paragraph_format.line_spacing = 1.06
normal.paragraph_format.space_after = Pt(3)
for name in ['Body Text','First Paragraph','Compact','CV Career','CV Degree','CV Contact','CV Support','CV Employer','CV Institution','CV Entry Lead','CV Support Keep','CV Revision']:
    if name not in doc.styles: doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    doc.styles[name].base_style = normal
doc.styles['Title'].font.size = Pt(18)
doc.styles['Title'].font.bold = True
doc.styles['Title'].paragraph_format.space_after = Pt(4)
doc.styles['Title'].paragraph_format.keep_with_next = True
heading = doc.styles['Heading 1']
heading.font.size = Pt(11.5)
heading.font.bold = True
heading.paragraph_format.space_before = Pt(10)
heading.paragraph_format.space_after = Pt(4)
heading.paragraph_format.keep_with_next = True
doc.styles['CV Contact'].font.size = Pt(9.5)
doc.styles['CV Contact'].paragraph_format.space_after = Pt(2)
doc.styles['CV Contact'].paragraph_format.keep_with_next = True
doc.styles['CV Career'].paragraph_format.tab_stops.add_tab_stop(section.page_width-section.left_margin-section.right_margin, WD_TAB_ALIGNMENT.RIGHT)
doc.styles['CV Career'].paragraph_format.keep_with_next = True
doc.styles['CV Degree'].base_style = doc.styles['CV Career']
doc.styles['CV Support'].paragraph_format.left_indent = Cm(0.42)
doc.styles['CV Entry Lead'].paragraph_format.keep_with_next = True
doc.styles['CV Support Keep'].base_style = doc.styles['CV Support']
doc.styles['CV Support Keep'].paragraph_format.keep_with_next = True
for name in ['CV Employer']:
    doc.styles[name].font.size = Pt(11.5)
    doc.styles[name].font.bold = True
    doc.styles[name].paragraph_format.keep_with_next = True
doc.styles['CV Institution'].font.size = Pt(11)
doc.styles['CV Institution'].font.bold = False
revision = doc.styles['CV Revision'].paragraph_format
revision.alignment = WD_ALIGN_PARAGRAPH.RIGHT
revision.space_before = Pt(33)
revision.space_after = Pt(0)
revision.keep_together = True
for name in ['Hyperlink','FollowedHyperlink']:
    if name not in doc.styles: doc.styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
    doc.styles[name].font.color.rgb = RGBColor.from_string('356A80')
    doc.styles[name].font.underline = False
for root in [doc.styles.element, doc.element]:
    for node in list(root.iter(qn('w:pBdr'))): node.getparent().remove(node)
    for node in root.iter():
        if node.tag in {qn('w:i'), qn('w:iCs')}:node.set(qn('w:val'),'0')
doc.core_properties.title = 'Professional career document reference'
doc.core_properties.subject = 'Styles and page properties only; content belongs in QMD'
doc.core_properties.author = ''
doc.core_properties.last_modified_by = ''
path.parent.mkdir(parents=True,exist_ok=True)
doc.save(path)
print(path)
