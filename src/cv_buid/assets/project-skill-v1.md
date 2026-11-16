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
saves. Use --project PATH from another directory. These commands execute the
reviewed renderer named in config, in the same process; inspect unfamiliar
projects before running their scripts. The project renderer owns actual source
and output locations, profile/font checks, locking, retention and watch rules.
Config records source ownership; editing its qmd list does not reconfigure a
project-owned renderer. Check the renderer's own instructions for output paths.

Reconcile final PDF/Word content and hyperlinks with QMD and evidence. Inspect
every PDF page and disclose any unverified Word layout or platform behavior.
Keep personal data and project-specific instructions in this private repo.
Building does not authorize messages, public export, commits, pushes, merges
or website publication. Never install tools or silently substitute fonts.
