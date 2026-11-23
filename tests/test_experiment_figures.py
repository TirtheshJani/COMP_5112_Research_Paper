"""make_figures: three files appear, PDFs are non-empty, one summary paragraph per prediction with the given counts."""
import csv
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "make_figures.py"
HEAD = ["experiment", "pattern", "decoder", "arm", "px_per_cell", "tilt", "blur", "noise", "finger", "n", "correct",
        "rejected", "wrong", "wrong_le1_misread", "reads_le1_misread", "mean_misread_cells", "seed", "commit"]


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEAD)
        w.writeheader()
        for r in rows:
            w.writerow({**dict.fromkeys(HEAD, ""), "seed": 1, "commit": "x", "mean_misread_cells": 0.0, **r})


def test_make_figures(tmp_path):
    spec = importlib.util.spec_from_file_location("make_figures", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    puzzle = []
    for px in (8, 12):
        for finger in (0, 1):
            for pat in ("strong", "orient"):
                for dec in ("single", "grid"):
                    puzzle.append(dict(experiment="puzzle", pattern=pat, decoder=dec, px_per_cell=px, tilt=0.06, blur=1.0,
                                       noise=4, finger=finger, n=100, correct=90, rejected=9, wrong=1 if pat == "orient" else 0,
                                       wrong_le1_misread=0, reads_le1_misread=100))
    dense = [
        dict(experiment="dense", pattern="strong", decoder="single", arm="forced1", n=50, correct=0, rejected=50, wrong=0,
             wrong_le1_misread=0, reads_le1_misread=50),
        dict(experiment="dense", pattern="orient", decoder="single", arm="forced1", n=50, correct=0, rejected=40, wrong=10,
             wrong_le1_misread=10, reads_le1_misread=50),
    ]
    for p in (0.01, 0.1):
        for pat in ("strong", "orient"):
            dense.append(dict(experiment="dense", pattern=pat, decoder="single", arm="noise", noise=p, n=50, correct=30,
                              rejected=15, wrong=5, wrong_le1_misread=0, reads_le1_misread=40))
    write(tmp_path / "p.csv", puzzle)
    write(tmp_path / "d.csv", dense)
    out = tmp_path / "out"
    assert mod.main(["--puzzle", str(tmp_path / "p.csv"), "--dense", str(tmp_path / "d.csv"), "--out-dir", str(out)]) == 0
    for name in ("fig_puzzle.pdf", "fig_dense.pdf", "sim_summary.md"):
        assert (out / name).stat().st_size > 0
    for name in ("fig_puzzle.pdf", "fig_dense.pdf"):
        assert (out / name).read_bytes().startswith(b"%PDF")
    text = (out / "sim_summary.md").read_text(encoding="utf-8")
    paras = [p for p in text.split("\n\n") if p.startswith("Prediction")]
    assert len(paras) == 3
    assert "0 of 400" in paras[0]          # puzzle strong, single: 2 px x 2 finger x 100 reads
    assert "0 of 80" in paras[0]           # dense noise strong: 2 levels x 40 reads
    assert "10 of 50" in paras[1] and "0 of 50" in paras[1] and "untested" in paras[1]
    assert "4 of 400" in paras[2]          # orient wrong over the sweep, per decoder
    assert chr(0x2014) not in text and chr(0x2013) not in text
