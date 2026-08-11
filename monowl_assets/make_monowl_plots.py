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
PERSLICE = os.path.join(MONO, "perslice", "info", "inelastic_incoh",
                        "agbe_dl0.15_perslice", "slice_0", "frame_0")
PERSLICE_BB = os.path.join(MONO, "perslice_bb")   # broadband 186106 per-slice tree
PERSLICE_BB_NOCLIP = os.path.join(MONO, "perslice_bb_noclip")  # broadband, TOF clips off

# AgBe diffraction orders at the EQSANS calibration target Q1 = 0.1069 1/A
# (TARGET_Q1 in tools/agbe/agbe_reducenfit.py; d(001) = 2*pi/0.1069 ~ 58.8 A).
AGBE_Q1 = 0.1069
AGBE_Q = [AGBE_Q1, 2 * AGBE_Q1, 3 * AGBE_Q1]
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
    axR.text(AGBE_Q[0], 1.02, " AgBe(001) target 0.1069", color=GREY, fontsize=8, va="bottom")
    axR.set_xlabel("Q (1/A)"); axR.set_ylabel("I(Q) / peak")
    axR.set_title("First AgBe peak, peak-normalised", fontsize=10.5)
    axR.set_xlim(0.07, 0.15)
    axR.legend(fontsize=8.5)
    axR.grid(color="#eceef1")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl_agbe.png"), dpi=130)
    plt.close(fig)


def fig_perslice():
    """monoWL2 centrepiece: AgBe I(Q) per wavelength slice of the dl/l=0.15 band.
    Every slice's peak sits at Q1 -> the peaks overlap; there is no wavelength
    trend."""
    import glob
    Q1 = AGBE_Q1
    fs = sorted(glob.glob(os.path.join(PERSLICE, "IQ_*_before_b_correction.dat")),
                key=lambda f: float(f.split("IQ_")[1].split("_")[0]))
    if not fs:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 4.7))
    try:
        cmap = plt.cm.viridis
    except Exception:
        cmap = None
    n = len(fs)
    for i, f in enumerate(fs):
        wl = float(f.split("IQ_")[1].split("_")[0])
        q, iq, _ = read_iq(f)
        if not q:
            continue
        col = cmap(i / max(1, n - 1)) if cmap else BLUE
        a1.plot(q, iq, "-o", ms=2.4, lw=0.9, color=col, label="%.3f A" % wl)
        pk = [(x, y) for x, y in zip(q, iq) if 0.085 < x < 0.135]
        if pk:
            ym = max(y for _, y in pk)
            a2.plot([x for x, _ in pk], [y / ym for _, y in pk], "-o", ms=3,
                    lw=1.1, color=col, label="%.3f A" % wl)
    for a in (a1, a2):
        a.axvline(Q1, color=RED, ls="--", lw=1.2)
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xlabel("Q (1/A)"); a1.set_ylabel("I(Q)")
    a1.set_title("AgBe I(Q) per wavelength slice (dl/l=0.15 band)", fontsize=10.5)
    a1.legend(fontsize=7, title="slice lambda", ncol=2)
    a1.grid(which="both", color="#eceef1")
    a2.set_xlim(0.085, 0.135)
    a2.set_xlabel("Q (1/A)"); a2.set_ylabel("I(Q) / peak")
    a2.set_title("Peak region, each normalised to its own max", fontsize=10.5)
    a2.text(Q1, 1.03, "calibration target 0.1069", color=RED, fontsize=8, ha="center")
    a2.legend(fontsize=7, ncol=2)
    a2.grid(color="#eceef1")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl2_perslice.png"), dpi=130)
    plt.close(fig)


def fig_peakpos():
    """Two panels: (a) fitted AgBe peak position vs spread for single-bin vs
    multi-bin vs the broadband calibration; (b) convergence to Q1 as dl/l=0.05 is
    sliced into more wavelength bins."""
    Q1 = AGBE_Q1   # calibration target 0.1069
    # spread, band width, single-bin q0, multi-bin(0.1 A) q0   (Gaussian fits)
    rows = [("0.05", 0.176, 0.1039, 0.1058),
            ("0.10", 0.301, 0.1070, 0.1065),
            ("0.15", 0.426, 0.1079, 0.1067)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 4.5))
    x = list(range(len(rows)))
    a1.axhline(Q1, color=GREY, ls="--", lw=1.3, label="AgBe calibration target (0.1069)")
    a1.plot(x, [r[2] for r in rows], "o-", color=RED, ms=7, label="single-bin (monochromatic mode)")
    a1.plot(x, [r[3] for r in rows], "s-", color=GREEN, ms=7, label="multi-bin (0.1 A step)")
    a1.set_xticks(x); a1.set_xticklabels(["dl/l=%s\n(band %.2f A)" % (r[0], r[1]) for r in rows])
    a1.set_ylabel("fitted AgBe peak Q (1/A)")
    a1.set_title("Peak position vs spread", fontsize=10.5)
    a1.legend(fontsize=8); a1.grid(color="#eceef1")
    a1.set_ylim(0.100, 0.110)

    # convergence for dl/l=0.05
    nb = [1, 2, 8]; q0 = [0.1039, 0.1063, 0.1066]
    a2.axhline(Q1, color=GREY, ls="--", lw=1.3, label="calibration target (0.1069)")
    a2.plot(nb, q0, "o-", color=BLUE, ms=7)
    a2.set_xscale("log")
    a2.set_xticks(nb); a2.set_xticklabels([str(n) for n in nb])
    a2.set_xlabel("number of wavelength bins across the band")
    a2.set_ylabel("fitted AgBe peak Q (1/A)")
    a2.set_title("dl/l=0.05: finer binning -> converges to Q1", fontsize=10.5)
    a2.legend(fontsize=8); a2.grid(which="both", color="#eceef1")
    a2.set_ylim(0.103, 0.108)
    a2.annotate("1 bin =\nsingle-lambda", xy=(1, 0.1039), xytext=(1.4, 0.1045),
                fontsize=8, color=BLUE)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl2_peakpos.png"), dpi=130)
    plt.close(fig)


def _fit_perslice_q0(tree):
    """Gaussian-fit the AgBe(001) peak of every IQ_<wl>_before_b_correction.dat in
    a per-slice tree. Returns (wl[], q0[], err[]). Needs scipy; returns empties if
    unavailable."""
    import glob
    try:
        from scipy.optimize import curve_fit
    except Exception:
        return [], [], []
    import numpy as np
    fs = sorted(glob.glob(os.path.join(tree, "**", "IQ_*_before_b_correction.dat"),
                          recursive=True),
                key=lambda f: float(f.split("IQ_")[1].split("_")[0]))
    def model(q, A, q0, s, a, b):
        return A * np.exp(-(q - q0) ** 2 / (2 * s ** 2)) + a + b * q
    W, Q0, ER = [], [], []
    for f in fs:
        wl = float(f.split("IQ_")[1].split("_")[0])
        q, iq, err = read_iq(f)
        if not q:
            continue
        q = np.array(q); iq = np.array(iq); err = np.array(err)
        m = (q > 0.085) & (q < 0.135) & np.isfinite(iq) & (iq > 0)
        if m.sum() < 6:
            continue
        qq, ii, ee = q[m], iq[m], err[m]
        ee = np.where(ee > 0, ee, np.maximum(ii * 0.1, 1e-9))
        try:
            p, c = curve_fit(model, qq, ii,
                             p0=[ii.max() - np.median(ii), 0.107, 0.005, np.median(ii), 0],
                             sigma=ee, absolute_sigma=True, maxfev=40000,
                             bounds=([0, 0.095, 0.001, -np.inf, -np.inf],
                                     [np.inf, 0.125, 0.03, np.inf, np.inf]))
            if np.sqrt(c[1, 1]) < 0.003:
                W.append(wl); Q0.append(p[1]); ER.append(np.sqrt(c[1, 1]))
        except Exception:
            pass
    return W, Q0, ER


def fig_perslice_trend():
    """The physics test: does each wavelength give the same Q? Broadband per-slice
    is flat on the target (yes); the monochromatic band, finely sliced, drifts —
    a fine-slicing artifact, not real."""
    mw, mq, me = _fit_perslice_q0(PERSLICE)
    bw, bq, be = _fit_perslice_q0(PERSLICE_BB)
    if not mw and not bw:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axhline(AGBE_Q1, color="0.5", ls="--", lw=1.3, label="AgBe calibration target 0.1069")
    if bw:
        ax.errorbar(bw, bq, yerr=be, fmt="s", ms=5, color=GREEN, capsize=2,
                    label="broadband, per slice — flat (physically correct)")
    if mw:
        ax.errorbar(mw, mq, yerr=me, fmt="o", ms=6, color=RED, capsize=2,
                    label="monochromatic dl/l=0.15, per slice — spurious drift")
    ax.set_xlabel("slice wavelength (A)")
    ax.set_ylabel("fitted AgBe(001) peak Q (1/A)")
    ax.set_title("Each wavelength must give the same Q — broadband confirms it; "
                 "the mono drift is a fine-slice artifact", fontsize=9.8)
    ax.legend(fontsize=8.5); ax.grid(color="#eceef1"); ax.set_ylim(0.102, 0.110)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl2_trend.png"), dpi=130)
    plt.close(fig)


def fig_emission():
    """The emission-time-selection mechanism, two panels:
    (left) broadband with TOF clips OFF: interior flat, closing-edge slices rise
    over the last ~0.4 A -- and the STANDARD clips (500/2000 us, shaded) remove
    exactly those regions.
    (right) mono dl0.15 per-slice mislabel converted to the implied moderator
    emission-time offset: late tail at the opening edge, early rise at closing."""
    bw, bq, be = _fit_perslice_q0(PERSLICE_BB_NOCLIP)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.6, 4.6))
    # left: broadband no-clip
    if bw:
        a1.errorbar(bw, bq, yerr=be, fmt="s", ms=4.5, color=GREEN, capsize=2)
    a1.axhline(AGBE_Q1, color="0.55", ls="--", lw=1.2, label="calibration target 0.1069")
    band_min, band_max = 2.574, 6.074            # histogram band, clips off
    lo_clip = 500e-6 * 3956 / 18.15             # 0.109 A
    hi_clip = 2000e-6 * 3956 / 18.15            # 0.436 A
    a1.axvspan(band_min, band_min + lo_clip, color=BLUE, alpha=0.18,
               label="standard cutTOFmin (500 μs)")
    a1.axvspan(band_max - hi_clip, band_max, color=RED, alpha=0.18,
               label="standard cutTOFmax (2000 μs)")
    a1.set_xlabel("slice wavelength (A)")
    a1.set_ylabel("fitted AgBe(001) peak Q (1/A)")
    a1.set_xlim(2.45, 6.2)
    a1.set_ylim(0.1055, 0.1080)
    a1.set_title("Broadband, TOF clips OFF: closing-edge slices deviate —\n"
                 "the standard clips remove exactly those regions", fontsize=9.6)
    a1.legend(fontsize=7.5, loc="upper left")
    a1.grid(color="#eceef1")
    # right: mono implied emission-time offsets
    lab = [2.287, 2.337, 2.387, 2.437, 2.487, 2.537, 2.587, 2.637]
    off = [296, 114, 68, -5, -27, -28, -57, -95]      # microseconds (late > 0)
    a2.axhline(0, color="0.55", lw=1)
    a2.plot(lab, off, "o-", color=RED, ms=6)
    a2.annotate("late-emission tail passes\nfast neutrons at the\nopening edge",
                xy=(2.30, 280), fontsize=8, color=RED, ha="left", va="top")
    a2.annotate("early (sharp-rise) emission\npasses slow neutrons\nat the closing edge",
                xy=(2.52, -80), fontsize=8, color=RED, ha="left", va="bottom")
    a2.set_xlabel("mono slice label wavelength (A)")
    a2.set_ylabel("implied emission-time offset (μs)")
    a2.set_title("Mono dl/l=0.15: per-slice mislabel as emission-time offset\n"
                 "(drtsans mean delay at 2.5 A is 123 μs)", fontsize=9.6)
    a2.grid(color="#eceef1")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "monowl2_emission.png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    fig_bands()
    fig_intersection()
    fig_iq()
    fig_agbe()
    fig_perslice()
    fig_peakpos()
    fig_perslice_trend()
    fig_emission()
    print("wrote monowl_* and monowl2_* .png in", HERE)
