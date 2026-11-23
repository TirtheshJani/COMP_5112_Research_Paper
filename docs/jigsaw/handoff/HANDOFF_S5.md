# HANDOFF S5 (21 and 23 Nov 2026)

The print file `print/reachy_debruijn_jigsaw.pdf` was designed and verified on 21 Nov and moved into the package on 23 Nov (`jigsaw/printing.py`, `scripts/make_print.py`, `scripts/make_picture.py`).

Verified on 21 Nov from rendered pages: 3744/3744 back cells match the grid; 875/875 piece reads correct (35 pieces x 25 misregistrations up to 3 mm, 0.5 mm cutting slop, random turn); at least 4 complete windows on every piece; one misread cell rejected 875/875; 35/35 front tiles correct after a long-edge flip; ruler 50 mm; grid width 187.2 mm; alignment crosses mirror within 0.1 mm.

Verified on 23 Nov (`tests/test_printing.py`): the package builds a PDF whose four pages render pixel-identical to the verified file, and every back cell reads correctly at 300 dpi.

Human steps left: print pages 1 and 2 on one sheet (double-sided, flip on long edge, Actual size, matte card stock), check the crosses against a light, measure the ruler, cut on the picture-side lines, make a green reading mat.
