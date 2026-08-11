# Monochromatic-beam reduction

The 6-chopper upgrade (see the **Choppers** tab) lets EQSANS run a *monochromatic*
beam — a single narrow wavelength band instead of the broad TOF spectrum. In
2026B we measured a spread series at 4 m / 2.5 Å (runs 186204–186248), varying the
band width **dl/l = 0.03, 0.05, 0.10, 0.15** with everything else fixed.

**All 16 reductions initially failed and produced no usable data.** This page
documents why — three issues in how drtsans handles a monochromatic run, two of
which crash it outright — and shows a recipe that recovers the data, demonstrated
on AgBe.

## Symptoms

Every spread failed, but with three *different* errors, which was the first clue:

| spread | error raised by drtsans |
|---|---|
| dl/l = 0.03 | `IndexError: list index out of range` (at file load) |
| dl/l = 0.05 | `TransmissionNanError: Transmission at zero-angle is NaN` |
| dl/l = 0.10, 0.15 | `Levenberg-Marquardt … 1 data points, 2 fitting parameters` |

All three trace back to how drtsans reconstructs the transmitted wavelength band
from the chopper geometry, and how it then fits the sample transmission.

## Cause 1 — the reduction uses the wrong chopper phase

The transmitted wavelength band is set by the chopper phases. drtsans stores
several sets of EQSANS chopper phases (in `EQSANS_chopper_configurations.json`)
and picks one automatically per run. For these runs it picked a set whose phases
**do not match the chopper phase the instrument was actually running**, so the
reconstructed band comes out wrong.

Reproducing drtsans' own band math with each stored phase set (figure produced by
our own code — see *How the figures were made*):

![Transmitted band per spread: wrong vs correct chopper phase](assets/monowl/monowl_bands.png)

Only one phase set is physically right: the **green** bars — bands centred
**exactly at 2.50 Å with width = (dl/l) × 2.50** for every spread, i.e. what the
instrument was set to. **This set agrees with the most recently known (correct)
chopper phase.** It happens to be indexed in the drtsans table under the date-tag
`20260101`; we don't know why it carries that date, and *the date is not the
point* — what matters is that these are the correct phases and drtsans is not
applying them. (The date is only how drtsans looks up a set.)

The set drtsans applied instead is the **blue** bars. For the three wider spreads
a band still forms but is **shifted off-centre to ~2.57 Å** (nominal 2.50) and is
narrower than the true spread — so those runs are reduced at the wrong wavelength
(and dl/l=0.05 is so narrow the transmission comes out NaN). For the narrowest
spread, **dl/l=0.03, no band forms at all** — that is the blue *"EMPTY"* row in
the figure above, and it is the `IndexError`.

Why dl/l=0.03 has no band: each chopper still transmits something, but with the
wrong phases the six openings share no common wavelength — chopper 3b closes at
2.561 Å *before* chopper 1b opens at 2.672 Å. The band is the intersection of all
six, and here it is empty. In the figure below the red-shaded strip is that
**gap between openings (2.561–2.672 Å) — it is not a band**; for this spread there
is simply no wavelength open on all six choppers:

![dl/l=0.03: the six chopper openings share no common wavelength](assets/monowl/monowl_intersection.png)

**Fix:** make the reduction apply the correct chopper phases — the ones that
reproduce the 2.50 Å bands (green above). In drtsans that means the runs must pick
up the `20260101`-set values; add or correct a table entry so the current cycle's
runs do. This is an instrument-config change to coordinate with the SANS/drtsans
team, and it is **required just to load** the dl/l ≤ 0.05 runs (they `IndexError`
before any transmission or binning happens).

## Cause 2 — transmission is force-fit as wavelength-dependent

Even with the band fixed, drtsans computes the sample transmission by **fitting a
2-parameter line** `T(λ) = a·λ + b` across the band's wavelength bins
(`process_transmission` uses a hardcoded `LinearBackground`). A monochromatic band
spans only 0–2 wavelength bins, so the fit has too few points and dies:
`1 data points, 2 fitting parameters`.

A monochromatic transmission is **a single number**, not a function of
wavelength. drtsans already supports this — `calculate_transmission` with an empty
fit function returns the raw single value — but it is not exposed as a reduction
option. Two ways to get it:

- Pass a **fixed transmission value** per sample (a number ≤ 1, exactly like the
  blocked-beam 0.9 convention). Compute each sample's transmission once
  (drtsans prints `Average zero angle transmission = …`) and feed it back. No
  code change; works in the normal reduction path.
- Or force the empty fit function in `process_transmission` (an in-process patch).

## Cause 3 — the reduction should use a single wavelength bin

Monochromatic mode exists precisely to *avoid* combining wavelengths: with a
broad beam, the final I(Q) is built by normalising each wavelength slice (by the
wavelength-dependent flux and sensitivity) and then combining them — and any
imperfection in that normalisation, plus residual inelastic scattering, leaves a
wavelength-dependent intensity. A monochromatic run should therefore be reduced
as **one wavelength bin spanning the whole band**, so there is a single
normalisation and nothing is averaged across wavelength.

drtsans supports this directly: `convert_to_wavelength` has a **monochromatic
mode** that, when a run's `monochromatic` sample log is set, overrides the bin
width to `w_max − w_min` — one bin spanning the transmitted band — and a
downstream guard (`bypass_correction_for_single_wavelength_bin`) then skips the
elastic/inelastic wavelength corrections, which are meaningless for one bin. Our
runs simply **don't have that log set**, so drtsans binned them at the default
0.1 Å (2–3 bins across the band) and applied the per-wavelength machinery.

Equivalently, without the log, setting the reduction's **wavelength step equal to
the band width** produces the same single bin (verified: dl/l=0.10, band ≈0.25 Å
→ step ≥ 0.2 Å gives exactly one bin). What must be avoided is a step *much*
larger than the band (e.g. 2 Å): with `FullBinsOnly`, no full bin fits inside the
band, the frame comes out empty, and I(Q) binning dies with `zero-size array to
reduction operation minimum`. So the rule is *step ≈ band width*, not "as large
as possible."

## How we fixed it for this test (temporary)

The fix used to prove recovery is a **temporary, local workaround — nothing in the
shared drtsans install or its configuration was modified.** In the demonstration
script (`reduce_agbe_mono.py`) we, at runtime and in-memory only:

1. **Forced the correct chopper phase** — monkeypatched
   `EQSANSDiskChopperSet.get_chopper_configuration` to use the `20260101` phase
   set instead of the auto-selected one.
2. **Forced single-value transmission** — monkeypatched `calculate_transmission`
   to use an empty fit function (raw single value, no `a·λ+b` fit).
3. **Forced a single wavelength bin** — tagged each workspace with the
   `monochromatic` sample log (and set the wavelength step to the band width), so
   drtsans bins the whole band into one slice and bypasses the per-wavelength
   corrections.
4. Ran the reduction **in-process** (`reduceNow(..., debug=True)`) so the patches
   actually apply (the default path spawns a fresh subprocess that would not see
   them).

These patches live only inside the demonstration script and vanish when it exits.
They are enough to **prove the cause and recover data now**, but they are not a
setup anyone should run production reductions through.

## Result — AgBe across the four spreads

AgBe (silver behenate) is the sharpest test of a monochromatic reduction: it has
evenly spaced diffraction rings (Q = 0.1076, 0.2153, 0.3229 Å⁻¹), so a correct
reduction must place peaks *exactly* there. Reducing all four spreads with the
recipe above — correct chopper phase, single-value transmission, and a single
band-spanning bin (drtsans monochromatic mode engaged) — gives:

![AgBe I(Q) across the four spreads](assets/monowl/monowl_agbe.png)

- **dl/l = 0.10 and 0.15 are textbook AgBe** — three orders landing right on the
  reference positions (0.108 / 0.216 / 0.323 Å⁻¹, dotted lines). Peaks at the
  correct Q means the wavelength is correct: the chopper-phase fix worked.
- **Intensity scales with the band width.** A wider band passes more neutrons, so
  the pattern is stronger and cleaner — peak I(Q) ≈ 1.0, 0.52, 0.05 for
  dl/l = 0.15, 0.10, 0.05. This is the resolution-vs-flux trade the spread setting
  controls.
- **dl/l = 0.03 is flux-starved.** The razor-thin band passes so few neutrons that
  only a handful of Q points survive and the peak is lost in noise — the narrowest
  spread trades almost all intensity for resolution.
- The peak-normalised panel (right) shows the peaks are consistent in position and
  shape once there are enough counts; the extra sharpening from a narrower spread
  is modest here because at 4 m / 2.5 Å the detector geometry, not the wavelength
  spread, dominates the Q-resolution.

(The same recipe also recovers porasil — a smooth SANS curve — for the wider
spreads; see `reduce_mono_recipe.py`.)

## Suggested permanent fixes for drtsans

The temporary patches above point to real drtsans issues that should be fixed
upstream so monochromatic data reduces on the normal path:

1. **Chopper phase (a config bug — fix required).** Make the current cycle's runs
   pick up the correct (`20260101`-style) chopper phases — add or correct an entry
   in `EQSANS_chopper_configurations.json` so the applied phases match the
   instrument. This is an instrument-configuration change to coordinate with the
   SANS/drtsans team; it is **required just to load** the dl/l ≤ 0.05 runs (there
   is no no-code workaround — the phases must be right before the run will load).

2. **Single wavelength bin (engage the built-in monochromatic mode).** drtsans
   already makes one band-spanning bin and bypasses the per-wavelength corrections
   when a run's `monochromatic` sample log is set — so the run must carry that log
   (from the DAS, or added during reduction). *Interim, no-code option:* set the
   reduction's wavelength step equal to the transmitted band width, which yields
   the same single bin.

3. **Transmission fitting (a behaviour gap — enhancement).** drtsans should use a
   single-value transmission for monochromatic runs instead of the 2-parameter
   `a·λ+b` fit — e.g. auto-detect the monochromatic case, or expose the existing
   empty-fit-function path as an option. *Interim, no-code option:* pass a
   **fixed transmission value** per sample (a number ≤ 1, like the blocked-beam
   0.9 convention), which already works on the normal path once the run loads.

## How the figures were made

The band figures are **our own code**, not drtsans output:
`2026B_mp/reduction/mono_diagnosis/diagnose_chopper.py` loads each run's logged
chopper speeds/phases and reproduces drtsans' own transmission-band math for each
stored phase set (writing `chopper_diagnosis.md`); those band numbers are drawn by
`doc/monowl_assets/make_monowl_plots.py`. The AgBe and I(Q) curves are read
directly from the reduced `_Iq.dat` files produced by `reduce_agbe_mono.py` /
`reduce_mono_recipe.py`.

Full diagnosis, scripts and proof:
`2026B_mp/reduction/mono_diagnosis/` (`diagnose_chopper.py`,
`chopper_diagnosis.md`, `reduce_agbe_mono.py`, `reduce_mono_recipe.py`,
`DIAGNOSIS.md`).
