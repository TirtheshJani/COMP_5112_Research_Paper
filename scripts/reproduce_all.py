"""Clean-clone reproduction (S8 Q1, Q2): python scripts/reproduce_all.py

Clones the current commit into results/_repro/clone_<commit>, syncs the environment there, rebuilds the print PDF
with scripts/make_print.py, compares it with the committed print/ PDF, runs the full test suite, and writes
results/_repro/report.md. Exit code is non-zero if any step fails.

Not yet covered because the scripts do not exist at this commit: run_sim_dense.py, run_sim_puzzle.py,
make_figures.py, decode_physical.py. Add them to STEPS when their workstreams are merged.
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPRO = ROOT / "results" / "_repro"
PDF = "print/reachy_debruijn_jigsaw.pdf"


def run(cmd: list[str], cwd: Path, log: list[dict]) -> tuple[int, str]:
    env = {k: v for k, v in os.environ.items() if k != "SSL_CERT_FILE"}
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout + p.stderr).strip()
    log.append({"cmd": " ".join(cmd), "cwd": str(cwd), "code": p.returncode, "tail": "\n".join(out.splitlines()[-3:])})
    print(f"[{p.returncode}] {' '.join(cmd)}", flush=True)
    return p.returncode, out


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_pages(path: Path, px_per_mm: float = 4.0) -> list[np.ndarray]:
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
    return ok, (f"PDF bytes differ (sha256 {a[:16]} vs {b[:16]}); rendered pages at 4 px/mm "
                f"{'identical' if ok else 'DIFFER'}; differing pixel values per page: {diffs}")


def main() -> int:
    log: list[dict] = []
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dest = REPRO / f"clone_{commit[:10]}"
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    REPRO.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    if dirty:
        notes.append("Working tree has uncommitted tracked changes; the clone contains only the committed state.")
    failed = False
    comparison = ""
    summary = ""

    code, _ = run(["git", "clone", "--no-hardlinks", "-q", str(ROOT), str(dest)], ROOT, log)
    steps_ok = code == 0
    if steps_ok:
        steps_ok = run(["git", "checkout", "-q", commit], dest, log)[0] == 0
    if steps_ok:
        steps_ok = run(["uv", "sync", "--extra", "dev", "--extra", "print"], dest, log)[0] == 0
    if steps_ok:
        out_pdf = dest / "rebuilt" / "reachy_debruijn_jigsaw.pdf"
        out_pdf.parent.mkdir()
        steps_ok = run(["uv", "run", "python", "scripts/make_print.py", "print/picture_portrait.png", str(out_pdf)], dest, log)[0] == 0
        if steps_ok:
            same, comparison = compare_pdf(dest / PDF, out_pdf)
            failed |= not same
            print(comparison, flush=True)
    if steps_ok:
        code, out = run(["uv", "run", "pytest"], dest, log)
        summary = next((ln for ln in reversed(out.splitlines()) if " passed" in ln or " failed" in ln or " error" in ln), "(no summary line)")
        failed |= code != 0
    failed |= not steps_ok or any(s["code"] != 0 for s in log)

    lines = ["# Reproduction report", "", f"Commit: {commit}", f"Clone: {dest.relative_to(ROOT)}", ""]
    lines += [f"Result: {'FAIL' if failed else 'PASS'}", ""]
    lines += [f"PDF comparison: {comparison or 'not run'}", f"pytest summary: {summary or 'not run'}", ""]
    lines += [f"Note: {n}" for n in notes]
    lines += ["Not covered: run_sim_dense.py, run_sim_puzzle.py, make_figures.py, decode_physical.py (not in the repository at this commit).",
              "print/reachy_debruijn_jigsaw_preview.png is not regenerated: no script in the repository produces it.", "", "## Commands", ""]
    for s in log:
        lines += [f"- exit {s['code']}: `{s['cmd']}` (cwd `{Path(s['cwd']).name}`)"]
    REPRO.joinpath("report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{'FAIL' if failed else 'PASS'}: see {REPRO / 'report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
