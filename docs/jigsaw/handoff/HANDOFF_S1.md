# HANDOFF S1 (23 Nov 2026, built in chat)

Built: `jigsaw/geometry.py` (piece outlines, shared with S5), `decode.py` (`Table`, `build_table` with wrap, `decode_single`, `rot_affine`, `decode_grid`), `vision.py` (`paper_mask`, `read_grid`, `undistort`), `render.py` (`piece_back`, `photograph`), `pose.py` (`piece_pose` from the grid homography), `reader.py` (`PieceReader`).

Decoder results (`tests/test_decode.py`):
- every turned window of the back grid and both 6 x 6 tori decodes to its position;
- every single-cell flip of every turned window on the strong patterns is rejected (back grid: 326,400 flips);
- the control 6 x 6 torus is fooled by single flips (the effect the paper measures);
- all 35 pieces at all 4 turns decode to the right piece and turn;
- all 35 pieces decode with the back printed up to 3 mm off the cut (6 offsets each);
- one misread cell anywhere on a piece never gives a wrong piece (35 pieces, every visible cell);
- random grids are rejected; Hypothesis: decoders never raise.

Reader results on rendered photos (`tests/test_vision.py`, rerun on 23 Nov):
```
mat, 12-28 px/cell, tilt<=0.08, blur<=1.2, noise<=8: correct 150, rejected 0, wrong 0, wrong turn 0
same with a finger across the piece:                  correct 49, rejected 11, wrong 0, wrong turn 0
9-11 px per cell:                                     correct 40, rejected 0, wrong 0, wrong turn 0
clutter, no mat:                                      correct 0, rejected 30, wrong 0, wrong turn 0
```
Earlier sweep: 8 px per cell gave 59 of 60 correct, 1 rejected, 0 wrong. About 145 ms per 720 x 720 frame.

Design choices: the piece must be over a coloured mat (paper = low saturation or dark; the mat and skin are saturated); cells count as visible only if the whole cell lies inside the eroded silhouette, the centre is uniform and the value is not close to the threshold. Thresholds were set once from first principles and not tuned to remove a wrong read (there were none).

UNVERIFIED: everything about real camera frames (colour of white paper under room light, glare, autofocus). Run `scripts/probes/p3_live_read.py` with printed pieces.
Open: reading without a mat (S1 v2 box). Pose is tested on synthetic projections only.
