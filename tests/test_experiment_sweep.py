"""sweep.run_puzzle: rendered puzzle rows (S2 E2, E3, E8, E11)."""
import csv
import logging

import numpy as np
import pytest

from jigsaw.experiment.runner import COLUMNS, write_csv
from jigsaw.experiment.sweep import full_conditions, run_puzzle

BASE = {"px_per_cell": 16, "tilt": 0.06, "blur": 1.0, "noise": 4, "finger": 0}


def test_full_conditions_is_the_cross_of_the_levels():
    conds = full_conditions()
    assert len(conds) == 6 * 3 * 2 * 2 * 1
    assert len({tuple(sorted(c.items())) for c in conds}) == len(conds)
    assert {c["px_per_cell"] for c in conds} == {8, 10, 12, 16, 22, 28}
    assert {c["blur"] for c in conds} == {0.5, 1.0, 1.5}
    assert {c["noise"] for c in conds} == {4, 8}
    assert {c["finger"] for c in conds} == {0, 1}
    assert {c["tilt"] for c in conds} == {0.06}
    assert BASE in conds


@pytest.fixture(scope="module")
def rows50():
    return run_puzzle([BASE], 50, seed=7)


def test_one_row_per_pattern_and_decoder(rows50):
    assert sorted((r["pattern"], r["decoder"]) for r in rows50) == [
        ("orient", "grid"), ("orient", "single"), ("strong", "grid"), ("strong", "single")]
    for r in rows50:
        assert list(r) == COLUMNS[:-1]
        assert r["experiment"] == "puzzle" and r["seed"] == 7 and r["n"] == 50
        assert {k: r[k] for k in BASE} == BASE


def test_counts_sum_to_n(rows50):
    for r in rows50:
        assert r["correct"] + r["rejected"] + r["wrong"] == 50
        assert 0 <= r["wrong_le1_misread"] <= r["wrong"]
        assert 0 <= r["reads_le1_misread"] <= 50


def test_both_decoders_see_the_same_reads(rows50):
    for pattern in ("strong", "orient"):
        single, grid = (next(r for r in rows50 if r["pattern"] == pattern and r["decoder"] == d) for d in ("single", "grid"))
        assert single["mean_misread_cells"] == grid["mean_misread_cells"]
        assert single["reads_le1_misread"] == grid["reads_le1_misread"]


def test_truth_convention_gives_mostly_correct_reads_at_the_baseline(rows50):
    for r in rows50:
        assert r["correct"] >= 40, r


SMALL = [dict(BASE, px_per_cell=8), dict(BASE, noise=8, finger=1)]


def test_same_seed_gives_identical_rows():
    assert run_puzzle(SMALL, 4, seed=3) == run_puzzle(SMALL, 4, seed=3)


def test_adding_a_condition_does_not_change_the_others():
    assert run_puzzle(SMALL[1:], 4, seed=3) == run_puzzle(SMALL, 4, seed=3)[4:]


def test_parallel_equals_serial():
    assert run_puzzle(SMALL, 4, seed=5, workers=2) == run_puzzle(SMALL, 4, seed=5, workers=1)


def test_write_csv_ends_with_seed_and_commit(tmp_path, rows50):
    out = tmp_path / "sub" / "sim.csv"
    write_csv(out, rows50, "abc123")
    with open(out, newline="") as f:
        got = list(csv.reader(f))
    assert got[0] == COLUMNS and COLUMNS[-2:] == ["seed", "commit"]
    assert len(got) == 1 + len(rows50) and all(line[-2:] == ["7", "abc123"] for line in got[1:])


def test_a_strong_contradiction_saves_the_frame_and_stops(monkeypatch, tmp_path):
    from jigsaw.experiment import sweep
    from jigsaw.experiment.runner import Contradiction
    from jigsaw.types import Read
    monkeypatch.setattr(sweep, "decode_grid", lambda cells, mask, table: Read(6, 4, 3))   # a synthetic wrong decoder
    with pytest.raises(Contradiction) as e:
        sweep.run_puzzle([BASE], 3, seed=7, findings_dir=tmp_path)
    assert {(r["pattern"], r["decoder"]) for r in e.value.rows} == {("strong", "grid")}
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names and all(n.startswith("puzzle_strong_grid_") for n in names)
    assert {n.rsplit(".", 1)[1] for n in names} == {"npz", "png"}
    z = np.load(next(tmp_path.glob("*.npz")))
    assert {"cells", "mask", "H", "M", "truth", "decision", "misread"} <= set(z.files)


@pytest.fixture
def one_flip_unprinted(monkeypatch):
    """Truth rasters with the printed cell under the raster centre inverted (a hand-built single misread) and no
    printed bit in the left third (visible cells there are unknown, as if they fell off the grid)."""
    from jigsaw import types as T
    from jigsaw.experiment import sweep
    from jigsaw.experiment.runner import OFF_GRID, truth_raster
    rows, cols = np.mgrid[: T.GRID_ROWS, : T.GRID_COLS]
    real = sweep.piece

    def piece(r, c, px, name):
        gray, alpha, truth = real(r, c, px, name)
        h, w = truth.shape
        a, b = (truth_raster(r, c, px, truth.shape, grid=g) for g in (rows, cols))   # G row and col per pixel
        truth = truth.copy()
        truth[(a == a[h // 2, w // 2]) & (b == b[h // 2, w // 2])] ^= 1
        truth[:, : w // 3] = OFF_GRID
        return gray, alpha, truth

    monkeypatch.setattr(sweep, "piece", piece)


def test_a_wrong_read_with_one_misread_beside_unprinted_cells_trips_e9(one_flip_unprinted, monkeypatch, tmp_path):
    from jigsaw.experiment import sweep
    from jigsaw.experiment.runner import Contradiction
    from jigsaw.types import Read
    monkeypatch.setattr(sweep, "decode_grid", lambda cells, mask, table: Read(6, 4, 3))   # a synthetic wrong decoder
    with pytest.raises(Contradiction):
        sweep.run_puzzle([BASE], 3, seed=7, findings_dir=tmp_path)
    found = []
    for p in tmp_path.glob("*.npz"):
        with np.load(p) as z:
            found.append((int(z["misread"]), int(z["unknown"])))
    assert found and all(m == 1 and u > 0 for m, u in found), found


def test_unprinted_cells_are_logged_and_not_counted(one_flip_unprinted, caplog):
    from jigsaw.experiment import sweep
    with caplog.at_level(logging.WARNING, logger="jigsaw.experiment.sweep"):
        rows = sweep.run_puzzle([BASE], 3, seed=7)
    assert all(r["mean_misread_cells"] == 1.0 for r in rows), rows
    assert "no printed bit" in caplog.text


def test_strong_and_orient_see_the_same_trials(monkeypatch):
    """Patterns share one stream: same (r, c), angle (so turn) and generator state after every photograph."""
    from jigsaw.experiment import sweep
    log = []
    real_piece, real_photograph = sweep.piece, sweep.photograph

    def piece(r, c, px, name):
        log.append([name, r, c])
        return real_piece(r, c, px, name)

    def photograph(gray, alpha, rng, angle, **kw):
        out = real_photograph(gray, alpha, rng, angle, **kw)
        log[-1] += [angle, rng.bit_generator.state]
        return out

    monkeypatch.setattr(sweep, "piece", piece)
    monkeypatch.setattr(sweep, "photograph", photograph)
    sweep.run_puzzle([dict(BASE, noise=8, finger=1)], 6, seed=2)
    strong, orient = ([e[1:] for e in log if e[0] == name] for name in ("strong", "orient"))
    assert len(strong) == len(orient) == 6 and strong == orient


def test_no_findings_saved_for_the_control(monkeypatch, tmp_path):
    from jigsaw.experiment import sweep
    from jigsaw.types import Read
    monkeypatch.setattr(sweep, "PATTERN_NAMES", ("orient",))
    monkeypatch.setattr(sweep, "decode_grid", lambda cells, mask, table: Read(6, 4, 3))
    rows = sweep.run_puzzle([BASE], 3, seed=7, findings_dir=tmp_path)
    assert any(r["wrong_le1_misread"] > 0 for r in rows) and not list(tmp_path.iterdir())
