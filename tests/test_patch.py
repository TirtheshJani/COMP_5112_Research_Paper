from pathlib import Path

import numpy as np
import pytest

from jigsaw import types as T
from jigsaw.patch import back_grid, front_to_g, g_to_front, load_torus, verify

P = Path(__file__).parent.parent / "data" / "patterns"


def test_all_zero_pattern_fails():
    assert verify(np.zeros((12, 12), np.uint8), u=5, wrap=False)["min_distance"] == 0


def test_back_grid_is_strong_form():
    G = back_grid()
    assert G.shape == (T.GRID_ROWS, T.GRID_COLS)
    rep = verify(G, u=5, wrap=False)
    assert rep == {"windows": 68 * 48, "turned_windows": 4 * 68 * 48, "min_distance": 2, "distance1_pairs": 0}


def test_back_grid_is_the_printed_corner():
    assert np.array_equal(back_grid(), load_torus(P / "strong_u5_256.npz")[:72, :52])


def test_control_corner_has_distance_one_pairs():
    rep = verify(load_torus(P / "orient_u5_256.npz")[:72, :52], u=5, wrap=False)
    assert rep["min_distance"] == 1 and rep["distance1_pairs"] > 0


@pytest.mark.parametrize("name,dmin", [("strong_u3_6x6.txt", 2), ("orient_u3_6x6.txt", 1)])
def test_dense_tori(name, dmin):
    rep = verify(load_torus(P / name), u=3, wrap=True)
    assert rep["windows"] == 36 and rep["turned_windows"] == 144 and rep["min_distance"] == dmin


def test_front_back_mapping_round_trip():
    for i in range(-1, 71):
        for j in range(-1, 51):
            assert g_to_front(*front_to_g(i, j)) == (i, j)
    assert front_to_g(0, 0) == (1, 50) and front_to_g(0, 49) == (1, 1)
