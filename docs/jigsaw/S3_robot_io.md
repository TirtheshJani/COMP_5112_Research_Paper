# S3 Robot I/O: connection, frame sources, gestures, audio, probes

> **v2 update (23 Nov): started.** Probes are written in `scripts/probes/`: `p1_status.py` (HTTP only), `p2_camera.py` (frames, resolution, K, D, channel order), `p3_live_read.py` (live reading of real pieces, or `--replay` of saved frames) and `p4_nod.py` (moves only with `--move`). p1 and p4 ran against the SDK 1.15.0 daemon in `--mockup-sim` mode on 23 Nov; p3 ran in replay mode on rendered 1280 x 720 frames. p2 and p3 live need the robot, and the simulator cannot serve a camera without the GStreamer webrtc plugin. The focus check is now: what px per cell does p3 report at your working distance? The reader is tested down to 9 px per cell. Everything else in this file (adapters `connect`, `ReplaySource`, `RenderSource`, gestures, audio) is still to build.

| | |
|---|---|
| Terminal | Opus 5.5, effort xhigh, Ultracode off |
| Branch and worktree | `feat/s3-robot` in `.worktrees/s3-robot` |
| Depends on | S0 merged |
| Blocks | S5 (piece size from the focus check), S6 (app) |
| Owns | `jigsaw/robot/` (`__init__.py`, `reachy.py`, `sources.py`, `mujoco_scene.py`), `scripts/probes/`, `tests/test_robot_sources.py`, `tests/robot_live/`, `results/probes/`, `agents.local.md` |
| Must not edit | core modules, `types.py`, `fakes.py` |
| Human needed | Robot powered on and on the same Wi-Fi as the laptop for Tasks 3 to 5; a printed test piece for Task 4 |
| Skills | `karpathy-guidelines`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `engineering:code-review` |

---

## Spec

### Problem

Nothing in this project has run on the robot. Every statement about the SDK in the earlier plan came from documentation, and the one earlier project that did touch the robot (`rocky_mini`, audited against SDK 1.9.0 in July) found eight places where the documentation-level assumptions were wrong. The repository is now at 1.15.0.dev0. This workstream replaces assumptions with measurements and hides the SDK behind the four Protocols, so that no other workstream imports `reachy_mini`.

### Goals

1. One function, `connect()`, returns an object that satisfies `FrameSource`, `Gestures`, `AudioOut` and `AudioIn` for the real Reachy Mini Wireless over the network.
2. Three other frame sources with the same interface: rendered images, a folder of saved frames, and (P1) the MuJoCo simulator.
3. A set of probe scripts whose saved output answers every `(probe)` item in the README and every open question below.
4. A focus check that tells S5 what piece size to print.

### Non-goals

- No on-robot app. The program runs on the laptop and is not installed through the robot's dashboard or published as a Hugging Face Space.
- No JavaScript SDK. The viewer (S7) talks to our Flask server, not to the robot.
- No motion beyond a nod, a head shake and a neutral pose.
- No head tracking, no antenna behaviour, no recorded moves.

### Facts from the SDK source (commit 44ef448, 19 Nov 2026) and from `rocky_mini`

- `ReachyMini(host="reachy-mini.local", port=8000, connection_mode="auto", media_backend="default", timeout=5.0, ...)`. In `auto` mode the client tries localhost first, then `host`.
- A remote client gets media over WebRTC. On Windows the GStreamer runtime arrives as the `gstreamer-bundle` wheel, a dependency of `reachy-mini`.
- `media.get_frame()` returns `(H, W, 3)` uint8 or `None`. `media.camera.resolution`, `.framerate`, `.K` (rescaled to the current resolution), `.D`, and `.set_resolution(CameraResolution.X)` exist on the camera base class.
- Wireless camera modes: 1280 x 720 at 30 fps (default) and 60 fps, 1920 x 1080 at 30 fps, and 3840 x 2592, 3840 x 2160, 3264 x 2448, 3072 x 1728 at 10 fps.
- With the default mode and the calibrated focal length scaled to 1280 pixels wide (about 667 pixels), a 5 mm cell covers about 22 pixels at 150 mm and 11 pixels at 300 mm. This is an estimate to be replaced by the focus check.
- Audio is 16 kHz float32. `start_playing()` before `push_audio_sample()`, which is non-blocking; `start_recording()` before `get_audio_sample()`, which returns `(N, 2)` or `None`.
- `goto_target(head=4x4 matrix, antennas=[right, left] radians, duration, method, body_yaw)` raises `MoveBusyError` when another move is running. `create_head_pose(x, y, z, roll, pitch, yaw, mm=False, degrees=True)` builds the matrix. Head pitch and roll are limited to plus or minus 40 degrees.
- `rocky_mini` found on 1.9.0 that `wake_up()`, `goto_sleep()`, `play_move()` and `play_sound()` start daemon-side audio or motion. Do not call them.
- The daemon has `--sim` (MuJoCo), `--mockup-sim` (no MuJoCo), `--scene`, `--headless`, `--no-media`. The MuJoCo backend renders `eye_camera` at 1280 x 720 and sends frames to the media pipeline over UDP port 5005. Scenes are MJCF files under `descriptions/reachy_mini/mjcf/scenes/`.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| R1 | P0 | Pin the SDK: install `reachy-mini`, record the installed version and the robot daemon's version, and pin the exact version in the `robot` optional group | `results/probes/versions.txt`; a warning from the SDK about a version mismatch is resolved or recorded |
| R2 | P0 | `RenderSource(patch, rng, **render_args)` and `ReplaySource(folder)` | Unit tests with no robot: both yield `Frame` objects with BGR images; `ReplaySource` yields files in name order and stops |
| R3 | P0 | Probe 1, connection and camera: connect over the network, print resolution, frame rate, `K`, `D`, save 10 frames, measure the achieved frame rate over 100 frames and the fraction of `None` frames | `results/probes/camera.txt` and ten PNG files |
| R4 | P0 | Probe 2, channel order: hold a red object in view; the script reports which channel is brightest in the saved frame | Recorded; `reachy.py` converts to BGR accordingly |
| R5 | P0 | Probe 3, focus check: frames of the printed test piece at 10, 15, 20, 30 and 40 cm, at 1280 x 720 and at 1920 x 1080; for each, pixels per cell (from the detected quad) and whether `read_cells` plus `decode_four` succeeds | `results/probes/focus_check.md` with a table and a recommendation for piece size and working distance |
| R6 | P0 | `ReachyRobot.frames()` yields `Frame` with BGR image, monotonic time, `K`, `D`; skips `None` frames; stops cleanly on `close()` | Live test (`JIGSAW_LIVE=1`): 50 frames in under 10 seconds |
| R7 | P0 | Gestures: `nod()` and `shake()` using `goto_target` only, each under 1.5 seconds, returning to the neutral pose; `MoveBusyError` is caught and logged, not raised | Unit test with a stub `mini` that records calls: the sequence of poses is within the safety limits. Live: both gestures look right on the robot |
| R8 | P0 | Probe 4, motion and media: does a `goto_target` interrupt the camera stream or the audio that is playing? | Recorded. If yes, S6 must not gesture while speaking |
| R9 | P0 | `AudioOut.play(pcm, rate)`: resample to the output rate, call `start_playing()` once at connect, push, block for the duration; `is_playing()` true until then | Unit test with a stub: a 22,050 Hz buffer arrives as 16,000 Hz with the right length. Live: a 1 kHz tone of one second is heard and lasts one second |
| R10 | P0 | `AudioIn.read()`: `start_recording()` once at connect; returns mono float32 or `None`; never raises on `None` | Unit test with a stub. Live probe 5: record three seconds, save a WAV, report peak level |
| R11 | P0 | `connect()` fails with a clear message when the robot is unreachable or another app holds the robot | Unit test with a stub that raises; message names the three things to check (power, Wi-Fi, conversation app stopped) |
| R12 | P1 | `MujocoSource`: a scene with a textured plane showing one piece back in front of the camera, read through `media.get_frame()` against `reachy-mini-daemon --sim` | 100 frames decode to the right piece. If the SDK cannot load a custom scene from outside its package, record why and stop; do not patch the SDK |
| R13 | P0 | `agents.local.md` at the repository root, as the SDK's agent guide asks: robot type Wireless, SDK version, connection details, probe results | File exists |

### Open questions (each is answered by a probe)

| Question | Probe | Blocking |
|---|---|---|
| Does the WebRTC media backend work from this Windows laptop without extra GStreamer setup? | 1 | Yes |
| Are `K` and `D` available to a remote client, and at which resolution are they valid? | 1 | No (pose is P1) |
| RGB or BGR? | 2 | Yes |
| Nearest sharp distance and pixels per cell there | 3 | Yes, for S5 |
| Can a remote client change the camera resolution? | 3 | No |
| Do gestures disturb media? | 4 | Yes, for S6 |
| Is H.264 compression at the working distance a source of misread cells? | 3 (compare 720p and 1080p decode rates) | No, but report it |
| Robot's IP address when `reachy-mini.local` does not resolve on Windows | 1 | Yes if mDNS fails |

---

## Plan

**Goal:** `from jigsaw.robot import connect` gives the rest of the project a robot that behaves like the fakes, and `results/probes/` holds the evidence.

### Task 1: Worktree and reading

- [ ] Create the worktree and `uv sync --extra dev --extra robot`.
- [ ] Record versions: `uv pip show reachy-mini`, `python -c "import reachy_mini, sys; print(sys.version)"`. Save to `results/probes/versions.txt`. Pin the exact version in `pyproject.toml`.
- [ ] Dispatch the two Explore subagents below and read their answers before writing adapter code.
- [ ] Write `agents.local.md` (robot type Wireless, compute on the laptop, SDK version).

### Task 2: Sources that need no robot (R2)

- [ ] `tests/test_robot_sources.py`:

```python
def test_replay_source_reads_folder_in_order(tmp_path):
    for n in (2, 0, 1):
        cv2.imwrite(str(tmp_path / f"f{n:03d}.png"), np.full((8, 8, 3), n, np.uint8))
    frames = list(ReplaySource(tmp_path).frames())
    assert [int(f.image[0, 0, 0]) for f in frames] == [0, 1, 2]
    assert frames[0].image.dtype == np.uint8 and frames[0].K is None

def test_render_source_frames_decode(patch, table):
    src = RenderSource(patch, np.random.default_rng(0), px_per_cell=16, size=720, count=20)
    for f in src.frames():
        assert f.image.ndim == 3 and f.image.shape[2] == 3
```

- [ ] Run (fail), implement in `sources.py`, run (pass). `RenderSource` exposes `truth` (row, col, angle) for the frame it last yielded, for use by tests. Commit.

### Task 3: Connection and camera probes (R3, R4, R11). HUMAN: robot on, conversation app stopped

- [ ] Write `scripts/probes/p1_camera.py`. It imports `reachy_mini` only inside `main()`:

```python
# UNVERIFIED until this probe has run: API names from src/reachy_mini/reachy_mini.py and media/camera_base.py
import argparse, time, cv2

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--host", default="reachy-mini.local")
    ap.add_argument("--out", default="results/probes"); a = ap.parse_args()
    from reachy_mini import ReachyMini
    with ReachyMini(host=a.host, connection_mode="network") as mini:
        cam = mini.media.camera
        print("resolution", cam.resolution, "fps", cam.framerate)
        print("K", cam.K); print("D", cam.D)
        got = none = 0; t0 = time.monotonic()
        while got < 100 and time.monotonic() - t0 < 30:
            f = mini.media.get_frame()
            if f is None: none += 1; time.sleep(0.005); continue
            if got < 10: cv2.imwrite(f"{a.out}/cam_{got:02d}.png", f)
            got += 1
        dt = time.monotonic() - t0
        print(f"frames {got} in {dt:.1f}s = {got/dt:.1f} fps, None polls {none}, shape {f.shape}, dtype {f.dtype}")

if __name__ == "__main__":
    main()
```

- [ ] Ask the author to power on the robot, stop the conversation app from the dashboard, and confirm. Run `uv run python scripts/probes/p1_camera.py | tee results/probes/camera.txt`.
- [ ] If the connection fails: use `systematic-debugging`. Check in order `ping reachy-mini.local`, `curl http://reachy-mini.local:8000/docs`, the robot's IP from the router with `--host <ip>`, then the SDK troubleshooting page (`docs/source/troubleshooting.md` in the SDK clone). Do not try workarounds that change the robot's software.
- [ ] If `cam` attributes are missing on the WebRTC backend, record exactly which, and fall back to `reachy_mini.media.camera_constants.ReachyMiniWirelessCamSpecs` scaled to the frame size for `K` and `D`. Mark it `UNVERIFIED` as a calibration.
- [ ] `p2_channels.py`: the author holds something red in view; the script saves a frame and prints the mean of each channel in the central region. Record whether index 0 or index 2 is red.
- [ ] Commit the probe scripts and outputs.

### Task 4: Focus check (R5). HUMAN: printed test piece

- [ ] Before S5 exists, print the test piece with a few lines: `cv2.imwrite("test_piece.png", draw_piece(piece_cells(patch, 0, 0), 60))` and print it scaled so the outer border is 40 mm. Ask the author to measure it with a ruler.
- [ ] `p3_focus.py`: for each distance the author is prompted to hold the piece (flat against a light card) and press Enter; the script saves 5 frames, runs `read_cells` and `decode_four`, and records pixels per cell (quad perimeter divided by 32) and the decode result. Repeat at 1920 x 1080 if `set_resolution` works for a remote client; if it does not, record that.
- [ ] Write `results/probes/focus_check.md`: the table, the nearest sharp distance, and a recommendation using this rule: choose the piece size and distance that give at least 10 pixels per cell with all 5 frames decoding. If 40 mm fails that everywhere, recommend 60 mm.
- [ ] Tell the author the recommendation. S5 uses it.

### Task 5: The adapter (R6 to R11)

- [ ] Unit tests with a stub `mini` object (a small class in the test file with the same method names, recording calls). Cover: channel conversion, skipping `None`, clean stop, the gesture pose sequences staying within plus or minus 25 degrees of pitch and yaw, `MoveBusyError` swallowed, resampling length, `read()` on `None`.
- [ ] Implement `jigsaw/robot/reachy.py`. Keep it under about 150 lines. `connect(host=None)` builds the `ReachyMini`, calls `media.start_playing()` and `media.start_recording()`, moves to the neutral pose with `goto_target(head=create_head_pose(), duration=1.0)`, and returns the `ReachyRobot`. `close()` stops both audio directions and exits the SDK context.
- [ ] Gestures: `nod` is pitch +12, -8, 0 degrees over about 1.0 second in three `goto_target` calls; `shake` is yaw +15, -15, 0. Confirm the sign and size on the robot and adjust once.
- [ ] `p4_motion_media.py`: play a 3-second tone while polling frames and performing a nod at second 1. Report the frame gap around the nod and whether the author heard the tone interrupted.
- [ ] `p5_mic.py`: record 3 seconds while the author speaks, save `results/probes/mic.wav`, print peak and RMS.
- [ ] Live tests in `tests/robot_live/` (skipped unless `JIGSAW_LIVE=1`). Commit.

### Task 6: MuJoCo source (R12, P1). Do this last, and only if Tasks 1 to 5 are done

- [ ] Install `reachy-mini[mujoco]`. Start `reachy-mini-daemon --sim --scene minimal` and run `p1_camera.py --host localhost`. Record whether frames arrive and what they show.
- [ ] Read how `--scene` resolves a name (Explore subagent). If it accepts only names inside the installed package, the options are: generate our scene file into a temporary copy of the scenes folder and pass its path if the loader allows a path, or stop and record that R12 needs an SDK change. Time-box this task to two hours.

### Task 7: Review and handoff

- [ ] Review subagent. `HANDOFF_S3.md` lists every probe, its output file, each open question with its answer, and everything still `UNVERIFIED`. Open the pull request.

### Subagent use

- Explore subagent A, at the start: "In the clone of https://github.com/pollen-robotics/reachy_mini (clone it to a temporary folder if not present), read `src/reachy_mini/reachy_mini.py`, `src/reachy_mini/media/media_manager.py`, `media/webrtc_client_gstreamer.py` and `media/camera_base.py`. Answer with file and line: (1) what object is `mini.media.camera` when the backend is WEBRTC, and does it expose `resolution`, `K`, `D`, `set_resolution`; (2) what colour order does `get_frame` return on the WEBRTC path; (3) does `goto_target` block until the move ends; (4) what does `push_audio_sample` do if `start_playing` was not called. Quote the lines. Do not edit anything."
- Explore subagent B: "In `C:\Users\TJ\Documents\GitHub\rocky_mini`, read `docs/hardware-audit.md`, `docs/bring-up.md`, `rocky_mini/sources/` and `rocky_mini/vision/camera.py`. List every lesson about connecting to the Wireless robot, the camera, audio output and audio input that would apply to a laptop-side client. Quote the file and line. Do not edit anything."
- Explore subagent C (Task 6 only): "Find how `reachy-mini-daemon --sim --scene <x>` locates the scene file, and how `eye_camera` frames reach `media.get_frame()`. Can a scene outside the package be loaded? Quote the code."
- No parallel implementation subagents. The robot accepts one controlling session, and the adapter is one small file.
- Review subagent at the end: "Review `feat/s3-robot` against `main`. Check that `reachy_mini` is imported only inside functions in `jigsaw/robot/reachy.py` and the probe scripts; that none of `wake_up`, `goto_sleep`, `play_move`, `play_sound`, `start_head_tracking`, `enable_wobbling` is called; that every `# UNVERIFIED` comment has either a probe output in `results/probes/` or an entry in the handoff note. Do not edit files."

### What could go wrong

| If | Then |
|---|---|
| `reachy-mini.local` does not resolve on Windows | Use the IP address; record it in `agents.local.md`; S6 takes `--host` |
| WebRTC media fails from Windows | Check the SDK's GStreamer installation page and the firewall prompt. Fallback that keeps the project moving: run the frame grabber on the robot itself over SSH with the LOCAL backend, saving frames to a shared folder read by `ReplaySource`. Record the choice |
| SDK and daemon versions differ | Install the SDK version that matches the daemon, since updating the robot is the author's decision |
| 720p gives fewer than 10 pixels per cell at the nearest sharp distance | Try 1080p; if resolution cannot be changed remotely, recommend 60 mm pieces |
| Compression artefacts cause misreads | Report the reject rate per resolution. Rejections are acceptable; note it for the paper's threats to validity |
| A gesture stalls the video for more than half a second | S6 gestures only after the announcement and ignores frames for one second afterwards. Record the measured gap |
| The author cannot be at the robot today | Do Tasks 1, 2 and the unit-test part of 5 with stubs, and leave the probes ready to run. Say clearly in the handoff note that nothing is verified |

### Definition of done

Unit tests pass without a robot; all five probes have saved output; the focus recommendation has been given to the author; `HANDOFF_S3.md` lists what is verified and what is not; pull request open.
