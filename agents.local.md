# agents.local.md: this Reachy Mini (S3, 23 Nov 2026)

Local notes for coding agents, as the reachy-mini SDK's agent guide asks. Each value names the file it comes from.

## Robot and software

- Robot: Reachy Mini Wireless (`wireless_version: true`, `camera_specs_name: "wireless"`, `simulation_enabled: false`; results/probes/p1.txt).
- Daemon: version 1.15.0, state "running", Wi-Fi address 10.0.0.100, HTTP port 8000 (`/api/daemon/status` in results/probes/p1.txt).
- SDK on the laptop: reachy-mini 1.15.0, pinned in the `robot` group of pyproject.toml; GStreamer runtime gstreamer-bundle 1.28.3; Python 3.13.12 (results/probes/versions.txt). SDK and daemon versions match; p2.txt shows no version-mismatch warning at connect.
- Connect from code: `jigsaw.robot.reachy.connect("10.0.0.100")`, which calls `ReachyMini(connection_mode="network", host="10.0.0.100")`. Media arrive over WebRTC (`GstWebRTCClient`, results/probes/p2.txt). Whether `reachy-mini.local` resolves on this Windows laptop is not recorded, so pass the IP.
- Before connecting: robot on and booted, laptop on the same Wi-Fi, the conversation app stopped in the robot's dashboard.
- Never call `wake_up()`, `goto_sleep()`, `play_move()`, `play_sound()`, `start_head_tracking()` or `enable_wobbling()` (CLAUDE.md rule 7). Only `jigsaw/robot/reachy.py` calls `goto_target` and `push_audio_sample` (rule 6).

## What each probe showed

| Probe | Saved output | Result |
|---|---|---|
| p1 status | results/probes/p1.txt | Daemon reachable over HTTP. `/api/camera/specs` lists 7 modes; default R1280x720at30fps; R1920x1080at30fps has crop factor 1.115. Sensor K at 3840 x 2592 (fx 2001.8, fy 2003.1, cx 1905.9, cy 1328.3) and 12 distortion coefficients. |
| p2 camera | results/probes/p2.txt | WebRTC media work from this laptop with no extra GStreamer setup. First frame after 1.53 s, shape (720, 1280, 3) uint8. 194 non-None `get_frame()` results in 10 s (19.4 per s; repeated frames were not checked). K and D readable over the network; K at 720p as the SDK gives it: fx 667.27, fy 556.41, cx 635.29, cy 368.98. No red object was held, so the channel order is not settled. The SDK logged `No Reachy Mini Audio USB device found!` at connect. |
| p3 live read | results/probes/p3.txt | A live run of 290 frames at 3.7 per s: 204 `reject:no_match`, 86 `reject:no_grid`, no Read (so no wrong Read). The piece and distance used are not recorded. |
| p4 nod | results/probes/p4.txt | Empty file (0 bytes): no evidence that p4 ran on the robot. It ran on the mockup simulator in the cloud (docs/jigsaw/handoff/HANDOFF_S3_probes.md). |
| p5 motion and media | not run yet | Written 23 Nov; needs the robot. Writes results/probes/motion_media.md ending with `settling_time_s: <value>`. |
| p6 focus | not run yet | Written 23 Nov; needs the robot and a printed piece. Writes results/probes/focus_check.md. |

## Still UNVERIFIED on the robot

- Channel order of `get_frame()` (BGR per the SDK; no red-object reading saved).
- The 720p K correction in `jigsaw.robot.reachy.correct_k` (fy x 1.2, cy = (3.6 cy - 216) / 3), an orchestrator instruction.
- Gestures: `goto_target` blocking until the move ends, and `MoveBusyError` while another move runs.
- Audio out (`push_audio_sample` non-blocking, 16 kHz) and audio in (float32 (N, 2) or None, 16 kHz).
- Whether gestures drop frames or glitch audio, and the settling time after a gesture (p5).
- Working distance and resolution for reading (p6), and whether a remote client can get 1920 x 1080 at all: the SDK's WebRTC client refuses `set_resolution` while streaming and the daemon has no route to set it.
