# 07. The paper (draft 3)

## Metadata

- Title: Which Way Is Up? Orientation and Error Detection Compete in Binary Position Tori
- Author: Tirthesh Jani, Lakehead University (student number 1374286 on the author line)
- Format: LIPIcs (Overleaf project 12TJ); main file `1374286TJ.tex`; sections in `sections/01` to `11`; Assignment 3 as a course appendix (`Assignment3.tex`)
- Keywords: de Bruijn torus, orientable array, position sensing, window distance, Hamming distance, SAT, local search. CCS: Mathematics of computing, Combinatorics
- Build: `build/paper_draft3.pdf`, 28 pages including the Assignment 3 appendix. Git commit 4db4b9e in `research/paper` on TJ's PC
- Bibliography: refs.bib, 47 entries; refs_check.md logs how each was verified

## Abstract (verbatim)

A camera that reads a small window of a printed binary torus can find its position, unless it does not know which way it is turned or misreads a cell. Orientable arrays solve the first problem and arrays with large window distance solve the second; we ask whether one torus can do both. We call a torus strong-form when its u x u windows and all their quarter turns differ pairwise in at least two cells. We prove that this halves the counting ceiling, to 4,193,280 cells for 5 x 5 windows, and that at the level of window codes the factor of two is exact. Tori lose more. For 3 x 3 windows the largest strong-form torus has exactly 36 cells while orientation alone allows at least 85, a factor of at least 2.36, at least 18 percent beyond the code factor. The extra cost appears when the pattern must close on itself: an open patch can hold more turned windows at distance 2 than any torus (168 against 144), while a strip that wraps in one direction fails early, at a third of the code bound for width four. For 4 x 4 and 5 x 5 windows, local search with equal budgets reaches tori about 9 and 20 times smaller once distance is required, which is consistent with a growing cost but does not prove it; the largest 5 x 5 strong-form torus lies between 65,536 cells (a 256 x 256 torus we construct) and the ceiling. Two algebraic families with simple decoders reach 36 and 280 cells. In a simulated camera with a size-matched control, distance 2 cut wrong position reports at noise level 0.3 from 8.5 to 2.6 percent with the same rate of correct reads. Our two preregistered predictions both failed; the graded claim that the requirements compete, with a cost beyond counting, was formed after seeing the data and is exploratory.

## Sections

1. Introduction: position sensing, Dothraki, the turned reader and the misread cell, the question compose or compete, contributions.
2. Background and related work: de Bruijn tori, orientable sequences and arrays, robust positioning patterns, marker fields; Table 1 compares prior work; "The gap".
3. Definitions: tori, windows, the quarter turn rho with (rho W)[a][b] = W[b][u-1-a], turn sets K_1, K_2, K_4, instances (i, j, k), Definition 1 (s-orientable), Definition 2 (window distance d_s(T); strong form d_4 >= 2; weak form), Lemma 3 (turns of one window differ in an even number of cells), window codes, the compose/compete definition.
4. Ceilings: Lemma 4, Theorem 5, Theorem 6, Table 2, Remark 7, Lemma 8.
5. Exact maxima for 3 x 3 windows: Theorem 9, the SAT encoding, the exhaustive search, the second encoding, the orientation-only control, Proposition 10 (strips and patches), the 3 x 3 parity analogue.
6. Two algebraic families for 5 x 5 windows: 6.1 the XOR family; 6.2 the checkerboard interleave, Theorem 11, Theorem 12, the decoder.
7. Local search for larger windows: method, Table 3, reading.
8. A simulated camera: model, Table 4 with Wilson intervals, single- and multi-error reads, speed.
9. Discussion: the closure hypothesis, what the evidence does and does not show, limitations and deviations from the preregistered plan.
10. Conclusion: answer, open problems, data and code statement, use of AI tools (with TJ TODO comments still in the source).
A. Reproducibility details (commands, seeds, budgets, solver versions).
Course appendix: Assignment 3.

## Numbered results

Definition 1 orientability; Definition 2 window distance; Lemma 3; Lemma 4; Theorem 5 (odd sides); Theorem 6 (even sides); Remark 7; Lemma 8; Theorem 9 (3 x 3 maximum 36); Proposition 10 (strips and patches); Theorem 11 (interleave a, b, c); Theorem 12 (admissible interleave maximum 280). Tables: 1 related work, 2 ceilings, 3 local search, 4 camera. Figures 1 to 6: fig_windows (a window and its turns, on the 6 x 6 XOR torus), fig_exact3x3, fig_interleave, fig_sizes (sizes against ceilings, log scale), fig_search, fig_camera. Figure files in `paper/figures/` as .pdf, .png, .tex with captions.tex.

## Reviews

Two independent reviews by a separate Claude reviewer that did not draft the paper (`paper/review/peer_review_1.md`, `peer_review_2.md`).
- Review 1 (draft 1): 1 critical, 7 major, 12 minor. Critical: Theorem 11 (then numbered as the 280 maximum) was false as stated; it holds only for admissible labels; a 308-cell unrestricted interleave exists. Fixes in draft 2: claim restated with a quantitative compose/compete definition; equal search budgets and five seeds at 4 x 4; size-matched camera control; exhaustive search given its own window bookkeeping; open-strip proposition; every reported torus stored and re-verified; 3 x 3 orientation-only control pushed to 85.
- Review 2 (draft 2): 0 critical, 2 major, 7 minor; grade estimate A- to A. Major A: the strip result had been read as a local obstruction; an open-patch control showed the cost is closure; fixed in draft 3 (patches_3x3_s4_d2.csv, Proposition 10 restated). Major B is for TJ (the AI-use and data statements). Minors fixed.

## For TJ before submission

1. AI-use statement at the end of Section 10: what he checked himself, the course AI policy, model names (Claude Fable 5.2 and Claude Opus 5.5; review 2 could confirm only Opus), remove the TODO comments.
2. Data statement: public repository URL, or say the repository is submitted with the paper.
3. BibTeX from Google Scholar (course rule) versus the Crossref and arXiv checks done.
4. Write the four Assignment 3 summaries himself.
5. Remove leftover template text and check the author line.
6. The 11 sentence-level fixes in file 11.
7. If the jigsaw goes ahead: Section 8 and the conclusion change (file 15).

## Overleaf

`COMP5112_paper_overleaf.zip` holds the source packed for upload; it compiles standalone. Build pattern used here: copy to a temp folder, pdflatex, bibtex, pdflatex twice (plainurl.bst was fetched separately).
