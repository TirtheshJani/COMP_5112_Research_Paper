# 11. Open items: paper fixes, TJ's to-do list, open questions

## TJ's to-do list before submission

1. AI-use statement at the end of Section 10: what he checked himself, the course AI policy, the model names, remove the TODO comments.
2. Data statement: public repository URL, or say the repository is submitted with the paper.
3. BibTeX: course rule is Google Scholar exports; entries were checked against Crossref and arXiv. Ask Aaron which he wants.
4. Write the four Assignment 3 summaries (A.2) himself.
5. Remove template leftovers, check the author line.
6. Apply the 11 sentence fixes below.
7. Fix the FFMS page range in refs.bib if still 205 to 221 (should be 205 to 213).
8. Decide the jigsaw scope (file 15) and update Section 8, the conclusion and slides 12 and 14 if it goes ahead.

## The 11 sentence-level fixes found on 11 November

None changes a theorem or a headline number. Full text with suggested wording: `study_guide/paper_fixes_found.md`.
1. "Halves the ceiling" and "the factor of two is exact" hold for odd window sides only; for even u the factor is 2 - 2^(1-N/2) (1.992 at 4 x 4). Abstract, Section 1, Section 4 after Remark 7, Section 10.
2. Section 7: "a single conflicting pair (energy 2)" is one window equal to its own half turn (two pairs).
3. Section 8: 5 x 5 net difference in wrong reads is 183 (193 single-error removed, 10 more multi-error).
4. Section 5: second encoding ran on 56 of the 58 shapes with at most 30 cells (3 x 10 and 5 x 6 not run).
5. Section 5: "both 6 x 6 witnesses" are the same torus.
6. Section 8: same random draws; positions coincide only for tori of the same size.
7. Seed-0 256 x 256 solve is recorded with a 10M budget, not 30M; rerun at 30M identical.
8. Section 9: H1 was half right (large 5 x 5 tori exist).
9. Section 4: cite Burns and Mitchell Lemma 16 for s = 2 rather than "follows by the same argument".
10. Section 9: "orientation alone falls short of its own ceiling" is not established at 3 x 3 (85 to 120).
11. Appendix A: camera tori are passed as arguments to run_camera.py, not listed in the README; interleave scripts need their arguments.

## Stale result files

- results/bounds.md still lists constant-parity divisibility as not proved (it is Lemma 8 now).
- results/exact_3x3_strong_form.md calls the cause local (the paper says closure) and omits 2 x 3 from the mixed-parity list.
- paper/talk/talk_plan.md predates the reviews.

## Open mathematical questions (the paper's call for research)

- 3 x 3 orientation-only maximum: 85 to 120.
- 4 x 4 strong-form maximum: 441 to 8,192 (an exact answer would show whether the cost grows with window size).
- Unrestricted checkerboard interleave: 308 to 512 (or 480 if the study guide remark holds).
- 5 x 5 strong form: 65,536 to 4,193,280.
- Whether extremal tori must have constant parity (would give 4,193,275).
- Distance 3, so a reader can correct rather than reject one misread cell.
- Strip and patch experiments at 4 x 4 (would test the closure explanation).
- Open-patch maxima in their own right: the jigsaw is an open patch, not a torus (file 15).

## Leads not yet in the paper

- Theorem 11 (a) and (b) seem to hold without admissibility, and the caps tighten to 384 (admissible) and 480 (unrestricted) once half-turn-fixed descriptors are dropped. Brute-force checked (0 type-0/type-1 pairs at distance 1; 16 equal pairs, all with both words excluded; 2,400 random unrestricted label pairs). TJ should check the proof before using it.
- No 2- or 4-orientable binary torus with 2 x 2 windows exists (brute force).

## Questions for Aaron (from the prep notes)

AI statement detail and policy; data statement form; Scholar BibTeX or Crossref check; whether the printed Burns and Mitchell chapter is needed to confirm numbering (the open copy was used); final paper due date; and now, the scope and evidence he expects from the jigsaw (file 15).
