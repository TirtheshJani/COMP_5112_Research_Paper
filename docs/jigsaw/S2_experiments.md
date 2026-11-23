# S2 Experiments: rendered puzzle, dense tori, statistics, figures

> **v2 update (23 Nov).** Use `render.piece_back` + `render.photograph` and `reader.PieceReader` (or `vision.read_grid` + `decode.decode_grid`) instead of `draw_piece`, `read_cells` and `decode_four`. The two decoders compared are `single` (one window, the paper's single read) and `grid` (`decode_grid`). Pieces are 35 (7 x 5) jigsaw pieces at front coordinates; `classify(truth: Read, decision)` compares row and col. Sweep axes: px per cell (8 to 30), tilt, blur, noise, finger occlusion, duplex misregistration (`piece_back(offset_mm=...)`). The control pattern is the 72 x 52 corner of `orient_u5_256.npz`, which has distance-1 pairs; render it with the same outlines by passing its grid to a copy of `piece_back` (add a `grid` argument in S2's own helper, not in `render.py`). CSV columns are in CONTRACTS v2 section 6.

| | |
|---|---|
| Terminal | Opus 5.5, effort xhigh, Ultracode on |
| Branch and worktree | `feat/s2-experiments` in `.worktrees/s2-experiments` |
| Depends on | S1 merged |
| Blocks | S8, and the Results section of the paper |
| Owns | `jigsaw/experiment/` (`sweep.py`, `contrast.py`, `stats.py`, `figures.py`, `runner.py`), `scripts/run_sim_puzzle.py`, `scripts/run_sim_dense.py`, `scripts/make_figures.py`, `tests/test_experiment_*.py`, `results/sim_*.csv`, `results/figures/` |
| Must not edit | anything under `jigsaw/` outside `experiment/` |
| Skills | `karpathy-guidelines`, `test-driven-development`, `verification-before-completion`, `statistical-analysis`, `scientific-critical-thinking`, `matplotlib` or `scientific-visualization`, `dispatching-parallel-agents`, `engineering:code-review` |

---

## Spec

### Problem

The paper asks whether a strong-form pattern reduces wrong position reports compared with a 4-orientable pattern of the same size, under a single-window decoder and under a four-window decoder. The design was fixed in the outline before data collection. This workstream implements that design exactly and produces the CSV files and figures the paper cites.

### The design (from the paper outline, do not change)

Two factors in every experiment: pattern (`strong`, `orient`) and decoder (`single`, `four`). Each read is classified as correct, rejected or wrong. A wrong read is an accepted read that reports an incorrect position or turn.

| Experiment | Patterns | Read | Conditions | Reads |
|---|---|---|---|---|
| Rendered puzzle | 30 x 48 patches of the two 256 x 256 tori | 6 x 6 piece, 5 x 5 windows | pixels per cell 6, 8, 12, 24; tilt; blur; noise | 20,000 per condition |
| Dense tori | the two 6 x 6 tori | 4 x 4 patch, 3 x 3 windows | arm `noise` (image noise sweep) and arm `forced1` (exactly one cell flipped after a clean read) | 20,000 per condition |

Predictions the data are tested against:

1. On a strong-form pattern no read with at most one misread cell is wrong, for either decoder.
2. On the dense tori in the `forced1` arm, the single-window decoder produces wrong reads on the control pattern, and the four-window decoder rejects nearly all such reads on both patterns.
3. On the rendered puzzle, wrong reads are rare for both patterns and both decoders.

Prediction 4 (robot against simulation) belongs to S6, which uses `stats.wilson` from here.

### Goals

1. Two scripts that regenerate `results/sim_puzzle.csv` and `results/sim_dense.csv` from a seed, with the schema in `CONTRACTS.md` section 6.
2. For every row, the three counts sum to `n`, and the number of misread cells is recorded so that prediction 1 can be checked per row.
3. Wilson 95 percent intervals for every proportion, and a short machine-written summary (`results/sim_summary.md`) that states for each prediction whether the data agree, with the numbers.
4. Two figures in PDF for the paper.
5. An independent recomputation of the headline counts by a separate agent using its own code.

### Non-goals

- No change to the design, the levels or the number of reads without the author's approval. If a level turns out to be uninformative, report it; do not replace it.
- No significance tests beyond the intervals. The outline promises intervals.
- No tuning of the renderer to make results look better.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| E1 | P0 | `runner.classify(truth, decision)` returns `correct`, `rejected` or `wrong` | Unit tests for all three, including a correct position with a wrong turn (which is wrong) |
| E2 | P0 | `sweep.run_puzzle(conditions, n, seed)` yields one CSV row per pattern, decoder and condition | With `n=50`: counts sum to 50 in every row; same seed gives identical rows |
| E3 | P0 | Paired reads: for a given condition and pattern, both decoders see the same rendered image and the same sampled cells | Test that `mean_misread_cells` is equal for `single` and `four` rows of the same condition |
| E4 | P0 | `misread_cells` is computed by comparing sampled cells with the true cells under the true turn | Unit test with a known flip |
| E5 | P0 | `contrast.run_dense(arm, levels, n, seed)` for both arms | `forced1`: every read has exactly one misread cell; on `strong`, `wrong == 0` for both decoders |
| E6 | P0 | Control patch choice for the puzzle | The 30 x 48 control patch is the top-left corner of `orient_u5_256.npz`. If S0 found that this corner has no pair at distance 1, also run a second control corner that has at least one, chosen by a documented scan, and label it `orient_d1` |
| E7 | P0 | `stats.wilson(k, n, z=1.96)` | Matches `statsmodels.stats.proportion.proportion_confint(method="wilson")` to 1e-9 on a grid (test only; no runtime dependency) |
| E8 | P0 | Provenance | Each CSV row ends with `seed, commit`; scripts refuse a dirty tree unless `--allow-dirty` |
| E9 | P0 | Stop on a contradiction | If any `strong` row has `wrong_le1_misread > 0`, the script saves the offending image and cells to `results/findings/` and exits non-zero |
| E10 | P0 | `results/sim_summary.md` | Generated by `scripts/make_figures.py` from the CSVs; one paragraph per prediction with counts and intervals |
| E11 | P1 | Parallel execution over conditions with `concurrent.futures.ProcessPoolExecutor`, seeded per condition | Same output as serial execution for the same seed |
| E12 | P0 | Figures | `fig_dense.pdf`: wrong rate by pattern and decoder in the `forced1` arm with intervals. `fig_puzzle.pdf`: correct, rejected and wrong rates against pixels per cell. Vector PDF, colour-blind-safe palette, fonts embedded |

### Design notes

- Seeding. One `numpy.random.SeedSequence(seed)` spawned per condition, so that parallel and serial runs agree and adding a condition does not change the others.
- The noise sweep levels. Rendered puzzle: tilt in {0, 0.1, 0.2, 0.3}, blur sigma in {0, 1, 2, 3} pixels, noise sigma in {0, 8, 16, 32} grey levels, crossed with the four pixels-per-cell values. That is 256 conditions x 2 patterns x 20,000 reads. Estimate the run time on 1,000 reads first and report it before starting the full run. If it exceeds four hours on the laptop, ask the author whether to use a one-factor-at-a-time sweep around a centre point (tilt 0.15, blur 1, noise 8) instead of the full cross. Do not decide alone.
- The `forced1` arm bypasses the renderer: take the true `n x n` cells at a random position and turn, flip one uniformly chosen cell, and decode. It measures the decoders, not the camera.
- The dense `noise` arm goes through `render.draw_patch_read`, `photograph` and `vision.read_cells(n=4)`.
- Comparing patterns "at matched rates of correct reads" (the outline's wording for the noise arm): report the wrong rate for both patterns at each noise level, and state the correct rate beside it. Do not interpolate.

### Open questions

| Question | Who | Blocking |
|---|---|---|
| Full cross or one-factor-at-a-time for the puzzle sweep | Author, after the timing estimate | Yes for the full run |
| Does the top-left control corner contain distance-1 pairs | From `HANDOFF_S0.md` | Yes for E6 |

---

## Plan

**Goal:** two CSVs, a summary and two figures, regenerated by three commands.

### Task 1: Worktree, baseline, timing probe

- [ ] Create the worktree. `uv sync --extra dev --extra experiment`. Run the test suite (expect pass).
- [ ] Read `HANDOFF_S0.md` and `HANDOFF_S1.md`. Note the control-corner result and the `Table` choice.

### Task 2: Classification and misread counting (E1, E4)

- [ ] Write `tests/test_experiment_runner.py`:

```python
from jigsaw.types import Position, Reject
from jigsaw.experiment.runner import classify, count_misread

def test_classify():
    truth = Position(3, 4, 1)
    assert classify(truth, Position(3, 4, 1)) == "correct"
    assert classify(truth, Position(3, 4, 2)) == "wrong"      # right place, wrong turn
    assert classify(truth, Position(0, 4, 1)) == "wrong"
    assert classify(truth, Reject("no_match")) == "rejected"

def test_count_misread():
    import numpy as np
    true = np.zeros((6, 6), np.uint8); seen = true.copy(); seen[2, 3] = 1
    assert count_misread(true, seen) == 1
    assert count_misread(true, None) is None                  # no quad found
```

- [ ] Run (fail), implement, run (pass). Commit.

### Task 3: Dense tori, forced arm (E5, E9)

Do this before the rendered experiments. It is fast, it has an exact expected result, and it validates the whole counting path.

- [ ] Test:

```python
def test_forced1_strong_has_no_wrong_reads():
    rows = list(run_dense(arm="forced1", levels=[None], n=2000, seed=0))
    by = {(r["pattern"], r["decoder"]): r for r in rows}
    assert set(by) == {("strong", "single"), ("strong", "four"), ("orient", "single"), ("orient", "four")}
    for r in rows:
        assert r["correct"] + r["rejected"] + r["wrong"] == r["n"] == 2000
        assert r["reads_le1_misread"] == 2000
    assert by[("strong", "four")]["correct"] == by[("orient", "four")]["correct"] == 0
    assert by[("strong", "single")]["wrong"] == 0 and by[("strong", "four")]["wrong"] == 0
    assert by[("orient", "single")]["wrong"] > 0
```

- [ ] Implement `contrast.run_dense`. The flipped cell is drawn uniformly over the 16 cells of the 4 x 4 patch, because the outline says "exactly one cell of each read is changed". The single-window decoder reads the window at offset `(0, 0)`. When the flipped cell lies outside that window (7 of 16 cells), the single-window decoder sees a clean window and reads correctly, so its `correct` count is not 0. Report both the overall wrong rate and the rate conditional on the flip being inside the window that was read. Add a column-free way to recover the conditional rate: run a second level of the arm, `forced1_in_window`, in which the flip is drawn from the 9 cells of that window. Record this in the handoff note.
- [ ] Run. Check the `orient`, `single` wrong rate against the exhaustive count printed by S1's `test_single_is_fooled_on_the_control_torus` (they must agree within sampling error). Commit.

### Task 4: Rendered experiments (E2, E3, E6, E8, E11)

- [ ] Tests with `n=50` for counts, determinism and pairing. Implement `sweep.run_puzzle` and the `noise` arm of `run_dense`. Implement the dirty-tree check and the `commit` column with `git rev-parse --short HEAD`.
- [ ] Run a timing probe: `uv run python scripts/run_sim_puzzle.py --n 1000 --seed 1 --out results/_timing.csv --allow-dirty`. Report reads per second and the projected time for the full cross. Ask the author the open question if the projection exceeds four hours.
- [ ] Commit the code. Then, with a clean tree, run:

```
uv run python scripts/run_sim_dense.py  --n 20000 --seed 20261119 --out results/sim_dense.csv
uv run python scripts/run_sim_puzzle.py --n 20000 --seed 20261119 --out results/sim_puzzle.csv
```

- [ ] If either script exits non-zero because of E9, stop and report. Otherwise commit the CSVs.

### Task 5: Statistics, summary, figures (E7, E10, E12)

- [ ] Test `stats.wilson` against statsmodels on a grid of `(k, n)`, including `k=0` and `k=n`. Implement in six lines.
- [ ] `scripts/make_figures.py` reads the two CSVs and writes `results/figures/fig_dense.pdf`, `results/figures/fig_puzzle.pdf` and `results/sim_summary.md`. The summary is generated from the data: for each prediction, the relevant counts, proportions and intervals, and the word "agrees" or "contradicts". No hand-written numbers.
- [ ] Open both PDFs and look at them (render to PNG and read the image). Check axis labels, legend, and that intervals are visible. Commit.

### Task 6: Independent verification

- [ ] Dispatch the verifier subagent described below. Compare its counts with the CSV. Any difference is investigated with `systematic-debugging` before anything is reported.

### Task 7: Review, handoff, pull request

- [ ] Review subagent with `engineering:code-review`. Write `HANDOFF_S2.md`: commands, run times, the summary file's content, the verifier's result, and the decision from Task 3. Open the pull request.

### Subagent use

With Ultracode on, Claude plans its own workflow. Give it these boundaries:

- Parallel after Task 2: (a) dense tori experiment (Task 3 and the dense part of Task 4), (b) puzzle sweep (Task 4), (c) statistics and figure code written against a small hand-made CSV with the contract schema (Task 5). They touch `contrast.py`, `sweep.py`, and `stats.py` plus `figures.py` respectively. `runner.py` is finished first and is read-only for all three.
- Verifier (Task 6), a fresh general-purpose subagent that has not seen the implementation: "You are checking an experiment. Without reading anything under `jigsaw/experiment/`, write a standalone script `scripts/verify_forced1.py` that uses only `jigsaw.patch`, `jigsaw.decode` and numpy to count, exhaustively and not by sampling, for each of the two 6 x 6 tori in `data/patterns/` and each decoder: the number of (position, turn, flipped cell) cases that are wrong, rejected and correct, where the read is a 4 x 4 patch and the single-window decoder reads the window at offset (0, 0). There are 36 x 4 x 16 = 2,304 cases per torus. Print a table. Then read `results/sim_dense.csv` and state whether the `forced1` proportions are consistent with your exact proportions (inside the Wilson 95 percent interval). Return the table and the verdict."
- Critical reader, a second fresh subagent with `scientific-critical-thinking`: "Read `docs/jigsaw/S2_experiments.md` (design section) and `results/sim_summary.md`. List every sentence in the summary that claims more than the data support, and every prediction whose test could not have failed. Return a list."
- Do not let subagents start the full 20,000-read runs in parallel with each other on the same machine; run them one after the other from the main session.

### What could go wrong

| If | Then |
|---|---|
| A strong-form row has a wrong read with at most one misread cell | Contradiction of the proposition. Most likely a bug in `count_misread` or the turn convention. Stop, keep the saved frame, debug systematically, and report whatever the cause is |
| The puzzle sweep shows wrong reads at 6 pixels per cell for both patterns | Expected to be possible: these are multi-cell misreads. Report them. Prediction 3 says "rare", so give the rate |
| Strong form is worse than the control on multi-error reads | This was already observed in the earlier simulation (38 against 29 percent on the 3 x 3 pair). Report it plainly; the paper lists it |
| The control corner has no distance-1 pairs | Follow E6; the paper needs to say which corner was used and why |
| The full cross is too slow | Ask the author. Do not reduce `n` or drop levels on your own |

### Definition of done

Both CSVs committed with a clean-tree commit hash; summary and figures generated from them; exhaustive verifier agrees; critical-reader findings answered in the handoff note; pull request open.
