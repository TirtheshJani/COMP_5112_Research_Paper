# S5 Printing: piece backs and mirrored fronts as a PDF

> **v2 update (23 Nov): DONE.** The print file is `print/reachy_debruijn_jigsaw.pdf` (4 Letter pages: picture with jigsaw cut lines, the de Bruijn grid, answer key, how-to). It replaces everything in the v1 spec below (square pieces, framed backs, two sheets). Built by `jigsaw/printing.py` (`python scripts/make_print.py`); `tests/test_printing.py` checks every printed cell and that the package builds a pixel-identical PDF. Verified on 21 Nov: 3744/3744 cells, 875/875 misregistered piece reads, 35/35 front tiles after a long-edge flip.
>
> **Human steps:** print pages 1 and 2 double-sided (flip on long edge, Actual size, matte card stock), hold to a light and check the two crosses line up, measure the 50 mm ruler, cut on the picture-side lines. Also cut a green (or any strongly coloured) card about 15 x 15 cm as the reading mat.

| | |
|---|---|
| Terminal | Sonnet 5.5, effort medium, Ultracode off |
| Branch and worktree | `feat/s5-printing` in `.worktrees/s5-printing` |
| Depends on | S0 merged. Uses the piece size recommended by the S3 focus check; defaults to 40 mm until that arrives |
| Blocks | S6 physical test (pieces must exist) |
| Owns | `jigsaw/printing.py`, `scripts/make_pieces_pdf.py`, `tests/test_printing.py`, `results/print/` |
| Must not edit | everything else |
| Human needed | Print, measure with a ruler, cut |
| Skills | `karpathy-guidelines`, `test-driven-development`, `verification-before-completion`, `pdf` |

---

## Spec

### Problem

The physical test needs forty square pieces whose backs carry the right 6 x 6 cells at a known physical size, and whose fronts carry the matching part of a picture. A sheet printed on both sides flips left to right, so the front must be laid out mirrored or the picture will not match the positions the robot announces.

### Goals

1. One command writes a PDF that prints at true size on letter paper with cut lines.
2. Back and front pages register when printed double-sided with a long-edge flip.
3. Each piece can be identified by a person during the test without reading the pattern.

### Non-goals

- No interlocking tabs. Squares only.
- No picture design. The front is any image file the author supplies; the default is a generated gradient with large row and column numbers.
- No printer driver handling beyond "print at 100 percent, no scaling".

### Requirements

| # | Priority | Requirement | Acceptance |
|---|---|---|---|
| P1 | P0 | `layout(piece_mm, page="letter", margin_mm=10, gap_mm=3)` returns the page and position of each of the 40 pieces | With 40 mm pieces: 4 columns by 5 rows per page, two pages; no piece crosses a margin |
| P2 | P0 | Back pages: each piece is drawn as 8 x 8 units (half-unit black border, half-unit white margin, 6 x 6 cells), vector rectangles, pure black and white | The PDF, rasterised at 600 dpi, read through `vision.read_cells` and `decode_four`, gives the right `Read` for all 40 pieces |
| P3 | P0 | Physical size | Rasterise a back page at a known dpi and measure a piece: within 0.2 mm of `piece_mm` |
| P4 | P0 | Front pages are mirrored left to right within the page, so that after a long-edge flip the front of each piece lies behind its back | Test: for every piece, the x-range of its front on the front page equals the page width minus the x-range of its back, and the y-range is equal |
| P5 | P0 | The front shows the part of the picture for front slot `(row, cols - 1 - col)`, upright when the back is upright after flipping about the vertical axis | Test with a synthetic picture whose pixel values encode (row, column): each front tile contains the code of `front_slot(Read(row, col, 0))` |
| P6 | P0 | A small human-readable label on the front only (for example "R3 C5", front numbering, one-based), in a corner, 2 mm high | Present on the front pages; nothing is printed on the back except the pattern, because extra marks could be read as cells |
| P7 | P1 | An answer sheet page: the assembled front with labels, and the assembled back, for checking | Last page of the PDF |
| P8 | P0 | A single-piece test page (`--test-piece`) for the S3 focus check | One piece centred, with a 50 mm ruler line beside it |

### Design notes

- Use ReportLab with millimetre units. Vector output avoids resampling the cells.
- Mirroring is the only subtle part. State it once as a function, `front_position(back_rect, page_width)`, and test it. Do not sprinkle `width - x` through the drawing code.
- The front picture. Split the image into 5 rows and 8 columns in front coordinates. The piece at back `(row, col)` gets front tile `(row, 7 - col)`. Because the sheet is flipped about its vertical axis, the tile is drawn unmirrored and unrotated at the mirrored position.
- Card stock and a paper trimmer give squarer pieces than scissors. Say so in the script's `--help`.

---

## Plan

### Task 1: Worktree, dependency

- [ ] Create the worktree. `uv sync --extra dev --extra print`. Add `pymupdf` to the `print` group (the only group S5 may edit) for rasterising PDFs in tests.

### Task 2: Layout and mirroring (P1, P4)

- [ ] `tests/test_printing.py`:

```python
from jigsaw.printing import layout, front_position, LETTER_MM

def test_layout_40mm():
    lay = layout(piece_mm=40)
    assert len(lay) == 40 and {p.page for p in lay} == {0, 1}
    for p in lay:
        assert p.x >= 10 and p.x + 40 <= LETTER_MM[0] - 10
        assert p.y >= 10 and p.y + 40 <= LETTER_MM[1] - 10

def test_front_is_mirrored_about_the_vertical_axis():
    for p in layout(piece_mm=40):
        fx, fy = front_position(p.x, p.y, 40, LETTER_MM[0])
        assert abs((fx + 40) - (LETTER_MM[0] - p.x)) < 1e-9 and fy == p.y
```

- [ ] Run (fail), implement, run (pass). Commit.

### Task 3: Back pages (P2, P3, P8)

- [ ] Test: build the PDF to a temporary file, rasterise page 1 with PyMuPDF at 600 dpi, crop each piece by its layout rectangle plus 3 mm, run `read_cells` and `to_piece(decode_four(...))`, and assert the `Read` equals `(row, col, 0)`. Measure the black border's width in pixels and convert to millimetres for P3.
- [ ] Implement `draw_backs`. Implement `--test-piece`. Run. Commit.

### Task 4: Front pages (P5, P6, P7)

- [ ] Test with a synthetic picture: an image whose red channel is `row * 30` and green channel is `column * 30` in each of the 5 x 8 regions. Rasterise the front page, sample the centre of each front tile, and assert it carries the code of `front_slot`.
- [ ] Implement `draw_fronts`, labels and the answer sheet. Run. Commit.

### Task 5: Produce and check. HUMAN

- [ ] `uv run python scripts/make_pieces_pdf.py --piece-mm <from S3, default 40> --out results/print/pieces.pdf`.
- [ ] Open the PDF, render page 1 and page 2 to PNG and look at them.
- [ ] Ask the author to print one sheet double-sided at 100 percent with long-edge flip, measure one piece, hold the sheet to a light to check that fronts sit behind backs, and report. If the fronts are offset, the printer's duplex alignment is off: add `--front-offset-mm x y` and reprint one sheet.
- [ ] `HANDOFF_S5.md` with the measured size. Pull request.

### Subagent use

None needed. This is one small module. Use one review subagent at the end: "Review `feat/s5-printing`. Work through the mirroring by hand for the piece at back (0, 0) and back (4, 7) and state where each front tile lands on the front page and which part of the picture it shows. Compare with `front_slot`. Do not edit files."

### What could go wrong

| If | Then |
|---|---|
| The printer scales the page | The ruler line on the test page shows it; print with "actual size" |
| Duplex registration is off by more than 1 mm | Use the offset option, or print fronts and backs on separate sheets and glue them to card |
| The focus check asks for 60 mm pieces | `layout` handles it: 3 columns by 4 rows per page, four pages. The test for P1 is parametrised over 40 and 60 |
| Glossy stock reflects room light into the camera | Use matte stock; note it in the handoff |

### Definition of done

Tests pass; the PDF read back through the decoder gives all 40 pieces; one printed sheet measured and registered; handoff written.
