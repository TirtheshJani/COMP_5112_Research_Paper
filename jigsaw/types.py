"""Shared types and constants (CONTRACTS.md section 2). Frozen after S0.

Coordinates
-----------
G is the back grid exactly as printed, seen from the back: G[a, b], a = row from the top, b = column
from the left. The puzzle has PUZZLE_ROWS x PUZZLE_COLS pieces of PIECE_CELLS x PIECE_CELLS cells and
MARGIN_CELLS extra cells of pattern on every side. Turning the sheet over (long-edge flip) mirrors
left and right, so front lattice cell (i, j) carries G[i + MARGIN_CELLS, PUZZLE_COLS * PIECE_CELLS - 1 - j
+ MARGIN_CELLS].

A Read names a piece in FRONT coordinates: row 0 is the top row and col 0 the left column of the
picture, which is how the answer key and the robot's speech number them (plus one).

turn: number of counter-clockwise quarter turns, as seen by the camera, between the printed back
grid and what the camera sees. The camera image of a window is np.rot90(printed_window, turn).
"""
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

import numpy as np

U = 5                                     # window side
PIECE_CELLS = 10                          # cells per piece side
PUZZLE_ROWS, PUZZLE_COLS = 7, 5           # pieces, as seen on the picture side
MARGIN_CELLS = 1                          # extra printed cells around the puzzle
GRID_ROWS = PUZZLE_ROWS * PIECE_CELLS + 2 * MARGIN_CELLS   # 72
GRID_COLS = PUZZLE_COLS * PIECE_CELLS + 2 * MARGIN_CELLS   # 52
CELL_MM = 3.6
PIECE_MM = PIECE_CELLS * CELL_MM          # 36, without knobs


@dataclass(frozen=True)
class Position:
    """Top-left cell (i, j) in G of a matched window, and the turn."""
    i: int
    j: int
    turn: int


@dataclass(frozen=True)
class Read:
    """A piece identified from its back. row, col in front (picture side) coordinates."""
    row: int
    col: int
    turn: int


RejectReason = Literal["no_grid", "low_contrast", "no_window", "no_match", "ambiguous",
                       "inconsistent", "off_puzzle"]


@dataclass(frozen=True)
class Reject:
    reason: RejectReason


Decision = Read | Reject


@dataclass(frozen=True)
class GridRead:
    """Cells read from one piece, before decoding.

    cells: (h, w) uint8, 1 = black, in the camera's orientation up to a quarter turn.
    mask:  (h, w) bool, True where the cell lies on the piece and was read confidently.
    H:     (3, 3) homography from cell coordinates (x = column + 0.5, y = row + 0.5 is a cell
           centre) to image pixels.
    """
    cells: np.ndarray
    mask: np.ndarray
    H: np.ndarray


@dataclass(frozen=True)
class Frame:
    image: np.ndarray        # (H, W, 3) uint8 BGR
    t: float                 # seconds, time.monotonic()
    K: np.ndarray | None     # (3, 3) intrinsics at this resolution, or None
    D: np.ndarray | None     # distortion coefficients, or None


@runtime_checkable
class FrameSource(Protocol):
    name: str
    def frames(self) -> Iterator[Frame]: ...
    def close(self) -> None: ...


@runtime_checkable
class Gestures(Protocol):
    def nod(self) -> None: ...        # blocks until the move ends, under 1.5 s
    def shake(self) -> None: ...


@runtime_checkable
class AudioOut(Protocol):
    def play(self, pcm: np.ndarray, rate: int) -> None: ...   # mono float32, blocks until played
    def is_playing(self) -> bool: ...


@runtime_checkable
class AudioIn(Protocol):
    rate: int                                                  # 16000
    def read(self) -> np.ndarray | None: ...                   # mono float32 chunk or None
