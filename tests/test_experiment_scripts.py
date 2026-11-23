"""The experiment scripts: provenance (E8)."""
import csv
import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def puzzle(monkeypatch):
    mod = load("run_sim_puzzle")
    monkeypatch.setattr(mod, "git_commit", lambda: "c0ffee")
    monkeypatch.setattr(mod, "full_conditions",
                        lambda: [{"px_per_cell": 12, "tilt": 0.06, "blur": 1.0, "noise": 4, "finger": 0}])
    return mod


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def test_puzzle_script_refuses_a_dirty_tree(puzzle, monkeypatch, tmp_path):
    monkeypatch.setattr(puzzle, "tree_is_dirty", lambda: True)
    out = tmp_path / "p.csv"
    assert puzzle.main(["--seed", "1", "--n", "2", "--out", str(out), "--workers", "1"]) != 0
    assert not out.exists()


def test_puzzle_script_runs_dirty_with_allow_dirty(puzzle, monkeypatch, tmp_path):
    monkeypatch.setattr(puzzle, "tree_is_dirty", lambda: True)
    out = tmp_path / "p.csv"
    assert puzzle.main(["--seed", "1", "--n", "2", "--out", str(out), "--workers", "1", "--allow-dirty"]) == 0
    rows = read_rows(out)
    assert len(rows) == 4 and all(r["seed"] == "1" and r["commit"] == "c0ffee-dirty" for r in rows)


def test_puzzle_script_on_a_clean_tree(puzzle, monkeypatch, tmp_path):
    monkeypatch.setattr(puzzle, "tree_is_dirty", lambda: False)
    out = tmp_path / "p.csv"
    assert puzzle.main(["--seed", "2", "--n", "2", "--out", str(out), "--workers", "1"]) == 0
    assert all(r["commit"] == "c0ffee" and int(r["n"]) == 2 for r in read_rows(out))


@pytest.fixture
def dense(monkeypatch):
    mod = load("run_sim_dense")
    monkeypatch.setattr(mod, "git_commit", lambda: "c0ffee")
    return mod


def test_dense_script_refuses_a_dirty_tree(dense, monkeypatch, tmp_path):
    monkeypatch.setattr(dense, "tree_is_dirty", lambda: True)
    out = tmp_path / "d.csv"
    assert dense.main(["--seed", "1", "--n", "5", "--out", str(out)]) != 0
    assert not out.exists()


def test_dense_script_writes_both_arms(dense, monkeypatch, tmp_path):
    monkeypatch.setattr(dense, "tree_is_dirty", lambda: False)
    out = tmp_path / "d.csv"
    assert dense.main(["--seed", "3", "--n", "20", "--out", str(out), "--levels", "0.05", "0.1"]) == 0
    rows = read_rows(out)
    assert [(r["arm"], r["pattern"], r["noise"]) for r in rows] == [
        ("forced1", "strong", ""), ("forced1", "orient", ""),
        ("noise", "strong", "0.05"), ("noise", "orient", "0.05"), ("noise", "strong", "0.1"), ("noise", "orient", "0.1")]
    assert all(r["seed"] == "3" and r["commit"] == "c0ffee" and r["n"] == "20" for r in rows)
