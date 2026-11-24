"""Check the Contrado edition before ordering.

A stand-in die (8 x 6 pieces, knobs about 9 mm deep and 12 mm wide, knob directions random, so some pieces
have blanks on opposite sides, as Contrado's do) is cut out of the actual back PNG with the print shifted
up to +-1.5 mm against the cut.

1. Cell level: every piece, 4 turns, 25 random shifts. Reads must be right; one flipped cell must never
   give a wrong piece.
2. Image level: photographs on the green mat through vision.read_grid at several pixels per cell.

Usage: python scripts/verify_contrado.py BACK_PNG [--flip lr|tb]
"""
import sys

import cv2
import numpy as np
from PIL import Image

from jigsaw import contrado as K
from jigsaw.decode import build_table
from jigsaw.geometry import _edge
from jigsaw.render import photograph
from jigsaw.types import Read
from jigsaw.vision import read_grid

TAB, JIT = 0.085, 0.03
rng = np.random.default_rng(11)


def die(seed=3):
    """Front-trim outlines (mm) of all pieces, Contrado-like: random knob directions."""
    r = np.random.default_rng(seed)
    pw, ph = 255.0 / K.COLS, 190.0 / K.ROWS
    v = [[_edge(((k + 1) * pw, i * ph), ((k + 1) * pw, (i + 1) * ph), (1, 0), r.choice([-1, 1]),
                r.uniform(-JIT, JIT, 5), TAB) for k in range(K.COLS - 1)] for i in range(K.ROWS)]
    h = [[_edge((j * pw, (k + 1) * ph), ((j + 1) * pw, (k + 1) * ph), (0, 1), r.choice([-1, 1]),
                r.uniform(-JIT, JIT, 5), TAB) for j in range(K.COLS)] for k in range(K.ROWS - 1)]
    out = {}
    for i in range(K.ROWS):
        for j in range(K.COLS):
            x0, y0, x1, y1 = j * pw, i * ph, (j + 1) * pw, (i + 1) * ph
            top = np.array([(x0, y0), (x1, y0)]) if i == 0 else h[i - 1][j]
            right = np.array([(x1, y0), (x1, y1)]) if j == K.COLS - 1 else v[i][j]
            bottom = np.array([(x1, y1), (x0, y1)]) if i == K.ROWS - 1 else h[i][j][::-1]
            left = np.array([(x0, y1), (x0, y0)]) if j == 0 else v[i][j - 1][::-1]
            out[i, j] = np.vstack([top[:-1], right[:-1], bottom[:-1], left[:-1]])
    return out


def back_poly_px(poly_mm, shift_mm, flip):
    """Front-trim mm outline to back panel pixels, with the print shifted by shift_mm against the cut."""
    x = (poly_mm[:, 0] + 5.0 + shift_mm[0]) * K.PX_PER_MM
    y = (poly_mm[:, 1] + 5.0 + shift_mm[1]) * K.PX_PER_MM
    return np.column_stack([K.PANEL_W - x, y]) if flip == "lr" else np.column_stack([x, K.PANEL_H - y])


def piece_mask(poly_px):
    x0, y0 = np.floor(poly_px.min(0)).astype(int) - 4
    x1, y1 = np.ceil(poly_px.max(0)).astype(int) + 4
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.round((poly_px - (x0, y0)) * 8).astype(np.int32)], 255, shift=3)
    return m, x0, y0


def cells_of(poly_px, G, tol_mm=0.4):
    m, x0, y0 = piece_mask(poly_px)
    t = max(1, int(round(tol_mm * K.PX_PER_MM)))
    m = cv2.erode(m, np.ones((2 * t + 1, 2 * t + 1), np.uint8))
    c = K.CELL_PX
    a0, a1 = max(0, y0 // c), min(G.shape[0], (y0 + m.shape[0]) // c + 1)
    b0, b1 = max(0, x0 // c), min(G.shape[1], (x0 + m.shape[1]) // c + 1)
    vis = np.zeros((a1 - a0, b1 - b0), bool)
    for a in range(a0, a1):
        for b in range(b0, b1):
            ys, xs = a * c - y0, b * c - x0
            if ys < 0 or xs < 0 or ys + c > m.shape[0] or xs + c > m.shape[1]:
                continue
            vis[a - a0, b - b0] = m[ys:ys + c, xs:xs + c].min() == 255
    return G[a0:a1, b0:b1], vis


def windows_in(vis):
    h, w = vis.shape
    return sum(vis[y:y + 5, x:x + 5].all() for y in range(h - 4) for x in range(w - 4))


def cell_level(G, table, outlines, flip, shifts=25):
    ok = wrong = rej = 0
    err_wrong = err_total = 0
    min_win = 99
    for (i, j), poly in outlines.items():
        for s in range(shifts):
            sh = rng.uniform(-1.5, 1.5, 2)
            cells, vis = cells_of(back_poly_px(poly, sh, flip), G)
            min_win = min(min_win, windows_in(vis))
            for k in range(4):
                d = K.decode(np.rot90(cells, k), np.rot90(vis, k), table, flip)
                if d == Read(i, j, k if flip == "lr" else (k + 2) % 4):
                    ok += 1
                elif isinstance(d, Read):
                    wrong += 1
                else:
                    rej += 1
                ys, xs = np.nonzero(vis)
                if len(ys):
                    q = rng.integers(len(ys))
                    bad = cells.copy()
                    bad[ys[q], xs[q]] ^= 1
                    d2 = K.decode(np.rot90(bad, k), np.rot90(vis, k), table, flip)
                    err_total += 1
                    err_wrong += isinstance(d2, Read) and (d2.row, d2.col) != (i, j)
    return dict(ok=ok, wrong=wrong, rejected=rej, one_cell_error_trials=err_total,
                one_cell_error_wrong=int(err_wrong), min_windows_per_piece=int(min_win))


def image_level(back_png, table, outlines, flip, ppcs=(9, 11, 14, 18), per=2):
    back = np.array(Image.open(back_png).convert("L"))
    res = {}
    for ppc in ppcs:
        ok = wrong = rej = 0
        reasons = {}
        scale = ppc / K.CELL_PX
        for (i, j), poly in outlines.items():
            for _ in range(per):
                pp = back_poly_px(poly, rng.uniform(-1.5, 1.5, 2), flip)
                m, x0, y0 = piece_mask(pp)
                gray = back[max(0, y0):y0 + m.shape[0], max(0, x0):x0 + m.shape[1]]
                al = m[max(0, -y0):max(0, -y0) + gray.shape[0], max(0, -x0):max(0, -x0) + gray.shape[1]]
                sz = (max(1, round(gray.shape[1] * scale)), max(1, round(gray.shape[0] * scale)))
                g2 = cv2.resize(gray, sz, interpolation=cv2.INTER_AREA)
                a2 = cv2.resize(al, sz, interpolation=cv2.INTER_AREA)
                k = int(rng.integers(4))
                ang = 90 * k + rng.uniform(-20, 20)
                frame = photograph(g2, a2, rng, ang, tilt=0.06, blur=1.0, noise=4.0, size=(720, 720))
                gr = read_grid(frame)
                d = gr if not hasattr(gr, "cells") else K.decode(gr.cells, gr.mask, table, flip)
                if isinstance(d, Read):
                    if (d.row, d.col) == (i, j):
                        ok += 1
                    else:
                        wrong += 1
                else:
                    rej += 1
                    reasons[d.reason] = reasons.get(d.reason, 0) + 1
        res[ppc] = dict(ok=ok, wrong=wrong, rejected=rej, reasons=reasons)
    return res


if __name__ == "__main__":
    back_png = sys.argv[1]
    flip = sys.argv[sys.argv.index("--flip") + 1] if "--flip" in sys.argv else "lr"
    G = K.back_grid()
    # the PNG must carry G exactly: sample every cell centre
    img = np.array(Image.open(back_png).convert("L"))
    c = K.CELL_PX
    ys = (np.arange(G.shape[0]) * c + c // 2).clip(max=img.shape[0] - 1)
    xs = (np.arange(G.shape[1]) * c + c // 2).clip(max=img.shape[1] - 1)
    printed = (img[np.ix_(ys, xs)] < 128).astype(np.uint8)
    print("cells in PNG equal G:", bool((printed == G).all()), "mismatches:", int((printed != G).sum()))
    table = build_table(G)
    outlines = die()
    print("cell level", flip, cell_level(G, table, outlines, flip))
    if "--images" in sys.argv:
        print("image level", flip, image_level(back_png, table, outlines, flip))
