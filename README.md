# cv-buid

An offline Python package and agent workflow for evidence-backed CV profiles.
This is a bounded first scaffold, not an autonomous fact collector.

Install locally with `python3 -m pip install .`. Python 3.11+ is required;
JSON needs no runtime dependencies. YAML is optional with `pip install .[yaml]`.
Editable Word output is optional: `pip install .[word]`.
Quarto, LaTeX, a DOCX-to-PDF converter, and `pdftotext` are external tools,
used only by the selected workflow.

```sh
cv-buid inspect existing.tex --out /private/location/import
cv-buid validate /private/location/profile.json
cv-buid questions /private/location/profile.json
cv-buid diff /private/location/current.json /private/location/candidate.json
cv-buid quarto examples/profile.json examples/selection.json --out /tmp/cv.qmd
quarto render /tmp/cv.qmd --to pdf --no-execute
cv-buid quarto examples/profile.json examples/selection.json --style classic --out /tmp/classic-cv.qmd
quarto render /tmp/classic-cv.qmd --to pdf --no-execute
cv-buid public-export examples/profile.json examples/public-allowlist.json --out /tmp/public-profile.json
cv-buid docx examples/profile.json examples/selection.json --out /tmp/cv.docx
```

The [profile router](skills/cv-profile/SKILL.md) selects the standardized
[content](skills/cv-content/SKILL.md), [layout](skills/cv-layout/SKILL.md) and
[verification](skills/cv-qa/SKILL.md) skills. Repository discovery uses
`.agents/skills` links; each skill explicitly permits implicit invocation.
To install the workflow elsewhere, copy all four folders from `skills/` into
the target agent's skill directory. The CLI is installed through pip; installing
it does not change global agent configuration.

`person`, ID-indexed `sources`, and ID-indexed `entries` live in one private
canonical JSON or YAML file. Entries include `kind`, `fields`, `status`,
`evidence`, and optional `public`. Evidence names a source and a locator.
Selections list IDs in section order, independently of the profile and design.
Resume and full CV are independent content selections, not styles. Optional
`field_overrides` on a selection shorten only display fields; they never alter
canonical facts, evidence, statuses or public flags. Reconcile those wordings
with evidence and record substantial omissions in a separate selection note.
The same selection can be rendered with different style policies.
Proposed entries are excluded by default. For an explicitly requested review
draft, `quarto --review-candidates` labels each proposed entry as awaiting owner
review without changing its status. Conflicts remain blocked in either mode,
and the public export rules remain unchanged.
The schema is deliberately small and currently validated by Python rather than
a published JSON Schema. Field-level provenance, deduplication across research
versions, and an interactive interview are follow-up work.

The import command preserves and hashes local bytes but only extracts text.
An agent performs the semantic import and records missing evidence. Refreshes
are candidate profiles and deterministic diffs; there is no automatic approval,
network sync, scheduler, or publication.

Public exports require exact scalar JSON pointers. No object, wildcard,
source, note, or review-context exports are accepted. A publishable entry needs
an explicit public flag and corroborated or confirmed status. Keep policies
empty until the owner reviews their contents. Export is staging only; the
website adapter and publication step are intentionally separate.

The Word adapter uses ordinary editable paragraphs, body contacts, real bullets
and right tabs for employment/education dates. Bibliographic dates stay with
their citations. It has no layout tables, columns, graphics or text boxes.
Its professional preset uses Calibri, 11 pt body, 18 pt name, uppercase headings,
black text and no italics. Verify the actual installed/rendered font; explicitly
choose Arial or another approved sans-serif fallback if necessary.

An optional JSON file controls appearance without selecting content:

```json
{"font": "Arial", "body_pt": 11, "heading_pt": 11.5, "contact_pt": 9.5}
```

Pass it with `cv-buid docx PROFILE SELECTION --style STYLE.json --out CV.docx`.
The exporter rejects tiny body text and italics for this preset. It does not
convert to PDF or certify ATS behavior. Render the actual DOCX with a supported
local document workflow, inspect every page, and verify text, links, dates and
typography. Fonts and office runtimes are not bundled or redistributed.

The plain adapter delegates typography to Quarto. The `classic` adapter uses
Quarto's standard PDF pipeline with compact serif typography, a centered name,
uppercase section rules, and grouped employers or institutions with dates on
the right. It contains no personal data or copied third-party CV class.
The `hyndman` adapter emits
the shared Quarto Vitae entry syntax; install its extension separately.
Do not assume MIT covers templates: Quarto Vitae Hyndman is CC BY-SA 4.0,
and other templates have their own terms. No template is bundled in this
package. RenderCV is an alternate YAML/PDF backend with an MIT-licensed CLI
and an official agent skill; no RenderCV adapter is implemented yet.

Run checks with `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
All packaged examples and tests use synthetic identities. Keep real data,
imports, generated CVs, and credentials out of package history.
