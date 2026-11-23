"""Physical test capture (S6 A8, A9): 35 pieces x 8 angles x 5 frames through the robot's camera.

    uv run python scripts/run_physical.py --host 10.0.0.100 [--out results/frames] [--pieces 1,1 2,3 ...]

The robot speaks each prompt ("Piece row 2, column 3, angle 90.") and beeps after each saved set. Nothing
moves. Run it again after an interruption: complete presentations are skipped and nothing is overwritten.
The capture never decodes; scripts/decode_physical.py does that afterwards.
"""
import argparse
from pathlib import Path

import numpy as np

from jigsaw.protocol import ANGLES, capture

ROOT = Path(__file__).resolve().parents[1]
BEEP_RATE = 16000

INSTRUCTIONS = """Physical test. Start with the empty green card filling the camera view.
For each prompt: hold the piece with the picture upright, flip it left to right so the grid faces the robot,
then turn it counter-clockwise by the angle as the robot sees it (clockwise as you see the picture side).
Keep it still over the card until the beep. Between pieces, take the piece away so the card is empty.
Ctrl+C stops; running the same command again resumes."""


def beep_pcm(hz: float = 880.0, seconds: float = 0.15) -> np.ndarray:
    t = np.arange(int(BEEP_RATE * seconds)) / BEEP_RATE
    return (0.3 * np.sin(2 * np.pi * hz * t)).astype(np.float32)


def parse_pieces(values: list[str] | None) -> list[tuple[int, int]] | None:
    """One-based "row,col" as printed on the answer key, to zero-based front coordinates."""
    if values is None:
        return None
    pieces = []
    for v in values:
        r, c = (int(x) for x in v.split(","))
        pieces.append((r - 1, c - 1))
    return pieces


def main(argv: list[str] | None = None, robot=None, synthesize=None) -> dict:
    """robot and synthesize replace the real ones (for tests)."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=None, help="robot address (default reachy-mini.local)")
    ap.add_argument("--out", default=str(ROOT / "results" / "frames"))
    ap.add_argument("--pieces", nargs="+", default=None, help='one-based "row,col" pieces, for a dry run')
    a = ap.parse_args(argv)
    pieces = parse_pieces(a.pieces)
    if synthesize is None:
        from jigsaw.voice.tts import synthesize
    if robot is None:
        from jigsaw.robot.reachy import connect
        robot = connect(a.host)

    def prompt(text: str) -> None:
        print(text, flush=True)
        robot.play(*synthesize(text))

    def beep() -> None:
        robot.play(beep_pcm(), BEEP_RATE)

    print(INSTRUCTIONS, flush=True)
    try:
        out = capture(robot, a.out, prompt, beep, pieces=pieces, angles=ANGLES)
    finally:
        robot.close()
    state = "complete" if out["complete"] else "stopped early (run again to resume)"
    print(f"{out['captured']} presentations captured, {out['skipped']} already there; {state}. Frames in {a.out}")
    return out


if __name__ == "__main__":
    main()
