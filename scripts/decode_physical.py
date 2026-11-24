"""Offline decode of the physical test (S6 A10 to A12).

    uv run python scripts/decode_physical.py [--frames results/frames] [--out results/physical.csv]
        [--summary results/physical_summary.md] [--sim results/sim_puzzle.csv] [--undistort] [--allow-dirty]

Reads every frame saved by run_physical.py, decodes it with reader.PieceReader (decode_grid, the decoder the
demo uses) and writes one row per frame in the CONTRACTS section 6 schema. kind is computed against the label:
at a nominal angle that is a multiple of 90 only that quarter turn is correct; at an odd multiple of 45 either
adjacent quarter turn is. Then the label check, results/physical_summary.md, and a copy of every wrong frame in
results/findings/<presentation>/ (CLAUDE.md rule 5). Nothing is excluded automatically.

Exit code 0, or 1 when the tree has uncommitted changes and --allow-dirty is not given (nothing is written),
or 2 when any frame was read wrongly (everything is written first).
"""
import argparse
import csv
import json
import shutil
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from jigsaw.experiment.stats import wilson
from jigsaw.reader import PieceReader
from jigsaw.types import Read, U
from jigsaw.vision import undistort as undistort_image

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
COLUMNS = ("piece_row", "piece_col", "angle_deg", "frame_file", "kind", "row", "col", "turn", "reason",
           "visible_cells", "windows", "px_per_cell", "resolution", "timestamp", "commit")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def allowed_turns(angle: int) -> set[int]:
    """Quarter turns that count as correct at a nominal angle (counter-clockwise as the camera sees it)."""
    q, rem = divmod(angle % 360, 90)
    return {q % 4} if rem == 0 else {q % 4, (q + 1) % 4}


def kind(d, row: int, col: int, angle: int) -> str:
    if not isinstance(d, Read):
        return "rejected"
    return "correct" if (d.row, d.col) == (row, col) and d.turn in allowed_turns(angle) else "wrong"


def px_per_cell(H: np.ndarray, shape: tuple[int, ...]) -> float:
    """Image length of one cell at the centre of the read grid, as in scripts/probes/p6_focus.py."""
    h, w = shape[:2]
    p = np.array([[w / 2, h / 2, 1], [w / 2 + 1, h / 2, 1], [w / 2, h / 2 + 1, 1]], float) @ np.asarray(H, float).T
    p = p[:, :2] / p[:, 2:]
    return float((np.linalg.norm(p[1] - p[0]) + np.linalg.norm(p[2] - p[0])) / 2)


def complete_windows(mask: np.ndarray, u: int = U) -> int:
    h, w = mask.shape
    return sum(bool(mask[y:y + u, x:x + u].all()) for y in range(h - u + 1) for x in range(w - u + 1))


def decode_folder(frames_dir: str | Path, commit: str, undistort: bool = False) -> list[dict]:
    """One row per saved frame, in presentation and frame order."""
    frames_dir = Path(frames_dir)
    reader = PieceReader()
    rows = []
    for folder in sorted(p for p in frames_dir.iterdir() if p.is_dir() and not p.name.endswith(".partial")):
        for side_path in sorted(folder.glob("f*.json"), key=lambda p: int(p.stem[1:])):
            side = json.loads(side_path.read_text())
            png = side_path.with_suffix(".png")
            image = cv2.imread(str(png), cv2.IMREAD_COLOR)
            if image is None:   # a capture fault, not a decoder rejection: it must not enter the counts
                raise ValueError(f"cannot read {png}; delete {folder} and run run_physical.py again to capture it")
            if undistort and side["K"] is not None:
                image = undistort_image(image, np.array(side["K"]), np.array(side["D"] or np.zeros(5)))
            d = reader.read(image)
            grid = reader.last_grid
            r, c, a = side["piece_row"], side["piece_col"], side["angle_deg"]
            rows.append({
                "piece_row": r, "piece_col": c, "angle_deg": a, "frame_file": f"{folder.name}/{side_path.stem}.png",
                "kind": kind(d, r, c, a),
                "row": d.row if isinstance(d, Read) else None, "col": d.col if isinstance(d, Read) else None,
                "turn": d.turn if isinstance(d, Read) else None, "reason": None if isinstance(d, Read) else d.reason,
                "visible_cells": int(grid.mask.sum()) if grid is not None else 0,
                "windows": complete_windows(grid.mask) if grid is not None else 0,
                "px_per_cell": round(px_per_cell(grid.H, grid.cells.shape), 3) if grid is not None else None,
                "resolution": side["resolution"], "timestamp": side["time"], "commit": commit})
    return rows


def write_csv(rows: list[dict], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: "" if r[k] is None else r[k] for k in COLUMNS})


def presentation(r: dict) -> tuple[int, int, int]:
    return r["piece_row"], r["piece_col"], r["angle_deg"]


def label_check(rows: list[dict]) -> list[dict]:
    """Presentations in which more than half of the frames decode to one other piece, or to the labelled piece
    at a quarter turn the nominal angle does not allow: probable operator errors, for the author to decide."""
    groups = defaultdict(list)
    for r in rows:
        groups[presentation(r)].append(r)
    flags = []
    for (row, col, angle), rs in groups.items():
        n = len(rs)
        pieces = Counter((r["row"], r["col"]) for r in rs if r["kind"] != "rejected")
        for (pr, pc), k in pieces.items():
            if k > n / 2 and (pr, pc) != (row, col):
                flags.append({"piece_row": row, "piece_col": col, "angle_deg": angle, "problem": "piece",
                              "decoded": f"row {pr + 1}, column {pc + 1}", "frames": f"{k} of {n}"})
        turns = Counter(r["turn"] for r in rs if r["kind"] == "wrong" and (r["row"], r["col"]) == (row, col))
        if sum(turns.values()) > n / 2:
            flags.append({"piece_row": row, "piece_col": col, "angle_deg": angle, "problem": "angle",
                          "decoded": ", ".join(f"turn {t}" for t in sorted(turns)), "frames": f"{sum(turns.values())} of {n}"})
    return flags


def read_sim(path: str | Path) -> list[dict] | None:
    path = Path(path)
    if not path.exists():
        return None
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _share(k: int, n: int) -> str:
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k} ({k / n:.3f}; {lo:.3f} to {hi:.3f})"


def _counts(rs: list[dict]) -> tuple[int, Counter]:
    return len(rs), Counter(r["kind"] for r in rs)


def summary(rows: list[dict], flags: list[dict], sim: list[dict] | None, frames_dir: str, commit: str,
            undistort: bool, sim_path: str) -> str:
    primary = [r for r in rows if r["frame_file"].endswith("/f0.png")]
    right = lambda rs: [r for r in rs if r["angle_deg"] % 90 == 0]          # noqa: E731
    odd = lambda rs: [r for r in rs if r["angle_deg"] % 90 != 0]            # noqa: E731
    lines = [
        "# Physical test summary", "",
        f"Generated by scripts/decode_physical.py at commit {commit} from {frames_dir}: {len(primary)} presentations, "
        f"{len(rows)} frames. Decoder: reader.PieceReader (decode_grid). Undistortion: {'on' if undistort else 'off'}.", "",
        f"Analysis unit: the first frame of each presentation is the primary observation ({len(primary)} presentations). "
        "The other frames of each set are kept for robustness; they are not independent reads.", "",
        "## Counts", "",
        "Each cell: count (proportion; 95 percent Wilson interval). At odd multiples of 45 degrees either adjacent "
        "quarter turn counts as correct; the two angle groups are reported separately.", "",
        "| frames | nominal angles | n | correct | rejected | wrong |", "|---|---|---|---|---|---|"]
    for name, rs in (("primary", primary), ("all", rows)):
        for group, sel in (("multiples of 90", right), ("odd multiples of 45", odd), ("all", lambda x: x)):
            n, k = _counts(sel(rs))
            lines.append(f"| {name} | {group} | {n} | {_share(k['correct'], n)} | {_share(k['rejected'], n)} | "
                         f"{_share(k['wrong'], n)} |")
    wrong = [r for r in rows if r["kind"] == "wrong"]
    n_wrong_primary = sum(r["kind"] == "wrong" for r in primary)
    lines += ["", "## Prediction 1: no wrong read with at most one misread cell", "",
              f"Wrong reads: {n_wrong_primary} of {len(primary)} primary frames, {len(wrong)} of {len(rows)} frames."]
    if wrong:
        lines.append("This script does not count misread cells. Every wrong frame is listed under the label check and "
                     "copied to results/findings/ for inspection; a wrong frame in a flagged presentation may be an "
                     "operator error; inspect the saved frame before classifying it.")
    else:
        lines.append("Holds: no frame was read wrongly.")
    lines += ["", "## Prediction 4: robot against simulation", ""]
    px = [r["px_per_cell"] for r in primary if r["px_per_cell"] is not None]
    rows_sim = [s for s in sim or [] if s["pattern"] == "strong" and s["decoder"] == "grid"]
    compared = right(primary)
    if sim is None:
        lines.append(f"{sim_path} not found: prediction 4 not evaluated.")
    elif not px or not rows_sim or not compared:
        lines.append("No primary frame with a grid, no primary frame at a multiple of 90 degrees, or no strong-pattern "
                     "grid-decoder row in the simulation: not evaluated.")
    else:
        robot_px = statistics.median(px)
        nearest = min({float(s["px_per_cell"]) for s in rows_sim}, key=lambda v: abs(v - robot_px))
        n, k = _counts(compared)
        robot = {x: k[x] / n for x in ("correct", "rejected", "wrong")}
        lines += [f"Robot px per cell (median over primary frames with a grid): {robot_px:.2f}. "
                  f"Nearest simulated px per cell: {nearest:g} ({sim_path}, pattern strong, decoder grid). "
                  "The robot's noise level is not measured, so every simulated condition at that px per cell is listed.", "",
                  "Only nominal angles that are multiples of 90 are compared: there the robot, like the simulation, counts "
                  "one quarter turn as correct. At odd multiples of 45 the robot accepts either adjacent turn, which the "
                  "simulation never does.", "",
                  f"Robot, primary frames at nominal angles that are multiples of 90 ({n} presentations): correct "
                  f"{_share(k['correct'], n)}, rejected {_share(k['rejected'], n)}, wrong {_share(k['wrong'], n)}.", "",
                  "| px per cell | tilt | blur | noise | finger | n | correct | rejected | wrong | robot inside the interval "
                  "(correct, rejected, wrong) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for s in rows_sim:
            if float(s["px_per_cell"]) != nearest:
                continue
            sn = int(s["n"])
            inside = []
            for x in ("correct", "rejected", "wrong"):
                lo, hi = wilson(int(s[x]), sn)
                inside.append("yes" if lo <= robot[x] <= hi else "no")
            lines.append(f"| {s['px_per_cell']} | {s['tilt']} | {s['blur']} | {s['noise']} | {s['finger']} | {sn} | "
                         f"{_share(int(s['correct']), sn)} | {_share(int(s['rejected']), sn)} | {_share(int(s['wrong']), sn)} | "
                         f"{', '.join(inside)} |")
    lines += ["", "## Label check", "",
              "Presentations in which more than half of the frames decode to one other piece, or to the labelled piece at "
              "a quarter turn the nominal angle does not allow. Nothing is excluded automatically; the author decides.", ""]
    if flags:
        lines += ["| presentation | problem | decoded | frames |", "|---|---|---|---|"]
        lines += [f"| r{f['piece_row']}_c{f['piece_col']}_a{f['angle_deg']:03d} | {f['problem']} | {f['decoded']} | "
                  f"{f['frames']} |" for f in flags]
    else:
        lines.append("None flagged.")
    lines += ["", "Wrong frames (label in front coordinates, one-based):", ""]
    if wrong:
        lines += ["| frame file | label | decoded |", "|---|---|---|"]
        lines += [f"| {r['frame_file']} | row {r['piece_row'] + 1}, column {r['piece_col'] + 1}, angle {r['angle_deg']} | "
                  f"row {r['row'] + 1}, column {r['col'] + 1}, turn {r['turn']} |" for r in wrong]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def save_findings(rows: list[dict], frames_dir: str | Path, findings_dir: str | Path) -> list[str]:
    """Copy every wrong frame with its sidecar and decision to findings_dir/<presentation>/."""
    saved = []
    for r in rows:
        if r["kind"] != "wrong":
            continue
        src = Path(frames_dir) / r["frame_file"]
        dst = Path(findings_dir) / r["frame_file"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        side = json.loads(src.with_suffix(".json").read_text())
        side["decision"] = {"row": r["row"], "col": r["col"], "turn": r["turn"]}
        dst.with_suffix(".json").write_text(json.dumps(side, indent=1))
        saved.append(r["frame_file"])
    return saved


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", default=str(RESULTS / "frames"))
    ap.add_argument("--out", default=str(RESULTS / "physical.csv"))
    ap.add_argument("--summary", default=str(RESULTS / "physical_summary.md"))
    ap.add_argument("--sim", default=str(RESULTS / "sim_puzzle.csv"))
    ap.add_argument("--findings", default=str(RESULTS / "findings"))
    ap.add_argument("--undistort", action="store_true", help="undistort frames that carry K and D")
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args(argv)
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    if dirty and not a.allow_dirty:
        print("refusing to run with uncommitted tracked changes; commit them or pass --allow-dirty")
        return 1
    commit = git("rev-parse", "--short", "HEAD") + ("-dirty" if dirty else "")
    rows = decode_folder(a.frames, commit, a.undistort)
    flags = label_check(rows)
    write_csv(rows, a.out)
    Path(a.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(a.summary).write_text(summary(rows, flags, read_sim(a.sim), a.frames, commit, a.undistort, a.sim))
    saved = save_findings(rows, a.frames, a.findings)
    n, k = _counts(rows)
    print(f"{n} frames: {k['correct']} correct, {k['rejected']} rejected, {k['wrong']} wrong; "
          f"{len(flags)} presentations flagged. Wrote {a.out} and {a.summary}.")
    for f in saved:
        print(f"WRONG READ: {f} (copied to {a.findings})")
    return 2 if saved else 0


if __name__ == "__main__":
    raise SystemExit(main())
