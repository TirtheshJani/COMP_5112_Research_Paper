# HANDOFF S2: simulated experiments

Branch `feat/s2-experiments`, worktree `.worktrees/s2-experiments`. Status: the full runs, figures, summary, the independent recount and the review are done. The review fixes change `misread_cells`, so the puzzle CSV predates them: see "Rerun status" below. Results files (`results/`) are gitignored and not committed.

## What was built

| File | Contents |
|---|---|
| `jigsaw/experiment/runner.py` | `classify`, `decide_single`, `truth_raster`, `misread_cells` (returns `(misread, unknown)`); CSV schema `COLUMNS`, `write_csv`, `git_commit`, `tree_is_dirty`; `run_units` (serial or `ProcessPoolExecutor`, same output); `Contradiction` and `save_finding` (E9) |
| `jigsaw/experiment/sweep.py` | `full_conditions()`, `run_puzzle(conditions, n, seed, workers=1, findings_dir=None)` |
| `jigsaw/experiment/contrast.py` | `run_dense(arm, levels, n, seed, workers=1, findings_dir=None)` |
| `jigsaw/experiment/stats.py` | `wilson(k, n, z=1.96)` |
| `scripts/run_sim_puzzle.py`, `scripts/run_sim_dense.py` | `--seed` (required), `--n` (default 300), `--out`, `--workers`, `--allow-dirty`, `--findings`; `--levels` for dense |
| `scripts/make_figures.py` | `fig_puzzle.pdf`, `fig_dense.pdf` and `sim_summary.md` from the two CSVs alone |
| `tests/test_experiment_{runner,sweep,contrast,stats,scripts,figures}.py` | 111 tests |
| `pyproject.toml`, `uv.lock` | `statsmodels>=0.14` in the `experiment` extra, used only by `tests/test_experiment_stats.py` |

Commits: `344c2fa` (task 1), `2f73211` (task 2), `691ce7f` (task 3), `4b4afc6` (task 4), `61369fb` (task 5), `df9ec89` (first handoff draft; the full run used this commit), `33cccd5` (figures), `2098edd` (review fixes), and this handoff.

## How each piece works, and the choices made

- `classify(truth, decision)`: `rejected` for any `Reject`; `correct` only when row, col and turn all match; otherwise `wrong` (right piece, wrong turn is wrong).
- `decide_single(grid_read, table)`: finds the top-left-most complete 5 x 5 window in the mask (row-major order), runs `decode_single` on it, then does what `decode_grid` does after its vote: `placement`, the off-puzzle check on the mapped cells, the centroid of all visible cells, the row and col range check. It drops `decode_grid`'s agreement checks (one placement, `min_agree`) and its whole-piece consistency check (`max_disagree`). Choice: the two off-puzzle checks are kept, because they are part of turning a placement into a piece, not agreement or consistency checks. The tail is copied from `decode.py` (S1 owns it); a test checks `decide_single == decode_grid` on clean reads of four pieces and turns.
- `misread_cells(grid_read, M, truth_grid) -> (misread, unknown)`: each visible cell centre `(x + 0.5, y + 0.5)` goes through `GridRead.H` to the frame, then through `inv(M)` (from `photograph(return_transform=True)`) to piece_back pixels, is rounded to the nearest pixel, and is compared with `truth_grid`. `truth_grid` is `runner.truth_raster(r, c, px_per_cell, gray.shape, grid)`: the printed bit of the G cell under every piece_back pixel, 255 (`OFF_GRID`) off the grid. It mirrors `piece_back`'s layout; a test checks that it agrees with `piece_back`'s own drawing on every non-line pixel (exact, three pieces and pixel sizes, plus a random control grid). Since `2098edd`, a cell that lands off the raster or on `OFF_GRID` has no printed bit: it is counted in `unknown`, never in `misread`. `puzzle_unit` logs a warning per unit when any read has unknown cells (`... visible cells with no printed bit (not counted as misread)`) and saves `unknown` with E9 findings. Before `2098edd` such cells counted as misread.
- What "at most one misread cell" means in the CSV: the count is over all visible cells of the piece, not over one window. For `grid` this matches the decoder, which uses every visible cell. For `single` the decoder reads one 5 x 5 window, whose misreads are a subset of the piece total. So every read in the `<= 1` bucket also has at most one misread cell in its window, and the Prediction 1 claim does not overstate. The other direction is not covered: a `single` read with at most one misread cell in its window but two or more elsewhere on the piece is outside the bucket, so E9 would not see it if it were wrong. In the full run no puzzle read was wrong at all (`wrong` = 0 in all 288 rows), so nothing was missed here.
- `run_puzzle`: one unit per (condition, pattern). Per trial: piece `(r, c)` uniform over 7 x 5, turn `k` uniform, angle `90 k + U(-35, 35)` degrees (the S1 vision test convention, so the true turn is `k`), `piece_back(r, c, px, grid=pattern)`, `photograph(..., return_transform=True)` at size 720 x 720, `read_grid` once, both decoders on the same `GridRead` (E3). A `read_grid` reject counts as rejected for both decoders. Patterns: `strong` = `patch.back_grid()`, `orient` = the 72 x 52 corner of `orient_u5_256.npz`.
- Seeding (E11): `SeedSequence(seed, spawn_key=(px*1000, tilt*1000, blur*1000, noise*1000, finger))` per condition, so serial equals parallel and adding a condition leaves the others unchanged (both tested). Both patterns of a condition share the stream, so they see the same pieces, turns, perspective, noise and finger placement. A test now records `(r, c)`, the angle and the generator state after every `photograph` call (finger on) and checks that strong and orient match exactly.
- Columns not in the contract text, as interpreted: `reads_le1_misread` = trials that produced a `GridRead` with at most one misread visible cell (the same for both decoders); `wrong_le1_misread` = wrong reads among those; `mean_misread_cells` = mean over trials that produced a `GridRead` (empty if none). `arm` is empty for puzzle rows.
- The `noise` column has two units. Puzzle rows: the Gaussian pixel noise sigma passed to `photograph` (4 or 8 grey levels). Dense rows: the cell flip probability p of arm `noise` (0.01 to 0.2), empty for arm `forced1`. The two experiments are in separate CSVs and `make_figures.py` never pools across them: `fig_puzzle` reads only the puzzle CSV, `fig_dense` only the dense CSV, and its x axis is labelled "cell flip probability p".
- `run_dense`: the 6 x 6 tori, u = 3, tables with `wrap=True`, `decode_single` only (decoder column `single`). Per trial: window position and turn uniform, seen = `rot90(window, k)`; `forced1` flips one uniformly chosen cell; `noise` flips each cell with probability p. `px_per_cell`, `tilt`, `blur`, `finger` are empty. `forced1` ignores `levels` and gives one row per pattern. Both patterns share the stream.
- `wilson`: closed form, exact 0 at k = 0 and 1 at k = n. statsmodels takes alpha, not z, and uses `norm.isf(alpha / 2)` = 1.95996..., which differs from 1.96 by about 7e-6; the test therefore passes the alpha whose critical value is exactly z and then matches to 1e-9 on a 54-case grid. The test file now imports statsmodels directly, so a missing dependency fails loudly instead of skipping.
- E9: when a strong-pattern trial is wrong with at most one misread cell, the worker saves `puzzle_strong_<decoder>_<condition>_seed<s>_trial<t>.png` (frame) and `.npz` (cells, mask, H, M, truth, angle, decision, misread, unknown), or for dense `dense_strong_<arm>_p<level>_seed<s>_trial<t>.npz` (seen, truth window, flips, truth, decision), in `--findings` (default `results/findings/`). The check applies to every strong row, both decoders and both dense arms. `run_units` raises `Contradiction` as soon as such a unit finishes and cancels the pending ones; the script prints `E9 TRIPPED`, writes no CSV and exits with code 3. With `--workers` above 1, units already running when the first trip is seen still finish and may save their own findings, so which files appear in `results/findings/` depends on finish order. After a trip, re-run serially (`--workers 1`) for a deterministic findings folder.
- E8: the scripts refuse any `git status --porcelain` output (untracked files included; `results/` is ignored) with exit code 2 unless `--allow-dirty`, in which case the commit column ends in `-dirty`.

## Commands run and their output

### Review fixes (`2098edd`)

New and changed tests before the code change (RED):

```
$ uv run pytest tests/test_experiment_runner.py tests/test_experiment_sweep.py tests/test_experiment_stats.py -k "misread or unprinted or same_trials or wilson or one_misread"
FAILED tests/test_experiment_runner.py::test_misread_cells_is_zero_on_a_clean_read
FAILED tests/test_experiment_runner.py::test_misread_cells_counts_a_known_flip
FAILED tests/test_experiment_runner.py::test_misread_cells_ignores_cells_outside_the_mask
FAILED tests/test_experiment_runner.py::test_misread_cells_counts_cells_off_the_raster_as_unknown_not_misread
FAILED tests/test_experiment_runner.py::test_a_single_flip_counts_one_misread_beside_unprinted_cells
FAILED tests/test_experiment_sweep.py::test_a_wrong_read_with_one_misread_beside_unprinted_cells_trips_e9
FAILED tests/test_experiment_sweep.py::test_unprinted_cells_are_logged_and_not_counted
7 failed, 55 passed, 33 deselected in 7.72s
```

The E9 test failed with `DID NOT RAISE Contradiction`: before the fix, the unprinted cells pushed a wrong read with one real misread out of the `<= 1` bucket. `test_strong_and_orient_see_the_same_trials` passed on the existing code; with a temporary extra `rng.random()` for orient only it failed (`1 failed`), and the mutation was removed.

After the change:

```
$ uv run pytest tests/test_experiment_runner.py tests/test_experiment_sweep.py tests/test_experiment_contrast.py tests/test_experiment_stats.py tests/test_experiment_scripts.py tests/test_experiment_figures.py
111 passed in 54.73s
$ uv run ruff check jigsaw/experiment scripts/run_sim_puzzle.py scripts/run_sim_dense.py scripts/make_figures.py tests/test_experiment_*.py
All checks passed!
$ uv run pytest
211 passed, 4 skipped in 130.30s (0:02:10)
```

The 4 skips are outside S2: `test_viewer_server.py` (flask not installed), `test_voice_stt.py` (faster-whisper not installed), `test_voice_tts.py` twice (Piper voice file absent).

### Pilot (at `61369fb`, seed 0, n = 50)

```
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

The pilot showed no wrong read in any puzzle row; rejections came almost entirely from the finger (grid decoder, finger 0: strong 3 and orient 6 rejected of 1800; finger 1: strong 511 and orient 505 of 1800). The projected full puzzle run (about 43 minutes) was well under 4 hours, so the full cross of 72 conditions stayed and no `--design ofat` option was added.

### Full run (run by the orchestrator at `df9ec89`, before the review fixes)

```
cd C:/Users/TJ/Documents/GitHub/COMP_5112_Research_Paper/.worktrees/s2-experiments
unset SSL_CERT_FILE
uv run python scripts/run_sim_puzzle.py --seed 1 --n 300 --workers 16 --out results/sim_puzzle.csv --findings results/findings
uv run python scripts/run_sim_dense.py --seed 1 --n 300 --out results/sim_dense.csv --findings results/findings
```

`results/sim_puzzle_full.log`:

```
72 conditions x 2 patterns x 300 reads, seed 1, 16 workers
wrote 288 rows to results\sim_puzzle.csv in 2591.3 s
```

`results/sim_dense_full.log`:

```
forced1 and noise [0.01, 0.02, 0.05, 0.1, 0.2] x 2 patterns x 300 reads, seed 1
wrote 12 rows to results\sim_dense.csv in 0.2 s
```

Both exit codes were 0 (as reported by the orchestrator; the logs do not record them). E9 did not trip and `results/findings/` does not exist. Both CSVs carry seed 1 and commit `df9ec89431ffbd0dd0ab45a090d85cf22f3f26c9` in every row.

Puzzle totals over the 72 conditions (n = 21600 reads per pattern and decoder):

| pattern | decoder | wrong | wrong_le1_misread | reads_le1_misread | rejected |
|---|---|---|---|---|---|
| strong | single | 0 | 0 | 21436 | 3184 |
| strong | grid | 0 | 0 | 21436 | 3193 |
| orient | single | 0 | 0 | 21357 | 3239 |
| orient | grid | 0 | 0 | 21357 | 3247 |

Dense (`results/sim_dense.csv`, n = 300, decoder single):

```
pattern arm      p     correct rejected wrong wrong_le1 reads_le1 mean_misread
strong  forced1  -     0       300      0     0         300       1.0
orient  forced1  -     0       233      67    67        300       1.0
strong  noise    0.01  273     25       2     0         298       0.096667
orient  noise    0.01  273     21       6     6         298       0.096667
strong  noise    0.02  247     53       0     0         297       0.186667
orient  noise    0.02  247     40       13    13        297       0.186667
strong  noise    0.05  182     108      10    0         276       0.49
orient  noise    0.05  182     87       31    21        276       0.49
strong  noise    0.1   113     160      27    0         233       0.91
orient  noise    0.1   113     136      51    28        233       0.91
strong  noise    0.2   43      206      51    0         140       1.75
orient  noise    0.2   43      190      67    30        140       1.75
```

### Figures and summary (`33cccd5`)

```
$ uv run python scripts/make_figures.py --puzzle results/sim_puzzle.csv --dense results/sim_dense.csv --out-dir results
```

Writes `results/fig_puzzle.pdf` (29458 bytes), `results/fig_dense.pdf` (19327 bytes) and `results/sim_summary.md`. Re-running the committed script into a scratch folder gave exit 0, a byte-identical `sim_summary.md` and PDFs of the same sizes. `fig_puzzle`: correct, rejected and wrong rates against px per cell, pooled over blur, noise and tilt (sum k and n, then the Wilson interval), finger 0 and finger 1 in separate columns, four series (pattern x decoder). `fig_dense`: A, forced1 wrong rate per pattern; B and C, noise-arm wrong and correct rates against p on a log axis. Nobody has looked at the PDFs; they were checked in code only (non-empty, `%PDF` header).

Headline sentences of `results/sim_summary.md` (all intervals Wilson 95 percent):

1. Prediction 1: the data agree. Reads with at most one misread cell on the strong pattern were wrong 0 of 21436 times for each decoder on the puzzle (0.00 to 0.02 percent). On the dense tori the single decoder gave 0 of 300 in forced1 (0.00 to 1.26 percent) and 0 of 1244 in the noise arm (0.00 to 0.31 percent). The four-window decoder was not run on the dense tori.
2. Prediction 2: the single-window half agrees. Forced1 wrong reads were 67 of 300 on orient (22.33 percent, 17.99 to 27.38 percent) and 0 of 300 on strong (0.00 to 1.26 percent). The four-window half was not run, so it is reported as untested, neither agreeing nor disagreeing.
3. Prediction 3: wrong reads were 0 of 21600 for each of the four pattern and decoder combinations (0.00 to 0.02 percent). "Rare" is taken as a point estimate under 1 percent (a choice made in `make_figures.py`, see open questions).

The summary has one more paragraph, the noise-arm counts at each p.

Observations on the numbers:

- The rendered puzzle cannot separate the patterns: the control (orient) also had 0 wrong reads in 21600, for both decoders. Prediction 3 is met, but trivially.
- The strong pattern has wrong reads in the noise arm (2, 0, 10, 27, 51 at p = 0.01, 0.02, 0.05, 0.1, 0.2). Every one has at least two flipped cells (`wrong_le1_misread` = 0), so Prediction 1 holds.
- Correct counts are identical for strong and orient at every p (273, 247, 182, 113, 43). The patterns share the flip draws, and `decode_single` is correct only on an unflipped window, so this is expected by construction.
- Forced1 on strong: all 300 reads rejected, none correct and none wrong.

### Independent recount

Another agent recomputed everything from the two CSVs with its own code. Row checks: correct + rejected + wrong = n in every row; wrong_le1_misread <= wrong and wrong_le1_misread <= reads_le1_misread <= n in every row; one seed and one commit; 288 puzzle rows (72 x 2 x 2) with no duplicates; single and grid rows paired (equal `mean_misread_cells` and `reads_le1_misread` for every condition and pattern); 12 dense rows.

| Prediction | Count | Wilson 95 percent |
|---|---|---|
| 1, puzzle, strong, single | 0 of 21436 | 0 to 0.018 percent |
| 1, puzzle, strong, grid | 0 of 21436 | 0 to 0.018 percent |
| 1, dense forced1, strong, single | 0 of 300 | 0 to 1.26 percent |
| 1, dense noise, strong, single | 0 of 1244 | 0 to 0.31 percent |
| 2, forced1, orient, wrong | 67 of 300 | 17.99 to 27.38 percent |
| 2, forced1, strong, wrong | 0 of 300 | 0 to 1.26 percent |
| 3, puzzle, each pattern x decoder | 0 of 21600 | 0 to 0.018 percent |

Disagreements with `sim_summary.md`: none. Every count and interval matches, including the noise-arm paragraph; the four-window dense cell is marked untested. I spot-checked the puzzle totals and every dense row against the CSVs (tables above) and found the same numbers.

## Rerun status

RERUN NEEDED for the puzzle experiment only, because `2098edd` changes `misread_cells`, which feeds the puzzle CSV. Only two columns of puzzle rows can change: `reads_le1_misread` (the Prediction 1 denominator, 21436 for strong) and `mean_misread_cells`, and only if some read had visible cells with no printed bit (the rerun log will show a warning per affected unit). `correct`, `rejected` and `wrong` cannot change, because no decision depends on `misread_cells`. `wrong_le1_misread` stays 0 because `wrong` is 0 in every puzzle row. The dense experiment does not use `misread_cells`, and its CSV is unaffected. A rerun would be at `2098edd` or later, seed 1, n = 300, with the commands above (about 43 minutes), followed by `make_figures.py`.

## Review findings

| # | Severity | Finding | What I did |
|---|---|---|---|
| 1 | major | `misread_cells` counted visible cells off the raster as misread, which can move a wrong read out of the `<= 1` bucket and hide E9 | Fixed in `2098edd`. Returns `(misread, unknown)`; cells off the raster or on `OFF_GRID` go to `unknown`, never `misread`. `puzzle_unit` logs them per unit and saves `unknown` with findings. Tests: off-raster cells are unknown, not misread; a single flip beside unprinted cells counts exactly one misread for every visible cell; a hand-built single misread plus unprinted cells with a wrong decoder trips E9 (failed before the fix); unprinted cells are logged and not counted. RERUN NEEDED (see above) |
| 2 | minor | `np.round` has a half-pixel bias against `truth_raster`; use `np.floor` | Rejected, code unchanged. `inv(M)` gives cv2 coordinates, and `cv2.warpPerspective` puts source pixel i's centre at coordinate i, so the nearest pixel is `np.round`. A scratch check warped a random one-bit-per-pixel raster with `M` built as `photograph` builds it (5 random perspectives, about 52000 frame pixels each): `np.round` mismatched 0.0000, `np.floor` mismatched 0.37. The `misread_cells` docstring now says why |
| 3 | minor | `wrong_le1_misread` uses the whole-piece misread count while `single` reads one window | Documented above ("What at most one misread cell means"), including the direction the reviewer did not mention: E9 can miss a `single` wrong read with at most one misread cell in its window but more elsewhere. No puzzle read was wrong in the full run |
| 4 | minor | With `workers > 1`, which findings get saved after an E9 trip depends on finish order | Documented above (E9 bullet): re-run serially after a trip. The full run did not trip |
| 5 | minor | Nothing asserts that a strong `grid` row trips E9 | Rejected, already tested: `test_a_strong_contradiction_saves_the_frame_and_stops` (`tests/test_experiment_sweep.py`) makes `decode_grid` wrong and asserts the Contradiction rows are exactly `{("strong", "grid")}`; the new E9 test also trips through `grid`. The dense arms are covered by `test_a_strong_contradiction_saves_the_cells_and_stops` |
| 6 | minor | Strong and orient share one RNG stream only if draws do not depend on piece content | Fixed with a test: `test_strong_and_orient_see_the_same_trials` records `(r, c)`, angle and generator state after each `photograph` (finger on, noise 8) and requires equality; checked that it fails when orient takes one extra draw. No code change was needed |
| 7 | minor | `importorskip("statsmodels...")` can make the only `wilson` check vanish | Fixed: direct import, so a missing statsmodels fails loudly. statsmodels 0.15.0 is installed in the uv environment and the file runs (part of the 111) |
| 8 | minor | `noise` is pixel sigma in puzzle rows and flip probability in dense rows | Documented above (`noise` column bullet). `make_figures.py` never pools the two CSVs. A `CONTRACT_CHANGE` note for CONTRACTS section 6 is outside the files I may edit; see open questions |
| 9 | minor | `git status --porcelain` counts untracked files as dirty | No change, as the reviewer concluded |

The reviewer also checked and found no problem with: `COLUMNS` against CONTRACTS section 6, `decide_single` having no agreement or consistency check, paired reads in `puzzle_unit`, per-condition seeding, `classify` requiring row, col and turn, and the turn convention. The reviewer did not grep for en dashes; I grepped every S2 file (code, tests, scripts, `sim_summary.md`, this handoff) for U+2014 and U+2013 and found none.

## UNVERIFIED

Nothing robot-related was touched; no `# UNVERIFIED:` marks were added.

## Noticed outside my files

- `docs/jigsaw/S2_experiments.md` (v1 Spec) describes the dense experiment with a 4 x 4 patch and both decoders, and Prediction 2 is about the four-window decoder. The P4 task runs the dense tori with `decode_single` only, so the dense CSV has no four-window rows and cannot test the second half of Prediction 2.
- CONTRACTS section 6 does not say that `noise` means pixel sigma for puzzle rows and flip probability for dense rows.
- The S2 Spec's levels (px 6, 8, 12, 24; tilt 0 to 0.3; 20,000 reads) are superseded by the P4 levels used here (px 8 to 28, blur 0.5 to 1.5, noise 4 and 8, finger 0 and 1, tilt 0.06, n = 300). The paper's Methods section should state the P4 levels.
- `render.piece_back` already takes `grid=`, so no S2 copy of it was needed.
- This branch was created at `4905c0f`; `main` has since moved on.

## Open questions

1. Rerun: the puzzle CSV predates `2098edd`. Rerun the puzzle experiment (about 43 minutes, then `make_figures.py`), or keep the `df9ec89` data and state in the paper that unprinted cells, if any, were counted as misread?
2. Prediction 2, four-window half: untested. Add a dense run with the four-window decoder, or report it as untested in the paper?
3. Prediction 3: the control pattern also had no wrong reads on the rendered puzzle, so this experiment does not separate the patterns. "Rare" was taken as a point estimate under 1 percent; please confirm the threshold or the wording.
4. Prediction 1, window level: should the `single` decoder's E9 check also count misreads inside its own window (it would catch the case described under finding 3)? It needs a code change and a rerun; with zero wrong puzzle reads it would not change this run's conclusions.
5. CONTRACTS section 6: someone with access should file a `CONTRACT_CHANGE` note documenting the two units of `noise`.
6. Dense noise levels: I chose 0.01, 0.02, 0.05, 0.1, 0.2 (script default, `--levels` overrides). Please confirm.
7. Seeds: the pilot used seed 0 and the full run seed 1, so the full run does not reuse the pilot's draws. Change if the paper needs a specific seed.
