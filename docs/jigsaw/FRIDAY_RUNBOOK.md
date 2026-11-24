# Friday runbook: the physical session

Everything that needs the robot, the printed puzzle or a person. Part A finished the rest. Steps run in this order, one at a time: Claude says what to do and what to watch, TJ does it, and the outcome goes in the "Outcome" line before the next step starts.

Sources: `docs/jigsaw/handoff/HANDOFF_S3.md` ("Still needs the robot"), `HANDOFF_S4.md` (open questions), `HANDOFF_S6.md` ("HUMAN steps left"), `DECISIONS.md` and `DEMO_CHECKLIST.md`.

**Total time: about 3 hours**, of which the full capture (step 7b) is about 45 minutes.

## Stop rules (apply at every step)

1. **A wrong read or a wrong announcement stops everything.** That means the robot names the wrong row, column or turn, or a probe or decode reports `wrong`. Save the frame (the scripts write `results/findings/`), stop, and look at it with Claude before going on (CLAUDE.md rule 5). Never change a threshold to make it go away.
2. If the robot moves when no step asked it to, switch it off.
3. If a step fails twice for the same reason, stop that step, write what happened in its Outcome line and go on only if later steps do not depend on it.

## Before you start (10 minutes)

Bring: the printed and cut puzzle (35 pieces), the green card (about 15 cm square), something plainly red, a tape measure, a phone for the clip.

1. Robot on, on the same Wi-Fi as the laptop, conversation app stopped.
2. In the repo, in bash (Claude's shell):
   ```
   cd C:/Users/TJ/Documents/GitHub/COMP_5112_Research_Paper
   unset SSL_CERT_FILE
   git pull
   uv sync --inexact --extra dev --extra print --extra voice --extra viewer --extra experiment --extra robot
   uv run pytest
   ```
   In PowerShell the second line is `Remove-Item Env:SSL_CERT_FILE`.
3. Pass: the suite ends with `0 failed` (the Part A count is in `VERIFICATION_REPORT.md`).
4. The robot address used below is `10.0.0.100` (from `results/probes/p1.txt`). If `reachy-mini.local` resolves, either works (HANDOFF_S3 open question 3).

Outcome:

## Step 1: status, camera colour order, nod (6 minutes)

**1a. Status.**
```
uv run python scripts/probes/p1_status.py --host 10.0.0.100
```
- See: both endpoints answer, daemon state `running`, `wireless_version: true`, daemon version 1.15.0.
- Pass: same as `results/probes/p1.txt` from 23 Nov.

**1b. Red object (settles BGR or RGB).** Hold the red object so it fills the camera view, then run:
```
uv run python scripts/probes/p2_camera.py --host 10.0.0.100 --seconds 10
```
- See: per-channel means printed for the frames.
- Pass: if the frames are BGR, the last channel's mean is clearly the highest. Then remove the `# UNVERIFIED:` marks at `jigsaw/robot/reachy.py:144` and `scripts/probes/p2_camera.py:10`.
- If the first channel is highest instead, the frames are RGB. Stop: the adapter must convert at `reachy.py` before anything else runs (CLAUDE.md conventions: BGR inside the code).

**1c. Nod probe again** (`p4.txt` from 23 Nov is empty).
```
uv run python scripts/probes/p4_nod.py --host 10.0.0.100 --move
```
- See: one small nod, back to neutral.
- Pass: `results/probes/p4.txt` is no longer empty. Then remove the mark at `reachy.py:182` if no `MoveBusyError` appeared.

Outcome:

## Step 2: live robot tests (5 minutes)

```
JIGSAW_LIVE=1 JIGSAW_HOST=10.0.0.100 uv run pytest tests/robot_live -o addopts="" -s
```
In PowerShell: `$env:JIGSAW_LIVE = "1"; $env:JIGSAW_HOST = "10.0.0.100"; uv run pytest tests/robot_live -o addopts="" -s`.

Four tests, in order:
1. 50 frames in under 10 s.
2. Nod then shake, each under 1.5 s. TJ watches: a small nod, a small shake, the head back to neutral each time.
3. A 1 kHz tone for one second. TJ listens: one steady tone, no gap or click. The test checks timing only, so TJ's ear is the real check.
4. A 3 s recording. TJ speaks during it; the test saves a WAV and prints its peak level.

- Pass: `4 passed`, and TJ confirms the gestures, the tone and that the peak level rose while speaking.
- Then remove the marks at `reachy.py:211` (audio out) and `reachy.py:221` (audio in).

Outcome:

## Step 3: motion and media, then the settling time (10 minutes)

```
uv run python scripts/probes/p5_motion_media.py --host 10.0.0.100 --move
```
- See: the head nods and shakes while a tone plays and frames stream. At the end the probe asks: "Did the tone have a gap, a click or a pitch change while the head moved? [y/n]". TJ answers.
- Output: `results/probes/motion_media.md`, whose last line is `settling_time_s: <value>`.
- Then put that value into `jigsaw/app.py:27` in place of `SETTLE_S = 0.5`, delete its `# UNVERIFIED:` line, and run `uv run pytest tests/test_app.py`. Commit: `fix(S6): SETTLE_S from probe 5`.
- Pass: a number on the last line, frames not dropped during motion (the report says), and `tests/test_app.py` passes.
- If the line says `none`, keep 0.5 and write why in the Outcome.

Outcome:

## Step 4: focus check with printed pieces (15 minutes)

```
uv run python scripts/probes/p6_focus.py --host 10.0.0.100 --piece 4 2 --turn 0 --resolution 1280x720
```
- For each distance in turn (15, 20, 30 and 40 cm, camera to card, measured with the tape), TJ puts piece row 4, column 2 grid side up on the green card at that distance, upright, and presses Enter. The probe logs 20 frames.
- See: px per cell and the reader's decision per frame.
- Output: `results/probes/focus_1280x720.csv`, `p6_1280x720.txt` and `focus_check.md` with the recommended distance and resolution (at least 90 percent of frames read).
- 1920 x 1080: run again with `--resolution 1920x1080` only if the camera can be made to stream it. Nothing found so far lets a remote client switch resolution while streaming (HANDOFF_S3 open question 1). If it cannot, write that in the Outcome and stay at 1280 x 720.
- A wrong read stops the probe and saves the frame: apply stop rule 1.
- Pass: `focus_check.md` names a distance and resolution. Write both into `agents.local.md`, and remove the marks at `p6_focus.py:11` and `:29`.
- This step also explains why the 23 Nov live p3 run read nothing: 290 frames, 0 reads, probably too far. HANDOFF_S3 estimates about 8 px per cell at 30 cm.

Outcome:

## Step 5: turn sentences on real pieces, A13 (10 minutes)

```
uv run python scripts/run_demo.py --source robot --host 10.0.0.100 --no-voice-in --viewer
```
1. Take a piece and look at its picture upright. Turn it a quarter turn clockwise as you see the picture. Hold it up with the grid toward the robot and the picture toward you, both of you upright, at the distance from step 4.
2. Expect "Turn it a quarter turn to the left" (turn 1). Do what it says, as you see the picture. Is the picture now upright?
3. Take a second piece (the app announces a piece only once). Turn it a quarter turn counter-clockwise from upright. Expect "Turn it a quarter turn to the right" (turn 3) and check the same way.

- Pass: both pictures end upright.
- Why this matters: the S8 end-to-end test found the sentences are right only if the person flips the piece about its vertical axis and then turns it as seen from the picture side (`jigsaw/voice/phrases.py` lines 7 to 10; DECISIONS entry 14). Holding the piece with the picture toward you is that flip.
- If either fails: follow the sentence anyway and write down what it said and how the picture ended. The fix is to swap the turn 1 and turn 3 wording in `jigsaw/voice/phrases.py`, the operator instruction at `scripts/run_physical.py:20`, and the turn model in `tests/test_end_to_end.py`, all in one commit. Then run `uv run pytest tests/test_voice_phrases.py tests/test_end_to_end.py` and log it in DECISIONS.md.

Outcome:

## Step 6: five-piece demo dry run (15 minutes)

```
uv run python scripts/run_demo.py --source robot --host 10.0.0.100 --viewer
```
Open the viewer at http://localhost:8765. Present five different pieces one at a time over the green card, at the step 4 distance, each at a different turn.

- See and hear: one announcement per piece (row, column and turn sentence) with a nod; the board in the viewer fills in that piece.
- With fingers over the grid you should hear a reject phrase ("Move your fingers to the edge of the piece."); with the grid hidden, "Show me the grid side, over the green card."
- Voice commands: say "again", "next" and "stop" at least three times each across the run. Count how many were understood, out of 10 or more (S4 V8 target: nine of ten).
- Known behaviour, not a failure:
  - one empty-view frame while you hold a piece makes the robot repeat it (DECISIONS 23);
  - an "ask" answer can be followed by a shake for the same piece (DECISIONS 22).
- Pass: 5 of 5 pieces announced correctly, 0 wrong (stop rule 1). Write the voice-command count in the Outcome.

Outcome:

## Step 7: physical capture and decode (about 70 minutes)

**7a. Five-piece capture dry run (15 minutes).**
```
uv run python scripts/run_physical.py --host 10.0.0.100 --out results/frames_dry --pieces 1,1 2,3 4,5 6,2 7,4
uv run python scripts/decode_physical.py --frames results/frames_dry --out results/physical_dry.csv --summary results/physical_dry_summary.md --findings results/findings/dry --allow-dirty
```
The robot prompts each piece and angle by voice; every run, and every resumed run, starts by waiting for an empty card.

Check:
- no capture fired before you had turned or swapped the piece;
- none hung while the piece was held still (`STILL_IOU`, `jigsaw/protocol.py:37`);
- `results/physical_dry_summary.md` has no "angle" flags, which confirms the angle direction (`scripts/run_physical.py:20`);
- the frames are sharp.

Pass: all four hold. Remove the two UNVERIFIED marks they confirm. If the summary flags angles on every 90 and 270 presentation, the rig orientation differs from the instructions (HANDOFF_S6 open question 1): stop and fix the instruction first.

**7b. Full capture (about 45 minutes).**
```
uv run python scripts/run_physical.py --host 10.0.0.100
```
- 35 pieces x 8 angles (0 to 315 in steps of 45) x 5 frames = 1,400 frames.
- After any interruption, run the same command again: it resumes without overwriting.
- Pass: the script finishes all 280 presentations.

**7c. Decode (about 7 minutes; 1,400 frames at about 0.27 s each).** Commit first: the script refuses a dirty tree.
```
uv run python scripts/decode_physical.py
```
- Writes `results/physical.csv`, `results/physical_summary.md`, and `results/findings/` for any wrong frame.
- Exit code 2 means at least one wrong frame: read the label check in the summary before anything else (stop rule 1).
- Pass: exit code 0 and the summary has Wilson intervals and the comparison with `results/sim_puzzle.csv`.

Outcome:

## Step 8: demo clip and rehearsal (15 minutes)

```
uv run python scripts/run_demo.py --source robot --host 10.0.0.100 --viewer
```
- Record 60 s with the phone: a person presenting pieces, the robot answering, the viewer on screen. This is the fallback if the live demo fails.
- Then walk through `docs/jigsaw/DEMO_CHECKLIST.md` once as a rehearsal and tick each item.
- Pass: a 60 s clip in which every announcement is correct, and every checklist item ticked or noted.

Outcome:

## Step 9: results into the report (20 minutes, Claude)

1. Commit the evidence (results/ is git-ignored, so force-add exact paths; the frames stay local):
   ```
   git add -f results/probes/*.txt results/probes/*.md results/probes/focus_*.csv results/physical.csv results/physical_summary.md
   ```
2. One opus subagent fills in "Physical results" in `docs/jigsaw/VERIFICATION_REPORT.md` from `results/physical.csv` and `results/physical_summary.md`, under the same rules as Q9 (exact counts, Wilson intervals, only what the CSV supports). The reviewer subagent then reviews it.
3. Commit, push, and Claude gives TJ a 10-line summary of the final numbers and anything that contradicts the paper's predictions.

Outcome:

## Not covered on Friday unless there is time

- Measuring the 720p K correction (`reachy.py:58`, DECISIONS entry 7) needs a target of known size at a measured distance; no probe exists. Until then nothing in the paper may rely on the corrected K.
- Whether `connect()` should move the head to neutral (HANDOFF_S3 open question 5).
- Whether the SDK message "No Reachy Mini Audio USB device found!" matters for a remote client. Step 2 shows it in practice.
