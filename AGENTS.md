# Reusable private-career toolkit

Read skills/cv-profile/SKILL.md for career work; it routes content, layout and QA.
Private facts, sources, reviewed QMD and custom agent instructions stay in the
user repository. All examples/tests/reusable skills here must be synthetic.
Preserve existing user instructions and QMD; adoption adds files without overwrite.
The script adapter executes the reviewed project renderer in the same process.
New synthetic starters use the shared engine ported from that proven renderer;
keep its lock/watch/process/retention logic centralized and tested, rather than
copying a renderer into every new workspace. Existing private renderers stay intact.
Run package tests and the optional project-renderer acceptance suite. Never claim
native Windows verification from a Mac run. No commit/push/publication without
separate authorization. Keep release and deployment decisions separate from review-branch publication.
