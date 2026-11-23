"""Synthetic camera frames of a piece back, for tests and the simulated experiments.

piece_back draws the printed back of one piece (white paper, black cells, thin gray grid lines) with an
alpha mask cut to the jigsaw outline. photograph puts it on a reading mat (or clutter) with a turn,
perspective, scale, blur, noise and an optional finger.
"""
import cv2
import numpy as np

from jigsaw import types as T
from jigsaw.geometry import W, outline
from jigsaw.patch import back_grid

MAT_BGR = (70, 150, 60)       # green reading mat
LINE_MM = 0.2
LINE_GRAY = 140


def piece_back(r: int, c: int, px_per_cell: float, offset_mm=(0.0, 0.0),
               grid: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(gray, alpha) of the back of piece (r, c), seen from the back, upright.

    offset_mm is the duplex misregistration in front coordinates, as in geometry.visible_cells.
    grid replaces the printed back grid (72 x 52), e.g. with the orientation-only control pattern.
    """
    G = back_grid() if grid is None else grid
    s = px_per_cell / T.CELL_MM                                  # pixels per mm
    poly = outline(r, c)
    poly = np.column_stack([W - poly[:, 0], poly[:, 1]])         # back view
    x0, y0 = poly.min(0) - 2 * T.CELL_MM
    x1, y1 = poly.max(0) + 2 * T.CELL_MM
    w, h = int(np.ceil((x1 - x0) * s)), int(np.ceil((y1 - y0) * s))
    gray = np.full((h, w), 255, np.uint8)
    # print shift: front offset (dx, dy) is (-dx, dy) seen from the back
    sx, sy = -offset_mm[0], offset_mm[1]
    m = T.MARGIN_CELLS
    for a in range(G.shape[0]):
        for b in range(G.shape[1]):
            cx0 = ((b - m) * T.CELL_MM + sx - x0) * s
            cy0 = ((a - m) * T.CELL_MM + sy - y0) * s
            if cx0 > w or cy0 > h or cx0 + px_per_cell < 0 or cy0 + px_per_cell < 0:
                continue
            if G[a, b]:
                cv2.rectangle(gray, (int(round(cx0)), int(round(cy0))),
                              (int(round(cx0 + px_per_cell)) - 1, int(round(cy0 + px_per_cell)) - 1), 0, -1)
    lw = max(1, int(round(LINE_MM * s)))
    for b in range(G.shape[1] + 1):
        x = int(round(((b - m) * T.CELL_MM + sx - x0) * s))
        if 0 <= x < w:
            cv2.line(gray, (x, 0), (x, h - 1), LINE_GRAY, lw)
    for a in range(G.shape[0] + 1):
        y = int(round(((a - m) * T.CELL_MM + sy - y0) * s))
        if 0 <= y < h:
            cv2.line(gray, (0, y), (w - 1, y), LINE_GRAY, lw)
    alpha = np.zeros((h, w), np.uint8)
    cv2.fillPoly(alpha, [np.round((poly - (x0, y0)) * s * 8).astype(np.int32)], 255, shift=3)
    return gray, alpha


def photograph(gray: np.ndarray, alpha: np.ndarray, rng: np.random.Generator, angle_deg: float,
               tilt: float = 0.0, blur: float = 0.0, noise: float = 0.0, size: tuple[int, int] = (720, 720),
               scale: float = 1.0, background: str = "mat", finger: bool = False,
               light: float = 1.0, return_transform: bool = False):
    """BGR frame of the piece turned counter-clockwise by angle_deg as seen by the camera.

    With return_transform=True also returns M (3 x 3), mapping piece_back pixels to frame pixels.
    """
    H, Wd = size[1], size[0]
    h, w = gray.shape
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    c = np.float32([w / 2, h / 2])
    a = np.deg2rad(angle_deg)
    rot = np.float32([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])   # counter-clockwise on screen
    centre = np.float32([Wd / 2, H / 2]) + rng.uniform(-0.08, 0.08, 2).astype(np.float32) * min(Wd, H)
    dst = (src - c) @ rot.T * scale + centre
    dst += rng.uniform(-tilt, tilt, (4, 2)).astype(np.float32) * scale * max(w, h) / 2
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    if background == "mat":
        bg = np.empty((H, Wd, 3), np.float32)
        bg[:] = MAT_BGR
        bg *= rng.uniform(0.8, 1.15)
    elif background == "clutter":
        bg = np.full((H, Wd, 3), 120, np.float32)
        for _ in range(8):
            p = rng.integers(0, [Wd, H], 2)
            q = p + rng.integers(20, 200, 2)
            cv2.rectangle(bg, tuple(int(v) for v in p), tuple(int(v) for v in q),
                          tuple(float(v) for v in rng.uniform(0, 255, 3)), -1)
    else:
        bg = np.full((H, Wd, 3), 128, np.float32)
    # lighting gradient across the frame
    yy, xx = np.mgrid[0:H, 0:Wd].astype(np.float32)
    g = 1 + 0.15 * light * ((xx / Wd - 0.5) * rng.uniform(-1, 1) + (yy / H - 0.5) * rng.uniform(-1, 1))
    piece = cv2.warpPerspective(gray, M, (Wd, H), flags=cv2.INTER_AREA, borderValue=255).astype(np.float32)
    al = cv2.warpPerspective(alpha, M, (Wd, H), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
    paper = np.repeat(piece[..., None], 3, axis=2) * np.float32([0.97, 1.0, 1.02])   # slightly warm light
    img = bg * (1 - al) + paper * al
    if finger:
        ys, xs = np.nonzero(al[..., 0] > 0.5)
        k = int(rng.integers(len(xs)))
        tip = np.array([xs[k], ys[k]], float)
        out = tip - np.array([Wd / 2, H / 2])
        out = out / (np.linalg.norm(out) + 1e-6)
        cv2.line(img, tuple(int(v) for v in tip), tuple(int(v) for v in tip + out * 400),
                 (110, 140, 200), int(18 * scale + 10))
    img *= g[..., None]
    if blur > 0:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    if noise > 0:
        img += rng.normal(0, noise, img.shape).astype(np.float32)
    out = np.clip(img, 0, 255).astype(np.uint8)
    return (out, M) if return_transform else out
