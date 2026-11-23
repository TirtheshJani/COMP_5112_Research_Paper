"""Pattern files, the printed back grid, and the front/back mapping (CONTRACTS.md section 3)."""
from pathlib import Path

import numpy as np

from jigsaw import types as T

PATTERNS = Path(__file__).resolve().parent.parent / "data" / "patterns"


def load_torus(path) -> np.ndarray:
    """(R, C) uint8 from .npz (keys bits, shape) or .txt (rows of 0 and 1)."""
    path = Path(path)
    if path.suffix == ".npz":
        z = np.load(path)
        r, c = (int(v) for v in z["shape"])
        return np.unpackbits(z["bits"], bitorder="big")[: r * c].reshape(r, c).astype(np.uint8)
    return np.atleast_2d(np.loadtxt(path, dtype=np.uint8))


def back_grid() -> np.ndarray:
    """The printed back pattern G (GRID_ROWS x GRID_COLS), as seen when looking at the back."""
    return load_torus(PATTERNS / "strong_u5_256.npz")[: T.GRID_ROWS, : T.GRID_COLS].copy()


def front_to_g(i: int, j: int) -> tuple[int, int]:
    """Front lattice cell (i, j) (may be -1 or one past the end, the margin) to its G index."""
    return i + T.MARGIN_CELLS, T.PUZZLE_COLS * T.PIECE_CELLS - 1 - j + T.MARGIN_CELLS


def g_to_front(a: int, b: int) -> tuple[int, int]:
    return a - T.MARGIN_CELLS, T.PUZZLE_COLS * T.PIECE_CELLS - 1 - (b - T.MARGIN_CELLS)


def windows(pattern: np.ndarray, u: int, wrap: bool):
    """Yield (i, j, window) for every upright u x u window."""
    R, C = pattern.shape
    rows = range(R) if wrap else range(R - u + 1)
    cols = range(C) if wrap else range(C - u + 1)
    for i in rows:
        for j in cols:
            w = pattern.take(range(i, i + u), 0, mode="wrap").take(range(j, j + u), 1, mode="wrap")
            yield i, j, w


def verify(pattern: np.ndarray, u: int, wrap: bool) -> dict:
    """Count windows and turned windows, and the minimum Hamming distance between distinct turned windows."""
    weights = 1 << np.arange(u * u, dtype=np.int64)
    codes = []
    for _, _, w in windows(pattern, u, wrap):
        for k in range(4):
            codes.append(int((np.rot90(w, k).ravel().astype(np.int64) * weights).sum()))
    n = len(codes)
    uniq = set(codes)
    d1_pairs = sum(1 for x in uniq for bit in range(u * u) if (x ^ (1 << bit)) in uniq) // 2
    # 0: two turned windows coincide; 1: some pair differs in one cell; 2: means "at least 2"
    min_d = 0 if len(uniq) < n else (1 if d1_pairs else 2)
    return {"windows": n // 4, "turned_windows": n, "min_distance": min_d, "distance1_pairs": d1_pairs}
