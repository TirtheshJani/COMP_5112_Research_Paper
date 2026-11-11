# 15. The new direction: Reachy Mini and the two-sided jigsaw (11 November)

## What Aaron suggested (TJ's words, 16:32)

"I had a talk with my Professor Williams and he suggested a research topic about using Reachy Mini to sense orientations and Jigsaw puzzles, like what if we would have Reachy Mini as a companion to a jigsaw puzzle solver: when you hold a piece close to it, it will tell you exactly where it will go and what the window looks like on the back of it. So basically the jigsaw puzzle will be two-sided: one side would be a picture or abstract image and on the back it will be a binary de Bruijn grid."

TJ confirmed (16:40): Aaron meant it for this COMP 5112 research methods paper and presentation. If it is doable, work on it and plan it. First step: this context pack.

## Assessment given in chat (16:32 reply)

It is a strong application and fits the paper better than Dothraki does. Treat it as the paper's motivating application and physical test, not a new topic.

Why it fits:
- A held-up piece has exactly the paper's two problems. Nobody holds a piece the right way up, so the pattern must give the turn as well as the position (4-orientability). A plain de Bruijn grid fails for the reason on the poster: a turned window can equal a different window, so Reachy would confidently name the wrong place. A hand-held piece under room light gets cells misread, which is what the strong form is for (a single misread is rejected, not decoded to a wrong place).
- The sizes work. A 1,000-piece puzzle (25 x 40 pieces) with 6 x 6 cells per piece needs a 150 x 240 grid = 36,000 cells; the stored 256 x 256 strong-form torus has 65,536, so the puzzle can be cut from a torus that already exists (`results/witnesses/u5s4d2_R256C256_seed0.npz`). Any rectangle cut from a strong-form torus keeps the property, because its windows are a subset of the torus's.
- Each 6 x 6 piece contains four 5 x 5 windows, so Reachy also gets Dothraki's four-window cross-check for free.
- A puzzle does not wrap, so it is an open patch, not a torus. Proposition 10 found that open patches hold more turned windows at distance 2 than tori (168 against 144 at 3 x 3). The jigsaw gives that result a practical reason to matter, and opens the question of how large a strong-form open patch can be.

What it would fix in the paper: Section 8's camera is simulated and the paper lists that as a limitation. A physical read with Reachy replaces or backs it up, and answers Aaron's Lecture 10 point that an application is never a drop-in.

What makes it harder than it sounds:
- Continuous rotation: the theory covers four quarter turns; a hand holds a piece at any angle. The vision step must find the grid and square it up first; the pattern then settles which of the four turns it is.
- Piece shape: tabs and blanks cut into the grid, so some pieces will not show a clean 6 x 6 block; square-cut pieces are the sensible first version.
- Camera limits: resolution, focus distance, glare, perspective and fingers over cells decide how small cells can be.
- Mirroring: the back of a piece is a mirror image of its place on the front, so the reported column must be flipped (or the back pattern printed mirrored). Easy, but easy to forget.

The tension with the 9 November decision: Reachy was left out because hardware evidence was weak for the rubric and would cost the drafting week. Aaron suggesting it removes the first reason but not the second, and Space Apps takes 14 and 15 November. Suggested starting point: keep the paper's core as it is and build the smallest version first (print a region of the 256 x 256 torus, cut square pieces, have Reachy read a piece and report row, column and turn), giving a short physical-results section and a live demo for the talk.

## What is known about TJ's Reachy Mini

- Model: Reachy Mini Wireless (Pollen Robotics). Python SDK from Pollen Robotics. Camera and motorised head; no wheels.
- TJ's conversation app for it, Rocky (github.com/TirtheshJani/rocky_mini), v1 runs a locally trained Qwen model and was slow or unresponsive on the robot with the full stack running (missed turns; idle breathing kept running; no acknowledgement chord); v2 being designed. The 6 November plan said to keep Rocky's conversation stack off for camera work.
- Brain host: ROG Zephyrus G14 (GA402XZ), Ryzen 9 7940HS, 16 GB RAM, RTX 4080 Laptop GPU with 12 GB VRAM, Windows.
- The original Task 12 plan (6 November) for a Reachy camera test: read the SDK docs and record camera resolution, field of view, head degrees of freedom and roll range, frame grab and head pose from Python; print cards at 150 cells per inch (a plain torus patch and an orientable one); script roll angles 0, 90, 180, 270 (and in between if possible), grab a frame, find grid corners, perspective-warp, sample cell centres, decode, record true pose against decoded position and turn, 20 frames per angle; report accuracy per angle in results/reachy_orientation.csv with one figure. Risk noted: the head's roll range may not reach 90 degrees; then rotate the card instead.

## Not yet known (must be checked against the official docs, not memory)

Camera resolution, field of view, minimum focus distance, frame rate; head roll range; whether frames are processed on the robot or the laptop; SDK calls for frame grab, head pose and speech or display output; how Reachy can show "what the window looks like" (speech, a screen, a laptop display).

## Existing assets that carry over

- The decoder (otorus/decode.py: Decoder, sorted table, binary search, returns position and turn or a rejection) and the 256 x 256 strong-form and orientation-only tori, a natural experimental pair (same size, same window size).
- The camera simulator (otorus/camera.py), whose parameters (angle error, offset, blur, noise, threshold) become the things to measure physically.
- The size-matched 3 x 3 pair (6 x 6) if larger cells are needed: a 3 x 3 window piece could be tiny and easy to read.
- The PostScript and matplotlib renderers used for the poster figures, for printing the grid.

## Questions planning must answer (ask TJ one at a time)

1. Scope for the paper: a demo for the talk only, a short physical-experiment section measuring correct, rejected and wrong reads (strong form against orientation only), or also a new mathematical question about open patches?
2. Final paper due date and how much time is left after Space Apps.
3. Piece design: square pieces or real jigsaw cuts; cells per piece (6 x 6 gives four 5 x 5 windows); print size and resolution; front image.
4. Hardware facts from the Reachy Mini docs (above).
5. What Reachy reports and how (position on the puzzle, turn, a picture of the window; speech or screen).
6. Literature check for novelty: coded backs on jigsaw pieces, computer-vision jigsaw solvers, PuzzleBoard (a camera calibration pattern with position encoding, already cited), Anoto-style dot patterns.

Next step after this pack: brainstorm the scope with TJ (one question at a time), then writing-plans for a plan TJ signs off, then executing-plans.
