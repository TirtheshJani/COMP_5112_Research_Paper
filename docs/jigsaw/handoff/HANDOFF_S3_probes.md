# HANDOFF S3 probes (23 Nov 2026, partial)

Written: `scripts/probes/p1_status.py`, `p2_camera.py`, `p3_live_read.py`, `p4_nod.py`. API taken from the `reachy-mini` 1.15.0 source.

Run on 23 Nov in the cloud workspace against `reachy-mini-daemon --mockup-sim --headless` (SDK 1.15.0):
- p1: `/api/daemon/status` returned state "running", version "1.15.0"; `/api/camera/specs` answered. Exit code 0.
- p4 `--move`: the six moves completed ("done: nod and shake"); `/api/state/full` shows the head back at neutral.
- p3 `--replay` on six rendered 1280 x 720 frames: R1 C1, R1 C1, R4 C3, R7 C5, R7 C5 and one reject (a blank mat frame), all correct.
- p2: not testable; the simulator needs the GStreamer webrtc plugin to serve a camera.

On your PC (robot on, same Wi-Fi, conversation app stopped):
```
uv sync --extra dev --extra print --extra robot
uv run python scripts/probes/p1_status.py
uv run python scripts/probes/p2_camera.py --seconds 10
uv run python scripts/probes/p3_live_read.py --seconds 60
uv run python scripts/probes/p4_nod.py --move
```
If `reachy-mini.local` does not resolve, add `--host <robot IP>`. Save the console output of each next to the frames in `results/probes/`.
