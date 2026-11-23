"""Demo loop (S6 A7): jigsaw.app.run against the robot, the renderer or a folder of saved frames.

    uv run python scripts/run_demo.py --source robot [--host 10.0.0.100] [--no-voice-in] [--viewer]
    uv run python scripts/run_demo.py --source render [--seed 0] [--max-frames 200] [--viewer]
    uv run python scripts/run_demo.py --source replay --frames results/probes/reads [--viewer]

The robot is connected only with --source robot; it is then the frame source, the gestures, the audio
output and (unless --no-voice-in) the microphone for spoken commands. With render or replay nothing moves
and nothing is played: sentences are synthesized and logged, gestures are printed. --viewer serves the
projector view on http://127.0.0.1:8765. --max-frames ends the run after that many frames.
"""
import argparse
import logging

import numpy as np

from jigsaw import app
from jigsaw.robot.sources import RenderSource, ReplaySource
from jigsaw.types import PUZZLE_COLS, PUZZLE_ROWS

FRAMES_PER_PIECE = 10


class PrintedGestures:
    def nod(self) -> None:
        print("(nod)")

    def shake(self) -> None:
        print("(shake)")


class SilentAudio:
    def play(self, pcm: np.ndarray, rate: int) -> None:
        pass

    def is_playing(self) -> bool:
        return False


def render_source(seed: int) -> RenderSource:
    """Every piece once, in an order drawn from the seed, FRAMES_PER_PIECE frames each, at one quarter turn."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(PUZZLE_ROWS * PUZZLE_COLS)
    pieces = [(int(i) // PUZZLE_COLS, int(i) % PUZZLE_COLS) for i in order for _ in range(FRAMES_PER_PIECE)]
    return RenderSource(rng, pieces, size=(1280, 720), angle_deg=90 * int(rng.integers(4)))


def parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["robot", "render", "replay"], required=True)
    ap.add_argument("--host", default=None, help="robot address (default reachy-mini.local)")
    ap.add_argument("--no-voice-in", action="store_true", help="do not listen for spoken commands")
    ap.add_argument("--viewer", action="store_true", help="serve the projector view")
    ap.add_argument("--frames", default=None, help="folder of saved frames for --source replay")
    ap.add_argument("--seed", type=int, default=0, help="piece order and turn for --source render")
    ap.add_argument("--max-frames", type=int, default=None, help="stop after this many frames")
    a = ap.parse_args(argv)
    if a.source == "replay" and a.frames is None:
        ap.error("--source replay needs --frames DIR")
    return a


def main(argv: list[str] | None = None, gestures=None, audio_out=None) -> dict:
    """gestures and audio_out replace the defaults (for tests)."""
    a = parse(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    audio_in = None
    if a.source == "robot":
        from jigsaw.robot.reachy import connect
        robot = connect(a.host)
        source = audio_in = robot
        gestures, audio_out = gestures or robot, audio_out or robot
    elif a.source == "render":
        source = render_source(a.seed)
    else:
        source = ReplaySource(a.frames)
    gestures, audio_out = gestures or PrintedGestures(), audio_out or SilentAudio()
    listener = bus = None
    try:
        if audio_in is not None and not a.no_voice_in:
            from jigsaw.voice.stt import CommandListener
            listener = CommandListener(audio_in, audio_out.is_playing)
            listener.warm()
        if a.viewer:
            from jigsaw.viewer.events import EventBus
            from jigsaw.viewer.server import serve
            bus = EventBus()
            serve(bus)
        out = app.run(source, gestures, audio_out, bus=bus, listener=listener, max_frames=a.max_frames)
    finally:
        if listener is not None:
            listener.close()
        source.close()
    said = ", ".join(f"R{r.row + 1} C{r.col + 1} turn {r.turn}" for r in out["announced"]) or "nothing"
    print(f"{out['frames']} frames, {out['dropped']} dropped, {out['gave_up']} give-ups; announced: {said}")
    return out


if __name__ == "__main__":
    main()
