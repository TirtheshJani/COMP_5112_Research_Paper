"""Window tables and decoders (CONTRACTS.md section 3).

decode_single: one u x u window, any turn. Exactly one un-turning must be in the table.
decode_grid:   all complete windows of a piece read; every decoded window must agree on one placement,
               and the piece is the one under the centroid of the visible cells.
"""
from collections import Counter

import numpy as np

from jigsaw import types as T
from jigsaw.patch import g_to_front, windows
from jigsaw.types import Position, Read, Reject


class Table(dict):
    """Upright window bytes -> (i, j). Carries the pattern shape, window size and wrap flag."""

    def __init__(self, pattern, u, wrap):
        super().__init__()
        self.pattern = np.asarray(pattern, np.uint8)
        self.shape, self.u, self.wrap = self.pattern.shape, u, wrap


def build_table(pattern: np.ndarray, u: int = T.U, wrap: bool = False) -> Table:
    table = Table(pattern, u, wrap)
    for i, j, w in windows(pattern, u, wrap):
        key = w.astype(np.uint8).tobytes()
        if key in table:
            raise ValueError(f"window at {(i, j)} repeats the one at {table[key]}")
        table[key] = (i, j)
    return table


def decode_single(window: np.ndarray, table: Table) -> Position | Reject:
    window = np.asarray(window, np.uint8)
    hits = []
    for k in range(4):
        pos = table.get(np.rot90(window, -k).tobytes())
        if pos is not None:
            hits.append(Position(pos[0], pos[1], k))
    if not hits:
        return Reject("no_match")
    return hits[0] if len(hits) == 1 else Reject("ambiguous")


def rot_affine(k: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """For seen = np.rot90(printed, k) of an n x n block: printed index = M @ seen index + c."""
    k %= 4
    M = {0: [[1, 0], [0, 1]], 1: [[0, 1], [-1, 0]], 2: [[-1, 0], [0, -1]], 3: [[0, -1], [1, 0]]}[k]
    c = {0: (0, 0), 1: (0, n - 1), 2: (n - 1, n - 1), 3: (n - 1, 0)}[k]
    return np.array(M), np.array(c)


def placement(y0: int, x0: int, pos: Position, u: int) -> tuple[int, int, int]:
    """(turn, ti, tj): G index of seen cell (y, x) is M_turn @ (y, x) + (ti, tj)."""
    M, c = rot_affine(pos.turn, u)
    t = np.array([pos.i, pos.j]) - M @ np.array([y0, x0]) + c
    return pos.turn, int(t[0]), int(t[1])


def decode_grid(cells: np.ndarray, mask: np.ndarray, table: Table, u: int = T.U,
                min_agree: int = 2, max_disagree: int = 3) -> Read | Reject:
    cells = np.asarray(cells, np.uint8)
    mask = np.asarray(mask, bool)
    h, w = cells.shape
    starts = [(y, x) for y in range(h - u + 1) for x in range(w - u + 1) if mask[y:y + u, x:x + u].all()]
    if not starts:
        return Reject("no_window")
    votes = Counter()
    for y, x in starts:
        d = decode_single(cells[y:y + u, x:x + u], table)
        if isinstance(d, Position):
            votes[placement(y, x, d, u)] += 1
    if not votes:
        return Reject("no_match")
    if len(votes) > 1:
        return Reject("inconsistent")
    (turn, ti, tj), n = votes.most_common(1)[0]
    if n < min(min_agree, len(starts)):
        return Reject("no_match")
    M, _ = rot_affine(turn, u)
    ys, xs = np.nonzero(mask)
    g = (M @ np.vstack([ys, xs])).T + (ti, tj)
    R, C = table.shape
    inside = (g[:, 0] >= 0) & (g[:, 0] < R) & (g[:, 1] >= 0) & (g[:, 1] < C)
    if not inside.all():
        return Reject("off_puzzle")
    G = table.pattern                                  # whole-piece consistency check
    if int((G[g[:, 0], g[:, 1]] != cells[ys, xs]).sum()) > max_disagree:
        return Reject("inconsistent")
    front = np.array([g_to_front(a, b) for a, b in g], float) + 0.5
    ci, cj = front.mean(axis=0)
    row, col = int(np.floor(ci / T.PIECE_CELLS)), int(np.floor(cj / T.PIECE_CELLS))
    if not (0 <= row < T.PUZZLE_ROWS and 0 <= col < T.PUZZLE_COLS):
        return Reject("off_puzzle")
    return Read(row, col, turn)
