# 16. Tooling, skills and lessons

## Environment

- Two machines. The cloud workspace (Linux, Python, LaTeX, numba, PySAT) where most computing ran, and TJ's PC reached through the Claude desktop app's device bridge (connected folder COMP-5112-Research-Methodology, mounted at $HOME/mnt/COMP-5112-Research-Methodology). The bridge is only present while the desktop app is open and online.
- Device shell limits: each call is a fresh bash with at most 180 s; background processes are killed when the call ends (even with setsid). Long jobs on the PC must be cut into chunks under about 170 s; long searches ran in the cloud.
- Deleting in TJ's folders is off by default; ask for permission only when needed, and delete only what is necessary. git needs delete permission for its lock files.
- Moving files between machines: stage named files from the PC (never wildcard-copy the staged uploads folder; it holds stale copies), commit outputs back with device_commit_files, or move tarballs as base64 when needed. Read-only files on the PC may need chmod u+w before overwriting.
- The cloud shell has no rsync; use cp and find.
- Claude Science on TJ's Windows PC (native app with WSL as an SSH host for GPU jobs) was set up in October for long runs; not used in this chat.

## Artifacts

- Call list_types before making a new artifact. Types seen: Data, Design, Design System, Docs, Sheets, Slides, Whiteboard.
- Docs cannot typeset inline mathematics (formulas go in latex code blocks only), so the study guide was a LaTeX PDF and the reading list a Doc.
- Slides artifact: no sub tags in slide HTML; assets must sit under /mnt/user-data/outputs/artifacts/<slug>/assets/ to upload.

## LaTeX

- Paper builds: copy to a temp folder, pdflatex, bibtex, pdflatex twice; plainurl.bst fetched separately.
- Study guide: one shared preamble, parts checked one at a time with check_part.sh (compiles a part alone, fails on em dashes). Regex edits of captions are risky; rebuild from per-figure files instead.

## Skills used in this project

dispatching-parallel-agents (literature fan-out, Phase 4 drafting, the 11 November deliverables), literature-review, research-lookup, paper-search, citation-check, citation-management, scientific-brainstorming, hypothesis-generation, what-if-oracle, grill-with-docs, scientific-critical-thinking, peer-review, scientific-writing, venue-templates (LIPIcs), scientific-visualization, scientific-slides, karpathy-guidelines, test-driven-development, systematic-debugging, verification-before-completion, avoid-ai-writing, writing-plans, executing-plans.

## Lessons worth keeping

- Every number in the paper must trace to a results file with a commit; agents' reports are claims to verify, not facts.
- Independent checks catch real errors: the independent reviewer found the false theorem; the independent DFS confirmed SAT; the witness verifier shares no code with the search.
- Controls change readings: the open-patch control overturned the "local obstruction" story; the size-matched camera pair made the error-rate comparison fair.
- Write predictions down before experiments; report plainly when they fail.
- Keep a talk plan in sync with the paper or delete it; a stale plan nearly put pre-review numbers into the G2 notes.
- Check the exact claim, not the headline: "the factor of two is exact" was true only for odd window sides.
