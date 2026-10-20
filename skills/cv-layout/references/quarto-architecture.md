# QMD authority and format-specific presentation

The career profile is the private source of evidence and factual history.
Reviewed QMD files own each variant's wording, selection and order. PDF and
optional DOCX are derived outputs. An edit made in Word must return to QMD before
regeneration. A profile refresh proposes a QMD diff rather than replacing it.

Use one semantic Markdown body for both formats. Stable entry IDs link variant
paragraphs to the evidence map. Presentation classes can be interpreted by a
small Lua filter, keeping prose out of format-specific branches.

- [Quarto shared metadata](https://quarto.org/docs/projects/quarto-projects.html#shared-metadata)
  supports shared and per-format configuration in `_quarto.yml`.
- [Quarto Word templates](https://quarto.org/docs/output-formats/ms-word-templates.html)
  and [Pandoc reference-doc](https://pandoc.org/MANUAL.html#option--reference-doc)
  define Word styles and document properties. Page size, margins and headers/
  footers matter; the reference's body is not imported as document content.
- [Quarto PDF rendering](https://quarto.org/docs/reference/formats/pdf.html#rendering)
  uses PDF-specific settings and a TeX engine in this implementation. The shipped
  `pdf-header.tex` handles typography; it is independent of `reference.docx`.
- [Quarto conditional content](https://quarto.org/docs/authoring/conditional.html)
  can isolate unavoidable format differences. Prefer presentation handling in
  a filter rather than maintaining separate copies of career statements.

Matching content and coordinated styles are realistic. Identical pagination is
not promised across TeX and Word. Verify page counts and every final page in
both retained formats. PDF is the stable primary delivery. The one-page resume
must be one page in its primary PDF; report optional Word pagination separately.

`init-quarto` seeds a project once. Existing QMD and customized styles are never
overwritten. `render` calls Quarto on that existing QMD without content
regeneration. The optional mac profile locates installed Word Calibri files;
it distributes no fonts. On other systems, use installed family names or
configure an approved sans-serif fallback in PDF settings and Word reference.
