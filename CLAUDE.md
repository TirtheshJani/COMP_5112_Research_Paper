# CLAUDE.md: rules for the Reachy Jigsaw code

S0 copies this file to the repository root. Every session reads it before doing anything else.

## What this repository is

Software for a COMP 5112 research paper. A Reachy Mini Wireless reads the back of a jigsaw piece and says where it goes. The numbers this code produces are reported in a paper, so correctness and reproducibility matter more than features.

## Before you write code

1. Read `docs/jigsaw/CONTRACTS.md` and the workstream file you were given.
2. Load these skills: `karpathy-guidelines`, `test-driven-development`, `verification-before-completion`. Load `systematic-debugging` when a test fails for a reason you do not understand.
3. State your assumptions in one short list. If the workstream file and the code disagree, stop and ask.

## Karpathy guidelines, applied here

- Think before coding. If a requirement has two readings, write both down and ask. Do not pick one silently.
- Simplicity first. No plugin systems, no configuration files, no abstract base classes beyond the Protocols in `jigsaw/types.py`. A function with arguments is the default.
- Surgical changes. Edit only files your workstream owns. If you see a problem in another workstream's file, write it in your handoff note.
- Goal-driven. Every task in a plan has a command and an expected output. Run the command. Paste the real output into the handoff note.

## Hard rules

1. Never change a function signature, dataclass or CSV column listed in `CONTRACTS.md`. Request a change in `docs/jigsaw/handoff/CONTRACT_CHANGE_<ID>.md`.
2. The core modules (`types`, `patch`, `geometry`, `decode`, `vision`, `render`, `reader`, `pose`, `stable`) never import `reachy_mini`, an audio library, Flask, or anything that needs hardware. Tests for them run on a machine with no robot.
3. Imports of `reachy_mini`, `piper`, `faster_whisper` and `onnxruntime` are inside functions or inside the adapter modules named in the contracts, so that `import jigsaw` works without them.
4. Every experiment script takes a `--seed`, writes a CSV whose last columns are `seed` and `commit`, and refuses to run with uncommitted changes unless `--allow-dirty` is passed.
5. Never tune a threshold to remove a wrong read. A wrong read on a strong-form pattern with at most one misread cell contradicts a proposition in the paper. Save the frame to `results/findings/`, stop, and report.
6. One owner for robot motion and one owner for robot audio output: only `jigsaw/robot/reachy.py` calls `goto_target`, and only `jigsaw/robot/reachy.py` calls `push_audio_sample`. The probe `scripts/probes/p4_nod.py` is the one exception, and it moves nothing without `--move`.
7. Do not call `wake_up()`, `goto_sleep()`, `play_move()`, `play_sound()`, `start_head_tracking()` or `enable_wobbling()`. They start daemon-side motion or audio that conflicts with ours.
8. Anything learned from documentation and not yet run on the robot is marked `# UNVERIFIED:` with the source file. Remove the mark only after a probe in `scripts/probes/` has run and its output is saved in `results/probes/`.
9. No paid or cloud services. Speech synthesis and recognition run locally.
10. No em dashes anywhere.

## Conventions

- Python 3.12, `uv` for the environment, `pytest` for tests, `ruff` for lint. Type hints on public functions.
- Images inside this code are BGR `uint8` (OpenCV order). Adapters convert at the boundary.
- A quarter turn is counter-clockwise as seen in the image. `turn = k` means the camera sees the piece back rotated by `k` quarter turns counter-clockwise from its upright printed orientation.
- Rows and columns are zero-based in code and one-based in anything spoken or displayed.
- The back of the puzzle is a mirror of the front: front lattice cell `(i, j)` carries `G[i + 1, 49 - j + 1]` (`patch.front_to_g`). A `Read` is already in front coordinates (row 0 is the top row of the picture), so nothing downstream mirrors again.
- The camera reads pieces over a strongly coloured reading mat (green in the tests). Without it `read_grid` rejects; it never guesses.
- Commit messages: `feat(S1): ...`, `test(S1): ...`, `fix(S1): ...`, `docs(S1): ...`.

## Token budget

- This file is loaded automatically. Do not read it again, or its copy in docs/jigsaw.
- Read only the files your prompt lists. In a spec, read the v2 box and the Spec section; skip the v1 Plan (your prompt replaces it).
- Send lookups in the SDK, in ../rocky_mini or in long files to the `sdk-scout` subagent (Haiku). Send reviews to the `reviewer` subagent (Sonnet).
- While working, run one test file: `uv run pytest tests/test_<x>.py`. Run the full suite once per finished task. pytest is already quiet (`-q` in pyproject); adding `-q` hides the summary line.
- Never print or read .npz, .pdf, .png, .jpg or .zip files. Open an image only to debug a named failure.
- After each finished task: commit, then `/compact keep the task list status, file names and open questions`.
- Load only the skills your prompt lists. Load `systematic-debugging` only when a test fails for a reason you cannot see.

## When you finish a workstream

Write `docs/jigsaw/handoff/HANDOFF_<ID>.md` with: what was built, the exact commands run and their output, anything still `UNVERIFIED`, anything you noticed outside your files, and open questions. Then run the review subagent described in your workstream file and attach its findings.
