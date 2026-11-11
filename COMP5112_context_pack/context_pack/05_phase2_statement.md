# 05. Phase 2: brainstorm, hypotheses and the research statement (9 November)

Sources: `research/notes/02_phase2_brainstorm.md`, `02_research_statement_v1.md` (v1.1), `02_research_statement_v2.md`, `CONTEXT.md` (glossary); project docs claude/COMP5112_Research_Statement_v1_09Nov2026.md and claude/COMP5112_Research_Statement_v2_09Nov2026.md. Form follows The Craft of Research 5th ed. sections 1.3, 2.1 to 2.3, 9.4, 14.7.

## Decision 1: the floor

TJ accepted a problem-posing paper as the floor. What had to exist by 28 November: the strong-form definition, the two proved ceilings, an exact table for small windows, the 6 x 6 example and the XOR-family cap. A larger construction was the upside.

## Candidates

- A. Robust orientable torus (poster question, strong form), attacked by bounds, exact small-window tables and search growth. Chosen.
- B. Orientation-only binary torus. Cleanest open problem stated by others (PuzzleBoard, Horan and Stevens), weakest originality; fallback.
- C. Which algebraic families (XOR, interleave, Construction E) can produce orientable binary tori. Highest value, highest risk; folded into A.

## Hypotheses and the deciding test

- H1, compose: a strong-form torus exists within a small constant factor of 4,193,280, and small-window maxima match the counting bounds (3 x 3: 120 orientation only, 60 strong form).
- H2, compete: small-window maxima fall well below the bounds, algebraic families cap early (XOR at 36), search stalls far below the ceiling.
- Discriminating test: the exact 3 x 3 maximum. Decision trigger: if far below 60 by 16 November, headline H2 and move search budget to 4 x 4.

A what-if oracle gave about 20 percent best case, 55 percent likely, 25 percent worst case; the worst case was still the floor.

## Where Reachy Mini fitted (decided 9 November: out of the paper)

Reasons: weak evidence (one camera, few frames) against a simulated camera with thousands of controlled trials; it would cost the draft-writing week (22 to 24 November); the rubric's 40 content points reward argument and synthesis, not hardware; Craft of Research 2.3 keeps the application in the conclusion. Replacement: the simulated-camera experiment in the otorus library. Optional: a thirty-second clip of the real decoder reading a printout for the 30 November talk, only if everything else was done by 22 November. TJ's own reasoning at the time: he had considered the robot because he is likely the only student in the class with one, but chose a deeper research statement with code, simulation and a combinatorial approach. On 11 November Aaron himself suggested bringing it back (file 15).

## Research statement v1.1 (before experiments)

Topic: binary tori read through a 5 x 5 window by a camera whose rotation is unknown. Question: how large can such a torus be when every window and its three turns are pairwise distinct and any two turned windows differ in at least two cells? Known example 36 cells; ceiling 4,193,280. Problem: orientability and window distance are each achievable alone; nobody has shown both in a periodic binary array above 36 cells or computed an exact maximum for any window size; so we do not know whether the constraints compose or compete. Fourth step: Dothraki-style sensing that rejects a single misread without four-window agreement, tested in a simulated camera.

## Research statement v2 (after results and both reviews)

- Interest: patterns that let a sensor work out where it is from a single glance.
- Topic: binary tori read through a u x u window by a camera whose quarter-turn orientation is unknown.
- Question: unchanged; do the requirements compose or compete?
- Problem: orientability (Burns and Mitchell 1993) and window distance (Berkowitz and Kopparty 2016) each assume away the other's concern; without an answer a designer cannot tell whether requirements can be stacked or must be paid for in size.
- Claim: they compete (proved computationally at 3 x 3; suggested by search at 4 x 4 and 5 x 5), and the extra cost appears when the pattern must close on itself. Supporting points: the ceilings (4,193,280 for 5 x 5; 8,192 for 4 x 4), tight for window codes; 3 x 3 maximum 36 against at least 85; open patches against tori (168 against 144); search ratios about 9 and about 20; 256 x 256 exists; XOR family 36, interleave 280 (admissible), 308 unrestricted.
- Hypotheses: both falsified as stated; a graded H2 supported, exploratory.
- Fourth step: simulated camera, size-matched 6 x 6 pair, wrong reads at noise 0.3 from 8.5 to 2.6 percent at the same correct rate; worse on multi-error reads (38 against 29 percent); 0 of 103,801 single-error reads wrong (an implementation check); 3.9 to 16.8 million lookups per second.
- Significance: designers should not expect to stack requirements and stay near the counting bound; ask for distance where density makes it pay.
- Open: 3 x 3 orientation-only maximum (85 to 120); 4 x 4 strong form (441 to 8,192); unrestricted interleave (308 to 512); 5 x 5 strong form (65,536 to 4,193,280); constant parity; distance 3 for correction.
- Limits: search brackets from one method and few seeds; exact results computational without DRAT certificates; camera simulated; no Google Scholar.

## Glossary fixed in Phase 2

torus, window, turned window, 4-orientable, strong form, weak form, window distance, ceiling, orbit bound (file 13).
