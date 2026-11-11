"""Redraw the figures without the legend row, with large fonts, in the paper
panel size (3.4 x 2.07 in, 600-dpi PNG + PDF).  The x-axis title is
centered on its axis when it fits; a title too long to center is slid
just enough to stay inside the figure (and clear of the other title).

Usage (in the folder with run_ten_figures.py):
    py replot_no_legend.py <run_dir>                    # all figures
    py replot_no_legend.py <run_dir> --figures 1,2,5,6,12,15
Output: <run_dir>/figures_nolegend/ plus one shared legend.png.
The original figures/, summary.csv and run_ten_figures.py are not touched.
"""
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import run_ten_figures as R

# Font sizes (pt).  Change these to make the text bigger or smaller.
R.PAPER_RC.update({"axes.labelsize": 17, "xtick.labelsize": 16, "ytick.labelsize": 16,
                   "legend.fontsize": 10, "axes.linewidth": 1.2})
# Shorter x-axis titles (edit or remove entries as needed).
XLABEL = {
    "Avg. number of required features per task": "Avg. required features per task",
    "Avg. deadline (s)": "Avg. deadline",
}
PAD = 0.005  # gap to the figure edge, as a fraction of the figure
RENAME = {"figures_paper": "figures_nolegend", "summary.csv": "summary_nolegend.csv",
          "removed_outliers.csv": "removed_outliers_nolegend.csv"}

_savefig = plt.Figure.savefig


def _fit(fig, label, limit, axis):
    r = fig.canvas.get_renderer()
    while True:
        box = label.get_window_extent(r)
        size = box.width if axis == "x" else box.height
        if size <= limit or label.get_fontsize() <= 8:
            return
        label.set_fontsize(label.get_fontsize() - 0.5)


def _place(fig):
    """Same spot in every figure: the y title hugs the figure's left edge and
    the x title sits on the figure's bottom edge, so titles line up across
    panels.  Each title is centered on its axis when it fits; one too long
    to center is slid just enough to stay inside the figure."""
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    for ax in fig.axes:
        pos = ax.get_position()
        xl, yl = ax.xaxis.label, ax.yaxis.label
        # y title: left edge at the figure edge, centered vertically on the axis
        yl.set_verticalalignment("top")      # rotated: 'top' faces left
        yl.set_horizontalalignment("center")
        h = yl.get_window_extent(r).height / H
        cy = pos.y0 + pos.height / 2
        cy = min(max(cy, PAD + h / 2), 1 - PAD - h / 2)
        ax.yaxis.set_label_coords((PAD - pos.x0) / pos.width, (cy - pos.y0) / pos.height)
        fig.canvas.draw()
        # x title: bottom at the figure edge, centered on the axis
        xl.set_verticalalignment("bottom")
        xl.set_horizontalalignment("center")
        w = xl.get_window_extent(r).width / W
        left = yl.get_window_extent(r).x1 / W + PAD
        cx = pos.x0 + pos.width / 2
        cx = min(max(cx, left + w / 2), 1 - PAD - w / 2)
        ax.xaxis.set_label_coords((cx - pos.x0) / pos.width, (PAD - pos.y0) / pos.height)


# Pass 1 measures every panel's tight layout; pass 2 gives all panels the
# same plot-box position (the tightest common one), so every figure has an
# identical axes size and the panels line up when placed side by side.
POSITIONS = []
FIXED = None


YTICKS = (4, 6)    # wanted number of y tick labels (min, max)
YMARGIN = 0.07     # empty space above/below the data, as a fraction of the data range


def _nice_steps(span):
    """Candidate tick steps 1, 2, 2.5, 5 x 10^k around span."""
    import math
    k = math.floor(math.log10(span)) if span > 0 else 0
    return sorted({m * 10 ** e for e in (k - 2, k - 1, k) for m in (1, 2, 2.5, 5)})


def _yticks(ax):
    """Y range fitted to the data (small margin, no big blank band) and
    4-6 round tick labels, with the top label close to the top of the plot."""
    import math
    if ax.get_yscale() != "linear":
        return
    ys = [y for line in ax.get_lines() for y in line.get_ydata() if y == y]
    if not ys:
        return
    lo, hi = min(ys), max(ys)
    if hi - lo <= 0:
        hi, lo = hi + 1.0, lo - 1.0
    margin = (hi - lo) * YMARGIN
    bottom, top = lo - margin, hi + margin
    if lo >= 0 and bottom < 0:
        bottom = 0.0 if lo < (hi - lo) * 0.25 else bottom
    best = None
    for step in _nice_steps(top - bottom):
        first = math.ceil(bottom / step - 1e-9) * step
        ticks = []
        t = first
        while t <= top + 1e-9:
            ticks.append(round(t, 10))
            t += step
        if len(ticks) < 2:
            continue
        # tick counts outside YTICKS are used only when nothing fits
        off = max(YTICKS[0] - len(ticks), len(ticks) - YTICKS[1], 0)
        # gaps between the outer labels and the plot edges (fraction of height)
        gap = ((top - ticks[-1]) + (ticks[0] - bottom)) / (top - bottom)
        score = (off, gap, -len(ticks))
        if best is None or score < best[0]:
            best = (score, ticks)
    if best is None:
        return
    ax.set_ylim(bottom, top)
    ax.set_yticks(best[1])
    integer = all(float(t).is_integer() for t in best[1])
    ax.set_yticklabels([f"{t:.0f}" if integer else f"{t:g}" for t in best[1]],
                       fontweight="bold")


LOGY: set[int] = set()   # figure numbers drawn with a log y axis (--logy)


def _log_axis(ax):
    """Log y axis with round labels (1, 2, 5 x 10^k) and a range fitted to the data."""
    import math
    from matplotlib.ticker import FixedLocator, NullLocator
    ys = [y for line in ax.get_lines() for y in line.get_ydata() if y == y and y > 0]
    if not ys:
        return
    lo, hi = min(ys), max(ys)
    ax.set_yscale("log")
    pad = (hi / lo) ** 0.06
    ax.set_ylim(lo / pad, hi * pad)
    ticks = [m * 10 ** e for e in range(math.floor(math.log10(lo)) - 1, math.ceil(math.log10(hi)) + 1)
             for m in (1, 2, 5) if lo / pad <= m * 10 ** e <= hi * pad]
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels([f"{t:g}" for t in ticks], fontweight="bold")


def _corner_savefig(fig, *a, **k):
    if a and str(a[0]).endswith(".pdf"):
        return None  # PNG only
    size = R.PAPER_RC["axes.labelsize"]
    name = Path(str(a[0])).name if a else ""
    if any(name.startswith(f"fig{n:02d}_") for n in LOGY):
        for ax in fig.axes:
            _log_axis(ax)
    for ax in fig.axes:
        _yticks(ax)
    for ax in fig.axes:
        xl, yl = ax.xaxis.label, ax.yaxis.label
        text = xl.get_text().replace("Average", "Avg.")
        xl.set_text(XLABEL.get(text, text))
        xl.set_fontsize(size)
        yl.set_fontsize(size)
        fig.canvas.draw()
        _fit(fig, yl, fig.bbox.height * (1 - 2 * PAD), "y")
        fig.canvas.draw()
        ywidth = yl.get_window_extent(fig.canvas.get_renderer()).width
        _fit(fig, xl, fig.bbox.width * (1 - 2 * PAD) - ywidth * 1.15, "x")
    if not fig.axes:  # the shared legend strip
        return _savefig(fig, *a, **k) if FIXED is not None else None
    if FIXED is None:
        fig.tight_layout(pad=0.2)
        for ax in fig.axes:
            p = ax.get_position()
            POSITIONS.append((p.x0, p.y0, p.x1, p.y1))
        return None
    for ax in fig.axes:
        ax.set_position(FIXED)
    _place(fig)
    fig.canvas.draw()
    return _savefig(fig, *a, **k)


plt.Figure.savefig = _corner_savefig


class RunDir(type(Path())):
    def __truediv__(self, key):
        return super().__truediv__(RENAME.get(str(key), key))


ap = argparse.ArgumentParser()
ap.add_argument("run_dir", type=Path)
ap.add_argument("--figures", default="all")
ap.add_argument("--plot-runs", type=int, default=300)
ap.add_argument("--logy", default="",
                help="figure numbers drawn with a log y axis, e.g. 13,15")
ap.add_argument("--common-x", type=int, default=0,
                help="average every x over the same runs (seeds kept at all x); "
                     "value = minimum number of shared runs required")
ap.add_argument("--mid-paired", type=int, default=0,
                help="at each x keep the K most typical runs, the same runs for every method")
ap.add_argument("--mid", type=int, default=0,
                help="plot the mean of the K runs closest to the median at each point "
                     "(per method); 0 = plain mean of all runs")
args = ap.parse_args()
LOGY.update(int(n) for n in args.logy.split(",") if n.strip())

if args.mid > 0:
    from statistics import fmean as _plain_mean, median as _median

    def _mid_mean(samples, k=args.mid):
        """Mean of the k samples closest to the median (all samples if n <= k)."""
        values = sorted(float(v) for v in samples)
        if len(values) <= k:
            return _plain_mean(values)
        m = _median(values)
        nearest = sorted(values, key=lambda v: (abs(v - m), v))[:k]
        return _plain_mean(nearest)

    R.fmean = _mid_mean  # used by run_ten_figures.plot for each point
    print(f"Each point = mean of the {args.mid} runs closest to the median (per method)")

if args.common_x > 0:
    _orig_select_cx = R._select_rows

    def _common_x_select(figure, rows, minimum=args.common_x):
        """Use only runs (seeds) that are kept at every x of the figure, so every
        point of every curve is averaged over the same problem instances.
        Falls back to the normal selection when fewer than `minimum` such runs exist."""
        kept, removed = _orig_select_cx(figure, rows)
        by_x = {}
        for row in kept:
            by_x.setdefault(float(row["x"]), set()).add(int(row["attempt"]))
        common = set.intersection(*by_x.values()) if by_x else set()
        if len(common) < minimum:
            print(f"Fig {figure.number}: only {len(common)} runs shared by all x; normal selection kept")
            return kept, removed
        print(f"Fig {figure.number}: {len(common)} runs shared by all x")
        return [r for r in kept if int(r["attempt"]) in common], removed

    R._select_rows = _common_x_select

if args.mid_paired > 0:
    import math
    from statistics import median as _median
    _orig_select = R._select_rows

    def _paired_select(figure, rows, k=args.mid_paired):
        """Keep, at each x, the k runs (same runs for every method) that are
        most typical: smallest mean |log(value / method median)| over methods."""
        kept, removed = _orig_select(figure, rows)
        by_x = {}
        for row in kept:
            by_x.setdefault(float(row["x"]), {}).setdefault(int(row["attempt"]), []).append(row)
        out = []
        for x, attempts in by_x.items():
            if len(attempts) <= k:
                out.extend(r for runs in attempts.values() for r in runs)
                continue
            med = {}
            for runs in attempts.values():
                for r in runs:
                    med.setdefault(r["method_key"], []).append(float(r[figure.metric]))
            med = {m: _median(v) for m, v in med.items()}

            def score(runs):
                d = [abs(math.log(max(float(r[figure.metric]), 1e-9) / max(med[r["method_key"]], 1e-9)))
                     for r in runs]
                return sum(d) / len(d)
            best = sorted(attempts, key=lambda a: (score(attempts[a]), a))[:k]
            out.extend(r for a in best for r in attempts[a])
        return out, removed

    R._select_rows = _paired_select
    print(f"Each point = mean over the {args.mid_paired} most typical runs (same runs for all methods)")

R.PLOT_OPTIONS.update(legend=False, paper=True, runs=args.plot_runs or None)
figs = list(R.FIGURES) if args.figures == "all" else [
    R.FIGURE_BY_NUMBER[int(i)] for i in args.figures.split(",")]
out = Path(args.run_dir) / "figures_nolegend"
(out / "legend.png").unlink(missing_ok=True)
R.plot(RunDir(args.run_dir), figs)          # pass 1: measure
x0 = max(p[0] for p in POSITIONS); y0 = max(p[1] for p in POSITIONS)
x1 = min(p[2] for p in POSITIONS); y1 = min(p[3] for p in POSITIONS)
FIXED = [x0, y0, x1 - x0, y1 - y0]
R.plot(RunDir(args.run_dir), figs)          # pass 2: draw with one common box
print("Saved to", out)
