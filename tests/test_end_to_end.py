"""Q5: page 2 of the S5 PDF -> S1 reader -> S4 phrase -> parse -> front tile, for all 35 pieces, no robot.

Each piece is cut from the rendered back page, put on the green mat, turned k = index % 4 quarter turns
counter-clockwise, read, phrased, and the sentence is parsed back. Then the physical front of the piece
(page 1 of the same PDF) is brought to the state the person sees after flipping the piece over about its
vertical axis, the announced turn is applied as seen from the picture side (the reading documented in
jigsaw/voice/phrases.py), and the result is compared with the picture tile at the announced row and column.
"""
import re
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
import pytest
from PIL import Image

from jigsaw import geometry as geo
from jigsaw import printing as pr
from jigsaw import types as T
from jigsaw.reader import PieceReader
from jigsaw.render import photograph
from jigsaw.types import Read
from jigsaw.voice.phrases import TURN_SENTENCE, phrase_read

ROOT = Path(__file__).resolve().parent.parent
PXMM = 6.0          # page render resolution: 21.6 px per cell
TILE = 64
TOL = 12.0          # mean absolute difference, grey levels of 255
SENTENCE = re.compile(r"Row (\d+), column (\d+)\. (.*)")
TURN_OF = {s: k for k, s in TURN_SENTENCE.items()}


def render_page(pdf, index):
    page = pdf[index]
    img = page.render(scale=PXMM * 25.4 / 72).to_numpy()
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY if img.shape[2] == 3 else cv2.COLOR_RGBA2GRAY)


def cut_back(page2, r, c):
    """(gray, alpha) of piece (r, c) cut from the rendered back page, seen from the back, upright."""
    poly = geo.outline(r, c)
    poly = np.column_stack([pr.XB + geo.W - poly[:, 0], pr.Y0 + poly[:, 1]]) * PXMM
    pad = 2 * T.CELL_MM * PXMM
    x0, y0 = np.floor(poly.min(0) - pad).astype(int)
    x1, y1 = np.ceil(poly.max(0) + pad).astype(int)
    gray = page2[y0:y1, x0:x1].copy()
    alpha = np.zeros_like(gray)
    cv2.fillPoly(alpha, [np.round((poly - (x0, y0)) * 8).astype(np.int32)], 255, shift=3)
    return gray, alpha


def tile_from_page1(page1, r, c):
    p = geo.P
    x, y = (pr.X0 + c * p) * PXMM, (pr.Y0 + r * p) * PXMM
    return page1[round(y):round(y + p * PXMM), round(x):round(x + p * PXMM)]


def tile_from_picture(pic, r, c):
    k = pic.shape[1] / (geo.W + 2 * pr.BLEED)
    p = geo.P
    x, y = (pr.BLEED + c * p) * k, (pr.BLEED + r * p) * k
    return pic[round(y):round(y + p * k), round(x):round(x + p * k)]


def small(a):
    return cv2.resize(a, (TILE, TILE), interpolation=cv2.INTER_AREA).astype(np.float32)


def mad(a, b):
    return float(np.abs(small(a) - small(b)).mean())


@pytest.fixture(scope="module")
def sheets():
    pdf = pdfium.PdfDocument(str(ROOT / "print" / "reachy_debruijn_jigsaw.pdf"))
    pic = np.asarray(Image.open(ROOT / "print" / "picture_portrait.png").convert("L"))
    return render_page(pdf, 0), render_page(pdf, 1), pic


def test_every_piece_is_read_phrased_and_shows_its_picture_tile(sheets):
    page1, page2, pic = sheets
    reader = PieceReader()
    rng = np.random.default_rng(0)
    turns_used, rejected, wrong, bad = set(), [], [], []
    for n, (r, c) in enumerate((r, c) for r in range(T.PUZZLE_ROWS) for c in range(T.PUZZLE_COLS)):
        k = n % 4
        gray, alpha = cut_back(page2, r, c)
        frame = photograph(gray, alpha, rng, 90.0 * k, size=(1280, 720))
        d = reader.read(frame)
        if not isinstance(d, Read):
            rejected.append(((r, c, k), d))
            continue
        m = SENTENCE.fullmatch(phrase_read(d))
        row, col, turn = int(m.group(1)) - 1, int(m.group(2)) - 1, TURN_OF[m.group(3)]
        turns_used.add(turn)
        if (row, col, turn) != (r, c, k):
            wrong.append(((r, c, k), (row, col, turn)))
            continue
        # Front of the true piece after flipping about the vertical axis: the picture turned k quarter turns clockwise.
        in_hand = np.rot90(tile_from_page1(page1, r, c), -k)
        shown = np.rot90(in_hand, turn)                     # announced turn, counter-clockwise from the picture side
        truth = tile_from_picture(pic, row, col)
        errs = [mad(np.rot90(shown, q), truth) for q in range(4)]
        if not (errs[0] < TOL and errs[0] < min(errs[1:])):
            bad.append(((r, c, k), [round(e, 1) for e in errs]))
    assert not rejected, f"{len(rejected)} of 35 rejected: {rejected}"
    assert not wrong, f"wrong reads: {wrong}"
    assert not bad, f"tile mismatch: {bad}"
    assert turns_used == {0, 1, 2, 3}
