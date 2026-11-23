import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from jigsaw import geometry as geo
from jigsaw import types as T

ROOT = Path(__file__).resolve().parents[1]


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_export_outlines(tmp_path):
    out = tmp_path / "outlines.json"
    _script("export_outlines").export(out)
    d = json.loads(out.read_text())
    assert (d["rows"], d["cols"]) == (T.PUZZLE_ROWS, T.PUZZLE_COLS) == (7, 5)
    assert d["width"] == pytest.approx(geo.W) and d["height"] == pytest.approx(geo.H)
    assert len(d["pieces"]) == 35
    assert {(p["row"], p["col"]) for p in d["pieces"]} == {(r, c) for r in range(7) for c in range(5)}
    for p in d["pieces"]:
        pts = np.array(p["points"])
        assert pts.shape == (len(geo.outline(p["row"], p["col"])), 2)
        np.testing.assert_allclose(pts, geo.outline(p["row"], p["col"]), atol=0.01)
        assert pts.min() >= -0.01 and pts[:, 0].max() <= geo.W + 0.01 and pts[:, 1].max() <= geo.H + 0.01


def test_committed_outlines_are_current(tmp_path):
    out = tmp_path / "outlines.json"
    _script("export_outlines").export(out)
    assert json.loads(out.read_text()) == json.loads((ROOT / "viewer-ui" / "src" / "outlines.json").read_text())


def test_bleed_matches_printing():
    printing = pytest.importorskip("jigsaw.printing")
    assert _script("export_outlines").BLEED_MM == printing.BLEED
