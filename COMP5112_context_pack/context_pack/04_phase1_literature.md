# 04. Phase 1: literature review (6 to 7 November)

Full notes on TJ's PC: `research/notes/lit/` (00_synthesis.md with the gap table, seven resolved disagreements and directions S1 to S7; 01_orientability.md, 02_robustness.md, 03_structure.md, 04_construction.md, 05_applications.md; 06_pool_A/B/C.md, the triage of the roughly 180 PDFs in the course folder; 07_threat_checks.md; UNVERIFIED.md). Short version: project doc claude/COMP5112_Phase1_Synthesis_Verdict_07Nov2026.md.

## How it was done

Five parallel agents, one per line of work, each with the same output template (what the paper proves, exact statements relied on, follow-on work with DOI or arXiv, what it does not do, ideas, BibTeX):
- A, orientability: Burns and Mitchell 1993; Dai, Martin, Robshaw, Wild 1993; Mitchell and Wild 2022; Gabric and Sawada 2024; Alhakim, Mitchell, Szmidt, Wild 2024.
- B, robustness: Berkowitz and Kopparty 2016; Bruckstein et al. 2012; later robust positioning work.
- C, structure: Becher and Carton 2024 (nested perfect arrays); Etzion; Hurlbert and Isaak; Paterson; Horan and Stevens.
- D, construction: Kreitzer, Nica and Pereira 2024; Fan, Fan, Ma, Siu 1985; Cock 1988; universal partial tori; torus packing for multisets.
- E, applications: Herout et al. 2013; Szentandrasi et al. 2012 (Uniform Marker Fields); HydraMarker 2023; Dothraki 2021; PuzzleBoard 2024; Schmid, Wimmer, Lippl 2022 (CNN orientation).
Then three triage passes over the course PDFs, extra arXiv, Crossref, OpenAlex and web searches, citation-check on every entry (163 bibliography entries in notes/bib/otorus.bib; the paper's refs.bib has 47), and three targeted threat checks. Google Scholar was not used.

## The five levers (from the plan)

| Reference | Lever |
| --- | --- |
| Burns and Mitchell | orientability (the property) |
| Berkowitz and Kopparty | window Hamming distance (the robustness condition) |
| Becher and Carton | positions split by (row, column) mod n (idea for interleaving) |
| Kreitzer, Nica and Pereira | alternating de Bruijn sequences (rectangular building blocks) |
| Herout et al. | greyscale relaxation; aperiodic 4-orientable fields found by search |

## Verdict

The gap is real, with caveats. No paper, preprint or patent was found that treats a periodic binary array whose windows are distinct under the four turns and pairwise at Hamming distance 2 or more. Confidence moderately high for refereed literature, low to moderate for patents and technical reports. The novelty is the combination, not any ingredient.

Nearest neighbours, which force careful wording:
- Vandenhouten, Hermerschmidt and Fiebelkorn, SPIE 10335 (2017): binary toroidal patterns with Hamming distance as a figure of merit, but centrally symmetric (the opposite of 2-orientable) and 7 x 7 or larger windows.
- Xu, Ma and Tan (2007): aperiodic binary, unique 5 x 5 windows, no orientation, no distance.
- Morano (1998), Albitar (2007): distance-designed aperiodic multi-symbol arrays.
- HydraMarker (Zhu et al. 2023): 123 x 123, aperiodic, 4-orientable, about 0.17 percent of the orbit ceiling.
- Garrido-Jurado et al. (ArUco 2014): rotation-aware distance for isolated square markers that share no cells.
- US 5,442,147 (Burns and Lloyd, Hewlett-Packard): orientability, no distance.

## Threat checks

- US 5,442,147: full text and all 57 claims scanned; 1-, 2-, 4-orientable patterns, no Hamming distance, redundancy or parity. No threat. Nearest industrial neighbour US 7,445,160 B2 (nine-symbol 5 x 5 regions, registration marks for orientation, Reed-Solomon).
- Garrido-Jurado et al.: no threat, but the novelty sentence must say "windows of a doubly periodic array".
- Lloyd and Burns 1993: no copy reachable; described by others as discrete-logarithm decoding of pseudorandom arrays, no rotation or errors. Inconclusive, leaning no threat.

## Own results proved or computed in Phase 1

- Windows fixed by the half turn: 2^13; by the quarter turn: 2^7; orbit bound (2^25 - 2^13)/4 = 8,386,560 (Burns and Mitchell Lemma 19).
- Strong-form ceiling RC <= 4,193,280 = 2^22 - 2^10 by centre-flip pairing (replaced the plan's 2^22).
- If all windows share one parity, 5 | R and 5 | C, giving 4,193,275 (later proved as Lemma 8 for sides not in {1, 5}); that near-extremal tori must have constant parity is not proved.
- Weak-form ceiling stays 8,386,560.
- XOR tori: 4-orientable pairs only at 5 x 6 and 6 x 6 among RC <= 120 in the first check (the full table later added 1 x 6 and 4 x 6). The 6 x 6 example A = 000001, B = 001011 has 144 distinct turned windows and minimum distance 5. Bruckstein's 16 x 32 product array is not even 2-orientable.
- 3 x 3 pilot ceilings: 120 orientation only, 60 strong form.
- Huge binary 5 x 5 de Bruijn tori contain every window, every turn and every distance-1 neighbour, so they say nothing about orientability.

## Corrections made in Phase 1

- "XOR grids can never be orientable" is false in general; it holds only when the grid contains all 512 XOR-type windows.
- "Universal torus" is an umbrella term, not a synonym for de Bruijn torus.
- Duplicate Kreitzer key removed; Herout DOI added; Garrido-Jurado 2014 and the HP patent added. Print-only items without identifiers listed in UNVERIFIED.md and not cited.

## Found later (Nov 11, reading list work)

- Burns and Mitchell's Lemma 16 (Section 5.1) already states the s = 2 bound; Lemma 19 (Section 6.1) the s = 4 bound. The paper's Section 4 says s = 2 "follows by the same argument"; cite Lemma 16 instead.
- The MacWilliams and Sloane entry in refs.bib is their 1976 Proc. IEEE paper, not the coding textbook.
