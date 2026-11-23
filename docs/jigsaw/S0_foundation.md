# S0 Foundation

> **v2 update (23 Nov): DONE.** Built in chat to CONTRACTS v2 (35 jigsaw pieces, 10 x 10 cells, 72 x 52 back grid). Constants, `Read` in front coordinates, `GridRead`, the new reject reasons and the four pattern files are in place; `tests/test_types.py` and `tests/test_patch.py` pass. The tasks below describe the v1 plan and are kept for the record. On your PC run `uv sync --extra dev --extra print` then `uv run pytest`; if Windows differs, fix only S0 files and note it in `handoff/HANDOFF_S0.md`.

| | |
|---|---|
| Terminal | Opus 5.5 (or Fable 5.2), effort high, Ultracode off |
| Branch and worktree | work directly on `main`; no worktree, because every other workstream branches from the result |
| Depends on | nothing |
| Blocks | every other workstream |
| Owns | `CLAUDE.md`, `pyproject.toml`, `.gitignore`, `.github/workflows/ci.yml`, `data/patterns/`, `jigsaw/__init__.py`, `jigsaw/types.py`, `jigsaw/fakes.py`, `jigsaw/patch.py`, first version of `jigsaw/decode.py`, `jigsaw/vision.py`, `jigsaw/render.py`, and their tests |
| Skills | `karpathy-guidelines`, `test-driven-development`, `verification-before-completion`, `engineering:code-review` (final review subagent) |

---

## Spec

### Problem

Five terminals will write code at the same time. Without a shared skeleton and fixed interfaces they will invent incompatible types, duplicate the patch loader, and block each other. The prototype from 11 Nov works but lives in a zip, uses a random stand-in patch in its tests, and does not match the interfaces in `CONTRACTS.md`.

### Goals

1. `import jigsaw` works on a clean Windows 11 machine with Python 3.12 and no robot, and `pytest` passes.
2. Every type, function and fake listed in `CONTRACTS.md` sections 2 to 4 exists with the stated signature, for the parts assigned to S0.
3. The four pattern files are in the repository with checksums, and a test proves their distances.
4. The prototype's decoder, vision reader and renderer run against the real 30 x 48 patch with the contract signatures.
5. CI runs lint and tests on every push.

### Non-goals

- No new behaviour beyond the prototype. The single-window decoder, wrap-around tables and vision hardening belong to S1.
- No robot, voice or viewer code. Not even stubs beyond the Protocols and fakes.
- No packaging for PyPI or Hugging Face. The app runs from the repository on the laptop.

### Requirements

| # | Requirement | Acceptance |
|---|---|---|
| F1 | `pyproject.toml` with core dependencies (`numpy`, `opencv-python`) and one optional group per workstream (`robot`, `voice`, `viewer`, `experiment`, `print`, `dev`) | `uv sync --extra dev` succeeds; `uv run python -c "import jigsaw"` prints nothing and exits 0 |
| F2 | `jigsaw/types.py` exactly as in `CONTRACTS.md` section 2 | A test imports every name |
| F3 | `jigsaw/patch.py` with `load_torus`, `cut_patch`, `verify`, `piece_cells` | Tests below pass |
| F4 | Pattern files copied and checksummed | `verify` gives min distance 2 for both strong files and 1 for both control files; the puzzle patch has 1,144 windows and 4,576 turned windows |
| F5 | Prototype `decode`, `vision`, `render` moved in and adapted to the contract signatures | All 40 pieces at all 4 turns decode correctly; all 5,760 single-cell flips are rejected; 400 rendered reads give 0 wrong |
| F6 | `jigsaw/fakes.py` | Each fake satisfies its Protocol under `isinstance` checks with `runtime_checkable`, or a structural test |
| F7 | CI workflow: `ruff check`, `pytest -q` on Windows and Ubuntu, Python 3.12 | Green on the first push |
| F8 | `CLAUDE.md` at the repository root, copied from `docs/jigsaw/CLAUDE.md` | File exists and is identical |

### Open questions

| Question | Who | Blocking |
|---|---|---|
| Exact file names of the two control patterns | S0 finds them in `research/otorus/scripts/run_camera.py` | Yes for F4 |
| Is the research code (`research/otorus`) copied into this repository or left in the other folder? | Author | No. Default: leave it, copy only the four pattern files |

---

## Plan

**Goal:** a repository in which `uv run pytest -q` passes and all Wave 1 terminals can start.

**Architecture:** one flat Python package `jigsaw`. Core modules are pure NumPy and OpenCV. Hardware sits behind the four Protocols in `types.py`.

### Task 1: Repository skeleton

- [ ] Confirm the working tree: `git status` in `C:\Users\TJ\Documents\GitHub\COMP_5112_Research_Paper`. If it is not clean, stop and ask.
- [ ] Add `.gitignore` entries: `.venv/`, `__pycache__/`, `.worktrees/`, `results/frames/`, `node_modules/`, `viewer-ui/dist/`, `*.onnx`. Commit this first, so later worktrees are ignored.
- [ ] Create `pyproject.toml`:

```toml
[project]
name = "jigsaw"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["numpy>=2.2", "opencv-python>=4.10"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6", "hypothesis>=6"]
experiment = ["matplotlib>=3.9", "scipy>=1.14"]
robot = ["reachy-mini"]            # S3 pins the exact version after the probe
voice = []                         # S4 fills this in
viewer = ["flask>=3"]
print = ["reportlab>=4"]

[tool.setuptools.packages.find]
include = ["jigsaw*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --ignore=tests/robot_live"

[tool.ruff]
line-length = 100
```

- [ ] Run `uv venv --python 3.12` and `uv sync --extra dev`. Expected: an environment with numpy, opencv-python, pytest, ruff, hypothesis.
- [ ] Copy `docs/jigsaw/CLAUDE.md` to the repository root. Commit: `feat(S0): repository skeleton`.

### Task 2: Types and fakes

- [ ] Write `tests/test_types.py`:

```python
import numpy as np
from jigsaw import types as T
from jigsaw.fakes import FakeFrameSource, FakeGestures, FakeAudioOut, FakeAudioIn

def test_constants():
    assert (T.U, T.PIECE_CELLS) == (5, 6)
    assert T.PATCH_ROWS == T.PUZZLE_ROWS * T.PIECE_CELLS == 30
    assert T.PATCH_COLS == T.PUZZLE_COLS * T.PIECE_CELLS == 48

def test_read_is_hashable_and_frozen():
    assert T.Read(1, 2, 3) == T.Read(1, 2, 3)
    assert len({T.Read(1, 2, 3), T.Read(1, 2, 3)}) == 1

def test_fake_frame_source_yields_frames():
    img = np.zeros((4, 4, 3), np.uint8)
    frames = list(FakeFrameSource([img, img]).frames())
    assert len(frames) == 2 and frames[0].image.shape == (4, 4, 3) and frames[0].K is None

def test_fake_gestures_record_calls():
    g = FakeGestures(); g.nod(); g.shake()
    assert g.calls == ["nod", "shake"]

def test_fake_audio():
    out = FakeAudioOut(); out.play(np.zeros(160, np.float32), 16000)
    assert out.played == [(160, 16000)] and out.is_playing() is False
    assert FakeAudioIn([np.ones(3, np.float32)]).read().sum() == 3
    assert FakeAudioIn([]).read() is None
```

- [ ] Run `uv run pytest tests/test_types.py`. Expected: fails with `ModuleNotFoundError: jigsaw`.
- [ ] Write `jigsaw/__init__.py` (empty), `jigsaw/types.py` (copy section 2 of `CONTRACTS.md` exactly), and `jigsaw/fakes.py` (four small classes, about 40 lines).
- [ ] Run the test. Expected: 5 passed. Commit.

### Task 3: Pattern files and patch loader

- [ ] Find the source files. The strong 5 x 5 torus is `research/results/witnesses/u5s4d2_R256C256_seed0.npz` and the strong 3 x 3 torus is `u3v3s4d2_R6C6.txt`. For the two controls, open `research/otorus/scripts/run_camera.py` and read which 256 x 256 orientation-only torus and which 6 x 6 orientation-only torus it loads. The research folder is `C:\Users\TJ\Downloads\Lakehead-MSc\COMP-5112-Research-Methodology\research`; the same files are inside `COMP5112_WhichWayIsUp_everything.zip` in this repository. If `run_camera.py` builds a control pattern in code instead of loading a file, run that code once and save the result. Record what you did in `data/patterns/README.md`.
- [ ] Copy the four files to `data/patterns/` under the names in `CONTRACTS.md` section 7. Write `data/patterns/SHA256SUMS` with the original file names as comments.
- [ ] Write `tests/test_patch.py`:

```python
from pathlib import Path
import numpy as np
import pytest
from jigsaw.patch import load_torus, cut_patch, verify, piece_cells

P = Path(__file__).parent.parent / "data" / "patterns"

def test_all_zero_pattern_fails():
    rep = verify(np.zeros((12, 12), np.uint8), u=5, wrap=False)
    assert rep["min_distance"] == 0

def test_puzzle_patch_is_strong_form():
    patch = cut_patch(load_torus(P / "strong_u5_256.npz"))
    assert patch.shape == (30, 48)
    rep = verify(patch, u=5, wrap=False)
    assert rep == {"windows": 1144, "turned_windows": 4576, "min_distance": 2, "distance1_pairs": 0}

def test_control_patch_is_orientable_only():
    rep = verify(cut_patch(load_torus(P / "orient_u5_256.npz")), u=5, wrap=False)
    assert rep["min_distance"] >= 1          # 4-orientable on this patch
    # distance1_pairs may be 0 on a 30 x 48 corner; the full torus must have some
    full = verify(load_torus(P / "orient_u5_256.npz")[:64, :64], u=5, wrap=False)
    assert full["min_distance"] >= 1

@pytest.mark.parametrize("name,dmin", [("strong_u3_6x6.txt", 2), ("orient_u3_6x6.txt", 1)])
def test_dense_tori(name, dmin):
    rep = verify(load_torus(P / name), u=3, wrap=True)
    assert rep["windows"] == 36 and rep["turned_windows"] == 144 and rep["min_distance"] == dmin

def test_piece_cells():
    patch = cut_patch(load_torus(P / "strong_u5_256.npz"))
    assert np.array_equal(piece_cells(patch, 1, 2), patch[6:12, 12:18])
```

If the 30 x 48 corner of the control torus happens to contain no pair at distance 1, record that in `data/patterns/README.md`: it matters to S2, which then picks a corner of the control torus that does contain such pairs, or reports that none exists.

- [ ] Run the tests (expect failure), then write `jigsaw/patch.py`. `load_torus` reads `.npz` with `np.unpackbits(z["bits"], bitorder="big")[:R*C].reshape(R, C)` and `.txt` as rows of 0 and 1 separated by spaces. `verify` enumerates windows (with wrap-around when `wrap=True`), builds the four turns with `np.rot90`, packs them, and computes the minimum pairwise Hamming distance and the number of pairs at distance 1. A reference implementation that was run on 18 Nov is `scripts/check_patch.py` in the prototype notes; the vectorised loop from the 11 Nov plan (Task 2) also works.
- [ ] Run the tests. Expected: all pass, in under 30 seconds. Commit: `feat(S0): pattern files and patch loader`.

### Task 4: Bring the prototype up to the contracts

- [ ] Unzip `docs/jigsaw/reference/jigsaw_proto.zip` into a temporary folder. Copy `jigsaw/decode.py`, `jigsaw/vision.py`, `jigsaw/render.py` into the package and its two test files into `tests/`.
- [ ] Change signatures to match `CONTRACTS.md`, and nothing else:
  - `decode.py`: remove the local `Read`, `U`, `CELLS` and import from `types`. Rename `decode_piece` to `decode_four` and make it return `Position | Reject` for a `(u+1, u+1)` grid (the origin is the position of the top-left window; drop the piece-boundary check). Add `to_piece`. Keep `front_slot`. Distinguish `Reject("no_match")` (no un-turning fits) from `Reject("ambiguous")` (more than one fits).
  - `vision.py`: `read_cells` returns `CellRead(cells, quad)` or `Reject("no_quad")` or `Reject("low_contrast")`. Remove the `scale` argument from the public signature (keep it as a module constant).
  - `render.py`: rename `scale` to `px_per_cell` in `draw_piece`.
- [ ] Rewrite the prototype tests to use the real patch (fixture `patch` in `tests/conftest.py` loads `strong_u5_256.npz` and cuts 30 x 48) and to assert:

```python
def test_every_piece_every_turn(patch, table):
    for r in range(5):
        for c in range(8):
            for k in range(4):
                cells = np.rot90(piece_cells(patch, r, c), k)
                assert to_piece(decode_four(cells, table, 5)) == Read(r, c, k)

def test_every_single_flip_is_rejected(patch, table):
    n = 0
    for r in range(5):
        for c in range(8):
            for k in range(4):
                base = np.rot90(piece_cells(patch, r, c), k).copy()
                for a in range(6):
                    for b in range(6):
                        cells = base.copy(); cells[a, b] ^= 1
                        assert isinstance(decode_four(cells, table, 5), Reject)
                        n += 1
    assert n == 5760

def test_rendered_round_trip(patch, table):
    rng = np.random.default_rng(0); wrong = rejected = 0
    for _ in range(400):
        r, c = rng.integers(5), rng.integers(8)
        img = photograph(draw_piece(piece_cells(patch, r, c), 40), rng, rng.uniform(0, 360),
                         tilt=0.15, blur=1.0, noise=8.0, size=480, frac=0.45)
        cr = read_cells(img)
        d = to_piece(decode_four(cr.cells, table, 5)) if isinstance(cr, CellRead) else cr
        if isinstance(d, Reject): rejected += 1
        elif (d.row, d.col) != (r, c): wrong += 1
    assert wrong == 0 and rejected <= 20
```

The turn convention needs one check here, because the rendered piece is rotated by an arbitrary angle and the decoder reports a quarter turn. Add an assertion that for `angle_deg` in `{0, 90, 180, 270}` with `tilt=0` the decoded turn follows the convention in `CLAUDE.md` (counter-clockwise as seen in the image). If the prototype's renderer rotates the other way, fix the renderer's sign, not the decoder, and say so in the handoff note.

- [ ] Run `uv run pytest`. Expected: every test passes. Commit: `feat(S0): prototype core adapted to contracts`.

### Task 5: CI

- [ ] Add `.github/workflows/ci.yml`: matrix `windows-latest` and `ubuntu-latest`, Python 3.12, `pip install -e .[dev]`, `ruff check .`, `pytest -q`. Push and confirm the run is green with `gh run watch`.

### Task 6: Review and handoff

- [ ] Dispatch one review subagent (see below). Fix what it finds that is inside S0's files.
- [ ] Write `docs/jigsaw/handoff/HANDOFF_S0.md` with the test output, the names of the control files, whether the control patch has distance-1 pairs, and the turn convention result.
- [ ] Push `main`. Tell the author that Wave 1 can start.

### Subagent use

- Task 3, one Explore subagent: "In `<research folder>/otorus/scripts/run_camera.py` and `results/README.md`, find which seven tori the simulated camera uses. Return the file name or the constructing code for (a) the 256 x 256 orientation-only 5 x 5 torus and (b) the 6 x 6 orientation-only 3 x 3 torus of the size-matched pair. Quote the lines."
- Task 6, one general-purpose subagent with the `engineering:code-review` skill: "Review the diff of `main` since commit `<first S0 commit>`. Check every signature against `docs/jigsaw/CONTRACTS.md` sections 2 to 4 and list each mismatch. Check that no module under `jigsaw/` imports anything outside numpy, cv2 and the standard library. Do not edit files. Return a list of findings with file and line."
- Nothing in S0 runs in parallel. The tasks are short and each depends on the previous one.

### What could go wrong

| If | Then |
|---|---|
| The control torus is built in code, not stored | Run the code with its recorded seed, save the array, and note the seed |
| `verify` on the full 256 x 256 torus is slow | Only verify patches and the two 6 x 6 tori in tests; the full torus was verified in the research code |
| The Windows CI job fails on OpenCV | Switch the dependency to `opencv-python-headless` for CI only and note it |
| The turn convention test fails | Fix the renderer sign, rerun, and flag it in the handoff note, because S5 (printing) and S4 (phrases) depend on it |

### Definition of done

`uv run pytest -q` passes locally and in CI; the contract review reports no mismatches; `HANDOFF_S0.md` is written; `main` is pushed.
