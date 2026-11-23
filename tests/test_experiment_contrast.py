"""contrast.run_dense: the 6 x 6 tori at the cell level, u = 3, decode_single (S2 E5)."""
import numpy as np
import pytest

from jigsaw.experiment.contrast import run_dense
from jigsaw.experiment.runner import COLUMNS


def by_pattern(rows):
    return {r["pattern"]: r for r in rows}


@pytest.fixture(scope="module")
def forced():
    return by_pattern(run_dense("forced1", (), 2000, seed=11))


def test_forced1_rows(forced):
    assert set(forced) == {"strong", "orient"}
    for r in forced.values():
        assert list(r) == COLUMNS[:-1]
        assert (r["experiment"], r["decoder"], r["arm"], r["seed"], r["n"]) == ("dense", "single", "forced1", 11, 2000)
        assert r["correct"] + r["rejected"] + r["wrong"] == 2000


def test_forced1_has_exactly_one_misread_cell_per_read(forced):
    for r in forced.values():
        assert r["mean_misread_cells"] == 1.0 and r["reads_le1_misread"] == 2000
        assert r["wrong_le1_misread"] == r["wrong"]


def test_forced1_on_strong_is_never_wrong(forced):
    assert forced["strong"]["wrong"] == 0 and forced["strong"]["correct"] == 0


def test_forced1_can_be_wrong_on_the_control(forced):
    assert forced["orient"]["wrong"] > 0          # the control torus has distance-1 pairs


def test_noise_arm_levels_and_counts():
    rows = run_dense("noise", (0.0, 0.05, 0.2), 300, seed=4)
    assert [(r["pattern"], r["noise"]) for r in rows] == [
        ("strong", 0.0), ("orient", 0.0), ("strong", 0.05), ("orient", 0.05), ("strong", 0.2), ("orient", 0.2)]
    for r in rows:
        assert r["arm"] == "noise" and r["correct"] + r["rejected"] + r["wrong"] == 300
        assert 0 <= r["wrong_le1_misread"] <= r["wrong"] and r["reads_le1_misread"] <= 300
    clean = [r for r in rows if r["noise"] == 0.0]
    assert all(r["correct"] == 300 and r["mean_misread_cells"] == 0.0 for r in clean)
    assert all(r["wrong_le1_misread"] == 0 for r in rows if r["pattern"] == "strong")


def test_patterns_share_the_flips():
    rows = by_pattern(run_dense("noise", (0.1,), 500, seed=9))
    assert rows["strong"]["mean_misread_cells"] == rows["orient"]["mean_misread_cells"]


def test_same_seed_identical_and_parallel_equals_serial():
    a = run_dense("noise", (0.02, 0.1), 200, seed=5)
    assert a == run_dense("noise", (0.02, 0.1), 200, seed=5)
    assert a == run_dense("noise", (0.02, 0.1), 200, seed=5, workers=2)
    assert a[2:] == run_dense("noise", (0.1,), 200, seed=5)


def test_a_strong_contradiction_saves_the_cells_and_stops(monkeypatch, tmp_path):
    from jigsaw.experiment import contrast
    from jigsaw.experiment.runner import Contradiction
    from jigsaw.types import Position
    monkeypatch.setattr(contrast, "decode_single", lambda window, table: Position(5, 5, 3))   # synthetic wrong decoder
    with pytest.raises(Contradiction) as e:
        run_dense("forced1", (), 5, seed=1, findings_dir=tmp_path)
    assert [r["pattern"] for r in e.value.rows] == ["strong"]
    files = list(tmp_path.glob("dense_strong_forced1_*.npz"))
    assert files and not list(tmp_path.glob("*.png"))
    z = np.load(files[0])
    assert {"seen", "truth_window", "flips", "truth", "decision"} <= set(z.files)
