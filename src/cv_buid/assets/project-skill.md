---
name: cv-project
description: Edit and build this private CV project with its reviewed QMD sources, evidence profile and local renderer through cv-buid.
---

Read cv-buid.json from the repository root, then the files named in instructions.
Private project instructions and explicit owner requests take precedence over
generic toolkit guidance. Preserve unrelated work and existing AGENTS.md.

The evidence_profile path supports career facts, evidence and review status.
The qmd paths own each variant's reviewed wording, selection and order. Read
both before proposing factual changes. A wording-only edit can stay in QMD.
Never regenerate reviewed QMD from historical JSON selections. Refresh evidence
as a separate candidate and show a diff; sources do not approve claims.

Edit the requested QMD variant directly. Leave Quarto configuration, PDF
presentation files and DOCX reference files alone unless style changes are
requested. PDF is primary; Word is derived from the same QMD, with independent
presentation and potentially different pagination.

From the root run cv-buid build; cv-buid build --watch optionally rebuilds on
saves. Use --project PATH from another directory. These commands use the configured builtin engine or execute a reviewed
project script in the same process. Inspect unfamiliar project scripts before
running them. The project renderer owns actual source
and output locations, profile/font checks, locking, retention and watch rules.
With renderer=builtin, qmd selects files in one Quarto project. With a
project-owned script, qmd records source ownership and does not reconfigure it. Check the renderer's own instructions for output paths.

Reconcile final PDF/Word content and hyperlinks with QMD and evidence. Inspect
every PDF page and disclose any unverified Word layout or platform behavior.
Keep personal data and project-specific instructions in this private repo.
Building does not authorize messages, public export, commits, pushes, merges
or website publication. Never install tools or silently substitute fonts.

For toolkit upgrades, create a cv-buid upgrade plan and review its diff before
apply-upgrade. Stale plans are rejected; customized skills require manual review.
Never overwrite QMD, evidence or AGENTS.md during an upgrade.
