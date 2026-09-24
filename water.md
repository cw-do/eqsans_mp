# Water (H2O / D2O) at 1.3 m — where the high-Q upturn comes from

**Date:** 2026-09-24 · **drtsans:** stable production `1.34.0` (no monkeypatches)
· **scripts:** `2026B_mp/reduction/reduce_water.py`,
`2022A_mp/reduction/reduce_water_2022.py`, `2026B_mp/reduction/analyze_water.py`

**Short answer.** Flat-scattering water does show a high-Q upturn, but it is **not
water physics**. In every wavelength slice, the intensity rises with scattering
angle: +5–6 % at 20°, +13–15 % at 30°, ~+20 % in the detector corners. The rise is
the same for H2O and D2O, for the 1 Å and 2.5 Å bands, and for 2022 and 2026.
**drtsans does not apply the solid-angle correction twice** — an audit and an
on/off test show it is applied exactly once. What goes wrong is the **sensitivity
(flood) file**: it was built with the solid-angle correction computed for the
*nominal* geometry (pixels at z ≈ 1.29 m), while the reduction computes it for the
*calibrated* geometry (z ≈ 1.07 m, after the sample/detector offsets). The two do
not cancel. That alone predicts **+4.9 % at 20° and +11 % at 30°** — most of the
measured rise. In the combined I(Q), two wavelength effects at the band edge partly
hide the rise, and can even turn it into a drop. The only genuine high-Q feature is
**liquid water's first structure-factor peak at Q ≈ 1.95–2.0 Å⁻¹**, which the 1 Å
band at 1.3 m reaches (strong in D2O).

---

## 1. Every water measurement in the calibration proposals

None of these water runs had ever been reduced in the machine-physics folders.
Water shows up there only as the *flood* for old sensitivity files (2013A, 2013B,
2014A, 2020A).

| IPTS | cycle | water runs | what | used here |
|---|---|---|---|---|
| **37618** | 2026B | **188953–189016** (2026-09-23) | broadband standards block: `H2O_1mm`, `D2O_1mm` + PeltierWindow, banjo, porsil, AgBe, PMMA, blocked beam at **1.3 m 1 Å**, **1.3 m 2.5 Å**, 2.5 m 2.5 Å, 4 m 2.5 Å (`MCON16 = 0`) | **all four configs reduced** |
| 37618 | 2026B | 187505–187584 (2026-08-29 → 31) | **monochromatic** (`MCON16 = 1`) H2O / D2O at **4 m only**: λ 0.5–10 Å, dλ/λ 5/10/15 %, room temp + 65 °C, transmission through attenuators (d25mm, d15mm, d5mm, d25Cd) | not reduced — no 1.3 m setting, and no empty-beam run was taken |
| 36254 | 2026A | — | no water (has a vanadium 2-hour series) | — |
| 34965 | 2025B | 160708, 160709 | `S-80sps_10k_5wt_d2o_100N_80C` — a user polymer in D2O (22 s, 777 s), not a water standard | excluded |
| 33626 | 2025A | — | no water | — |
| 31849 | 2023A | — | no water | — |
| 30047 | 2022B | — | no water (13 runs) | — |
| **28942** | 2022A | 72 runs, three campaigns | 2022-01-04 H2O only (4 m 2.5/10/12 Å, 2.5 m 2.5/1.5 Å, **1.3 m 2.5/1 Å**, 9 m 15 Å); 2022-05-19 H2O + D2O (4 m, 2.5 m, **1.3 m 2.5 Å**); 2022-05-20 → 22 H2O + D2O (4 m, 2.5 m, **1.3 m 2.5/1 Å**, 8 m, 9 m) | **the five 1.3 m sets reduced** |
| 27799 | 2021B | — | no water | — |

**No monochromatic 1.3 m water exists** — the only monochromatic water series is
at 4 m.

## 2. How it was reduced

- **Transmission is referenced to the empty banjo cell.** The 2026-09-23 block has
  no empty-beam run (neighbouring runs are other proposals), and the 1 Å band has
  no empty beam anywhere. So every set uses its own T-banjo as the "empty", with a
  banjo background at T = 1. This leaves curve **shapes** unchanged and lowers the
  absolute scale by the cell's transmission (~0.9). **Cross-check:** at 1.3 m 2.5 Å,
  the August empty beam 186164 has the same slits, chopper phases, detector Z and
  beamstop. Reducing against it gives an identical shape (diagnostics panel c).
- **2026:** 2026B dark (186198), flood (thinPMMA 1.3 m 186202), flux (2026B), mask
  and AgBe calibration (scalecomp [1.004124, 1.057996, 1], detoffset 66.714,
  samoffset 285).
- **2022:** the 2022 conventions and files — Jan/May dark (129142 / 134663) and
  1.3 m flood (129145 / 134666), 2022A 1.3 m beamstop mask, the 2011 default flux
  profile, sampleOffset 314.5, detectorOffset 0, no AgBe calibration. 2022 ran the
  **old 4-chopper system**; 2026 runs the 6-chopper system. Because 2022 geometry
  was uncalibrated, its Q-axis reads ~6 % high, so the 2022 curves below are
  rescaled by each set's own AgBe (001) peak to 0.1069 Å⁻¹ (Q × 0.937–0.948).
- Samples: H2O, D2O, AgBe and porsil in banjo cells (banjo background); PMMA and
  blocked beam without background. 2026: 32 reductions, 2022: 31 — all ok.

## 3. The 1.3 m data (2026-09-23)

![All samples at 1.3 m, 1 Å and 2.5 Å bands](assets/water/water_1p3m_2026.png)

H2O (~2.4–2.5 cm⁻¹) and D2O (~0.19 cm⁻¹) are flat from 0.1 to ~1 Å⁻¹. In the 1 Å
band, D2O rises into a strong peak at **Q = 1.95 Å⁻¹ (1.70× its plateau)**. That is
the first peak of liquid D2O's structure factor — real, and expected. H2O's
coherent peak is weak under its large incoherent level. The AgBe (001) peak sits at
0.1064 / 0.1059 Å⁻¹ (2.5 Å / 1 Å bands), within 1 % of 0.1069 — the 1.3 m Q-axis
is right.

## 4. The upturn is a function of **scattering angle**, not Q

Reducing with the per-wavelength profile output gives I(Q) for each 0.1 Å
wavelength slice (35 per band). Each slice rises toward its own high-Q end — which
is always the largest scattering angle.

![Per-wavelength I(Q) slices at 1.3 m](assets/water/water_perlambda.png)

Plot every slice against **2θ** instead, normalised to its own 3–6° level, and all
35 slices collapse onto **one curve** — a per-pixel factor, independent of
wavelength and Q:

![Slices vs scattering angle](assets/water/water_vs_angle.png)

| median over all slices | 2θ = 20° | 2θ = 30° |
|---|---|---|
| 2026 H2O · 1 Å / 2.5 Å | 1.053 / 1.060 | 1.130 / 1.138 |
| 2026 D2O · 1 Å / 2.5 Å | 1.059 / 1.063 | 1.148 / 1.144 |
| 2022 H2O · 1 Å / 2.5 Å | 1.056 / 1.061 | 1.135 / 1.142 |
| 2022 D2O · 1 Å / 2.5 Å | 1.060 / 1.053 | 1.136 / 1.125 |
| **predicted: flood solid-angle geometry ≠ reduction geometry (§6)** | **1.049** | **1.107** |
| 1 / cos 2θ (for scale) | 1.064 | 1.155 |
| 1 / cos³ 2θ (a full extra solid-angle factor) | 1.205 | 1.540 |

![Median angular rise, 2022 vs 2026](assets/water/water_angle_summary.png)

What this rules out, and what it points to:

- **Not the sample.** H2O (T′ ≈ 0.63) and D2O (T′ ≈ 0.93) rise identically, so
  self-absorption, the θ-dependent transmission and multiple scattering are not
  involved — all three scale with how strongly the sample attenuates.
- **Not wavelength.** 1.2 Å and 6 Å slices rise identically, so it is not detector
  efficiency (λ-dependent) or H2O's inelastic scattering.
- **Not one flood or one year.** 2022 (old flood, 4-chopper system, 2011 flux) and
  2026 give the same curve.
- **Not a double solid-angle correction** — that would be 1/cos³ 2θ, 3–4× too
  large, and the audit shows the correction is applied once (§6).
- **It is the flood's solid-angle geometry.** The green curve in the figure above is
  the predicted factor from §6, computed pixel by pixel with no free parameter. It
  matches the data to ~17° and accounts for ~80–90 % of the rise at 20° and ~75 % at
  30°. The remaining +1 % at 20° / +3–4 % at 30° is still open (candidates in §6).

The same factor appears in the combined I(Q) as a bump toward each
configuration's edge. For the three configurations sharing the 2.5 Å band, the
bump sits at the same Q × L — the same radius on the detector — not at the same Q:

![H2O / D2O across configurations and vs Q × L](assets/water/water_config_overlap.png)

## 5. Why the combined I(Q) often *drops* instead

In the combined curve, the highest Q of each configuration comes only from the
shortest wavelengths. Two wavelength effects work against the angular rise there:

1. **Band-edge slice.** The first (shortest-λ) slice of every band is normalised
   30–56 % too low. H2O 1 Å: 0.80 vs 1.81 for the next slice; H2O 2.5 Å: 1.47 vs
   2.08; D2O the same. This is the flux normalisation at the chopper-opening edge.
   That one slice dominates the last Q points, so each configuration's curve falls
   at its Q-max.
2. **Level rises with λ.** Across the 1 Å band, the plateau of **both** H2O and D2O
   climbs ×1.4 from 1.4 Å to 4.6 Å — mostly the flux-spectrum shape at short λ. In
   the 2.5 Å band, H2O climbs ×1.37 but D2O only ×1.17; the difference is H2O's
   inelastic incoherent scattering.

The flux file sets this balance. Reducing the same 2022 data with the 2026B flux
instead of the 2011 profile flips the H2O 1 Å high-Q end from a **drop (0.83×)**
to an **upturn (1.31×)**, and doubles the D2O edge (1.27× → 2.00×). The 2022 and
2026 curves agree closely from 0.1 to ~1 Å⁻¹ but part ways at the very high-Q end:

![2022 vs 2026 at 1.3 m](assets/water/water_2022_vs_2026.png)

![Diagnostics](assets/water/water_diagnostics.png)

- **(a) drtsans inelastic-incoherent correction** (`fitInelasticIncoh`) removes
  most of the water signal and leaves a curve that **rises monotonically** with Q.
  The H2O edge goes 0.52 → 1.31, D2O 0.83 → 2.46. This correction assumes a
  flat incoherent background under a coherent signal; water *is* the incoherent
  signal, so applying it to water manufactures an upturn.
- **(b) flux swap** (above).
- **(c) transmission reference** — banjo-referenced and true empty beam give the
  same shape.
- **(d) room background** — the blocked-beam residual that survives background
  subtraction is ≤ 1.4 % of the water signal even at the highest Q. Negligible.

## 6. Does drtsans apply the solid-angle correction twice?

**No.** A code audit of drtsans 1.34.0 plus a direct test show the correction is
applied **exactly once** to every workspace that should get it.

| workspace | solid angle | where (drtsans 1.34.0) |
|---|---|---|
| sample, background (banjo) | once | `tof/eqsans/api.py` → `reduction_api.py:133` (`useSolidAngleCorrection: true`) |
| empty / transmission runs | no (a ratio — it would cancel) | `reduction_api.py:168` |
| dark current, blocked beam | no; subtracted from raw counts *before* the sample's correction — consistent | `reduction_api.py:112–123` |
| sensitivity *application* | no — a plain divide | `sensitivity.py:130` |
| sensitivity *preparation* (flood) | once, `SOLID_ANGLE_CORRECTION=True` | `prepare_sensivities_correction.py:561–569` |

The formula is Mantid `SolidAngle(Method="VerticalTube")`, the right one for
EQSANS's vertical tubes (0.878 at 20°, vs 0.851 for a flat plane).

**The on/off test** (run 188966, H2O 1.3 m 1 Å): the reduction's own
`prepare_data_workspaces` call, with solid angle on vs off. (off/on) matches the
vertical-tube formula to machine precision, and its square is off by 10 % — so it
is applied once. The saved `H2O_1p3m_1A_processed.nxs` equals the solid-angle-on
workspace to ±0.7 % at every angle, so nothing later in the chain applies it again.

**The actual error is a geometry mismatch between flood and reduction.** The
flood divides out the solid angle computed with the *nominal* geometry (sample at
the nominal position, **pixels at z = 1.27–1.30 m**, no offsets, no
`scaleComponents`). The reduction divides out the solid angle computed with the
*calibrated* geometry (samoffset 285 mm, detoffset 66.7 mm, scaleComponents →
**pixels at z = 1.05–1.09 m**). With the same geometry the two cancel, as the
sensitivity scheme intends. With different geometry, the same pixel sits at
different angles in the two calculations, so each pixel keeps a factor
SA_flood / SA_sample. That factor is +0.6 % at 8°, +2.4 % at 14°, **+4.9 % at 20°**,
+6.8 % at 23° and **+11 % at 30°**; about +0.9 % of the 20° value comes from
`scaleComponents` alone. The cause is in
`prepare_sensitivity.py` → drtsans `prepare_sensitivities_correction`, which passes
only the beam centre and flux to the loader, so the offsets default to 0 and scale
components are never set.

Smaller angle effects checked:
- θ-dependent transmission correction: ~+1 % expected at 20°; after banjo
  subtraction the net is ≈ 0.
- The flood was taken in the 2.5 Å band and is also used for the 1 Å band. Back
  tubes come out ~7.6 % high relative to front tubes, nearly flat in angle (≤ +1 %).
- Dark current: ~2 × 10⁻⁶ of the water rate.

**Fix (not applied — it changes every user's reduction at 1.3 m):** build the
flood with the reduction geometry. The preparer has no offset setter, but
`scale_components` exists; the offsets would need a small drtsans change or a
patched loader. Alternatively, multiply the existing flood by SA_sample / SA_flood,
or turn solid angle off in both the flood and the reduction (they are at the same
distance). The 2022 data show the same rise. The 2022 flood was presumably built the
same way, but that has not been checked.

Audit script and numbers: `2026B_mp/reduction/solid_angle_audit/sa_test.py`,
`sa_test_results.txt`; predicted curve `sa_flood_mismatch.csv`.

## Verdict

1. **Water's "strange upturn" at high Q is instrumental.** Within every wavelength,
   intensity rises toward large angles (~+5–6 % at 20°, ~+13–15 % at 30° at 1.3 m),
   the same in 2022 and 2026, for H2O and D2O.
2. **drtsans applies the solid-angle correction once, not twice.** Most of the rise
   comes from a **flood built with the nominal geometry** while the reduction uses the
   AgBe-calibrated one (predicted +4.9 % at 20°, +11 % at 30°). A residual of
   ~+1 % at 20° / +3–4 % at 30° is still unexplained.
3. How it shows up in a combined I(Q) depends on the **band-edge flux
   normalisation**. It can appear as an upturn (2022 D2O 2.5 Å, 1.28×; any data
   with a mismatched flux file), as a bump before the edge (all configurations), or
   be hidden under a drop (2026).
4. **Don't apply drtsans's inelastic-incoherent correction to water standards** —
   it creates a rising curve.
5. The one real high-Q feature is liquid water's **S(Q) peak at 1.95–2.0 Å⁻¹** in
   the 1 Å band (D2O 1.70× plateau), at the same Q in 2022 and 2026 once 2022's Q
   is AgBe-rescaled.

**Follow-ups:** rebuild the 1.3 m flood with the reduction geometry and re-check
the water slices (expect the rise to drop to the ~1–4 % residual); check the 2022
flood's geometry; the 4 m monochromatic water series (needs empty-beam runs matched to
its attenuators); the IPTS-36254 vanadium series, a λ-independent elastic flat
scatterer that would confirm the angular factor without any water physics; and a
fix for the band-edge slice (drop the first 0.1 Å bin or tighten the TOF cut).

**Provenance.** 2026-09-24, drtsans `1.34.0`:
`reduce_water.py` → `2026B_mp/reduction/reduced_water/` (32/32 ok: 4 configs ×
6 samples, empty-beam cross-check, per-λ profiles);
`reduce_water_2022.py` → `2022A_mp/reduction/reduced_water/` (31/31 ok: 5 sets,
flux swap, per-λ profiles); `solid_angle_audit/sa_test.py` → the solid-angle
on/off test and the flood-mismatch prediction; `analyze_water.py` → the figures and
`doc/water_assets/water_metrics.json`.
