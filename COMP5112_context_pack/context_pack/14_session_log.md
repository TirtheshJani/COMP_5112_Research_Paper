# 14. Session log: what happened in this chat

This chat ran from 6 to 11 November 2026 (Toronto time). TJ's requests are paraphrased closely; decisions and corrections are recorded as they happened.

## 6 November: setup and plan

- TJ shared the project and his skills list, and asked which model was best for the task.
- The research plan was written (project doc claude/COMP5112_Orientable_Torus_Research_Plan_06Nov2026.md): goal, four phases, tasks 1 to 13, sign-off gates, deadlines, risks. Working folders on TJ's PC were set up (research/notes, research/otorus).

## 7 November: Phase 1, literature

- "Run Phase 1 now": five literature agents in parallel, citation-check, synthesis with a gap table and threats to novelty.
- TJ asked whether the folder he had granted (about 180 PDFs) had been checked; three triage passes over the course PDFs followed.
- TJ asked to close three checks before Phase 2 and asked whether The Craft of Research was being followed. The three threat checks (HP patent, Garrido-Jurado, Lloyd and Burns) were done, and the plan was mapped to 5th-edition sections. Verdict: the gap is real (file 04).

## 9 November: Phase 2, statement

- "Start Phase 2 now using Fable." Brainstorm, candidates A to C, hypotheses H1 and H2, a what-if oracle, the decision trigger.
- TJ asked how Reachy Mini could be used. After discussion he decided it was better left out in favour of a deeper statement with code, simulation and a combinatorial approach ("yes"). Statement v1.1 written.

## 9 November: Phase 3, experiments

- "Continue on to Phase 3 with all necessary skills; shortlist the skills first; if Fable runs out move to Opus 5.5 at max", then "continue with Opus max".
- Built the otorus library with tests (TDD), ceilings, exact 3 x 3 by SAT and exhaustive search, XOR and interleave families, local search, decoder, simulated camera, witness verification. Results committed in research/results (Phase 3 close-out f0f7561). Project doc claude/COMP5112_Phase3_Results_09Nov2026.md.

## 9 to 10 November: Phase 4, paper

- "Start Phase 4, use dispatching-parallel-agents and avoid-ai-writing." Draft 1 of the paper (LIPIcs, from the Overleaf 12TJ project), figures, related work, bibliography.
- Peer review 1 (independent reviewer): Theorem 11 (280 maximum) false as stated; fixed by restricting to admissible labels; new experiments (equal budgets, five seeds at 4 x 4, size-matched camera control, independent DFS bookkeeping, 3 x 3 control to 85, every torus stored). Draft 2.
- Peer review 2: the strip result had been misread as a local obstruction; the open-patch control showed closure; Proposition 10 restated. Draft 3 (28 pages).
- Slides deck (14 slides) built as a Slides artifact. Research statement v2 written. Everything synced to TJ's PC and committed (otorus 8194250, results 1f27d18, paper 4db4b9e). Project docs v2 statement and Phase 4 status.

## 11 November: study guide, reading list, G2 notes, zip

- 11:10, TJ asked for a zip of everything, a reading list, an in-depth explainer of every symbol, definition, theorem, hypothesis, derivation and pseudocode with worked examples to write by hand, and G2 Conversate prep notes for his meeting with Aaron, using parallel agents.
- Seven agents ran in parallel (five study-guide parts, reading list, G2 notes); two reviewers rechecked the guide. Findings fed into 11 paper fixes (file 11).
- 12:07, TJ asked for the G2 prep notes first; they were delivered at once, then the study guide PDF, the paper fixes list and the zip. The reading list was published as a Docs artifact. Project doc claude/COMP5112_Study_Guide_and_Meeting_Prep_11Nov2026.md saved.
- 12:23, TJ asked for a summary of the poster process and how the research question came about; answered from the poster pack and Assignment 3 (files 02 and 03).
- 16:32, after meeting Aaron: Aaron suggested a Reachy Mini companion for a two-sided jigsaw puzzle with a binary de Bruijn-style grid on the back. Assessment given: strong fit; it turns the simulated camera into a physical test; challenges are continuous rotation, piece shape, camera limits and mirroring; asked whether it was meant for this paper or a follow-on.
- 16:40, TJ: it is for this research methods paper and presentation; if doable, plan it; first gather all context into structured markdown files (this pack).

## Errors made and fixed along the way

- Theorem 11 as first stated was false (reviewer); restricted to admissible labels; the 308-cell counterexample reported.
- Strips misread as a local obstruction (review 2); open-patch control added; restated as closure.
- The exhaustive search first shared the SAT code's instance list; rewritten with independent turned_cells; reran with identical results.
- Witness count mismatch between cloud (92) and PC; synced; all 136 stored and verified.
- Background processes on the PC were killed after each device_bash call; device jobs were run in chunks under 170 s and the 5 x 5 runs in the cloud.
- A wildcard copy from the staged uploads folder brought stale exact_3x3_strong_form.md and bounds_5x5.md into the cloud; restored from the PC; lesson: copy only explicitly named staged files.
- A regex caption replacement mangled captions.tex; rebuilt from the per-figure files.
- make_figures.py had hard-coded asserts (81, 65,536 of 1,048,576); updated.
- tar overwrite failed on read-only paper files on the PC; chmod then re-extract.
- The talk_plan.md numbers are pre-review; the G2 notes were corrected to describe the actual 14-slide deck.
- Study guide slips (16) fixed by the two reviewers; first-person wording removed; a figure number fixed (the misread illustration is the paper's Figure 2).
