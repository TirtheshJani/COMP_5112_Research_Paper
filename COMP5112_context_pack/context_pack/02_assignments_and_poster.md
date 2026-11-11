# 02. Assignments 1 to 4 and the poster

Full source: the poster pack on TJ's PC, `COMP-5112-Research-Methodology\Poster-12TJ\knowledge-pack\` (files 00 to 04), built 3 November 2026.

## Assignment 1: research topic (due 15 September)

TJ wrote an informal description of a binary de Bruijn torus (a grid that wraps both ways in which every r x c window appears exactly once), a formal definition (a binary R x C torus T such that every one of the 2^(rc) binary r x c arrays occurs as the window W_T(i, j) for exactly one position), and a valid 4 x 4 example with 2 x 2 windows:

```
0 0 0 1
0 0 1 0
1 0 1 1
0 1 1 1
```

He showed four windows covering every kind of wraparound: (0,0) no wrap, (3,0) bottom to top, (0,3) right to left, (3,3) both. The counting condition RC = 2^(rc) is necessary but not sufficient (2 x 8 with 2 x 2 windows passes the count and never works). Three AI tools were asked for an (8, 32; 2, 4) torus: Google AI Mode returned websites, Gemini returned an unverified 8 x 32 grid, Claude models did not produce one. Lecture 4 feedback: anchor the definition to the 1D sequence, explain "torus", introduce notation such as T: Z_R x Z_C -> {0,1}, split helper definitions into their own blocks.

## Assignment 2: references (due 1 October)

Five references added to the shared Overleaf pool with BibTeX and PDFs: Burns and Mitchell (HP report version, later cited as the 1993 book chapter), Dothraki (TEI 2021), Berkowitz and Kopparty (SODA 2016), Becher and Carton (flagged as a duplicate of a classmate's entry and replaced by Kreitzer, Nica and Pereira 2024), Kapinya (2004 thesis, no PDF), plus Herout et al. (CVPR 2013).

## Assignment 3: leveraging references (due 8 October)

Three references chosen and their BibTeX corrected: Burns and Mitchell (re-keyed from burns1992coding to burns1993coding, Cryptography and Coding III, OUP 1993, pp. 31 to 66), Berkowitz and Kopparty, Dothraki; plus Cooper and Heitsch (2013) as background. For each: research interest, topic, questions, problem (Craft of Research Part I). The four summaries in section A.2 are still placeholders "[Summary to be written by TJ]" and must be written by TJ himself (the assignment forbids AI-written summaries).

The new research question (section A.4), posed as of Dothraki's publication in February 2021:
- Interest: position-encoding patterns that stay reliable when a cheap sensor sees only a few cells and may be rotated.
- Topic: binary tori that reveal position and orientation from one window and detect one misread cell; 4-orientable arrays (Burns and Mitchell) with pairwise Hamming distance at least 2.
- Question: for 5 x 5 windows, which fit inside Dothraki's 6 x 6 view, what is the largest binary R x C torus in which all windows and their 90, 180 and 270 degree turns are distinct and every two differ in at least two cells? Can it be decoded as quickly as Dothraki's torus?
- Problem: Dothraki's torus carries no orientation and any single flipped cell turns one window into another, so it compares four overlapping windows and still handles only four orientations. Counting: 4RC <= 2^24, so RC <= 2^22, one eighth of Dothraki's 2^25 positions (a 2048 x 2048 square, about 35 cm a side at 150 cells per inch).

## Assignment 4: programs and proofs (due 22 October)

A NumPy notebook (Google Drive, `Tirthesh_Jani_de_Bruijn_Torus_Programming4444.ipynb`) rebuilding Burns and Mitchell in five functions: `isOrientable(T, r, c, k)`, `findOrientableSequences(v, n)`, `constructionE(A, B, d)`, `decodeWindow(...)`, `orientableBound(m, n, c, u, v, s)`. Results: 12 two-orientable binary cycles of length 6 for 5-windows, all rotations or complements of the paper's 110100; Figures 5 and 6 rebuilt; 144 of 144 windows of Figure 6 decoded (36 positions x 4 turns) and 48 of 48 for Figure 5; Figure 6 has 36 cells against a Lemma 19 limit of 281,474,959,933,440 (about 2.8 x 10^14), Figure 5 has 24 against 523,776. The decoder for Construction E (divide by d for the A-window, remainder for the B-window, forwards or backwards table for the turn) is TJ's addition; the paper discusses decoding only for 1-orientable arrays.

## The poster

"Which Way Is Up? Orientable de Bruijn arrays for position sensing", 48 x 36 inches, final PDF `Poster-12TJ\12TJ.pdf` (Canva v2, design DAHZsRMgJhA; v1 DAHZamlorkY kept). Subtitle: a close reading of Burns and Mitchell (1993), the code that checks it, and the question it leaves open. Header sentence: print two one-way sequences on top of each other and a single glance at the floor tells a robot both where it is and which way it is facing; the price, so far, is a tiny floor.

Layout: a journey map with four colour-coded stops.
1. The promise (blue): a de Bruijn torus gives position from one window (Pac-Man wraparound, RC = 2^(rc), the 4 x 4 torus and the 4 x 16 torus drawn on a doughnut). The catch: in the 4 x 16 torus with 2 x 3 windows, the window at (0,7) turned 180 degrees is the window at (2,7) (a 6 and a 9). Dothraki's fix is four windows that must agree. An upside-down sticky note ("you are 4-orientable"). Timeline of uses: 1993 Burns and Mitchell, 2012 Uniform Marker Fields, 2021 Dothraki, 2023 HydraMarker.
2. The paper (orange): 1-, 2-, 4-orientable glyph panels; the bound mn <= (c^(uv) - c^floor((uv+1)/2))/s (Lemmas 16 and 19, not tight); the necklace 110100 (Dai, Martin, Robshaw and Wild: no longer binary necklace for v = 5); Construction E, e_ij = d a_i + b_j (tens and units), Theorem 17 (2-orientable), Theorem 20 (4-orientable when A is also 2-orientable); Figure 6, the 6 x 6 four-symbol array with A = B = 110100.
3. My check (green): the five functions, stat tiles 12, 144/144, 36 cells; a log-scale line from 36 up to 2.8 x 10^14 with Dothraki at 33.6 million and the research-question limit at 4.2 million; a worked divide-and-remainder decode of Figure 5.
4. The open question (purple): the Assignment 3 question, 4RC <= 2^24, one eighth of Dothraki; orientation alone would allow 8,386,560. "What I am thinking about now": a binary interleave of A and B, longer sequences (Mitchell and Wild), error detection (Berkowitz and Kopparty), and greedy search.

Eight references; footer discloses AI use (Claude helped draft text and assemble in Canva; claims checked, code run by TJ).

Talk: a two-minute version and a ten-minute script (about 1,400 words), a Claude doc and a teleprompter file for the G2 glasses. Sessions on 3 and 5 November, run by the TA (Nahoon) while Aaron was in Massachusetts; PDF uploaded by 10 AM the day before; a separate 10 to 15 minute video meeting with Aaron to review the PDF.

## Corrections found while building the poster pack

1. FFMS (Fan, Fan, Ma, Siu 1985) pages are 205 to 213, not 205 to 221.
2. Dothraki's acceptance rule is worded two ways: Section 4.2 accepts when at least three of four windows land next to each other; Section 4.3 needs all four. The paper follows 4.3.
3. Burns and Mitchell has two numberings: the typeset chapter (Lemma 16, Construction E, Theorem 17, Lemma 19, Theorem 20, Figures 4 to 6) and the scanned HP report (Lemma 5.2, Construction 5.3, Theorem 5.4, Lemma 6.2, Theorem 6.3, Figures 6, 8, 9).
4. Poster function signatures are shortened versions of the notebook's.
5. HydraMarker's method is binary wave function collapse.
6. Dai et al. author order differs between sources; pages 97 to 115.
7. Assignment 3 summaries still placeholders on TJ's copy.

## How the assignments feed each other

A1 gives the definition and the count; A2 the reference pool; A3 the deep-read paper and the research question; A4 the code. The poster is all four in one page, and its last stop became the paper.
