# Contrado edition: 48-piece plastic jigsaw (24 Nov 2026)

A shop-made version of the puzzle, ordered from Contrado (contrado.ca, "Custom Plastic Jigsaw"), for the final demo and as a gift. The card version in `print/reachy_debruijn_jigsaw.pdf` stays the test copy for Friday.

## What to order

In Contrado's editor choose **Large Rectangle (x48, 10.04 in)**, **Print both sides**, packaging **None** (the tin is included and has its own panel). Upload, each at 100% with no cropping, rotating or filters:

| Contrado panel | File | Size |
|---|---|---|
| Jigsaw Front | `print/contrado/contrado_front_3130x2362.png` | 3130 x 2362 px, 300 dpi |
| Jigsaw Back | `print/contrado/contrado_back_3130x2362.png` | 3130 x 2362 px, 300 dpi |
| Tin | `print/contrado/contrado_tin_1972x1323.png` | 1972 x 1323 px, 300 dpi |

Each file is exactly the panel size the editor asks for, so the image should fill the panel edge to edge without any scaling. Check in the 3D preview that the back shows the black-and-white grid right to the edges.

The editor showed CAD $88.80 for this size printed on both sides (23 Nov). Contrado ships in 1 to 2 working days and quotes 3 to 5 days for most international deliveries, from CAD $12.95 to Canada. Ordered on 24 November with the fastest shipping option offered at checkout, it can arrive before 1 December. With standard shipping it more likely lands between 30 November and 2 December. Both are Contrado's estimates, not guarantees.

The same three pages are in Canva as "Contrado 48-piece Reachy jigsaw (front, back, tin)" (design DAHbx2OX5fg). Its PNG export was compared with these files and is pixel-identical, so downloading from Canva or using the files directly gives the same print.

## How the back works

- Contrado cuts with its own die (8 x 6 pieces, about 31.9 x 31.7 mm, knobs about 9 mm deep), so the back is one continuous grid over the whole panel, including the 5 mm bleed.
- One cell is 30 px = 2.54 mm (0.1 in), down from 3.6 mm on the card, so that every Contrado piece keeps complete 5 x 5 windows. That is an exact 30 px at 300 dpi and 20 px at Contrado's 200 dpi print resolution.
- The grid is `torus[100:179, 120:225]` of the strong-form u = 5 torus (79 x 105 cells). It does not overlap the card's `torus[0:72, 0:52]`, so a card piece never decodes as a Contrado piece.
- The robot finds the piece from the centroid of all the cells it sees, mapped to the front through the flip, then to Contrado's 8 x 6 grid. `jigsaw/contrado.py` holds the geometry, `ContradoReader` (same interface as `reader.PieceReader`) and `decode`.

## Checks run before ordering

`scripts/verify_contrado.py print/contrado/contrado_back_3130x2362.png --images`

- Every cell in the PNG matches G (8,295 cells, 0 mismatches). G has 7,575 windows and 30,300 turned windows with minimum distance 2.
- Contrado's own cut lines, measured from its 3D preview: the worst interior piece still holds at least 4 complete 5 x 5 windows at 2.5 to 2.6 mm cells, with the print shifted anywhere against the cut and 0.8 mm cut tolerance.
- Stand-in die, a little harsher than Contrado's (smallest free square 17.3 mm against Contrado's 18.8 mm), print shifted up to 1.5 mm against the cut: all 48 pieces, 4 turns, 25 shifts: 4,800 of 4,800 reads correct, 0 wrong, and at least 2 complete windows on every piece. One flipped cell in each of 4,800 reads gave 0 wrong pieces. Both flip directions pass.
- Simulated photos on the green mat through `vision.read_grid`, at 9, 11, 14 and 18 px per cell, with tilt, blur, noise and turns: 384 of 384 correct, 0 wrong, 0 rejected.

## What is not checked

- **Glare.** Contrado's plastic is high-gloss. Glare can make the reader refuse a frame (it refuses, it does not misplace), so tilt the piece slightly away from lights.
- **The flip direction.** `FLIP = "lr"` assumes the back panel is what you see after turning the puzzle over left to right. On arrival, show Reachy the top-left corner piece (picture side: sky, top left). If it says column 8 instead of column 1, set `FLIP = "tb"`.
- **Camera resolution.** The cells are 30% smaller than on the card. Friday's focus check on the card (3.6 mm cells) gives the px per cell at each distance; multiply by 0.71 for the Contrado pieces and aim for at least 9 px per cell.
- **Contrado's real die and print registration** were measured from their preview, not a physical puzzle.

## To wire into the app

`scripts/run_demo.py` needs an `--edition card|contrado` option that builds `contrado.ContradoReader()` in place of `reader.PieceReader()`. The voice phrases already read `Read.row + 1` and `Read.col + 1`, so rows 1 to 6 and columns 1 to 8 need no other change. The viewer board is drawn for the card's 7 x 5 layout and would need a Contrado layout to show placed pieces.
