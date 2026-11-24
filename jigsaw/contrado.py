"""Contrado edition: the 48-piece plastic jigsaw (Large Rectangle, 10.04 x 7.48 in, printed both sides).

Contrado cuts its own die, so the back is one continuous grid over the whole panel and the robot finds
the piece from the centroid of what it sees, not from our cut lines.

Panel geometry (Contrado's editor, 300 dpi): 3130 x 2362 px, with a 5 mm bleed on every side, so the
trim is 255 x 190 mm. The die is 8 columns x 6 rows of pieces, about 31.9 x 31.7 mm each.

Back: cell (a, b) of G covers panel pixels x in [30 b, 30 b + 30), y in [30 a, 30 a + 30), seen from the
back. One cell is 30 px = 2.54 mm. G is torus[100:179, 120:225] of the strong-form u = 5 torus, a block
that does not overlap the card edition's torus[0:72, 0:52], so a card piece can never decode here.

Flip: FLIP = "lr" assumes the back panel is what you see after turning the puzzle over left to right.
If the robot names the mirror-image column for a corner piece, set FLIP = "tb" (turned over top to bottom).
"""
import numpy as np

from jigsaw.decode import build_table, decode_single, placement, rot_affine
from jigsaw.patch import PATTERNS, load_torus
from jigsaw.types import Position, Read, Reject

DPI = 300
PX_PER_MM = DPI / 25.4
PANEL_W, PANEL_H = 3130, 2362
BLEED_PX = 5 * PX_PER_MM                       # 59.06
TRIM_W, TRIM_H = PANEL_W - 2 * BLEED_PX, PANEL_H - 2 * BLEED_PX
ROWS, COLS = 6, 8                              # pieces, picture side, landscape
PITCH_X, PITCH_Y = TRIM_W / COLS, TRIM_H / ROWS
CELL_PX = 30
CELL_MM = CELL_PX / PX_PER_MM                  # 2.54
G_ORIGIN = (100, 120)
G_ROWS, G_COLS = -(-PANEL_H // CELL_PX), -(-PANEL_W // CELL_PX)    # 79, 105
FLIP = "lr"
U = 5


def back_grid() -> np.ndarray:
    a, b = G_ORIGIN
    return load_torus(PATTERNS / "strong_u5_256.npz")[a:a + G_ROWS, b:b + G_COLS].copy()


def g_to_front_px(a: float, b: float, flip: str = FLIP) -> tuple[float, float]:
    """Centre of G cell (a, b) (float indices allowed) to front panel pixels (x, y)."""
    xb, yb = (b + 0.5) * CELL_PX, (a + 0.5) * CELL_PX
    return (PANEL_W - xb, yb) if flip == "lr" else (xb, PANEL_H - yb)


def front_px_to_piece(x: float, y: float) -> tuple[int, int] | None:
    col, row = int(np.floor((x - BLEED_PX) / PITCH_X)), int(np.floor((y - BLEED_PX) / PITCH_Y))
    return (row, col) if 0 <= row < ROWS and 0 <= col < COLS else None


class ContradoReader:
    """Same contract as reader.PieceReader, for the Contrado edition."""

    def __init__(self, flip: str = FLIP):
        self.G = back_grid()
        self.table = build_table(self.G)
        self.flip = flip
        self.last_grid = None

    def read(self, bgr: np.ndarray):
        from jigsaw.vision import read_grid
        gr = read_grid(bgr)
        self.last_grid = None if isinstance(gr, Reject) else gr
        if isinstance(gr, Reject):
            return gr
        return decode(gr.cells, gr.mask, self.table, self.flip)


def decode(cells, mask, table, flip: str = FLIP, u: int = U, min_agree: int = 2, max_disagree: int = 3):
    """decode.decode_grid with the Contrado mapping from G to pieces."""
    cells = np.asarray(cells, np.uint8)
    mask = np.asarray(mask, bool)
    h, w = cells.shape
    starts = [(y, x) for y in range(h - u + 1) for x in range(w - u + 1) if mask[y:y + u, x:x + u].all()]
    if not starts:
        return Reject("no_window")
    votes = {}
    for y, x in starts:
        d = decode_single(cells[y:y + u, x:x + u], table)
        if isinstance(d, Position):
            k = placement(y, x, d, u)
            votes[k] = votes.get(k, 0) + 1
    if not votes:
        return Reject("no_match")
    if len(votes) > 1:
        return Reject("inconsistent")
    (turn, ti, tj), n = next(iter(votes.items()))
    if n < min(min_agree, len(starts)):
        return Reject("no_match")
    M, _ = rot_affine(turn, u)
    ys, xs = np.nonzero(mask)
    g = (M @ np.vstack([ys, xs])).T + (ti, tj)
    R, C = table.shape
    if not ((g[:, 0] >= 0) & (g[:, 0] < R) & (g[:, 1] >= 0) & (g[:, 1] < C)).all():
        return Reject("off_puzzle")
    if int((table.pattern[g[:, 0], g[:, 1]] != cells[ys, xs]).sum()) > max_disagree:
        return Reject("inconsistent")
    a, b = g.mean(axis=0)
    piece = front_px_to_piece(*g_to_front_px(a, b, flip))
    if piece is None:
        return Reject("off_puzzle")
    # A top-to-bottom flip is a left-to-right flip plus a half turn, so the spoken turn shifts by 2.
    return Read(piece[0], piece[1], turn if flip == "lr" else (turn + 2) % 4)
