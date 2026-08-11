# Monochromatic reduction II — peak position, wavelength binning & Q

A follow-up to the **monoWL** tab. Once the monochromatic AgBe runs reduced, the
diffraction **peak position appeared to shift with the spread setting** — dl/l=0.05
gave Q≈0.104, dl/l=0.15 gave Q≈0.108. That should be impossible: AgBe has a fixed
d-spacing, so its ring must sit at the same Q at every spread — the EQSANS AgBe
calibration target **Q1 = 0.1069 Å⁻¹** (d(001) ≈ 58.8 Å; `TARGET_Q1` in the AgBe
calibration) — only the *resolution* (peak width) should change.

This page tracks that down (and was corrected several times as it did). The solid
result: the **single-bin reduction** shifts the peak by forcing one wavelength into
the Q calculation — fixed by a **wavelength-resolved** reduction. The chopper config
does **not** reassign individual event wavelengths. A small (~0.5 %)
monochromatic-vs-broadband peak offset remains as an open instrument-level item. The
bottom line is in *Final verdict* at the end; the reasoning is below.

## The symptom

Gaussian fits of the AgBe (001) peak from the single-bin "monochromatic mode",
against the calibration target:

| reduction | dl/l=0.05 | dl/l=0.10 | dl/l=0.15 |
|---|---|---|---|
| single-bin (monochromatic mode) | 0.1039 | 0.1070 | 0.1079 |
| **AgBe calibration target (all spreads)** | **0.1069** | **0.1069** | **0.1069** |

The reference is the calibration target **Q1 = 0.1069 Å⁻¹**. The AgBe calibration's
own verification (Details tab) reaches it — q1 = 0.1069 at both 2.5 Å and 6 Å, and
0.1074 at 10 Å (so even the calibration scatters ~0.5% across configurations, from
the coarse log-Q grid, not from the physics). A Gaussian fit of the standard
broadband reductions lands at ≈0.1068 for every configuration — essentially the
target. And the transmitted **band centre is 2.475 Å for all four spreads** — the
spread setting widens the band but does not move its centre. So neither the
detector geometry nor the centre wavelength is shifting; the problem is downstream,
in how I(Q) is built.

## The mechanism — drtsans computes Q from the wavelength *bin centre*

When drtsans histograms events into wavelength bins, each (pixel, wavelength-bin)
cell gets its Q from the **bin-centre** wavelength and the pixel angle:

```
Q_computed = 4*pi*sin(theta) / lambda_bin-centre
           = Q_true * (lambda_true / lambda_bin-centre)
```

This equals the true Q1 **only when the bin centre matches the neutron's true
wavelength.** A neutron whose true wavelength differs from its assigned bin centre
is placed at the wrong Q, scaled by the ratio of the two.

This is *provable*: if drtsans used each event's true (time-of-flight) wavelength,
the bin width could not possibly matter — one bin would already give Q1. It does
matter (below), so drtsans is using bin centres.

## Single-bin collapses the band → a shift set by intensity weighting

![Peak position vs spread and convergence with finer binning](assets/monowl/monowl2_peakpos.png)
*Figure: (left) fitted AgBe peak vs spread — single-bin (red) drifts away from the broadband calibration (grey), multi-bin at 0.1 Å (green) stays on it; (right) dl/l=0.05 climbs to Q1 as the band is split into more wavelength bins. Fits by scipy; reductions by reduce_agbe_mono.py / reduce_agbe_multibin.py / reduce_agbe_dl05_fine.py.*

In single-bin mode the whole transmitted band (0.13–0.43 Å wide) becomes **one**
bin, and every neutron is assigned the single band-centre wavelength. Neutrons of
different true wavelength — which diffract at different detector angles — are all
re-mapped with that one λ, so the sharp ring smears, and the **intensity-weighted
mean wavelength** of the band sets where the merged peak lands:

```
Q_peak(single-bin) = Q1 * <lambda>_intensity-weighted / lambda_bin-centre
```

That is the weighting effect: the peak moves because the flux is not flat across
the band, not because any wavelength is mis-measured.

**A clean demonstration — dl/l=0.05.** Here the band (0.176 Å) is narrow enough
that *both* the single-bin and the 0.1 Å "multi-bin" reductions ended up with
**exactly one wavelength bin** — but at different centres:

| reduction | wavelength bins | assigned λ | peak Q |
|---|---|---|---|
| single-bin (mono) | 1 | 2.475 Å (band centre) | 0.1039 |
| multi-bin (0.1 Å) | 1 | 2.437 Å (top of band dropped by `FullBinsOnly`) | 0.1058 |

With one bin each, "multi vs single" is a distinction without a difference — the
only thing that changed is the assigned wavelength. And Q ∝ 1/λ predicts the whole
shift: 0.1039 × (2.475 / 2.437) = **0.1055** ≈ the observed 0.1058. Direct proof
that a single bin's peak Q is set by its assigned wavelength.

## The proof — every wavelength gives the same Q (broadband), and why the mono slices look like they don't

The physical requirement is that AgBe sits at the same Q at *every* wavelength — a
different wavelength diffracts at a different angle, but Q = 4π·sinθ/λ maps them all
to the same Q. Different wavelengths cannot reveal different structure. The decisive
test is to write out I(Q) for each wavelength slice separately and fit its peak.

![Per-slice AgBe peak vs wavelength: broadband flat, mono drift is a fine-slice artifact](assets/monowl/monowl2_trend.png)
*Figure: fitted AgBe(001) peak Q per wavelength slice. Broadband (green, run 186106, 2.7–5.6 Å) is dead flat on the calibration target — slope 0.4σ = zero — so every wavelength gives the same Q, as required (and it stays flat at a 0.05 Å step too). The monochromatic dl/l=0.15 band (red, 2.3–2.6 Å) drifts 7.2σ (0.104→0.108) — a real, mono-specific wavelength-axis distortion (see below), not flux and not slicing. Gaussian fits by scipy; per-slice profiles from reduce_agbe_perslice.py / reduce_agbe_bb_perslice.py / reduce_agbe_bb05_perslice.py.*

**Broadband is the clean answer:** across 2.7–5.6 Å every slice fits to
0.1067 ± 0.0001 — flat, on target (slope 0.4σ = zero). Different wavelengths give
the same Q, and a monochromatic beam at any one of those wavelengths sits there too.
This holds at 0.1 Å **and** at a fine 0.05 Å step (61 slices, slope 0.000016/Å,
negligible) — so fine slicing itself does *not* cause a drift.

**The monochromatic per-slice drift is a wavelength-axis distortion, not flux and
not slicing.** When the *narrow* dl/l=0.15 band is sliced at 0.05 Å, the fitted
peaks drift 7.2σ (0.104→0.108) — ~275× steeper than the broadband slope at the same
step. Since the broadband control at 0.05 Å is flat, this is neither counting
statistics (peak *position* does not depend on flux) nor a slicing/grid artifact.
It comes from the **wavelength assignment inside the narrow band**. Converting each
slice's measured ring angle back through Bragg gives the *true* wavelength that
produced it:

| slice **label** λ | true λ from ring angle |
|---|---|
| 2.287 | 2.223 |
| 2.437 | 2.438 |
| 2.487 | 2.494 |
| 2.587 | 2.599 |
| 2.637 | 2.658 |

**It is NOT the reduction config.** It is tempting to blame the `20260101` config we
forced for the mono reduction, but the data rules that out: re-reducing the *same*
mono run with the **default** config gives the **same q0 at every matched wavelength**
(≈0.1071–0.1074 near 2.5 Å with either config). The config changes only *which band
loads* (its edges), not the wavelength assigned to a given event — consistent with
the physics: `correct_tof_frame` only **frame-unwraps** slow neutrons (adds whole
pulse periods), and the fast 2.5 Å neutrons here do not wrap, so their wavelength is
config-independent. The apparent 7.2σ-vs-2σ difference between configs was only that
the forced config's *wider* band reaches down to ~2.29 Å, where q0 droops; the
default band starts at ~2.44 Å and never samples it.

**What is left is a real, unexplained run-level offset.** Comparing the reduced
*runs* rather than the configs: where the monochromatic run (186246) and the
broadband run (186106) overlap in wavelength (~2.6 Å), the mono AgBe peak sits at
≈0.1074 while broadband sits at ≈0.1067 — a **~0.5 % offset** — and the mono run
droops further at short λ. Broadband is flat (0.1067–0.1068) wherever it is measured.
This is a difference between the two **physical measurements** (different chopper
*hardware* settings/timing for monochromatic vs broadband), present under either
reduction config — most likely an **instrument-level chopper-phasing / TOF-timing**
effect in the monochromatic setup, not a reduction artifact. It is not yet
explained, and is flagged as an open item.

**Practical impact is small:** the *combined* (multi-bin) mono peak still lands near
Q1 (0.1065–0.1067). The recommendation (wavelength-resolved reduction, standard
calibration) holds.

*(This page has been corrected repeatedly as the analysis sharpened: it first
claimed the mono slices "overlap at Q1" (argmax illusion), then blamed "flux-starved
edge slices", then "a forced-config wavelength distortion / calibration mismatch" —
all wrong. The verified facts: single-bin shifts the peak by band-centre weighting
(use wavelength-resolved instead); the reduction **config does not reassign
wavelengths**; and a small ~0.5 % monochromatic-vs-broadband peak offset remains, an
open instrument-level question.)*

## Why broadband at 0.1 Å is fine but single-bin is not

They sound like they should be identical — a monochromatic 2.5 ± 0.05 Å band is
just the [2.45, 2.55] slice of a broadband run. And they *are*: both give Q1. The
difference is only how many bins the ring's wavelength content is spread over:

- **Broadband** always chops into ~0.1 Å slices, so the AgBe ring is built from
  **many** slices, each at Q1 → sum at Q1. A 0.1 Å bin's residual smear is ±2% and
  symmetric, and averages out over the many bins.
- **Single-bin "monochromatic mode"** puts the ring's *entire* wavelength content
  into **one** bin as wide as the band (up to 0.43 Å) → large smear, weighted
  shift, no averaging.

So monochromatic data is not intrinsically "more sensitive to binning." A
monochromatic 0.1 Å band reduced in a 0.1 Å bin behaves exactly like a broadband
0.1 Å slice. The shift came only from collapsing a *wide* band into *one* bin —
something broadband never does. Split the band into several bins and the peak
converges to Q1 (right panel of the first figure: 1 bin → 0.1039, 2 → 0.1063,
8 → 0.1066, approaching the 0.1069 target).

## Recommendation

- **Use the same calibration for every spread.** You never need a different
  geometry for dl/l=0.05 vs 0.15 — the calibration is spread-independent (target
  0.1069; broadband and every per-slice above sit at ≈0.1068–0.1069).
- **Reduce wavelength-resolved — multiple bins across the band, not one.** A
  wavelength step that puts several bins across the transmitted band (roughly
  step ≤ band/5), or simply the standard broadband-style reduction. Every spread
  then gives the same peak position, differing only in resolution — exactly as
  expected.
- **You do not sacrifice the wavelength-dependent normalization.** Peak *position*
  does not depend on it at all (normalization scales intensity, not Q), and over a
  *narrow* monochromatic band the flux/sensitivity barely change, so the per-slice
  normalization is nearly uniform — the artifact that motivated collapsing to one
  bin is negligible precisely because the band is narrow. The aggressive
  wavelength-dependent *corrections* (inelastic/elastic) can simply be left off.
- **Do not use the single-bin "monochromatic mode" for quantitative Q.** It forces
  one wavelength into the Q calculation and silently shifts the peak; the narrower
  the resolution the more it collapses, until the run is flux-starved. It is the
  wrong lever.

This reverses the provisional recommendation on the monoWL tab (which framed
single-bin as *the* fix): the correct approach is a wavelength-resolved reduction
with the standard calibration.

## Final verdict — what is solid, and what is still open

This investigation was corrected several times as the analysis sharpened. The
verified conclusions:

**1. Single-bin reduction shifts the peak (real; fixable).** Collapsing the whole
band into one wavelength bin forces a single λ into Q = 4π·sinθ/λ, so the merged peak
lands at the intensity-weighted mean wavelength and shifts with spread. **Fix:**
reduce wavelength-resolved (multiple bins across the band), with the standard
calibration. Then every spread gives the same peak position, differing only in
resolution.

**2. The reduction config does NOT reassign individual wavelengths.** At a pulsed
source the recorded time is relative to the proton pulse and ambiguous by whole pulse
periods; `correct_tof_frame` only **frame-unwraps** slow neutrons (adds pulse
periods). The fast 2.5 Å monochromatic neutrons do not wrap, so their wavelength is
independent of the chopper config — confirmed by re-reducing the same mono run with
two different configs and getting the **same q0 at every matched wavelength**. The
chopper phase sets *which* wavelengths pass (the band), not each event's wavelength.
*(An earlier version of this page claimed a config-driven "wavelength distortion /
calibration mismatch" — that was wrong and has been retracted.)*

**3. Open item — a ~0.5 % monochromatic-vs-broadband peak offset.** Where the
monochromatic run and a broadband run overlap in wavelength (~2.6 Å), the AgBe peak
differs by ~0.5 % (mono ≈0.1074 vs broadband ≈0.1067), with a further droop at short
λ in the mono run. This is a difference between the two **physical measurements**
(different chopper hardware settings/timing), present under either reduction config —
most plausibly an **instrument-level chopper-phasing / TOF-timing** effect in
monochromatic mode. It is small (combined peak still ≈Q1) and **not yet explained**;
it needs an instrument-level TOF/chopper-timing check, not a reduction change.

## Note on calibration

All 2026B machine-physics calibration (dark, sensitivity, flux, AgBe geometry) was
done under the default `20260304` config, without forcing. Because the detector
**geometry** calibration (`detoffset`, `samoffset`) constrains scattering *angle*,
which is wavelength-independent, it transfers across configs — so a config change at
reduction time does not, by itself, invalidate the geometry calibration. The 6-chopper
config still needs to be corrected upstream for other reasons (it gives empty/
mis-centred bands for narrow monochromatic spreads — see the **monoWL** tab), and the
~0.5 % monochromatic offset above should be understood; if the correct chopper
configuration changes the *band definition* materially, it is prudent to re-verify the
AgBe calibration under it. But the strong "recalibrate everything because the config
distorts wavelengths" claim from an earlier version of this page is **withdrawn** — the
config does not distort the per-event wavelengths.

## Scripts & data

All under `2026B_mp/reduction/mono_diagnosis/`:
`reduce_agbe_mono.py` (single-bin), `reduce_agbe_multibin.py` (0.1 Å),
`reduce_agbe_dl05_fine.py` (convergence), `reduce_agbe_perslice.py` (mono per-slice
profiles), `reduce_agbe_bb_perslice.py` / `reduce_agbe_bb05_perslice.py` (broadband
per-slice controls), `reduce_agbe_dl15_default.py` (default-config isolation test).
Figures drawn by `doc/monowl_assets/make_monowl_plots.py`; peak fits by scipy
Gaussian + linear background over Q ∈ [0.085, 0.130].
