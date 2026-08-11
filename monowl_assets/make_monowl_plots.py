#!/usr/bin/env python3
"""Generate the figures for the monoWL (monochromatic reduction) diagnosis tab.

Stdlib + matplotlib only. Band numbers are taken verbatim from the diagnosis
(../../2026B_mp/reduction/mono_diagnosis/chopper_diagnosis.md); the I(Q) curves
are read from the proof reduction (mono_diagnosis/reduced_recipe/).

    python3 make_monowl_plots.py     # writes *.png next to this script
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
MONO = os.path.normpath(os.path.join(
    HERE, "..", "..", "2026B_mp", "reduction", "mono_diagnosis"))
RECIPE = os.path.join(MONO, "reduced_recipe")
AGBE = os.path.join(MONO, "reduced_agbe_mono")

# AgBe silver-behenate diffraction orders (d = 58.38 A -> Q = 2*pi*n/d)
AGBE_Q = [0.10763, 0.21526, 0.32289]
# spread colours match the site (SPREAD_COLOR in index.html)
SPREAD_COLOR = {"0.03": "#0067b9", "0.05": "#00703c",
                "0.10": "#b26a00", "0.15": "#c0392b"}

GREEN = "#00703c"
BLUE = "#0067b9"
RED = "#c0392b"
GREY = "#8a8f98"

# ---- band data (Angstrom) -------------------------------------------------
# selected = REAL transmitted_bands() lead band with the drtsans-selected
#            daystamp-20260304 config; None => empty intersection (IndexError).
# correct  = same run recomputed with the daystamp-20260101 ("final answer") config.
SPREADS = ["0.03", "0.05", "0.10", "0.15"]
SELECTED = {"0.03": None, "0.05": (2.562, 2.586),
            "0.10": (2.500, 2.649), "0.15": (2.438, 2.711)}
# correct-config bands = the REAL drtsans transmitted bands, read from the
# "Monochromatic mode detected: single bin spanning [wmin,wmax]" notices logged
# by reduce_agbe_mono.py (authoritative; these are what the reduction actually
# used). They are wider than the ideal (dl/l)x2.5 and centred ~2.475 A.
CORRECT = {"0.03": (2.412, 2.538), "0.05": (2.387, 2.563),
           "0.10": (2.324, 2.625), "0.15": (2.262, 2.688)}


def fig_bands():
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    h = 0.34
    for i, sp in enumerate(SPREADS):
        y = i
        # correct (green)
        b = CORRECT[sp]
        ax.broken_barh([(b[0], b[1] - b[0])], (y + 0.04, h), facecolors=GREEN,
                       edgecolor="#004a27", zorder=3)
        ax.text(b[1] + 0.01, y + 0.04 + h / 2,
                "band {:.3f} A".format(b[1] - b[0]),
                va="center", ha="left", fontsize=8, color=GREEN)
        # selected (blue) or empty
        s = SELECTED[sp]
        if s is None:
            ax.text(2.50, y - 0.04 - h / 2, "EMPTY  →  IndexError (fails to load)",
                    va="center", ha="center", fontsize=8.5, color=RED,
                    fontweight="bold")
            ax.broken_barh([(2.30, 0.40)], (y - 0.04 - h, h), facecolors="none",
                           edgecolor=RED, linestyle=":", zorder=3)
        else:
            ax.broken_barh([(s[0], s[1] - s[0])], (y - 0.04 - h, h),
                           facecolors=BLUE, edgecolor="#003f73", zorder=3)
            ax.text(s[1] + 0.01, y - 0.04 - h / 2,
                    "w={:.3f} A  centre {:.3f}".format(s[1] - s[0], (s[0] + s[1]) / 2),
                    va="center", ha="left", fontsize=8, color=BLUE)
    ax.axvline(2.50, color=GREY, lw=1.2, ls="--", zorder=1)
    ax.text(2.50, len(SPREADS) - 0.35, "nominal 2.50 A", color=GREY,
            fontsize=8.5, ha="center")
    ax.set_yticks(range(len(SPREADS)))
    ax.set_yticklabels(["dl/l = " + s for s in SPREADS])
    ax.set_ylim(-0.9, len(SPREADS) - 0.2)
    ax.set_xlim(2.28, 2.95)
    ax.set_xlabel("transmitted wavelength band (A)")
    ax.set_title("Transmitted band per spread: drtsans-selected vs correct chopper config",
                 fontsize=10.5)
    ax.legend(handles=[
        Patch(facecolor=GREEN, edgecolor="#004a27", label="correct config (daystamp 20260101)"),
        Patch(facecolor=BLUE, edgecolor="#003f73", label="drtsans-selected (daystamp 20260304)"),
    ], loc="lower right", fontsize=8, framealpha=0.95)
    ax.grid(axis="x", color="#e5e7eb", zorder=0)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl_bands.png"), dpi=130)
    plt.close(fig)


def fig_intersection():
    """dl=0.03: first transmitted band edge of each of the six choppers (selected
    config), showing the gap that empties the intersection."""
    # first band of each chopper near 2.5 A (from chopper_diagnosis.md, run 186211)
    first = [(2.672, 6.838), (2.594, 6.822), (2.507, 6.942),
             (0.000, 2.561), (0.000, 2.896), (0.000, 2.673)]
    labels = ["1b (ch0)", "2b (ch1)", "3a (ch2)", "3b (ch3)", "1a (ch4)", "2a (ch5)"]
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    for i, (b, lab) in enumerate(zip(first, labels)):
        lo, hi = max(b[0], 2.3), min(b[1], 2.95)
        ax.broken_barh([(lo, hi - lo)], (i - 0.3, 0.6), facecolors="#cfe0ee",
                       edgecolor=BLUE, zorder=3)
        ax.text(2.31, i, lab, va="center", ha="left", fontsize=8.5, color="#1b2733")
    # the required-open window is the intersection of all six -> here it is empty:
    ax.axvspan(2.561, 2.672, color=RED, alpha=0.13, zorder=1)
    ax.text(2.6165, 5.72, "no wavelength open on all six\n(2.561 – 2.672 A gap)",
            color=RED, fontsize=8.5, ha="center", va="top", fontweight="bold")
    ax.annotate("3b closes at 2.561", xy=(2.561, 3), xytext=(2.40, 4.4),
                fontsize=8, color="#1b2733",
                arrowprops=dict(arrowstyle="->", color="#1b2733", lw=0.8))
    ax.annotate("1b opens at 2.672", xy=(2.672, 0), xytext=(2.74, 1.0),
                fontsize=8, color="#1b2733",
                arrowprops=dict(arrowstyle="->", color="#1b2733", lw=0.8))
    ax.set_xlim(2.3, 2.95)
    ax.set_ylim(-0.9, 6.1)
    ax.set_yticks([])
    ax.set_xlabel("wavelength (A)")
    ax.set_title("dl/l=0.03: the six chopper openings share no band under the "
                 "selected config", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl_intersection.png"), dpi=130)
    plt.close(fig)


def read_iq(path):
    q, iq, err = [], [], []
    if not os.path.isfile(path):
        return q, iq, err
    with open(path) as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            p = ln.replace(",", " ").split()
            if len(p) < 2:
                continue
            try:
                x, y = float(p[0]), float(p[1])
            except ValueError:
                continue
            e = float(p[2]) if len(p) > 2 else 0.0
            if y > 0:
                q.append(x); iq.append(y); err.append(e)
    return q, iq, err


def fig_iq():
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    series = [("porasil dl/l=0.10", "porasil_dl0.10_Iq.dat", GREEN, "o"),
              ("porasil dl/l=0.03", "porasil_dl0.03_Iq.dat", BLUE, "s")]
    any_data = False
    for lab, fn, col, mk in series:
        q, iq, err = read_iq(os.path.join(RECIPE, fn))
        if not q:
            continue
        any_data = True
        ax.errorbar(q, iq, yerr=err, fmt=mk, ms=3.2, lw=0, elinewidth=0.6,
                    color=col, ecolor=col, label=lab, capsize=0)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Q (1/A)"); ax.set_ylabel("I(Q)  (1/cm)")
    ax.set_title("Recovered porasil I(Q) after the fix", fontsize=10.5)
    if any_data:
        ax.legend(fontsize=8.5)
    ax.grid(which="both", color="#eceef1")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl_iq.png"), dpi=130)
    plt.close(fig)


def fig_agbe():
    """AgBe across the four spreads: full I(Q) with diffraction orders marked,
    plus the first peak normalised to compare resolution/statistics."""
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.7))
    spreads = ["0.15", "0.10", "0.05", "0.03"]
    for sp in spreads:
        q, iq, err = read_iq(os.path.join(AGBE, "agbe_dl{0}_Iq.dat".format(sp)))
        if not q:
            continue
        col = SPREAD_COLOR[sp]
        axL.plot(q, iq, "-o", ms=2.6, lw=1.0, color=col, label="dl/l = " + sp)
    for qc in AGBE_Q:
        axL.axvline(qc, color=GREY, ls=":", lw=1, zorder=0)
    axL.text(AGBE_Q[0], axL.get_ylim()[1], " AgBe orders", color=GREY, fontsize=8,
             va="top")
    axL.set_xscale("log"); axL.set_yscale("log")
    axL.set_xlabel("Q (1/A)"); axL.set_ylabel("I(Q)  (1/cm)")
    axL.set_title("AgBe I(Q) vs spread — full range", fontsize=10.5)
    axL.legend(fontsize=8.5, title="wider band = more flux")
    axL.grid(which="both", color="#eceef1")

    # right: first-order peak, each normalised to its own max in [0.08,0.14]
    for sp in spreads:
        q, iq, err = read_iq(os.path.join(AGBE, "agbe_dl{0}_Iq.dat".format(sp)))
        pk = [(x, y) for x, y in zip(q, iq) if 0.07 < x < 0.15]
        if len(pk) < 3:
            continue
        ymax = max(y for _, y in pk)
        col = SPREAD_COLOR[sp]
        axR.plot([x for x, _ in pk], [y / ymax for _, y in pk], "-o", ms=3.2,
                 lw=1.2, color=col, label="dl/l = " + sp)
    axR.axvline(AGBE_Q[0], color=GREY, ls=":", lw=1)
    axR.text(AGBE_Q[0], 1.02, " AgBe(001) 0.1076", color=GREY, fontsize=8, va="bottom")
    axR.set_xlabel("Q (1/A)"); axR.set_ylabel("I(Q) / peak")
    axR.set_title("First AgBe peak, peak-normalised", fontsize=10.5)
    axR.set_xlim(0.07, 0.15)
    axR.legend(fontsize=8.5)
    axR.grid(color="#eceef1")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl_agbe.png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    fig_bands()
    fig_intersection()
    fig_iq()
    fig_agbe()
    print("wrote monowl_bands/intersection/iq/agbe .png in", HERE)
