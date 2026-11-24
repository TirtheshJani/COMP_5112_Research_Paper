"""Clean-clone reproduction (S8 Q1, Q2): python scripts/reproduce_all.py

Clones the current commit into results/_repro/clone_<commit>, syncs the environment there, rebuilds the print PDF
with scripts/make_print.py, compares it with the committed print/ PDF, runs the full test suite, and writes
results/_repro/report.md. Exit code is non-zero if any step fails.

Not yet covered because the scripts do not exist at this commit: run_sim_dense.py, run_sim_puzzle.py,
make_figures.py, decode_physical.py. Add them to STEPS when their workstreams are merged.
"""
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
NOT_COVERED = ("run_sim_dense.py", "run_sim_puzzle.py", "make_figures.py", "decode_physical.py",
               "print/reachy_debruijn_jigsaw_preview.png (no script produces it)")
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


def main() -> int:
    allow_dirty = "--allow-dirty" in sys.argv[1:]
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

    code, _ = run(["git", "clone", "--no-hardlinks", "-q", str(ROOT), str(dest)], ROOT, log)
    steps_ok = code == 0
    if steps_ok:
        steps_ok = run(["git", "checkout", "-q", commit], dest, log)[0] == 0
    if steps_ok:
        steps_ok = run(["uv", "sync", "--locked", *extras_to_sync()], dest, log)[0] == 0
    if steps_ok:
        out_pdf = dest / "rebuilt" / "reachy_debruijn_jigsaw.pdf"
        out_pdf.parent.mkdir()
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
    failed |= not steps_ok or any(s["code"] != 0 for s in log)

    lines = ["# Reproduction report", "", f"Commit: {commit}", f"Clone: {dest.relative_to(ROOT)}", ""]
    result = "FAIL" if failed else f"PASS (partial: {len(NOT_COVERED)} items not covered)"
    lines += [f"Result: {result}", ""]
    lines += [f"PDF comparison: {comparison or 'not run'}", f"pytest summary: {summary or 'not run'}", ""]
    lines += [f"Note: {n}" for n in notes]
    lines += ["", "## Skipped tests", ""]
    lines += [f"- {n} x {loc}: {reason} ({'expected' if exp else 'UNEXPECTED, run fails'})" for loc, reason, n, exp in skips] or ["- none"]
    lines += [""]
    lines += ["Not covered (not in the repository at this commit, or no script produces it): " + ", ".join(NOT_COVERED), "", "## Commands", ""]
    for s in log:
        lines += [f"- exit {s['code']}: `{s['cmd']}` (cwd `{Path(s['cwd']).name}`)"]
    REPRO.joinpath("report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{result}: see {REPRO / 'report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
