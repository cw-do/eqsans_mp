#!/usr/bin/env python3
"""
Estimate how the 1A<->1B / 2A<->2B chopper label swap propagates into the
wavelength and spread that the reduction software recovers from the
(correctly set) chopper phases.

Model, faithful to bl6-SkfChopper/hexaSub.c monochromatic mode at 60 Hz:

  * EPICS sets each PHYSICAL disk's phase from its TRUE distance:
      A disks (1A,2A,3A): opening edge aligned to wl1 = lam0*(1 - s/2)
      B disks (1B,2B,3B): closing edge aligned to wl2 = lam0*(1 + s/2)
    A disk's open-window "center" time = TOF(edge) +halfopen (opener)
                                                    -halfopen (closer)

  * Reduction recovers, per disk, the wavelengths at which that disk opens
    and closes, using the distance (and optionally the phase offset) it
    BELIEVES the disk has; the transmitted band is the intersection of the
    six ~4 A-wide windows -> [max opening edge, min closing edge].

  * The label swap = for stations 1 and 2 the reduction pairs each phase with
    its PARTNER disk's distance (and, optionally, its partner's calibration
    offset). Station 3 (3A,3B) is not swapped.

Run:  python3 chopper_label_swap.py   ->  writes chopper_label_swap.png here.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

C = 3.9560346          # lam[A] = C * t[us] / L[mm]   (h/m_n)
SPEED = 60.0
FRAME = 1e6 / SPEED

# index: 0=1A 1=2A 2=3A 3=3B 4=1B 5=2B   (EPICS / hexaSub.c / config order)
L_true = np.array([5675.7668, 7775.7668, 9497.8, 9507.8, 5660.1247, 7760.1247])
ANGLE  = np.array([129.605, 179.989, 230.010, 230.007, 129.605, 179.989])
OFFSET = np.array([14954.46, 14805.4, 14726.06, 14565.6, 15072.89, 14834.04])
OPENER = np.array([True, True, True, False, False, False])  # A open, B close
PERM   = np.array([4, 5, 2, 3, 0, 1])   # swap 1A<->1B, 2A<->2B; leave 3A,3B
HALF   = (ANGLE / 2.0) / 360.0 / SPEED * 1e6


def forward_centers(lam0, s):
    wl1, wl2 = lam0 * (1 - s / 2.0), lam0 * (1 + s / 2.0)
    edge = np.where(OPENER, wl1, wl2)
    return edge * L_true / C + np.where(OPENER, HALF, -HALF)


def recover(centers, swap_dist=False, swap_offset=False):
    L_used = L_true[PERM] if swap_dist else L_true
    off_used = OFFSET[PERM] if swap_offset else OFFSET
    c = centers + OFFSET - off_used          # rec center = set_phase - off_used
    lo = (C * (c - HALF) / L_used).max()     # most restrictive lower edge
    hi = (C * (c + HALF) / L_used).min()     # most restrictive upper edge
    center = 0.5 * (lo + hi)
    return center, (hi - lo) / center


def main():
    s_in = 0.05
    lam = np.arange(1.0, 10.5, 1.0)          # 1,2,...,10 A  -> 10 points
    scen = {"correct":       dict(swap_dist=False, swap_offset=False),
            "swap_dist":     dict(swap_dist=True,  swap_offset=False),
            "swap_dist_off": dict(swap_dist=True,  swap_offset=True)}
    res = {k: {"c": [], "s": []} for k in scen}
    for L in lam:
        ctr = forward_centers(L, s_in)
        for k, kw in scen.items():
            cc, sp = recover(ctr, **kw)
            res[k]["c"].append(cc); res[k]["s"].append(sp)
    for k in res:
        res[k]["c"] = np.array(res[k]["c"]); res[k]["s"] = np.array(res[k]["s"])

    assert np.allclose(res["correct"]["c"], lam, rtol=1e-6)
    assert np.allclose(res["correct"]["s"], s_in, atol=1e-6)

    GREEN, BLUE, RED, GREY = "#00703c", "#0067b9", "#c0392b", "#5b6570"
    # marker at the estimated (recovered) wavelength; error bar = +/- spread/2
    series = [
        ("correct",       "correct labels",                 GREEN, "o", -0.17),
        ("swap_dist",     "swapped (distance)",             RED,   "s",  0.00),
        ("swap_dist_off", "swapped (distance + offsets)",   BLUE,  "^",  0.17),
    ]
    fig, ax = plt.subplots(figsize=(9.0, 6.6))
    ax.set_title("Estimated wavelength ± spread that reduction recovers\n"
                 "under the 1A↔ 1B / 2A↔ 2B label swap  "
                 "(EPICS set: λ₀ = 1–10 Å, 5% spread, 60 Hz mono)",
                 fontsize=12.5, fontweight="bold")
    ax.plot([0, 11], [0, 11], color=GREY, ls=":", lw=1.2, zorder=0,
            label="ideal (recovered = set)")
    for key, lab, col, mk, dx in series:
        c, s = res[key]["c"], res[key]["s"]
        ax.errorbar(lam + dx, c, yerr=c * s / 2.0, fmt=mk, color=col, ms=6.5,
                    capsize=4, elinewidth=1.7, capthick=1.7, lw=0, label=lab, zorder=3)
    ax.set_xlabel("nominal wavelength set at EPICS,  λ₀ (Å)")
    ax.set_ylabel("estimated wavelength (Å)   —   error bar = ± spread/2")
    ax.set_xticks(range(1, 11))
    ax.set_xlim(0.3, 10.9); ax.set_ylim(0, 11)
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.96)
    ax.text(0.985, 0.03,
            "error-bar length = recovered spread:\n"
            "  correct                 5.00%\n"
            "  swapped (distance)      4.45%\n"
            "  swapped (dist+offsets)  ~5.0%\n"
            "mean wavelength shift < 0.01% (markers on the line)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
            family="monospace", color="#333",
            bbox=dict(boxstyle="round", fc="#f4f6f7", ec="#d3d7dc"))
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chopper_label_swap.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)
    print(f"\n{'lam0':>5} {'center err% (dist)':>18} {'spread% dist':>13} {'spread% dist+off':>17}")
    for i, L in enumerate(lam):
        print(f"{L:5.1f} {(res['swap_dist']['c'][i]-L)/L*100:18.4f}"
              f"{res['swap_dist']['s'][i]*100:13.3f}{res['swap_dist_off']['s'][i]*100:17.3f}")


if __name__ == "__main__":
    main()
