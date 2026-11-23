"""Rendered puzzle experiment: uv run python scripts/run_sim_puzzle.py --seed 1 [--n 300] [--out results/sim_puzzle.csv]

Writes one row per condition, pattern and decoder (CONTRACTS.md section 6). Refuses a dirty git tree unless
--allow-dirty is passed, in which case the commit column ends in -dirty.
"""
import argparse
import os
import sys
import time
from pathlib import Path

from jigsaw.experiment.runner import git_commit, tree_is_dirty, write_csv
from jigsaw.experiment.sweep import full_conditions, run_puzzle

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--n", type=int, default=300, help="reads per condition and pattern")
    p.add_argument("--out", type=Path, default=ROOT / "results" / "sim_puzzle.csv")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    p.add_argument("--allow-dirty", action="store_true")
    a = p.parse_args(argv)
    dirty = tree_is_dirty()
    if dirty and not a.allow_dirty:
        print("refusing to run: the git tree has uncommitted changes (pass --allow-dirty to override)", file=sys.stderr)
        return 2
    commit = git_commit() + ("-dirty" if dirty else "")
    conditions = full_conditions()
    print(f"{len(conditions)} conditions x 2 patterns x {a.n} reads, seed {a.seed}, {a.workers} workers", flush=True)
    t0 = time.perf_counter()
    rows = run_puzzle(conditions, a.n, a.seed, workers=a.workers)
    write_csv(a.out, rows, commit)
    print(f"wrote {len(rows)} rows to {a.out} in {time.perf_counter() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
