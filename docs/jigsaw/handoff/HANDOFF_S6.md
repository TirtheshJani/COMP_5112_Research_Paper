# HANDOFF S6: app loop and physical-test tooling (23 Nov 2026)

Branch `feat/s6-app` in `.worktrees/s6-app`, made from main with S0, S1, S3, S4, S5, S7 and S8 merged. Not pushed, not merged. Nothing in this session connected to the robot, moved it, played sound (on the robot or the laptop) or waited for a person. Everything that needs the robot, the printed puzzle or a person is in "HUMAN steps left" below.

## What was built

| Commit | Task | Change |
|---|---|---|
| 7e55861 | 1 (A1) | `jigsaw/stable.py` `Stable(need=3, miss_limit=15)`, `update(d)`, `last`; `tests/test_stable.py` (13 tests). |
| d606abc | 2 (A2 to A6) | `jigsaw/app.py` `run(source, gestures, audio_out, bus=None, listener=None, max_frames=None)`; `tests/test_app.py` (loop, events, settling, commands, A3 gate). |
| 1e3ba61 | 3 (A7) | `scripts/run_demo.py --source robot\|render\|replay [--host] [--no-voice-in] [--viewer] [--frames DIR] [--seed N] [--max-frames N]`; four tests in `tests/test_app.py`. |
| 10f719f | 5 (A8 to A12) | `jigsaw/protocol.py`, `scripts/run_physical.py`, `scripts/decode_physical.py`, `tests/test_protocol.py` (13 tests). |
| (this commit) | 6 | This note, and two UNVERIFIED marks added after 10f719f (`protocol.py:33`, `run_physical.py:19`) with the operator instructions reworded. |

### Stable (A1)

A presentation is the time a piece is in view; a `no_grid` reject ends it. `update` returns `"announce"` when the same `Read` (row, col and turn) has arrived `need` times in a row and its piece differs from `last`; the same piece at another turn is not announced again (`next` makes a new `Stable`). It returns `"give_up"` once per presentation after `miss_limit` frames without an answer; every frame that is neither `no_grid` nor the one completing a stable read counts as a miss. After an answer, or after the announced piece is read stably again, the presentation gives up no more. `no_grid` frames alone never give up, so an empty mat never makes the robot shake.

### App loop (A2 to A6)

- Order: on `announce`, publish `announce` then `board`, speak, nod. On `give_up`, publish `give_up`, speak `phrase_reject` of the reject reason at that frame (the default sentence if that frame was a Read), shake.
- A4: a frame is dropped, not read, while `audio_out.is_playing()` or when its `Frame.t` is earlier than the end of the last speech and gesture plus `SETTLE_S`. Speech and gestures block, so frames that arrive during them carry earlier stamps.
- A5: events are CONTRACTS v2 section 5. `grid` is the four image corners of cell corners (0, 0), (w, 0), (w, h), (0, h) mapped through `GridRead.H`; it is set whenever `read_grid` found a grid, also for `no_match` and similar rejects. `rvec`, `tvec` come from `pose.piece_pose` and are null without `K`. The JPEG goes to `bus.set_frame` before each frame event. A `board` event with `placed: []` is published at start. `head` events are not published: the `Gestures` interface has no pose.
- A6: `again` speaks the last announcement again without a gesture; `next` makes a new `Stable` (the board keeps its pieces); `stop` ends the loop; `ask` answers from the next frame that is read: announce if it decodes, else the rejection sentence and a shake.
- `run` takes two keyword-only test seams beyond the spec signature, `clock` and `synthesize`, and returns counts: frames taken, frames dropped, announced Reads, give-ups.

### Physical test (A8 to A12)

- Capture (`protocol.capture`, `run_physical.py`): 35 pieces in front order x angles 0 to 315 in steps of 45 x 5 frames, one voice prompt per presentation ("Piece row 2, column 3, angle 90."), a beep after each saved set. It never decodes; the test `test_the_protocol_never_decodes` parses the imports and allows only `jigsaw.vision.paper_mask` (plus `jigsaw.types`).
- Presence rule, my addition to "paper_mask finds it for 5 frames in a row": after each prompt the view must first change (an empty mat, or a piece overlapping the last saved mask by IoU below `STILL_IOU`), then the piece must be found in 5 frames in a row with every mask overlapping the run's first by at least `STILL_IOU`. Without the change rule the piece from the previous presentation would be saved before the operator turns or swaps it; without the stillness rule a piece being turned would be saved mid-turn. At the start of a run only an empty mat counts as a change.
- Nominal angle: counter-clockwise as the camera sees the grid, so angle 90 is turn 1. Operator wording (piece held up, grid to the robot, picture upright facing the operator at angle 0, turned clockwise as the operator sees the picture) follows the S6 v2 box and is unverified.
- Layout: `results/frames/r{row}_c{col}_a{angle:03d}/f{n}.png` and `f{n}.json` (piece, angle, frame index, `Frame.t`, wall time, resolution, K, D). A set is written to a `.partial` folder and renamed when complete. A run skips complete sets and deletes leftover `.partial` folders, so resuming overwrites nothing.
- Decode (`decode_physical.py`): one row per frame in the CONTRACTS section 6 columns, decoder `reader.PieceReader` (decode_grid). `kind` against the label: at multiples of 90 only that turn is correct, at odd multiples of 45 either adjacent turn. `px_per_cell` as in `p6_focus.py`; `windows` counts complete 5 x 5 windows in the mask. Refuses a dirty tree unless `--allow-dirty`; `commit` is `git rev-parse --short HEAD`. `--undistort` uses the K and D saved with each frame; the summary says whether it was on.
- Label check: a presentation is flagged when more than half of its frames decode to one other piece ("piece"), or to the labelled piece at a turn the angle does not allow ("angle"). Every wrong frame is also listed one by one and copied, with its sidecar and decision, to `results/findings/<presentation>/` (rule 5); the script exits with code 2 after writing everything. Nothing is excluded automatically.
- `results/physical_summary.md`: counts with Wilson intervals for primary frames (f0 of each set) and all frames, split by multiples of 90 and odd multiples of 45; prediction 1; prediction 4 against every `sim_puzzle.csv` row with pattern `strong`, decoder `grid` at the px per cell nearest the robot's median; the label check.
- Wilson: `jigsaw.experiment` is not on this branch, so `decode_physical.wilson` computes the score interval with a comment that it must equal `stats.wilson` once S2 merges. Tested against Newcombe (1998) Table I: 81/263, 15/148, 0/20, 1/29.

## Commands run and their output

All from the worktree with `SSL_CERT_FILE` unset. During most of this session another worktree (`s2-experiments`) ran `run_sim_puzzle.py` with 16 worker processes and the CPU stood at 100 percent, which explains the long times.

```
$ uv run pytest tests/test_stable.py
13 passed in 0.51s
$ # mutation check: miss limit off by one, and last compared as a whole Read instead of (row, col)
5 failed, 8 passed in 0.60s              (restored: 13 passed in 0.51s)
$ uv run pytest                          # after Task 1
204 passed in 122.70s (0:02:02)
$ uv run pytest tests/test_app.py -k "not gate"
14 passed, 1 deselected in 7.69s
$ # mutation check: no SETTLE_S after speech and gesture
FAILED tests/test_app.py::test_frames_during_speech_motion_and_settling_are_dropped
1 failed, 3 passed, 11 deselected in 1.72s
$ uv run pytest tests/test_app.py -k gate -s
A3 gate over 200 presentations: correct 187, rejected or given up 13, wrong 0
1 passed, 14 deselected in 124.23s (0:02:04)
$ uv run pytest                          # after Task 2, CPU at 100 percent from the S2 run
FAILED tests/test_voice_tts.py::test_warm_cache_fast_afterwards - assert (263...
1 failed, 218 passed in 1202.05s (0:20:02)
$ uv run pytest tests/test_app.py -k run_demo
4 passed, 15 deselected in 65.56s (0:01:05)
$ uv run python scripts/run_demo.py --source render --seed 0 --max-frames 40
announce: Row 1, column 5. Turn it a quarter turn to the right.
loaded Piper voice ...\assets\voice\en_US-lessac-medium.onnx
announce: Row 7, column 4. Turn it a quarter turn to the right.
announce: Row 7, column 1. Turn it a quarter turn to the right.
announce: Row 1, column 3. Turn it a quarter turn to the right.
(nod)
(nod)
(nod)
(nod)
40 frames, 4 dropped, 0 give-ups; announced: R1 C5 turn 3, R7 C4 turn 3, R7 C1 turn 3, R1 C3 turn 3
$ # truth for seed 0: pieces (0, 4), (6, 3), (6, 0), (0, 2) at angle 270 (turn 3)
$ # replay: 30 frames of render_source(1) written to a scratch folder (pieces (1, 1), (0, 0), (1, 4), angle 90)
$ uv run python scripts/run_demo.py --source replay --frames <scratch>/replay
announce: Row 2, column 2. Turn it a quarter turn to the left.
announce: Row 1, column 1. Turn it a quarter turn to the left.
announce: Row 2, column 5. Turn it a quarter turn to the left.
30 frames, 8 dropped, 0 give-ups; announced: R2 C2 turn 1, R1 C1 turn 1, R2 C5 turn 1
$ uv run pytest tests/test_protocol.py
13 passed in 386.19s (0:06:26)
$ # mutation check: Wilson without the z^2/4n^2 term, and one allowed turn at 45 degrees
2 failed, 11 deselected in 15.12s        (restored: 2 passed, 11 deselected in 14.85s)
$ uv run ruff check jigsaw/stable.py jigsaw/app.py jigsaw/protocol.py scripts/run_demo.py scripts/run_physical.py scripts/decode_physical.py tests/test_stable.py tests/test_app.py tests/test_protocol.py
All checks passed!
$ uv run pytest                          # final, at 10f719f, CPU still at 100 percent
236 passed in 561.12s (0:09:21)
$ # after the last edits (a comment in protocol.py, the instruction text and a comment in run_physical.py)
$ uv run pytest tests/test_protocol.py -k "run_physical or never"
2 passed, 11 deselected in 6.54s
```

236 = 204 after Task 1 (191 from main plus 13 in `test_stable.py`) + 19 in `test_app.py` + 13 in `test_protocol.py`.

The synthetic capture in `tests/test_protocol.py` (35 pieces x angles 0 and 45 x 5 frames, rendered at 12 px per cell) has three deliberate operator errors: presentation r0_c0_a045 shows piece row 7 column 5, r1_c1_a000 shows the right piece upside down, and frame 3 of r2_c2_a000 shows another piece. Its summary reports 339 correct, 0 rejected and 11 wrong of 350 frames; the 11 wrong frames are exactly those, and the label check flags r0_c0_a045 ("piece", row 7 column 5, 5 of 5) and r1_c1_a000 ("angle", turn 2, 5 of 5). `test_every_wrong_frame_is_a_deliberate_mislabel` fails on any other wrong frame.

## UNVERIFIED marks

- `jigsaw/app.py:27`: `SETTLE_S = 0.5`, placeholder until `scripts/probes/p5_motion_media.py` writes `settling_time_s` to `results/probes/motion_media.md` (DECISIONS.md entry 8).
- `jigsaw/protocol.py:33`: `STILL_IOU = 0.9`, not measured with the robot's camera.
- `scripts/run_physical.py:19`: the operator's turn direction in the printed instructions.

## Deviations and decisions

1. Spec A2 lists `decoder="four"`; v2 and the task use `PieceReader`, so there is no decoder argument.
2. Spec A10 asks for both decoders and a `misread_cells` column. The frozen CSV in CONTRACTS section 6 has neither a decoder nor a misread column, so `physical.csv` has one row per frame for `PieceReader` only, and prediction 1 is confirmed only when there is no wrong frame; otherwise the summary lists each wrong frame for inspection. A11 asks for a flag column; the flags are in the summary instead, for the same reason. No contract change is requested; if the paper needs the single-window decoder or misread counts on the physical frames, CONTRACTS section 6 needs `decoder` and `misread_cells` columns.
3. `decode_physical.py` has no `--seed` (CLAUDE.md rule 4): nothing in it is random and the section 6 schema ends with `timestamp,commit`, not `seed,commit`. It has the dirty-tree check and the commit column.
4. Spec A9 names `vision.find_quad`; v2 has no quad, and the task names `vision.paper_mask`.
5. The spec counts 40 pieces and 320 presentations; v2 has 35 pieces, so 280 presentations and 1,400 frames.
6. Without the robot, `run_demo.py` plays nothing: sentences are synthesized with Piper and logged, gestures printed.
7. The A3 gate runs each presentation as one `app.run` with up to 20 frames of one piece (more than `miss_limit`) and stops at the robot's first answer. Conditions per presentation: piece, turn, angle jitter of up to 35 degrees, px per cell 10 to 18, tilt, blur, noise, light, finger (30 percent) and background (90 percent mat, 5 percent clutter, 5 percent plain). It also asserts at least 150 correct, so that a gate that rejects everything cannot pass. It takes about two minutes.

## Noticed outside my files

- `tests/test_voice_tts.py::test_warm_cache_fast_afterwards` (S4) times `warm_cache()` against 60 s of wall clock. It failed once at 263 s while the S2 run held the CPU at 100 percent, and passed in the Task 1 suite run. It measures the machine's load as much as the code.
- `voice/stt.CommandListener.poll()` reads one microphone chunk per call, and the app polls once per frame. HANDOFF_S3 infers about 3.7 frames per second on the robot. If the robot delivers chunks faster than that, spoken commands will lag behind; Friday's demo will show whether `again`, `next` and `stop` respond in time.
- `scripts/reproduce_all.py` says to add `decode_physical.py` to `STEPS` when this branch merges.
- `paper_mask` counts any large low-saturation region as a piece, so a white wall or a shirt in view behind the green card makes the capture think a piece is present. The card must fill the camera view.

## Open questions

1. Is the physical rig a piece held up in front of the green card (what the instructions assume), or a piece lying on the card under the camera? In the second case the angle direction must be worked out again; the label check would show it as "angle" flags on every 90 and 270 presentation of the dry run.
2. Should a give-up use the most frequent reject reason of the presentation instead of the reason at the last frame?

## Review

This session could not start subagents, so the `reviewer` subagent has not reviewed this branch. Run it before merging.

## HUMAN steps left

Robot address as in HANDOFF_S3: `10.0.0.100`. Each step from the worktree with `SSL_CERT_FILE` unset.

1. A13, the turn sentence, on two real pieces. Start the demo without voice input:
   `uv run python scripts/run_demo.py --source robot --host 10.0.0.100 --no-voice-in --viewer`
   Take a piece, look at its picture upright, turn it a quarter turn clockwise as you see the picture, and hold it up with the grid facing the robot and the picture facing you, both of you upright. Expect "Turn it a quarter turn to the left" (turn 1). Do what the sentence says, as you see the picture: is the picture now upright? Then take a second piece (the app announces a piece only once unless it hears `next`), turn it a quarter turn counter-clockwise from upright, expect "Turn it a quarter turn to the right" (turn 3) and check the same way. If the robot says the other sentence, follow it anyway and write down what it said and whether the picture ended upright. The S8 end-to-end test found the sentences are right only if the person flips the piece about its vertical axis and then turns it as seen from the picture side (`jigsaw/voice/phrases.py` lines 7 to 10); holding the piece up with the picture toward you is that flip, so A13 decides whether that reading holds. Write the result here; if it fails, send S4 a one-line fix request, and change the instruction at `scripts/run_physical.py:19` too.
2. Replace `SETTLE_S`. Run probe 5:
   `uv run python scripts/probes/p5_motion_media.py --host 10.0.0.100 --move`
   Copy the value on the last line of `results/probes/motion_media.md` (`settling_time_s: <value>`) into `jigsaw/app.py:27`, remove the UNVERIFIED mark, then `uv run pytest tests/test_app.py` and commit `fix(S6): SETTLE_S from probe 5`. If the line says `none`, keep 0.5 and ask.
3. Five-piece dry run of the capture and the decode:
   `uv run python scripts/run_physical.py --host 10.0.0.100 --out results/frames_dry --pieces 1,1 2,3 4,5 6,2 7,4`
   `uv run python scripts/decode_physical.py --frames results/frames_dry --out results/physical_dry.csv --summary results/physical_dry_summary.md --findings results/findings/dry --allow-dirty`
   Check: no capture fired before you had turned or swapped the piece, and none hung with the piece held still (`STILL_IOU`, `protocol.py:33`); `results/physical_dry_summary.md` has no "angle" flags (confirms the angle direction, `run_physical.py:19`); the frames are sharp. Remove the UNVERIFIED marks that this confirms.
4. The real capture, all 35 pieces, about 45 minutes; run the same command again after any interruption:
   `uv run python scripts/run_physical.py --host 10.0.0.100`
5. Decode, after S2 has merged (for `results/sim_puzzle.csv` and `stats.wilson`) and with a clean tree:
   `uv run python scripts/decode_physical.py`
   It writes `results/physical.csv`, `results/physical_summary.md` and, for any wrong frame, `results/findings/`; exit code 2 means at least one wrong frame: read the label check before anything else (rule 5). Once S2 is merged, replace `decode_physical.wilson` with `jigsaw.experiment.stats.wilson` and rerun `uv run pytest tests/test_protocol.py`.
6. The 60 s backup clip: start the demo with the projector view, record 60 s of a person presenting pieces with the robot answering (phone or screen recorder):
   `uv run python scripts/run_demo.py --source robot --host 10.0.0.100 --viewer`
