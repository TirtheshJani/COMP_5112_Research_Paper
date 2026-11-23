# Orchestrator decisions (Part A, 23 Nov 2026)

Each entry: what was decided, why, and what would reverse it.

1. **HANDOFF_S7.md had no uncommitted edit.** The ground truth listed one, but `git status` in .worktrees/s7-viewer was clean and the handoff is in commit 23263c0. Nothing to commit.
2. **`uv sync --inexact`, with the viewer extra added.** A plain `uv sync --extra dev --extra print --extra voice` would have uninstalled reachy-mini 1.15.0 from the main venv, and the merged S7 server tests need flask. Reversal: none needed; the lock file is the same either way.
3. **Voice tests now run.** Copied en_US-lessac-medium.onnx and .onnx.json from ../rocky_mini into assets/voice/ (ignored by assets/voice/.gitignore). piper-tts 1.8.0 installed. Full suite after merging S7 and S4: 115 passed, 0 skipped; tests/test_voice_tts.py: 5 passed.
4. **Waves run as Workflow scripts** (implement, then the `reviewer` agent, then a fixer on the same model), with the models the plan gives. Subagents cannot spawn sdk-scout, so they do SDK lookups with narrow greps.
5. **S2 may add statsmodels to the `experiment` extra.** P4 Task 4 tests `wilson` against statsmodels but pyproject.toml is outside S2's edit list. Test-only dependency.
6. **The orchestrator, not the S2 agent, launches the full n = 300 run** in the background, so its completion is tracked and the figures agent starts only when it has finished. The pilot writes to separate `*_pilot.csv` files.
7. **K correction scope (S3).** The given formula (fy = 1.2 fy_sdk, cy = (3.6 cy_sdk - 216) / 3) is applied to 720-row frames only, marked UNVERIFIED. Its arithmetic matches a centred 3840 x 2160 crop of the 2592-row sensor scaled down 3x, which no probe has confirmed. Reversal: a Friday measurement of K at 720p disagrees.
8. **p5 must report a settling time** (`settling_time_s:` line in results/probes/motion_media.md), because Part B step 3 copies it into app.py in place of the 0.5 s constant.
