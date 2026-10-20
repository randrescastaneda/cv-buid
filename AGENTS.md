# Career document work

Use the discoverable `cv-profile` skill for profile imports, refreshes, CVs and
resumes. Its router selects `cv-content`, `cv-layout` and `cv-qa` as needed.
The canonical skill sources are in `skills/`; `.agents/skills` links to them.

Keep real career data in the user's private data repository. Package examples,
tests and reusable skills use synthetic identities. Preserve content variants
as authoritative QMD, independently of output-specific presentation files.
The private profile holds evidence; rendering must not overwrite reviewed QMD.
PDF is primary. Optional Word must derive from the same QMD using reference-doc.
Run the actual documented Quarto pipeline and relevant tests before delivery.
