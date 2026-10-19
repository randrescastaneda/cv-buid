# cv-buid

An offline Python package and agent workflow for evidence-backed CV profiles.
This is a bounded first scaffold, not an autonomous fact collector.

Install locally with `python3 -m pip install .`. Python 3.11+ is required;
JSON needs no runtime dependencies. YAML is optional with `pip install .[yaml]`.
Quarto, LaTeX, and `pdftotext` are external tools, used only when needed.

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
```

Agent instructions are in [skills/cv-profile/SKILL.md](skills/cv-profile/SKILL.md).
Copy that folder into an agent's skill directory when installing the workflow;
the CLI itself is installed through pip. No global skill configuration is
changed by this package.

`person`, ID-indexed `sources`, and ID-indexed `entries` live in one private
canonical JSON or YAML file. Entries include `kind`, `fields`, `status`,
`evidence`, and optional `public`. Evidence names a source and a locator.
Selections list IDs in section order, independently of the profile and design.
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
