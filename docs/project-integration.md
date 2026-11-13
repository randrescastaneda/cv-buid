## Responsibilities

| Private repository | Reusable toolkit |
| --- | --- |
| Facts, evidence and review status | Import, validate and review-diff tools |
| Authoritative QMD prose/selection | Source-ownership project config and CLI |
| Quarto YAML and PDF/DOCX presentation | Generic workflow and safe adoption |
| Owner instructions and reviewed renderer | Adapter to the renderer contract |
| Generated private outputs | Synthetic examples and tests |

`cv-buid.json` contains schema_version, renderer, evidence_profile, qmd and
instructions. Paths are repository-relative with `/` separators on both OSes.
Absolute paths, Windows drive/UNC paths, parent traversal and symlink escapes
are rejected. Rendering is an explicit execution of a trusted local Python
script, not a sandbox for arbitrary imported repositories.

The QMD list and evidence/instruction paths describe authority for agents.
They are validated as existing files but are not used to generate prose or to
reconfigure a renderer's hard-coded project layout. The existing private
renderer remains the source of its input/output and font policies. This is an
adapter seam, not extraction of a new universal render engine.

The same-process adapter passes only `--watch` and an optional `--profile`,
preserves renderer exit codes, and restores arguments, cwd, import path and
signal handlers after return. No extra shell or wrapper child changes the
renderer's existing OS lock and child-process ownership. Run it from the CLI's
main thread. Restart watch mode after changing config, renderer code or toolkit
installation; source/presentation save watching remains the renderer's job.

Adoption creates only config and a standalone private project skill, refusing
any existing target. It checks the whole plan before writing and rolls back
new files if a write fails; it never rolls back user files. It leaves preexisting
instructions unchanged. There is no `--force`, global installation of skills,
network collector, automatic public export, commit, push or publish operation.

## Development checks

On Mac, from this toolkit checkout:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 tests/check_project_renderer.py /path/to/private-project
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
py -3 -m unittest discover -s tests -v
py -3 tests/check_project_renderer.py C:/path/to/private-project
```

The optional suite requires the existing project's `tests/test_render.py`
fixture contract. It runs that suite through `cv-buid build` using synthetic
temporary sources, not the user's career data. It exercises real save events,
failure/retention/recovery, stale batches, locking and shutdown. The five native
Windows sharing/scratch/process cases run only on Windows; they are skipped on
Mac and must not be reported as Windows passes.

For real-document acceptance, make a disposable private copy **outside this
generic toolkit repo**. Build current sources with its direct renderer, then
through the installed toolkit command. Reconcile PDF text, links, page geometry,
fonts and DOCX text/relationships; inspect every PDF page. Compare source,
evidence and presentation hashes before/after. Never run a destructive test in
the owner's working checkout.

The review branch runs synthetic unit and wheel-install checks on native
Windows and macOS. Full native Windows renderer acceptance remains pending:
run the optional fixture and real-render acceptance on a Windows environment
with a compatible reviewed renderer and licensed fonts. Prior checks of that
renderer alone are supporting history, not proof of the new adapter.
