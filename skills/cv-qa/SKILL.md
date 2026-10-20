---
name: cv-qa
description: Verify final CV and resume documents against selected facts and their rendered pages. Use before delivering editable Word files and PDFs or after content or layout revisions.
---

## Outcome

Deliver the requested documents with trustworthy claims and readable pages.
Done means the final editable files and PDFs reconcile with their selections,
all pages have been visually inspected, the documented Quarto pipeline has run,
and the delivered bytes are verified.

## Inputs

Use the career evidence profile, authoritative QMD variants, format-specific
configuration/templates/reference files and selection note. Preserve earlier
versions. Confirm that rendering reads existing QMD and does not regenerate it
from stale JSON. Do not validate a parallel renderer in place of the documented
Quarto pipeline, or treat independently edited Word content as authoritative.

## Workflow

1. Validate evidence references and entry status. Exclude unresolved conflicts
   and unapproved proposals. Reconcile wording, dates, degrees, publication
   status, coauthors, scope and ongoing work with the evidence.
2. Check the editable structure: ordinary paragraphs and styles, body contacts,
   consistent indents, proper right date tabs, readable sizes, resolved font,
   working links, and no layout tables, text boxes, columns or graphics in the
   professional preset. Verify no italics are applied or inherited.
3. Run the documented Quarto command on each final QMD and rasterize its
   primary PDF. If optional DOCX is retained, derive it from the same QMD and
   render it separately for QA. Inspect every page for clipping, overlap, missing glyphs,
   orphan headings, awkward breaks, date alignment and balanced whitespace.
   Re-render after changes. Confirm a requested one-page resume is one page.
4. Extract PDF text and compare the approved QMD content, bullets and links
   against both the output and career evidence. Initial migrations also reconcile
   all previously reviewed fields. Check optional DOCX XML/links if delivered.
   Verify published/accepted distinctions and internal notes staying outside
   outward files. Do not claim universal ATS certification.
5. Run relevant package and skill checks. Keep personal data out of generic
   examples, tests and reusable skills. Review a diff and the omission note.
6. Save only within authorized destinations. Verify successful uploads or
   repository writes against final bytes, preserve private visibility and
   version history, and report exact failures. Do not retry an unchanged denied
   route or infer success from tool availability.

## Delivery

Provide primary PDFs with QMD/configuration/reference-file links, optional
Word only if derived and verified, and a concise
description of the revision, selection notes and material limitations. State a
font fallback or remaining blocker clearly. Keep QA screenshots internal unless
the user asked for them. Drafting does not itself authorize external messages,
public publication, merges or website changes.
