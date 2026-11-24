# Verification report (S8)

Written 23 Nov 2026 against the code at 5cdb036, the tip of `main` (the report's own commits on top of it change only this file and the checklist; worktree `.worktrees/s8-verify`, branch `chore/s8-verify`). It covers everything that runs without the robot. The physical session is on Friday 27 Nov (`docs/jigsaw/FRIDAY_RUNBOOK.md`); its results go in the last section, which is left as an empty structure.

Requirements are from `docs/jigsaw/S8_verification.md` (Spec, Q1 to Q11, and the v2 box). "DECISIONS n" means entry n of `docs/jigsaw/handoff/DECISIONS.md`.

## Summary

Verified in this report:

- Every count and interval in `results/sim_summary.md` (20 counts, 10 intervals) was recomputed from the two CSVs by two separate scripts, neither using repository code. All match exactly (Q3).
- The three S2 runs (df9ec89, 46eb97b, 8f3b33a) give identical count columns; I compared the files of all three myself (Q2). None of them was a fresh clone.
- `tests/test_end_to_end.py` passes at 5cdb036 (1 passed in 7.46 s), and it fails when the turn 1 and turn 3 sentences are swapped (Q5).
- Six conventions traced to every use. All code agrees; the spoken turn sentence and the camera's channel order stay open until Friday (Q4).
- Every signature in `CONTRACTS.md` matches the code, with documented additions (Q7).
- 21 `UNVERIFIED` marks in the code, each listed with what clears it and the Friday step that does so (Q8).

Headline numbers (simulation, seed 1, n = 300 per condition, commit column 8f3b33a; Wilson 95 percent intervals):

- Prediction 1, strong pattern, wrong reads among reads with at most one misread cell: 0 of 21436 for the single-window decoder and 0 of 21436 for the grid decoder on the rendered puzzle (0.00 to 0.02 percent each); 0 of 300 in the dense forced1 arm (0.00 to 1.26 percent); 0 of 1244 in the dense noise arm (0.00 to 0.31 percent). The puzzle presented at most 6 misread cells to the strong pattern, so the dense arms carry this test (Q9).
- Prediction 2, single-window half: forced1 wrong reads 67 of 300 on the control pattern (22.33 percent, 17.99 to 27.38) and 0 of 300 on the strong pattern (0.00 to 1.26). Exact enumeration of all forced1 cases gives 296 of 1296 (22.84 percent) and 0 of 1296. The four-window half was not run.
- Prediction 3: 0 of 21600 wrong for each pattern and decoder (0.00 to 0.02 percent). Both patterns score zero, so this experiment cannot separate them.

Pending:

- Q1 and Q2 results: the full `reproduce_all.py` run (the orchestrator fills these in).
- v2 clean-clone run of `tests/test_printing.py` and `tests/test_vision.py`: same run.
- Prediction 4, Q11 timing, the label check of `results/physical.csv` against the answer key, and the robot `UNVERIFIED` marks: Friday.
- The turn sentence (A13, runbook step 5) and BGR order (runbook step 1b): Friday.

Found during this check (details in the sections named):

1. `scripts/reproduce_all.py` at 5cdb036 does not run the simulations or `make_figures.py`; it lists them as "not covered" (Q1). Commit 9ac5db4, which adds them, is on `fix/a4-print-verify` and not in `main`.
2. `FRIDAY_RUNBOOK.md` step 6 lists "an ask answer can be followed by a shake for the same piece (DECISIONS 22)" as known behaviour. A4 app F4 (e64b1ec) fixed that: `app.py:130` calls `Stable.mark_answered()`, and `stable.py:56-57` then blocks the give-up (Q11 section, "Documentation drift").
3. `tests/test_end_to_end.py:52` converts the pypdfium2 render with `COLOR_RGB2GRAY`, but pypdfium2 5.15.2 returns BGR. The test still passes; the conversion nearly triples the tile error (Q4, channel order).
4. The v2 check "no UNVERIFIED marks remain in `jigsaw/robot/`" cannot pass after Friday as planned: `reachy.py:58` (the 720p K correction) has no Friday step (v2 checks).
5. The paper outline describes the dense and physical experiments differently from what was run (Q9).

## Q1: clean-clone reproduction

Result: **pending the full reproduce_all run (orchestrator fills this in).**

What `scripts/reproduce_all.py` does at 5cdb036: it clones the current commit into `results/_repro/clone_<commit>` (lines 102 and 114), checks out the commit (117), runs `uv sync --locked` with every optional extra except `robot` (119, 55-58), rebuilds the print PDF with `scripts/make_print.py` and compares it with the committed PDF, by bytes and then rendered at 300 dpi (121-127, 81-91), runs `uv run pytest -rs` (129), accepts only the skip reasons "Piper voice file absent" and "JIGSAW_LIVE=1" (27-32), and writes `results/_repro/report.md`.

What it does not do at 5cdb036: run `run_sim_dense.py`, `run_sim_puzzle.py`, `make_figures.py` or `decode_physical.py`. They are in `NOT_COVERED` (lines 33-34), and the docstring (lines 7-8) says they "do not exist at this commit", which is no longer true: all four are in `scripts/` at 5cdb036. So the script at 5cdb036 does not meet Q1 as written. Commit 9ac5db4 ("reproduce_all regenerates the simulations and diffs them, Q1 and Q2"; parent 5cdb036; 158 lines changed in `reproduce_all.py`, 81 added to `tests/test_reproduce_all.py`) is on branch `fix/a4-print-verify` only. I did not read or run it.

Earlier evidence, superseded: the S8 prep clean-clone run gave PASS, 119 passed, 2 skipped, both "Piper voice file absent" (DECISIONS 13). That was before S2, S6 and the A4 fixes merged. The orchestrator reports 392 passed, 0 failed for the full suite after the last code merge (0a414fd), in the main checkout, not a clone; I did not rerun the suite (another process may be using the machine).

`decode_physical.py` on stored frames: no frames exist until Friday's capture.

To fill in: commit of the script that ran, exit code, pytest summary line, skip list, PDF comparison line, and the simulation diff from Q2.

## Q2: regenerated CSVs against the committed ones

Result: **pending the full reproduce_all run (orchestrator fills this in).**

| File | Rows | Compared | Differences except `commit` | Commit in committed file | Commit in regenerated file |
|---|---|---|---|---|---|
| `results/sim_puzzle.csv` | 288 | columns 1 to 17 | pending | 8f3b33a7095232296cb74811534ef13a68b71157 | pending |
| `results/sim_dense.csv` | 12 | columns 1 to 17 | pending | 8f3b33a7095232296cb74811534ef13a68b71157 | pending |
| `results/sim_summary.md` | | bytes | pending | | |

What the three earlier runs show. All three used seed 1 and n = 300 and were run in the S2 worktree with a clean tree, not in a fresh clone (DECISIONS 17, 31):

| Run | Code | Puzzle workers | Where the files are |
|---|---|---|---|
| 1 | df9ec89 | 16 | `.worktrees/s2-experiments/results/run_df9ec89/` (not committed) |
| 2 | 46eb97b (after the S2 review fix) | 16 | committed in f161830 |
| 3 | 8f3b33a (after the A4 fixes) | 6 | committed in 919ad8c, current |

I checked this myself with `cut -d, -f1-17` and `cmp`. Columns 1 to 17 of both CSVs are byte-identical between f161830 and the current files, and between the uncommitted df9ec89 files (289 and 13 lines, commit df9ec89431ff...) and the current files. `git diff --stat f161830 919ad8c` lists no change to `sim_summary.md`. The two figure PDFs changed bytes between those commits at the same sizes (19327 and 29458 bytes), so a byte comparison of the figures will fail; compare them rendered.

What this shows: the counts do not depend on the worker count (16 or 6), the S2 review fix to `misread_cells`, or the A4 change to `vision.read_grid` (DECISIONS 30). What it does not show: that a fresh clone with a freshly built environment gives the same numbers. Same machine, same environment and the same seed throughout, so the agreement is determinism, not independent replication.

## Q3: number trace

`results/physical_summary.md` does not exist yet (Friday). For `results/sim_summary.md`:

Row checks (both recounts): in both CSVs `correct + rejected + wrong = n` in every row, `wrong_le1_misread <= wrong`, and `wrong_le1_misread <= reads_le1_misread <= n`. Each file has one seed (1) and one commit (8f3b33a7095232296cb74811534ef13a68b71157). `sim_puzzle.csv` has 288 unique rows (6 px per cell x 1 tilt x 3 blur x 2 noise x 2 finger = 72 conditions, x 2 patterns x 2 decoders), and the single and grid rows of all 144 condition-pattern pairs share `mean_misread_cells` and `reads_le1_misread` (paired reads, E3).

Units of the `noise` column (DECISIONS 18): in `sim_puzzle.csv` it is the Gaussian pixel noise sigma passed to `photograph` (4 or 8 grey levels); in `sim_dense.csv` it is the cell flip probability p of the noise arm (0.01 to 0.2) and is empty for forced1.

Two recounts. Recount A is the independent agent's (its own Wilson, z = 1.96, closed form). Recount B is mine: Python standard library only, its own Wilson, and it formats each statement in `sim_summary.md`'s own wording and searches for that exact string in the file. All 10 interval statements and all 5 noise-arm lines were found verbatim.

| Statement | Value in `sim_summary.md` | Source and row filter | Recount A and B | Match |
|---|---|---|---|---|
| P1 puzzle, strong, single | 0 of 21436 (0.00%, 0.00 to 0.02%) | puzzle CSV, pattern=strong, decoder=single, sum `wrong_le1_misread` / sum `reads_le1_misread` | 0 of 21436 (0.00%, 0.00 to 0.02%) | yes |
| P1 puzzle, strong, grid | 0 of 21436 (0.00%, 0.00 to 0.02%) | puzzle CSV, pattern=strong, decoder=grid, same ratio | 0 of 21436 (0.00%, 0.00 to 0.02%) | yes |
| P1 dense, strong, forced1 | 0 of 300 (0.00%, 0.00 to 1.26%) | dense CSV, pattern=strong, arm=forced1, same ratio | 0 of 300 (0.00%, 0.00 to 1.26%) | yes |
| P1 dense, strong, noise | 0 of 1244 (0.00%, 0.00 to 0.31%) | dense CSV, pattern=strong, arm=noise, same ratio (298+297+276+233+140) | 0 of 1244 (0.00%, 0.00 to 0.31%) | yes |
| P2 forced1, orient, wrong | 67 of 300 (22.33%, 17.99 to 27.38%) | dense CSV, pattern=orient, arm=forced1, `wrong` / `n` | 67 of 300 (22.33%, 17.99 to 27.38%) | yes |
| P2 forced1, strong, wrong | 0 of 300 (0.00%, 0.00 to 1.26%) | dense CSV, pattern=strong, arm=forced1, `wrong` / `n` | 0 of 300 (0.00%, 0.00 to 1.26%) | yes |
| P3 puzzle, strong, single | 0 of 21600 (0.00%, 0.00 to 0.02%) | puzzle CSV, pattern=strong, decoder=single, sum `wrong` / sum `n` | 0 of 21600 (0.00%, 0.00 to 0.02%) | yes |
| P3 puzzle, strong, grid | 0 of 21600 (0.00%, 0.00 to 0.02%) | puzzle CSV, pattern=strong, decoder=grid | 0 of 21600 (0.00%, 0.00 to 0.02%) | yes |
| P3 puzzle, orient, single | 0 of 21600 (0.00%, 0.00 to 0.02%) | puzzle CSV, pattern=orient, decoder=single | 0 of 21600 (0.00%, 0.00 to 0.02%) | yes |
| P3 puzzle, orient, grid | 0 of 21600 (0.00%, 0.00 to 0.02%) | puzzle CSV, pattern=orient, decoder=grid | 0 of 21600 (0.00%, 0.00 to 0.02%) | yes |
| Noise p = 0.01, correct (strong / orient) | 273 of 300 / 273 of 300 | dense CSV, arm=noise, noise=0.01, `correct` / `n` | 273 / 273 of 300 | yes |
| Noise p = 0.01, wrong (strong / orient) | 2 / 6 | same rows, `wrong` | 2 / 6 | yes |
| Noise p = 0.02, correct | 247 / 247 of 300 | arm=noise, noise=0.02 | 247 / 247 | yes |
| Noise p = 0.02, wrong | 0 / 13 | same rows | 0 / 13 | yes |
| Noise p = 0.05, correct | 182 / 182 of 300 | arm=noise, noise=0.05 | 182 / 182 | yes |
| Noise p = 0.05, wrong | 10 / 31 | same rows | 10 / 31 | yes |
| Noise p = 0.1, correct | 113 / 113 of 300 | arm=noise, noise=0.1 | 113 / 113 | yes |
| Noise p = 0.1, wrong | 27 / 51 | same rows | 27 / 51 | yes |
| Noise p = 0.2, correct | 43 / 43 of 300 | arm=noise, noise=0.2 | 43 / 43 | yes |
| Noise p = 0.2, wrong | 51 / 67 | same rows | 51 / 67 | yes |

The noise-arm block gives counts only, without intervals. Each of its 20 counts was checked separately for strong and orient.

Numbers used in Q9 that are not in `sim_summary.md` (recount B, same filters): control pattern, noise arm, wrong among reads with at most one flip, 98 of 1244 (7.88 percent, 6.51 to 9.51); strong pattern, noise arm, all wrong reads, 90 of 1500; puzzle, strong, single, finger 0: correct 10787 of 10800 (99.88 percent, 99.79 to 99.93); finger 1: correct 7629 of 10800 (70.64 percent, 69.77 to 71.49).

All recomputations match exactly.

## Q4: convention audit

**Turn direction.** Defined in `CONTRACTS.md:61`, `jigsaw/types.py:14-15` and `CLAUDE.md:39`: `turn = k` means the camera image of a window is `np.rot90(printed_window, k)`, k quarter turns counter-clockwise as the camera sees it. Uses: `decode.py:39` undoes it with `np.rot90(window, -k)`; `decode.py:47-52` (`rot_affine`) and `:55-59` (`placement`) map seen cells back to G; `render.py:64` and `:73` turn the piece counter-clockwise on screen (for 90 degrees the matrix sends image +x to -y, the same sense as `np.rot90(., 1)`); `experiment/sweep.py:75-76` photographs at `90 k + U(-35, 35)` and takes k as the true turn; `experiment/contrast.py:45-47` uses `seen = np.rot90(window, k)`; `experiment/runner.py:115-118` (`classify`) counts a read correct only if the turn matches; `protocol.py:14` and `decode_physical.py:42-45` define the nominal angle as counter-clockwise as the camera sees the grid, so 90 is turn 1; `scripts/probes/p6_focus.py:14-15` takes `--turn` as `Read.turn`; `tests/test_vision.py:77-81` checks that renders at 0, 90, 180 and 270 degrees read as turns 0 to 3. All code uses agree. Two items stay open. (1) The spoken sentence (`voice/phrases.py:6-10` derivation, `:11-16` `TURN_SENTENCE`) is right only if the person flips the piece about its vertical axis and then turns it as seen from the picture side; if people turn it while looking at the grid, turns 1 and 3 are swapped (DECISIONS 14). `tests/test_end_to_end.py` encodes the same reading, so it cannot settle this. Friday's A13 check (runbook step 5) decides. (2) The rig differs between probes: `p6_focus.py:150` asks for the piece "grid side up over the green card" (lying under the camera), while `run_physical.py:24` and A13 have it held up with the picture toward the person (HANDOFF_S6 open question 1). The operator instruction at `run_physical.py:20-25` stays `UNVERIFIED` until step 5 and the 7a angle flags confirm it.

**Mirroring.** Defined in `CONTRACTS.md:59`, `types.py:5-9`, `CLAUDE.md:41` and `patch.py:26-32` (`front_to_g`, `g_to_front`): front lattice cell (i, j) carries `G[i + 1, 50 - j]`. Back-side uses: `decode.py:92` and `experiment/runner.py:141` convert decoded G cells to front coordinates with `g_to_front`; `render.py:29` and `:34-35` draw the piece outline and the print shift in back view; `runner.py:157` builds the truth raster the same way; `geometry.py:108` (`visible_cells`) uses `front_to_g`; `printing.py:27` places the back grid at `XB = PW - X0 - W` and mirrors the crosses (`:128`) and the how-to page (`:210`, `:229`); `scripts/replay_events.py:53-56` draws back views; `tests/test_end_to_end.py:58` cuts pieces from the back page the same way. No file mirrors after a `Read`: a grep for `front_to_g`, `g_to_front` and `W -` finds no use in `app.py`, `voice/`, `viewer/` or `viewer-ui/src`. All uses agree. Evidence that the chain is right end to end: `tests/test_end_to_end.py` passes (the announced front tile matches the picture), and the 21 Nov print check found 35 of 35 front tiles correct after a long-edge flip (HANDOFF_S5).

**Zero-based and one-based indexing.** Defined in `CLAUDE.md:40`, `types.py:11-12` and `CONTRACTS.md:179` (`physical.csv` zero-based). One-based outputs: `voice/phrases.py:27`; `protocol.py:44-46` (spoken prompt); `scripts/run_demo.py:94`; `decode_physical.py:122` and `:223-227` (summary); `p6_focus.py:76` and `:148`; `viewer-ui/src/BoardPanel.tsx:40`, `:45`, `:75` and `state.ts:75`; the answer key page, `printing.py:138` ("Rows 1 to 7 from the top, columns 1 to 5 from the left"). One-based inputs converted at the boundary: `run_physical.py:36-48` (`--pieces`) and `p6_focus.py:173-174`, `:196` (`--piece`). Zero-based: `Read`, both simulation CSVs, `physical.csv`, the frame sidecars, and the capture folder names `r{row}_c{col}_a{angle:03d}` (`protocol.py:16`, `:40-41`). All uses agree with the rule. One trap for readers: the label-check table in `physical_summary.md` prints the zero-based folder name (`decode_physical.py:219`) beside a one-based "decoded" value (`:122`) in the same row, so `r3_c1_a090` is the piece spoken as row 4, column 2. The demo's replay fallback must also use the zero-based folder names (see `DEMO_CHECKLIST.md`).

**Image channel order.** Defined in `CLAUDE.md:38`, `types.py:77` (`Frame.image` BGR) and `CONTRACTS.md:55`. Uses: `vision.py:30` (`COLOR_BGR2HSV`), `:120` (`COLOR_GRAY2BGR`, which expands a grey input to three channels) and `:124` (`COLOR_BGR2GRAY`); `render.py:14` (`MAT_BGR`), `:96` (warm light as B, G, R factors 0.97, 1.0, 1.02) and `:106` (skin colour in BGR); `robot/sources.py:33` (`cv2.imread`, BGR); `protocol.py:140` (`cv2.imwrite`); `decode_physical.py:76` (`cv2.imread`); `app.py:122` (`cv2.imencode` for the viewer); `robot/reachy.py:8-9` and `:144` (the SDK's `get_frame()`). All code paths agree, with two qualifications. (1) Whether the robot's frames really are BGR is `UNVERIFIED` (`reachy.py:144`, `p2_camera.py:10`; `p2.txt` has no red-object reading); runbook step 1b settles it. The reading is barely sensitive to the answer: I rendered one frame per piece (35 frames, 14 px per cell, tilt 0.06, blur 1.0, noise 4, random finger) and read each as is and with R and B swapped. `paper_mask` was identical in 35 of 35 (it uses only HSV saturation and value, which do not change when R and B swap), and `PieceReader` gave 31 correct, 4 rejected, 0 wrong both ways. A wrong order would show mainly as wrong colours in the viewer. (2) `tests/test_end_to_end.py:52` converts the pypdfium2 render with `COLOR_RGB2GRAY`, but pypdfium2 5.15.2 returns mode `BGR` (checked with `render().mode`). On page 2 (black and white) this does nothing. On page 1 (the picture) it weights R and B the wrong way round against the reference tile, which comes from PIL's correct RGB conversion. Measured over the 35 tiles: mean error at the announced rotation 6.78 grey levels with the current conversion and 2.35 with `COLOR_BGR2GRAY`; smallest gap to a wrong rotation 0.88 against 0.98 (tile (4, 0)). The test passes either way. Suggested one-line fix for its owner (S8, print and verification group): `COLOR_BGR2GRAY` and `COLOR_BGRA2GRAY` at line 52.

**The window used by the single-window decoder.** Defined in `experiment/runner.py:4-6` and `:121-133` (`decide_single`): the top-left-most complete 5 x 5 window of the read mask, scanning rows then columns, in the cell array as the camera sees it (`GridRead.cells` is "in the camera's orientation up to a quarter turn", `types.py:65`). After `decode_single` it uses `decode.placement` and the same off-puzzle and centroid steps as `decode_grid`, without the agreement and whole-piece consistency checks. Uses: `experiment/sweep.py:90-91`, the `single` rows of `sim_puzzle.csv`. Tests: `tests/test_experiment_runner.py:66-79` (equal to `decode_grid` on clean reads; ignores cells outside its window). The dense experiment has no offset question: `contrast.py:45-58` decodes the whole seen 3 x 3 window, so the v1 plan's "window at offset (0, 0) of a 4 x 4 patch" (`S2_experiments.md:140`) does not apply. Nothing else uses a single-window decoder: the demo, the probes and `decode_physical.py` all use `decode_grid` through `PieceReader` (`reader.py:20`, `decode_physical.py:28`), so the physical test says nothing about the single decoder (HANDOFF_S6 deviation 2). One definition, one user, consistent with `sim_summary.md` ("Decoder single is one 5 x 5 window"). Two consequences for the paper: which printed window is read depends on the turn and on the mask; and the misread count that defines "at most one misread cell" is taken over the whole piece, not that window (DECISIONS 20; `sweep.py:82`, `:96`).

**45-degree angles.** The simulation never photographs near 45 degrees: `sweep.py:29` and `:76` limit the angle to within 35 degrees of a quarter turn, as do the S1 vision tests. `vision.read_grid` finds the grid direction modulo 90 degrees (`vision.py:47-49`, `:131`, `:137-146`), so at 45 degrees two quarter turns are equally plausible. The physical capture uses 0 to 315 degrees in steps of 45 (`protocol.py:34`). `decode_physical.py:42-45` accepts either adjacent quarter turn at odd multiples of 45, the summary reports the two angle groups separately (`:161-168`), and prediction 4 compares only primary frames at multiples of 90 (`:180-200`), because the simulation has no 45-degree data and counts one turn as correct. The label check counts a turn as wrong only after that leniency (`:123-126`). `tests/test_protocol.py:23` renders angles 0 and 45. All uses agree; the leniency is stated in the summary text. At 45 degrees the robot announces whichever adjacent turn it reads, so the sentence leaves the picture 45 degrees off; the demo shows pieces only at quarter turns.

## Q5: end-to-end consistency test

`tests/test_end_to_end.py` (added in c3be23b, fixed in f896bf2 and 9821ddc) is the recommended addition. For each of the 35 pieces it renders page 2 of the committed print PDF at 6 px per mm (21.6 px per cell), cuts the piece, places it on the green mat turned k = index mod 4 quarter turns counter-clockwise (1280 x 720, no tilt, blur, noise or finger), reads it with `PieceReader`, phrases it with `phrase_read`, and parses the sentence back. Row, column and sentence must equal the truth and a hard-coded sentence table (lines 36-44), so a swap of the left and right sentences fails. Then it takes the front tile from page 1, turns it as the person sees it after flipping the piece about its vertical axis, applies the rotation the sentence asks for, and compares it with the picture tile at the announced position; the announced rotation must beat the other three by at least 0.5 grey levels (`MIN_GAP`, line 45). All four turns must occur.

Result at 5cdb036:

```
$ cd .worktrees/s8-verify && unset SSL_CERT_FILE && uv run pytest tests/test_end_to_end.py
.                                                                        [100%]
1 passed in 7.46s
```

Can it fail? I swapped `TURN_SENTENCE[1]` and `TURN_SENTENCE[3]` in memory (no file changed) and called the test: it failed with `wrong reads: [((0, 1, 1), (0, 1, 'Turn it a quarter turn to the right.')), ((0, 3, 3), (0, 3, 'Turn it a quarter turn to the left.')), ...`. This is the A4 print-verify major finding (9821ddc), now confirmed red and green.

Limits, from the file's docstring (lines 9-12) and this check: the flip model and `phrases.py` come from the same reading, so the test is self-consistent and does not show that people hold pieces that way (A13 decides); frames are clean, so it says nothing about rejecting bad input; three tiles pass with small margins against `MIN_GAP` = 0.5 (gaps 0.88, 0.97 and 1.37 grey levels, line 46); and the gray conversion at line 52 is wrong (Q4, channel order), which shrinks those margins slightly.

## Q6: reviews

Every module was reviewed by an agent that did not write it, first per workstream and then by the A4 group reviews, where a separate skeptic agent checked each finding before any fix (DECISIONS 25, 26). No review reported a critical finding.

Per-workstream reviews:

| Workstream | Findings | Outcome | Commits |
|---|---|---|---|
| S2 experiments | 9: 1 major, 8 minor | Major fixed. #2 rejected with evidence (`np.floor` mismatched the OpenCV pixel-centre convention in 37 percent of cells; `np.round` in 0); #5 rejected as already tested; #9 no change, as the reviewer concluded; the rest fixed or documented | 2098edd |
| S3 robot I/O | 12, severities not recorded in HANDOFF_S3 | 10 fixed in code; #11 (K correction) and #12 (no neutral move in `connect()`) recorded without a code change | 2cb5a30 |
| S4 voice | 12, none critical | Fixed except WAV fixtures for V7 and `small.en` | 6e7d018 |
| S6 app and physical | 13: 3 major, 10 minor | #1 rejected (spec A6); #8 and #13 no code change; the rest fixed | 2dc2770, ceaecc7, e109cbf, b11ca9f; handoff 454b32b |
| S7 viewer | 14: 2 major, 7 minor, 5 nit | All addressed; #13 left as an open question | af55601 |
| S8 prep | 7 | Fixed | f896bf2, 9f5fde4 |

A4 group reviews (reported / confirmed real / refuted / needs decision):

| Group | Counts | Highest severity | Fix commit |
|---|---|---|---|
| Core (types, patch, geometry, decode, vision, render, reader, pose) | 14 / 10 / 3 / 1 | minor | b3d7f19 |
| Robot and voice | 13 / 8 / 5 / 0 | minor | c857fb8 |
| App and protocol | 15 / 9 / 6 / 0 | minor | e64b1ec (F5 kept by design) |
| Experiment | 10 / 6 / 4 / 0 | minor | 6c84d5a |
| Viewer | 13 / 2 / 10 / 1 | major (1) | 9d1ee88 |
| Print and verification | 15 / 11 / 4 / 0 | major (1) | 9821ddc |

All six fix branches merged into `main` without conflicts at 0a414fd (DECISIONS 26).

Every major finding, with owner and status:

| Finding | Owner | Status |
|---|---|---|
| S2 #1: `misread_cells` counted off-raster cells as misread, which could hide an E9 contradiction | S2 | Fixed in 2098edd; rerun at 46eb97b changed no count (DECISIONS 17) |
| S6 #1: `ask` announces from one frame that has not passed Stable | S6 | Rejected: spec A6 asks for this (DECISIONS 22). Its side effect, a give-up after an ask answer, was later fixed by A4 app F4 (e64b1ec) |
| S6 #2: the five frames after the still run were saved without checks | S6 | Fixed in e109cbf |
| S6 #3: stillness measured against the run's first frame | S6 | Fixed differently in e109cbf; `STILL_IOU` stays UNVERIFIED (`protocol.py:37`) until runbook step 7a |
| S7 #1: on Windows a second viewer could bind a port already in use | S7 | Fixed in af55601 |
| S7 #2: a page opened or reconnected mid-demo had an empty board | S7 | Fixed in af55601 |
| A4 viewer F1: the board was not cleared on reconnect to a restarted server | S7 viewer group | Fixed in 9d1ee88 |
| A4 print-verify: the end-to-end test could not fail on a swapped turn sentence | S8 | Fixed in 9821ddc; red and green confirmed here (Q5) |

Open items that need a decision: core F5, `decode.placement` is public but not in `CONTRACTS.md` (DECISIONS 27, left as is); viewer F9, the overlay can lag the camera image by one frame (DECISIONS 28, deferred past Friday).

The flaky failure seen under full CPU load (DECISIONS 12, 24) was `tests/test_voice_tts.py::test_warm_cache_fast_afterwards`. c857fb8 replaced it with `test_warm_cache_real_voice_serves_the_cached_object`, which has no wall-clock bound (`grep` finds no timing assertion in the file).

## Q7: contract check

No `CONTRACT_CHANGE_*.md` exists in `docs/jigsaw/handoff/`, so there is no approved change to reflect.

| `CONTRACTS.md` item | Code | Matches |
|---|---|---|
| Constants `U`, `PIECE_CELLS`, `PUZZLE_ROWS, PUZZLE_COLS`, `MARGIN_CELLS`, `GRID_ROWS, GRID_COLS`, `CELL_MM`, `PIECE_MM` (39-45) | `types.py:23-30`; `GRID_*` computed as 72 and 52, `PIECE_MM` = 36.0 | yes |
| `Position`, `Read`, `Reject` and its seven reasons, `Decision`, `GridRead`, `Frame` (47-55) | `types.py:33-80` | yes |
| `FrameSource`, `Gestures`, `AudioOut`, `AudioIn`, runtime-checkable (56) | `types.py:83-105` | yes |
| `load_torus(path)`, `back_grid()`, `front_to_g(i, j)`, `g_to_front(a, b)`, `windows(pattern, u, wrap)`, `verify(pattern, u, wrap) -> dict` (68-72) | `patch.py:11, 21, 26, 31, 35, 46`; `verify` returns the four named keys | yes |
| `outline(r, c, seed=5)`, `edges(seed=5)` returning `(vdir, hdir, vedge, hedge)`, `visible_cells(r, c, tol_mm=0.5, offset_mm=(0, 0))` (78-80) | `geometry.py:69, 36, 88`; `SEED = 5` (line 16); return at line 66 | yes |
| `Table(dict)` with `.pattern .shape .u .wrap`; `build_table(pattern, u=5, wrap=False)` raising on a repeat (88-89) | `decode.py:16-32` (`ValueError`) | yes |
| `decode_single(window, table)`, `rot_affine(k, n)`, `decode_grid(cells, mask, table, u=5, min_agree=2, max_disagree=3)` (90-92) | `decode.py:35, 47, 62` | yes |
| `paper_mask(bgr)`, `read_grid(bgr)`, `undistort(image, K, D)` (102-104) | `vision.py:29, 118, 25` | yes |
| `piece_back(r, c, px_per_cell, offset_mm=(0, 0), grid=None)`; `photograph(...)` with every listed parameter and default (110-113) | `render.py:19, 60-63` | yes |
| `PieceReader().read(bgr) -> Decision`, keeps `last_grid` (116) | `reader.py:9-20` | yes |
| `piece_pose(H, K, D, shape)` (118) | `pose.py:8` | yes |
| `printing.build(picture_path, out_pdf)`; `PW, PH, X0, Y0, XB, BLEED, CROSSES` (120) | `printing.py:260` is `build(picture_path, out_path, seed=geo.SEED)`; constants at 25-30 | yes by position; the second parameter is named `out_path`, and a `seed` keyword with a default was added |
| `Stable(need=3, miss_limit=15)`, `update(d)`, `last` (126-129) | `stable.py:22-62` | yes; `gap()` and `mark_answered()` added (DECISIONS 29) |
| `classify(truth, decision)`, `wilson(k, n, z=1.96)` (131-132) | `experiment/runner.py:115`, `experiment/stats.py:5` | yes |
| `phrase_read(read)`, `phrase_reject(reason)`, `Command`, `match_command(text)` (134-137) | `voice/phrases.py:25, 30`; `voice/commands.py:7, 22` | yes |
| `synthesize(text) -> (pcm, rate)`; `CommandListener(audio_in, is_muted).poll()` (138) | `voice/tts.py:60`; `voice/stt.py:47-56, 97` | yes; `CommandListener` adds `transcribe=None, threshold=0.02` |
| `connect(host=None) -> ReachyRobot`; `ReplaySource(folder)`; `RenderSource(...)` (139-140) | `robot/reachy.py:229`; `robot/sources.py:20-25, 42-52` | yes |
| `FakeFrameSource(images)`, `FakeGestures()`, `FakeAudioOut()`, `FakeAudioIn(chunks)`; `tests/robot_live/` skipped unless `JIGSAW_LIVE=1` (145) | `fakes.py:10-52` (`FakeFrameSource` adds `K=None, D=None`); `pyproject.toml:25` ignores the folder, and its fixture skips without `JIGSAW_LIVE` | yes |
| Viewer events `frame`, `announce`, `give_up`, `board` (151-157) | `app.py:38-50, 88-89, 97, 102` | yes |
| Viewer event `head` (158) | not published: `Gestures` has no pose (HANDOFF_S6, A5); the viewer accepts it | not produced |
| Simulation CSV columns (166-167) | `experiment/runner.py:35-37` | yes |
| `physical.csv` columns (175-176) | `scripts/decode_physical.py:34-35` | yes |
| Layout: `jigsaw/experiment/` with `figures.py` (23) | figures are in `scripts/make_figures.py`; `runner.py` added | layout differs; no signature involved |

Additions that are not contract changes: `Stable.gap()` and `Stable.mark_answered()` extend the class without changing a frozen member (DECISIONS 29).

Documented deviations: `physical.csv` has no `seed` column and ends in `timestamp, commit` as section 6 says, which exempts `decode_physical.py` from the seed half of CLAUDE.md rule 4 (DECISIONS 21); the `noise` column means pixel sigma in `sim_puzzle.csv` and flip probability in `sim_dense.csv` (DECISIONS 18); `decode.placement` is public and imported by `experiment/runner.py:26` but not in the contract (DECISIONS 27).

## Q8: UNVERIFIED sweep

`grep -rn UNVERIFIED` over the repository, excluding `docs/`, finds 21 marks in code. Runbook steps are in `FRIDAY_RUNBOOK.md`.

| Mark | Assumption | What verifies it | Friday step |
|---|---|---|---|
| `jigsaw/app.py:27` | `SETTLE_S = 0.5` | `settling_time_s` from probe 5 | 3 |
| `jigsaw/protocol.py:37` | `STILL_IOU = 0.9` | dry-run capture: no early capture, none hung | 7a |
| `jigsaw/robot/reachy.py:58` | 720p K correction (DECISIONS 7) | K measured with a target of known size | none (runbook "Not covered on Friday unless there is time") |
| `jigsaw/robot/reachy.py:144` | `get_frame()` is BGR | p2 with a red object | 1b |
| `jigsaw/robot/reachy.py:182` | `goto_target` blocks; `MoveBusyError` | p4 on the robot, live gesture test | 1c, 2 |
| `jigsaw/robot/reachy.py:211` | `push_audio_sample` returns at once, 16 kHz | live tone test, TJ listening | 2 |
| `jigsaw/robot/reachy.py:221` | `get_audio_sample` float32 (N, 2) or None, 16 kHz | live recording test | 2 |
| `jigsaw/voice/stt.py:35`, `:40` | faster-whisper API | spoken commands recognised | 6 (command count, S4 V8) |
| `jigsaw/voice/tts.py:39`, `:48` | Piper API | already exercised: `tests/test_voice_tts.py` 5 passed with piper-tts 1.8.0 and the voice file (DECISIONS 3); `run_demo.py` loaded the voice (HANDOFF_S6) | none needed; S4 can remove the marks |
| `scripts/listen.py:18` | sounddevice `InputStream` | run `scripts/listen.py` on the laptop | none; the demo does not use it |
| `scripts/say.py:18` | sounddevice `play`, `wait` | run `scripts/say.py` once | none; the demo's audio fallback depends on it, so `DEMO_CHECKLIST.md` runs it the evening before |
| `scripts/probes/p2_camera.py:10` | BGR order | p2 with a red object | 1b |
| `scripts/probes/p4_nod.py:7` | `goto_target`, `create_head_pose` on the robot | p4 | 1c |
| `scripts/probes/p5_motion_media.py:32` | p5's timing assumptions | p5 | 3 |
| `scripts/probes/p6_focus.py:11` | how to stream 1920 x 1080 | p6 second run, if possible | 4 |
| `scripts/probes/p6_focus.py:29` | p6 frames from `get_frame` | p6 | 4 |
| `scripts/run_physical.py:20` | operator turn direction | A13 and no "angle" flags in the dry run | 5, 7a |
| `viewer-ui/src/ScenePanel.tsx:6` | horizontal field of view 70 degrees | camera K | none. The SDK's K in `p2.txt` (fx 667.27 at 1280 px wide) implies about 88 degrees; cosmetic, 3D panel only |
| `viewer-ui/src/scene.ts:38` | frame of the `head` pose | none possible yet: `app.py` publishes no `head` events | none |

Items marked only in handoffs:

- HANDOFF_S1:25, everything about real camera frames (paper colour under room light, glare, autofocus): runbook steps 4, 6 and 7.
- HANDOFF_S4:24-25, V7 and V8 unmeasured and the VAD threshold 0.02 untuned: step 6 counts commands understood.
- HANDOFF_S7:68-70, the head pose frame, the 70-degree field of view and the offset of the piece square in the 3D panel: no step.
- HANDOFF_S6 open question 1, the rig (piece held up or lying on the card): steps 4 and 5 use different rigs; the 7a angle flags show a mismatch.
- DECISIONS 15 and 16: why the 23 Nov live p3 run read nothing (step 4), 1920 x 1080 from a remote client (step 4), `connect()` not moving to neutral (open, runbook "Not covered").

Nothing in the reported simulation numbers depends on a marked item. `Frame.K` feeds only the viewer's 3D pose (`app.py:43`) and `decode_physical.py --undistort` (off by default).

## Q9: claims check, simulated half

Scope: predictions 1 to 3 as worded in `paper/12outline.tex:636-638`; prediction 4 is in the Friday section. The analysis unit is one rendered read (one synthetic frame, or one 3 x 3 window for the dense tori), not a physical piece.

**Prediction 1** (on a strong-form pattern, no read with at most one misread cell is wrong, for either decoder). Supported where tested. Rendered puzzle: 0 of 21436 for the single decoder and 0 of 21436 for the grid decoder (0.00 to 0.02 percent each). Dense tori, single decoder: 0 of 300 in forced1 (0.00 to 1.26) and 0 of 1244 in the noise arm (0.00 to 0.31). The four-window decoder was not run on the dense tori, so "for either decoder" is tested only on the rendered puzzle (DECISIONS 11). The strength of this claim comes from the construction, not the sample size: the printed grid has minimum distance 2 between turned windows (HANDOFF_S0), S1 checked every single-cell flip of every turned window (326,400) and found all rejected, and one misread cell anywhere on a piece never gave a wrong piece (HANDOFF_S1). In the simulation no violation was observed, and the puzzle presented almost no misread cells. On the puzzle the "at most one misread cell" bucket is nearly every read (21436 of 21600), and almost none of those reads had any misread cell: `mean_misread_cells` is above 0 in 3 of the 72 strong conditions (at most 0.0112), and n times that mean sums to 6.61 cells over all 21600 reads. That is an upper bound, because the mean is taken over reads with a grid; with `reads_le1_misread` as the denominator the three products are exactly 1, 2 and 3, so 6 misread cells in at most 6 reads. The control looks the same (5 of 72 conditions above 0, at most 0.365, at most 115.0 cells by the same bound) and also had 0 wrong reads. So "0 of 21436" mostly shows that the reader gets cells right; it barely tests the single-flip rejection property. That property is exercised by the dense forced1 and noise arms and by the two enumerations (S1's, and the forced1 enumeration under Prediction 2), not by the puzzle. Since the grid decoder ran only on the puzzle, its half of the prediction rests on the construction, not on the simulation. The dense arms are not empty tests: there the control pattern did produce wrong reads with at most one flip, 67 of 300 in forced1 and 98 of 1244 in the noise arm (7.88 percent, 6.51 to 9.51). The strong pattern is not immune to wrong reads with two or more flips: in the noise arm 90 of 1500 reads were wrong, all with at least two flipped cells, including 51 of 300 at p = 0.2. Definition the paper must state: "misread cells" are counted over all visible cells of the piece, not over the window the single decoder read (DECISIONS 20). For the single decoder this makes the bucket a subset of the window-level bucket; a single-decoder wrong read with at most one misread cell in its window but two or more elsewhere would fall outside it. No puzzle read was wrong at all, so nothing was missed in this data.

**Prediction 2** (dense tori, exactly one changed cell: the single-window decoder gives wrong reads on the control pattern, and the four-window decoder rejects nearly all such reads on both patterns). The single-window half is supported: 67 of 300 wrong on orient (22.33 percent, 17.99 to 27.38) against 0 of 300 on strong (0.00 to 1.26). I enumerated every forced1 case with my own decoder (36 positions x 4 turns x 9 cells = 1296 per torus): exactly 296 of 1296 wrong on orient (22.84 percent, inside the sampled interval) and 0 of 1296 on strong (all 1296 rejected). The four-window half was not run and the data neither support nor contradict it (DECISIONS 11; `sim_summary.md` says the same).

**Prediction 3** (rendered puzzle, wrong reads rare for both patterns and decoders). Supported: 0 of 21600 wrong for each of strong single, strong grid, orient single and orient grid (0.00 to 0.02 percent each). "Rare" was set in `scripts/make_figures.py:208` as a point estimate under 1 percent, a choice by the S2 agent, not the spec; with zero wrong reads any threshold gives the same answer. The experiment cannot separate the patterns, because the control also had zero wrong reads (DECISIONS 19). The outline already expects this (`12outline.tex:625-626`, `:654`). The separation shows only in the dense forced1 arm. The price of zero wrong reads is rejections: with a finger over the piece, the strong single decoder read 7629 of 10800 correctly (70.64 percent, 69.77 to 71.49), against 10787 of 10800 without (99.88 percent, 99.79 to 99.93). The paper should report rejection rates next to wrong rates.

Statements the data support, as the paper may write them:

1. On the rendered puzzle, no read of the strong pattern with at most one misread cell (counted over the whole piece) was wrong: 0 of 21436 for each decoder (Wilson 95 percent interval 0.00 to 0.02 percent). At most 6 of those reads had any misread cell, so this is not a test of single-flip rejection; statement 2 is.
2. On the 6 x 6 tori with one flipped cell, the single-window decoder read 67 of 300 windows of the control pattern wrongly (22.33 percent, 17.99 to 27.38) and 0 of 300 of the strong pattern; exact enumeration gives 296 of 1296 and 0 of 1296.
3. On the rendered puzzle, no read was wrong for either pattern or decoder: 0 of 21600 each (0.00 to 0.02 percent).
4. Under random cell noise the strong pattern still gives wrong reads (90 of 1500), each with at least two flipped cells.

Statements the data do not support: that the four-window decoder rejects nearly all single-flip reads on the dense tori (not run); that the strong pattern gives fewer wrong reads than the control on the rendered puzzle (both zero); anything about printed pieces, angles near 45 degrees, duplex misregistration (`offset_mm` was not swept; `sweep.py:27-28`), tilt other than 0.06, or lighting other than the renderer's gradient.

Limits the paper must state:

- Analysis unit: one rendered read. The 21600 reads per pattern and decoder are 300 reads in each of 72 conditions, drawn from 35 pieces, so each piece appears about 617 times. The Wilson intervals treat reads as independent Bernoulli trials; that holds for the renderer's random draws, but the intervals do not cover variation between physical pieces, prints or cameras.
- One seed. All reported numbers use seed 1; the pilot (seed 0, n = 50) also had no wrong puzzle read (HANDOFF_S2, not recomputed here). The three reruns repeat the same seed, so they show determinism, not sampling stability.
- The dense noise levels (p = 0.01, 0.02, 0.05, 0.1, 0.2) were chosen by the S2 agent; the spec gives no values (DECISIONS 10).
- Units of the `noise` column differ between the two CSVs (DECISIONS 18).
- The paper outline describes the experiments differently from what ran. `12outline.tex:628` says each dense read is a 4 x 4 patch with four 3 x 3 windows; the run decoded a single 3 x 3 window. Lines 618 and 632 say every experiment, including the physical one, is decoded with both decoders; the dense run used the single decoder and `decode_physical.py` uses only `decode_grid`. Lines 613 and 631 say 40 pieces (about 320 presentations); v2 has 35 pieces and 280 presentations. Line 611 gives 20,000 reads per condition for the rendered puzzle (line 612 the same for the dense tori); the run used n = 300 per condition, which is 21600 per pattern and decoder on the puzzle and 300 per arm or noise level on the tori. The outline's patch numbers (30 x 48, 1,144 windows, 5,760 cases, lines 490, 500, 611, 626 and 647) are from v1; the printed grid is 72 x 52 with 3264 windows (HANDOFF_S0).
- "Four-window decoder" is not literal. `sim_summary.md` calls the `grid` decoder "the four-window decoder", but `decode_grid` (`decode.py:62-97`) decodes every complete 5 x 5 window in the mask; every window that decodes must vote for the same placement, since a second placement rejects the read as `inconsistent` (`decode.py:77-78`); that placement needs at least min(2, number of complete windows) votes (`:80`); and at most 3 cells over the piece may disagree with it (`:90`). The paper should describe it as implemented.

## Q10: demo checklist

See `docs/jigsaw/DEMO_CHECKLIST.md` (demo on 30 Nov). It uses only commands that exist in `scripts/` at 5cdb036 and states plainly where a fallback the spec asks for has no command: there is no flag that sends speech to the laptop while the robot is the frame source, and no script plays the recorded clip.

## Q11: timing

Result: **pending; needs the Friday dry run logs.**

What exists now is context, not a measurement of the full loop: about 145 ms per 720 x 720 rendered frame for the reader (HANDOFF_S1); 19.4 `get_frame()` results per second on the robot (p2.txt) and about 3.7 frames per second during the live p3 run, from which HANDOFF_S3 infers about 0.27 s per 720p frame for `PieceReader.read` on this laptop (an inference, HANDOFF_S3).

A gap to close on Friday: the demo log has no timestamps. `run_demo.py:66` sets the log format to `%(message)s`, and the final line (`run_demo.py:94-95`) gives a frame count but no duration. Frames per second and the time from presenting a piece to speech therefore cannot be read from the existing logs. Two ways that need no code change: run `time uv run python scripts/run_demo.py --source robot --host <IP> --no-voice-in --max-frames 200` and divide (this includes start-up time, and `--max-frames` counts dropped frames too, `app.py:56`); and time piece-to-speech from the 60 s clip (runbook step 8). Also, S4's V5 bound (cache warm-up under 60 s) is no longer asserted by any test since c857fb8, so start-up time is measured only by Friday's runs.

### Documentation drift found during this check

- `FRIDAY_RUNBOOK.md` step 6 still lists DECISIONS 22's "an ask answer can be followed by a shake for the same piece" as known behaviour. Since e64b1ec (A4 app F4), `app.py:130` calls `stable.mark_answered()` and `stable.py:56-57` returns no give-up after it. A shake can still follow an `ask` that lands on a rejected frame, but not a nod.
- `scripts/reproduce_all.py:7-8` says the simulation scripts do not exist at this commit; they do (Q1).
- `HANDOFF_S2.md:3` says the results files are not committed; they have been committed since f161830.
- `HANDOFF_S6.md` cites `protocol.py:35` and `run_physical.py:19`; the marks are now at `:37` and `:20`. The runbook already uses the new lines.
- `HANDOFF_S6.md:36` describes a local `decode_physical.wilson`; `decode_physical.py:27` now imports `jigsaw.experiment.stats.wilson` (DECISIONS 26).

## v2 checks

| Check | Status |
|---|---|
| Rerun `tests/test_printing.py` and `tests/test_vision.py` from a clean clone | **Pending the full reproduce_all run.** The clean-clone suite includes both files. An earlier clean clone passed them (DECISIONS 13), but that was before A4 core F3 changed `vision.read_grid` (b3d7f19, DECISIONS 30) |
| Compare `results/physical.csv` against the answer key page | **Pending Friday.** The answer key is page 3 of `print/reachy_debruijn_jigsaw.pdf` (`printing.py:133-138`), numbered one-based; `physical.csv` is zero-based, so key label = `piece_row + 1`, `piece_col + 1` |
| No `UNVERIFIED` marks remain in `jigsaw/robot/` | **Not met; expected until Friday.** Five remain: `reachy.py:58` (K correction), `:144` (BGR), `:182` (gestures), `:211` (audio out), `:221` (audio in). Friday steps 1b, 1c and 2 can clear four. `reachy.py:58` has no Friday step, so this check will still fail after Friday unless the K measurement is added or the mark is accepted as a stated limit |

## Commands run for this report

All from `.worktrees/s8-verify`, with the code and results files at 5cdb036, and with `SSL_CERT_FILE` unset. Scratch scripts lived in the session scratchpad and are not committed (S8 may edit only this file and the checklist here).

```
$ uv run pytest tests/test_end_to_end.py
1 passed in 7.46s
$ # recount B (stdlib only) of sim_summary.md from both CSVs
puz rows 288 bad 0; den rows 12 bad 0; puz unique 288; pairs 144 mismatched 0
10 of 10 interval statements and 5 of 5 noise lines found verbatim in sim_summary.md
$ # puzzle misread cells per pattern: sum of n * mean_misread_cells (upper bound) and of reads_le1_misread * mean_misread_cells
strong single rows 72 n 21600 le1 21436 wrong 0 wrong_le1 0 rows>0 3 max 0.011194 total n-weighted 6.61 le1-weighted 6.00
orient single rows 72 n 21600 le1 21357 wrong 0 wrong_le1 0 rows>0 5 max 0.364964 total n-weighted 115.03 le1-weighted 104.63
$ # count columns of the three runs: cut -d, -f1-17 then cmp
sim_puzzle f161830 vs current: identical; sim_dense f161830 vs current: identical
sim_puzzle df9ec89 vs current: identical; sim_dense df9ec89 vs current: identical
$ # exact forced1 enumeration on the 6 x 6 tori, own decoder
strong cases 1296 {'correct': 0, 'rejected': 1296, 'wrong': 0}
orient cases 1296 {'correct': 0, 'rejected': 1000, 'wrong': 296}
$ # end-to-end test with TURN_SENTENCE[1] and [3] swapped in memory
unmutated: pass
mutated (1 and 3 swapped): FAILED as it should: wrong reads: [((0, 1, 1), (0, 1, 'Turn it a quarter turn to the right.')), ...
$ # R and B swapped on 35 rendered frames
35 frames; paper_mask identical after the swap in 35
bgr: correct 31, rejected 4, wrong 0
swapped: correct 31, rejected 4, wrong 0
$ # pypdfium2 render mode, and the end-to-end tile errors under both conversions
pypdfium2 5.15.2: mode BGR rev_byteorder False
RGB2GRAY (test) smallest gaps: [(0.88, (4, 0)), (0.97, (5, 4)), (1.37, (5, 0))] mean own-rotation error 6.78
BGR2GRAY smallest gaps: [(0.98, (4, 0)), (1.05, (5, 4)), (1.52, (5, 0))] mean own-rotation error 2.35
```

## Physical results: pending Friday

To be filled from `results/physical.csv` and `results/physical_summary.md` after `FRIDAY_RUNBOOK.md` step 7c, under the same rules as Q9: exact counts k of n, Wilson 95 percent intervals, and only what the CSV supports. The reviewer subagent then reviews this section (runbook step 9).

### Run record

- Date:
- Commit of the `decode_physical.py` run (`commit` column):
- Robot, daemon version, SDK version:
- Resolution and distance (from `results/probes/focus_check.md`):
- Undistortion on or off:
- Presentations captured, of 280; frames, of 1,400:
- Interruptions and resumes:
- Runs or presentations discarded, and why (nothing is excluded automatically; every exclusion is listed here):

### Counts

Primary frames are f0 of each presentation; all frames are kept for robustness but are not independent reads.

| Frames | Nominal angles | n | correct | rejected | wrong |
|---|---|---|---|---|---|
| primary | multiples of 90 | | | | |
| primary | odd multiples of 45 | | | | |
| primary | all | | | | |
| all | multiples of 90 | | | | |
| all | odd multiples of 45 | | | | |
| all | all | | | | |

### Prediction 1 on the robot

Wrong frames: __ of __ primary, __ of __ all. `physical.csv` has no misread-cell column (HANDOFF_S6 deviation 2), so prediction 1 is confirmed on the robot only if no frame is wrong. Every wrong frame is listed in the summary and copied to `results/findings/`, and is inspected before it is classified (CLAUDE.md rule 5).

### Prediction 4: robot against `sim_puzzle.csv`

Wording: `12outline.tex:639`.

- Robot px per cell (median over primary frames with a grid):
- Nearest simulated px per cell:
- Robot proportions, primary frames at multiples of 90 degrees (n = __): correct __, rejected __, wrong __, each with its Wilson interval:
- Simulated rows at that px per cell (pattern strong, decoder grid; 12 rows: 3 blur x 2 noise x 2 finger), and whether each robot proportion lies inside each row's interval:
- Which simulated row or rows the paper compares against, and why (the robot's noise level is not measured; the S6 spec, line 163, asks for this to be recorded):

### Label check against the answer key

- Flags in `physical_summary.md` ("piece" or "angle"):
- Confirmation that the piece labels used in the capture came from the answer key (page 3, one-based) and that `physical.csv` (zero-based) matches them:
- Result of the turn-sentence check (A13, step 5), and whether the "angle" flags confirm the angle direction (step 7a):

### Timing (Q11)

- Frames per second of the full loop:
- Time from presenting a piece to speech:
- How each was measured:

### Limits

- One robot (Reachy Mini Wireless, daemon 1.15.0), one room, one lighting setup:
- How pieces were held (by hand, held up with the grid to the robot, or lying on the card), and by whom:
- Analysis unit: one primary frame per presentation; 35 pieces each shown at 8 angles, so presentations of the same piece are not independent:
- The operator knew each label while presenting (not blind):
- Angles were set by hand to the nominal value:
- Runs discarded:
