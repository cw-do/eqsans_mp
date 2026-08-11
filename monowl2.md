# Monochromatic reduction II — peak position, wavelength binning & Q

A follow-up to the **monoWL** tab. Once the monochromatic AgBe runs reduced, the
diffraction **peak position appeared to shift with the spread setting** — dl/l=0.05
gave Q≈0.104, dl/l=0.15 gave Q≈0.108. That should be impossible: AgBe has a fixed
d-spacing, so its ring must sit at the same Q at every spread — the EQSANS AgBe
calibration target **Q1 = 0.1069 Å⁻¹** (d(001) ≈ 58.8 Å; `TARGET_Q1` in the AgBe
calibration) — only the *resolution* (peak width) should change.

This page tracks that down. The short version: **nothing is wrong with the
wavelength conversion or the calibration.** The shift is entirely an artifact of
collapsing the band into a single wavelength bin, and it disappears when the band
is reduced wavelength-resolved (as broadband always is).

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

The middle is correct (true ≈ label), but the labels are **compressed** relative to
the true wavelengths — the ring angles span the full transmitted band (~2.22–2.66 Å,
matching the 0.43 Å band width), while the labels span only 2.29–2.64. A mislabelled
λ gives Q = 4π·sinθ/λ_assigned off by the mislabel ratio, varying across the band.

**The cause is the chopper config we forced, not the data.** The monochromatic
reduction is "special" only because we changed two things for it: (1) monkeypatched
drtsans to the `20260101` chopper config (the default gives empty bands for narrow
spreads), and (2) disabled TOF clipping. The chopper config feeds
`correct_tof_frame`, which sets the TOF→wavelength/frame correction from the chopper
geometry. Re-running the *same* dl/l=0.15 AgBe with the **default** config (no force)
collapses the drift from 7.2σ to ~2σ (the reliable slices go flat) — so the forced
`20260101` config, while it centres the band at 2.5 Å, skews the wavelength
assignment *inside* the band. Broadband (default config, wide well-resolved band) is
immune. The corollary is uncomfortable: the config needed to make the narrow bands
*load* and centre correctly is the same one distorting the intra-band wavelength
scale — so neither 6-chopper config is fully right for these runs. This is the same
chopper-configuration problem flagged on the monoWL tab, now with a second symptom.

**Practical impact is small:** the *combined* (multi-bin) mono peak still lands near
Q1 (0.1065–0.1067), because it is the intensity-weighted average over the band,
dominated by the centre where the distortion vanishes. So the recommendation holds.

*(Earlier versions of this page first claimed the mono slices "overlap at Q1"
(an argmax illusion), then blamed "flux-starved edge slices" — both wrong. A proper
Gaussian fit shows a real drift; the broadband control at 0.05 Å being flat rules
out slicing; and the default-config test pins the cause on our forced chopper
config.)*

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

## Scripts & data

All under `2026B_mp/reduction/mono_diagnosis/`:
`reduce_agbe_mono.py` (single-bin), `reduce_agbe_multibin.py` (0.1 Å),
`reduce_agbe_dl05_fine.py` (convergence), `reduce_agbe_perslice.py` (per-slice
profiles). Figures drawn by `doc/monowl_assets/make_monowl_plots.py`; peak fits
by scipy Gaussian + linear background over Q ∈ [0.085, 0.130].
