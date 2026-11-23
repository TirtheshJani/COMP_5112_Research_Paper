# COMP 5112 Reachy de Bruijn jigsaw: project folder (23 Nov 2026)

This folder is the whole project so far: the print file, the paper outline, the specs and plans, and the first working code. It is laid out as the repository, so copy everything in it into `C:\Users\TJ\Documents\GitHub\COMP_5112_Research_Paper` (the repo currently holds only a licence and a few zips, so nothing is overwritten).

## What is in it

| Folder or file | What it is |
|---|---|
| `print/reachy_debruijn_jigsaw.pdf` | The puzzle to print: page 1 picture with jigsaw cut lines, page 2 the de Bruijn grid, page 3 answer key, page 4 how-to |
| `print/reachy_debruijn_jigsaw_preview.png`, `print/picture_portrait.png` | Preview of the four pages; the front picture |
| `paper/` | The outline assignment: `12outline.tex`, `12outline.pdf`, the Overleaf upload zip, and the BibTeX correction notes |
| `docs/jigsaw/` | Specs and plans v2: `README.md` (status, order, which model for which spec), `CLAUDE.md`, `CONTRACTS.md`, `S0` to `S8`, risks, handoff notes |
| `jigsaw/` | The Python package: decoder, camera reader, renderer, pose, print builder |
| `tests/` | 40 tests (decoder, reader, print, types, patterns) |
| `scripts/probes/` | Four robot probes: daemon status, camera, live reading of pieces, a small nod |
| `data/patterns/` | The strong-form torus the grid is cut from, the control tori, checksums |

## Status

S0 (foundation), S1 (decoder and camera reader for the reading-mat setup) and S5 (printing) are built and tested; S3 has its probes. The decoder and reader made no wrong read in any test, including every piece at every turn, every single misread cell, and 875 misregistered prints. Details are in `docs/jigsaw/handoff/`.

## What to do next, in order

1. Copy this folder into the repo, then in a terminal there: `uv venv --python 3.12`, `uv sync --extra dev --extra print`, `uv run pytest`. Expect 40 passed.
2. Print pages 1 and 2 double-sided (flip on long edge, Actual size, matte card stock). Check the crosses against a light, measure the ruler, cut. Cut a green card (any strong colour) about 15 x 15 cm as the reading mat.
3. With the robot on and the conversation app stopped: `uv sync --extra robot`, then run `scripts/probes/p1_status.py`, `p2_camera.py`, `p3_live_read.py` and `p4_nod.py --move` (commands in `docs/jigsaw/handoff/HANDOFF_S3_probes.md`). p3 is the first real test: hold pieces over the green card and it prints the piece it sees.
4. Start the remaining workstreams with the prompts in `docs/jigsaw/PROMPTS.md`: S3, S4 and S7 in parallel (S2 can join them), then S6, then S8.

## Which model for which spec

The prompts to paste into each Claude Code terminal, with the model, effort and skills for each and the rules that keep token use down, are in `docs/jigsaw/PROMPTS.md`.

| Spec | Model | Effort |
|---|---|---|
| S0 rerun, S5 printing, probes p1 to p4 | none (you run them) | |
| S3 robot I/O | Opus 5.5 | high |
| S4 voice | Sonnet 5.5 | medium |
| S7 viewer | Sonnet 5.5 | high |
| S2 experiments | Opus 5.5 | high |
| S6 app and physical test | Opus 5.5 | high |
| S8 verification | Opus 5.5 (Fable 5.2 optional for the claims check) | high |
| S1 without a mat (optional) | Opus 5.5 | high |

Ultracode stays off everywhere.
