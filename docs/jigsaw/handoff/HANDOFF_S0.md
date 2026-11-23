# HANDOFF S0 (23 Nov 2026, built in chat)

Built: `pyproject.toml` (groups dev, experiment, robot, voice, viewer, print), `CLAUDE.md` at the root, `.gitignore`, `.github/workflows/ci.yml` (Ubuntu and Windows, Python 3.12, ruff and pytest), `jigsaw/types.py` (CONTRACTS v2), `jigsaw/fakes.py`, `jigsaw/patch.py`, `data/patterns/` with SHA256SUMS.

Pattern files: `strong_u5_256.npz` = `u5s4d2_R256C256_seed0.npz` (byte-identical to the file the print used), `orient_u5_256.npz` = `u5s4d1_R256C256_seed0.npz`, `strong_u3_6x6.txt` = `u3v3s4d2_R6C6.txt`, `orient_u3_6x6.txt` = `u3v3s4d1_R6C6.txt`. The control names come from the arguments of `research/otorus/scripts/run_camera.py` and the witness folder in `COMP5112_WhichWayIsUp_everything.zip`.

Checked (`tests/test_patch.py`): the printed 72 x 52 back grid has 3264 windows, 13056 turned windows, all distinct, no pair at distance 1. The 72 x 52 corner of the control torus has distance-1 pairs (min distance 1). Both 6 x 6 tori: 36 windows, 144 turned windows, min distance 2 and 1. Front/back mapping round-trips for every cell.

Command and output (cloud workspace, Python 3.12.3, numpy 2.x, OpenCV 5.0.0):
```
uv run pytest -q   ->  38 passed in 57.47s
ruff check .       ->  All checks passed!
```
Not done here: CI has not run on GitHub (nothing pushed); the Windows run is untested. Turn convention: checked in `tests/test_vision.py::test_turn_convention` (render at 0, 90, 180, 270 degrees counter-clockwise gives turn 0 to 3).
