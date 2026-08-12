# Attenuation for transmission (monochromatic mode)

Transmission measurements record the **direct beam** through the sample, which is
intense enough to saturate and distort the detector. In monochromatic mode the
beam is attenuated by the choice of **slit 1** (source aperture): from the heavily
attenuating **d25Cd** (25 mm aperture behind cadmium) up through **d5, d10, d15,
d20, d25** (progressively larger openings → progressively higher count rate).

W. Heller measured the resulting **detector count rate (counts per second)** for
each slit at every wavelength and monochromatic spread (dL/L). The goal is to pick
the slit that gives the **highest count rate** (best statistics) while staying
**below the ~20 k cps distortion onset** — so a transmission is neither
noise-limited nor detector-distorted.

> *"Clear signal distortion seems to creep in around 20 k CPS, but that does not
> mean that 10 k–20 k CPS do not cause some distortion."* — W. Heller

- **nm** = not measured or not measurable.
- **/dis** = distorted (count rate at/above the distortion threshold — avoid).
- **Recommended slit** = the largest measured, non-distorted rate that stays
  ≤ 20 k cps (bold cell). Where the highest available option is only a few hundred
  cps, that is genuinely the best choice — a larger slit would distort.

## Count rate (cps) by slit, with recommended choice

<!-- ATTEN_TABLE -->

## Reading the recommendations

- **Short wavelengths at narrow spread** (e.g. 2.5 Å / 5 %) tolerate a large open
  slit (d20) because the beam is already spread thin; as the spread widens the beam
  intensifies and the recommended slit closes down (d20 → d5 → d25Cd at 2.5 Å).
- **Across most of 2.5–8 Å**, the practical choice is **d5 at 5 % spread** and
  **d25Cd at 10–15 %** — the d5 slit distorts (>20 k cps) once the spread reaches
  10 %, so the cadmium slit becomes the only safe option and rates drop to a few
  hundred cps (long transmission counts needed).
- **Long wavelengths** (10–15 Å) are low-flux enough that the **larger open slits
  (d10–d20)** are back in play and give the highest clean rates.
- **1 Å** is barely measurable — only the largest slit (d25) registers anything,
  and only at ≥ 10 % spread.

Source: `2026B_mp/attenuation_for_trans.xlsx` (W. Heller). This tab is regenerated
from that spreadsheet by `doc/generate.py`.
