from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from jigsaw import types as T
from jigsaw.decode import build_table, decode_grid, decode_single, rot_affine
from jigsaw.geometry import visible_cells
from jigsaw.patch import back_grid, load_torus, windows
from jigsaw.types import Position, Read, Reject

P = Path(__file__).parent.parent / "data" / "patterns"


@pytest.fixture(scope="module")
def G():
    return back_grid()


@pytest.fixture(scope="module")
def table(G):
    return build_table(G)


def turned(pattern, u, wrap):
    for i, j, w in windows(pattern, u, wrap):
        for k in range(4):
            yield i, j, k, np.rot90(w, k)


def seen_piece(G, r, c, k, **kw):
    """What the camera sees of piece (r, c) at turn k: the cropped cells and the visibility mask."""
    vis = visible_cells(r, c, **kw)
    a, b = np.nonzero(vis)
    sub = (slice(a.min(), a.max() + 1), slice(b.min(), b.max() + 1))
    return np.rot90(G[sub], k), np.rot90(vis[sub], k)


def test_rot_affine_matches_numpy():
    n = 5
    idx = np.arange(n * n).reshape(n, n)
    for k in range(4):
        seen = np.rot90(idx, k)
        M, c = rot_affine(k, n)
        for a in range(n):
            for b in range(n):
                p, q = M @ (a, b) + c
                assert seen[a, b] == idx[p, q]


def test_table_sizes(G):
    assert len(build_table(G)) == 68 * 48
    strong3 = load_torus(P / "strong_u3_6x6.txt")
    t = build_table(strong3, 3, wrap=True)
    assert len(t) == 36 and set(t.values()) == {(i, j) for i in range(6) for j in range(6)}


@pytest.mark.parametrize("name,u,wrap", [(None, 5, False), ("strong_u3_6x6.txt", 3, True),
                                         ("orient_u3_6x6.txt", 3, True)])
def test_single_decodes_every_turned_window(G, name, u, wrap):
    pattern = G if name is None else load_torus(P / name)
    table = build_table(pattern, u, wrap)
    for i, j, k, w in turned(pattern, u, wrap):
        assert decode_single(w, table) == Position(i, j, k)


@pytest.mark.parametrize("name,u,wrap", [(None, 5, False), ("strong_u3_6x6.txt", 3, True)])
def test_single_rejects_every_flip_on_strong_form(G, name, u, wrap):
    pattern = G if name is None else load_torus(P / name)
    table = build_table(pattern, u, wrap)
    n = 0
    for _, _, _, w in turned(pattern, u, wrap):
        for a in range(u):
            for b in range(u):
                x = w.copy()
                x[a, b] ^= 1
                assert isinstance(decode_single(x, table), Reject)
                n += 1
    assert n == 4 * len(table) * u * u


def test_single_is_fooled_on_the_control_torus():
    orient3 = load_torus(P / "orient_u3_6x6.txt")
    table = build_table(orient3, 3, True)
    wrong = 0
    for i, j, k, w in turned(orient3, 3, True):
        for a in range(3):
            for b in range(3):
                x = w.copy()
                x[a, b] ^= 1
                d = decode_single(x, table)
                wrong += isinstance(d, Position) and d != Position(i, j, k)
    assert wrong > 0


def test_every_piece_every_turn(G, table):
    for r in range(T.PUZZLE_ROWS):
        for c in range(T.PUZZLE_COLS):
            for k in range(4):
                cells, mask = seen_piece(G, r, c, k)
                assert decode_grid(cells, mask, table) == Read(r, c, k), (r, c, k)


def test_every_piece_with_misregistration(G, table):
    for r in range(T.PUZZLE_ROWS):
        for c in range(T.PUZZLE_COLS):
            for off in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 3), (3, 0)]:
                cells, mask = seen_piece(G, r, c, 1, offset_mm=off)
                assert decode_grid(cells, mask, table) == Read(r, c, 1), (r, c, off)


def test_one_misread_cell_never_misplaces_a_piece(G, table):
    wrong = 0
    for r in range(T.PUZZLE_ROWS):
        for c in range(T.PUZZLE_COLS):
            cells, mask = seen_piece(G, r, c, 3)
            for a, b in zip(*np.nonzero(mask)):
                x = cells.copy()
                x[a, b] ^= 1
                d = decode_grid(x, mask, table)
                wrong += isinstance(d, Read) and d != Read(r, c, 3)
    assert wrong == 0


def test_rejects_garbage(table):
    rng = np.random.default_rng(0)
    for _ in range(200):
        cells = rng.integers(0, 2, (14, 14)).astype(np.uint8)
        assert isinstance(decode_grid(cells, np.ones_like(cells, bool), table), Reject)
    assert decode_grid(np.zeros((4, 4), np.uint8), np.ones((4, 4), bool), table) == Reject("no_window")


def test_two_and_three_misread_cells_never_misplace_a_piece(G, table):
    rng = np.random.default_rng(7)
    wrong = reads = trials = 0
    for r in range(T.PUZZLE_ROWS):
        for c in range(T.PUZZLE_COLS):
            for k in range(4):
                cells, mask = seen_piece(G, r, c, k)
                idx = np.argwhere(mask)
                for n_flip in (2, 3):
                    for _ in range(3):
                        x = cells.copy()
                        for a, b in idx[rng.choice(len(idx), n_flip, replace=False)]:
                            x[a, b] ^= 1
                        d = decode_grid(x, mask, table)
                        trials += 1
                        assert d == Read(r, c, k) or isinstance(d, Reject), (r, c, k, n_flip, d)
                        reads += isinstance(d, Read)
                        wrong += isinstance(d, Read) and d != Read(r, c, k)
    assert wrong == 0 and trials == 35 * 4 * 2 * 3 and reads > 0


_TABLE = build_table(back_grid())


@settings(max_examples=200, deadline=None, derandomize=True)
@given(st.integers(0, 2 ** 64 - 1), st.integers(0, 2 ** 64 - 1))
def test_decoders_never_raise(bits, mbits):
    cells = np.array([(bits >> n) & 1 for n in range(64)], np.uint8).reshape(8, 8)
    mask = np.array([(mbits >> n) & 1 for n in range(64)], bool).reshape(8, 8)
    t = _TABLE
    assert isinstance(decode_grid(cells, mask, t), (Read, Reject))
    assert isinstance(decode_single(cells[:5, :5], t), (Position, Reject))


def test_control_pattern_table_checks_against_its_own_pattern():
    ctrl = load_torus(P / "orient_u5_256.npz")[:72, :52]
    t = build_table(ctrl)
    assert np.array_equal(t.pattern, ctrl)
    for r, c, k in [(0, 0, 0), (3, 2, 1), (6, 4, 3)]:
        cells, mask = seen_piece(ctrl, r, c, k)
        assert decode_grid(cells, mask, t) == Read(r, c, k)
