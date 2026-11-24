"""Print files for the Contrado 48-piece plastic jigsaw (front, back, tin lid), 300 dpi sRGB PNG.

Usage: python scripts/make_contrado.py OUT_DIR
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from jigsaw import contrado as K
from jigsaw.patch import verify

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "print/contrado")
OUT.mkdir(parents=True, exist_ok=True)
LINE_GRAY, LINE_PX = 140, 2          # 0.17 mm grid lines, the gray the reader expects
TIN_W, TIN_H = 1972, 1323
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"


def back_image(G: np.ndarray) -> Image.Image:
    cell = K.CELL_PX
    big = np.kron(1 - G, np.ones((cell, cell), np.uint8)) * 255          # 255 white, 0 black
    img = big[: K.PANEL_H, : K.PANEL_W].astype(np.uint8)
    for b in range(0, K.PANEL_W + 1, cell):                              # line centred on each boundary
        img[:, max(0, b - LINE_PX // 2): b + LINE_PX - LINE_PX // 2] = np.minimum(
            img[:, max(0, b - LINE_PX // 2): b + LINE_PX - LINE_PX // 2], LINE_GRAY)
    for a in range(0, K.PANEL_H + 1, cell):
        img[max(0, a - LINE_PX // 2): a + LINE_PX - LINE_PX // 2, :] = np.minimum(
            img[max(0, a - LINE_PX // 2): a + LINE_PX - LINE_PX // 2, :], LINE_GRAY)
    return Image.fromarray(img).convert("RGB")


def tin_image(picture: Image.Image) -> Image.Image:
    # cover-crop the picture to the lid, keeping the lake and the moon
    s = max(TIN_W / picture.width, TIN_H / picture.height)
    pic = picture.resize((round(picture.width * s), round(picture.height * s)), Image.LANCZOS)
    x0 = (pic.width - TIN_W) // 2
    y0 = int((pic.height - TIN_H) * 0.35)
    lid = pic.crop((x0, y0, x0 + TIN_W, y0 + TIN_H)).convert("RGBA")
    # dark band behind the title, fading upwards
    band = Image.new("RGBA", lid.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    top = int(TIN_H * 0.60)
    for y in range(top, TIN_H):
        t = min(1.0, (y - top) / (TIN_H * 0.12))
        bd.line([(0, y), (TIN_W, y)], fill=(10, 12, 30, int(200 * t)))
    lid = Image.alpha_composite(lid, band)
    d = ImageDraw.Draw(lid)
    margin = int(12 * K.PX_PER_MM)          # keep text 12 mm in from the edge (bleed plus the lid's curve)
    title = ImageFont.truetype(FONT.format("Bold"), 128)
    sub = ImageFont.truetype(FONT.format("Medium"), 44)
    small = ImageFont.truetype(FONT.format("Regular"), 34)
    y = TIN_H - margin - 34 - 22 - 44 - 30 - 128
    d.text((margin, y), "Which Way Is Up?", font=title, fill=(250, 244, 220))
    y += 128 + 30
    d.text((margin, y), "A 48-piece jigsaw with a strong-form orientable de Bruijn torus on the back",
           font=sub, fill=(235, 225, 245))
    y += 44 + 22
    d.text((margin, y), "Show Reachy Mini any piece, grid side up: one look gives its row, column and turn.",
           font=small, fill=(205, 195, 225))
    # a small 5 x 5 window motif, top right, from the real back grid
    G = K.back_grid()
    w = G[40:45, 50:55]
    c = 26
    ox, oy = TIN_W - margin - 5 * c, margin
    d.rectangle([ox - 8, oy - 8, ox + 5 * c + 8, oy + 5 * c + 8], fill=(250, 250, 250, 235))
    for a in range(5):
        for b in range(5):
            if w[a, b]:
                d.rectangle([ox + b * c, oy + a * c, ox + (b + 1) * c - 1, oy + (a + 1) * c - 1], fill=(15, 15, 25))
    for k in range(6):
        d.line([ox + k * c, oy, ox + k * c, oy + 5 * c], fill=(140, 140, 140), width=2)
        d.line([ox, oy + k * c, ox + 5 * c, oy + k * c], fill=(140, 140, 140), width=2)
    return lid.convert("RGB")


def main():
    G = K.back_grid()
    v = verify(G, K.U, wrap=False)
    assert v["min_distance"] == 2, v
    print("G", G.shape, v)
    front = OUT / "contrado_front_3130x2362.png"
    subprocess.run([sys.executable, "scripts/make_picture.py", str(front), "255", "190", "5"], check=True)
    pic = Image.open(front)
    assert pic.size == (K.PANEL_W, K.PANEL_H), pic.size
    back_image(G).save(OUT / "contrado_back_3130x2362.png", dpi=(K.DPI, K.DPI))
    tin_image(pic).save(OUT / "contrado_tin_1972x1323.png", dpi=(K.DPI, K.DPI))
    print("written to", OUT)


if __name__ == "__main__":
    main()
