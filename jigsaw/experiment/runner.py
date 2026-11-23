"""Classify decisions, the single-window decoder, and misread counting (S2 E1, E4).

classify:      a read is correct only if row, col and turn all match the truth.
decide_single: the paper's single read. Decode the top-left-most complete u x u window only, then place the
               piece exactly as decode.decode_grid does (placement, off-puzzle checks, centroid), without
               decode_grid's agreement and whole-piece consistency checks.
misread_cells: count visible cells whose read bit differs from the printed cell at the place the camera
               looked. Cell centre -> GridRead.H -> frame pixel -> inverse of photograph's M -> piece_back
               pixel -> truth_raster.
"""
from typing import Literal

import cv2
import numpy as np

from jigsaw import types as T
from jigsaw.decode import Table, decode_single, placement, rot_affine
from jigsaw.geometry import W, outline
from jigsaw.patch import back_grid, g_to_front
from jigsaw.types import Decision, GridRead, Position, Read, Reject

OFF_GRID = 255        # truth_raster value where no printed cell is


def classify(truth: Read, decision: Decision) -> Literal["correct", "rejected", "wrong"]:
    if isinstance(decision, Reject):
        return "rejected"
    return "correct" if decision == truth else "wrong"


def decide_single(grid_read: GridRead, table: Table) -> Decision:
    cells = np.asarray(grid_read.cells, np.uint8)
    mask = np.asarray(grid_read.mask, bool)
    u = table.u
    h, w = cells.shape
    start = next(((y, x) for y in range(h - u + 1) for x in range(w - u + 1) if mask[y:y + u, x:x + u].all()), None)
    if start is None:
        return Reject("no_window")
    y, x = start
    d = decode_single(cells[y:y + u, x:x + u], table)
    if not isinstance(d, Position):
        return d
    turn, ti, tj = placement(y, x, d, u)
    # From here on, the same steps as decode.decode_grid after its agreement check, minus its consistency check.
    M, _ = rot_affine(turn, u)
    ys, xs = np.nonzero(mask)
    g = (M @ np.vstack([ys, xs])).T + (ti, tj)
    R, C = table.shape
    if not ((g[:, 0] >= 0) & (g[:, 0] < R) & (g[:, 1] >= 0) & (g[:, 1] < C)).all():
        return Reject("off_puzzle")
    front = np.array([g_to_front(a, b) for a, b in g], float) + 0.5
    ci, cj = front.mean(axis=0)
    row, col = int(np.floor(ci / T.PIECE_CELLS)), int(np.floor(cj / T.PIECE_CELLS))
    if not (0 <= row < T.PUZZLE_ROWS and 0 <= col < T.PUZZLE_COLS):
        return Reject("off_puzzle")
    return Read(row, col, turn)


def truth_raster(r: int, c: int, px_per_cell: float, shape: tuple[int, int], grid: np.ndarray | None = None,
                 offset_mm=(0.0, 0.0)) -> np.ndarray:
    """(h, w) uint8 at render.piece_back pixel resolution: the printed bit (1 = black) of the cell under each
    pixel, OFF_GRID outside the printed grid. Mirrors piece_back's layout; shape is piece_back's gray.shape.
    """
    G = back_grid() if grid is None else np.asarray(grid, np.uint8)
    s = px_per_cell / T.CELL_MM
    poly = outline(r, c)
    poly = np.column_stack([W - poly[:, 0], poly[:, 1]])
    x0, y0 = poly.min(0) - 2 * T.CELL_MM
    sx, sy = -offset_mm[0], offset_mm[1]
    h, w = shape
    b = np.floor(((np.arange(w) + 0.5) / s + x0 - sx) / T.CELL_MM).astype(int) + T.MARGIN_CELLS
    a = np.floor(((np.arange(h) + 0.5) / s + y0 - sy) / T.CELL_MM).astype(int) + T.MARGIN_CELLS
    ok = (a[:, None] >= 0) & (a[:, None] < G.shape[0]) & (b[None, :] >= 0) & (b[None, :] < G.shape[1])
    out = np.full((h, w), OFF_GRID, np.uint8)
    aa, bb = np.broadcast_arrays(a[:, None], b[None, :])
    out[ok] = G[aa[ok], bb[ok]]
    return out


def misread_cells(grid_read: GridRead, M: np.ndarray, truth_grid: np.ndarray) -> int:
    """Visible cells whose read bit differs from truth_grid (a truth_raster) where the camera looked."""
    ys, xs = np.nonzero(np.asarray(grid_read.mask, bool))
    if len(ys) == 0:
        return 0
    centres = np.float64(np.column_stack([xs + 0.5, ys + 0.5])).reshape(-1, 1, 2)
    frame = cv2.perspectiveTransform(centres, np.asarray(grid_read.H, np.float64))
    back = cv2.perspectiveTransform(frame, np.linalg.inv(np.asarray(M, np.float64))).reshape(-1, 2)
    px, py = np.round(back[:, 0]).astype(int), np.round(back[:, 1]).astype(int)
    h, w = truth_grid.shape
    inside = (px >= 0) & (px < w) & (py >= 0) & (py < h)
    truth = np.full(len(ys), OFF_GRID, np.int64)
    truth[inside] = truth_grid[py[inside], px[inside]]
    read = np.asarray(grid_read.cells, np.int64)[ys, xs]
    return int((read != truth).sum())
