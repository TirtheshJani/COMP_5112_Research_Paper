# S1 Core: decoders, vision, pose, renderer

> **v2 update (23 Nov): DONE for the reading-mat setup.** The v1 plan below (framed quad, `read_cells`, `decode_four`, `to_piece`) no longer applies. What exists instead: `decode_single` and `decode_grid` (every complete 5 x 5 window must agree on one placement, piece from the centroid), `vision.read_grid` (mat silhouette, grid angle from the 4-fold gradient average, pitch and phase from edge profiles, line-by-line fits, homography, cell sampling with a visibility mask), `render.piece_back` and `render.photograph`, `pose.piece_pose`, `reader.PieceReader`. Results are in `handoff/HANDOFF_S1.md`: 0 wrong reads in every test, including 875 misregistered pieces and every single-cell misread.
>
> **Remaining (P1, Opus 5.5 xhigh):** reading without a mat (clutter behind a held piece). Today `read_grid` rejects every such frame (30 of 30 in the test), which is safe but limits the demo. Approach to try: accept a cell only if its four borders show the gray grid line or a black/white step, take the largest connected set, fill holes. Acceptance: on `background="clutter"` frames, 0 wrong and at most 20 percent rejected. Never relax `decode_grid` to get there.

| | |
|---|---|
| Terminal | Opus 5.5, effort high, Ultracode off |
| Branch and worktree | `feat/s1-core` in `.worktrees/s1-core` |
| Depends on | S0 merged |
| Blocks | S2 (experiments), S6 (app) |
| Owns | `jigsaw/decode.py`, `jigsaw/vision.py`, `jigsaw/render.py`, `jigsaw/pose.py`, `tests/test_decode.py`, `tests/test_vision.py`, `tests/test_render.py`, `tests/test_pose.py` |
| Must not edit | `jigsaw/types.py`, `jigsaw/patch.py`, `jigsaw/fakes.py` |
| Skills | `karpathy-guidelines`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `engineering:code-review` |

---

## Spec

### Problem

The paper's third research question compares two patterns under two decoders. After S0 only the four-window decoder exists, only for open patches, and only for 5 x 5 windows. The vision reader has been tested on clean synthetic images with a plain background, not on frames with a hand, a cluttered room and lens distortion. The experiments in S2 and the app in S6 need the missing pieces, and they need them to be correct, because a decoder bug would be reported in the paper as a property of the pattern.

### Goals

1. A single-window decoder and a four-window decoder that both work for any window size `u`, on open patches and on tori.
2. The decoders satisfy the paper's Proposition (single misreads are rejected on strong-form patterns) for every pattern in `data/patterns/`, checked exhaustively.
3. A vision reader that finds a piece among other dark objects, at any in-plane angle, and returns the quad it used.
4. A pose estimate (rotation and translation of the piece relative to the camera) for the viewer.
5. A renderer that can produce the conditions S2 sweeps: pixels per cell, tilt, blur, noise, and a cluttered background.

### Non-goals

- No error correction. A read with a wrong cell is rejected, never repaired.
- No detection of several pieces in one frame.
- No learning-based detector. Thresholding and contours only, as described in the paper.
- No speed work. The table lookup already runs at millions of decodes per second.

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| C1 | P0 | `build_table(pattern, u, wrap)` supports tori (`wrap=True`) | For both 6 x 6 tori, the table has 36 entries for the strong torus; for the control torus it has 36 entries or raises only if two upright windows are equal |
| C2 | P0 | `decode_single(window, table)` | For every turned window of every pattern file, returns the true `Position`. On strong-form patterns, every single-cell flip of every turned window is rejected |
| C3 | P0 | `decode_four(cells, table, u)` generalised to any `u` and to tori (positions compared modulo the torus size) | For the 6 x 6 tori, every 4 x 4 patch at every turn decodes to its position; on the strong torus every single flip is rejected |
| C4 | P0 | Decoders never raise on any binary input | Hypothesis test with random arrays of the right shape |
| C5 | P0 | `read_cells` picks the piece, not the largest dark blob | Rendered frames with a dark rectangle, a dark circle and a hand-coloured blob beside the piece still decode: at most 5 percent rejected, 0 wrong, over 400 frames |
| C6 | P0 | `read_cells` returns `Reject("low_contrast")` when border and margin are less than 40 grey levels apart | Test with a washed-out image |
| C7 | P0 | Optional undistortion: `read_cells(gray)` takes an image that the caller has already undistorted; `vision.undistort(image, K, D)` is provided | Round trip on a synthetically distorted image |
| C8 | P1 | `piece_pose(quad, K, D, side_mm)` using `cv2.solvePnP` with `SOLVEPNP_IPPE_SQUARE` | Synthetic projection at known pose recovers translation within 2 percent and rotation within 2 degrees |
| C9 | P0 | `render.photograph` gains `background` (plain or cluttered) and exact control of pixels per cell | A test measures the rendered quad side and checks it against `px_per_cell * 8` within 3 percent at zero tilt |
| C10 | P0 | `render.draw_patch_read(pattern, i, j, n, px_per_cell)` draws an `n x n` read of a torus with border and margin, for the dense-tori experiment | Round trip through `read_cells(gray, n=4)` on the 6 x 6 tori |

### Design notes

- How `read_cells` chooses the quad. The piece is the only dark quadrilateral that contains a light ring just inside it. Candidates are the convex four-sided contours above a minimum area; each is warped to a square and scored by the contrast between the border band and the margin band on all four sides. Take the best score above the threshold. This replaces "largest dark blob" and is the only change to the algorithm.
- Why the single-window decoder needs its own table. `decode_single` tries the four un-turnings of the window and looks each up in the table of upright windows. That is the same as looking the window up among all turned windows, which is what the paper states. Exactly one hit is a `Position`; no hit is `Reject("no_match")`; more than one is `Reject("ambiguous")` and can only happen on a pattern that is not 4-orientable.
- Which window does the single-window decoder read in the experiments? The window at offset `(0, 0)` of the read grid after sampling, as in the 18 Nov pilot. That choice is made in S2, not here.
- Tori. With `wrap=True`, positions are compared modulo `(R, C)`, and `to_piece` is not used.

### Open questions

| Question | Who | Blocking |
|---|---|---|
| Does the real camera need undistortion at the working distance? | S3 focus check | No. C7 is provided either way; S6 decides whether to call it |
| Minimum quad area as a fraction of the frame | S1 picks 0.5 percent, S3 focus check may revise | No |

---

## Plan

**Goal:** all ten requirements pass their tests, and the branch is ready for S2 and S6 to import.

### Task 1: Worktree and baseline

- [ ] Use the `using-git-worktrees` skill: `git worktree add .worktrees/s1-core -b feat/s1-core`, then `uv sync --extra dev` inside it.
- [ ] Run `uv run pytest -q`. Expected: the S0 tests pass. If any fail, stop and report.

### Task 2: Tables for tori (C1)

- [ ] Add to `tests/test_decode.py`:

```python
@pytest.fixture(scope="module")
def strong3():  return load_torus(P / "strong_u3_6x6.txt")
@pytest.fixture(scope="module")
def orient3():  return load_torus(P / "orient_u3_6x6.txt")

def test_torus_table_has_one_entry_per_position(strong3):
    t = build_table(strong3, u=3, wrap=True)
    assert len(t) == 36 and set(t.values()) == {(i, j) for i in range(6) for j in range(6)}

def test_open_table_unchanged(patch):
    assert len(build_table(patch, u=5)) == 26 * 44
```

- [ ] Run (fails on the `wrap` argument). Implement `wrap` by indexing with `np.take(..., mode="wrap")` on both axes. Run (passes). Commit.

### Task 3: Single-window decoder (C2)

- [ ] Add tests:

```python
def turned_windows(pattern, u, wrap):
    R, C = pattern.shape
    rows = range(R) if wrap else range(R - u + 1)
    cols = range(C) if wrap else range(C - u + 1)
    for i in rows:
        for j in cols:
            w = pattern.take(range(i, i + u), 0, mode="wrap").take(range(j, j + u), 1, mode="wrap")
            for k in range(4):
                yield i, j, k, np.rot90(w, k)

@pytest.mark.parametrize("fix,u,wrap", [("patch", 5, False), ("strong3", 3, True), ("orient3", 3, True)])
def test_single_decodes_every_turned_window(fix, u, wrap, request):
    pattern = request.getfixturevalue(fix); table = build_table(pattern, u, wrap)
    for i, j, k, w in turned_windows(pattern, u, wrap):
        assert decode_single(w, table) == Position(i, j, k)

@pytest.mark.parametrize("fix,u,wrap", [("patch", 5, False), ("strong3", 3, True)])
def test_single_rejects_every_flip_on_strong_form(fix, u, wrap, request):
    pattern = request.getfixturevalue(fix); table = build_table(pattern, u, wrap)
    for i, j, k, w in turned_windows(pattern, u, wrap):
        for a in range(u):
            for b in range(u):
                x = w.copy(); x[a, b] ^= 1
                assert isinstance(decode_single(x, table), Reject)

def test_single_is_fooled_on_the_control_torus(orient3):
    table = build_table(orient3, 3, True); wrong = 0
    for i, j, k, w in turned_windows(orient3, 3, True):
        for a in range(3):
            for b in range(3):
                x = w.copy(); x[a, b] ^= 1
                d = decode_single(x, table)
                wrong += isinstance(d, Position) and d != Position(i, j, k)
    assert wrong > 0     # the control pattern has pairs at distance 1
```

The last test documents the effect the paper measures. Print the count; S2 will report the rate.

- [ ] Run (fails: no `decode_single`). Implement in about 12 lines. Run (passes). The patch test loops over 4,576 x 25 flips and should finish in a few seconds. Commit.

### Task 4: Four-window decoder for any `u` and for tori (C3, C4)

- [ ] Add tests: every 4 x 4 patch of both 6 x 6 tori at every turn decodes to its `Position`; every single flip on the strong torus is rejected; and a Hypothesis test:

```python
@given(st.integers(0, 2**36 - 1))
def test_four_never_raises(bits):
    cells = np.array([(bits >> n) & 1 for n in range(36)], np.uint8).reshape(6, 6)
    assert isinstance(decode_four(cells, TABLE, 5), (Position, Reject))
```

- [ ] `decode_four` needs the torus size to compare positions modulo `(R, C)`. Do not change the contract signature. Store the size in the table under a reserved key, or return a small `Table` subclass of `dict` with attributes `shape` and `wrap`; the second is cleaner and still satisfies `dict[bytes, tuple[int, int]]`. State the choice in the handoff note.
- [ ] Run, implement, run. Confirm the S0 tests (`test_every_piece_every_turn`, `test_every_single_flip_is_rejected`) still pass unchanged. Commit.

### Task 5: Renderer options (C9, C10)

- [ ] Tests first: measured quad side against `8 * px_per_cell`; `draw_patch_read` round trip for `n=4`; a cluttered background contains at least three dark blobs larger than 1 percent of the frame (so the vision test below is meaningful).
- [ ] Implement `background="clutter"` with a seeded random set of dark rectangles, a dark disc and a skin-toned (mid-grey in the grey image) blob touching one edge of the piece's margin, never covering cells. Implement `px_per_cell` by computing `frac` from `size`. Keep the old arguments working, because S0's tests use them.
- [ ] Run. Commit.

### Task 6: Vision hardening (C5, C6, C7)

- [ ] Tests first:

```python
def test_reads_piece_among_clutter(patch, table):
    rng = np.random.default_rng(1); wrong = rejected = 0
    for _ in range(400):
        r, c = int(rng.integers(5)), int(rng.integers(8))
        img = photograph(draw_piece(piece_cells(patch, r, c), 16), rng, rng.uniform(0, 360),
                         tilt=0.15, blur=1.0, noise=8.0, size=720, frac=None,
                         px_per_cell=16, background="clutter")
        cr = read_cells(img)
        d = to_piece(decode_four(cr.cells, table, 5)) if isinstance(cr, CellRead) else cr
        rejected += isinstance(d, Reject)
        wrong += isinstance(d, Read) and (d.row, d.col) != (r, c)
    assert wrong == 0 and rejected <= 20

def test_low_contrast_is_rejected():
    img = np.full((480, 480), 128, np.uint8); img[100:300, 100:300] = 110
    assert read_cells(img) == Reject("low_contrast") or read_cells(img) == Reject("no_quad")
```

- [ ] Run. The clutter test is expected to fail with the S0 reader (it picks the largest blob). Use `systematic-debugging`: save three failing frames to a temporary folder and look at which contour was chosen before changing code.
- [ ] Implement the candidate scoring described in the design notes. Keep `find_quad` returning one quad.
- [ ] If any read in the clutter test is wrong (not rejected, wrong), stop. Save the frame to `results/findings/` and report. Do not adjust thresholds to make it pass.
- [ ] Add `undistort(image, K, D)` as a thin wrapper over `cv2.undistort` with a round-trip test using `cv2.initUndistortRectifyMap` on a synthetic image. Commit.

### Task 7: Pose (C8)

- [ ] Test: project the four corners of a 40 mm square at a known pose with `cv2.projectPoints` and a made-up `K`; `piece_pose` returns `rvec`, `tvec` within tolerance. A second test: `K=None` returns `None`.
- [ ] Implement with `cv2.solvePnP(obj, quad, K, D, flags=cv2.SOLVEPNP_IPPE_SQUARE)`. The object points must be in the order that flag requires (top-left, top-right, bottom-right, bottom-left, with the origin at the centre). Commit.

### Task 8: Review, handoff, merge request

- [ ] Run the full suite and `ruff check`. Paste the output into `HANDOFF_S1.md`, with the count printed by `test_single_is_fooled_on_the_control_torus`.
- [ ] Dispatch the review subagent. Address findings inside S1's files.
- [ ] Push the branch and open a pull request. Do not merge it yourself.

### Subagent use

Most of S1 is one chain of reasoning about conventions, so keep it in the main session. Two places where subagents help:

- Tasks 5 and 7 are independent of Tasks 2 to 4 and of each other (different files). After Task 1, you may dispatch two general-purpose subagents in parallel while the main session does Tasks 2 to 4:
  - "In worktree `.worktrees/s1-core`, implement requirement C9 and C10 from `docs/jigsaw/S1_core_decode_vision.md` in `jigsaw/render.py` and `tests/test_render.py` only. Follow `CLAUDE.md`. Write tests first. Do not edit any other file. Return the test output and a summary of the function signatures you added."
  - "In worktree `.worktrees/s1-core`, implement requirement C8 in `jigsaw/pose.py` and `tests/test_pose.py` only. ..." (same structure).
  Task 6 starts after the renderer subagent returns, because its test uses the cluttered background.
- Task 8 review subagent, with `engineering:code-review`: "Review the diff between `main` and `feat/s1-core`. Focus on: (1) any place where a decoder could return a `Position` for an input at Hamming distance 1 from a true turned window on a strong-form pattern; (2) off-by-one errors in wrap-around indexing; (3) the corner order passed to `solvePnP`; (4) thresholds that look tuned to a test. Do not edit files. Return findings with file and line."

### What could go wrong

| If | Then |
|---|---|
| The control 6 x 6 torus has two equal upright windows | It is not 4-orientable and is the wrong file. Stop and report to the author; S0 picked the wrong control |
| Candidate scoring is slow on 720p frames | Limit to the 10 largest candidates. Do not downscale the image, because that changes pixels per cell |
| Clutter test rejects more than 5 percent | Report the rate. A high reject rate is acceptable for the paper as long as wrong is 0; ask before spending time on it |
| The turn reported for a rendered piece disagrees with the convention | The renderer and decoder disagree on rotation direction. Find which one matches `CLAUDE.md` and fix the other. This must be settled here, before S4 and S5 use it |

### Definition of done

All S0 and S1 tests pass; no wrong read in any test; review findings addressed; `HANDOFF_S1.md` written; pull request open.
