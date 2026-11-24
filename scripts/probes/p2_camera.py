"""Probe 2: get camera frames through the SDK and save a few.

    python scripts/probes/p2_camera.py [--host reachy-mini.local] [--seconds 10]

Saves frames to results/probes/, prints their shape, dtype, the camera resolution and whether the
intrinsics K and D are available over the network. Hold something red in front of the camera: the
script prints the mean of each channel, and in BGR the red object raises the LAST channel.
Uses ReachyMini(connection_mode="network", host=...) and media.get_frame(), reachy-mini 1.15.0; both
worked on the robot and gave (720, 1280, 3) uint8 frames with K and D (results/probes/p2.txt, 23 Nov 2026).
UNVERIFIED: BGR channel order (reachy_mini/media/media_manager.py:242-250, get_frame docstring); the saved p2.txt has no red-object reading.
"""
import argparse
import time
from pathlib import Path

import cv2

OUT = Path(__file__).resolve().parents[2] / "results" / "probes"


def main():
    from _tee import tee
    tee("p2")
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="reachy-mini.local")
    ap.add_argument("--seconds", type=float, default=10)
    a = ap.parse_args()
    from reachy_mini import ReachyMini

    OUT.mkdir(parents=True, exist_ok=True)
    with ReachyMini(connection_mode="network", host=a.host) as mini:
        cam = mini.media.camera
        print("camera:", type(cam).__name__ if cam is not None else None)
        for name in ("resolution", "K", "D"):
            try:
                print(f"{name}:", getattr(cam, name))
            except Exception as e:  # noqa: BLE001
                print(f"{name}: unavailable ({e!r})")
        t0, n, saved = time.monotonic(), 0, 0
        while time.monotonic() - t0 < a.seconds:
            f = mini.media.get_frame()
            if f is None:
                time.sleep(0.05)
                continue
            n += 1
            if n == 1:
                print("first frame after", round(time.monotonic() - t0, 2), "s:", f.shape, f.dtype)
            if n % 15 == 1:
                p = OUT / f"frame_{int(time.time())}_{n:04d}.png"
                cv2.imwrite(str(p), f)
                saved += 1
                print(f"saved {p.name}  channel means (0, 1, 2) = {f.reshape(-1, 3).mean(0).round(1)}")
        print(f"{n} frames in {a.seconds:.0f} s ({n / a.seconds:.1f} fps), {saved} saved to {OUT}")


if __name__ == "__main__":
    main()
