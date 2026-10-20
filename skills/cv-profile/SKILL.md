---
name: cv-profile
description: Maintain evidence-backed private career profiles and route CV or resume work through content, layout and final verification skills. Use for imports, refreshes, tailored selections and document revisions.
---

## Outcome

Produce reviewable career documents from one private profile. Content variants
and visual styles are separate inputs. Done means requested documents exist,
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

For editable Word, use `cv-buid docx PROFILE SELECTION --style STYLE.json --out CV.docx`.
It uses ordinary paragraphs and right date tabs. PDF conversion is external;
use a supported local document renderer and inspect the actual DOCX render.
For Quarto, run `cv-buid validate PROFILE`, then
`cv-buid quarto PROFILE SELECTION --out PRIVATE/cv.qmd`.
Render with `quarto render PRIVATE/cv.qmd --to pdf --no-execute`.
`--style hyndman` requires the separately licensed Quarto Vitae extension.
Compare extracted PDF text with selected entries and inspect every rendered
page for clipping, glyph errors, and awkward page breaks. Do not promise ATS
compatibility from appearance alone.

The website is a destination for an explicit reviewed subset. Default to an
empty public policy. `cv-buid public-export PROFILE POLICY --out STAGING.json`
exports only exact scalar fields. Entries also require `public: true` and a
corroborated or confirmed status. The command never publishes. Review the
export and website patch within the user's publication authorization.
Creating a draft does not authorize messages, pushes, merges, or deployments.
