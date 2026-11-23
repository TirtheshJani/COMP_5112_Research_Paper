"""Replay a recorded viewer event file in a loop, with camera frames from the renderer (W4).

Usage: uv run python scripts/replay_events.py tests/data/events_sample.jsonl --rate 10 [--port 8765] [--loops 0]

For each frame event the matching JPEG is set on the bus before the event is published. Read frames
show the announced piece at its turn on the green mat; a too_many_errors reject shows a piece on the mat
(its grid is drawn in amber); other rejects show a piece at an odd angle on clutter.
Frames are rendered once at start (seeded by the event's index) and reused on every loop.
"""
import argparse
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from jigsaw import types as T
from jigsaw.geometry import W, outline
from jigsaw.render import photograph, piece_back
from jigsaw.viewer.events import EventBus

PX_PER_CELL = 8.0
SIZE = (720, 720)


def load_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def render_frame(event: dict, seed: int) -> tuple[bytes, list[list[float]] | None]:
    """(JPEG, grid) for a frame event. grid is the piece's square of cells in image pixels, or None."""
    rng = np.random.default_rng(seed)
    d = event["decision"]
    if d["kind"] == "read":
        r, c, angle, background = d["row"], d["col"], 90.0 * d["turn"] + rng.uniform(-6, 6), "mat"
    elif d["reason"] == "too_many_errors":     # a grid was found but did not decode: draw it in amber
        r, c, angle, background = int(rng.integers(T.PUZZLE_ROWS)), int(rng.integers(T.PUZZLE_COLS)), rng.uniform(0, 360), "mat"
    else:
        r, c, angle, background = int(rng.integers(T.PUZZLE_ROWS)), int(rng.integers(T.PUZZLE_COLS)), 45.0, "clutter"
    gray, alpha = piece_back(r, c, PX_PER_CELL)
    img, M = photograph(gray, alpha, rng, angle, tilt=0.03, size=SIZE, scale=3.0, background=background,
                        return_transform=True)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    assert ok
    if background != "mat":
        return buf.tobytes(), None
    # same back-view frame as piece_back: outline mirrored, origin two cells outside its bounding box
    s = PX_PER_CELL / T.CELL_MM
    poly = outline(r, c)
    poly = np.column_stack([W - poly[:, 0], poly[:, 1]])
    x0, y0 = poly.min(0) - 2 * T.CELL_MM
    P = T.PIECE_MM
    sq = np.array([[W - (c + 1) * P, r * P], [W - c * P, r * P], [W - c * P, (r + 1) * P], [W - (c + 1) * P, (r + 1) * P]])
    px = ((sq - (x0, y0)) * s).astype(np.float32).reshape(-1, 1, 2)
    grid = cv2.perspectiveTransform(px, M).reshape(4, 2)
    return buf.tobytes(), [[round(float(x), 1), round(float(y), 1)] for x, y in grid]


def replay(bus: EventBus, events: list[dict], rate: float = 10.0, loops: int = 0,
           sleep: Callable[[float], None] = time.sleep) -> None:
    """Publish events at `rate` per second, `loops` times (0 = forever). Frame times keep increasing."""
    frames = {i: render_frame(e, seed=i)[0] for i, e in enumerate(events) if e["type"] == "frame"}
    ts = [e["t"] for e in events if e["type"] == "frame"]
    period = (max(ts) - min(ts) + 1.0 / rate) if ts else 0.0
    n = 0
    while loops == 0 or n < loops:
        for i, e in enumerate(events):
            if e["type"] == "frame":
                e = {**e, "t": round(e["t"] + n * period, 3)}
                bus.set_frame(frames[i])
            bus.publish(e)
            sleep(1.0 / rate)
        n += 1


def main() -> None:
    from jigsaw.viewer.server import serve

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("events", type=Path)
    ap.add_argument("--rate", type=float, default=10.0, help="events per second")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--loops", type=int, default=0, help="0 = forever")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    bus = EventBus()
    if serve(bus, port=args.port) is None:
        raise SystemExit(f"port {args.port} is taken")
    print(f"replaying {args.events} at {args.rate}/s on http://127.0.0.1:{args.port}/", flush=True)
    replay(bus, load_events(args.events), rate=args.rate, loops=args.loops)


if __name__ == "__main__":
    main()
