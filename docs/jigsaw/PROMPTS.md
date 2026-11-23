# Prompts to implement the Reachy jigsaw (23 Nov 2026)

One prompt per Claude Code terminal. Start the terminal in the repo with the model and effort given, paste the prompt, and answer "go" once it has replied with its short plan. That reply is your sign-off step: the plan is already written into each prompt, so you only check it was understood.

```
cd C:\Users\TJ\Documents\GitHub\COMP_5112_Research_Paper
claude --model <model id>
/effort <level>
<paste the prompt>
```

Model ids: `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-fable-5-2`. Confirm the names in `/model` and the levels in `/effort` in your installed version.

## How these prompts save tokens

1. **No model for work you can do yourself.** Rerunning the tests, printing, cutting and the four probes cost nothing when you run them (P0).
2. **The cheapest model that can do the job.** Sonnet 5.5 writes the voice and viewer code, where the libraries are well known and the prompt is exact. Opus 5.5 at high effort handles the robot, the experiments and the app, where a mistake changes the paper's numbers.
   - Nothing uses xhigh or Ultracode. Ultracode plans parallel subagents for every task at xhigh effort, which multiplies usage. Where independent checking matters (S2 figures, S8 reviews), the prompt sends one small job to a cheaper subagent instead.
   - Fable 5.2 is optional, and only for one short, high-value pass in S8.
3. **Haiku for lookups, Sonnet for reviews.** The repo now has two subagents in `.claude/agents/`:
   - `sdk-scout` (Haiku) searches the SDK, `rocky_mini` or long files, and returns 15 lines instead of whole files.
   - `reviewer` (Sonnet) reviews each branch cold.
4. **Small context.** Each prompt lists the only files to read. The prompts replace the old v1 plans inside the specs, so the agent never reads them.
   - `CLAUDE.md` loads by itself and now has a token budget section: one test file at a time, never open binaries or images, and `/compact` after each task.
   - Start every workstream in a fresh session.
5. **Few skills.** Every skill an agent loads costs context. Each prompt names its skills:
   - The core set is `karpathy-guidelines`, `using-git-worktrees`, `executing-plans`, `test-driven-development` and `verification-before-completion`.
   - `systematic-debugging` is loaded only when a test fails for a reason the agent cannot see.
   - Extra skills appear only where they earn their place.
6. **Optional parts last.** P1 requirements (3D viewer, speech commands, simulator) come only after the P0 work is committed, so you can stop there.

## At a glance

| Prompt | Workstream | When | Model | Effort | Skills beyond the core set |
|---|---|---|---|---|---|
| P0 | you | now | none | | |
| P1 | S3 robot I/O | after P0 | Opus 5.5 | high | none |
| P2 | S4 voice | with P1 | Sonnet 5.5 | medium | none |
| P3 | S7 viewer | with P1 | Sonnet 5.5 | high | `frontend-design`, `playwright-skill` |
| P4 | S2 experiments | any time (needs only S1, done) | Opus 5.5 | high | `statistical-analysis`; its figures subagent uses `scientific-visualization` |
| P5 | S6 app and physical test | after P1 and P2 are merged | Opus 5.5 | high | none |
| P6 | S8 verification | after everything is merged | Opus 5.5 | high | `dispatching-parallel-agents`, `scientific-critical-thinking`, `avoid-ai-writing` |
| P7 | S1 reading without a mat | only if the demo needs it | Opus 5.5 | high | `systematic-debugging` |

After each terminal finishes, read its handoff note, merge its branch into `main` and push. Start the next wave from the updated `main`.

---

## P0: you, no model

In PowerShell:

```
cd C:\Users\TJ\Documents\GitHub\COMP_5112_Research_Paper
Expand-Archive "$HOME\Downloads\Lakehead-MSc\COMP-5112-Research-Methodology\COMP5112_Reachy_Jigsaw_Project.zip" "$env:TEMP\jig" -Force
robocopy "$env:TEMP\jig\COMP5112_Reachy_Jigsaw_Project" . /E
uv venv --python 3.12
uv sync --extra dev --extra print
uv run pytest
git add -A
git commit -m "S0, S1, S5 and S3 probes from chat (23 Nov)"
git push
```

`uv run pytest` should end with `40 passed`. If `uv` is missing, install it first with `pip install uv`.

Then do the following:

1. Print pages 1 and 2 of `print/reachy_debruijn_jigsaw.pdf` on one sheet: double-sided, flip on long edge, Actual size, matte card stock.
2. Check the crosses against a light and measure the ruler. Cut on the picture-side lines.
3. Cut a green card about 15 cm square for the reading mat.

With the robot on and the conversation app stopped:

```
uv sync --extra dev --extra print --extra robot
uv run python scripts/probes/p1_status.py
uv run python scripts/probes/p2_camera.py
uv run python scripts/probes/p3_live_read.py --seconds 60
uv run python scripts/probes/p4_nod.py --move
```

Add `--host <robot IP>` if `reachy-mini.local` does not resolve. During p2, hold something red in front of the camera. During p3, show five or six pieces over the green card. Each probe saves what it prints to `results/probes/p1.txt` to `p4.txt`, and that is what P1 reads.

---

## P1: S3 robot I/O (Opus 5.5, high)

```
You are executing workstream S3 (robot I/O) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, test-driven-development, verification-before-completion.
Read only: docs/jigsaw/CONTRACTS.md; in docs/jigsaw/S3_robot_io.md the v2 box and the Spec section (skip its Plan, this prompt replaces it); docs/jigsaw/handoff/HANDOFF_S3_probes.md; results/probes/p1.txt to p4.txt.
SDK lookups go to the sdk-scout subagent (.venv/Lib/site-packages/reachy_mini and ../rocky_mini). Do not open SDK files yourself.
Worktree: feat/s3-robot in .worktrees/s3-robot. Edit only jigsaw/robot/, scripts/probes/, tests/test_robot_*.py, tests/robot_live/, results/probes/, agents.local.md and the robot group of pyproject.toml.

Tasks
1. uv sync --extra dev --extra print --extra robot. Pin reachy-mini to the installed version in the robot group. Write results/probes/versions.txt with the SDK version and the daemon version from p1.txt.
2. jigsaw/robot/sources.py: ReplaySource(folder) and RenderSource(rng, pieces, **photograph_kwargs), both yielding Frame (BGR, time.monotonic(), K=None, D=None). Unit tests with no robot.
3. jigsaw/robot/reachy.py: connect(host=None) -> ReachyRobot implementing FrameSource, Gestures, AudioOut and AudioIn (CONTRACTS section 2).
   - Frames: skip None; BGR as p2.txt shows (convert only if it shows RGB); K and D if available.
   - Gestures: nod and shake with goto_target only, at most 12 degrees, under 1.5 s, back to neutral; catch and log MoveBusyError.
   - AudioOut: start_playing once at connect, resample to the robot's rate, push, block for the duration; is_playing true until then.
   - AudioIn: start_recording once, return mono float32 or None.
   - A failed connect names the three things to check: power, Wi-Fi, conversation app stopped.
   Unit tests with a stub mini object. Nothing imports reachy_mini at module import time.
4. Live tests in tests/robot_live/ (JIGSAW_LIVE=1): 50 frames in under 10 s; nod and shake; a 1 kHz tone for one second; a 3 s recording saved as WAV with its peak level. HUMAN: stop and ask me to watch and listen.
5. scripts/probes/p5_motion_media.py: does a goto_target during playback or capture drop frames or glitch audio? Write the answer to results/probes/motion_media.md.
6. HUMAN focus check: with printed pieces over the green card at 15, 20, 30 and 40 cm, at 1280x720 and 1920x1080, log for 20 frames each the px per cell (from GridRead.H) and the decision, using reader.PieceReader. Write results/probes/focus_check.md with the recommended distance and resolution.
7. agents.local.md at the repo root: Wireless robot, SDK version, host, probe results. Remove an UNVERIFIED mark only where a saved probe output confirms it.
8. Skip R12 (MujocoSource); the simulator serves no camera without the GStreamer webrtc plugin. Say so in the handoff.
9. Write docs/jigsaw/handoff/HANDOFF_S3.md. Run the reviewer subagent on the branch and fix its findings in your files.

First reply: your plan in at most 8 lines, then wait for my "go". Commit after each task. Do not push.
```

---

## P2: S4 voice (Sonnet 5.5, medium)

```
You are executing workstream S4 (voice) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, test-driven-development, verification-before-completion.
Read only: docs/jigsaw/CONTRACTS.md; in docs/jigsaw/S4_voice.md the v2 box and the Spec section (skip its Plan).
Lookups in ../rocky_mini go to the sdk-scout subagent.
Worktree: feat/s4-voice in .worktrees/s4-voice. Edit only jigsaw/voice/, scripts/say.py, scripts/listen.py, tests/test_voice_*.py, assets/voice/README.md and the voice group of pyproject.toml.

Tasks
1. jigsaw/voice/phrases.py.
   - phrase_read(read) returns "Row {row+1}, column {col+1}. " plus TURN_SENTENCE[turn]:
     0 "It is the right way up."
     1 "Turn it a quarter turn to the left."
     2 "Turn it upside down."
     3 "Turn it a quarter turn to the right."
     Add a comment that S6 confirms these on real pieces.
   - phrase_reject(reason):
     no_grid "Show me the grid side, over the green card."
     no_window "Move your fingers to the edge of the piece."
     anything else "I cannot read that one. Show me again."
   Tests for every turn and reason.
2. jigsaw/voice/commands.py: match_command, using the V6 table in the spec. Tests.
3. jigsaw/voice/tts.py: synthesize(text) -> (mono float32 in [-1, 1], rate) with Piper. Ask sdk-scout which Piper voice and loading code ../rocky_mini uses, and reuse that approach; the voice file lives in assets/voice/ (git-ignored, README explains where to get it). warm_cache() synthesizes all 35 x 4 read sentences and the reject sentences once; later calls return in under 5 ms. Imports of piper and onnxruntime stay inside functions (V9). The test is skipped when the voice file is absent.
4. scripts/say.py "text" plays through the laptop speakers (sounddevice), as the audio fallback.
5. Only after 1 to 4 are committed: jigsaw/voice/stt.py CommandListener (V7, V8). It is P1; the demo runs without it (--no-voice-in).
6. Write docs/jigsaw/handoff/HANDOFF_S4.md. Run the reviewer subagent and fix its findings.

First reply: your plan in at most 6 lines, then wait for my "go". Commit after each task. Do not push.
```

---

## P3: S7 viewer (Sonnet 5.5, high)

```
You are executing workstream S7 (viewer) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, test-driven-development, verification-before-completion, frontend-design, playwright-skill.
Read only: docs/jigsaw/CONTRACTS.md sections 1 and 5; in docs/jigsaw/S7_viewer.md the v2 box and the Spec section (skip its Plan).
Worktree: feat/s7-viewer in .worktrees/s7-viewer. Edit only jigsaw/viewer/, viewer-ui/, scripts/replay_events.py, scripts/export_outlines.py, tests/test_viewer_*.py and tests/data/events_sample.jsonl.

Tasks
1. jigsaw/viewer/events.py EventBus (W1) and server.py Flask app with serve(bus, port=8765) (W2, W3). Tests with the Flask test client.
2. scripts/export_outlines.py writes viewer-ui/src/outlines.json from jigsaw.geometry.outline for all 35 pieces (front view, mm).
3. tests/data/events_sample.jsonl (about 40 events in the CONTRACTS v2 section 5 format, frames carry "grid") and scripts/replay_events.py, which loops them with JPEG frames from jigsaw.render (W4).
4. viewer-ui with React 19, TypeScript and Vite, no component library:
   - camera panel with the grid polygon (green for a read, amber for a reject) and the decision text (W5);
   - a 7 x 5 board drawn with the real jigsaw outlines from outlines.json, filling an announced piece with its part of print/picture_portrait.png and highlighting it for 2 s (W6);
   - a large status line (W7);
   - reconnect every second with a "disconnected" note (W9).
5. Playwright tests for W5, W6, W7 and W9 against the replay server.
6. Build into jigsaw/viewer/static/ and commit the build, so the demo needs no Node (W10).
7. Only after 1 to 6 are committed: the 3D panel (W8, P1).
8. Write docs/jigsaw/handoff/HANDOFF_S7.md. Run the reviewer subagent and fix its findings.

First reply: your plan in at most 8 lines, then wait for my "go". Commit after each task. Do not push.
```

---

## P4: S2 simulated experiments (Opus 5.5, high)

```
You are executing workstream S2 (simulated experiments for the paper) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, test-driven-development, verification-before-completion; statistical-analysis only for task 4.
Read only: docs/jigsaw/CONTRACTS.md sections 2, 3, 6 and 7; in docs/jigsaw/S2_experiments.md the v2 box, Goals and Requirements (skip the v1 Plan).
Worktree: feat/s2-experiments in .worktrees/s2-experiments. Edit only jigsaw/experiment/, scripts/run_sim_puzzle.py, scripts/run_sim_dense.py, scripts/make_figures.py, tests/test_experiment_*.py and results/sim_*.

Tasks
1. jigsaw/experiment/runner.py:
   - classify(truth: Read, decision): the right piece with the wrong turn counts as wrong.
   - decide_single(grid_read, table): decode only the top-left-most complete 5 x 5 window, then use the same placement and centroid as decode.decode_grid, with no agreement or consistency check.
   - misread_cells(grid_read, M, truth_grid): map each visible cell centre through GridRead.H, then through the inverse of M from render.photograph(return_transform=True), into the piece's back-view grid, and count cells whose read bit differs.
   Unit tests, including one with a known flipped cell.
2. jigsaw/experiment/sweep.py run_puzzle(conditions, n, seed).
   - Each trial renders one frame with render.piece_back(grid=pattern) and photograph, reads it once with vision.read_grid, and decides with both decoders on the same GridRead (paired, E3).
   - Patterns: strong (patch.back_grid()) and orient (the 72 x 52 corner of orient_u5_256.npz).
   - Conditions: px per cell 8, 10, 12, 16, 22, 28; blur 0.5, 1.0, 1.5; noise 4, 8; finger 0, 1; tilt 0.06.
   - CSV per CONTRACTS section 6, ending in seed and commit. Refuse a dirty tree unless --allow-dirty (E8).
   - ProcessPoolExecutor seeded per condition, with the same output as serial (E11).
3. jigsaw/experiment/contrast.py run_dense(arm, levels, n, seed) works at the cell level, with no rendering: the 6 x 6 tori, u = 3, decode_single.
   - Arm forced1 flips exactly one cell of a turned window.
   - Arm noise flips each cell with probability p.
   - On strong, forced1 must give wrong == 0.
4. jigsaw/experiment/stats.py wilson(k, n). Test it against statsmodels proportion_confint(method="wilson") to 1e-9; statsmodels is used only in the test.
5. Stop on a contradiction (E9): any strong row with wrong_le1_misread > 0 saves the frame and cells to results/findings/ and exits non-zero.
6. Run a pilot with n = 50 per condition and report the run time. Then run the full set with n = 300 in the background and check only the final summary, not the log.
7. Dispatch one general-purpose subagent on Sonnet that loads scientific-visualization. Give it only the CSV paths, the column names and these specs: scripts/make_figures.py writes results/fig_puzzle.pdf (correct, rejected and wrong rates against px per cell, by pattern and decoder) and results/fig_dense.pdf (wrong rate in the forced1 arm with Wilson intervals), as vector PDFs with a colour-blind-safe palette and embedded fonts, and results/sim_summary.md, with one paragraph per prediction giving counts and Wilson intervals.
8. Write docs/jigsaw/handoff/HANDOFF_S2.md. Run the reviewer subagent and fix its findings.

First reply: your plan in at most 8 lines, then wait for my "go". Commit after each task. Do not push.
```

---

## P5: S6 app and physical test (Opus 5.5, high)

```
You are executing workstream S6 (app loop and physical test) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, test-driven-development, verification-before-completion.
Read only: docs/jigsaw/CONTRACTS.md; in docs/jigsaw/S6_app_physical.md the v2 box, Goals and Requirements (skip the v1 Plan); docs/jigsaw/handoff/HANDOFF_S3.md and HANDOFF_S4.md; results/probes/focus_check.md and motion_media.md.
Worktree: feat/s6-app in .worktrees/s6-app from main with S3 and S4 merged. Edit only jigsaw/stable.py, jigsaw/app.py, jigsaw/protocol.py, scripts/run_demo.py, scripts/run_physical.py, scripts/decode_physical.py, tests/test_stable.py, tests/test_app.py, tests/test_protocol.py and results/physical*.

Tasks
1. jigsaw/stable.py Stable (A1), with tests.
2. jigsaw/app.py run(source, gestures, audio_out, bus=None, listener=None, max_frames=None) using reader.PieceReader (A2 to A6).
   - Events follow CONTRACTS v2 section 5, with the grid corners taken from GridRead.H.
   - Tests with RenderSource and fakes:
     - 10 frames of one piece give one play and one nod;
     - 200 rendered presentations never announce a wrong piece (A3);
     - frames that arrive during speech or motion are dropped, using a fake clock and the settling time from motion_media.md (A4).
3. scripts/run_demo.py --source robot|render|replay [--host] [--no-voice-in] [--viewer] (A7). It must run with --source render on a machine with no robot.
4. HUMAN: confirm the turn sentences on two real pieces, at turn 1 and turn 3 (A13). If they are wrong, write the fix request for S4 in the handoff folder.
5. jigsaw/protocol.py and scripts/run_physical.py (A8, A9).
   - Capture 35 pieces x 8 angles (0 to 315 in steps of 45) x 5 frames over the green card, prompted by voice.
   - A piece counts as present when vision.paper_mask finds it for 5 frames in a row. The protocol never decodes.
   - Resume without overwriting.
   HUMAN: run it with me.
6. scripts/decode_physical.py (A10 to A12): results/physical.csv per CONTRACTS section 6, the label check, and results/physical_summary.md with Wilson intervals and the comparison with results/sim_puzzle.csv at the nearest px per cell.
7. HUMAN: record a 60 s clip of the demo working, as the fallback.
8. Write docs/jigsaw/handoff/HANDOFF_S6.md. Run the reviewer subagent and fix its findings.

First reply: your plan in at most 8 lines, then wait for my "go". Commit after each task. Do not push.
```

---

## P6: S8 verification (Opus 5.5, high)

```
You are executing workstream S8 (verification and demo rehearsal) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, verification-before-completion, dispatching-parallel-agents, scientific-critical-thinking (only for Q9), avoid-ai-writing (only for the report and the checklist).
Read only: docs/jigsaw/CONTRACTS.md, the Spec section of docs/jigsaw/S8_verification.md and every file in docs/jigsaw/handoff/.
Worktree: chore/s8-verify in .worktrees/s8-verify from main after S1 to S7 are merged. Edit only docs/jigsaw/VERIFICATION_REPORT.md, docs/jigsaw/DEMO_CHECKLIST.md, scripts/reproduce_all.py, tests/test_end_to_end.py and results/_repro/.

Tasks: Q1 to Q10 from the spec, with these v2 changes.
- Q5, end to end: tests/test_end_to_end.py renders page 2 of print/reachy_debruijn_jigsaw.pdf with pypdfium2, cuts each piece out with geometry.outline (mirrored to the back), reads it with reader.PieceReader, phrases it with voice.phrases, and checks that the front tile at the announced row and column, turned as the sentence says, shows the right part of print/picture_portrait.png the right way up.
- Q4, convention audit: also covers front coordinates, the turn sentences and the reading mat.
- Q6, reviews: dispatch the reviewer subagent in parallel, once per group (core: types, patch, geometry, decode, vision, render, reader, pose; robot and voice; app and protocol; experiment; viewer), each with only its file list. Do not use Ultracode.
- Q9, claims: only state what the CSVs support, with the exact counts.

First reply: your plan in at most 8 lines, then wait for my "go". Commit after each task. Do not push.
```

Optional, only if you have budget left: rerun Q9 alone in a fresh session with `claude-fable-5-2` at `/effort high`. Give it only `results/*.csv`, `results/*summary.md` and the paper's predictions. It should check the claims without seeing the first answer.

---

## P7: S1 reading without a mat (Opus 5.5, high, optional)

Use this only if the physical test or the demo shows that the green card is not practical.

```
You are executing the S1 remainder (reading a piece without a coloured mat) of the Reachy jigsaw. CLAUDE.md is loaded; follow it, including its token budget.
Skills: karpathy-guidelines, using-git-worktrees, executing-plans, test-driven-development, verification-before-completion, systematic-debugging.
Read only: docs/jigsaw/CONTRACTS.md sections 2 and 3; the v2 box of docs/jigsaw/S1_core_decode_vision.md; jigsaw/vision.py; tests/test_vision.py.
Worktree: feat/s1-nomat in .worktrees/s1-nomat. Edit only jigsaw/vision.py and tests/test_vision.py.

Goal: on render.photograph(..., background="clutter") frames, 0 wrong reads and at most 20 percent rejected. All existing tests must still pass.
Approach to try first: when paper_mask fails, fall back to cell evidence. Find the grid on the whole frame. Accept a cell only if at least three of its four borders show the gray grid line or a black/white step and its centre is uniform. Take the largest 4-connected set of accepted cells and fill its holes.
Never relax decode.decode_grid to get there. A wrong read is a finding: save the frame to results/findings/ and stop.
Finish with docs/jigsaw/handoff/HANDOFF_S1_nomat.md and the reviewer subagent.

First reply: your plan in at most 6 lines, then wait for my "go". Commit after each task. Do not push.
```
