"""Clean-clone reproduction (S8 Q1, Q2): python scripts/reproduce_all.py

Clones the current commit into results/_repro/clone_<commit>, syncs the environment there, rebuilds the print PDF
with scripts/make_print.py, compares it with the committed print/ PDF, runs the full test suite, then (unless
--skip-sims) regenerates the simulations into results/_regen/ inside the clone with the seed and n read from the
committed CSVs, diffs each regenerated CSV against the committed one (every column except commit), reruns
make_figures.py and checks sim_summary.md byte for byte. decode_physical.py runs only if the clone has stored frames.
Writes results/_repro/report.md. Exit code is non-zero if any step fails.

Options: --allow-dirty, --skip-sims (quick run, Result says PASS (partial)), --workers N (puzzle simulation, default 6).
"""
import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPRO = ROOT / "results" / "_repro"
PDF = "print/reachy_debruijn_jigsaw.pdf"

# Skip reasons a clean clone is allowed to show. Substring match on the reason text pytest prints with -rs.
# Anything else, including a missing optional extra, makes the run FAIL.
EXPECTED_SKIPS = (
    # assets/voice/ is git-ignored, so a clone never has the Piper voice file (tests/test_voice_tts.py).
    "Piper voice file absent",
    # Tests that drive the robot are gated on JIGSAW_LIVE=1 and cannot run in a clone.
    "JIGSAW_LIVE=1",
)
NOT_COVERED = ("print/reachy_debruijn_jigsaw_preview.png (no script produces it)",)
KEY_COLS = ("experiment", "pattern", "decoder", "arm", "px_per_cell", "tilt", "blur", "noise", "finger")
SIM_CSVS = ("sim_dense.csv", "sim_puzzle.csv")
SKIPPED_FRAMES = "skipped: no stored frames (physical session pending)"
DPI = 300   # same resolution as tests/test_printing.py
_SKIP_LINE = re.compile(r"^SKIPPED \[(\d+)\] (.+?:\d+): (.*)$")
_SUMMARY = re.compile(r"\d+ (passed|failed|error)")


def classify_pytest(out: str) -> tuple[str, list[tuple[str, str, int, bool]], bool]:
    """Parse pytest -rs output into (summary line, skips, ok). A skip is (location, reason, count, expected).
    ok is False with no summary line, any failure or error, or any skip whose reason is not in EXPECTED_SKIPS."""
    lines = out.splitlines()
    summary = next((ln for ln in reversed(lines) if _SUMMARY.search(ln)), "(no summary line)")
    skips = []
    for ln in lines:
        m = _SKIP_LINE.match(ln.strip())
        if m:
            reason = m.group(3)
            skips.append((m.group(2), reason, int(m.group(1)), any(e in reason for e in EXPECTED_SKIPS)))
    ok = summary != "(no summary line)" and not re.search(r"\d+ (failed|error)", summary) and all(s[3] for s in skips)
    return summary, skips, ok


def extras_to_sync() -> list[str]:
    """Every optional extra in pyproject.toml except robot, as uv sync arguments."""
    extras = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["optional-dependencies"]
    return [a for name in extras if name != "robot" for a in ("--extra", name)]


def run(cmd: list[str], cwd: Path, log: list[dict]) -> tuple[int, str]:
    # SSL_CERT_FILE is removed because on this machine it points at a missing file, which breaks uv. The report records it.
    env = {k: v for k, v in os.environ.items() if k != "SSL_CERT_FILE"}
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout + p.stderr).strip()
    log.append({"cmd": " ".join(cmd), "cwd": str(cwd), "code": p.returncode, "tail": "\n".join(out.splitlines()[-3:])})
    print(f"[{p.returncode}] {' '.join(cmd)}", flush=True)
    return p.returncode, out


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_pages(path: Path, px_per_mm: float = DPI / 25.4) -> list[np.ndarray]:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(path))
    return [pdf[i].render(scale=px_per_mm * 25.4 / 72).to_numpy() for i in range(len(pdf))]


def compare_pdf(committed: Path, rebuilt: Path) -> tuple[bool, str]:
    a, b = sha(committed), sha(rebuilt)
    if a == b:
        return True, f"PDF bytes identical (sha256 {a[:16]})"
    pa, pb = render_pages(committed), render_pages(rebuilt)
    if len(pa) != len(pb):
        return False, f"PDF bytes differ and page counts differ ({len(pa)} vs {len(pb)})"
    diffs = [int((x != y).sum()) if x.shape == y.shape else -1 for x, y in zip(pa, pb)]
    ok = all(d == 0 for d in diffs)
    return ok, (f"PDF bytes differ (sha256 {a[:16]} vs {b[:16]}); rendered pages at {DPI} dpi "
                f"{'identical' if ok else 'DIFFER'}; differing pixel values per page: {diffs}")


def seed_and_n(path: Path) -> tuple[int, int]:
    """The single seed and single n recorded in a committed simulation CSV. Raises ValueError unless each is unique."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path.name} has no rows")
    found = {}
    for col in ("seed", "n"):
        values = sorted({r[col] for r in rows})
        if len(values) != 1:
            raise ValueError(f"{path.name}: column {col} is not unique: {values}")
        found[col] = int(values[0])
    return found["seed"], found["n"]


def _keyed(path: Path) -> tuple[list[str], dict[tuple, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows: dict[tuple, dict[str, str]] = {}
        for r in reader:
            key = tuple(r.get(c, "") for c in KEY_COLS)
            if key in rows:
                raise ValueError(f"{path.name}: duplicate row key {key}")
            rows[key] = r
    return header, rows


def compare_csvs(committed: Path, regenerated: Path) -> dict:
    """Compare two simulation CSVs by row key. Every column except commit must be equal and the row sets must match."""
    h_c, rows_c = _keyed(committed)
    h_r, rows_r = _keyed(regenerated)
    columns: dict[str, int] = {}
    differing = 0
    both = rows_c.keys() & rows_r.keys()
    for key in both:
        bad = [c for c in h_c if c != "commit" and rows_c[key].get(c) != rows_r[key].get(c)]
        differing += bool(bad)
        for c in bad:
            columns[c] = columns.get(c, 0) + 1
    only_c, only_r = len(rows_c.keys() - rows_r.keys()), len(rows_r.keys() - rows_c.keys())
    header_same = h_c == h_r
    return {"rows_compared": len(both), "rows_differing": differing, "columns": dict(sorted(columns.items())),
            "only_committed": only_c, "only_regenerated": only_r, "header_same": header_same,
            "ok": differing == 0 and only_c == 0 and only_r == 0 and header_same}


def same_bytes(a: Path, b: Path) -> bool:
    return a.is_file() and b.is_file() and a.read_bytes() == b.read_bytes()


def has_frames(frames: Path) -> bool:
    return frames.is_dir() and any(p.is_file() for p in frames.rglob("*"))


def describe_diff(name: str, r: dict) -> str:
    cols = ", ".join(f"{c} ({n})" for c, n in r["columns"].items()) or "none"
    head = "" if r["header_same"] else "; HEADER DIFFERS"
    return (f"{name}: rows compared {r['rows_compared']}, rows differing {r['rows_differing']}, columns that differ: {cols}; "
            f"rows only in committed {r['only_committed']}, only in regenerated {r['only_regenerated']}{head} -> "
            f"{'identical except commit' if r['ok'] else 'FAIL'}")


def rebuilt_pdf_path(dest: Path) -> Path:
    """The rebuilt print PDF lives under results/ (git-ignored) so the clone stays clean for the run scripts."""
    return dest / "results" / "_rebuilt" / "reachy_debruijn_jigsaw.pdf"


def clone_dirty_paths(dest: Path) -> list[str]:
    """Paths `git status --porcelain` reports in the clone, tracked or untracked; the run scripts refuse to run if any exist."""
    out = subprocess.run(["git", "status", "--porcelain"], cwd=dest, capture_output=True, text=True, check=True).stdout
    return [line[3:] for line in out.splitlines()]


def run_sims(dest: Path, workers: int, log: list[dict]) -> tuple[bool, list[str]]:
    """Regenerate both simulations in the clone into results/_regen/, diff against the committed CSVs, rerun the figures."""
    dirty = clone_dirty_paths(dest)
    if dirty:
        return False, [f"FAIL: the clone is not clean, so the run scripts would refuse to run (dirty-tree check). Offending paths: {', '.join(dirty)}"]
    regen = dest / "results" / "_regen"
    regen.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    try:
        seed_d, n_d = seed_and_n(dest / "results" / "sim_dense.csv")
        seed_p, n_p = seed_and_n(dest / "results" / "sim_puzzle.csv")
    except (ValueError, OSError) as e:
        return False, [f"FAIL: cannot read seed and n from the committed CSVs: {e}"]
    lines.append(f"Committed seed and n: dense seed {seed_d} n {n_d}; puzzle seed {seed_p} n {n_p}.")
    ok = True
    for script, seed, n, extra in (("run_sim_dense.py", seed_d, n_d, []), ("run_sim_puzzle.py", seed_p, n_p, ["--workers", str(workers)])):
        name = "sim_dense.csv" if "dense" in script else "sim_puzzle.csv"
        findings = f"results/_regen/findings_{name[4:-4]}"
        code, _ = run(["uv", "run", "python", f"scripts/{script}", "--seed", str(seed), "--n", str(n),
                       "--out", f"results/_regen/{name}", "--findings", findings, *extra], dest, log)
        if code != 0 or not (regen / name).is_file():
            ok = False
            lines.append(f"{name}: FAIL, {script} exited {code}")
            continue
        try:
            r = compare_csvs(dest / "results" / name, regen / name)
        except ValueError as e:
            ok = False
            lines.append(f"{name}: FAIL, {e}")
            continue
        ok &= r["ok"]
        lines.append(describe_diff(name, r))
    if ok:
        code, _ = run(["uv", "run", "python", "scripts/make_figures.py", "--puzzle", "results/_regen/sim_puzzle.csv",
                       "--dense", "results/_regen/sim_dense.csv", "--out-dir", "results/_regen"], dest, log)
        same = code == 0 and same_bytes(dest / "results" / "sim_summary.md", regen / "sim_summary.md")
        ok &= same
        lines.append(f"sim_summary.md byte-identical to committed: {'yes' if same else 'NO, FAIL'} (PDFs not compared byte for byte)")
    else:
        lines.append("make_figures.py not run: a simulation step failed.")
    return ok, lines


def run_physical(dest: Path, log: list[dict]) -> tuple[str, bool]:
    if not has_frames(dest / "results" / "frames"):
        return SKIPPED_FRAMES, True
    code, out = run(["uv", "run", "python", "scripts/decode_physical.py", "--out", "results/_regen/physical.csv",
                     "--summary", "results/_regen/physical_summary.md", "--findings", "results/_regen/findings_physical"], dest, log)
    return f"exit {code}: {(out.splitlines() or [''])[-1]}", code == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--skip-sims", action="store_true", help="skip the simulation regeneration, diff and figure steps")
    ap.add_argument("--workers", type=int, default=6, help="worker processes for run_sim_puzzle.py (16 ran the laptop out of memory)")
    args = ap.parse_args(sys.argv[1:])
    allow_dirty = args.allow_dirty
    log: list[dict] = []
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty and not allow_dirty:
        print("refusing to run with uncommitted tracked changes; commit them or pass --allow-dirty")
        return 2
    dest = REPRO / f"clone_{commit[:10]}"
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    REPRO.mkdir(parents=True, exist_ok=True)
    notes: list[str] = ["SSL_CERT_FILE unset in every subprocess (reproduction env differs from the shell env in that variable only)."]
    if dirty:
        notes.append("Run with --allow-dirty. Working tree has uncommitted tracked changes; the clone contains only the committed state.")
    failed = False
    comparison = ""
    summary = ""
    skips: list[tuple[str, str, int, bool]] = []
    sim_lines: list[str] = []
    physical = "not run"
    skipped_steps: list[str] = []

    code, _ = run(["git", "clone", "--no-hardlinks", "-q", str(ROOT), str(dest)], ROOT, log)
    steps_ok = code == 0
    if steps_ok:
        steps_ok = run(["git", "checkout", "-q", commit], dest, log)[0] == 0
    if steps_ok:
        steps_ok = run(["uv", "sync", "--locked", *extras_to_sync()], dest, log)[0] == 0
    if steps_ok:
        out_pdf = rebuilt_pdf_path(dest)
        out_pdf.parent.mkdir(parents=True)
        steps_ok = run(["uv", "run", "python", "scripts/make_print.py", "print/picture_portrait.png", str(out_pdf)], dest, log)[0] == 0
        if steps_ok:
            same, comparison = compare_pdf(dest / PDF, out_pdf)
            failed |= not same
            print(comparison, flush=True)
    if steps_ok:
        code, out = run(["uv", "run", "pytest", "-rs"], dest, log)
        summary, skips, ok = classify_pytest(out)
        failed |= not ok
        failed |= code != 0
        if steps_ok and args.skip_sims:
            skipped_steps = ["simulation regeneration (run_sim_dense.py, run_sim_puzzle.py)", "CSV diff", "make_figures.py check"]
        elif steps_ok:
            sim_ok, sim_lines = run_sims(dest, args.workers, log)
            failed |= not sim_ok
        if steps_ok:
            physical, phys_ok = run_physical(dest, log)
            failed |= not phys_ok
    failed |= not steps_ok or any(s["code"] != 0 for s in log)

    lines = ["# Reproduction report", "", f"Commit: {commit}", f"Clone: {dest.relative_to(ROOT)}", ""]
    result = "FAIL" if failed else ("PASS (partial; skipped: " + "; ".join(skipped_steps) + ")" if skipped_steps else "PASS")
    lines += [f"Result: {result}", ""]
    lines += [f"PDF comparison: {comparison or 'not run'}", f"pytest summary: {summary or 'not run'}",
              f"Physical decode: {physical}", ""]
    if skipped_steps:
        lines += ["Skipped by --skip-sims: " + "; ".join(skipped_steps), ""]
    if sim_lines:
        lines += ["## Simulation regeneration", ""] + sim_lines + [""]
    lines += [f"Note: {n}" for n in notes]
    lines += ["", "## Skipped tests", ""]
    lines += [f"- {n} x {loc}: {reason} ({'expected' if exp else 'UNEXPECTED, run fails'})" for loc, reason, n, exp in skips] or ["- none"]
    lines += [""]
    lines += ["Not covered (no script produces it): " + ", ".join(NOT_COVERED), "", "## Commands", ""]
    for s in log:
        lines += [f"- exit {s['code']}: `{s['cmd']}` (cwd `{Path(s['cwd']).name}`)"]
    REPRO.joinpath("report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{result}: see {REPRO / 'report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
