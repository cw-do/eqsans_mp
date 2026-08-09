# EQSANS Machine Physics summary site

A static web page that summarises the per-cycle machine-physics calibration
files in `/SNS/EQSANS/shared/NeXusFiles/EQSANS`. It opens on the **most recent
cycle** and lets you pick any past cycle from the dropdown.

- **Summary** view — the full path (one-click copy) of each cycle's dark
  current, sensitivity (flood) and flux spectrum files, plus the AgBe
  instrument variables (`scale_y`, `scale_all`, `detoffset`, `samoffset`,
  `scalecomp`).
- **Details** view — the flux spectrum plotted, QC / flood / AgBe plots, and
  the cycle's own `README.md` rendered inline.

Live page: **https://cw-do.github.io/eqsans_mp/** (once GitHub Pages is
enabled for this repo — Settings → Pages → deploy from `main` / root).

## Files

| File | What it is |
|---|---|
| `index.html` | the page — self-contained, no external dependencies |
| `data.js` | generated: `window.EQSANS_DATA` with every cycle's summary + flux curves |
| `assets/<cycle>/` | generated: copied QC/AgBe/flood plots for each cycle |
| `generate.py` | scans the cycle folders and rebuilds `data.js` + `assets/` |

`data.js` and `assets/` are **generated** — do not edit them by hand. Edit
`index.html` (layout) or `generate.py` (what gets collected) instead.

## Updating

The easy way, from inside a Claude Code session in the machine-physics folder:

```
/update-mp-page
```

That regenerates the site, shows you what changed, and commits + pushes.

By hand:

```bash
cd /SNS/EQSANS/shared/NeXusFiles/EQSANS/doc
python3 generate.py          # rescan, rebuild data.js + assets/
python3 generate.py --check  # dry run: print what was found, write nothing
git add -A && git commit -m "Update machine-physics summary" && git push
```

`generate.py` uses only the Python standard library, so a plain `python3`
works — no drtsans / mantid needed. It never reads the multi-GB NeXus files;
it only stats them and copies small PNG plots, so the repo stays light.

## How a cycle is detected

Any sibling folder named like `2026B_mp` (`<year><A|B>_mp`) is a cycle. Within
it the generator looks for:

- **dark current** — top-level `EQSANS_*.nxs.h5` / `EQSANS_*_event.nxs`
- **sensitivity** — top-level `Sensitivity_patched_*.nxs` (distance parsed
  from `1o3m` / `2o5m` / `4m` … in the name)
- **flux** — a `*flux*.txt` (a `final_flux/` copy wins if present)
- **AgBe variables** — `calibration_report.txt`, else the AgBe
  `checkpoint.json`, else `result_scale_all_detoffset.txt`
- **plots** — representative `*.png` files, copied into `assets/<cycle>/`

Older cycles that predate this file convention still show whatever matches
(usually dark current + sensitivity); newer cycles show the full set.
