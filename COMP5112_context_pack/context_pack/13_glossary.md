# 13. Glossary of terms and symbols

## Terms

- de Bruijn torus (perfect map, de Bruijn array): a doubly periodic array in which every r x c window over the alphabet appears exactly once. "Universal torus" is an umbrella term, not a synonym.
- Torus: an R x C array whose indices wrap modulo R and C (Pac-Man wraparound).
- Window W_{i,j}(T): the u x u block with top-left corner (i, j), read with wraparound. A torus has RC windows.
- Quarter turn rho: (rho W)[a][b] = W[b][u-1-a]; rho^2 is the half turn; rho^4 is the identity.
- Turn set K_s: K_1 = {0}, K_2 = {0, 2}, K_4 = {0, 1, 2, 3}.
- Instance (i, j, k): the window at (i, j) turned k quarter turns; a torus has sRC instances.
- Turned window: the array rho^k W_{i,j}.
- s-orientable (Definition 1): all sRC turned windows are pairwise distinct. 1-orientable = all windows distinct; 2-orientable = also under the half turn; 4-orientable = under all four turns.
- Window distance d_s(T) (Definition 2): the least Hamming distance between two distinct instances. d_s >= 1 is the same as s-orientable.
- Strong form: d_4(T) >= 2 (all 4RC turned windows pairwise at least two cells apart). Weak form: 4-orientable and d_1 >= 2 (only upright windows). The paper uses the strong form.
- Window code: a set of u x u arrays closed under the turns, with the distance condition, without requiring that they fit together into a torus. The comparison object for "the factor of two".
- Ceiling: an upper bound on RC from counting.
- Orbit bound: Burns and Mitchell's Lemma 19 count (arrays not fixed by the half turn, divided by s).
- F_u: arrays not fixed by the half turn; |F_u| = 2^N - 2^ceil(N/2).
- Centre flip phi: flip the centre cell (odd u); pairs F_u with itself; at most one array of each pair can be a turned window at distance 2.
- Compose / compete: the requirements compose if distance 2 shrinks the largest torus by about the window-code factor (2 for odd u), compete if by more.
- H1 / H2: the two preregistered predictions (file 05). Both failed as stated.
- Closure: the reading that the extra cost comes from the pattern having to wrap around (periodicity), not from packing windows locally. Evidence: open patches beat tori.
- Strip: a pattern that wraps in one direction only. Open patch: wraps in neither (a jigsaw puzzle is an open patch).
- XOR family: T[i][j] = a_i xor b_j.
- Checkerboard interleave A [+] B: T[i][j] = a_i on cells with i + j even, b_j on the others. A binary counterpart of Construction E.
- Type of an instance: parity of i + j + k (which colour class lands on the even cells after turning).
- Descriptor: the pair of 5-letter label words a window shows.
- Admissible labels: label sequences with no 5-window 00000, 11111, 01010 or 10101.
- Construction E (Burns and Mitchell): e_ij = d a_i + b_j over d^2 symbols; Theorem 17 (2-orientable), Theorem 20 (4-orientable).
- Orientable sequence: a cyclic sequence whose v-windows are all distinct read forwards and backwards (110100 for v = 5).
- Energy E: number of instance pairs at distance below delta; zero means a valid torus.
- Metropolis rule: accept a move that raises E by Delta E with probability exp(-Delta E / temperature); here the temperature is 0.5 (written tau in the study guide to avoid clashing with the torus T).
- Conflict ball: the 1 + u^2 codes within distance 1 of a turned window; occupancy = density times ball size.
- Wilson interval: a confidence interval for a proportion that behaves well near 0 and 1.
- SAT, CNF, Tseitin encoding, sequential counter, CaDiCaL, Glucose, PySAT, UNSAT, DRAT: see the study guide Part 3.

## Symbols

R, C rows and columns of the torus; u window side; N = u^2; T the torus; (i, j) a position; k a turn count; s the number of allowed turns; delta the required distance; d_H Hamming distance; wt Hamming weight; Q_N the hypercube on all binary u x u arrays (even and odd sides by weight parity); A, B label sequences with entries a_i, b_j; sigma camera noise level; tau search temperature; E energy.
