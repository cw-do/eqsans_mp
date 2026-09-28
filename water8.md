# Water 8 — where the banjo cell's structure sits, vs PMMA

**Date:** 2026-09-28 · **drtsans:** stable `1.34.0` · **data:** 1.3 m, 1 Å band (IPTS-37618, 2026-09-23
block): empty banjo cell S 188962 / T 188954, thin PMMA S 188965 / T 188957, PeltierWindow background
S 188961 / T 188953 · **scripts:** `2026B_mp/reduction/water3/summary/banjo_w8.py`, `reduce_w3.py`
(set `recipe`, `--winbkg`), `water4/tail_w4.py`

Two of our flood choices carry the sample cell's or sheet's own structure into the flood: a **thin
PMMA** flood carries PMMA's, and a **water-in-banjo** flood carries the empty banjo cell's (which is
why Water 3 subtracts the banjo). This page just shows **where each one's structure sits in Q**, so it's
clear they don't land in the same place.

The 1.3 m **1 Å band** is the one to use: it reaches Q ≈ 2.5 Å⁻¹, far enough to see the banjo cell's
peak. Longer bands and larger distances stop below ~1.3 Å⁻¹ and never reach it.

## The comparison

Empty banjo and PMMA reduced **identically**: recipe H2O flood (flat, banjo already removed),
PeltierWindow background (both are bare — a cell and a sheet), blocked beam, cutTOF 1650/3150, incoh fit
on, 24 px tube ends masked in the data. Each curve is normalised to its own value at Q 0.35–0.5 Å⁻¹ to
compare shape (the absolute levels differ — PMMA scatters far more, being hydrogen-rich).

![Banjo cell vs PMMA structure](assets/water8/w8_banjo_pmma.png)

*Fig. 1 — Left: combined I(Q) on an **absolute** log scale (as reduced) — PMMA is ~10× the banjo
everywhere. Middle and right: single I(Q, λ) slices, each normalised to its own value at Q 0.35–0.5 Å⁻¹
to show that the peak stays at one Q while the wavelength (and therefore the detector angle) moves.*

## The banjo scatters much less than PMMA (absolute)

In absolute intensity the banjo cell is far weaker than PMMA, everywhere:

| Q (Å⁻¹) | 0.4 | 0.7 | 1.0 | 1.24 | 1.54 |
|---|---|---|---|---|---|
| **PMMA** I(Q) (1/cm) | 1.46 | 1.46 | 1.50 | 1.59 | 1.50 |
| **banjo** I(Q) (1/cm) | 0.072 | 0.082 | 0.099 | 0.14 | 0.23 |

So PMMA scatters 7–20× more than the empty banjo — as expected, since PMMA is hydrogen-rich. What makes
the banjo's silica peak *look* dominant is only the shape normalisation in the slice panels: quartz is a
**coherent** scatterer (low flat background, sharp peak → ×3 relative), while PMMA's ~1.5 level is mostly
flat **incoherent** background from its hydrogen, with a small coherent halo on top (only +10 % relative).
Weak-but-sharp vs strong-but-broad. The reduction of both is on the same absolute scale; only the middle
and right panels are divided by their own baseline to compare shape.

## What it shows

| feature | Q (Å⁻¹) | as 2θ, 1 Å band | height above baseline | what it is |
|---|---|---|---|---|
| PMMA inter-chain peak | ≈ 0.6 | 8–27° | +0.6 % | polymer chain–chain spacing (Water summary §5b) |
| PMMA amorphous halo | **1.24** | 17–31° | +10 % | PMMA's main amorphous peak |
| banjo cell peak | **1.54** | 21–32° | ×3 (strong) | fused-silica **first sharp diffraction peak** |

- **The banjo cell is fused silica.** Its one strong peak at Q = 1.54 Å⁻¹ is the classic first sharp
  diffraction peak of vitreous SiO₂ (literature ≈ 1.5 Å⁻¹ — the intermediate-range Si–O–Si network
  order). It's a factor of ~3, much stronger than PMMA's halo.
- **Both are real structure.** Each peak sits at the **same Q in every wavelength slice**, even though
  each slice measures that Q at a different angle (banjo: 2θ 21–32°; PMMA: 17–31°). A detector or flood
  artifact would track the angle, not Q. (Same test as the summary §5.)
- **They don't overlap.** Banjo at 1.54, PMMA's halo at 1.24, PMMA's weak peak at 0.6 — three different
  places. So the banjo's structure cannot hide inside PMMA's, nor vice versa.

## Did the banjo create the ~0.7 Å⁻¹ feature in PMMA? No

The reason for this comparison was to check whether the banjo cell could be behind PMMA's weak peak at
0.6 Å⁻¹ / dip at 0.78 Å⁻¹ (Water summary §5b). It cannot, for three independent reasons:

1. **PMMA was not in the banjo.** The PMMA sheet (188965) is free-standing; its background is the
   PeltierWindow (188961), not the banjo. The banjo cell was never in the PMMA beam path, so its
   scattering cannot enter the PMMA measurement.
2. **The banjo has no feature at 0.7.** Its I(Q) rises smoothly and monotonically through that region
   (0.072 → 0.093 over Q 0.45–0.91) — no bump, no peak. Its only peak is the 1.54 Å⁻¹ silica FSDP.
3. **Not through the flood either.** The recipe flood is water-in-banjo with the banjo subtracted; any
   residual banjo feature would land at 1.54 Å⁻¹, not 0.7.

Wrong beam path *and* wrong Q. The PMMA 0.6 / 0.78 Å⁻¹ features are PMMA's own inter-chain structure.

## Why it matters for floods

- A **PMMA flood** stamps the 1.24 Å⁻¹ halo (and the 0.6 peak) onto every reduced curve — smeared over
  the flood's wavelength spread, so it lands across a range of angles. That's what left structure in
  high-Q data (Water summary §5).
- A **water-in-banjo flood** carries the banjo's 1.54 Å⁻¹ silica peak. That is exactly why Water 3
  subtracts the empty banjo: after subtraction the flood is water only — flat, no 1.54 feature.
- Because the two features are at **different Q**, the choice of flood shows up at different places in
  the data, and neither is hidden by the other. Water (with the banjo subtracted) is the clean flood:
  its own scattering is featureless incoherent, and the cell's 1.54 peak is removed.
- The banjo silica peak at 1.54 Å⁻¹ is **out of range** for the longer bands (2.5 Å / 6 Å) and larger
  distances, which stop below ~1.3 Å⁻¹. But its **leading edge** (the rise from ~0.8 Å⁻¹, visible in
  Fig. 1) still reaches into the SANS range, so subtracting the empty banjo matters even when the peak
  itself is off the detector.

## Bottom line

The empty banjo (quartz) cell has a strong first sharp diffraction peak at **Q ≈ 1.54 Å⁻¹**; thin PMMA
has its amorphous halo at **1.24 Å⁻¹** and a weak inter-chain peak at **0.6 Å⁻¹**. Different Q, both
real. This is one more reason the recommended flood is **water with the banjo subtracted**: it removes
the only structured contribution (the silica cell), leaving flat incoherent scattering.
