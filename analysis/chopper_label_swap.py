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
    lam = np.linspace(1.0, 10.0, 181)
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
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.2, 8.0), sharex=True)
    fig.suptitle("Effect of the 1A↔ 1B / 2A↔ 2B label swap on reduction\n"
                 "(EPICS sets phases for 1–10 Å at 5% spread; reduction uses the swapped labels)",
                 fontsize=12.5, fontweight="bold")

    a1.axhline(0, color=GREY, lw=1, ls=":")
    a1.plot(lam, (res["correct"]["c"] - lam) / lam * 100, color=GREEN, lw=2.4, label="correct labels")
    a1.plot(lam, (res["swap_dist"]["c"] - lam) / lam * 100, color=RED, lw=2.0, label="swapped labels (distance only)")
    a1.plot(lam, (res["swap_dist_off"]["c"] - lam) / lam * 100, color=BLUE, lw=2.0, ls="--", label="swapped labels (distance + calib. offsets)")
    a1.set_ylabel("recovered mean\nwavelength error (%)")
    a1.set_ylim(-0.03, 0.03); a1.grid(alpha=0.25)
    a1.legend(loc="upper right", fontsize=9, framealpha=0.95)
    a1.text(0.015, 0.06, "center essentially unchanged:\nmax |error| < 0.01% across 1–10 Å",
            transform=a1.transAxes, fontsize=9, va="bottom", color=GREY,
            bbox=dict(boxstyle="round", fc="#f4f6f7", ec="#d3d7dc"))

    a2.axhline(s_in * 100, color=GREEN, lw=2.4, label=f"correct labels = input ({s_in*100:.1f}%)")
    a2.plot(lam, res["swap_dist"]["s"] * 100, color=RED, lw=2.0, label="swapped labels (distance only)")
    a2.plot(lam, res["swap_dist_off"]["s"] * 100, color=BLUE, lw=2.0, ls="--", label="swapped labels (distance + calib. offsets)")
    a2.set_xlabel("nominal wavelength set at EPICS,  λ₀ (Å)")
    a2.set_ylabel("recovered spread (%)")
    a2.set_ylim(4.2, 5.15); a2.grid(alpha=0.25)
    a2.legend(loc="lower left", fontsize=9, framealpha=0.95)
    a2.annotate("distance-only swap under-reports spread\nby ~0.55 pts (5.0% → 4.45%), flat in λ",
                xy=(6, 4.448), xytext=(4.3, 4.62), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
    a2.annotate("offsets swapped too: the un-swapped\nstation-3 disks pin the band → ~5%",
                xy=(3.0, 5.0), xytext=(4.7, 4.85), fontsize=9, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.2))

    fig.text(0.5, 0.005, "A disks (1A,2A,3A) open at λ₀(1−s/2); B disks (1B,2B,3B) close at "
             "λ₀(1+s/2). Station 3 is not swapped, so it bounds the recovered band.",
             ha="center", fontsize=8, color=GREY)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chopper_label_swap.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)
    print(f"\n{'lam0':>5} {'center err% (dist)':>18} {'spread% dist':>13} {'spread% dist+off':>17}")
    for L in [1, 2, 2.5, 4, 6, 8, 10]:
        i = int(np.argmin(np.abs(lam - L)))
        print(f"{lam[i]:5.1f} {(res['swap_dist']['c'][i]-lam[i])/lam[i]*100:18.4f}"
              f"{res['swap_dist']['s'][i]*100:13.3f}{res['swap_dist_off']['s'][i]*100:17.3f}")


if __name__ == "__main__":
    main()
