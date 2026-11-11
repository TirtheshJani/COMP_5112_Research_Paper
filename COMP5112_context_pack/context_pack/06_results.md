# 06. Results: everything proved or computed

The index of record is `research/results/README.md`; every number below traces to a file in `research/results/` and the code in `research/otorus/`. Tests: 61 pass (`cd research/otorus && python3 -m pytest -q`). Witnesses: 136 stored tori, 136 of 136 re-verified by `scripts/verify_witnesses.py` with code independent of the search and SAT code (`verify_witnesses.txt`).

## 1. Ceilings (Section 4; bounds.md; otorus/bounds.py)

N = u^2. Arrays fixed by the half turn: 2^ceil(N/2). F_u = arrays not fixed by the half turn, |F_u| = 2^N - 2^ceil(N/2).
- Lemma 4 (after Burns and Mitchell Lemma 19; Lemma 16 for s = 2): for s in {2, 4}, sRC <= |F_u|.
- Theorem 5 (odd u, centre flip pairs F_u with itself; at most one of each pair at distance 2): sRC <= |F_u|/2 = 2^(N-1) - 2^((N-1)/2). For 5 x 5, s = 4: RC <= 4,193,280.
- Theorem 6 (even u, Hall and Konig on the hypercube; the odd-weight side lies inside F_u): sRC <= 2^(N-1). For 4 x 4, s = 4: RC <= 8,192.
- Remark 7: tight for window codes (even-weight arrays in F_u for odd u; odd-weight for even u). Caveat found 11 Nov: the factor between the two ceilings is exactly 2 only for odd u; for even u it is 2 - 2^(1-N/2) (1.992 at 4 x 4).
- Lemma 8 (constant parity, 5 x 5, sides not in {1, 5}): 5 | R and 5 | C, so RC <= 4,193,275. 3 x 3 analogue: 3 | R and 3 | C.

Table 2 (u; s = 1, 2, 4 orientation only / strong form):
- 2 x 2: 16 / 8; 6 / 4; 3 / 2
- 3 x 3: 512 / 256; 240 / 120; 120 / 60
- 4 x 4: 65,536 / 32,768; 32,640 / 16,384; 16,320 / 8,192
- 5 x 5: 33,554,432 / 16,777,216; 16,773,120 / 8,386,560; 8,386,560 / 4,193,280
(Side fact from the study guide: no 2- or 4-orientable binary torus with 2 x 2 windows exists at all.)

## 2. Exact 3 x 3 strong form (Theorem 9; exact_3x3_strong_form.md; sat_table.csv)

Maximum 36 cells. Shapes that exist: 2 x 3, 3 x 3, 3 x 4, 3 x 5, 3 x 6, 3 x 9, 3 x 12, 6 x 6. All 134 shapes with R <= C and RC <= 60 decided.
- SAT (otorus/sat.py): one variable per cell; for each pair of cells one shared XOR auxiliary (four Tseitin clauses); for each instance pair the set D of window positions whose cells are distinct, with |D| clauses "some other position in D differs" (forces at least two differences); |D| <= 1 makes it UNSAT at once; cell 0 fixed (complement symmetry). CaDiCaL 1.5.3 via PySAT, 50,000-conflict rounds with a wall-clock check. Hardest UNSAT: 6 x 10, 398 s.
- Exhaustive depth-first search (otorus/exhaustive.py, numba), its own turned_cells index arithmetic shared with nothing else, shapes transposed so rows are short, conflict = equal code or (for distance 2) a code one bit away. At most 5,728,261 nodes. Agrees with SAT on all 134 shapes (verify_3x3_s4_d2_dfs.csv).
- Second SAT encoding: Glucose 4 with a sequential counter (Sinz 2005) on 56 shapes of at most 30 cells; agrees (verify_3x3_s4_d2.csv). Note: there are 58 such shapes; 3 x 10 and 5 x 6 were not run.
- Existence is not monotone (3 x 9 exists, 3 x 10 does not); widths 4 and 5 fail at every length.

## 3. 3 x 3 orientation-only control (sat_table.csv, delta = 1)

Every shape with 3 <= R <= C and RC <= 81 exists (71 shapes); also 4 x 21, 6 x 14 (84) and 5 x 17 (85). Undecided: 3 x 28 and 7 x 12 at 50 s; 14 shapes from 87 to 116 cells at 40 s; 10 x 12 and 5 x 24 at 25 minutes. Maximum in [85, 120]. Cost factor 85/36 = 2.36 to 120/36 = 3.33; excess over the code factor 2 of 18 to 67 percent.

## 4. Strips and open patches (Proposition 10; strips_3x3_s4_d2.csv, strips_3x3_s4_d1.csv, patches_3x3_s4_d2.csv)

Strips wrap one way. Distance 2, failing length by width: 1: 5; 2: 7; 3: 17; 4 and 5: 7; 6: 9; 7 and 8: 6; 9: 7. Distance 1: widths 3 to 5 reach length 20. Open patches wrap neither way, distance 2: 8 x 8 (144 turned windows), 9 x 8 (168), 20 x 4 (144) can be filled; 9 x 9 undecided at 3 x 10^8 nodes. The best torus has 36 x 4 = 144 turned windows, so the 9 x 8 patch holds more than any torus. Reading (after review 2): the cost appears with closure, not local packing. Witness 9 x 8 patch rows: 01110111, 10011011, 00010011, 10101100, 10011011, 11001000, 00011010, 10011011, 11001000.

## 5. XOR family T[i][j] = a_i xor b_j (Section 6.1; xor_table.csv)

512 distinct 5 x 5 windows (pairs (x, y) and their complement give the same window); closed under turns (x_a xor y_b goes to y_(4-a) xor x_b); 32 fixed by the half turn; difference weight |p|(5-|q|) + (5-|p|)|q| >= 5, so every 4-orientable XOR torus has distance 5; cap (512 - 32)/4 = 120. Exact maximum 36: 306 shapes decided; four exist (1 x 6, 4 x 6, 5 x 6, 6 x 6). Example A = 000001, B = 001011 (6 x 6, distance 5); the csv row stores another valid pair (A = 001000, B = 101001).

## 6. Checkerboard interleave A [+] B (Section 6.2; interleave.md, interleave_table.csv, interleave_rows6.csv)

T[i][j] = a_i if i + j is even, else b_j. Turns map colour classes to colour classes; type of an instance = parity of i + j + k; descriptor = two 5-letter words. Admissible labels: no 5-window equal to 00000, 11111, 01010 or 10101 (a set closed under reversal).
- Theorem 11: (a) 4-orientable iff the 2RC type-0 descriptors are distinct; (b) then distance at least 2; (c) RC <= 392 (28 x 28 descriptors / 2).
- Theorem 12: admissible maximum 280 (14 x 20, A = 01001111000011, B = 10111010001001101100); 41 shapes above 280 and the six 6-row classes UNSAT. Other existing shapes include 14 x 16, 10 x 20, 14 x 14, 12 x 16, 10 x 18, and 6 x C for C in {30 to 40, 44}.
- Correction after review 1: without admissibility a 14 x 22 interleave (308 cells) exists at distance 2; unrestricted cap 512 (4RC <= 2 x 32 x 32); maximum open.
- Decoder: test whether the even class is row-constant, otherwise apply a quarter turn; look up in a table of at most 784 descriptors.
- Possible strengthening found 11 Nov (study guide Part 4 remark, brute-force checked, not proved by TJ): (a) and (b) hold without admissibility; dropping half-turn-fixed descriptors tightens the caps to 384 (admissible) and 480 (unrestricted).

## 7. Local search (Section 7, Table 3; grow_4x4.csv, grow_5x5.csv; otorus/search.py)

Energy = number of instance pairs at distance below delta (always even when s = 4); code-count table; one flip changes s u^2 codes (64 for 4 x 4, 100 for 5 x 5); Metropolis at temperature 0.5; conflict list fully rescanned every 50,000 flips (without rescans one run stalled at 256 x 256); fresh random torus per size and seed. Equal budgets: 3 x 10^6 flips (4 x 4, seeds 0 to 4), 3 x 10^7 (5 x 5).
- 4 x 4 orientation only: 64 x 64 = 4,096 solved on 3 of 5 seeds; 72 x 72 failed on all.
- 4 x 4 strong form: 21 x 21 = 441 on 1 of 5 (20 x 20 on 3 of 5); 22 x 22 failed on all.
- 5 x 5 orientation only: 1152 x 1152 = 1,327,104 solved (12.5 million flips); 1280 x 1280 failed (energy 660).
- 5 x 5 strong form: 256 x 256 = 65,536 on seeds 0 and 1 (728,102 and 15.6 million flips); 272 x 272 failed on both (energies 20 and 2; energy 2 = one window equal to its own half turn); 288 x 288 failed (energy 32). The csv records the seed-0 256 solve with a 10M budget; a rerun at 30M gives the identical torus.
- Ratios of largest solved sizes: about 9 (4 x 4; brackets 8.5 to 11.8) and about 20 (5 x 5; brackets 18 to 25). Ratios of what one method finds, not of maxima. Percent of ceiling: 25 and 5.4 (4 x 4), 15.8 and 1.6 (5 x 5). Flips per cell: 458 (256^2) against 23 (1152^2).
- Occupancy of each window's conflict ball (density x (1 + u^2) for distance 2, density for orientation only) between solved and failed: 0.16 to 0.20 (5 x 5) and 0.25 to 0.32 (4 x 4) orientation only; 0.20 to 0.23 (5 x 5) and 0.46 to 0.50 (4 x 4) strong form. Ball sizes 17 (4 x 4) and 26 (5 x 5).

## 8. Simulated camera (Section 8, Table 4; camera_robustness.csv; otorus/camera.py, decode.py)

Seven tori, 20,000 reads per noise level, sigma in {0, 0.10, ..., 0.40}, seed 12345 (common random numbers), angle error 1 degree, offset 0.05, blur 0.10 with 16 subsamples, threshold 0.5; decoder = sorted code table with binary search; outcomes correct, rejected, wrong. At sigma = 0.3 (correct / rejected / wrong, percent):
- 3 x 3 strong 6 x 6: 63.9 / 33.5 / 2.6
- 3 x 3 orientation only 6 x 6: 64.2 / 27.3 / 8.5
- 3 x 3 orientation only 9 x 9: 64.0 / 12.8 / 23.3
- XOR 6 x 6: 30.3 / 69.7 / 0
- Interleave: 29.9 / 69.8 / 0.29
- 5 x 5 strong 256^2: 29.5 / 70.2 / 0.29
- 5 x 5 orientation only 256^2: 29.5 / 70.0 / 0.51
Single-error reads decoded wrongly: 0 of 103,801 for strong-form tori; 5,885 of 25,669 (6 x 6) and 16,255 of 25,404 (9 x 9) orientation only; 193 of 26,043 for the 5 x 5 orientation-only torus. Multi-error wrong: 38.3 against 28.6 percent (3 x 3 pair); 299 against 289 reads (5 x 5 pair). Wilson 95 percent intervals reported. Decoding speed: medians of five runs of 200,000 decodes, 3.9 to 16.8 million lookups per second (decode_timing.md). Dothraki's pipeline runs at 14 Hz.

## 9. Witnesses on disk (results/witnesses/)

136 files: 74 u3v3s4d1 (3 x 3 orientation only), 9 u3v3s4d2 (3 x 3 strong), 15 u4s4d1, 11 u4s4d2, 4 u5s4d1, 4 u5s4d2, 4 xor, 13 interleave, 2 interleave_unrestricted (including R14C22 and R6C48). Large tori are .npz with np.packbits (unpack with np.unpackbits(bits)[:R*C].reshape(shape)). The ones most relevant to the jigsaw: u5s4d2_R256C256_seed0.npz and _seed1.npz (5 x 5 strong form, 65,536 cells) and u5s4d1_R256C256_seed0.npz (orientation only, the camera control).
