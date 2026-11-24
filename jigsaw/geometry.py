"""Jigsaw piece outlines (front view, millimetres, origin at the puzzle's top-left corner).

Rule that keeps every piece readable: no piece has blanks on two opposite sides. Along each row the
vertical knobs point left and then right; down each column the horizontal knobs point up and then down.
"""
from functools import lru_cache

import cv2
import numpy as np

from jigsaw import types as T
from jigsaw.patch import front_to_g

P = T.PIECE_MM
W, H = T.PUZZLE_COLS * P, T.PUZZLE_ROWS * P
TAB, JIT, SEED = 0.08, 0.03, 5


def _bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t ** 2) * p2 + (t ** 3) * p3


def _edge(A, B, perp, d, jit, t=TAB, n=20):
    """Knobbed edge from A to B; d = +1 puts the knob on the +perp side."""
    a, b, c, dd, e = jit
    ctrl = np.array([(0, 0), (0.2, a), (0.5 + b + dd, -t + c), (0.5 - t + b, t + c),
                     (0.5 - 2 * t + b - dd, 3 * t + c), (0.5 + 2 * t + b - dd, 3 * t + c),
                     (0.5 + t + b, t + c), (0.5 + b + e, -t + c), (0.8, e), (1.0, 0)], float)
    pts = np.vstack([_bezier(*ctrl[0:4], n), _bezier(*ctrl[3:7], n)[1:], _bezier(*ctrl[6:10], n)[1:]])
    A, B, perp = (np.asarray(v, float) for v in (A, B, perp))
    return A + pts[:, :1] * (B - A) + d * pts[:, 1:2] * np.linalg.norm(B - A) * perp


@lru_cache(maxsize=4)
def edges(seed: int = SEED):
    """Knob directions and curves for every inner edge: (vdir, hdir, vedge, hedge)."""
    rng = np.random.default_rng(seed)
    R, C = T.PUZZLE_ROWS, T.PUZZLE_COLS
    vsplit = rng.integers(0, C, size=R)
    hsplit = rng.integers(0, R, size=C)
    vdir = [[-1 if k < vsplit[r] else 1 for k in range(C - 1)] for r in range(R)]
    hdir = [[-1 if k < hsplit[c] else 1 for c in range(C)] for k in range(R - 1)]

    def line_jitter(dirs):
        out, e_prev, d_prev = [], 0.0, None
        for d in dirs:
            a = 0.0 if d_prev is None else (-e_prev if d == d_prev else e_prev)
            b, c, dd, e = rng.uniform(-JIT, JIT, 4)
            out.append((a, b, c, dd, e))
            e_prev, d_prev = e, d
        return out

    vedge = [[None] * (C - 1) for _ in range(R)]
    for k in range(C - 1):
        dirs = [vdir[r][k] for r in range(R)]
        for r, jit in enumerate(line_jitter(dirs)):
            x = (k + 1) * P
            vedge[r][k] = _edge((x, r * P), (x, (r + 1) * P), (1, 0), dirs[r], jit)
    hedge = [[None] * C for _ in range(R - 1)]
    for k in range(R - 1):
        dirs = [hdir[k][c] for c in range(C)]
        for c, jit in enumerate(line_jitter(dirs)):
            y = (k + 1) * P
            hedge[k][c] = _edge((c * P, y), ((c + 1) * P, y), (0, 1), dirs[c], jit)
    return vdir, hdir, vedge, hedge


def outline(r: int, c: int, seed: int = SEED) -> np.ndarray:
    """Closed outline of piece (r, c) in front coordinates (mm), clockwise on screen."""
    _, _, vedge, hedge = edges(seed)
    x0, y0, x1, y1 = c * P, r * P, (c + 1) * P, (r + 1) * P
    top = np.array([(x0, y0), (x1, y0)]) if r == 0 else hedge[r - 1][c]
    right = np.array([(x1, y0), (x1, y1)]) if c == T.PUZZLE_COLS - 1 else vedge[r][c]
    bottom = np.array([(x1, y1), (x0, y1)]) if r == T.PUZZLE_ROWS - 1 else hedge[r][c][::-1]
    left = np.array([(x0, y1), (x0, y0)]) if c == 0 else vedge[r][c - 1][::-1]
    return np.vstack([top[:-1], right[:-1], bottom[:-1], left[:-1]])


def _all_edges(seed: int = SEED) -> list[np.ndarray]:
    _, _, vedge, hedge = edges(seed)
    return [e for row in vedge for e in row] + [e for row in hedge for e in row]


_PX_PER_MM = 20


def visible_cells(r: int, c: int, tol_mm: float = 0.5, offset_mm=(0.0, 0.0)) -> np.ndarray:
    """(GRID_ROWS, GRID_COLS) bool: G cells lying fully inside piece (r, c), shrunk by tol_mm.

    offset_mm shifts the back print relative to the cut, in front coordinates (duplex misregistration).
    """
    px_per_mm = _PX_PER_MM
    poly = outline(r, c)
    pad = 2 * P
    ox, oy = c * P - pad / 2, r * P - pad / 2
    size = int((P + pad) * px_per_mm)
    img = np.zeros((size, size), np.uint8)
    pts = np.round((poly - (ox, oy)) * px_per_mm).astype(np.int32)
    cv2.fillPoly(img, [pts], 255)
    k = int(round(tol_mm * px_per_mm))
    if k > 0:
        img = cv2.erode(img, np.ones((2 * k + 1, 2 * k + 1), np.uint8))
    out = np.zeros((T.GRID_ROWS, T.GRID_COLS), bool)
    s = T.CELL_MM
    for i in range(r * T.PIECE_CELLS - 4, (r + 1) * T.PIECE_CELLS + 4):
        for j in range(c * T.PIECE_CELLS - 4, (c + 1) * T.PIECE_CELLS + 4):
            a, b = front_to_g(i, j)
            if not (0 <= a < T.GRID_ROWS and 0 <= b < T.GRID_COLS):
                continue
            x0 = int(round((j * s + offset_mm[0] - ox) * px_per_mm))
            y0 = int(round((i * s + offset_mm[1] - oy) * px_per_mm))
            x1, y1 = x0 + int(round(s * px_per_mm)), y0 + int(round(s * px_per_mm))
            if 0 <= x0 and 0 <= y0 and x1 <= size and y1 <= size and img[y0:y1, x0:x1].min() == 255:
                out[a, b] = True
    return out
