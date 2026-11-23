"""Print file for the two-sided de Bruijn jigsaw (Letter, portrait).

Sheet 1, printed double-sided (flip on the long edge):
  page 1  FRONT  the picture, with jigsaw cut lines
  page 2  BACK   one continuous binary de Bruijn grid (strong-form torus patch), no cut lines
Sheet 2, reference only:
  page 3  answer key (where each piece goes)
  page 4  how it works and how to print

Usage: python scripts/make_print.py  (or printing.build(picture, out_pdf))
"""
import sys

import numpy as np
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from jigsaw import geometry as geo
from jigsaw import types as T
from jigsaw.patch import back_grid

PW, PH = letter[0] / mm, letter[1] / mm          # 215.9 x 279.4 mm
X0, Y0 = (PW - geo.W) / 2, (PH - geo.H) / 2          # puzzle top-left on the front page
XB = PW - X0 - geo.W                                 # puzzle left edge on the back page
BLEED = 4.0
EPS = 0.02
CROSSES = [(X0 - 8, Y0 + 70), (X0 + geo.W + 8, Y0 + geo.H - 70)]   # front positions; back ones are mirrored
BLUE = (0 / 255, 114 / 255, 178 / 255)            # Okabe-Ito blue


def Y(y_top, h=0.0):
    """Top-based mm to reportlab's bottom-based points."""
    return (PH - y_top - h) * mm


def path_from(c, pts, ox, oy, scale=1.0, mirror_w=None):
    p = c.beginPath()
    for k, (x, y) in enumerate(pts):
        if mirror_w is not None:
            x = mirror_w - x
        X, Yy = (ox + x * scale) * mm, Y(oy + y * scale)
        p.moveTo(X, Yy) if k == 0 else p.lineTo(X, Yy)
    return p


def cut_lines(c, ox, oy, edges, white=0.9, dark=0.4):
    """Draw every edge twice, white underneath and dark on top, so lines show on light and dark areas."""
    for width, gray in ((white, 1.0), (dark, 0.12)):
        c.setLineWidth(width)
        c.setStrokeGray(gray)
        c.setLineJoin(1)
        c.setLineCap(1)
        for pts in edges:
            c.drawPath(path_from(c, pts, ox, oy), stroke=1, fill=0)
        c.rect(ox * mm, Y(oy, geo.H), geo.W * mm, geo.H * mm, stroke=1, fill=0)


def cross(c, x, y, r=3.0):
    c.setStrokeGray(0)
    c.setLineWidth(0.5)
    c.line((x - r) * mm, Y(y), (x + r) * mm, Y(y))
    c.line(x * mm, Y(y - r), x * mm, Y(y + r))
    c.circle(x * mm, Y(y), r * 0.6 * mm, stroke=1, fill=0)


def all_edges(vedge, hedge):
    return [e for row in vedge for e in row] + [e for row in hedge for e in row]


def draw_grid(c, G, left, top, cell, lines=True):
    """Draw G with its cell (a, b) at (left + b*cell, top + a*cell)."""
    c.setFillGray(0)
    for a in range(G.shape[0]):
        b = 0
        while b < G.shape[1]:
            if G[a, b]:
                b2 = b
                while b2 + 1 < G.shape[1] and G[a, b2 + 1]:
                    b2 += 1
                x, y, w = left + b * cell, top + a * cell, (b2 - b + 1) * cell
                c.rect((x - EPS) * mm, Y(y - EPS, cell + 2 * EPS), (w + 2 * EPS) * mm, (cell + 2 * EPS) * mm, stroke=0, fill=1)
                b = b2 + 1
            else:
                b += 1
    if lines:
        c.setStrokeGray(0.55)
        c.setLineWidth(0.2 * mm)   # 0.2 mm grid lines
        for b in range(G.shape[1] + 1):
            c.line((left + b * cell) * mm, Y(top), (left + b * cell) * mm, Y(top + G.shape[0] * cell))
        for a in range(G.shape[0] + 1):
            c.line(left * mm, Y(top + a * cell), (left + G.shape[1] * cell) * mm, Y(top + a * cell))


def ruler(c, x, y, length=50.0, label="50 mm: measure this to check the print scale."):
    c.setStrokeGray(0)
    c.setLineWidth(0.6)
    c.line(x * mm, Y(y), (x + length) * mm, Y(y))
    for t in range(int(length // 10) + 1):
        h = 2.5 if t in (0, int(length // 10)) else 1.5
        c.line((x + 10 * t) * mm, Y(y), (x + 10 * t) * mm, Y(y - h))
    c.setFont("Helvetica", 6.5)
    c.setFillGray(0)
    c.drawString((x + length + 3) * mm, Y(y + 0.8), label)


def page_front(c, picture, vedge, hedge):
    px_per_mm = picture.width / (geo.W + 2 * BLEED)
    assert abs(px_per_mm - picture.height / (geo.H + 2 * BLEED)) < 0.05, "picture has the wrong aspect ratio"
    c.drawImage(ImageReader(picture), (X0 - BLEED) * mm, Y(Y0 - BLEED, geo.H + 2 * BLEED),
                (geo.W + 2 * BLEED) * mm, (geo.H + 2 * BLEED) * mm)
    cut_lines(c, X0, Y0, all_edges(vedge, hedge))
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(X0 * mm, Y(6.2), "Reachy de Bruijn jigsaw, 35 pieces.  FRONT: picture side. Cut on these lines.")
    for x, y in CROSSES:
        cross(c, x, y)


def page_back(c, G):
    draw_grid(c, G, XB - T.MARGIN_CELLS * T.CELL_MM, Y0 - T.MARGIN_CELLS * T.CELL_MM, T.CELL_MM)
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString((XB - T.MARGIN_CELLS * T.CELL_MM) * mm, Y(6.2), "BACK: binary de Bruijn grid (strong-form torus). Do not cut or write on this side.")
    for x, y in CROSSES:
        cross(c, PW - x, y)
    ruler(c, XB - T.MARGIN_CELLS * T.CELL_MM, PH - 4.8,
          label="50 mm: check the print scale. One cell = 3.6 mm, one piece = 36 mm without knobs.")


def page_key(c, picture, polys, vedge, hedge):
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(X0 * mm, Y(9), "Answer key: where each piece goes (picture side up)")
    c.setFont("Helvetica", 7.5)
    c.drawString(X0 * mm, Y(13.2), "Rows 1 to 7 from the top, columns 1 to 5 from the left. Reachy says the same row and column.")
    top = Y0 + 4
    scale = (geo.H - 8) / geo.H
    w, h = geo.W * scale, geo.H * scale
    left = (PW - w) / 2
    c.saveState()
    c.drawImage(ImageReader(picture.crop((int(BLEED * picture.width / (geo.W + 2 * BLEED)),
                                          int(BLEED * picture.height / (geo.H + 2 * BLEED)),
                                          int((BLEED + geo.W) * picture.width / (geo.W + 2 * BLEED)),
                                          int((BLEED + geo.H) * picture.height / (geo.H + 2 * BLEED))))),
                left * mm, Y(top, h), w * mm, h * mm)
    c.setFillColorRGB(1, 1, 1, alpha=0.35)
    c.rect(left * mm, Y(top, h), w * mm, h * mm, stroke=0, fill=1)
    c.restoreState()
    c.setLineWidth(0.6)
    c.setStrokeGray(0.1)
    for pts in all_edges(vedge, hedge):
        c.drawPath(path_from(c, pts, left, top, scale), stroke=1, fill=0)
    c.rect(left * mm, Y(top, h), w * mm, h * mm, stroke=1, fill=0)
    for (r, col), poly in polys.items():
        cx, cy = (col + 0.5) * T.PIECE_MM * scale + left, (r + 0.5) * T.PIECE_MM * scale + top
        label = f"R{r + 1} C{col + 1}"
        tw = c.stringWidth(label, "Helvetica-Bold", 8) / mm
        c.setFillColorRGB(1, 1, 1, alpha=0.85)
        c.roundRect((cx - tw / 2 - 1.5) * mm, Y(cy - 2.4, 4.8), (tw + 3) * mm, 4.8 * mm, 1 * mm, stroke=0, fill=1)
        c.setFillGray(0)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(cx * mm, Y(cy + 1.1), label)


def wrap(c, text, x, y, width, font="Helvetica", size=9.5, lead=13.2):
    c.setFont(font, size)
    words, line = text.split(), ""
    for w in words:
        trial = (line + " " + w).strip()
        if c.stringWidth(trial, font, size) / mm > width:
            c.drawString(x * mm, Y(y), line)
            y += lead * 0.3528
            line = w
        else:
            line = trial
    if line:
        c.drawString(x * mm, Y(y), line)
        y += lead * 0.3528
    return y


def page_howto(c, G, polys):
    x, width = 20.0, PW - 40.0
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(x * mm, Y(24), "Reachy de Bruijn jigsaw: how it works")
    y = 34.0
    y = wrap(c, "The front of each piece is part of a picture. The back is part of one binary grid that covers the "
                "whole puzzle. The grid is cut from a strong-form de Bruijn torus: every 5 x 5 block of cells appears "
                "only once, and it still appears only once after a quarter, half or three-quarter turn. Any two of those "
                "turned blocks differ in at least two cells.", x, y, width)
    y += 2
    y = wrap(c, "Hold a piece grid-side up to Reachy Mini. The camera reads a 5 x 5 block it can see and looks it up. "
                "That one lookup gives where the block sits in the grid, which piece it belongs to, and how far the piece "
                "is turned. Reachy says the row, the column and the turn, and you place the piece picture-side up. If the "
                "camera misreads one cell, the block matches nothing, so Reachy asks for another look instead of sending "
                "the piece to the wrong place. Every piece shows at least four complete blocks, so there is always a cross-check.",
             x, y, width)

    # Illustration: the back of one piece, enlarged, with one window outlined
    r, col = 3, 1
    scale = 1.9
    pts = polys[(r, col)]
    ring = [tuple(v) for v in np.vstack([pts, pts[:1]])]
    minx, miny = pts.min(axis=0)
    maxx, maxy = pts.max(axis=0)
    bx0, by0 = geo.W - maxx, miny                       # bounds in back view (mirrored)
    ox, oy = x + 4, y + 6
    i0, i1 = int(np.floor(miny / T.CELL_MM)), int(np.ceil(maxy / T.CELL_MM))
    jb0, jb1 = int(np.floor(bx0 / T.CELL_MM)), int(np.ceil((geo.W - minx) / T.CELL_MM))
    sub = np.zeros((i1 - i0, jb1 - jb0), np.uint8)
    for i in range(i0, i1):
        for jb in range(jb0, jb1):
            a, b = i + T.MARGIN_CELLS, jb + T.MARGIN_CELLS
            if 0 <= a < G.shape[0] and 0 <= b < G.shape[1]:
                sub[i - i0, jb - jb0] = G[a, b]
    c.saveState()
    clip = path_from(c, ring, ox - bx0 * scale, oy - by0 * scale, scale, mirror_w=geo.W)
    c.clipPath(clip, stroke=0, fill=0)
    draw_grid(c, sub, ox + (jb0 * T.CELL_MM - bx0) * scale, oy + (i0 * T.CELL_MM - by0) * scale, T.CELL_MM * scale)
    c.restoreState()
    c.setLineWidth(1.0)
    c.setStrokeGray(0)
    c.drawPath(path_from(c, ring, ox - bx0 * scale, oy - by0 * scale, scale, mirror_w=geo.W), stroke=1, fill=0)
    # a window fully inside the core of this piece
    wi, wj = r * T.PIECE_CELLS + 2, (T.PUZZLE_COLS - 1 - col) * T.PIECE_CELLS + 3        # back-view cell indices
    c.setStrokeColorRGB(*BLUE)
    c.setLineWidth(2.2)
    c.rect((ox + (wj * T.CELL_MM - bx0) * scale) * mm, Y(oy + (wi * T.CELL_MM - by0) * scale, 5 * T.CELL_MM * scale),
           5 * T.CELL_MM * scale * mm, 5 * T.CELL_MM * scale * mm, stroke=1, fill=0)
    cap_x = ox + (maxx - minx) * scale + 8
    c.setFillGray(0)
    wrap(c, "The back of one piece, enlarged. The blue square is one 5 x 5 window. Reachy needs only one "
                 "complete window to place the piece; any other window on the same piece must agree.",
              cap_x, oy + 10, PW - 20 - cap_x, size=8.5, lead=11.5)
    y = oy + (maxy - miny) * scale + 10

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x * mm, Y(y), "Printing and cutting")
    y += 6
    steps = [
        "Print pages 1 and 2 on one sheet: double-sided, flip on long edge, Actual size (100%), on matte card stock "
        "(65 to 110 lb cover, about 175 to 300 gsm). Glossy paper glares in the camera.",
        "Hold the sheet up to a light. The two crosses on the picture side must sit on the two crosses on the grid side. "
        "If one sits near the top and the other near the bottom, the printer flipped on the short edge: reprint.",
        "Measure the 50 mm ruler on the grid side. One cell is 3.6 mm and one piece is 36 mm across without its knobs.",
        "Cut on the lines on the picture side with a craft knife or small scissors. Never cut from the grid side.",
        "Pages 3 and 4 (the answer key and this page) are for reference. Print them single-sided.",
    ]
    for k, s in enumerate(steps, 1):
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x * mm, Y(y), f"{k}.")
        y = wrap(c, s, x + 5, y, width - 5) + 1.2
    ruler(c, x, y + 4, label="50 mm")


def build(picture_path, out_path, seed=geo.SEED):
    picture = Image.open(picture_path).convert("RGB")
    _, _, vedge, hedge = geo.edges(seed)
    polys = {(r, c): geo.outline(r, c, seed) for r in range(T.PUZZLE_ROWS) for c in range(T.PUZZLE_COLS)}
    G = back_grid()
    c = canvas.Canvas(out_path, pagesize=letter, invariant=1)
    c.setTitle("Reachy de Bruijn jigsaw: print sheets")
    page_front(c, picture, vedge, hedge)
    c.showPage()
    page_back(c, G)
    c.showPage()
    page_key(c, picture, polys, vedge, hedge)
    c.showPage()
    page_howto(c, G, polys)
    c.showPage()
    c.save()
    print("wrote", out_path)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
