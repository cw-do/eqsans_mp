# Water 4 — why self-flooded water is not flat, and what makes it flat

**Date:** 2026-09-25 · **drtsans:** stable `1.34.0` · **data:** the 2026-09-23 1.3 m block
(IPTS-37618), 1 Å and 2.5 Å bands; H2O 188966 / 188982, D2O, PMMA in the same block ·
**scripts:** `2026B_mp/reduction/water3/water4/`

**The question.** H2O is reduced with a flood made from **the same H2O run**. Everything is
done the same way in both:
- the banjo cell and the blocked beam are subtracted;
- solid-angle and θ-dependent transmission corrections are applied;
- the incoh fit is on.

Why, then, is I(Q) not perfectly flat? Every I(Q, λ) slice has a slight slope, and the
combined curve has small but systematic deviations.

> **Blocked-beam and flood set-up on this page.** Every reduction here is Water 3 §9 case D.
> - **Flood:** `Sensitivity_H2Obsbb_*`, built from the same H2O run, with the banjo AND the
>   blocked beam subtracted (188984 at 2.5 Å, 188968 at 1 Å).
> - **Reduction:** H2O, D2O and PMMA with `blockedBeamRunNumber` set to the same run; dark
>   current 186198.
>
> The flood band matches the data band.

**Short answer.** It is not the flood, and it is not the solid angle. Four things remain:

1. **The b(λ) fit amplifies each slice's shape, relative to a bad reference** (proven exactly,
   §3). drtsans subtracts a constant b(λ) so that every slice matches the reference slice.
   With `selectMinIncoh`, that is the slice with the smallest b: always the **band-edge**
   slice, which sits at about half the level of the others.
   - Each slice's relative shape is multiplied by c(λ)/c_ref, up to **2.0×** (2.5 Å band) and
     **3.4×** (1 Å band): measured correlation 1.000, slope 1.00.
   - The absolute level becomes the edge slice's: 0.86 / 1.55 cm⁻¹ instead of about 2.5.
2. **The band-edge slices are not usable** (§4). The first and last 2–3 λ bins of each band
   (the partly lit edges of the chopper window) are off by up to 2× in level and ±2 % in
   shape. They are the only slices that reach the highest Q, so they set the high-Q end.
3. **The θ-dependent transmission correction uses the incident-λ transmission for the exit
   path** (§5). For water, which scatters inelastically and heats cold neutrons, this puts an
   angle × λ error in each slice. It is proven with a fixed-Q test that is free of the sample's
   S(Q). Making the exit path λ-independent flattens the λ-trend: +0.33 → −0.03 %/Å.
4. **Above about 0.9 Å⁻¹, what is left is water's own S(Q)** (§7). About 4.6 % of H2O's
   cross-section is coherent. The same −0.4 % dip at 1.0–1.3 Å⁻¹ appears in both bands, although
   the 1 Å band sees it at 12–20° and the 2.5 Å band at 25–35°. It is real, and it should not
   be flattened.

**Result.** With the band edges removed and the exit path made λ-independent, still using
drtsans's own b(λ) fit and binning:
- **self-flooded H2O is flat to 0.08–0.11 % rms, and within 0.36 % everywhere, over
  Q 0.1–0.9 Å⁻¹, in both bands;**
- χ²/bin falls from 24 / 12 (default) to 4.3 / 2.3, i.e. 1.5–2 × the counting error;
- the absolute level after the incoh fit comes back to 2.25 / 2.46 cm⁻¹.

The production-style version needs only configuration changes: wider TOF edge cuts,
**`cutTOFmin` 1650 / `cutTOFmax` 3150 µs**. It already reaches 0.11–0.12 % rms (χ² 9.2).

![self-flooded H2O at 1.3 m, incoh fit on: drtsans default, production recipe, full recipe](assets/water4/w4_hero.png)

---

## 1. Why a self-flood can only be flat on average

The flood is one number per pixel: the flux-weighted sum over λ of the water's own counts.
Dividing by it removes everything that factorises as **(pixel) × (λ)**. So, at every pixel,
the flux-weighted average over λ of the self-flooded water is exactly flat.

What survives is the **non-separable part**: an angular shape that differs between
wavelengths. This is exactly what you see as "each slice has a slope". A slope common to all
slices would have been divided out by the flood, so the slices must tilt in different
directions: short λ one way, long λ the other. Their average is flat, but the combined I(Q)
is not an average over all λ at every Q. At the highest Q only the shortest λ contribute,
so their tilt shows.

The non-separable part can be measured without any flood:
Δ(pixel, λ) = r / (λ-median of r at that pixel), with r = P / P(2θ 3–6°) per λ. Any
per-pixel factor, i.e. any flood, cancels in Δ (`diag_w4.py`).

![Δ(2θ, λ) for H2O, PMMA and D2O, both bands](assets/water4/w4_delta_maps.png)

How to read the maps:
- **Diagonals are lines of constant Q** (λ ∝ sin θ), so they are the sample's own structure.
  PMMA's map is almost all diagonals (its ~1 Å⁻¹ structure). So is most of H2O's 1 Å map: red
  at Q > 1.6 Å⁻¹ and blue at 1.1–1.5 Å⁻¹.
- **Horizontal bands are λ-effects:** in H2O at 2.5 Å, red at 4.8–5.5 Å growing with angle,
  and blue at the 2.7 Å band edge.

![Δ vs 2θ for six wavelengths, and the same vs Q](assets/water4/w4_delta_cuts.png)

## 2. Hypotheses and verdicts

| | hypothesis | prediction | test | verdict |
|---|---|---|---|---|
| H1 | detector efficiency vs angle and λ (tube layers, oblique incidence) | same for every sample; strongest at short λ; direction-dependent | Δ by layer/direction; 3He shadowing model fitted (`model_w4.py`) | **exists per pixel, not the cause in I(Q)** (§6) |
| H2 | water's inelastic scattering: exit neutrons faster than incident | an angle × λ error in the θ correction, only for inelastic samples | fixed-Q test, exit-path scan (§5) | **confirmed** |
| H3 | self-absorption / multiple-scattering model | scales with (1 − T) | part of H2's test | covered by H2 |
| H4 | water's own S(Q) (coherent ≈ 4.6 %) | depends on Q, not angle; same in both bands | both bands overlaid (§7) | **confirmed, above ~0.9 Å⁻¹** |
| H5 | count-rate dead time | depends on rate (H2O ≫ banjo) and the flux peak | not tested | not needed: the rest is at the statistical level |
| H6 | the b(λ) fit (additive, band-edge reference) | amplifies each slice by c(λ)/c_ref | drtsans's before/after profiles (§3) | **confirmed, exactly** |

Everything was checked through **drtsans's own code**. `tail_w4.py` reloads a reduction's
`_processed.nxs`, applies a per-pixel × per-λ correction, and calls drtsans's
`convert_to_q` → `split_by_frame` → `bin_i_with_correction` (binning, b(λ) or k(λ), and the
combination), with the reduction's own parameters. With no correction it reproduces the
original `_Iq.dat` **bit for bit** (max relative difference 0.0).

## 3. Test 1 — the b(λ) fit amplifies each slice's shape (H6)

drtsans's b(λ) (`calculate_b_factors`) works like this:
- the reference is the shortest λ, or with `selectMinIncoh` the slice with the smallest b;
- every slice is shifted down by b(λ) = its mean excess over that reference.

A constant shift keeps each slice's *absolute* deviation, so its *relative* deviation grows by
c(λ)/c_ref. The reference is the band-edge slice (level 1.55 against up to 3.15 in the 2.5 Å
band; 0.86 against 2.90 in the 1 Å band).

| band | largest gain c(λ)/c_ref | rms slice deviation before → after b(λ) | after = before × c/c_ref |
|---|---|---|---|
| 1 Å | 3.39 | 1.03 % → **2.54 %** | correlation 0.999, slope 0.96 |
| 2.5 Å | 2.03 | 0.53 % → **0.89 %** | correlation 1.000, slope 1.00 |

![slice levels, deviations before/after b(λ), and the exact amplification](assets/water4/w4_amplification.png)

The same mechanism sets the absolute level after the fit to that of the band-edge slice, which
is why the incoh-on plateau differed between configurations (Water 3 §5).

## 4. Test 2 — the band-edge slices

The fixed-Q test (§5 figure) shows the first 2–3 bins of the 1 Å band and the last 3 of the
2.5 Å band deviating by 1–2 % in shape, besides their factor-2 level offset.

Dropping 3 bins (0.3 Å) at each end has two effects:
- **The b(λ) reference becomes a normal slice.** With the edges out, b(λ) and a
  multiplicative k(λ) give the same result (R3 vs R3b in §8).
- **The spurious high-Q end goes away.**

In production this is the TOF edge cut. The present `cutTOFmin` 500 / `cutTOFmax` 2000 µs is
too small at 1.3 m. **1650 / 3150 µs** (≈ +0.3 Å at each end) was tested in a normal drtsans
reduction (P1, §8).

## 5. Test 3 — the θ-dependent transmission correction's exit path (H2)

drtsans divides every sample by A = T(λ)^((1 + sec 2θ)/2), using the transmission of the
**incident** wavelength for the path out of the sample as well. Water scatters strongly and
inelastically: cold neutrons are mostly *heated*, so the scattered neutrons are faster and
are attenuated less on the way out than T(λ) implies. The exit-path loss is therefore
over-corrected, more at longer λ (lower T) and at larger angle. That produces a fan: long-λ
slices tilt up, short-λ slices down.

**The fixed-Q test** (`fixq_w4.py`) takes, for each λ, the ratio I(Q 0.6–0.9) / I(Q 0.2–0.35).
Both windows are at fixed Q, so the sample's S(Q) cancels identically. Only the angle of the
windows changes with λ, and any λ-trend is an angle × λ artifact. The exit path's
λ-dependence was scanned: T_out = T(λ)^γ · T_ref^(1−γ), with γ = 1 drtsans and γ = 0
λ-independent.

| H2O, fixed-Q λ-trend | γ = 1 (drtsans) | γ = 0.5 | γ = 0 |
|---|---|---|---|
| 2.5 Å band | +0.33 %/Å | +0.15 %/Å | **−0.03 %/Å** |
| 1 Å band | +0.33 %/Å | +0.24 %/Å | +0.15 %/Å |

- **The 2.5 Å band's trend is removed completely; the 1 Å band's is halved.** The 1 Å
  remainder is dominated by the band-edge slices.
- **D2O (T = 0.93) is unchanged by γ,** as expected, because its correction is small.
- **A single constant exit transmission is exactly equivalent to γ = 0.** Its angular shape is
  λ-independent, so a self-flood removes it. Only the λ-dependence can be tested, and it
  should be about zero for water.

![fixed-Q ratio per λ, γ scan, H2O and D2O](assets/water4/w4_fixq.png)

![each self-flooded slice's 25–35° level vs its 3–8° level (fan), drtsans vs λ-independent exit path](assets/water4/w4_fan.png)

## 6. Test 4 — detector efficiency by tube layer and angle (H1)

The detector has two tube layers per 8-pack:
- **Front layer:** tubes at 11.0 mm pitch.
- **Back layer:** 8.2 mm further from the sample and shifted half a pitch, behind the front
  layer's gaps (from the reduction geometry).

A back tube sees most of the beam *through* the front tubes, so its efficiency relative to the
front layer depends on λ (Water 3 §8: ±1.5 % between the 1 Å and 2.5 Å floods). Δ confirms it
per pixel. At 25°, H2O's back-layer pixels read +5 % (2.64 Å) and +12 % (1.17 Å) relative to
their λ-average, against −2.4 to −2.7 % for the front layer.

But a physical model (`model_w4.py`: 3He absorption ∝ λ, the real tube positions, chords
lengthened by the vertical angle, shadowing by the front tubes; tube radius R and pressure P
fitted to the back/front and vertical/horizontal contrasts) **did not describe it**. The best
fits sit at the edge of the grid (R = 3.5 mm, P = 2–4 atm), and at 2.5 Å it fits worse than no
model at all. The effect is real but not yet understood.

**It does not matter for I(Q):** every Q ring averages both layers equally, and the final
H2O curves are at the counting-statistics level without it. It would matter for 2D,
sector or per-pixel work.

## 7. What is left above ~0.9 Å⁻¹ is water's own S(Q) (H4)

Water's scattering is about 95 % incoherent, but about 4.6 % is coherent: 7.7 b of 168 b per
molecule. That coherent part has H2O's intermolecular structure, peaking near 2 Å⁻¹; D2O,
mostly coherent, shows the same peak very strongly.

With the fixes, the 1 Å and 2.5 Å bands show the **same −0.4 % dip at Q 1.0–1.3 Å⁻¹**. The
1 Å band sees it at about 12–20° and the 2.5 Å band at about 25–35°. Same Q, different angles,
same deviation: it is the sample. The 1 Å band then rises +1–2 % toward the 2 Å⁻¹ peak. This
is physics, and a reduction should keep it.

(The self-flood itself absorbs part of that structure at the high-angle pixels. Any water
flood at 1.3 m carries water's S(Q) at the ±1 % level beyond about 25°.)

![H2O in both bands: default vs final recipe](assets/water4/w4_final_bands.png)

## 8. Results — recipes through drtsans's own binning

All are self-flooded H2O (and D2O with the same H2O flood), incoh fit on unless stated.
"Edges out" means 3 λ bins removed at each end (`tail_w4.py --crop 3`); P1 uses the drtsans
TOF cuts instead.

| recipe | H2O 1 Å: Q 0.1–0.9 max / rms / χ²/bin | H2O 2.5 Å: max / rms / χ²/bin | H2O plateau 1 Å / 2.5 Å (cm⁻¹) | H2O slice spread 1 Å / 2.5 Å |
|---|---|---|---|---|
| R0 drtsans default | 0.83 / 0.34 % / 24 | 0.53 / 0.17 % / 12 | 0.86 / 1.55 | 0.82 / 0.43 % |
| R1 multiplicative k(λ) instead of b(λ) | — / 0.15 % (Q 0.07–0.9) | — / 0.12 % | 0.86 / 1.55 | — |
| R5 edges out, b(λ) | 0.41 / 0.13 % / 10 | 0.34 / 0.11 % / 8.7 | 2.15 / 2.36 | — |
| **P1 production: cutTOF 1650 / 3150 µs** | **0.33 / 0.11 % / 9.2** | **0.41 / 0.12 % / 9.2** | 2.08 / 2.34 | 0.34 / 0.26 % |
| **R3b edges out + γ = 0, b(λ)** | **0.36 / 0.11 % / 4.3** | **0.31 / 0.08 % / 2.3** | 2.25 / 2.46 | **0.31 / 0.21 %** |
| R3 edges out + γ = 0, k(λ) from H2O | 0.48 / 0.14 % (Q 0.07–0.9) | 0.39 / 0.10 % | 2.25 / 2.46 | — |

The per-bin counting error is 0.05 %. R3b is within 1.5–2 × of it.

**Independent test — D2O** (reduced with the H2O flood; not self-referential):

| recipe | D2O slice spread 1 Å / 2.5 Å | D2O I(1.0)/plateau, 1 Å vs 2.5 Å band | D2O plateau 1 Å / 2.5 Å (cm⁻¹) |
|---|---|---|---|
| R0 default | 3.55 / 1.50 % | 1.134 vs 1.071 (bands differ 6 %) | 0.067 / 0.117 |
| P1 production | 1.52 / 0.91 % | 1.057 vs 1.055 | 0.164 / 0.180 |
| R3b | 1.47 / 0.95 % | **1.054 vs 1.051** | 0.165 / 0.184 |

With the fixes, the two bands' D2O agree to 0.3 % at 1 Å⁻¹, where they differed by 6 %.

P1 alone leaves the exit-path effect at high Q: in the 2.5 Å band its I(Q) dips to about −1 % above 1 Å⁻¹, where only the short-λ slices contribute. R3b does not (headline figure).

![combined I(Q) per recipe, H2O and D2O, both bands](assets/water4/w4_final_iq.png)

![I(Q, λ) slices: drtsans default vs final recipe](assets/water4/w4_final_iqlambda.png)

**Why the final recipe keeps drtsans's additive b(λ) rather than a multiplicative k(λ).**
Normalising each slice by water's k(λ) (drtsans's elastic-reference normalisation, with H2O
as the reference) flattens H2O just as well. But applied to D2O, the slices **do not align**:
the short-λ slices sit 5–10 % low. Water's λ-dependence is *water's own*: its apparent
cross-section grows with λ because of inelastic scattering. It is not an instrument
normalisation, so it must not be transferred to other samples. With the band edges out, the
b(λ) fit no longer does harm.

![D2O normalised with water's k(λ): the slices do not align](assets/water4/w4_d2o_waterk.png)

## 9. What to change

- **Now, configuration only:**
  - Widen the TOF edge cuts at 1.3 m (**`cutTOFmin` 1650, `cutTOFmax` 3150 µs** tested here;
    check other configurations).
  - Subtract the blocked beam in both the flood and the reduction (Water 3 §9).

  Self-flooded H2O goes from 0.34 / 0.17 % rms to 0.11 / 0.12 % rms, the D2O slice spread
  halves, and the incoh-fit absolute level is no longer set by a band-edge slice.
- **drtsans, to raise with the developers:**
  - **θ-dependent transmission correction:** an option for the exit-path transmission of
    strongly inelastic samples (water), e.g. λ-independent. Worth another 2–4 × in χ² here.
  - **`selectMinIncoh`:** the minimum-b slice is almost always the band edge. A reference
    chosen away from the edges (or excluding them) avoids the amplification even when the TOF
    cuts are left at their defaults.
- **Not a problem for I(Q):** tube-layer (front/back) efficiency; the flood's λ-independence
  along each tube.
- **Physics, keep it:** water's S(Q) above about 0.9 Å⁻¹ (±1–2 %).

**Provenance.** 2026-09-25, drtsans `1.34.0`, `2026B_mp/reduction/water3/`:
- **Reductions:**
  - `reduce_w3.py` gained `--samples=` and `--cuttof=`.
  - PMMA at 1.3 m, case D (`reduce_w3.py waterbsbb[1A] <cfg> --bb --samples=PMMA`).
  - P1: `reduce_w3.py waterbsbb[1A] <cfg> --bb --samples=H2O,D2O --cuttof=1650,3150` →
    `reduced_*_bb_cut1650-3150_incoh*`.
- **`water4/` scripts:**
  - `tail_w4.py`: drtsans's post-processing tail, bit-exact.
  - `diag_w4.py`: Δ maps and cuts.
  - `model_w4.py`: detector model and fit (`w4_model.json`, `logs/model_fit.log`).
  - `amp_w4.py`: b(λ) amplification.
  - `fan_w4.py`, `fixq_w4.py`: the θ-correction exit path.
  - `build_corr_w4.py`, `run_tail_w4.sh`, `run_tail_w4b.sh`: recipes R0–R5 in `out/`.
  - `final_w4.py`, `hero_w4.py`: figures, `w4_final.json`, `w4_flatness.json`,
    `w4_production.json`.
