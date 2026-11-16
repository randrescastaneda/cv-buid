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

The toolkit keeps these reusable instructions in skills/. Adoption writes a
standalone project skill inside the private repository; existing private
instructions remain authoritative. Copy all four reusable skill folders together
if installing them separately. Choose content/layout/QA by the requested work.

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

For a new independent private repository, cv-buid init NEW_DIRECTORY creates
fictional starter files and refuses existing directories. Replace all examples
through the evidence/import/interview workflow before sharing a real CV. Builtin
rendering uses the shared staged engine; existing script renderers remain valid.

For an existing private repository, read its cv-buid.json and project instructions.
Use cv-buid build --project PROJECT, optionally --watch, to run its reviewed
local renderer. Config names evidence and authoritative QMD; it never selects
or rewrites prose. The renderer owns actual input/output locations, style,
locking and last-successful-output retention. Do not assume editing the metadata
list relocates sources in a project-owned renderer.

Adoption is explicit: cv-buid adopt PROJECT --renderer render.py
--evidence-profile PRIVATE_PROFILE --qmd QMD (repeat --qmd for each variant).
Preview with --dry-run. This creates config and a private project skill, never
replaces AGENTS.md, and refuses existing adoption targets. Inspect unfamiliar
renderer scripts before executing them. No global agent configuration changes.

For a first migration only, the legacy quarto PROFILE SELECTION --out NEW.qmd
may seed a new file. It refuses existing output; it is not a render step and
must never regenerate reviewed QMD. Newer unreconciled local init-quarto/render
commands are not part of this prototype. Do not use JSON-to-Word as a competing
content source. PDF and optional Word derive from the same authoritative QMD;
PDF presentation and DOCX reference files are independent. Verify the project's
actual documented pipeline and every final page.

The website is a destination for an explicit reviewed subset. Default to an
empty public policy. `cv-buid public-export PROFILE POLICY --out STAGING.json`
exports only exact scalar fields. Entries also require `public: true` and a
corroborated or confirmed status. The command never publishes. Review the
export and website patch within the user's publication authorization.
Creating a draft does not authorize messages, pushes, merges, or deployments.

Plan upgrades with cv-buid upgrade --out PLAN.json, review the diff, then use
apply-upgrade. Only config and recognized generated skills are eligible; preserve
custom instructions and never treat QMD/evidence as upgrade targets.
