# CONTRACTS.md: frozen interfaces (v2, 23 Nov 2026)

v2 replaces the framed square pieces of v1 with the printed jigsaw: 35 real jigsaw pieces (5 columns x 7 rows) cut from one sheet, picture on the front, one continuous strong-form grid on the back, no frames. S0 and S1 have been built to this version and their tests pass (see `handoff/HANDOFF_S0.md` and `HANDOFF_S1.md`). Everything below exists in code unless marked "to build".

After this point these interfaces change only through `handoff/CONTRACT_CHANGE_<ID>.md`.

## 1. Repository layout and ownership

```
COMP_5112_Research_Paper/
  CLAUDE.md                         S0
  pyproject.toml                    S0 (others add dependencies only in their own optional group)
  .github/workflows/ci.yml          S0
  data/patterns/                    S0   four pattern files and SHA256SUMS
  print/                            S5   picture_portrait.png, reachy_debruijn_jigsaw.pdf, preview
  jigsaw/
    types.py fakes.py patch.py      S0   frozen
    geometry.py                     S5   piece outlines (shared with render and tests)
    decode.py                       S1
    vision.py render.py pose.py     S1
    reader.py                       S1   frame -> decision in one call
    printing.py                     S5
    experiment/                     S2   to build: sweep.py contrast.py stats.py figures.py
    robot/                          S3   to build: reachy.py sources.py
    voice/                          S4   to build: phrases.py tts.py commands.py stt.py
    stable.py app.py protocol.py    S6   to build
    viewer/                         S7   to build: server.py events.py static/
  viewer-ui/                        S7   to build: React 19 + TypeScript + Vite + three
  scripts/probes/                   S3   p1_status.py p2_camera.py p3_live_read.py p4_nod.py (written)
  scripts/                          make_print.py make_picture.py; each workstream adds only its own
  tests/                            one file per module, owned with the module
  results/                          written by scripts, never by hand
  docs/jigsaw/                      these documents
```

## 2. Shared types (`jigsaw/types.py`)

```python
U = 5                                     # window side
PIECE_CELLS = 10                          # cells per piece side (piece is 36 mm without knobs)
PUZZLE_ROWS, PUZZLE_COLS = 7, 5           # pieces, as seen on the picture side
MARGIN_CELLS = 1                          # extra printed cells around the puzzle
GRID_ROWS, GRID_COLS = 72, 52             # the printed back grid G, with the margin
CELL_MM = 3.6
PIECE_MM = 36.0

Position(i, j, turn)      # top-left cell of a matched window in G, and the turn
Read(row, col, turn)      # a piece, in FRONT coordinates (row 0 = top row of the picture)
Reject(reason)            # reason in: no_grid, low_contrast, no_window, no_match, ambiguous,
                          #            inconsistent, off_puzzle
Decision = Read | Reject
GridRead(cells, mask, H)  # cells (h, w) uint8 1 = black as the camera sees it; mask (h, w) bool,
                          # True where the cell is on the piece and read confidently; H (3, 3) maps
                          # cell coordinates (x = column, y = row; cell centre at +0.5) to image pixels
Frame(image, t, K, D)     # image (H, W, 3) uint8 BGR
FrameSource, Gestures, AudioOut, AudioIn   # runtime_checkable Protocols, unchanged from v1
```

Coordinates. G is the back grid as printed, seen from the back. Turning the sheet over (long-edge flip) mirrors left and right, so front lattice cell `(i, j)` carries `G[i + 1, 49 - j + 1]` (`patch.front_to_g`, `patch.g_to_front`). A `Read` is already in front coordinates; there is no `front_slot` any more.

Turn. `turn = k` means the camera image of a window is `np.rot90(printed_window, k)`: the piece back is turned k quarter turns counter-clockwise as seen by the camera.

## 3. Core functions

`jigsaw/patch.py` (S0)

```python
def load_torus(path) -> np.ndarray                 # .npz (bits, shape; big-endian unpack) or .txt
def back_grid() -> np.ndarray                      # (72, 52): top-left corner of strong_u5_256.npz
def front_to_g(i, j) -> (a, b);  def g_to_front(a, b) -> (i, j)
def windows(pattern, u, wrap)                      # yields (i, j, window)
def verify(pattern, u, wrap) -> dict               # windows, turned_windows, min_distance, distance1_pairs
```

`jigsaw/geometry.py` (S5)

```python
def outline(r, c, seed=5) -> np.ndarray            # closed outline of piece (r, c), front view, mm
def edges(seed=5) -> (vdir, hdir, vedge, hedge)    # knob directions and curves
def visible_cells(r, c, tol_mm=0.5, offset_mm=(0, 0)) -> np.ndarray   # (72, 52) bool, cells fully inside
```

Rule built into `edges`: no piece has blanks on two opposite sides, which keeps at least four complete 5 x 5 windows on every piece for any duplex misregistration up to 3 mm.

`jigsaw/decode.py` (S1)

```python
class Table(dict)                                  # upright window bytes -> (i, j); .pattern .shape .u .wrap
def build_table(pattern, u=5, wrap=False) -> Table # raises if an upright window repeats
def decode_single(window, table) -> Position | Reject
def rot_affine(k, n) -> (M, c)                     # printed index = M @ seen index + c
def decode_grid(cells, mask, table, u=5, min_agree=2, max_disagree=3) -> Read | Reject
    # Decodes every complete u x u window in the mask. All decoded windows must imply one placement
    # (turn and offset), at least min(min_agree, number of complete windows) must agree, and at most
    # max_disagree visible cells may differ from table.pattern under that placement. The piece is the one under
    # the centroid of the visible cells.
```

`jigsaw/vision.py` (S1)

```python
def paper_mask(bgr) -> np.ndarray | None           # low-saturation or dark pixels, largest blob, holes filled
def read_grid(bgr) -> GridRead | Reject            # needs the piece over a coloured reading mat
def undistort(image, K, D) -> np.ndarray
```

`jigsaw/render.py` (S1)

```python
def piece_back(r, c, px_per_cell, offset_mm=(0, 0), grid=None) -> (gray, alpha)   # grid: e.g. the control pattern
def photograph(gray, alpha, rng, angle_deg, tilt=0, blur=0, noise=0, size=(720, 720), scale=1,
               background="mat" | "clutter" | "plain", finger=False, light=1.0,
               return_transform=False) -> BGR image, or (image, M) with M mapping piece_back pixels to the frame
```

`jigsaw/reader.py` (S1): `PieceReader().read(bgr) -> Decision`, keeps `last_grid` for the viewer.

`jigsaw/pose.py` (S1): `piece_pose(H, K, D, shape) -> (rvec, tvec mm) | None`.

`jigsaw/printing.py` (S5): `build(picture_path, out_pdf)`; constants `PW, PH, X0, Y0, XB, BLEED, CROSSES`.

To build, unchanged from v1 except where noted:

```python
# jigsaw/stable.py (S6)
class Stable:
    def __init__(self, need: int = 3, miss_limit: int = 15): ...
    def update(self, d: Decision) -> Literal["announce", "give_up", None]
    last: Read | None
# jigsaw/experiment (S2)
def classify(truth: Read, decision: Decision) -> Literal["correct", "rejected", "wrong"]
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]
# jigsaw/voice/phrases.py (S4)
def phrase_read(read: Read) -> str        # v2: no cols argument, Read is already front coordinates
def phrase_reject(reason: str) -> str     # v2: reason-specific ("show me the grid side", "move your fingers")
Command = Literal["ask", "again", "next", "stop"]
def match_command(text: str) -> Command | None
# jigsaw/voice/tts.py and stt.py (S4): synthesize(text) -> (pcm, rate); CommandListener(audio_in, is_muted).poll()
# jigsaw/robot (S3): connect(host=None) -> ReachyRobot (FrameSource + Gestures + AudioOut + AudioIn);
#                    ReplaySource(folder); RenderSource(...) built on render.photograph
```

## 4. Fakes (`jigsaw/fakes.py`, S0)

`FakeFrameSource(images)`, `FakeGestures()`, `FakeAudioOut()`, `FakeAudioIn(chunks)`. No test outside `tests/robot_live/` needs a robot; that folder is skipped unless `JIGSAW_LIVE=1`.

## 5. Viewer events (S6 produces, S7 consumes)

As in v1, with `quad` replaced by `grid` (the four image corners of the read grid) and front coordinates in the decision:

```json
{"type": "frame", "t": 12.3, "grid": [[x, y], [x, y], [x, y], [x, y]], "rvec": [a, b, c], "tvec": [x, y, z],
 "decision": {"kind": "read", "row": 3, "col": 1, "turn": 2}}
{"type": "frame", "t": 12.4, "grid": null, "rvec": null, "tvec": null, "decision": {"kind": "reject", "reason": "no_grid"}}
{"type": "announce", "row": 3, "col": 1, "turn": 2, "text": "Row 4, column 2. ..."}
{"type": "give_up", "text": "I cannot read that one. Show me again."}
{"type": "board", "placed": [[0, 0], [2, 4]]}          # 7 x 5 board
{"type": "head", "pose": [16 numbers, row-major 4 x 4]}
```

## 6. CSV schemas

Simulated experiments (`results/sim_puzzle.csv`, `results/sim_dense.csv`), one row per condition:

```
experiment,pattern,decoder,arm,px_per_cell,tilt,blur,noise,finger,n,correct,rejected,wrong,
wrong_le1_misread,reads_le1_misread,mean_misread_cells,seed,commit
```

`decoder` is `single` (one window, the paper's single read) or `grid` (`decode_grid`).

Physical test (`results/physical.csv`), one row per frame:

```
piece_row,piece_col,angle_deg,frame_file,kind,row,col,turn,reason,visible_cells,windows,
px_per_cell,resolution,timestamp,commit
```

`piece_row`, `piece_col` and `row`, `col` are front coordinates (zero-based). `kind` is `correct`, `rejected` or `wrong`.

## 7. Pattern files (`data/patterns/`)

| File | Original name | Use |
|------|---------------|-----|
| `strong_u5_256.npz` | `u5s4d2_R256C256_seed0.npz` | the printed back grid is its top-left 72 x 52 |
| `orient_u5_256.npz` | `u5s4d1_R256C256_seed0.npz` | orientation-only control (distance 1 pairs exist in its 72 x 52 corner) |
| `strong_u3_6x6.txt` | `u3v3s4d2_R6C6.txt` | dense-tori experiment, strong |
| `orient_u3_6x6.txt` | `u3v3s4d1_R6C6.txt` | dense-tori experiment, control |

Checksums are in `data/patterns/SHA256SUMS`; `tests/test_patch.py` checks the distances.
