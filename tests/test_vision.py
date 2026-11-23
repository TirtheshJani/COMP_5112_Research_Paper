"""The camera reader on rendered photos. The bar is the paper's: no wrong read, few rejections."""
import cv2
import numpy as np
import pytest

from jigsaw import types as T
from jigsaw.decode import build_table, decode_grid
from jigsaw.patch import back_grid
from jigsaw.render import photograph, piece_back
from jigsaw.types import GridRead, Read, Reject
from jigsaw.vision import read_grid, undistort


@pytest.fixture(scope="module")
def table():
    return build_table(back_grid())


_cache = {}


def shoot(rng, r, c, ppc, angle, **kw):
    key = (r, c, ppc)
    if key not in _cache:
        _cache[key] = piece_back(r, c, ppc)
    return photograph(*_cache[key], rng, angle, **kw)


def decide(img, table):
    gr = read_grid(img)
    return decode_grid(gr.cells, gr.mask, table) if isinstance(gr, GridRead) else gr


def run(table, n, seed, ppc_range=(12, 28), finger=0.0, background="mat"):
    rng = np.random.default_rng(seed)
    correct = rejected = wrong = turn_wrong = 0
    for _ in range(n):
        r, c = int(rng.integers(T.PUZZLE_ROWS)), int(rng.integers(T.PUZZLE_COLS))
        k = int(rng.integers(4))
        img = shoot(rng, r, c, int(rng.integers(*ppc_range)), 90 * k + rng.uniform(-35, 35),
                    tilt=rng.uniform(0, 0.08), blur=rng.uniform(0, 1.2), noise=rng.uniform(0, 8),
                    finger=bool(rng.random() < finger), background=background)
        d = decide(img, table)
        if isinstance(d, Reject):
            rejected += 1
        elif (d.row, d.col) == (r, c):
            correct += 1
            turn_wrong += d.turn != k
        else:
            wrong += 1
    return correct, rejected, wrong, turn_wrong


def test_reads_pieces_on_the_mat(table):
    correct, rejected, wrong, turn_wrong = run(table, 150, seed=1)
    assert wrong == 0 and turn_wrong == 0 and rejected <= 3, (correct, rejected, wrong, turn_wrong)


def test_fingers_cause_rejections_not_errors(table):
    correct, rejected, wrong, turn_wrong = run(table, 60, seed=2, finger=1.0)
    assert wrong == 0 and turn_wrong == 0 and correct >= 40, (correct, rejected, wrong)


def test_small_cells(table):
    correct, rejected, wrong, _ = run(table, 40, seed=3, ppc_range=(9, 11))
    assert wrong == 0 and rejected <= 2, (correct, rejected, wrong)


def test_turn_convention(table):
    rng = np.random.default_rng(4)
    for k in range(4):
        d = decide(shoot(rng, 2, 3, 18, 90 * k, light=0), table)
        assert d == Read(2, 3, k)


def test_without_the_mat_it_rejects(table):
    _, rejected, wrong, _ = run(table, 30, seed=5, background="clutter")
    assert wrong == 0 and rejected == 30


def test_blank_and_picture_frames_are_rejected(table):
    assert isinstance(decide(np.full((480, 640, 3), (70, 150, 60), np.uint8), table), Reject)
    rng = np.random.default_rng(6)
    noise = rng.integers(0, 256, (480, 640, 3)).astype(np.uint8)
    assert isinstance(decide(noise, table), Reject)


def test_undistort_round_trip():
    K = np.array([[600, 0, 320], [0, 600, 240], [0, 0, 1]], float)
    D = np.array([-0.2, 0.05, 0, 0, 0], float)
    img = np.zeros((480, 640, 3), np.uint8)
    cv2.rectangle(img, (200, 150), (440, 330), (255, 255, 255), 3)
    mapx, mapy = cv2.initUndistortRectifyMap(K, -D, None, K, (640, 480), cv2.CV_32FC1)
    distorted = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
    back = undistort(distorted, K, D)
    assert np.abs(back.astype(int) - img.astype(int))[100:380, 150:490].mean() < 20
