"""Probe 6 (P1 Task 6): focus check. At which distance and resolution does the reader read a printed piece?

    python scripts/probes/p6_focus.py --piece 4 2 --turn 0 [--host reachy-mini.local] [--resolution 1280x720]
    python scripts/probes/p6_focus.py --piece 4 2 --turn 0 --resolution 1920x1080

One resolution per run. reachy-mini 1.15.0 cannot switch the camera resolution while it streams: the remote
(WebRTC) client's set_resolution raises "Cannot change resolution while the camera is streaming"
(media/webrtc_client_gstreamer.py:160-166), and the daemon has no HTTP route that sets it (only GET
/api/camera/specs, daemon/app/routers/camera.py:51). So --resolution states what the camera is expected to
stream in this run; the script checks the first frame against it and stops, writing nothing, if they
differ. How to make the robot stream 1920 x 1080 is still open (UNVERIFIED).

For each distance (15, 20, 30 and 40 cm, camera to card) the operator places piece --piece (row and column
as printed, one-based) grid side up over the green card at that distance, turned so that the camera sees it
at --turn (counter-clockwise quarter turns from upright in the camera image, as Read.turn), and presses
Enter. The script then logs FRAMES new frames, each with the PieceReader decision and the pixels per cell
from GridRead.H (px_per_cell: mean image length of one cell's two sides at the centre of the read grid). A
Read with the wrong row, column or turn is a finding (CLAUDE.md rule 5): the frame is saved to
results/findings/ and the script stops. If only the turn differs, check how the piece was placed first.

Writes results/probes/focus_<resolution>.csv (one row per frame of this run) and rebuilds
results/probes/focus_check.md from every focus_*.csv present: a table per (resolution, distance) and the
recommendation. Console in results/probes/p6_<resolution>.txt.

Recommendation rule (recommend): a (resolution, distance) qualifies when at least 90 percent of its frames
are correct reads and none is wrong. Among those, the highest read rate wins; a tie goes to the larger
distance (more room for the hand), then to 1280x720 (the default mode, and the only one whose K the adapter
corrects).
UNVERIFIED: the frames come from get_frame over the WebRTC client of reachy-mini 1.15.0
(media/webrtc_client_gstreamer.py:346) at the size the robot streams (:160-166 above); no probe has run this
on the robot. Remove this mark once p6_<resolution>.txt and focus_check.md are saved.
"""
import argparse
import csv
import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

import cv2
import numpy as np

from jigsaw.reader import PieceReader
from jigsaw.types import Decision, Frame, Read

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "probes"
FINDINGS = ROOT / "results" / "findings"
DISTANCES_CM = (15, 20, 30, 40)
FRAMES = 20
RESOLUTIONS = ("1280x720", "1920x1080")
DEFAULT_RESOLUTION = "1280x720"
MIN_READ_RATE = 0.9
FIELDS = ("resolution", "distance_cm", "frame", "piece", "kind", "decision", "px_per_cell")


def px_per_cell(H: np.ndarray, shape: tuple[int, ...]) -> float:
    """Image length of one cell, averaged over its two sides, at the centre of a grid of shape (rows, cols).

    H maps cell coordinates (x = column, y = row) to image pixels (GridRead.H).
    """
    h, w = shape[:2]
    cells = np.array([[w / 2, h / 2, 1], [w / 2 + 1, h / 2, 1], [w / 2, h / 2 + 1, 1]], dtype=float)
    p = cells @ np.asarray(H, dtype=float).T
    p = p[:, :2] / p[:, 2:]
    return float((np.linalg.norm(p[1] - p[0]) + np.linalg.norm(p[2] - p[0])) / 2)


def kind(decision: Decision, row: int, col: int, turn: int) -> str:
    """"correct", "wrong" or "rejected" against the true piece (zero-based row and column) and its true turn."""
    if not isinstance(decision, Read):
        return "rejected"
    return "correct" if (decision.row, decision.col, decision.turn) == (row, col, turn) else "wrong"


def label(d: Decision) -> str:
    return f"R{d.row + 1} C{d.col + 1} turn {d.turn}" if isinstance(d, Read) else f"reject:{d.reason}"


def summarize(rows: Iterable[dict]) -> list[dict]:
    """One entry per (resolution, distance), ordered by image width then distance."""
    groups: dict[tuple[str, int], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["resolution"], r["distance_cm"]), []).append(r)
    out = []
    for (res, dist), rs in sorted(groups.items(), key=lambda g: (int(g[0][0].split("x")[0]), g[0][1])):
        kinds = [r["kind"] for r in rs]
        px = [r["px_per_cell"] for r in rs if r["px_per_cell"] is not None]
        out.append({"resolution": res, "distance_cm": dist, "frames": len(rs), "correct": kinds.count("correct"),
                    "rejected": kinds.count("rejected"), "wrong": kinds.count("wrong"),
                    "read_rate": kinds.count("correct") / len(rs), "median_px": float(np.median(px)) if px else None,
                    "pieces": sorted({r["piece"] for r in rs})})
    return out


def recommend(summary: Sequence[dict]) -> dict | None:
    """The rule in the module docstring; None when no condition qualifies."""
    ok = [c for c in summary if c["wrong"] == 0 and c["read_rate"] >= MIN_READ_RATE]
    if not ok:
        return None
    return max(ok, key=lambda c: (c["read_rate"], c["distance_cm"], c["resolution"] == DEFAULT_RESOLUTION))


def _px(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.1f}"


def report(summary: Sequence[dict], rec: dict | None) -> str:
    pieces = sorted({p for c in summary for p in c["pieces"]})
    lines = ["# Focus check (probe 6)", "",
             f"Pieces: {', '.join(pieces) or 'none'}. Frames per condition: {FRAMES} requested. "
             "The reader is tested down to 9 px per cell.", "",
             "| Resolution | Distance (cm) | Frames | Correct | Rejected | Wrong | Read rate | Median px per cell |",
             "|---|---|---|---|---|---|---|---|"]
    for c in summary:
        lines.append(f"| {c['resolution']} | {c['distance_cm']} | {c['frames']} | {c['correct']} | {c['rejected']} "
                     f"| {c['wrong']} | {c['read_rate']:.2f} | {_px(c['median_px'])} |")
    lines += ["", "Rule: a condition qualifies with at least 90 percent correct reads and no wrong read; the highest "
              "read rate wins, then the larger distance, then 1280x720.", ""]
    if rec is None:
        lines.append("Recommended: none (no condition had at least 90 percent correct reads and no wrong read).")
    else:
        lines.append(f"Recommended: {rec['resolution']} at {rec['distance_cm']} cm (read rate {rec['read_rate']:.2f}, "
                     f"median {_px(rec['median_px'])} px per cell).")
    return "\n".join(lines) + "\n"


def write_rows(path: Path, rows: Iterable[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "px_per_cell": "" if r["px_per_cell"] is None else r["px_per_cell"]})


def read_rows(paths: Iterable[Path]) -> list[dict]:
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append({**r, "distance_cm": int(r["distance_cm"]), "frame": int(r["frame"]),
                             "px_per_cell": float(r["px_per_cell"]) if r["px_per_cell"] else None})
    return rows


def measure(it: Iterator[Frame], reader: PieceReader, resolution: str, row: int, col: int, turn: int,
            rows: list[dict]) -> int:
    """Prompt for each distance and append one row per frame. 0 when done, 3 after a wrong read."""
    piece = f"R{row + 1} C{col + 1} turn {turn}"
    for dist in DISTANCES_CM:
        input(f"\nPlace piece {piece} grid side up over the green card, {dist} cm from the camera, so that the "
              f"camera sees it at turn {turn}; press Enter. ")
        next(it)                                         # may show the scene from before the prompt
        for i in range(1, FRAMES + 1):
            image = next(it).image
            d = reader.read(image)
            grid = reader.last_grid
            px = None if grid is None else round(px_per_cell(grid.H, grid.cells.shape), 3)
            k = kind(d, row, col, turn)
            rows.append({"resolution": resolution, "distance_cm": dist, "frame": i, "piece": piece, "kind": k,
                         "decision": label(d), "px_per_cell": px})
            print(f"{dist:3d} cm  frame {i:2d}  {k:8s}  {label(d):22s}  px per cell {px}")
            if k == "wrong":
                FINDINGS.mkdir(parents=True, exist_ok=True)
                path = FINDINGS / f"focus_{resolution}_{dist}cm_{i:02d}.png"
                cv2.imwrite(str(path), image)
                print(f"FINDING: piece {piece} read as {label(d)}; frame saved to {path}. Stopping (CLAUDE.md rule 5).")
                return 3
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--piece", nargs=2, type=int, required=True, metavar=("ROW", "COL"),
                    help="the printed piece, row and column one-based as on its front")
    ap.add_argument("--turn", type=int, choices=(0, 1, 2, 3), required=True,
                    help="the turn the camera sees: counter-clockwise quarter turns from upright, as Read.turn")
    ap.add_argument("--resolution", choices=RESOLUTIONS, default=DEFAULT_RESOLUTION,
                    help="what the camera streams in this run (one per run; the SDK cannot switch it)")
    ap.add_argument("--host", default=None, help="robot address (default: reachy-mini.local)")
    a = ap.parse_args()
    from _tee import tee
    tee(f"p6_{a.resolution}")
    from jigsaw.robot.reachy import connect

    w, h = (int(v) for v in a.resolution.split("x"))
    reader = PieceReader()
    robot = connect(a.host)
    rows: list[dict] = []
    try:
        it = robot.frames()
        shape = next(it).image.shape
        if shape[:2] != (h, w):
            print(f"The camera streams {shape[1]}x{shape[0]}, not {a.resolution}; the SDK cannot switch the "
                  "resolution while streaming (see --help). Stopping; nothing written.")
            sys.exit(2)
        status = measure(it, reader, a.resolution, a.piece[0] - 1, a.piece[1] - 1, a.turn, rows)
    finally:
        robot.close()
    write_rows(OUT / f"focus_{a.resolution}.csv", rows)
    summary = summarize(read_rows(sorted(OUT.glob("focus_*.csv"))))
    text = report(summary, recommend(summary))
    (OUT / "focus_check.md").write_text(text, encoding="utf-8")
    print("\n" + text)
    sys.exit(status)


if __name__ == "__main__":
    main()
