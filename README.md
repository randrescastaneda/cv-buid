# cv-buid

A small local toolkit for evidence-backed career records and QMD-first CVs.
Python 3.11+ is required. JSON operations have no runtime dependency. Install with
`python3 -m pip install .`; YAML is optional with `.[yaml]`. Quarto and a TeX
installation provide primary PDF rendering. Font and office binaries are not
bundled. The optional `word` extra is needed only for legacy Word export or
rebuilding the default Word reference, not ordinary Quarto rendering.

## Source ownership

- One private profile holds career facts, source evidence and review status.
- Independent QMD files own the resume and full CV wording, inclusion and order.
- `_quarto.yml` and output-specific presentation files own visual style.
- PDFs and optional DOCX files are derived; never edit them as competing sources.

The profile supports what is true; QMD controls what a particular variant says.
A new fact updates the evidence and affected QMD after review. A wording-only
change can stay in QMD. Refreshes propose reviewable diffs instead of regenerating
edited documents from stale JSON. Keep personal content outside this generic repo.

## Draft once then edit QMD

```sh
cv-buid inspect existing.tex --out /private/location/import
cv-buid validate /private/location/profile.json
cv-buid init-quarto examples/profile.json examples/selection.json --directory /tmp/career-project --name resume
cv-buid render /tmp/career-project/resume.qmd --to pdf
cv-buid render /tmp/career-project/resume.qmd --to docx
```

`init-quarto` uses a reviewed JSON selection as a migration seed. It refuses to
overwrite a QMD and preserves existing presentation files. After seeding, edit
QMD directly. It is not regenerated during render. Create a separate QMD with a
separate selection for a longer CV; the variant is independent of style.

The project contains semantic QMD, shared/per-format YAML, a PDF LaTeX header,
a small presentation filter and a content-free Word reference. PDF is primary.
The reference DOCX supplies Word styles and page properties; it does not style
PDF. Both outputs use the same QMD content, without an identical-pagination
promise. Bring any desired Word edits back into QMD before rendering again.

The professional preset uses Calibri, 11 pt body and no italics. Dates use a
right-aligned guide for employment and education. Contacts stay in body text.
Employers are prominent above regular position titles; education instead uses
bold degrees and regular university names. Links use muted blue #356A80. Dated
works link only a supported year. Undated software gets a clear Repository
link until a citation or release year is verified; never invent a date.
The optional `--profile mac` finds Calibri in a standard Microsoft Word Mac
installation. Otherwise use installed fonts or explicitly configure an approved
sans-serif fallback. Check embedded fonts and every final page.

The default reference can be created at a new path with
`python scripts/create_word_reference.py NEW_REFERENCE.docx`. The command
requires python-docx and refuses an overwrite. Customize the resulting reference
directly for Word; customize the PDF header/YAML independently.

## Agent routing

The [profile router](skills/cv-profile/SKILL.md) selects standardized
[content](skills/cv-content/SKILL.md), [layout](skills/cv-layout/SKILL.md) and
[verification](skills/cv-qa/SKILL.md) skills. `.agents/skills` links support
repository discovery with implicit invocation enabled. Copy all four skill
folders together when installing the agent workflow elsewhere. Pip installation
does not change global agent configuration.

[Architecture and official documentation](skills/cv-layout/references/quarto-architecture.md)
explain the output-specific references and source ownership. Run the actual
Quarto pipeline, reconcile output with QMD and evidence, and inspect every page.
No universal ATS certification is claimed.

## Evidence and compatibility

Entries keep stable IDs, source locators, review status and public flags.
Conflicts/proposals are excluded from ordinary selections. Sources suggest facts;
they do not approve impact, leadership or publication. Keep shared authorship and
ongoing-work qualifications. Imports hash/copy sources without executing LaTeX.

`questions`, `diff` and `public-export` support review. Public export uses explicit
scalar allowlists, requires approved/corroborated entry flags, and never publishes.
Default to an empty allowlist until reviewed.

The older `quarto` snapshot adapters and JSON-to-Word `docx` exporter remain for
history/backward compatibility. They are not the current authoring pipeline.
The snapshot CLI refuses to overwrite an existing QMD. Old Quarto Vitae templates
retain their own licences; the new default uses ordinary Quarto/LaTeX presentation.

Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` for package checks.
All examples, tests, skills and presentation assets are generic or synthetic.
