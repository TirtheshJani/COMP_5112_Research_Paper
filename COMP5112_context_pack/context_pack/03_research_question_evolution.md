# 03. How the research question evolved

## Stage 1: the seed (8 October)

Two things met. Aaron's Lecture 10 inner-tube example showed that a de Bruijn torus fails when the reader can be turned, and that fixing this changes the definition. Dothraki showed the same failure in a real system, plus a second one: any single misread cell turns one valid window into another, so Dothraki must make four overlapping windows agree. TJ asked whether the pattern itself could carry both orientation and error detection, which means combining Burns and Mitchell's 4-orientability with Berkowitz and Kopparty's window distance.

## Stage 2: the Assignment 3 question and the poster (8 October to 5 November)

For 5 x 5 windows, the largest binary torus whose windows and their three turns are pairwise distinct and pairwise at least two cells apart, and whether it decodes as fast as Dothraki's. Counting bound 4RC <= 2^24, RC <= 2^22 = 4,194,304. The poster's last stop presents this as open, with four directions (binary interleave, longer sequences, error detection, search).

## Stage 3: the plan (6 November)

The research plan (project doc claude/COMP5112_Orientable_Torus_Research_Plan_06Nov2026.md) set four phases: literature fan-out with parallel agents, brainstorm and lock the statement, experiments, then Reachy Mini and the paper. It named the object a robust orientable torus (R, C; 5, 5; s = 4, delta = 2) and noted that rotation preserves weight, so the even-weight code is closed under turns and the two requirements are compatible at the level of window sets; the real question is whether overlapping windows allow it. Candidate directions S1 to S8 included S8, physical validation with Reachy Mini's camera.

## Stage 4: Phase 1 sharpened it (7 November)

- The gap is real: no paper, preprint or patent found treating a periodic binary array whose windows are distinct under the four turns and pairwise at distance 2 or more.
- The ceiling was corrected from 2^22 to exactly 4,193,280 = 2^22 - 2^10 (centre-flip pairing on arrays not fixed by the half turn).
- Strong form (all 4RC turned windows pairwise at distance 2) versus weak form (only the RC upright windows); the paper uses the strong form because it matches Dothraki.
- Known example: the 6 x 6 XOR torus, 36 cells, distance 5.

## Stage 5: Phase 2 turned it into a test (9 November)

Three candidates: A, the poster question in strong form, attacked through bounds, exact small-window tables and search (chosen); B, orientation only, no distance (fallback); C, which algebraic families can produce orientable binary tori (folded into A). The question became sharper: do orientation and distance compose (largest torus near the ceiling, so requirements can be stacked like constraints on a code) or compete (maxima collapse)? Two predictions were written down before the experiments:
- H1 compose: 3 x 3 exact maximum equals the ceiling 60, and a 5 x 5 torus of hundreds of cells per side exists.
- H2 compete: small-window maxima fall well short, algebraic families cap early, and 5 x 5 search stalls near 36.
The exact 3 x 3 maximum was the deciding test. Reachy Mini was taken out of the paper the same day (file 05 has the reasons).

## Stage 6: the answer (9 to 10 November)

Both predictions failed. 3 x 3 came out at 36, not 60 (H1's first half wrong), and 5 x 5 search reached 256 x 256 = 65,536 cells, not about 36 (H2 wrong; H1's second half held). The claim was restated with a quantitative definition: the requirements compose if adding distance 2 shrinks the largest torus by about the factor window codes lose (exactly 2 for odd window sides), and compete if it shrinks it by more. They compete: at 3 x 3 the factor is at least 85/36 = 2.36. After review 2, the mechanism was restated as closure: open patches hold more turned windows at distance 2 than any torus, so the cost appears when the pattern must wrap. The graded claim was formed after seeing the data, so it is labelled exploratory. Title: "Which Way Is Up? Orientation and Error Detection Compete in Binary Position Tori".

The second half of the poster question (decoding speed) survives as the decoders of Section 6 and the timing in Section 8 (3.9 to 16.8 million lookups per second against Dothraki's 14 Hz pipeline).

## Stage 7: the application comes back (11 November)

In their meeting Aaron suggested, for this paper and presentation, a two-sided jigsaw puzzle: a picture or abstract image on the front, a binary de Bruijn-style grid on the back, and a Reachy Mini that reads a held-up piece and says where it goes and what its window looks like. This is the same move as Lecture 10 and Dothraki, a real setting that pushes back, and it puts physical evidence where the paper currently has a simulated camera. File 15 has the analysis and the planning questions.
