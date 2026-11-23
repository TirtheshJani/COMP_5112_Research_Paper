"""Read the cells on the back of a frameless jigsaw piece (CONTRACTS.md section 3).

The piece is shown over a strongly coloured reading mat. Paper (black, white and the gray grid lines) has
low colour saturation, the mat and skin do not, so the piece silhouette is the largest low-saturation
blob. Inside it:

1. the grid direction comes from the 4-fold average of gradient directions;
2. the image is turned so the grid is upright, and pitch and phase come from edge profiles;
3. every grid line is located band by band and fitted as a straight line, and the line intersections
   give a homography from cell coordinates to the image, which absorbs perspective;
4. each cell is sampled at its centre; a cell counts as visible when its whole square lies inside the
   (eroded) silhouette and its centre is uniform.
"""
import cv2
import numpy as np

from jigsaw.types import GridRead, Reject

SAT_MAX = 70          # paper is below this saturation (0-255)
MIN_AREA = 0.005      # silhouette area as a fraction of the frame
MIN_CONTRAST = 40     # gray levels between black and white cells
DARK_MAX = 70         # pixels darker than this count as paper whatever their saturation


def undistort(image: np.ndarray, K: np.ndarray, D: np.ndarray) -> np.ndarray:
    return cv2.undistort(image, K, D)


def paper_mask(bgr: np.ndarray) -> np.ndarray | None:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # dark pixels have unreliable saturation, so anything dark counts as paper (black cells)
    m = ((hsv[..., 1] < SAT_MAX) | (hsv[..., 2] < DARK_MAX)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n < 2:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[k, cv2.CC_STAT_AREA] < MIN_AREA * m.size:
        return None
    m = (lab == k).astype(np.uint8) * 255
    # fill holes (dark cells are low saturation too, so holes are rare, but glare can make them)
    flood = m.copy()
    cv2.floodFill(flood, np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8), (0, 0), 255)
    return m | cv2.bitwise_not(flood)


def _grid_angle(gx, gy, weight) -> float:
    z = np.sum(weight * (gx * gx + gy * gy) * np.exp(4j * np.arctan2(gy, gx)))
    return float(np.angle(z) / 4)


def _period(profile: np.ndarray, lo: int, hi: int) -> float | None:
    p = profile - cv2.blur(profile.reshape(1, -1).astype(np.float32), (2 * hi + 1, 1)).ravel()
    n = len(p)
    if n < 3 * lo or hi <= lo:
        return None
    ac = np.array([np.dot(p[:n - L], p[L:]) / (n - L) for L in range(hi + 2)])
    cand = [L for L in range(lo, hi + 1) if ac[L] > ac[L - 1] and ac[L] >= ac[L + 1] and ac[L] > 0]
    if not cand:
        return None
    best = max(ac[L] for L in cand)
    L = min(c for c in cand if ac[c] >= 0.6 * best)          # fundamental, not a multiple
    a, b, c = ac[L - 1], ac[L], ac[L + 1]
    d = a - 2 * b + c
    return L + (0.5 * (a - c) / d if d != 0 else 0.0)


def _phase(profile: np.ndarray, p: float) -> float:
    xs = np.arange(len(profile))
    best, arg = -1.0, 0.0
    for f in np.arange(0, p, 0.25):
        pts = np.arange(f, len(profile) - 1, p)
        v = np.interp(pts, xs, profile).sum()
        if v > best:
            best, arg = v, f
    return arg


def _fit_lines(edge, inner, pos, other, p, vertical):
    """Locate each grid line band by band; return {index: (a, b)} with coord = a + b * t along the line."""
    out = {}
    h, w = edge.shape
    for m, x in enumerate(pos):
        pts = []
        for y in other[:-1]:
            t0, t1 = int(y + 0.2 * p), int(y + 0.8 * p)
            s0, s1 = int(round(x - 0.4 * p)), int(round(x + 0.4 * p)) + 1
            if vertical:
                if s0 < 0 or s1 > w or t0 < 0 or t1 > h or not inner[t0:t1, s0:s1].all():
                    continue
                prof = edge[t0:t1, s0:s1].sum(axis=0)
            else:
                if s0 < 0 or s1 > h or t0 < 0 or t1 > w or not inner[s0:s1, t0:t1].all():
                    continue
                prof = edge[s0:s1, t0:t1].sum(axis=1)
            k = int(np.argmax(prof))
            if 0 < k < len(prof) - 1:
                a, b, c = prof[k - 1], prof[k], prof[k + 1]
                d = a - 2 * b + c
                k = k + (0.5 * (a - c) / d if d != 0 else 0.0)
            pts.append((0.5 * (t0 + t1), s0 + k))
        if len(pts) < 3:
            continue
        t, s = np.array(pts).T
        keep = np.ones(len(t), bool)
        for _ in range(3):
            A = np.vstack([np.ones(keep.sum()), t[keep]]).T
            coef, *_ = np.linalg.lstsq(A, s[keep], rcond=None)
            res = np.abs(s - (coef[0] + coef[1] * t))
            keep = res < 0.12 * p
            if keep.sum() < 3:
                break
        if keep.sum() >= 3:
            out[m] = (float(coef[0]), float(coef[1]))
    return out


def read_grid(bgr: np.ndarray) -> GridRead | Reject:
    if bgr.ndim == 2:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGR)
    mask = paper_mask(bgr)
    if mask is None:
        return Reject("no_grid")
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    area = float((mask > 0).sum())
    e = max(3, int(0.02 * np.sqrt(area)))
    inner = cv2.erode(mask, np.ones((2 * e + 1, 2 * e + 1), np.uint8)) > 0
    g = cv2.GaussianBlur(gray, (0, 0), 0.8)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    theta = _grid_angle(gx, gy, inner)

    hgt, wid = gray.shape
    ys, xs = np.nonzero(mask)
    centre = (float(xs.mean()), float(ys.mean()))
    best = None
    for sign in (1, -1):       # pick the rotation direction that makes the grid upright
        R = cv2.getRotationMatrix2D(centre, sign * np.degrees(theta), 1.0)
        gr = cv2.warpAffine(g, R, (wid, hgt), flags=cv2.INTER_LINEAR)
        ir = cv2.warpAffine(inner.astype(np.uint8), R, (wid, hgt), flags=cv2.INTER_NEAREST) > 0
        ex = np.abs(cv2.Sobel(gr, cv2.CV_32F, 1, 0, ksize=3)) * ir
        ey = np.abs(cv2.Sobel(gr, cv2.CV_32F, 0, 1, ksize=3)) * ir
        resid = abs(_grid_angle(cv2.Sobel(gr, cv2.CV_32F, 1, 0, ksize=3),
                                cv2.Sobel(gr, cv2.CV_32F, 0, 1, ksize=3), ir))
        if best is None or resid < best[0]:
            best = (resid, R, gr, ir, ex, ey)
    _, R, gr, ir, ex, ey = best
    if ir.sum() < 100:
        return Reject("no_grid")
    side = np.sqrt(ir.sum())
    lo, hi = max(4, int(side / 30)), max(8, int(side / 4))
    px, py = _period(ex.sum(axis=0), lo, hi), _period(ey.sum(axis=1), lo, hi)
    if px is None or py is None or abs(px - py) > 0.2 * max(px, py):
        return Reject("no_grid")
    p = 0.5 * (px + py)
    rows, cols = np.nonzero(ir)
    fx, fy = _phase(ex.sum(axis=0), px), _phase(ey.sum(axis=1), py)
    xpos = np.arange(fx + np.floor((cols.min() - fx) / px) * px, cols.max() + px, px)
    ypos = np.arange(fy + np.floor((rows.min() - fy) / py) * py, rows.max() + py, py)
    vlines = _fit_lines(ex, ir, xpos, ypos, p, vertical=True)
    hlines = _fit_lines(ey, ir, ypos, xpos, p, vertical=False)
    src, dst = [], []
    for m, (a1, b1) in vlines.items():          # x = a1 + b1 * y
        for n, (a2, b2) in hlines.items():      # y = a2 + b2 * x
            y = (a2 + b2 * a1) / (1 - b2 * b1)
            x = a1 + b1 * y
            src.append((m, n))
            dst.append((x, y))
    if len(src) < 8:
        return Reject("no_grid")
    Hr, ok = cv2.findHomography(np.float32(src), np.float32(dst), cv2.RANSAC, 0.15 * p)
    if Hr is None:
        return Reject("no_grid")
    Rinv = cv2.invertAffineTransform(R)
    H = np.vstack([Rinv, [0, 0, 1]]) @ Hr       # cell coords -> original image

    nx, ny = len(xpos) - 1, len(ypos) - 1
    gcx, gcy = np.meshgrid(np.arange(nx) + 0.5, np.arange(ny) + 0.5)
    centres = cv2.perspectiveTransform(np.float32(np.dstack([gcx, gcy]).reshape(-1, 1, 2)), H).reshape(ny, nx, 2)
    corners = {}
    for dx in (0.08, 0.92):
        for dy in (0.08, 0.92):
            q = np.dstack([gcx - 0.5 + dx, gcy - 0.5 + dy]).reshape(-1, 1, 2)
            corners[(dx, dy)] = cv2.perspectiveTransform(np.float32(q), H).reshape(ny, nx, 2)
    gray_s = cv2.GaussianBlur(gray, (0, 0), max(0.5, 0.08 * p))
    vals = cv2.remap(gray_s, centres[..., 0].astype(np.float32), centres[..., 1].astype(np.float32),
                     cv2.INTER_LINEAR, borderValue=-1)
    inner_strict = cv2.erode(mask, np.ones((3, 3), np.uint8)) > 0
    vis = np.ones((ny, nx), bool)
    for pts in list(corners.values()) + [centres]:
        xi = np.clip(np.round(pts[..., 0]).astype(int), 0, wid - 1)
        yi = np.clip(np.round(pts[..., 1]).astype(int), 0, hgt - 1)
        inside = (pts[..., 0] >= 0) & (pts[..., 0] < wid) & (pts[..., 1] >= 0) & (pts[..., 1] < hgt)
        vis &= inside & inner_strict[yi, xi]
    # uniform centre: the four quarter points between centre and corners agree with the centre
    for pts in corners.values():
        mid = 0.5 * (pts + centres)
        v2 = cv2.remap(gray_s, mid[..., 0].astype(np.float32), mid[..., 1].astype(np.float32),
                       cv2.INTER_LINEAR, borderValue=-1)
        vis &= np.abs(v2 - vals) < 0.35 * max(1.0, np.ptp(vals[vis]) if vis.any() else 1.0)
    if vis.sum() < 25:
        return Reject("no_window")
    v = vals[vis].astype(np.float32)
    thr = float(v.mean())                      # two-class threshold (isodata), robust to pure 0/255 data
    for _ in range(20):
        lo_c, hi_c = v[v <= thr], v[v > thr]
        if len(lo_c) == 0 or len(hi_c) == 0:
            break
        thr = 0.5 * (lo_c.mean() + hi_c.mean())
    dark, light = v[v <= thr], v[v > thr]
    if len(dark) == 0 or len(light) == 0 or light.mean() - dark.mean() < MIN_CONTRAST:
        return Reject("low_contrast")
    # a cell too close to the threshold is not read confidently
    vis &= np.abs(vals - thr) > 0.2 * (light.mean() - dark.mean())
    cells = (vals <= thr).astype(np.uint8)
    return GridRead(cells, vis, H)
