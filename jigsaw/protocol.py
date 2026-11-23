"""Capture for the physical test (S6 A8, A9). It never decodes: the only vision call is paper_mask.

For each piece in front order (row by row) and each nominal angle 0, 45, ..., 315 the operator is prompted
("Piece row 2, column 3, angle 90."). The capture then waits for the view to change (an empty mat, or a piece
that no longer overlaps the last saved one), then for paper_mask to find a piece in PRESENT_FRAMES frames in a
row without it moving, saves the next SET_FRAMES frames as PNG with a sidecar JSON and beeps.

The change and stillness conditions are additions to "present for 5 frames in a row": without them the piece
from the previous presentation would be captured before the operator turns or swaps it. STILL_IOU is a
placeholder that the five-piece dry run checks.

Nominal angle: counter-clockwise as seen by the camera, from the back's upright position, so 90 is turn 1.

Layout: <out>/r{row}_c{col}_a{angle:03d}/f{n}.png and f{n}.json (row, col zero-based front coordinates).
A presentation is written to a .partial folder and renamed when complete. A run skips complete presentations
and deletes leftover .partial folders, so resuming never overwrites a saved frame.
"""
import json
import shutil
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from jigsaw.types import PUZZLE_COLS, PUZZLE_ROWS, Frame, FrameSource
from jigsaw.vision import paper_mask

ANGLES = tuple(range(0, 360, 45))
PRESENT_FRAMES = 5
SET_FRAMES = 5
STILL_IOU = 0.9  # UNVERIFIED: placeholder, not measured with the robot's camera; the five-piece dry run checks it


def folder_name(row: int, col: int, angle: int) -> str:
    return f"r{row}_c{col}_a{angle:03d}"


def prompt_text(row: int, col: int, angle: int) -> str:
    """Spoken one-based, as everything the robot says."""
    return f"Piece row {row + 1}, column {col + 1}, angle {angle}."


def iou(a: np.ndarray, b: np.ndarray) -> float:
    union = np.count_nonzero(a | b)
    return np.count_nonzero(a & b) / union if union else 1.0


def wait_for_piece(frames: Iterator[Frame], reference: np.ndarray | None) -> np.ndarray | None:
    """Mask of a piece that is present and still for PRESENT_FRAMES frames, after the view has changed.

    The view has changed at a frame with no piece, or with a piece overlapping `reference` (the last saved
    mask) by less than STILL_IOU; with no reference only an empty frame counts. A run of frames is still while
    every mask overlaps the run's first by at least STILL_IOU. Returns None when the frames end.
    """
    changed, run = False, []
    for frame in frames:
        m = paper_mask(frame.image)
        if m is None:
            changed, run = True, []
            continue
        m = m > 0
        if not changed:
            if reference is None or iou(m, reference) >= STILL_IOU:
                continue
            changed = True
        if run and iou(run[0], m) < STILL_IOU:
            run = []
        run.append(m)
        if len(run) == PRESENT_FRAMES:
            return m
    return None


def _sidecar(row: int, col: int, angle: int, n: int, frame: Frame) -> dict:
    h, w = frame.image.shape[:2]
    return {"piece_row": row, "piece_col": col, "angle_deg": angle, "frame": n, "t": frame.t,
            "time": datetime.now().isoformat(timespec="milliseconds"), "resolution": f"{w}x{h}",
            "K": None if frame.K is None else np.asarray(frame.K).tolist(),
            "D": None if frame.D is None else np.asarray(frame.D).ravel().tolist()}


def capture(source: FrameSource, out_dir: str | Path, prompt: Callable[[str], None], beep: Callable[[], None],
            pieces: Iterable[tuple[int, int]] | None = None, angles: Iterable[int] = ANGLES) -> dict:
    """Run the protocol. Returns {"captured", "skipped", "complete"}; complete is False if the frames ran out."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pieces = [(r, c) for r in range(PUZZLE_ROWS) for c in range(PUZZLE_COLS)] if pieces is None else list(pieces)
    frames = iter(source.frames())
    reference = None
    done = {"captured": 0, "skipped": 0, "complete": False}
    for row, col in pieces:
        for angle in angles:
            final = out / folder_name(row, col, angle)
            if final.exists():
                done["skipped"] += 1
                continue
            partial = final.with_name(final.name + ".partial")
            if partial.exists():
                shutil.rmtree(partial)
            prompt(prompt_text(row, col, angle))
            reference = wait_for_piece(frames, reference)
            if reference is None:
                return done
            partial.mkdir()
            for n in range(SET_FRAMES):
                frame = next(frames, None)
                if frame is None:
                    return done
                cv2.imwrite(str(partial / f"f{n}.png"), frame.image)
                (partial / f"f{n}.json").write_text(json.dumps(_sidecar(row, col, angle, n, frame)))
            partial.rename(final)
            beep()
            done["captured"] += 1
    done["complete"] = True
    return done
