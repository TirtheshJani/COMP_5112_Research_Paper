"""Dense tori experiment: uv run python scripts/run_sim_dense.py --seed 1 [--n 300] [--out results/sim_dense.csv]

Runs arm forced1 (one row per pattern) and arm noise (one row per flip probability and pattern) at the cell
level with decode_single (CONTRACTS.md section 6). Refuses a dirty git tree unless --allow-dirty is passed,
in which case the commit column ends in -dirty.
"""
import argparse
import sys
import time
from pathlib import Path

from jigsaw.experiment.contrast import run_dense
from jigsaw.experiment.runner import git_commit, tree_is_dirty, write_csv

ROOT = Path(__file__).resolve().parent.parent
NOISE_LEVELS = (0.01, 0.02, 0.05, 0.1, 0.2)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--n", type=int, default=300, help="reads per condition and pattern")
    p.add_argument("--out", type=Path, default=ROOT / "results" / "sim_dense.csv")
    p.add_argument("--levels", type=float, nargs="+", default=list(NOISE_LEVELS), help="flip probabilities, arm noise")
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--allow-dirty", action="store_true")
    a = p.parse_args(argv)
    dirty = tree_is_dirty()
    if dirty and not a.allow_dirty:
        print("refusing to run: the git tree has uncommitted changes (pass --allow-dirty to override)", file=sys.stderr)
        return 2
    commit = git_commit() + ("-dirty" if dirty else "")
    print(f"forced1 and noise {a.levels} x 2 patterns x {a.n} reads, seed {a.seed}", flush=True)
    t0 = time.perf_counter()
    rows = run_dense("forced1", (), a.n, a.seed, workers=a.workers) + run_dense("noise", a.levels, a.n, a.seed, workers=a.workers)
    write_csv(a.out, rows, commit)
    print(f"wrote {len(rows)} rows to {a.out} in {time.perf_counter() - t0:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
