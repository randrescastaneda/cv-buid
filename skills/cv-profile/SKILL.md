---
name: cv-profile
description: Maintain evidence-backed private career profiles and route CV or resume work through content, layout and final verification skills. Use for imports, refreshes, tailored selections and document revisions.
---

## Outcome

Maintain career evidence in one private profile and reviewed variant prose in
authoritative QMD files. QMD content and format-specific presentation are separate inputs. Done means requested documents exist,
their facts reconcile with evidence, and every final rendered page was checked.

## Inputs and routing

- Read [../cv-content/SKILL.md](../cv-content/SKILL.md) for importing facts,
  rewriting prose, selecting a resume or full CV, and recording omissions.
- Read [../cv-layout/SKILL.md](../cv-layout/SKILL.md) when formatting documents.
- Read [../cv-qa/SKILL.md](../cv-qa/SKILL.md) before delivery.

These skills are also discovered through `.agents/skills` in this repository.
An installed workflow should copy all four skill folders together. Automatic
invocation remains enabled; the router chooses the relevant work, not a style
based on a filename or page count.

## Profile workflow

Use the installed `cv-buid` CLI. Keep the user's canonical profile and source
evidence outside this package repository. Start from `examples/profile.json`
only for the schema; the example identity is synthetic.

Read existing repository instructions and preserve unrelated branches and files.
Inspect an existing CV with `cv-buid inspect SOURCE --out PRIVATE/import`.
This copies and hashes the input and extracts text; it never compiles imported
LaTeX. Resolve referenced class, bibliography, and included files before
claiming a faithful source render. Preserve unresolved bibliography keys.

Read the substantive source and ask about the target audience, current role,
recent work, contributions, outcome measures, and conflicting facts. Ask only
questions that affect the next draft. Do useful independent work while waiting.

Store stable entry IDs, fields, evidence with source IDs and locators, and a
status. `imported` means a source claim, `corroborated` means additional evidence,
and `confirmed` means the owner resolved the claim. Keep `conflict` entries out
of CV selections. Proposed entries are excluded by default; an expressly
requested review draft can use `quarto --review-candidates`, which labels each
proposal as awaiting owner review without approving or publishing it.
Sources suggest facts; a found page,
repository ownership, or commit count does not establish the user's impact.
Preserve coauthorship. Never invent skills, metrics, leadership, or dates.

Check public identity before importing Scholar, ORCID, OpenAlex, Crossref,
GitHub, or blog data. Prefer author exports and documented APIs to bulk Scholar
scraping. Exclude credentials, irrelevant sensitive details, and private details
about other people. Do not send profile data to a service without authorization.

For refreshes, write a candidate profile separately and show
`cv-buid diff CURRENT CANDIDATE`. Resolve conflicts with the owner before
replacing canonical facts. Select entries for opportunities; tailor wording
within the supported evidence rather than expanding the claims.

For a new draft, seed once with
`cv-buid init-quarto PROFILE SELECTION --directory PROJECT --name resume`.
The initializer refuses to overwrite QMD or customized presentation files.
After the first reviewed draft, edit QMD directly. Profile refreshes propose
changes to QMD; rendering never regenerates reviewed prose from old JSON.

Render the authoritative source with `cv-buid render PROJECT/resume.qmd --to pdf`.
PDF is primary. Optional Word is `--to docx` from that same QMD, using its
`reference-doc`. PDF uses its own LaTeX configuration/header/filter. A Word
reference does not style PDF and does not guarantee identical pagination.
The optional `--profile mac` locates installed Microsoft Word Calibri fonts on
macOS. No fonts are bundled. Verify the actual documented Quarto pipeline.

The old `quarto` snapshot exporter and `docx` JSON-to-Word command remain for
history/backward compatibility; they are not the QMD-first workflow. Do not edit
derived DOCX/PDF as a competing source. Bring any desired output edits into QMD.

The website is a destination for an explicit reviewed subset. Default to an
empty public policy. `cv-buid public-export PROFILE POLICY --out STAGING.json`
exports only exact scalar fields. Entries also require `public: true` and a
corroborated or confirmed status. The command never publishes. Review the
export and website patch within the user's publication authorization.
Creating a draft does not authorize messages, pushes, merges, or deployments.
