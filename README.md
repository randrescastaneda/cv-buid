# cv-buid

Local tools for private career evidence and QMD-first CV projects. Development version 0.1.2.dev0 extends the upstream v0.1.1 scaffold. It has
no public package release. Python 3.11+ is required; JSON has no runtime dependencies.

Keep career facts/evidence, reviewed QMD, presentation files and custom agent
instructions in your own private repository. The toolkit contains generic code,
synthetic examples and reusable guidance only.

## Connect an existing project

Install this checkout locally with `python3 -m pip install .`; on Windows use
`py -3 -m pip install .`. This does not install Quarto, fonts or TeX, and it does
not change global agent configuration. Inspect the project's renderer first.

```sh
cv-buid adopt /path/to/private-project --renderer render.py --evidence-profile private/profile.json --qmd private/quarto/resume.qmd --qmd private/quarto/full-cv.qmd --dry-run
```

Review the plan, then repeat without `--dry-run`. Adoption adds `cv-buid.json`
and `.agents/skills/cv-project/SKILL.md`. It refuses existing targets and never
replaces QMD, evidence, presentation files or `AGENTS.md`.

From the private repository root:

```sh
cv-buid build
cv-buid build --watch
```

The installed command is the same on Mac and Windows. Alternatively use
`python3 -m cv_buid.cli build` on Mac or `py -3 -m cv_buid.cli build` on Windows.
From another directory append `--project /path/to/private-project`. Stop watch
mode with Ctrl+C. `--profile NAME` is passed to the existing renderer.

The prototype delegates to the project-owned renderer **in the same process**.
That renderer owns Quarto commands, actual input/output locations, font/profile
checks, locking, output retention and watch behavior. Config records source
ownership; changing its QMD list does not relocate inputs in an existing script.
The supported renderer contract is a trusted Python entry point accepting
`--watch` and `--profile NAME`, using exit codes 0/1/2/130. Existing direct
renderer commands keep working. There is no duplicate renderer or bundled font.

[Integration details and reconciliation](docs/project-integration.md) explain
the boundary, tests and remaining Windows verification.

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
`PYTHONPATH=src python3 -m unittest discover -s tests -v`. Optional renderer
integration tests and Windows commands are documented in the linked guide.


## Documentation preview

The repository now includes a Quarto documentation site in docs/. Build it with
`quarto render docs --to html --no-execute`; preview locally with
`quarto preview docs --host 127.0.0.1 --no-browser`. Generated docs/_site and
Quarto caches are ignored. No hosting or publication workflow is enabled.
See [Quick start](docs/quick-start.qmd) and [Path to v1](docs/v1.qmd).
