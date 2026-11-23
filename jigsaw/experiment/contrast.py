"""Dense tori experiment at the cell level, no rendering (S2 E5).

The two 6 x 6 tori (u = 3, windows wrap). One trial: a random window position (i, j) and turn k, the
camera's view np.rot90(window, k), then
  arm forced1: exactly one uniformly chosen cell flipped;
  arm noise:   each cell flipped independently with probability p (the level, written in the noise column);
and decode.decode_single on that one window. A read is correct only at (i, j) with turn k.

Seeding as in sweep: one SeedSequence(seed, spawn_key=(arm, level)) per condition, shared by both patterns,
so the two patterns see the same positions, turns and flips.
"""
from functools import lru_cache

import numpy as np

from jigsaw.decode import build_table, decode_single
from jigsaw.experiment.runner import classify, run_units, save_finding
from jigsaw.patch import PATTERNS, load_torus
from jigsaw.types import Position, Read

U = 3
TORI = {"strong": "strong_u3_6x6.txt", "orient": "orient_u3_6x6.txt"}
ARMS = {"forced1": 1, "noise": 2}


@lru_cache(maxsize=None)
def torus(name: str) -> np.ndarray:
    return load_torus(PATTERNS / TORI[name])


@lru_cache(maxsize=None)
def torus_table(name: str):
    return build_table(torus(name), u=U, wrap=True)


def dense_unit(arm: str, name: str, level, n: int, seed: int, findings_dir=None) -> list[dict]:
    """n trials of one arm, level and pattern; one row. E9 findings on strong go to findings_dir."""
    pat, table = torus(name), torus_table(name)
    R, C = pat.shape
    key = (ARMS[arm], int(round(1e6 * float(level))) if level != "" else 0)
    rng = np.random.default_rng(np.random.SeedSequence(seed, spawn_key=key))
    counts = {"correct": 0, "rejected": 0, "wrong": 0, "wrong_le1_misread": 0}
    misreads = []
    for t in range(n):
        i, j, k = int(rng.integers(R)), int(rng.integers(C)), int(rng.integers(4))
        window = pat.take(range(i, i + U), 0, mode="wrap").take(range(j, j + U), 1, mode="wrap")
        seen = np.rot90(window, k)
        if arm == "forced1":
            flips = np.zeros(U * U, bool)
            flips[rng.integers(U * U)] = True
        else:
            flips = rng.random(U * U) < float(level)
        seen = seen ^ flips.reshape(U, U).astype(np.uint8)
        m = int(flips.sum())
        misreads.append(m)
        d = decode_single(seen, table)
        decision = Read(d.i, d.j, d.turn) if isinstance(d, Position) else d
        kind = classify(Read(i, j, k), decision)
        counts[kind] += 1
        if kind == "wrong" and m <= 1:
            counts["wrong_le1_misread"] += 1
            if name == "strong" and findings_dir is not None:
                save_finding(findings_dir, f"dense_{name}_{arm}_p{level}_seed{seed}_trial{t}", seen=seen,
                             truth_window=window, flips=flips.reshape(U, U), truth=[i, j, k], decision=repr(decision))
    return [{"experiment": "dense", "pattern": name, "decoder": "single", "arm": arm, "px_per_cell": "", "tilt": "",
             "blur": "", "noise": level, "finger": "", "n": n, **counts,
             "reads_le1_misread": sum(m <= 1 for m in misreads),
             "mean_misread_cells": round(float(np.mean(misreads)), 6), "seed": seed}]


def run_dense(arm: str, levels, n: int, seed: int, workers: int = 1, findings_dir=None) -> list[dict]:
    """One row per level and pattern. levels: flip probabilities for arm noise; arm forced1 ignores them.

    Raises runner.Contradiction on E9 after saving the offending cells to findings_dir.
    """
    if arm not in ARMS:
        raise ValueError(arm)
    levels = [""] if arm == "forced1" else list(levels)
    args = [(arm, name, level, n, seed, findings_dir) for level in levels for name in TORI]
    return run_units(dense_unit, args, workers)
