"""Probe 3: read real pieces through the robot's camera, or replay saved frames.

    python scripts/probes/p3_live_read.py --host reachy-mini.local [--seconds 60]
    python scripts/probes/p3_live_read.py --replay results/probes

Hold a printed piece grid-side up over the green reading mat (any strongly coloured card works).
Every frame is read and decoded; the script prints each change of decision ("R4 C2 turn 1" or the
reject reason), saves frames with a Read to results/probes/reads/, and ends with counts.
A Read whose row and column are wrong is a finding (CLAUDE.md rule 6): note the piece, keep the frame.
"""
import argparse
import time
from collections import Counter
from pathlib import Path

import cv2

from jigsaw.reader import PieceReader
from jigsaw.types import Read

OUT = Path(__file__).resolve().parents[2] / "results" / "probes"


def label(d):
    return f"R{d.row + 1} C{d.col + 1} turn {d.turn}" if isinstance(d, Read) else f"reject:{d.reason}"


def frames_live(host, seconds):
    from reachy_mini import ReachyMini
    with ReachyMini(connection_mode="network", host=host) as mini:
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            f = mini.media.get_frame()
            if f is None:
                time.sleep(0.02)
                continue
            yield f


def frames_replay(folder):
    for p in sorted(Path(folder).glob("*.png")):
        img = cv2.imread(str(p))
        if img is not None:
            yield img


def main():
    from _tee import tee
    tee("p3")
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="reachy-mini.local")
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--replay", default=None)
    a = ap.parse_args()
    reader = PieceReader()
    (OUT / "reads").mkdir(parents=True, exist_ok=True)
    counts, last, n = Counter(), None, 0
    t0 = time.monotonic()
    src = frames_replay(a.replay) if a.replay else frames_live(a.host, a.seconds)
    for img in src:
        n += 1
        d = reader.read(img)
        s = label(d)
        counts[s] += 1
        if s != last:
            print(f"{time.monotonic() - t0:7.2f}s  {s}")
            last = s
        if isinstance(d, Read) and counts[s] <= 3:
            cv2.imwrite(str(OUT / "reads" / f"{s.replace(' ', '_')}_{counts[s]}.png"), img)
    dt = time.monotonic() - t0
    print(f"\n{n} frames, {n / max(dt, 1e-6):.1f} per second")
    for s, k in counts.most_common():
        print(f"  {k:5d}  {s}")


if __name__ == "__main__":
    main()
