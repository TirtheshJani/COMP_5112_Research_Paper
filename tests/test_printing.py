"""The print file: every back cell where it should be, and the port matches the verified PDF."""
from pathlib import Path

import numpy as np
import pytest

pdfium = pytest.importorskip("pypdfium2")
pytest.importorskip("reportlab")

import importlib.util  # noqa: E402

from jigsaw import geometry as geo  # noqa: E402
from jigsaw import printing as pr  # noqa: E402
from jigsaw import types as T  # noqa: E402
from jigsaw.patch import back_grid, front_to_g  # noqa: E402
from jigsaw.printing import PH, PW, X0, XB, Y0, build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DPI = 300
PX = DPI / 25.4


def render(pdf, page):
    doc = pdfium.PdfDocument(str(pdf))
    return np.asarray(doc[page].render(scale=DPI / 72).to_pil().convert("L"), int)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("print") / "sheets.pdf"
    build(str(ROOT / "print" / "picture_portrait.png"), str(out))
    return out


def test_back_cells_match_the_grid(built):
    back = render(built, 1)
    assert abs(back.shape[0] / PX - PH) < 0.5
    G = back_grid()
    left, top = XB - T.MARGIN_CELLS * T.CELL_MM, Y0 - T.MARGIN_CELLS * T.CELL_MM
    q = int(T.CELL_MM * PX * 0.2)
    read = np.zeros_like(G)
    for a in range(G.shape[0]):
        for b in range(G.shape[1]):
            cx, cy = int((left + (b + 0.5) * T.CELL_MM) * PX), int((top + (a + 0.5) * T.CELL_MM) * PX)
            read[a, b] = back[cy - q:cy + q, cx - q:cx + q].mean() < 128
    assert (read == G).all()


def test_front_cells_are_mirrored_on_the_back(built):
    """Page 2 is the back of page 1 after a flip on the long edge, so page-1 x maps to PW - x on page 2.
    Front cell (i, j) sits at (X0 + j*cell, Y0 + i*cell) on page 1 and must show G[front_to_g(i, j)].
    Uses only page-1 geometry (X0, Y0, PW) and the documented mirror, not the layout constants XB or MARGIN_CELLS
    that the back page is drawn from."""
    back = render(built, 1)
    G = back_grid()
    cell = T.CELL_MM
    q = int(cell * PX * 0.2)
    rows, cols = T.PUZZLE_ROWS * T.PIECE_CELLS, T.PUZZLE_COLS * T.PIECE_CELLS
    for i in range(rows):
        for j in range(cols):
            cx = int((PW - (X0 + (j + 0.5) * cell)) * PX)
            cy = int((Y0 + (i + 0.5) * cell) * PX)
            dark = back[cy - q:cy + q, cx - q:cx + q].mean() < 128
            assert dark == bool(G[front_to_g(i, j)]), f"front cell ({i}, {j})"
    # The grid is not mirror-symmetric, so this check cannot pass for an unmirrored page.
    unmirrored = sum(bool(G[front_to_g(i, j)]) != bool(G[front_to_g(i, cols - 1 - j)]) for i in range(rows) for j in range(cols))
    assert unmirrored > rows * cols // 4


def test_port_matches_the_verified_pdf(built):
    """Exact pixel equality at 300 dpi. It depends on the pdfium version and on build() writing with invariant=1,
    and it fails on any deliberate change to the print: regenerate print/reachy_debruijn_jigsaw.pdf in the same commit."""
    for page in range(4):
        assert (render(built, page) == render(ROOT / "print" / "reachy_debruijn_jigsaw.pdf", page)).all()


def test_make_picture_defaults_match_the_committed_picture():
    spec = importlib.util.spec_from_file_location("make_picture", ROOT / "scripts" / "make_picture.py")
    mp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mp)            # must not parse argv or draw at import
    assert mp.parse_args(["make_picture.py", "o.png"]) == ("o.png", geo.W, geo.H, pr.BLEED)
    assert mp.parse_args(["make_picture.py", "o.png", "10", "20", "1"]) == ("o.png", 10.0, 20.0, 1.0)
    from PIL import Image
    w, h = Image.open(ROOT / "print" / "picture_portrait.png").size
    assert (round((geo.W + 2 * pr.BLEED) * mp.MM), round((geo.H + 2 * pr.BLEED) * mp.MM)) == (w, h)
