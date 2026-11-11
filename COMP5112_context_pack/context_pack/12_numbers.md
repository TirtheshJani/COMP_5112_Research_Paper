# 12. Numbers worth knowing

N = u^2; |F_u| = 2^N - 2^ceil(N/2) (arrays not fixed by the half turn).

| Number | What it is | Source |
| --- | --- | --- |
| 2^(rc) | cells of a de Bruijn torus (RC = 2^(rc)) | Assignment 1 |
| 2^25 = 33,554,432 | Dothraki's torus, 8192 x 4096, 5 x 5 windows, 150 cells per inch, 1 mm sensor, 6 x 6 readable patch, 14 Hz | Dothraki |
| 2^22 = 4,194,304 | the poster's ceiling (4RC <= 2^24) | Assignment 3, poster |
| 4,193,280 = 2^22 - 2^10 | 5 x 5 strong-form ceiling | Theorem 5 |
| 4,193,275 | same if all windows share one parity (5 divides R and C) | Lemma 8 |
| 8,386,560 | 5 x 5 orientation-only ceiling, (2^25 - 2^13)/4 | Lemma 4 (B&M Lemma 19) |
| 2^13 = 8,192 / 2^7 = 128 | 5 x 5 windows fixed by the half turn / by the quarter turn | Section 4 |
| 33,546,240 | abs(F_5) | Section 4 |
| 120 / 60 | 3 x 3 ceilings, orientation only / strong form | Table 2 |
| 16,320 / 8,192 | 4 x 4 ceilings | Table 2 (Theorem 6) |
| 1.992 | 4 x 4 ratio of the two ceilings (not 2) | fix 1 |
| 36 | 3 x 3 strong-form maximum; also the XOR maximum; also B&M Figure 6 | Theorem 9, Section 6.1 |
| 85 | largest known 3 x 3 orientation-only torus (5 x 17) | sat_table.csv |
| 2.36 to 3.33 | 3 x 3 cost factor (85/36, 120/36) | Section 5 |
| 18 to 67 percent | excess over the code factor 2 | Section 5 |
| 134 / 56 of 58 | 3 x 3 shapes decided / shapes run with the second encoding | Section 5 |
| 398 s | hardest UNSAT shape (6 x 10) | sat_table.csv |
| 5,728,261 | most nodes in the exhaustive search | exhaustive logs |
| 144 / 168 | turned windows: best 3 x 3 torus / open 9 x 8 patch | Proposition 10 |
| 5, 7, 17, 7, 7, 9, 6, 6, 7 | failing strip lengths, widths 1 to 9, distance 2 | Proposition 10 |
| 512 / 32 / 120 / 5 | XOR family: windows / half-turn-fixed / cap / minimum distance | Section 6.1 |
| 306 | XOR shapes decided | xor_table.csv |
| 280 (14 x 20) | admissible interleave maximum | Theorem 12 |
| 392 / 784 | admissible interleave cap / descriptor table size | Theorem 11 |
| 308 (14 x 22) / 512 | unrestricted interleave found / cap | review 1 |
| 384 / 480 | possible sharper caps (lead, not in the paper) | study guide Part 4 |
| 65,536 (256 x 256) | largest 5 x 5 strong-form torus found (seeds 0, 1) | Table 3 |
| 1,327,104 (1152 x 1152) | largest 5 x 5 orientation-only torus found | Table 3 |
| 441 (21 x 21) / 4,096 (64 x 64) | largest 4 x 4 strong / orientation-only found | Table 3 |
| about 9 / about 20 | ratio of largest solved sizes, 4 x 4 / 5 x 5 | Table 3 |
| 8.5 to 11.8 / 18 to 25 | brackets on those ratios | Section 7 |
| 3 x 10^6 / 3 x 10^7 | flip budgets 4 x 4 / 5 x 5 | Section 7 |
| 0.5 | Metropolis temperature | Section 7 |
| 50,000 | flips between full rescans; also the SAT conflict-round size | Sections 5, 7 |
| 64 / 100 | codes changed by one flip, 4 x 4 / 5 x 5 | s u^2 |
| 17 / 26 | radius-1 ball, 4 x 4 / 5 x 5 (1 + u^2) | Section 7 |
| 8.5 to 2.6 percent | wrong reads at noise 0.3, size-matched 6 x 6 pair | Table 4 |
| 63.9 / 64.2 percent | correct reads, same pair | Table 4 |
| 0 of 103,801 | single-error reads decoded wrongly, strong-form tori | Section 8 |
| 38.3 / 28.6 percent | multi-error wrong reads, strong / orientation only (3 x 3) | Section 8 |
| 20,000 / 12345 | reads per noise level / random seed | Section 8 |
| 3.9 to 16.8 million per second | decoding speed (median of five runs) | decode_timing.md |
| 136 of 136 | stored tori re-verified | verify_witnesses.txt |
| 61 | tests passing | otorus/tests |
| 47 / 163 | refs.bib entries / research bibliography entries | paper, notes/bib |
| 28 / 84 / 14 | pages of paper draft 3 / pages of the study guide / slides | builds |
| 110100 | unique 2-orientable binary cycle of length 6 for 5-windows (up to rotation and complement) | B&M Figure 4, A4 |
| 144 of 144 / 48 of 48 | A4 decoder on Figures 6 and 5 | Assignment 4 |
| 2.8 x 10^14 | Lemma 19 limit for Figure 6's 4-symbol parameters | Assignment 4 |
| 36,000 | cells for a 1,000-piece jigsaw (25 x 40 pieces) at 6 x 6 cells per piece; fits inside one 256 x 256 torus | file 15 |
