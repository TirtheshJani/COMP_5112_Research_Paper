"""runner: classification, the single-window decoder and misread counting (S2 E1, E4)."""
import numpy as np
import pytest

from jigsaw.decode import build_table, decode_grid
from jigsaw.experiment.runner import (
    OFF_GRID,
    Contradiction,
    classify,
    decide_single,
    misread_cells,
    run_units,
    save_finding,
    truth_raster,
)
from jigsaw.geometry import visible_cells
from jigsaw.patch import back_grid
from jigsaw.render import LINE_GRAY, photograph, piece_back
from jigsaw.types import GridRead, Read, Reject


@pytest.fixture(scope="module")
def G():
    return back_grid()


@pytest.fixture(scope="module")
def table(G):
    return build_table(G)


def seen_grid(G, r, c, k):
    """GridRead of piece (r, c) as a perfect camera would see it, turned k quarter turns."""
    vis = visible_cells(r, c)
    a, b = np.nonzero(vis)
    sl = slice(a.min(), a.max() + 1), slice(b.min(), b.max() + 1)
    return GridRead(np.rot90(G[sl], k).copy(), np.rot90(vis[sl], k).copy(), np.eye(3))


def top_left_start(mask, u=5):
    h, w = mask.shape
    return next((y, x) for y in range(h - u + 1) for x in range(w - u + 1) if mask[y:y + u, x:x + u].all())


# classify ---------------------------------------------------------------------------------------

def test_classify_correct():
    assert classify(Read(3, 1, 2), Read(3, 1, 2)) == "correct"


def test_classify_rejected():
    assert classify(Read(3, 1, 2), Reject("no_match")) == "rejected"


def test_classify_wrong_piece():
    assert classify(Read(3, 1, 2), Read(3, 2, 2)) == "wrong"


def test_classify_right_piece_wrong_turn_is_wrong():
    assert classify(Read(3, 1, 2), Read(3, 1, 1)) == "wrong"


# decide_single ----------------------------------------------------------------------------------

@pytest.mark.parametrize("r,c,k", [(0, 0, 0), (5, 1, 1), (3, 4, 2), (6, 2, 3)])
def test_decide_single_matches_decode_grid_on_a_clean_read(G, table, r, c, k):
    gr = seen_grid(G, r, c, k)
    assert decide_single(gr, table) == decode_grid(gr.cells, gr.mask, table) == Read(r, c, k)


def test_decide_single_ignores_cells_outside_the_top_left_window(G, table):
    gr = seen_grid(G, 5, 1, 1)
    y, x = top_left_start(gr.mask)
    cells = gr.cells.copy()
    ys, xs = np.nonzero(gr.mask)
    far = np.argmax(ys + xs)                       # a visible cell far from the top-left window
    assert not (y <= ys[far] < y + 5 and x <= xs[far] < x + 5)
    cells[ys[far], xs[far]] ^= 1
    assert decide_single(GridRead(cells, gr.mask, gr.H), table) == Read(5, 1, 1)


def test_decide_single_rejects_a_flip_in_its_window_on_strong(G, table):
    gr = seen_grid(G, 5, 1, 1)
    y, x = top_left_start(gr.mask)
    cells = gr.cells.copy()
    cells[y + 2, x + 2] ^= 1
    assert decide_single(GridRead(cells, gr.mask, gr.H), table) == Reject("no_match")


def test_decide_single_has_no_agreement_check(G, table):
    k = 1
    gr = seen_grid(G, 5, 1, k)
    y, x = top_left_start(gr.mask)
    cells = gr.cells.copy()
    cells[y:y + 5, x:x + 5] = np.rot90(G[20:25, 20:25], k)    # a valid window from elsewhere in G
    gr2 = GridRead(cells, gr.mask, gr.H)
    d = decide_single(gr2, table)
    assert isinstance(d, Read) and (d.row, d.col) != (5, 1)
    # every window overlaps the pasted one on this piece, so decode_grid fails its agreement test (min_agree)
    assert isinstance(decode_grid(gr2.cells, gr2.mask, table), Reject)


def test_decide_single_without_a_complete_window(table):
    gr = GridRead(np.zeros((4, 4), np.uint8), np.ones((4, 4), bool), np.eye(3))
    assert decide_single(gr, table) == Reject("no_window")


# truth_raster and misread_cells ------------------------------------------------------------------

@pytest.mark.parametrize("r,c,ppc", [(5, 1, 16), (0, 4, 8), (3, 2, 11)])
def test_truth_raster_agrees_with_the_drawing(G, r, c, ppc):
    gray, _ = piece_back(r, c, ppc)
    truth = truth_raster(r, c, ppc, gray.shape)
    cell = gray != LINE_GRAY                       # grid-line pixels carry no cell colour
    assert truth.shape == gray.shape
    assert np.array_equal(truth[cell] == 1, gray[cell] == 0)


def test_truth_raster_with_a_control_grid():
    rng = np.random.default_rng(0)
    ctrl = rng.integers(0, 2, (72, 52)).astype(np.uint8)
    gray, _ = piece_back(2, 2, 12, grid=ctrl)
    truth = truth_raster(2, 2, 12, gray.shape, grid=ctrl)
    cell = gray != LINE_GRAY
    assert np.array_equal(truth[cell] == 1, gray[cell] == 0)


@pytest.fixture(scope="module")
def clean_shot():
    rng = np.random.default_rng(3)
    gray, alpha = piece_back(5, 1, 16)
    img, M = photograph(gray, alpha, rng, 90 + 12, return_transform=True)
    from jigsaw.vision import read_grid
    gr = read_grid(img)
    assert isinstance(gr, GridRead)
    return gr, M, truth_raster(5, 1, 16, gray.shape)


def test_misread_cells_is_zero_on_a_clean_read(clean_shot):
    gr, M, truth = clean_shot
    assert gr.mask.sum() >= 25
    assert misread_cells(gr, M, truth) == (0, 0)


def test_misread_cells_counts_a_known_flip(clean_shot):
    gr, M, truth = clean_shot
    ys, xs = np.nonzero(gr.mask)
    cells = gr.cells.copy()
    cells[ys[7], xs[7]] ^= 1
    assert misread_cells(GridRead(cells, gr.mask, gr.H), M, truth) == (1, 0)
    cells[ys[20], xs[20]] ^= 1
    assert misread_cells(GridRead(cells, gr.mask, gr.H), M, truth) == (2, 0)


def test_misread_cells_ignores_cells_outside_the_mask(clean_shot):
    gr, M, truth = clean_shot
    ys, xs = np.nonzero(~gr.mask)
    cells = gr.cells.copy()
    cells[ys, xs] ^= 1
    assert misread_cells(GridRead(cells, gr.mask, gr.H), M, truth) == (0, 0)


def test_misread_cells_counts_cells_off_the_raster_as_unknown_not_misread(clean_shot):
    gr, M, truth = clean_shot
    shift = np.array([[1, 0, 5000], [0, 1, 0], [0, 0, 1]], float)   # every centre lands far outside
    assert misread_cells(GridRead(gr.cells, gr.mask, shift @ gr.H), M, truth) == (0, int(gr.mask.sum()))


def test_a_single_flip_counts_one_misread_beside_unprinted_cells(clean_shot):
    """Left third of the raster has no printed bit. Flipping a cell there changes nothing; flipping any other
    visible cell gives exactly one misread. Unprinted cells must never push a single flip out of the <= 1 bucket."""
    gr, M, truth = clean_shot
    part = truth.copy()
    part[:, : part.shape[1] // 3] = OFF_GRID
    misread, unknown = misread_cells(gr, M, part)
    assert misread == 0 and 0 < unknown < gr.mask.sum()
    ys, xs = np.nonzero(gr.mask)
    got = []
    for y, x in zip(ys, xs):
        cells = gr.cells.copy()
        cells[y, x] ^= 1
        got.append(misread_cells(GridRead(cells, gr.mask, gr.H), M, part))
    assert got.count((0, unknown)) == unknown
    assert got.count((1, unknown)) == len(ys) - unknown


# run_units and E9 --------------------------------------------------------------------------------

def fake_unit(pattern, wrong_le1):
    return [{"pattern": pattern, "decoder": "single", "wrong_le1_misread": wrong_le1}]


@pytest.mark.parametrize("workers", [1, 2])
def test_run_units_keeps_order(workers):
    rows = run_units(fake_unit, [("strong", 0), ("orient", 3), ("strong", 0)], workers)
    assert [(r["pattern"], r["wrong_le1_misread"]) for r in rows] == [("strong", 0), ("orient", 3), ("strong", 0)]


@pytest.mark.parametrize("workers", [1, 2])
def test_run_units_stops_on_a_strong_contradiction(workers):
    with pytest.raises(Contradiction) as e:
        run_units(fake_unit, [("orient", 2), ("strong", 1), ("strong", 0)], workers)
    assert [r["pattern"] for r in e.value.rows] == ["strong"]


def test_save_finding_writes_frame_and_cells(tmp_path):
    img = np.zeros((20, 30, 3), np.uint8)
    paths = save_finding(tmp_path / "findings", "puzzle_strong_single_trial3", image=img,
                         cells=np.ones((4, 4), np.uint8), truth=[1, 2, 3])
    names = sorted(p.name for p in paths)
    assert names == ["puzzle_strong_single_trial3.npz", "puzzle_strong_single_trial3.png"]
    z = np.load(tmp_path / "findings" / "puzzle_strong_single_trial3.npz")
    assert z["cells"].shape == (4, 4) and list(z["truth"]) == [1, 2, 3] and "image" not in z


def test_save_finding_without_a_frame(tmp_path):
    paths = save_finding(tmp_path, "dense_strong", cells=np.zeros((3, 3), np.uint8))
    assert [p.suffix for p in paths] == [".npz"]
