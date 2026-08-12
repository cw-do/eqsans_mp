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

As a rule of thumb the recommended slit **closes down (fewer counts) as the spread
widens**, since a wider band lets more of the beam through; and it **opens back up
at long wavelength**, where the incident flux is lower. Where the best available
option is only a few hundred cps, that is genuinely the safest choice — a larger
slit would distort — and the transmission simply needs a longer count.

The count-rate table below is **specific to the selected cycle** (generated from
that cycle's own `attenuation_for_trans.xlsx` by `doc/generate.py`). It is measured
per cycle and may not be repeated every cycle.
