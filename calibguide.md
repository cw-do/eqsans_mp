# EQSANS calibration guide — how to calibrate a cycle, step by step

**Audience:** the next instrument scientist or AI agent who has to produce a cycle's calibration from
scratch · **Scope:** detector geometry + TOF timing (AgBe), dark current, sensitivity (flood), flux
spectrum, detector mask, standard-sample reduction with the B1 absolute scale, and publishing to this
site · **Project root:** `/SNS/EQSANS/shared/NeXusFiles/EQSANS` (one folder per cycle, `<cycle>_mp/`, e.g.
`2027A_mp/`). Every step also has a `/eqsans-*` Claude Code skill (named at each step) that does exactly
this.

## What a cycle produces, and in what order

Each cycle delivers four calibration files plus verification:

1. **Dark current** — a raw `Darkcurrent` NeXus file (used as-is)
2. **Flux spectrum** — `bl6_flux_<cycle>_<tag>_rebinned.txt`
3. **Sensitivity (flood)** — one `Sensitivity_patched_*.nxs` per detector distance
4. **AgBe calibration** — detector geometry + TOF timing (`scale_y`, `scale_all`, `detoffset`,
   `samoffset`, `scalecomp`)

then a **mask** and a **standard-sample reduction** (with the **B1 absolute scale**) verify it, and the
**summary page** publishes it.

**The order matters, because of one circular dependency:** AgBe calibration *consumes* the dark current,
flux and a flood; but the final flood must be built with the geometry AgBe produces. This is resolved by
building the flood **twice** — a first "nominal" pass (no geometry) so AgBe has a flood to use, then a
rebuild with the AgBe geometry. The flood's smooth angular factor shifts AgBe peak *positions* < 0.5 %, so
the AgBe numbers do not need redoing. **All of that lives in one section (step 3 below); its two passes
straddle the AgBe step (4).**

```
0. scaffold the cycle folder
1. dark current  ─┐
2. flux  ─────────┤   (independent; any order)
3. sensitivity ───┘   PASS 1: nominal flood (no geometry yet)
4. AgBe calibration   (uses dark + flux + the nominal flood)  →  calibration_report.txt
3. sensitivity        PASS 2: rebuild the flood with the AgBe geometry, then QC   ← back to step 3
5. mask
6. reduce standards (porsil first)  +  B1 absolute scale
7. standards report
8. publish  (/update-mp-page)
```

**Environment.** `drtsans` is the Mantid/drtsans shell. `drtsans --classic <script.py> <args>` runs a
script *with* its command-line flags; **bare `drtsans <script.py>` starts ipython and silently drops the
flags** — so always use `--classic` when you pass arguments. `drtsans --dev` selects the newer `sans_dev`
build; `sans_qa` (the default sensitivity builder's environment) is reached with
`pixi run --frozen --manifest-path /usr/local/pixi/sans_qa <cmd>`. Pure-python helper scripts
(`0_find_runs.py`, `generate.py`, the report tools) run under plain `python3`.

**Finding runs.** Every calibration run is identified by its **title**, not its position in a block
(`T-` = transmission/beam-centre, `S-` = scattering; `NoWindow`, `banjo`, `agbe`, `blockedbeam`,
`PeltierWindow`, `Darkcurrent`, `T-flux`). List a cycle's IPTS with
`python3 tools/flux/0_find_runs.py <IPTS> --list` or the `/oncat-catalog` skill. **Always verify the
logged distance/wavelength against the title** — a block labelled one wavelength but taken at another is a
real, silent trap (it happened in 2026B at 1.3 m).

---

## 0. Scaffold the cycle folder

**Script:** `tools/new_cycle.py`

```bash
cd /SNS/EQSANS/shared/NeXusFiles/EQSANS
python3 tools/new_cycle.py 2027A --tag jan
```

Creates `2027A_mp/` with the sensitivity scripts (`prepare_sensitivity.py`, `check_sensitivity.py`,
`plot_flood.py`), `agbe_calibration/agbe_reducenfit.py`, and a self-contained `flux/` folder, then prints
the ordered next steps. (`--tag` is the flux filename label. Each toolkit also has its own
`setup_cycle_*.py` if you want to scaffold one piece.) It does **not** copy the dark current or run
anything.

---

## 1. Dark current

**Purpose:** the detector's electronic background, subtracted from every reduction. **Script:**
`tools/darkcurrent/copy_darkcurrent.py` · **Skill:** `/eqsans-darkcurrent`

```bash
python3 tools/darkcurrent/copy_darkcurrent.py <IPTS>            # list candidates (no copy)
python3 tools/darkcurrent/copy_darkcurrent.py <IPTS> 2027A      # copy newest into 2027A_mp/, verified
```

**What to choose:** the most recent run titled `Darkcurrent` — the **long (~6 h) 4 m** one (there is
sometimes a short one too; force a specific run with `--run <number>`). **Output:**
`2027A_mp/EQSANS_<run>.nxs.h5` (multi-GB; the script checks the copied size against the source).

---

## 2. Flux spectrum

**Purpose:** the beam flux vs wavelength that reduction normalises by. **Scripts:** `<cycle>_mp/flux/`
pipeline · **Skill:** `/eqsans-flux`

```bash
cd 2027A_mp/flux
python3 0_find_runs.py <IPTS> --list            # confirm the T-flux campaign, then:
python3 0_find_runs.py <IPTS> <first>-<last>     # write the run manifest (read the warnings)
python3 run_flux.py <IPTS>                       # full pipeline: find→reduce→stitch→rebin→plot
```

**What to edit:** normally nothing — `setup_cycle_flux.py` (run by `new_cycle.py`) filled
`flux_config.json` with the cycle + tag and symlinked the mask. Just confirm the run range in step 0
(auto-detection picks the newest `T-flux` block; a partial/repeated campaign is where it goes wrong). Do
**not** hand-edit `flux_runs.json` (re-run step 0) or change `wl_bin_width` (0.1 — it sets the absolute
scale). Steps 1–2 of the pipeline need `drtsans`; `run_flux.py` dispatches them. Resume with
`run_flux.py --from 2`.

**Check:** `python3 4_plot.py --all --save flux_summary.png` and compare shape/magnitude with the previous
cycle (`head -4 ../../<prev>_mp/bl6_flux_*_rebinned.txt`). Spikes at 10.93 / 14.55 / 18.18 Å and band-edge
partial bins are known, not bugs.

**Deliver:** copy the result up to the cycle root (where reduction and the site read it):

```bash
cp bl6_flux_2027A_jan_rebinned.txt ../
```

(Ask before copying a flux file into `/SNS/EQSANS/shared/instrument_configuration/` — that changes
reduction for every user.)

---

## 3. Sensitivity (flood) — everything in one place

**Purpose:** the per-pixel relative-efficiency (flood) map. **Skill:** `/eqsans-sensitivity`

**Recommended flood sample:** H2O 1 mm in the banjo cell (flat incoherent, no structure near 1 Å⁻¹ as
thin PMMA has), long-λ band. **The recipe is the same whichever tool builds it:** reduction (AgBe)
geometry + computed solid angle, θ-dependent self-absorption with the flood's own transmission, empty
banjo subtracted, blocked beam (same band) subtracted, TOF cuts 1650 / 3150 µs, 15 px tube-end mask.

**Built in two passes, around AgBe (step 4):**

- **Pass 1 — nominal** (do it now, before AgBe): build the flood with **no** geometry. Its only job is to
  give AgBe a flood to apply.
- **Pass 2 — rebuild** (after step 4): rebuild with the geometry from
  `agbe_calibration/*/calibration_report.txt` (`samoffset`, `detoffset`, `scalecomp`). This is the flood
  reduction actually uses — without it the solid angle divided out of the flood and out of each sample do
  not cancel (+4.9 % at 20° / +11 % at 30° at 1.3 m).

### 3a. Default method — drtsans `prepare_sensitivities_eqsans` (TOML)

The drtsans team's first-class EQSANS sensitivity builder (environment **`sans_qa`**, drtsans ≥ 1.36). It
takes a small TOML and does the whole recipe, computing the transmission correction as **T(λ, θ)** from
the transmission runs. **This is the method to use.** Full documentation and the validation against the
old script (they agree to 0.05–0.07 %) are on the **drtsans sensitivity** tab.

```bash
pixi run --frozen --manifest-path /usr/local/pixi/sans_qa \
    prepare_sensitivities_eqsans  <config>.toml  /path/out.nxs        # output path is a CLI arg, not a TOML key
```

**The TOML** (one per distance/band). Example — 1.3 m / 2.5 Å H2O, with the pass-2 (AgBe) geometry:

```toml
FLOOD_RUNS = [189933]                 # S-H2O-in-banjo (the flood)
DIRECT_BEAM_RUNS = [189924]           # beam-centre run (T-empty NoWindow)
BLOCKED_BEAM_RUNS = 189936            # S-blocked beam, same band (also removes dark)
EMPTY_CELL_RUNS = 189932              # S-empty banjo cell (subtracted)
TRANSMISSION_FLOOD_RUNS = 189926      # T-H2O-in-banjo      } all three together
TRANSMISSION_EMPTY_CELL_RUNS = 189925 # T-empty banjo       } or none; needs EMPTY_CELL_RUNS
TRANSMISSION_REFERENCE_RUNS = 189924  # T-empty beam (reference)
SAMPLE_OFFSET = 285.0                 # mm   } from agbe_calibration/.../calibration_report.txt
DETECTOR_OFFSET = 66.714              # mm   }  (PASS 2 only — see below)
SCALE_COMPONENTS = { detector1 = [1.004124, 1.057996, 1.0] }
LOW_TOF_CLIP = 1650.0                 # µs frame-edge cut (fast end)
HIGH_TOF_CLIP = 3150.0                # µs frame-edge cut (slow end)
MASKED_PIXELS = "1-15,242-256"        # tube ends (15 px each)
MASK_BEAM_CENTER_RADIUS = 40.0        # mm
SOLID_ANGLE_CORRECTION = true
MIN_THRESHOLD = 0.1                   # pixels outside [0.1, 3.0] are masked
MAX_THRESHOLD = 3.0
```

**What to change between cycles:** the seven run numbers (by title — `FLOOD` = S-H2O, `DIRECT_BEAM` =
T-empty NoWindow, `BLOCKED_BEAM` = S-blocked beam, `EMPTY_CELL` = S-banjo, and the three `TRANSMISSION_*` =
T-H2O / T-banjo / T-empty), and the geometry (`SAMPLE_OFFSET`, `DETECTOR_OFFSET`, `SCALE_COMPONENTS`) from
this cycle's AgBe report. The cuts, masks, radius and thresholds are the standard recipe and stay fixed.

- **Pass 1 (nominal):** omit `SCALE_COMPONENTS` and set `SAMPLE_OFFSET = 0.0`, `DETECTOR_OFFSET = 0.0`
  (their defaults) — i.e. no geometry. Build each distance, run AgBe (step 4).
- **Pass 2 (rebuild):** fill `SAMPLE_OFFSET` / `DETECTOR_OFFSET` / `SCALE_COMPONENTS` from
  `calibration_report.txt` and re-run. This is the deployed flood.

Example TOMLs: `2026B_mp/sensitivity_drtsans_qa/*.toml`.

### 3b. Legacy method — `prepare_sensitivity.py` (CONFIGS)

The in-house batch script, still useful for building all distances/bands in one loop and for the
`<flood>.geometry.json` provenance sidecar it writes. It applies the self-absorption with a single
flux-weighted scalar transmission (vs the official method's T(λ, θ)); the two agree to 0.05–0.07 %.

**What to edit:** the `CONFIGS` table at the top of `2027A_mp/prepare_sensitivity.py` — the only block that
changes between cycles. One entry per distance/band; each names its runs:

| `CONFIGS` field | meaning |
|---|---|
| `flood` | the flood S-run (H2O in banjo) |
| `direct` | beam-centre run (T-empty NoWindow) |
| `distance_m`, `sample` | 4.0 / 2.5 / 1.3; sample name for the output filename |
| `transmission` | flood transmission (H2O vs empty banjo), flux-weighted over the cut band; `None` = none |
| `background` | empty-cell S-run (empty banjo), else `None` |
| `blocked_beam` | blocked-beam S-run, same band, else `None` |

```bash
cd 2027A_mp
drtsans --classic prepare_sensitivity.py --list                               # check configured runs
for c in 4m 2o5m 1o3m; do drtsans --classic prepare_sensitivity.py $c --nominal; done   # PASS 1 (before AgBe)
# ... run AgBe (step 4) ...
rm Sensitivity_patched_*.nxs                                                  # drop the nominal floods
for c in 4m 2o5m 1o3m; do drtsans --classic prepare_sensitivity.py $c; done   # PASS 2 (reads AgBe geometry)
```

`--nominal` builds with offsets 0 / no scale components. Without `--nominal` the script reads
`agbe_calibration/*/calibration_report.txt` automatically and refuses to run if it is missing.
`--outdir DIR` writes elsewhere (to compare before replacing).

### 3c. QC (either method)

```bash
cd 2027A_mp && python3 check_sensitivity.py --save sensitivity_qc.png
```

A healthy map has mean ≈ 1 over surviving pixels, a narrow spread, and bad pixels confined to the masked
tube-end bands + the beam-centre hole. The wide, bimodal spread (front tubes shadow back ones) and a
broader 1.3 m map are normal.

---

## 4. AgBe calibration

**Purpose:** detector geometry (`scale_y`, `scale_all`) and TOF timing (`detoffset`) from the silver-
behenate ring series. **Runs last of the four** — it applies the dark, flux and the **pass-1 nominal**
flood from step 3. **Script:** `<cycle>_mp/agbe_calibration/agbe_reducenfit.py` · **Skill:** `/eqsans-agbe`

**What to edit** — the `CONFIGURATION - EDIT THIS SECTION` block at the top:

- `IPTS_NUMBER`, `CYCLE_DIR` (this cycle's `<cycle>_mp` path)
- `DARK_FILE`, `FLUX_FILE`, `FLOOD_FILES` — the files from steps 1–3 (use the **pass-1 nominal** floods)
- `MASK_FILE` — the 4 m mask (default `eqsanstools/mask_4m.nxs` is fine)
- `SAMPLE_OFFSET` — measured at the beamline (e.g. 285 mm)
- the `CONFIG_4M` / `CONFIG_2O5M` / `CONFIG_1O3M` run lists. Each entry is
  `(name, samscatt, samtrans, bkgscatt, bkgtrans, emptybeam)` — **roles assigned by title:**
  `samscatt = S-agbe`, `samtrans = T-agbe`, `bkgscatt = S-banjo`, `bkgtrans = T-banjo`,
  `emptybeam = T-empty NoWindow` (the banjo cell holds the AgBe, so the empty banjo is the background).
- `RUN_STEPS` — `(1,2,3)`: (1) `scale_y` from the isotropic ring, (2) `scale_all` + `detoffset` scan,
  (3) wavelength cross-check. Add `4` (frame-skip) only if the cycle has 30 Hz frame-skip AgBe data
  (recent cycles are all 60 Hz → no step 4).

```bash
cd 2027A_mp/agbe_calibration
drtsans --classic agbe_reducenfit.py
```

**Output:** `agbe_<IPTS>/calibration_report.txt` with the copy-paste reduction values:

```
scalecomp = [scale_all, scale_all*scale_y, 1]
detoffset = ...
samoffset = ...
```

**Check:** the verification table — `q1 ≈ 0.1069`, `q2/q1 ≈ 2.0`, `q3/q1 ≈ 3.0`. Record this cycle's data
notes (mislabelled blocks, missing frame-skip data) in `agbe_calibration/README.md`.

**→ Now go back to step 3 and do PASS 2** (rebuild the flood with this geometry, then QC).

---

## 5. Detector mask

**Purpose:** mask the beam-stop shadow, the low-count top/bottom pixel bands, and dead/hot tubes.
**Script:** `tools/mask/make_mask.py` (runs under the **sansdir** venv python) · **Skill:** `/eqsans-mask`

```bash
SANSDIR=/SNS/EQSANS/shared/script/sansdir
$SANSDIR/.venv/bin/python tools/mask/make_mask.py <run> --ipts <IPTS> --outdir 2027A_mp/masks
```

**What to choose:** a **banjo / flood / empty-cell** run (uniform illumination, so anomalies stand out).
**Always open** `EQSANS_<run>_mask_compare.png` — the red overlay should cover the beam shadow, the
top/bottom edges and any off tubes, and nothing else. Tune with `--beam-scale`, `--beam-pad` (y-pixels),
`--top N --bottom M`, `--tube-sigma` (higher = stricter), `--tubes <id>`, `--no-tubes`/`--no-beam`;
`--no-nxs` re-renders the plot without the slow Mantid write. **Output:** `EQSANS_<run>_mask.nxs` (point
the reduction's `MASK[...]` / `eq._maskfilename` at it) + `_compare.png` + `_mask.params.json`.

---

## 6. Reduce the standard samples + B1 absolute scale

**Purpose:** reduce the cycle's standards (porsil, agbe, blockedbeam, peltierwindow) to verify the
calibration and set the absolute-intensity scale. **Scripts:** `tools/reduce/generate_reduction.py`,
`tools/reduce/find_absscale.py` · **Skills:** `/eqsans-reduce`, `/eqsans-absscale`

```bash
python3 tools/reduce/generate_reduction.py 2027A <IPTS> <first>-<last>   # writes reduction/reduce_standards.py
cd 2027A_mp/reduction
RS_LIST=1 drtsans reduce_standards.py          # review the plan (configs, runs, skips)
drtsans reduce_standards.py                    # reduce all (slow)
RS_ONLY=porsil RS_CONFIG=4m_2.5A drtsans reduce_standards.py   # narrow to one
```

The generated script is wired to this cycle's flood / dark / flux / AgBe geometry and mask. **Review the
CONFIG block** (masks, q bins, absolute scale) before the full run, and **reduce porsil first** to set the
scale. Bare `drtsans` eats CLI flags, so options go through env vars (`RS_LIST`, `RS_ONLY`, `RS_CONFIG`).
Backgrounds: porsil/agbe use the empty banjo; blockedbeam/peltierwindow use none. Blocked beam has no real
transmitted beam → give it a *fixed* transmission (`--fixed-trans blockedbeam=0.9`, regenerate into a new
file, re-reduce just it).

**B1 absolute scale** (porous-silica standard) — run before publishing standards:

```bash
python3 tools/reduce/find_absscale.py 2027A                      # default overlap window q 0.01–0.03
python3 tools/reduce/find_absscale.py 2027A --only 1o3m_2.5A --qmin 0.05 --qmax 0.1   # short-distance configs
```

Writes `reduced/absscale.json` + a fit PNG per config. A short-distance/short-λ config (e.g. 1.3 m 2.5 Å,
q starts ~0.04) has no data in 0.01–0.03 → re-run it with a window both curves cover. A tight spread (a
few %) and factors that cluster across configs mean a good scale.

---

## 7. Standards report

**Purpose:** collect the reduced standards for the site. **Script:** `tools/reduce/report_standards.py` ·
**Skill:** `/eqsans-standards`

```bash
python3 tools/reduce/report_standards.py 2027A <IPTS> <first>-<last>   # -> reduced/standards.json
```

Runs **after** `find_absscale.py` (it folds `absscale.json` into the porsil cards). Matches each reduced
dataset to its run via ONCat for run/counts/duration. For a monochromatic vary-spread series, also run
`python3 tools/reduce/report_varyspread.py 2027A <IPTS> <first>-<last>`.

---

## 8. Publish the summary page

**Purpose:** regenerate and publish this website. **Script:** `doc/generate.py` · **Skill:**
`/update-mp-page`

```bash
DOC=/SNS/EQSANS/shared/NeXusFiles/EQSANS/doc
cd "$DOC" && python3 generate.py --check      # dry scan: does the new cycle's dark/sens/flux/AgBe count look right?
cd "$DOC" && python3 generate.py              # rewrite data.js + assets/
git add -A && git status && git --no-pager diff --cached --stat   # review; NO .nxs/.nxs.h5 should be staged
git commit -m "Update machine-physics summary: <what changed>" && git push
```

`generate.py` scans every `<cycle>_mp/` folder and rebuilds `doc/data.js` + `doc/assets/` (standard-library
only — it never reads the multi-GB NeXus files). **Only `doc/` is a git repo** (→ `cw-do/eqsans_mp`,
published at <https://cw-do.github.io/eqsans_mp/>); the cycle folders and `tools/` are **never** committed
(they hold multi-GB NeXus data). If push fails on authentication, ask the user to push themselves with a
`!` command; if the remote is ahead, `git pull --rebase origin main` then push.

---

## Quick reference

| step | script | run it | edit |
|---|---|---|---|
| 0 scaffold | `tools/new_cycle.py` | `python3 tools/new_cycle.py 2027A --tag jan` | — |
| 1 dark | `tools/darkcurrent/copy_darkcurrent.py` | `python3 … <IPTS> 2027A` | — |
| 2 flux | `<cycle>_mp/flux/run_flux.py` | `python3 run_flux.py <IPTS>` | confirm run range (step 0) |
| 3 flood **(default)** | `prepare_sensitivities_eqsans` (sans_qa) | `pixi run --manifest-path /usr/local/pixi/sans_qa prepare_sensitivities_eqsans cfg.toml out.nxs` | TOML runs + geometry (pass 2) |
| 3 flood (legacy) | `<cycle>_mp/prepare_sensitivity.py` | `drtsans --classic prepare_sensitivity.py <c> [--nominal]` | `CONFIGS` runs |
| 3 flood QC | `check_sensitivity.py` | `python3 check_sensitivity.py --save qc.png` | — |
| 4 AgBe | `<cycle>_mp/agbe_calibration/agbe_reducenfit.py` | `drtsans --classic agbe_reducenfit.py` | `CONFIGURATION` block (files, runs, `SAMPLE_OFFSET`) |
| 5 mask | `tools/mask/make_mask.py` | `$SANSDIR/.venv/bin/python … <run> --ipts <IPTS> --outdir …` | tune flags after reviewing PNG |
| 6 reduce + scale | `generate_reduction.py`, `find_absscale.py` | `drtsans reduce_standards.py`; `python3 find_absscale.py 2027A` | CONFIG block; absscale window |
| 7 standards | `tools/reduce/report_standards.py` | `python3 … 2027A <IPTS> <first>-<last>` | — |
| 8 publish | `doc/generate.py` | `/update-mp-page` | commit message |

## Gotchas worth repeating

- **Sensitivity is built twice, around AgBe** — pass 1 nominal (no geometry) so AgBe has a flood, then
  pass 2 with the AgBe geometry. Both passes are in step 3; AgBe is step 4 in between.
- **`drtsans --classic` when passing flags** — bare `drtsans` runs ipython and drops them.
- **Roles by title, not position** — blocks grow between cycles (2026B went 7→11 runs); match
  `T-/S-` + `NoWindow/banjo/agbe/...`, and verify the logged distance/λ against the title.
- **AgBe runs last of the four** — it consumes the dark, flux and (nominal) flood.
- **Copy the flux and flood up to `<cycle>_mp/`** — reduction and the site read them from the cycle root.
- **Never commit NeXus** — only `doc/` is git; the cycle folders hold multi-GB data files.
- **Ask before writing to `/SNS/EQSANS/shared/instrument_configuration/`** — that changes reduction for
  every user.
