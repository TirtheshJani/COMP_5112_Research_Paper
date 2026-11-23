"""The print file: every back cell where it should be, and the port matches the verified PDF."""
from pathlib import Path

import numpy as np
import pytest

pdfium = pytest.importorskip("pypdfium2")
pytest.importorskip("reportlab")

from jigsaw import types as T  # noqa: E402
from jigsaw.patch import back_grid  # noqa: E402
from jigsaw.printing import PH, XB, Y0, build  # noqa: E402

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


def test_port_matches_the_verified_pdf(built):
    for page in range(4):
        assert (render(built, page) == render(ROOT / "print" / "reachy_debruijn_jigsaw.pdf", page)).all()
