import cv2
import numpy as np

from jigsaw.render import photograph, piece_back


def test_piece_back_size_and_outline():
    gray, alpha = piece_back(3, 2, 20)
    # piece core is 10 cells = 200 px; knobs and the 2-cell margin make the image larger
    assert 200 < gray.shape[0] < 400 and 200 < gray.shape[1] < 400
    area_cells = (alpha > 127).sum() / 20 ** 2
    assert 90 < area_cells < 115          # a jigsaw piece is about one core square in area
    assert set(np.unique(gray)) <= {0, 140, 255}


def test_photograph_turns_counter_clockwise():
    # an arrow-like test card: dark block in the top-left corner
    g = np.full((100, 100), 255, np.uint8)
    g[:30, :30] = 0
    a = np.full((100, 100), 255, np.uint8)
    rng = np.random.default_rng(0)
    img = photograph(g, a, rng, 90, size=(400, 400), background="plain", light=0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ys, xs = np.nonzero(gray < 40)
    piece_ys, piece_xs = np.nonzero(gray > 200)
    # a quarter turn counter-clockwise moves the top-left corner to the bottom-left
    assert ys.mean() > piece_ys.mean() and xs.mean() < piece_xs.mean()


def test_control_grid_and_transform():
    from pathlib import Path

    from jigsaw.patch import load_torus
    ctrl = load_torus(Path(__file__).parent.parent / "data" / "patterns" / "orient_u5_256.npz")[:72, :52]
    g1, _ = piece_back(2, 2, 12)
    g2, a2 = piece_back(2, 2, 12, grid=ctrl)
    assert g1.shape == g2.shape and (g1 != g2).any()
    img, M = photograph(g2, a2, np.random.default_rng(0), 30, return_transform=True)
    assert img.shape == (720, 720, 3) and M.shape == (3, 3)
    # a point mapped through M lands on the same grey value in the frame: dark and light patches of g2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inside = np.nonzero(a2[8:-8, 8:-8] > 127)
    seen = {0: [], 255: []}
    for y, x in zip(inside[0][::37] + 8, inside[1][::37] + 8):
        if g2[y, x] in seen and (g2[y - 4:y + 5, x - 4:x + 5] == g2[y, x]).all():
            u, v, w = M @ (x, y, 1)
            seen[int(g2[y, x])].append(gray[int(round(v / w)), int(round(u / w))])
    assert len(seen[0]) > 5 and len(seen[255]) > 5
    assert np.median(seen[0]) < 90 and np.median(seen[255]) > 170


def test_finger_on_an_empty_piece_does_not_raise():
    g = np.full((20, 20), 255, np.uint8)
    img = photograph(g, np.zeros((20, 20), np.uint8), np.random.default_rng(0), 10, scale=1e-4, finger=True)
    assert img.shape == (720, 720, 3)
