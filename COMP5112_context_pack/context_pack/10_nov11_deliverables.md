# 10. Deliverables made on 11 November

Request (TJ, 11:10): put everything in a zip, create a reading list, create a document explaining the paper with all the math, pseudocode, theorems, hypotheses and definitions broken down step by step with worked examples so he can write it by hand and understand every derivation and symbol, and create Even Realities G2 Conversate prep notes for his meeting with Aaron; use parallel agents.

## Study guide (`study_guide/Which_Way_Is_Up_Study_Guide.pdf`, 84 pages, LaTeX)

Typeset PDF rather than a Docs artifact because Docs cannot typeset inline mathematics. Seven agents ran in parallel (five guide parts, the reading list, the G2 notes); two further independent reviewers rechecked every proof step and number and fixed 16 small slips (an exercise with two arrays swapped, a vertex-degree claim, cost lines, a decoder line numbering, label sequences, a SAT clause count).

Structure (section numbers equal part numbers):
- How to use this guide (unnumbered): the coloured boxes (In plain words, Symbols used here, Write it out by hand, Easy to get wrong, Where this number comes from), a study method, the paper on one page, a map of results.
- 1 Objects, symbols and definitions: a symbol glossary, tori and windows, the quarter turn and its cycle structure, Definitions 1 and 2, the error-detection proof by the triangle inequality, Lemma 3, window codes, compose versus compete, H1 and H2.
- 2 Ceilings: fixed-array counts, Lemma 4, Theorem 5, Theorem 6 with Hall and Konig, Table 2 cell by cell, Remark 7, Lemma 8 and its analogues.
- 3 Exact answers for 3 x 3 windows: SAT from zero, the encoding, the solver loop, the exhaustive search with a 17-node trace, the sequential counter, the control, Proposition 10, witness checking (five algorithms).
- 4 Two constructions: the XOR family and the checkerboard interleave, Theorems 11 and 12, the decoder; plus a remark marked "checked here, not in the paper" (caps 384 and 480).
- 5 Local search and the simulated camera: energy, Metropolis, Table 3, the camera model, the decoder, Table 4, the Wilson interval with all seven intervals reproduced, speed.
- 6 Every headline number and how to reproduce it, plus ten questions to answer without notes.

## Reading list (Docs artifact)

https://claude.ai/artifact/PCz18FSBpZs2rkDExeU6aj, also `study_guide/reading_list.md`. 35 readings, each tied to a section or result of the paper, with a two-week order (about 47 hours). Every DOI resolved and checked against Crossref on 11 November; arXiv ids through the arXiv API. Tiers: 1, ten core papers (Burns and Mitchell; Dothraki; Berkowitz and Kopparty; Bruckstein et al.; Mitchell and Wild; Alhakim et al.; Gabric and Sawada; Mitchell, Etzion and Paterson; Burns and Lloyd patent; Gerlach et al. Twori); 2, eight mathematics readings (van Lint and Wilson; MacWilliams and Sloane textbook; Diestel; Bondy and Murty; Hall 1935; Cock 1988; Ruskey, Sawada and Williams 2012; MacWilliams and Sloane 1976); 3, ten methods readings (Prestwich CNF encodings; Tseitin; Sinz; PySAT; CaDiCaL; Glucose; Metropolis; Kirkpatrick et al.; Wilson 1927; Agresti and Coull); 4, six applications (PuzzleBoard; Uniform Marker Fields; HydraMarker; ArUco; AprilTag; Vandenhouten et al.); 5, The Craft of Research. Two notes at the top: cite Burns and Mitchell Lemma 16 for s = 2; Dothraki's three-of-four versus four-of-four wording.

## G2 Conversate prep notes (`meeting_prep_aaron/`)

Conversate Prep Notes came in Even app v2.0.9: details typed in the app plus uploaded supporting files; the loaded note shows at the top of the glasses display; swipe up to pick a theme, tap to view; AI cues appear during the conversation; live transcript; needs phone internet. The support page does not list accepted file types, limits or the number of notes, so the files are plain text.
- `00_how_to_load.txt`: steps, what to paste if an upload is refused (04, then 03, then 02), tell Aaron the glasses transcribe, keep contact details out.
- `01_prep_note_manual_entry.txt` (1,384 characters, no line over 45): title, goal, Aaron co-wrote two cited papers, pitch, themes 1 Main claim, 2 Key numbers, 3 Review fixes, 4 Limits (including "factor 2 exact for odd u only"), 5 Ask Aaron (AI statement, data statement, BibTeX, Burns and Mitchell numbering), 6 Talk (14 slides), 7 Next steps.
- `02_brief_upload.txt`: full brief (results with labels, how each was established, corrections, limits, talk, Aaron's two co-authored papers and his affiliation, the Burns and Mitchell numbering note).
- `03_likely_questions_upload.txt`: 21 questions with answers to say aloud (novelty, why strong form, compete, preregistration, beyond 3 x 3, budgets, what failure proves, the Theorem 12 error, closure, simulated camera, AI use, data, factor of two for even u, H1 half right).
- `04_numbers_and_terms_upload.txt`: key numbers with sources, and plain definitions.

The meeting took place on 11 November. Its outcome that TJ reported: Aaron suggested the Reachy Mini jigsaw application for this paper and presentation (file 15). Anything else said in the meeting has not been recorded here; add it.

## The everything zip

`COMP5112_WhichWayIsUp_everything.zip` (333 files, about 5.9 MB): research/notes, otorus, results (with 136 witnesses), paper (with reviews, talk plan, builds), study_guide (PDF and source, reading list, paper fixes), meeting_prep_aaron, slides (deck files), COMP5112_paper_overleaf.zip, README.md. Checked by unzipping a fresh copy: 61 tests pass, the guide compiles to 84 pages.
