"""Rendered puzzle experiment (S2 E2, E3, E11).

One trial: a random piece (r, c) and turn k, the piece back rendered with render.piece_back(grid=pattern),
photographed at angle 90 k + U(-35, 35) degrees (as in the S1 vision tests, so the true turn is k), read once
with vision.read_grid, and decided by both decoders on the same GridRead (paired, E3).

Seeding (E11): each condition gets its own numpy SeedSequence(seed, spawn_key=condition), so serial and
parallel runs agree and adding a condition leaves the others unchanged. Both patterns of a condition use the
same stream, so they see the same pieces, turns, perspective, noise and finger placement.
"""
import itertools
import logging
from functools import lru_cache

import numpy as np

from jigsaw import types as T
from jigsaw.decode import build_table, decode_grid
from jigsaw.experiment.runner import FINDINGS_DIR, classify, decide_single, misread_cells, run_units, save_finding, truth_raster
from jigsaw.patch import PATTERNS, back_grid, load_torus
from jigsaw.render import photograph, piece_back
from jigsaw.types import GridRead, Read
from jigsaw.vision import read_grid

PATTERN_NAMES = ("strong", "orient")
DECODERS = ("single", "grid")
LEVELS = {"px_per_cell": (8, 10, 12, 16, 22, 28), "tilt": (0.06,), "blur": (0.5, 1.0, 1.5), "noise": (4, 8),
          "finger": (0, 1)}
JITTER_DEG = 35
log = logging.getLogger(__name__)


def full_conditions() -> list[dict]:
    keys = list(LEVELS)
    return [dict(zip(keys, v)) for v in itertools.product(*(LEVELS[k] for k in keys))]


def condition_rng(seed: int, cond: dict) -> np.random.Generator:
    key = tuple(int(round(1000 * float(cond[k]))) for k in LEVELS)
    return np.random.default_rng(np.random.SeedSequence(seed, spawn_key=key))


@lru_cache(maxsize=None)
def pattern_grid(name: str) -> np.ndarray:
    if name == "strong":
        return back_grid()
    if name == "orient":
        return load_torus(PATTERNS / "orient_u5_256.npz")[: T.GRID_ROWS, : T.GRID_COLS].copy()
    raise ValueError(name)


@lru_cache(maxsize=None)
def pattern_table(name: str):
    return build_table(pattern_grid(name))


@lru_cache(maxsize=2 * T.PUZZLE_ROWS * T.PUZZLE_COLS)
def piece(r: int, c: int, px_per_cell: int, name: str):
    gray, alpha = piece_back(r, c, px_per_cell, grid=pattern_grid(name))
    return gray, alpha, truth_raster(r, c, px_per_cell, gray.shape, grid=pattern_grid(name))


def puzzle_unit(cond: dict, name: str, n: int, seed: int, findings_dir=FINDINGS_DIR) -> list[dict]:
    """n trials of one pattern under one condition; one row per decoder.

    E9: a wrong read with at most one misread cell on the strong pattern saves the frame and the cells to
    findings_dir (default results/findings); run_units then stops the run.
    """
    rng = condition_rng(seed, cond)
    table = pattern_table(name)
    counts = {d: {"correct": 0, "rejected": 0, "wrong": 0, "wrong_le1_misread": 0} for d in DECODERS}
    misreads = []
    unknown_reads = unknown_cells = 0
    for t in range(n):
        r, c, k = int(rng.integers(T.PUZZLE_ROWS)), int(rng.integers(T.PUZZLE_COLS)), int(rng.integers(4))
        angle = 90 * k + rng.uniform(-JITTER_DEG, JITTER_DEG)
        gray, alpha, truth_grid = piece(r, c, cond["px_per_cell"], name)
        img, M = photograph(gray, alpha, rng, angle, tilt=cond["tilt"], blur=cond["blur"], noise=cond["noise"],
                            finger=bool(cond["finger"]), return_transform=True)
        gr = read_grid(img)
        truth = Read(r, c, k)
        m, unknown = misread_cells(gr, M, truth_grid) if isinstance(gr, GridRead) else (None, 0)
        if m is not None:
            misreads.append(m)
            unknown_reads += unknown > 0
            unknown_cells += unknown
        for dec in DECODERS:
            if not isinstance(gr, GridRead):
                decision = gr
            elif dec == "single":
                decision = decide_single(gr, table)
            else:
                decision = decode_grid(gr.cells, gr.mask, table)
            kind = classify(truth, decision)
            counts[dec][kind] += 1
            if kind == "wrong" and m is not None and m <= 1:
                counts[dec]["wrong_le1_misread"] += 1
                if name == "strong":
                    tag = "_".join([f"puzzle_{name}_{dec}"] + [f"{key}{cond[key]}" for key in LEVELS] + [f"seed{seed}_trial{t}"])
                    save_finding(findings_dir, tag, image=img, cells=gr.cells, mask=gr.mask, H=gr.H, M=M,
                                 truth=[r, c, k], angle_deg=angle, decision=repr(decision), misread=m,
                                 unknown=unknown)
    le1 = sum(m <= 1 for m in misreads)
    mean = round(float(np.mean(misreads)), 6) if misreads else ""
    levels = {key: cond[key] for key in LEVELS}
    if unknown_reads:
        log.warning("puzzle %s %s seed %s: %d of %d reads had %d visible cells with no printed bit (not counted "
                    "as misread)", name, levels, seed, unknown_reads, n, unknown_cells)
    return [{"experiment": "puzzle", "pattern": name, "decoder": dec, "arm": "", **levels, "n": n, **counts[dec],
             "reads_le1_misread": le1, "mean_misread_cells": mean, "seed": seed} for dec in DECODERS]


def run_puzzle(conditions: list[dict], n: int, seed: int, workers: int = 1, findings_dir=FINDINGS_DIR) -> list[dict]:
    """One row per condition, pattern and decoder, in that order (CONTRACTS.md section 6, without commit).

    Raises runner.Contradiction on E9 after saving the offending frames to findings_dir.
    """
    args = [(cond, name, n, seed, findings_dir) for cond in conditions for name in PATTERN_NAMES]
    return run_units(puzzle_unit, args, workers)
