# cv-buid

[Documentation](https://randrescastaneda.github.io/cv-buid/) · [Quick start](https://randrescastaneda.github.io/cv-buid/quick-start.html)

Local tools for private career evidence and QMD-first CV projects. Development version 0.2.0.dev0 extends the upstream v0.1.1 scaffold. It has
no public package release. Python 3.11+ is required; JSON has no runtime dependencies.

Keep career facts/evidence, reviewed QMD, presentation files and custom agent
instructions in your own private repository. The toolkit contains generic code,
synthetic examples and reusable guidance only.

## Start or connect a private workspace

Install from the review wheel with its provided hash-checked requirements file,
or from this checkout in a local virtual environment. See the
[Quick start](docs/quick-start.qmd) for exact Mac and Windows commands.

```sh
cv-buid init /path/to/new-private-cv
cv-buid build --project /path/to/new-private-cv
cv-buid build --project /path/to/new-private-cv --watch
```

The new directory contains fictional Alex Example QMD and evidence, separate PDF
and Word presentation, owner instructions and a project skill. Replace the
fictional content before sharing anything. Init refuses an existing directory.
The shared engine retains staged builds, stale-source checks, failure rollback,
OS locking and child-process cleanup from the proven renderer. No font binaries
or tools are installed by build. The starter uses TeX's Helvetica-compatible
sans-serif family for PDF and an explicit Arial Word reference.

For an existing project, preserve its renderer and reviewed content:

```sh
cv-buid adopt /path/to/private-project --renderer render.py --evidence-profile private/profile.json --qmd private/quarto/resume.qmd --qmd private/quarto/full-cv.qmd --dry-run
```

Review the plan and repeat without --dry-run. Only config and a generated project
skill are added; existing targets are refused. Existing AGENTS.md and QMD are
never overwritten. Script renderers keep their existing layout and output rules.
With renderer=builtin, the config's QMD list selects variants in one Quarto project.

## Reviewable upgrades

```sh
cv-buid upgrade --project /path/to/private-project --out upgrade-plan.json
cv-buid apply-upgrade upgrade-plan.json --project /path/to/private-project
```

Read the plan's diff first. An optional --candidate JSON file proposes config
changes. Application checks original hashes again, keeps backups, and rolls back
on failure. Customized skills are reported for manual review and are not replaced.
QMD, evidence and owner AGENTS.md are never upgrade targets. See
[Project contract](docs/project-contract.qmd) and [release preparation](docs/release-preparation.md).

## Evidence and agents

The private profile supports facts, evidence and review status. Each QMD owns
its variant's reviewed wording, selection and order. Render never regenerates
QMD from historical JSON selections. PDF is primary; optional Word derives from
the same QMD using separate format-specific presentation.

The [profile router](skills/cv-profile/SKILL.md) routes content, layout and QA.
Private project instructions take precedence. Proposed refreshes remain diffs;
sources do not approve achievements. `inspect`, `validate`, `questions`, `diff`
and `public-export` remain available. Public export is explicit allowlisted
staging, never automatic publication. The legacy `quarto` command can seed only
a new draft path and refuses existing files; do not use it on reviewed sources.

Run synthetic package tests with
`PYTHONPATH=src python3 -m unittest discover -s tests -v`. Self-contained installed-command acceptance is in tests/check_starter.py and
runs against the same checksummed wheel on native macOS and Windows CI.


## Documentation preview

The repository now includes a Quarto documentation site in docs/. Build it with
`quarto render docs --to html --no-execute`; preview locally with
`quarto preview docs --host 127.0.0.1 --no-browser`. Generated docs/_site and Quarto caches are ignored. Private PR artifacts contain
a single-file, script-free docs guide plus the interactive HTML pages. Extract
the artifact and open preview-all.html; no localhost server is needed. No public
hosting or deployment workflow is enabled.
See [Quick start](docs/quick-start.qmd) and [Path to v1](docs/v1.qmd).
