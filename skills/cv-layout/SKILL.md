---
name: cv-layout
description: Apply a reusable, editable CV or resume style while preserving the chosen content variant. Use for Word and PDF typography, spacing, alignment and page layout.
---

## Outcome

Produce a calm, readable document that the owner can edit. Done means the chosen
style is consistent, every page is visually clean, and fitting the layout has
not silently changed the content selection.

## Inputs

Use the owner's visual direction, authoritative QMD variants and format-specific
presentation files. Read [references/quarto-architecture.md](references/quarto-architecture.md)
when configuring the render pipeline.
Read [references/professional-style.md](references/professional-style.md) for the
professional sans-serif preset and the context behind its guidance. Explicit
owner preferences take precedence over a preset or generic career advice.

## Workflow

Use a single column and normal body paragraphs. Keep contacts in the body,
immediately below the name. Use paragraph styles and proper right tab stops
for dates. Do not align dates with spaces or use layout tables, text boxes,
icons, graphics or decorative backgrounds for this preset.

Build hierarchy with type, weight and spacing. Check font availability in the
actual renderer. Prefer Calibri when available; otherwise use a clean sans-serif
such as Arial or Aptos and disclose the fallback. Keep one family when possible.
The preset uses an 18 pt name, 11–12 pt uppercase headings, 10–11 pt body and
9–10 pt contacts. Prefer 11 pt body when space permits. Use roughly 1.9 cm side
margins and moderate vertical margins.

Emphasize employer and institution names above subordinate position labels in
the professional preset. Preserve the same hierarchy in PDF and Word.

Keep three guides: primary information at the left margin, supporting details
and bullets at consistent indents, dates ending at one right tab. Use black on
white, consistent paragraph spacing and restrained bold for recurring categories.
The preset has no italics, including citations. Thin 0.5 pt black dividers are
optional, not a requirement. A name block needs no decorative rule.

Balance comparable bullets without deleting achievements or inventing symmetry.
Use enough line spacing for comfortable reading. Let a full CV gain pages when
necessary. For a strict page target, revisit the selection before shrinking type.
Keep headings with following content and avoid splitting short entries.

QMD contains semantic Markdown and stable entry IDs. `_quarto.yml` owns shared
and per-format settings. PDF uses its LaTeX header/configuration and a small
presentation filter. Optional Word uses `reference-doc` for Word styles and
page properties, including margins, size and headers/footers; its body content
is ignored. Never claim that a DOCX reference styles PDF or equalizes pagination.

Use `cv-buid render SOURCE.qmd --to pdf` as the primary pipeline. Optional
`--to docx` derives content from the same source. Isolate necessary alignment
handling in the filter; do not duplicate prose in format-specific branches.

## Verification

Render the actual QMD through the documented Quarto PDF pipeline. If Word is
retained, render that derived DOCX separately for layout QA. Inspect every page at normal
reading size. Verify the intended font and sizes rather than trusting style
names. After any layout change, render again and use
[../cv-qa/SKILL.md](../cv-qa/SKILL.md).
