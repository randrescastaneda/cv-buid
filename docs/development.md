# Contributor reconciliation notes

## Reconciled baseline

This work starts from upstream `cv-buid/main` at
`ff590191df924fbd96bcfc30268f506c31e7f7ed` (v0.1.1).
The existing non-Git local package folder reports v0.3.2 and has later QMD-first
skills, seeding/render helpers and legacy Word code. That folder is preserved
unchanged. The four later generic skills and their references were reconciled
here; routing now names only commands actually present in this prototype.
The unfinished Word backend, presentation assets and extra legacy exporters
were not copied wholesale. Current candidate: `0.2.0.dev0`; not released. The synthetic starter now
reuses the staged renderer port and separate generic PDF/Word presentation.
The original unversioned package and all personal sources remain untouched.
