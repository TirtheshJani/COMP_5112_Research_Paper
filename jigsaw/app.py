"""Live loop for the demo (S6 A2 to A6): frame, PieceReader, Stable, then events, speech and a gesture.

One loop in the caller's thread. The robot is reached only through the FrameSource, Gestures and AudioOut
interfaces (CLAUDE.md rule 6); speech is synthesized with jigsaw.voice.tts, which imports Piper lazily.

Frames are dropped, not read, while audio is playing, and until SETTLE_S after the robot has finished
speaking and moving (A4); speech and gestures block, so a frame that arrives in that time carries an
earlier time stamp than the end of the quiet period.
"""
import itertools
import logging
import time
from collections.abc import Callable

import cv2
import numpy as np

from jigsaw.pose import piece_pose
from jigsaw.reader import PieceReader
from jigsaw.stable import Stable
from jigsaw.types import AudioOut, Decision, Frame, FrameSource, Gestures, GridRead, Read, Reject
from jigsaw.voice import tts
from jigsaw.voice.phrases import phrase_read, phrase_reject

log = logging.getLogger(__name__)

SETTLE_S = 0.5  # UNVERIFIED: placeholder until scripts/probes/p5_motion_media.py writes settling_time_s
#                 to results/probes/motion_media.md (docs/jigsaw/handoff/DECISIONS.md entry 8)


def grid_corners(grid: GridRead) -> list[list[float]]:
    """Image corners of the read grid: cell corners (0, 0), (w, 0), (w, h), (0, h) mapped through GridRead.H."""
    h, w = grid.cells.shape
    p = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], float) @ np.asarray(grid.H, float).T
    return [[round(float(x), 1), round(float(y), 1)] for x, y in p[:, :2] / p[:, 2:]]


def frame_event(frame: Frame, d: Decision, grid: GridRead | None) -> dict:
    """CONTRACTS section 5 frame event."""
    corners = rvec = tvec = None
    if grid is not None:
        corners = grid_corners(grid)
        pose = piece_pose(grid.H, frame.K, frame.D, grid.cells.shape)
        if pose is not None:
            rvec, tvec = ([round(float(v), 4) for v in a] for a in pose)
    if isinstance(d, Read):
        decision = {"kind": "read", "row": int(d.row), "col": int(d.col), "turn": int(d.turn)}
    else:
        decision = {"kind": "reject", "reason": d.reason}
    return {"type": "frame", "t": float(frame.t), "grid": corners, "rvec": rvec, "tvec": tvec, "decision": decision}


def run(source: FrameSource, gestures: Gestures, audio_out: AudioOut, bus=None, listener=None,
        max_frames: int | None = None, *, clock: Callable[[], float] = time.monotonic,
        synthesize: Callable[[str], tuple[np.ndarray, int]] | None = None) -> dict:
    """Run until the source ends, `stop` is heard or max_frames frames have been taken from the source.

    bus: anything with publish(event) and set_frame(jpeg), such as viewer.events.EventBus, or None.
    listener: anything with poll() -> "ask" | "again" | "next" | "stop" | None, such as voice.stt.CommandListener.
    clock and synthesize are for tests. Returns counts: frames taken, frames dropped, announced Reads, give-ups.
    """
    say = synthesize or tts.synthesize
    reader, stable = PieceReader(), Stable()
    placed: list[list[int]] = []
    out: dict = {"frames": 0, "dropped": 0, "announced": [], "gave_up": 0}
    quiet_until = float("-inf")
    last_text: str | None = None
    reason = ""             # last reject reason of this presentation, for the give-up sentence
    ask = False

    def publish(event: dict) -> None:
        if bus is not None:
            bus.publish(event)

    def speak(text: str, gesture: Callable[[], None] | None) -> None:
        nonlocal quiet_until
        pcm, rate = say(text)
        audio_out.play(pcm, rate)
        if gesture is not None:
            gesture()
        quiet_until = clock() + SETTLE_S

    def announce(read: Read) -> None:
        nonlocal last_text
        text = phrase_read(read)
        if [read.row, read.col] not in placed:
            placed.append([int(read.row), int(read.col)])
        publish({"type": "announce", "row": int(read.row), "col": int(read.col), "turn": int(read.turn), "text": text})
        publish({"type": "board", "placed": [list(p) for p in placed]})
        log.info("announce: %s", text)
        out["announced"].append(read)
        last_text = text
        speak(text, gestures.nod)

    def give_up(why: str) -> None:
        text = phrase_reject(why)
        publish({"type": "give_up", "text": text})
        log.info("give up: %s", text)
        out["gave_up"] += 1
        speak(text, gestures.shake)

    publish({"type": "board", "placed": []})
    for frame in itertools.islice(source.frames(), max_frames):
        out["frames"] += 1
        command = listener.poll() if listener is not None else None
        if command is not None:
            log.info("command: %s", command)
        if command == "stop":
            break
        if command == "next":
            stable = Stable()
        elif command == "again" and last_text is not None:
            speak(last_text, None)
        elif command == "ask":
            ask = True
        if audio_out.is_playing() or frame.t < quiet_until:
            out["dropped"] += 1
            stable.gap()
            continue
        d = reader.read(frame.image)
        if bus is not None:
            ok, jpeg = cv2.imencode(".jpg", frame.image)
            if ok:
                bus.set_frame(jpeg.tobytes())
        publish(frame_event(frame, d, reader.last_grid))
        if isinstance(d, Reject):
            reason = "" if d.reason == "no_grid" else d.reason      # no_grid ends the presentation
        if ask:
            ask = False
            stable.mark_answered()
            if isinstance(d, Read):
                stable.last = d
                announce(d)
            else:
                give_up(d.reason)
            continue
        what = stable.update(d)
        if what == "announce":
            announce(stable.last)
        elif what == "give_up":
            give_up(reason)
    return out
