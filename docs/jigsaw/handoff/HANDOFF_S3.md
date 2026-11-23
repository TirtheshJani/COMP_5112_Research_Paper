# HANDOFF S3: robot I/O (23 Nov 2026)

Branch `feat/s3-robot` in `.worktrees/s3-robot`. Not pushed, not merged. Nothing in this session moved the robot, played sound on it or waited for a person; p5 and p6 are written and not run.

## What was built

Earlier (P1 Tasks 1 to 4): `ReplaySource`, `RenderSource`, `ReachyRobot` and `connect()` with stub tests, probes p1 to p4, live tests in `tests/robot_live/` (never run; they run on Friday).

This session, one commit each:

| Commit | Change |
|---|---|
| 1db986a | `ReachyRobot.frames()` skips a frame byte-identical to the previous one (like None) and logs a warning after 2 s without a new frame, again every 2 s, and keeps waiting. `ReachyRobot(..., clock=time.monotonic)` takes an injectable clock for `Frame.t` and the warning. |
| 8f42362 | Fix to 1db986a: the 2 s timer restarts when the caller asks for the next frame, so a caller that pauses (an operator prompt in p6) does not cause a false stall warning. |
| 0a42994 | `connect()` drains stale frames and stale recorded audio after the first frame arrives: read and discard until the SDK returns None, at most 600 reads per stream. |
| 6d05733 | Fix to 0a42994: each stream also stops after 0.5 s. Every SDK read waits up to 20 ms for live data (`media/gstreamer_utils.py:132`), so with live audio arriving about that often the drain could have read up to the 600-read cap, about 12 s. |
| dcb51bb | `correct_k(K, height)`, a pure function: at 720 rows fy = 1.2 fy and cy = (3.6 cy - 216) / 3, fx and cx unchanged; other heights unchanged. `frames()` applies it to every frame; for another height it logs once that K is uncorrected. |
| f393597 | `scripts/probes/p5_motion_media.py` (P1 Task 5) and `scripts/probes/p6_focus.py` (P1 Task 6), with unit tests of their pure helpers in `tests/test_robot_probes.py`. |
| 953689f | `results/probes/p4.txt` copied from the main checkout and committed with `git add -f`. The file is 0 bytes. |
| (this commit) | `agents.local.md`, this handoff, and probe docstrings: the UNVERIFIED mark removed from p1 (confirmed by p1.txt), narrowed to the channel order in p2 (p2.txt confirms the connection, frame shape and K, D), and p3's rule reference corrected from rule 6 to rule 5. |

Probe 5. A thread reads `robot.frames()` through three phases: 5 s still and silent (baseline), nod, shake, nod, shake with 2.5 s of stillness after each, then a 6 s 440 Hz tone with one nod and one shake during it. Motion and sound go through `ReachyRobot` only (rule 6), and nothing moves or plays without `--move`. For each gesture window it reports new frames, frames per second and the largest gap, against the still phase, and asks the operator whether the tone had a gap, click or pitch change. Settling metric: mean absolute grey-level difference of consecutive new frames shrunk to 160 x 90. Threshold: twice the 95th percentile of that difference in the still phase, at least 0.5 grey levels. A gesture has settled at the first frame after `nod()` or `shake()` returns from which 5 consecutive differences are below the threshold. The value for S6 is the largest of the four motion-phase settling times, or `none` if any did not settle within 2.5 s. Output: `results/probes/motion_media.md`, last line `settling_time_s: <value>`; console in `p5.txt`.

Probe 6. One resolution per run (`--resolution 1280x720` or `1920x1080`). SDK 1.15.0 cannot switch the resolution while streaming: `GstWebRTCClient._apply_resolution` raises (`media/webrtc_client_gstreamer.py:160-166`), and the daemon only has `GET /api/camera/specs` (`daemon/app/routers/camera.py:51`). The script stops, writing nothing, if the first frame's size differs from the flag. For 15, 20, 30 and 40 cm it prompts the operator to place piece `--piece ROW COL` (one-based) over the green card, then logs 20 new frames with the `PieceReader` decision and px per cell from `GridRead.H` (mean image length of a cell's two sides at the grid centre). A wrong Read saves the frame to `results/findings/` and stops (rule 5). Output: `results/probes/focus_<resolution>.csv` per run and `results/probes/focus_check.md` rebuilt from all of them. Recommendation rule (my choice; the task did not fix one): at least 90 percent correct reads and no wrong read; then the highest read rate; ties go to the larger distance, then to 1280x720.

## Commands run and their output

All from the worktree, with `SSL_CERT_FILE` unset.

```
$ uv run pytest tests/test_robot_reachy.py
33 passed in 2.42s
$ uv run pytest tests/test_robot_probes.py
22 passed in 0.60s
$ uv run pytest tests/test_robot_sources.py
7 passed in 1.88s
$ uv run ruff check jigsaw/robot scripts/probes tests/test_robot_reachy.py tests/test_robot_probes.py
All checks passed!
$ uv run pytest
102 passed in 86.39s (0:01:26)
$ uv run pytest tests/robot_live -o addopts=""        # JIGSAW_LIVE unset
no tests ran in 0.41s
$ uv run python scripts/probes/p5_motion_media.py      # no --move: dry run, no connection
Dry run. Add --move to let the head nod and shake (10 degrees) and play a 440 Hz tone.
```

`p5_motion_media.py --help` and `p6_focus.py --help` printed their usage with exit code 0 and wrote no file in `results/probes/` (both parse arguments before teeing). To check that the new helper tests can fail, I changed the settling window index in p5 and inverted the distance tie-break in p6. With those changes, `uv run pytest tests/test_robot_probes.py` gave `3 failed, 19 passed`; after restoring the files it gave `22 passed`.

## UNVERIFIED marks (file:line)

- `jigsaw/robot/reachy.py:58`: the 720p K correction (orchestrator instruction, DECISIONS.md entry 7 on main; no probe has measured it).
- `jigsaw/robot/reachy.py:141`: BGR channel order of `get_frame()`.
- `jigsaw/robot/reachy.py:179`: `goto_target` blocks until the move ends and raises `MoveBusyError` (seen only on the mockup simulator; `p4.txt` is empty).
- `jigsaw/robot/reachy.py:206`: `push_audio_sample` returns at once and plays at 16 kHz.
- `jigsaw/robot/reachy.py:216`: `get_audio_sample` gives float32 (N, 2) or None at 16 kHz.
- `scripts/probes/p2_camera.py:10`: BGR channel order (no red-object reading in `p2.txt`).
- `scripts/probes/p4_nod.py:7`: p4 on the robot.
- `scripts/probes/p5_motion_media.py:31`: p5 on the robot.
- `scripts/probes/p6_focus.py:11`: how to get 1920 x 1080 from a remote client.
- `scripts/probes/p6_focus.py:28`: p6 on the robot.

Removed: `scripts/probes/p1_status.py` (both endpoints answered on the real robot; `p1.txt` shows `wireless_version: true`, `simulation_enabled: false`, `mockup_sim_enabled: false`).

## Still needs the robot

1. Live tests (R6, R7, R9, R10; a person watches the gestures and listens to the tone): `JIGSAW_LIVE=1 JIGSAW_HOST=10.0.0.100 uv run pytest tests/robot_live -o addopts="" -s`.
2. p2 red-object check, because `p2.txt` does not settle BGR vs RGB (no red object was held; the whole-scene channel means do not decide it): `uv run python scripts/probes/p2_camera.py --host 10.0.0.100 --seconds 10` with something red filling the view. If the frames are BGR, the last channel mean rises. Then remove the marks at `reachy.py:141` and `p2_camera.py:10`.
3. p4 again, because `p4.txt` is empty: `uv run python scripts/probes/p4_nod.py --host 10.0.0.100 --move`. Then `reachy.py:179`.
4. p5: `uv run python scripts/probes/p5_motion_media.py --host 10.0.0.100 --move`. The operator answers one question about the tone. S6 copies the last line of `results/probes/motion_media.md` into `app.py`.
5. p6 with a printed piece and the green card: `uv run python scripts/probes/p6_focus.py --host 10.0.0.100 --piece <row> <col> --resolution 1280x720`, then `--resolution 1920x1080` if the robot can be made to stream it (open question 1).
6. A measurement of the 720p K correction. No probe measures it yet; one would need a target of known size at a measured distance.

## Skipped: MujocoSource (R12)

Not built. The simulator serves no camera to a client without the GStreamer webrtc plugin (S3 v2 note; `HANDOFF_S3_probes.md`: "p2: not testable; the simulator needs the GStreamer webrtc plugin to serve a camera"). R12 is P1, and the task list for this session excluded it.

## Noticed outside my files

- `results/probes/versions.txt` promises a "connect warnings" line "below" that is not there. `p2.txt`, the first SDK connection, shows no version-mismatch warning. It does show `ERROR:reachy_mini.media.audio_control_utils:No Reachy Mini Audio USB device found!`, followed by the WebRTC audio chain reporting ready.
- `HANDOFF_S3_probes.md` describes p3 as a six-frame replay. The `p3.txt` now in `results/probes/` is a live run: 290 frames, no Read, 204 `no_match` and 86 `no_grid`. The piece and distance are not recorded. A guess, not measured: the piece was too far for the 720p stream. The SDK's 720p K (fx about 667) gives about 8 px per 3.6 mm cell at 30 cm, below the 9 px the reader is tested at. p6 will show the real numbers.
- p3 ran at 3.7 frames per second against p2's 19.4 `get_frame()` results per second. This suggests that `PieceReader.read` takes about 0.27 s per 720p frame on this laptop. It is an inference that matters for S6's loop rate, not a timing measurement.
- `tests/robot_live/test_live_robot.py` is kept as is. Because `frames()` now skips repeats and `connect()` drains, its `distinct` count is 50 by construction, and its first `next(it)` is redundant but harmless.

## Open questions

1. How can a remote client get 1920 x 1080? `set_resolution` raises while the stream plays, and nothing I found sets it before the pipeline starts. I tried nothing on the robot.
2. Is the SDK's "No Reachy Mini Audio USB device found!" harmless for a remote client? The live audio tests will tell.
3. Does `reachy-mini.local` resolve on this laptop? The saved probes do not say; versions.txt used the IP.
4. I did not read DECISIONS.md (not in this session's read list). The formula and its explanation come from the task text.

## Review

Not run. This session could not start subagents, so the `reviewer` subagent named in the workstream file still has to review commits 1db986a to the handoff commit.
