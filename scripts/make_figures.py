"""Figures and summary for S2: uv run python scripts/make_figures.py --puzzle results/sim_puzzle.csv --dense results/sim_dense.csv --out-dir results

Writes fig_puzzle.pdf, fig_dense.pdf and sim_summary.md from the two CSVs alone. Every interval is a Wilson 95 percent
interval from jigsaw.experiment.stats.wilson. In the puzzle figure the counts are pooled over blur, noise and tilt at
each px per cell (sum k and n, then the interval); finger 0 and finger 1 stay separate.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from jigsaw.experiment.stats import wilson  # noqa: E402

matplotlib.rcParams.update({
    "pdf.fonttype": 42, "ps.fonttype": 42, "font.family": "sans-serif", "font.size": 7,
    "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.spines.top": False, "axes.spines.right": False,
})

# Okabe-Ito
COLOUR = {"strong": "#0072B2", "orient": "#D55E00"}
STYLE = {"single": ("o", "-"), "grid": ("s", "--")}
DECODER_LABEL = {"single": "single window", "grid": "four windows"}
COUNTS = ("n", "correct", "rejected", "wrong", "wrong_le1_misread", "reads_le1_misread")


def load(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            for c in COUNTS:
                r[c] = int(r[c])
            rows.append(r)
    return rows


def pool(rows: list[dict], key) -> dict:
    """Sum the count columns of the rows that share key(row)."""
    out: dict = defaultdict(lambda: dict.fromkeys(COUNTS, 0))
    for r in rows:
        for c in COUNTS:
            out[key(r)][c] += r[c]
    return out


def rate(k: int, n: int) -> tuple[float, float, float]:
    lo, hi = wilson(k, n)
    return k / n, lo, hi


def errbars(rates: list[tuple[float, float, float]]) -> tuple[list[float], list[list[float]]]:
    p = [r[0] for r in rates]
    return p, [[max(0.0, r[0] - r[1]) for r in rates], [max(0.0, r[2] - r[0]) for r in rates]]


def fig_puzzle(rows: list[dict], path: Path) -> None:
    pooled = pool(rows, lambda r: (r["pattern"], r["decoder"], int(r["finger"]), int(r["px_per_cell"])))
    pxs = sorted({k[3] for k in pooled})
    fingers = sorted({k[2] for k in pooled})
    series = [(p, d) for p in ("strong", "orient") for d in ("single", "grid")]
    fig, axes = plt.subplots(3, len(fingers), figsize=(3.4, 5.2), sharex=True, squeeze=False)
    for ci, finger in enumerate(fingers):
        for ri, field in enumerate(("correct", "rejected", "wrong")):
            ax = axes[ri][ci]
            for si, (pat, dec) in enumerate(series):
                xs, rs = [], []
                for xi, px in enumerate(pxs):
                    cell = pooled.get((pat, dec, finger, px))
                    if cell and cell["n"] > 0:
                        xs.append(xi + (si - 1.5) * 0.09)
                        rs.append(rate(cell[field], cell["n"]))
                if not xs:
                    continue
                y, e = errbars(rs)
                marker, ls = STYLE[dec]
                ax.errorbar(xs, y, yerr=e, color=COLOUR[pat], marker=marker, ls=ls, lw=0.8, ms=3, capsize=1.5,
                            elinewidth=0.7, label=f"{pat}, {DECODER_LABEL[dec]}")
            ax.set_ylim(-0.03, 1.03) if field != "wrong" else ax.set_ylim(bottom=-0.002)
            if ci == 0:
                ax.set_ylabel(f"{field} rate")
            if ri == 0:
                ax.set_title(f"finger {finger}", fontsize=7)
            if ri == 2:
                ax.set_xticks(range(len(pxs)), [str(p) for p in pxs])
                ax.set_xlabel("px per cell (pooled over blur, noise, tilt)")
    axes[0][0].legend(frameon=False, loc="lower right", handlelength=2.2)
    fig.tight_layout()
    fig.savefig(path, format="pdf")
    plt.close(fig)


def fig_dense(rows: list[dict], path: Path) -> None:
    single = [r for r in rows if r["decoder"] == "single"]
    forced = pool([r for r in single if r["arm"] == "forced1"], lambda r: r["pattern"])
    noise_rows = [r for r in single if r["arm"] == "noise"]
    noise = pool(noise_rows, lambda r: (r["pattern"], float(r["noise"])))
    ps = sorted({k[1] for k in noise})
    pats = ("strong", "orient")
    fig, axes = plt.subplots(3, 1, figsize=(3.4, 6.2))
    ax = axes[0]
    for i, pat in enumerate(pats):
        if pat in forced and forced[pat]["n"] > 0:
            y, e = errbars([rate(forced[pat]["wrong"], forced[pat]["n"])])
            ax.bar(i, y[0], color=COLOUR[pat], width=0.55)
            ax.errorbar([i], y, yerr=e, color="black", capsize=3, lw=0.8)
    ax.set_xticks(range(len(pats)), list(pats))
    ax.set_ylabel("wrong rate")
    ax.set_title("A. forced1 arm (one flipped cell), single window", fontsize=7, loc="left")
    for bi, (field, label) in enumerate((("wrong", "wrong rate"), ("correct", "correct rate"))):
        ax = axes[1 + bi]
        for i, pat in enumerate(pats):
            xs, rs = [], []
            for p in ps:
                cell = noise.get((pat, p))
                if cell and cell["n"] > 0:
                    xs.append(p * (1.04 if i else 1 / 1.04))
                    rs.append(rate(cell[field], cell["n"]))
            if xs:
                y, e = errbars(rs)
                ax.errorbar(xs, y, yerr=e, color=COLOUR[pat], marker="os"[i], ls="-" if i == 0 else "--", lw=0.8,
                            ms=3, capsize=1.5, elinewidth=0.7, label=pat)
        ax.set_xscale("log")
        ax.set_xticks(ps, [f"{p:g}" for p in ps])
        ax.minorticks_off()
        ax.set_xlabel("cell flip probability p")
        ax.set_ylabel(label)
        ax.set_title(f"{'BC'[bi]}. noise arm, {field} rate", fontsize=7, loc="left")
    axes[1].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, format="pdf")
    plt.close(fig)


def fmt(k: int, n: int) -> str:
    if n <= 0:
        return "no reads"
    lo, hi = wilson(k, n)
    return f"{k} of {n} ({100 * k / n:.2f} percent, Wilson 95 percent interval {100 * lo:.2f} to {100 * hi:.2f} percent)"


def summary(puzzle: list[dict], dense: list[dict]) -> str:
    out = ["# S2 simulation summary", ""]
    out.append("All intervals are Wilson 95 percent intervals. In fig_puzzle.pdf the counts are pooled over blur, noise "
              "and tilt at each px per cell, with finger 0 and finger 1 shown as separate panels. Decoder \"single\" is "
              "one 5 x 5 window; decoder \"grid\" is the four-window decoder.")
    out.append("")

    # Prediction 1
    parts = []
    strong_p = [r for r in puzzle if r["pattern"] == "strong"]
    allzero = True
    for dec in ("single", "grid"):
        t = pool([r for r in strong_p if r["decoder"] == dec], lambda r: 0).get(0)
        if t is None:
            parts.append(f"on the rendered puzzle with the {DECODER_LABEL[dec]} decoder there are no strong rows")
            continue
        allzero &= t["wrong_le1_misread"] == 0
        parts.append(f"on the rendered puzzle with the {DECODER_LABEL[dec]} decoder, {fmt(t['wrong_le1_misread'], t['reads_le1_misread'])} "
                     "of the reads with at most one misread cell were wrong")
    for arm in ("forced1", "noise"):
        t = pool([r for r in dense if r["pattern"] == "strong" and r["arm"] == arm and r["decoder"] == "single"],
                 lambda r: 0).get(0)
        if t is None:
            parts.append(f"on the dense tori, arm {arm}, there are no strong rows")
            continue
        allzero &= t["wrong_le1_misread"] == 0
        parts.append(f"on the dense tori, arm {arm}, single-window decoder, {fmt(t['wrong_le1_misread'], t['reads_le1_misread'])} "
                     "of the reads with at most one misread cell were wrong")
    verdict = "The data agree with this prediction for every cell tested." if allzero else \
        "The data do NOT agree: at least one strong-form read with at most one misread cell was wrong."
    out.append("Prediction 1 (no read with at most one misread cell is wrong on a strong-form pattern, for either decoder): "
               + "; ".join(parts) + f". {verdict} The four-window decoder was not run on the dense tori, so that cell is untested.")
    out.append("")

    # Prediction 2
    f = {pat: pool([r for r in dense if r["pattern"] == pat and r["arm"] == "forced1" and r["decoder"] == "single"],
                   lambda r: 0).get(0) for pat in ("orient", "strong")}
    if f["orient"] and f["strong"]:
        ok = f["orient"]["wrong"] > 0
        v = ("The single-window half agrees: the control pattern produces wrong reads and the strong pattern does not."
             if ok and f["strong"]["wrong"] == 0 else
             "The single-window half does not agree as stated (see counts).")
        body = (f"in the forced1 arm with the single-window decoder, wrong reads on the orient (control) pattern were "
                f"{fmt(f['orient']['wrong'], f['orient']['n'])}, and on the strong pattern "
                f"{fmt(f['strong']['wrong'], f['strong']['n'])}. {v}")
    else:
        body = "the forced1 arm rows for one or both patterns are missing."
    out.append("Prediction 2 (on the dense tori, forced1 arm, the single-window decoder gives wrong reads on the control pattern "
               "and the four-window decoder rejects nearly all such reads on both patterns): " + body +
               " The four-window half was not run on the dense tori (the dense run used the single decoder only), "
               "so it is untested and nothing here supports or contradicts it.")
    out.append("")

    # Prediction 3
    parts = []
    rare = True
    for pat in ("strong", "orient"):
        for dec in ("single", "grid"):
            t = pool([r for r in puzzle if r["pattern"] == pat and r["decoder"] == dec], lambda r: 0).get(0)
            if t is None:
                parts.append(f"{pat}, {DECODER_LABEL[dec]}: no rows")
                continue
            rare &= t["wrong"] / t["n"] < 0.01
            parts.append(f"{pat}, {DECODER_LABEL[dec]}: {fmt(t['wrong'], t['n'])}")
    v = ("Every pattern and decoder is under 1 percent, so the data agree that wrong reads are rare."
         if rare else "At least one pattern and decoder is at or above 1 percent, so the data do not agree that wrong reads are rare "
         "(rare is taken here as a point estimate under 1 percent).")
    out.append("Prediction 3 (on the rendered puzzle, wrong reads are rare for both patterns and both decoders; wrong over all reads in the "
               "whole sweep): " + "; ".join(parts) + f". {v}")
    out.append("")

    # Noise arm note
    noise = pool([r for r in dense if r["arm"] == "noise" and r["decoder"] == "single"],
                 lambda r: (float(r["noise"]), r["pattern"]))
    ps = sorted({k[0] for k in noise})
    lines = []
    for p in ps:
        s, o = noise.get((p, "strong")), noise.get((p, "orient"))
        if s and o:
            lines.append(f"p = {p:g}: correct {s['correct']} of {s['n']} (strong) and {o['correct']} of {o['n']} (orient), "
                         f"wrong {s['wrong']} (strong) and {o['wrong']} (orient)")
    if lines:
        out.append("Noise arm, single window, as plotted (no interpolation between noise levels): " + "; ".join(lines) + ".")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--puzzle", type=Path, required=True)
    ap.add_argument("--dense", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args(argv)
    puzzle, dense = load(a.puzzle), load(a.dense)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    fig_puzzle(puzzle, a.out_dir / "fig_puzzle.pdf")
    fig_dense(dense, a.out_dir / "fig_dense.pdf")
    (a.out_dir / "sim_summary.md").write_text(summary(puzzle, dense), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
