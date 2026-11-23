# HANDOFF S2: simulated experiments (first draft, P4 tasks 1 to 6)

Branch `feat/s2-experiments`, worktree `.worktrees/s2-experiments`. Figures, `sim_summary.md`, the independent recomputation and the review come later from the orchestrator. The full runs have not been launched (task 6e).

## What was built

| File | Contents |
|---|---|
| `jigsaw/experiment/runner.py` | `classify`, `decide_single`, `truth_raster`, `misread_cells`; CSV schema `COLUMNS`, `write_csv`, `git_commit`, `tree_is_dirty`; `run_units` (serial or `ProcessPoolExecutor`, same output); `Contradiction` and `save_finding` (E9) |
| `jigsaw/experiment/sweep.py` | `full_conditions()`, `run_puzzle(conditions, n, seed, workers=1, findings_dir=None)` |
| `jigsaw/experiment/contrast.py` | `run_dense(arm, levels, n, seed, workers=1, findings_dir=None)` |
| `jigsaw/experiment/stats.py` | `wilson(k, n, z=1.96)` |
| `scripts/run_sim_puzzle.py`, `scripts/run_sim_dense.py` | `--seed` (required), `--n` (default 300), `--out`, `--workers`, `--allow-dirty`, `--findings`; `--levels` for dense |
| `tests/test_experiment_{runner,sweep,contrast,stats,scripts}.py` | 106 tests |
| `pyproject.toml`, `uv.lock` | `statsmodels>=0.14` in the `experiment` extra, used only by `tests/test_experiment_stats.py` |

Commits: `344c2fa` (task 1), `2f73211` (task 2), `691ce7f` (task 3), `4b4afc6` (task 4), `61369fb` (task 5), and this handoff.

## How each piece works, and the choices made

- `classify(truth, decision)`: `rejected` for any `Reject`; `correct` only when row, col and turn all match; otherwise `wrong` (right piece, wrong turn is wrong).
- `decide_single(grid_read, table)`: finds the top-left-most complete 5 x 5 window in the mask (row-major order), runs `decode_single` on it, then does what `decode_grid` does after its vote: `placement`, the off-puzzle check on the mapped cells, the centroid of all visible cells, the row and col range check. It drops `decode_grid`'s agreement checks (one placement, `min_agree`) and its whole-piece consistency check (`max_disagree`). Choice: the two off-puzzle checks are kept, because they are part of turning a placement into a piece, not agreement or consistency checks. The tail is copied from `decode.py` (S1 owns it); a test checks `decide_single == decode_grid` on clean reads of four pieces and turns.
- `misread_cells(grid_read, M, truth_grid)`: each visible cell centre `(x + 0.5, y + 0.5)` goes through `GridRead.H` to the frame, then through `inv(M)` (from `photograph(return_transform=True)`) to piece_back pixels, is rounded to the nearest pixel, and is compared with `truth_grid`. `truth_grid` is `runner.truth_raster(r, c, px_per_cell, gray.shape, grid)`: the printed bit of the G cell under every piece_back pixel, 255 off the grid. It mirrors `piece_back`'s layout; a test checks that it agrees with `piece_back`'s own drawing on every non-line pixel (exact, three pieces and pixel sizes, plus a random control grid). A point outside the raster or off the grid counts as misread.
- `run_puzzle`: one unit per (condition, pattern). Per trial: piece `(r, c)` uniform over 7 x 5, turn `k` uniform, angle `90 k + U(-35, 35)` degrees (the S1 vision test convention, so the true turn is `k`), `piece_back(r, c, px, grid=pattern)`, `photograph(..., return_transform=True)` at size 720 x 720, `read_grid` once, both decoders on the same `GridRead` (E3). A `read_grid` reject counts as rejected for both decoders. Patterns: `strong` = `patch.back_grid()`, `orient` = the 72 x 52 corner of `orient_u5_256.npz`.
- Seeding (E11): `SeedSequence(seed, spawn_key=(px*1000, tilt*1000, blur*1000, noise*1000, finger))` per condition, so serial equals parallel and adding a condition leaves the others unchanged (both tested). Choice: both patterns of a condition share the stream, so they see the same pieces, turns, perspective, noise and finger placement (paired across patterns as well as decoders).
- Columns not in the contract text, as interpreted: `reads_le1_misread` = trials that produced a `GridRead` with at most one misread visible cell (the same for both decoders); `wrong_le1_misread` = wrong reads among those; `mean_misread_cells` = mean over trials that produced a `GridRead` (empty if none). `arm` is empty for puzzle rows.
- `run_dense`: the 6 x 6 tori, u = 3, tables with `wrap=True`, `decode_single` only (decoder column `single`). Per trial: window position and turn uniform, seen = `rot90(window, k)`; `forced1` flips one uniformly chosen cell; `noise` flips each cell with probability p. The level p is written in the `noise` column; `px_per_cell`, `tilt`, `blur`, `finger` are empty. `forced1` ignores `levels` and gives one row per pattern. Both patterns share the stream.
- `wilson`: closed form, exact 0 at k = 0 and 1 at k = n. statsmodels takes alpha, not z, and uses `norm.isf(alpha / 2)` = 1.95996..., which differs from 1.96 by about 7e-6; the test therefore passes the alpha whose critical value is exactly z and then matches to 1e-9 on a 54-case grid.
- E9: when a strong-pattern trial is wrong with at most one misread cell, the worker saves `puzzle_strong_<decoder>_<condition>_seed<s>_trial<t>.png` (frame) and `.npz` (cells, mask, H, M, truth, angle, decision, misread), or for dense `dense_strong_<arm>_p<level>_seed<s>_trial<t>.npz` (seen, truth window, flips, truth, decision), in `--findings` (default `results/findings/`). `run_units` raises `Contradiction` as soon as such a unit finishes and cancels the pending ones; the script prints `E9 TRIPPED`, writes no CSV and exits with code 3. Tested end to end with a synthetic wrong decoder.
- E8: the scripts refuse any `git status --porcelain` output (untracked files included; `results/` is ignored) with exit code 2 unless `--allow-dirty`, in which case the commit column ends in `-dirty`.

## Commands run and their output

Tests (each task ran its own file, then the full suite):

```
$ uv run pytest tests/test_experiment_runner.py tests/test_experiment_sweep.py tests/test_experiment_contrast.py tests/test_experiment_stats.py tests/test_experiment_scripts.py
106 passed in 41.69s
$ uv run pytest            # after task 5
206 passed, 4 skipped in 129.97s (0:02:09)
$ uv run ruff check jigsaw/experiment scripts/run_sim_*.py tests/test_experiment_*.py
All checks passed!
```

Pilot, on a clean tree at `61369fb`, 16 logical CPUs (other agents may have been running tests):

```
$ cd .worktrees/s2-experiments && unset SSL_CERT_FILE
$ time uv run python scripts/run_sim_puzzle.py --seed 0 --n 50 --out results/sim_puzzle_pilot.csv
72 conditions x 2 patterns x 50 reads, seed 0, 16 workers
wrote 288 rows to results\sim_puzzle_pilot.csv in 430.1 s
real	7m10.629s
exit 0

$ time uv run python scripts/run_sim_dense.py --seed 0 --n 50 --out results/sim_dense_pilot.csv
forced1 and noise [0.01, 0.02, 0.05, 0.1, 0.2] x 2 patterns x 50 reads, seed 0
wrote 12 rows to results\sim_dense_pilot.csv in 0.1 s
real	0m0.725s
exit 0
```

Puzzle pilot, summed over the 12 conditions at each pixel size (n = 600 per cell of the table; no row of the 288 has `wrong > 0`, so E9 did not trip):

| px | pattern | decoder | correct | rejected | wrong | wrong_le1_misread | reads_le1_misread |
|---|---|---|---|---|---|---|---|
| 8 | strong | single | 455 | 145 | 0 | 0 | 581 |
| 8 | strong | grid | 454 | 146 | 0 | 0 | 581 |
| 8 | orient | single | 459 | 141 | 0 | 0 | 574 |
| 8 | orient | grid | 458 | 142 | 0 | 0 | 574 |
| 12 | strong | single | 514 | 86 | 0 | 0 | 598 |
| 12 | strong | grid | 514 | 86 | 0 | 0 | 598 |
| 12 | orient | single | 511 | 89 | 0 | 0 | 598 |
| 12 | orient | grid | 511 | 89 | 0 | 0 | 598 |
| 16 | strong | single | 531 | 69 | 0 | 0 | 600 |
| 16 | strong | grid | 531 | 69 | 0 | 0 | 600 |
| 16 | orient | single | 529 | 71 | 0 | 0 | 600 |
| 16 | orient | grid | 529 | 71 | 0 | 0 | 600 |

Rejections come almost entirely from the finger: grid decoder, finger 0: strong 1797 correct / 3 rejected of 1800, orient 1794 / 6; finger 1: strong 1289 / 511, orient 1295 / 505. A serial spot check (seed 99, 80 trials each) found no rejections at px 8, blur 1, noise 4, finger 0, and 16 of 16 rejections at px 16, finger 1 were `decode_grid` `no_window` with 0 misread cells (the finger leaves no complete 5 x 5 window).

Dense pilot (`results/sim_dense_pilot.csv`, n = 50):

```
pattern arm      p     correct rejected wrong wrong_le1 mean_misread
strong  forced1  -     0       50       0     0         1.0
orient  forced1  -     0       41       9     9         1.0
strong  noise    0.01  49      1        0     0         0.02
orient  noise    0.01  49      1        0     0         0.02
strong  noise    0.02  40      10       0     0         0.22
orient  noise    0.02  40      8        2     1         0.22
strong  noise    0.05  30      20       0     0         0.42
orient  noise    0.05  30      12       8     8         0.42
strong  noise    0.1   21      26       3     0         0.84
orient  noise    0.1   21      23       6     3         0.84
strong  noise    0.2   8       32       10    0         1.86
orient  noise    0.2   8       26       16    5         1.86
```

## Timing, projection and design

- Puzzle: 430 s for 7,200 reads (72 conditions x 2 patterns x 50), so about 0.06 s of wall time per read with 16 workers. At n = 300 the projection is 6 x 430 = about 2,580 s, about 43 minutes, if the machine is as loaded as during the pilot.
- Dense: 0.1 s at n = 50; under a second at n = 300.
- Design: the projected full puzzle run is well under 4 hours, so the full cross (`full_conditions()`, 72 conditions, 288 rows) stays and no `--design ofat` option was added (task 6c adds it only above 4 hours).

## Full-run commands (for the orchestrator; not launched here)

```
cd C:/Users/TJ/Documents/GitHub/COMP_5112_Research_Paper/.worktrees/s2-experiments
unset SSL_CERT_FILE
uv run python scripts/run_sim_puzzle.py --seed 1 --n 300 --workers 16 --out results/sim_puzzle.csv --findings results/findings
uv run python scripts/run_sim_dense.py --seed 1 --n 300 --out results/sim_dense.csv --findings results/findings
```

Exit codes: 0 success, 2 dirty tree, 3 E9 (findings saved, no CSV written).

## UNVERIFIED

Nothing robot-related was touched; no `# UNVERIFIED:` marks were added.

## Noticed outside my files

- `docs/jigsaw/S2_experiments.md` (v1 Spec) describes the dense experiment with a 4 x 4 patch and both decoders, and prediction 2 is about the four-window decoder. The P4 task runs the dense tori with `decode_single` only, so the dense CSV has no four-window rows and cannot test the second half of prediction 2.
- The S2 Spec's levels (px 6, 8, 12, 24; tilt 0 to 0.3; 20,000 reads) are superseded by the P4 levels used here (px 8 to 28, blur 0.5 to 1.5, noise 4 and 8, finger 0 and 1, tilt 0.06, n = 300). This follows the task text; the paper's Methods section should state the P4 levels.
- `render.piece_back` already takes `grid=`, so no S2 copy of it was needed (the v2 box suggested one).
- This branch was created at `4905c0f`; `main` has since gained `02b38d4` (docs only).

## Open questions

1. Dense noise levels: the task gave no values for p. I chose 0.01, 0.02, 0.05, 0.1, 0.2 (script default, `--levels` overrides). Please confirm.
2. Seeds: pilot used `--seed 0`; the full-run commands use `--seed 1` so the full run does not reuse the pilot's draws. Change if the paper needs a specific seed.
3. Prediction 3 says wrong reads are rare for both patterns and decoders; the pilot has none at all in 14,400 decoder decisions (7,200 reads x 2 decoders). With the finger condition dominating the rejections, the puzzle sweep mostly measures window coverage, not decoding. This is reported, not changed.
