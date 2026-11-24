"""Draw an original front picture for the jigsaw: a mountain lake at dusk.

Output: a PNG covering the whole puzzle plus bleed, at 300 dpi.
Usage: python scripts/make_picture.py [out.png [WIDTH_MM HEIGHT_MM BLEED_MM]]
The committed print/picture_portrait.png is the default size (jigsaw.geometry W x H plus jigsaw.printing BLEED each side):
    python scripts/make_picture.py print/picture_portrait.png
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from jigsaw import geometry as geo
from jigsaw import printing

DPI = 300
MM = DPI / 25.4
SS = 2  # supersampling factor


def parse_args(argv: list[str]) -> tuple[str, float, float, float]:
    """(out, width_mm, height_mm, bleed_mm) from argv[1:]; sizes default to the puzzle and the print bleed."""
    out = argv[1] if len(argv) > 1 else "picture.png"
    if len(argv) > 4:
        return (out, *(float(v) for v in argv[2:5]))
    return out, geo.W, geo.H, printing.BLEED


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(top, mid, bottom, h, split=0.6):
    t = np.linspace(0, 1, h)[:, None]
    top, mid, bottom = (np.array(c, float) for c in (top, mid, bottom))
    a = np.clip(t / split, 0, 1)
    b = np.clip((t - split) / (1 - split), 0, 1)
    col = np.where(t < split, top + (mid - top) * a, mid + (bottom - mid) * b)
    return col


def ridge(n, rough, rng):
    """1-D midpoint displacement profile with n points in [0, 1]."""
    size = 1
    while size < n:
        size *= 2
    pts = np.zeros(size + 1)
    pts[0], pts[-1] = rng.uniform(0.3, 0.7, 2)
    step, scale = size, 1.0
    while step > 1:
        half = step // 2
        for i in range(half, size, step):
            pts[i] = (pts[i - half] + pts[i + half]) / 2 + rng.normal(0, scale)
        scale *= rough
        step = half
    pts = (pts - pts.min()) / (pts.max() - pts.min() + 1e-9)
    return np.interp(np.linspace(0, size, n), np.arange(size + 1), pts)


def main(argv: list[str]) -> None:
    out, W_MM, H_MM, BLEED = parse_args(argv)
    W = int(round((W_MM + 2 * BLEED) * MM)) * SS
    H = int(round((H_MM + 2 * BLEED) * MM)) * SS
    rng = np.random.default_rng(7)
    HORIZON = int(0.56 * H)
    img = np.zeros((H, W, 3), float)

    # Sky
    sky = gradient((14, 22, 64), (120, 70, 140), (250, 160, 90), HORIZON, split=0.55)
    img[:HORIZON] = sky[:, None, :]

    # Sun glow and disk
    sx, sy, sr = int(0.66 * W), int(HORIZON - 0.06 * H), int(0.055 * H)
    yy, xx = np.mgrid[0:HORIZON, 0:W]
    d = np.hypot(xx - sx, yy - sy)
    glow = np.exp(-(d / (sr * 4.0)) ** 2)[..., None]
    img[:HORIZON] = img[:HORIZON] * (1 - 0.55 * glow) + np.array([255, 200, 120]) * 0.55 * glow

    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)

    # Stars in the upper sky
    for _ in range(900):
        x = rng.uniform(0, W)
        y = rng.beta(0.8, 3.0) * HORIZON * 0.75
        r = rng.choice([1, 1, 1, 2, 2, 3, 4]) * SS
        b = int(rng.uniform(170, 255))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 20)))
    # A few bright four-point stars
    for _ in range(14):
        x, y = rng.uniform(0, W), rng.uniform(0.03, 0.30) * H
        L = rng.uniform(10, 22) * SS
        dr.line([x - L, y, x + L, y], fill=(255, 250, 230), width=2 * SS)
        dr.line([x, y - L, x, y + L], fill=(255, 250, 230), width=2 * SS)
        dr.ellipse([x - 3 * SS, y - 3 * SS, x + 3 * SS, y + 3 * SS], fill=(255, 255, 240))

    # Crescent moon, upper left
    mx, my, mr = int(0.46 * W), int(0.35 * H), int(0.042 * H)
    moon_mask = Image.new("L", im.size, 0)
    mm = ImageDraw.Draw(moon_mask)
    mm.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=255)
    off = int(0.42 * mr)
    mm.ellipse([mx - mr + off, my - mr - off // 3, mx + mr + off, my + mr - off // 3], fill=0)
    im.paste((250, 244, 220), (0, 0), moon_mask)
    dr = ImageDraw.Draw(im)

    # Clouds lit from below
    cloud_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud_layer)
    for cx, cy, cw in [(0.30, 0.30, 0.16), (0.52, 0.22, 0.12), (0.84, 0.34, 0.18), (0.08, 0.40, 0.12)]:
        for _ in range(9):
            ex = (cx + rng.uniform(-cw / 2, cw / 2)) * W
            ey = (cy + rng.uniform(-0.015, 0.015)) * H
            ew, eh = rng.uniform(0.04, 0.09) * W, rng.uniform(0.012, 0.025) * H
            cd.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=(255, 175, 160, 120))
    cloud_layer = cloud_layer.filter(ImageFilter.GaussianBlur(6 * SS))
    im = Image.alpha_composite(im.convert("RGBA"), cloud_layer)
    dr = ImageDraw.Draw(im)

    # Mountain ranges, far to near
    ranges = [
        (0.30, 0.20, (150, 110, 170), 0.60, False),
        (0.38, 0.14, (95, 70, 130), 0.55, False),
        (0.47, 0.09, (55, 45, 95), 0.50, False),
    ]
    for top_frac, amp_frac, col, rough, snow in ranges:
        prof = ridge(W, rough, rng)
        ys = HORIZON - (amp_frac * H) * (0.25 + prof) - (HORIZON - top_frac * H) * 0.0
        ys = np.minimum(ys, HORIZON)
        poly = [(0, HORIZON)] + [(x, float(ys[x])) for x in range(0, W, 4)] + [(W, HORIZON)]
        dr.polygon(poly, fill=col)
        if snow:
            snow_line = np.percentile(ys, 8)
            for x in range(0, W, 4):
                if ys[x] < snow_line:
                    dr.line([(x, ys[x]), (x, snow_line + (snow_line - ys[x]) * 0.35)],
                            fill=(240, 232, 245), width=4)

    # Lake: reflected sky, darker, with ripples
    lake_h = H - HORIZON
    arr = np.array(im.convert("RGB")).astype(float)
    refl = arr[HORIZON - 1::-1][:lake_h]
    lake = refl * 0.55 + np.array([10, 20, 50]) * 0.45
    arr[HORIZON:HORIZON + lake.shape[0]] = lake
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    for _ in range(700):
        y = HORIZON + rng.beta(1.2, 2.2) * lake_h * 0.9
        x = rng.uniform(0, W)
        L = rng.uniform(20, 120) * SS * (0.5 + (y - HORIZON) / lake_h)
        c = int(rng.uniform(120, 200))
        dr.line([x, y, x + L, y], fill=(c, c, min(255, c + 40)), width=SS)


    # Sailboat
    bx, by = int(0.40 * W), int(HORIZON + 0.11 * H)
    dr.polygon([(bx - 70 * SS, by), (bx + 70 * SS, by), (bx + 50 * SS, by + 22 * SS), (bx - 50 * SS, by + 22 * SS)],
               fill=(40, 25, 30))
    dr.line([bx, by, bx, by - 150 * SS], fill=(40, 25, 30), width=5 * SS)
    dr.polygon([(bx + 4 * SS, by - 145 * SS), (bx + 4 * SS, by - 12 * SS), (bx + 90 * SS, by - 12 * SS)],
               fill=(250, 235, 215))
    dr.polygon([(bx - 4 * SS, by - 120 * SS), (bx - 4 * SS, by - 12 * SS), (bx - 60 * SS, by - 12 * SS)],
               fill=(235, 200, 175))

    # Birds
    for _ in range(9):
        x, y = rng.uniform(0.35, 0.95) * W, rng.uniform(0.18, 0.40) * H
        s = rng.uniform(10, 22) * SS
        dr.line([(x - s, y - s * 0.4), (x, y), (x + s, y - s * 0.4)], fill=(30, 20, 40), width=3 * SS)

    # Shores with pine trees
    shore_col = (18, 28, 30)


    def pine(x, base, h):
        w = h * 0.36
        for t in range(4):
            y0 = base - h * (0.18 + 0.22 * t)
            ww = w * (1 - 0.2 * t)
            dr.polygon([(x - ww, y0 + h * 0.2), (x + ww, y0 + h * 0.2), (x, y0 - h * 0.12)], fill=shore_col)
        dr.rectangle([x - h * 0.03, base - h * 0.2, x + h * 0.03, base], fill=shore_col)


    left = [(0, H), (0, HORIZON + 0.18 * H), (0.12 * W, HORIZON + 0.24 * H), (0.30 * W, H * 0.95), (0.34 * W, H)]
    right = [(W, H), (W, HORIZON + 0.10 * H), (0.82 * W, HORIZON + 0.20 * H), (0.62 * W, H * 0.93), (0.58 * W, H)]
    bottom = [(0, H * 0.965), (W, H * 0.955), (W, H), (0, H)]
    for poly in (left, right, bottom):
        dr.polygon(poly, fill=shore_col)
    for _ in range(26):
        x = rng.uniform(0.0, 0.20) * W
        pine(x, HORIZON + rng.uniform(0.20, 0.30) * H, rng.uniform(0.16, 0.30) * H)
    for _ in range(22):
        x = rng.uniform(0.84, 1.0) * W
        pine(x, HORIZON + rng.uniform(0.13, 0.25) * H, rng.uniform(0.14, 0.26) * H)

    # Shore rocks and fireflies so the dark foreground pieces have detail
    for _ in range(40):
        x = rng.choice([rng.uniform(0.02, 0.30), rng.uniform(0.62, 0.98), rng.uniform(0.0, 1.0)]) * W
        y = rng.uniform(0.955, 0.995) * H if rng.random() < 0.4 else None
        if y is None:
            continue
        rw, rh = rng.uniform(25, 60) * SS, rng.uniform(12, 25) * SS
        g = int(rng.uniform(70, 110))
        dr.ellipse([x - rw, y - rh, x + rw, y + rh], fill=(g, g + 8, g + 15))
    for _ in range(160):
        if rng.random() < 0.5:
            x = rng.uniform(0.0, 0.26) * W
            y = rng.uniform(HORIZON + 0.08 * H, 0.99 * H)
        else:
            x = rng.uniform(0.70, 1.0) * W
            y = rng.uniform(HORIZON + 0.05 * H, 0.99 * H)
        r = rng.uniform(2.5, 5.5) * SS
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 235, 120))

    # Cabin with a lit window on the right shore
    cx, cy = int(0.76 * W), int(HORIZON + 0.205 * H)
    dr.rectangle([cx - 60 * SS, cy - 50 * SS, cx + 60 * SS, cy], fill=(60, 35, 30))
    dr.polygon([(cx - 75 * SS, cy - 48 * SS), (cx + 75 * SS, cy - 48 * SS), (cx, cy - 100 * SS)], fill=(35, 20, 20))
    dr.rectangle([cx - 30 * SS, cy - 35 * SS, cx - 5 * SS, cy - 12 * SS], fill=(255, 205, 110))
    dr.rectangle([cx + 15 * SS, cy - 30 * SS, cx + 40 * SS, cy], fill=(30, 18, 15))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - 90 * SS, cy - 70 * SS, cx + 40 * SS, cy + 20 * SS], fill=(255, 190, 90, 60))
    im = Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(25 * SS))).convert("RGB")

    im = im.resize((W // SS, H // SS), Image.LANCZOS)
    im.save(out, dpi=(DPI, DPI))
    print(out, im.size)


if __name__ == "__main__":
    main(sys.argv)
