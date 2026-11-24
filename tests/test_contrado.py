"""Contrado edition: the back grid, the mapping to Contrado's 8 x 6 pieces, and one-cell errors."""
from pathlib import Path

import numpy as np
import pytest

from jigsaw import contrado as K
from jigsaw.decode import build_table
from jigsaw.patch import verify
from jigsaw.types import Read

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def table():
    return build_table(K.back_grid())


def test_grid_is_strong_and_disjoint_from_card():
    G = K.back_grid()
    assert G.shape == (79, 105)
    assert verify(G, 5, wrap=False)["min_distance"] == 2
    a, b = K.G_ORIGIN
    assert a >= 72 or b >= 52            # no overlap with the card's torus[0:72, 0:52]


def _piece_block(row, col, flip):
    """A 12 x 12 block of G cells behind the middle of front piece (row, col)."""
    xf = K.BLEED_PX + (col + 0.5) * K.PITCH_X
    yf = K.BLEED_PX + (row + 0.5) * K.PITCH_Y
    xb, yb = (K.PANEL_W - xf, yf) if flip == "lr" else (xf, K.PANEL_H - yf)
    a, b = int(yb // K.CELL_PX) - 6, int(xb // K.CELL_PX) - 6
    G = K.back_grid()
    return G[a:a + 12, b:b + 12]


@pytest.mark.parametrize("flip", ["lr", "tb"])
def test_every_piece_every_turn(table, flip):
    for row in range(K.ROWS):
        for col in range(K.COLS):
            cells = _piece_block(row, col, flip)
            mask = np.ones_like(cells, bool)
            for k in range(4):
                d = K.decode(np.rot90(cells, k), np.rot90(mask, k), table, flip)
                assert d == Read(row, col, k if flip == "lr" else (k + 2) % 4)


def test_one_wrong_cell_never_names_another_piece(table):
    rng = np.random.default_rng(0)
    for row in range(K.ROWS):
        for col in range(K.COLS):
            cells = _piece_block(row, col, "lr").copy()
            y, x = rng.integers(0, 12, 2)
            cells[y, x] ^= 1
            d = K.decode(cells, np.ones_like(cells, bool), table)
            assert not isinstance(d, Read) or (d.row, d.col) == (row, col)


def test_back_png_carries_g():
    png = ROOT / "print" / "contrado" / "contrado_back_3130x2362.png"
    if not png.exists():
        pytest.skip("print file not built")
    from PIL import Image
    img = np.array(Image.open(png).convert("L"))
    assert img.shape == (K.PANEL_H, K.PANEL_W)
    c = K.CELL_PX
    ys = (np.arange(K.G_ROWS) * c + c // 2).clip(max=img.shape[0] - 1)
    xs = (np.arange(K.G_COLS) * c + c // 2).clip(max=img.shape[1] - 1)
    assert ((img[np.ix_(ys, xs)] < 128).astype(np.uint8) == K.back_grid()).all()
