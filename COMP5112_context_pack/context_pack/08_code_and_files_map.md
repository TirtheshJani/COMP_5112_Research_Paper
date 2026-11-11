# 08. Code, files and where everything lives

## Locations

- TJ's PC (Windows): `C:\Users\TJ\Downloads\Lakehead-MSc\COMP-5112-Research-Methodology\`. Through the desktop app's device bridge it mounts as `$HOME/mnt/COMP-5112-Research-Methodology`.
  - `research/notes`, `research/otorus`, `research/results`, `research/paper` (each of otorus, results and paper is its own git repository).
  - `Poster-12TJ/` (poster PDF, previews, figures, talk script, knowledge-pack 00 to 04).
  - `Overleaf Projects (4 items)/12TJ/` (personal Overleaf copy), `Overleaf Projects (4 items)/de Bruijn Tori (References)/` (shared class pool, about 150 PDFs), `A2-Reference-PDFs/`.
  - Course files: syllabus (.md and .docx), lecture PDFs, The Craft of Research PDF (4th ed.) and EPUB (5th ed.), PostScript torus template files.
- Cloud mirror used in this chat: `/home/claude/otorus_run/research/` (same layout plus `study_guide/`, `meeting_prep_aaron/`, `context_pack/`). As of 11 November the PC copy does not yet have study_guide, meeting_prep_aaron or context_pack; they are being committed to `research/` on the PC with this pack.
- Overleaf project: 12TJ. Assignment 4 notebook: Google Drive, `Tirthesh_Jani_de_Bruijn_Torus_Programming4444.ipynb`. Course notes: Notion (COMP 5112, Research Methodology in CS, under the Fall 2026 term hub).
- Project (claude.ai, Masters Research Project) docs listed in file 00.
- Delivered files in this chat: COMP5112_paper_draft3.pdf, COMP5112_paper_overleaf.zip, Which_Way_Is_Up_Study_Guide.pdf, COMP5112_paper_fixes_found.md, COMP5112_WhichWayIsUp_everything.zip, the five G2 prep note files.

## Git state on TJ's PC

- otorus: 8194250 (peer review 2: open-patch search), 07d727a (peer review 1), 1a839c1 (witness verification script)
- results: 1f27d18 (peer review 2), a819d2e (peer review 1), f0f7561 (Phase 3 close-out)
- paper: 4db4b9e (draft 3 after two reviews)
The paper repo needed a git identity copied from otorus's local config.

## The otorus library (`research/otorus`, Python >= 3.10, numpy; dev: pytest, python-sat; numba for the exhaustive search)

- `windows.py`: window, all_windows, rotations, pack, packed_turned_windows, is_orientable, min_window_distance, turned_window_codes, min_distance_fast (rmax = 2 also checks two-bit changes).
- `bounds.py`: fixed_by_rot90, fixed_by_rot180, even_fixed_by_rot180, ceiling, max_independent_free (bipartite matching check of the even-side bound).
- `sat.py`: _instances, encode (CNF with XOR auxiliaries), solve_torus (CaDiCaL), solve_torus_alt (Glucose with a sequential counter).
- `exhaustive.py`: turned_cells (independent index arithmetic), dfs_search, dfs_strip, dfs_patch.
- `search.py`: local_search and energy (Metropolis, code-count table, conflict ball, periodic rescans).
- `construct.py`: construction_e, xor_torus, xor_descriptors, solve_xor, interleave_checkerboard, interleave_descriptors, solve_interleave, random_window_cycle.
- `decode.py`: class Decoder(T, u, s) with decode and decode_batch (sorted code table, binary search; returns position and turn or a rejection).
- `camera.py`: simulate_reads(T, u, n, rng, blur, noise, angle_deg, offset, subsamples). This is the piece a physical Reachy read would replace or validate.

Tests (61 pass): test_windows, test_bounds, test_sat, test_exhaustive_independent (10 tests, including the reviewer's patch), test_search (includes the rescan regression), test_construct (descriptor criterion against the direct check on 360 random pairs), test_decode, test_camera, test_verify.

## Scripts (`research/otorus/scripts`) and what they produce

- `run_sat_table.py 3 3 4 2 <timeout>` -> sat_table.csv (u, s, delta per call)
- `verify_table.py 3 3 4 2 5e10 0` -> verify_3x3_s4_d2_dfs.csv; second encoding -> verify_3x3_s4_d2.csv
- `run_strips.py 3 4 2 9 60` -> strips_3x3_s4_d2.csv (and d1)
- `run_patches.py 3 4 2 3e8 ...` -> patches_3x3_s4_d2.csv
- `run_xor_table.py` -> xor_table.csv
- `run_interleave_table.py 300` -> interleave_table.csv; `run_interleave_rows6.py <timeout> 30,32,...,64` -> interleave_rows6.csv
- `run_grow.py 5 4 2 256 0:2 3e7 0.5` (u, s, delta, side, seed range a:b, flips, temperature) -> grow_5x5.csv, grow_4x4.csv, witnesses
- `run_camera.py name=path:u:s:design ...` -> camera_robustness.csv and decode_timing.md (five timing runs, median)
- `make_figures.py` -> paper/figures/*
- `verify_witnesses.py` -> verify_witnesses.txt (136 of 136)

## Results folder (`research/results`)

README.md (claims index), bounds.md, exact_3x3_strong_form.md, interleave.md, decode_timing.md (and _v1), sat_table.csv, verify_3x3_s4_d2.csv, verify_3x3_s4_d2_dfs.csv (and _shared_generator), strips_3x3_s4_d2.csv, strips_3x3_s4_d1.csv, patches_3x3_s4_d2.csv, xor_table.csv, interleave_table.csv, interleave_rows6.csv, grow_4x4.csv, grow_5x5.csv, camera_robustness.csv (and _v1), verify_witnesses.txt, logs, witnesses/ (136 files, file 06).

## Paper folder (`research/paper`)

1374286TJ.tex, Assignment3.tex, sections/01 to 11, figures/, refs.bib, refs_check.md, build/paper_draft1 to 3.pdf, review/peer_review_1.md and _2.md, talk/talk_plan.md (out of date; the deck replaces it), _superseded/refs_software.bib.

## Study guide folder (`research/study_guide`)

main.tex, preamble.tex, parts/part0 to part6, Which_Way_Is_Up_Study_Guide.pdf (84 pages), reading_list.md, paper_fixes_found.md. Compile with pdflatex main.tex twice.

## Reproduce from scratch

```
cd research/otorus
python3 -m pip install -e .[dev] numba
python3 -m pytest -q                  # 61 tests
python3 scripts/verify_witnesses.py   # 136 of 136
```
