#!/usr/bin/env python3
"""
EQSANS machine-physics summary site generator.

Scans the EQSANS NeXusFiles machine-physics folders (one per cycle, named
like ``2026B_mp``) and builds the data that drives the static summary page in
this ``doc/`` folder.

For every cycle it finds, it records:
  * the dark-current raw NeXus file(s)
  * the sensitivity (flood) files, one per detector distance
  * the beam flux spectrum file (and its curve, embedded for plotting)
  * the AgBe calibration results (scale_y, scale_all, detoffset, samoffset,
    scalecomp) parsed from the calibration report / checkpoint
  * a representative set of QC plots, copied into ``doc/assets/<cycle>/``
  * the cycle README, embedded so the detail view can render it

Output:
  * ``doc/data.js``  -- ``window.EQSANS_DATA = {...}`` consumed by index.html
  * ``doc/assets/<cycle>/*.png`` -- copied plots

It has no third-party dependencies (standard library only) so it runs anywhere
drtsans/python or a plain python3 is available.

Usage:
    python3 generate.py            # scan and write data.js + assets
    python3 generate.py --check    # scan and print a summary, write nothing
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

# --- attenuation-for-transmission table (from W. Heller's xlsx) ------------

def build_atten_table(xlsx_path):
    """Read attenuation_for_trans.xlsx (stdlib only) and return a markdown table
    of detector count rate (cps) per slit-1 choice, with a recommended slit per
    (wavelength, dL/L): the largest non-distorted rate that stays <= 20 k cps."""
    import zipfile
    import xml.etree.ElementTree as ET
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(xlsx_path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si"):
            shared.append("".join(t.text or "" for t in si.iter(M + "t")))
    ws = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))

    def cidx(ref):
        n = 0
        for ch in re.match("[A-Z]+", ref).group():
            n = n * 26 + (ord(ch) - 64)
        return n

    grid = {}
    for cell in ws.iter(M + "c"):
        ref = cell.get("r")
        v = cell.find(M + "v")
        rr = int(re.search(r"\d+", ref).group())
        cc = cidx(ref)
        val = shared[int(v.text)] if (cell.get("t") == "s" and v is not None) \
            else (v.text if v is not None else "")
        grid[(rr, cc)] = (val or "").strip()

    slits = ["d25Cd", "d5", "d10", "d15", "d20", "d25"]

    def parse(s):
        s = (s or "").strip()
        if not s or s.lower() == "nm":
            return (None, False)
        dist = "dis" in s.lower()
        num = s.split("/")[0].strip().lower()
        mult = 1000 if num.endswith("k") else 1
        num = num.rstrip("k")
        try:
            return (float(num) * mult, dist)
        except ValueError:
            return (None, dist)

    lines = ["| λ (Å) | dL/L | " + " | ".join(slits) + " | **Recommended slit** |",
             "|---|---|" + "---|" * 6 + "---|"]
    for rr in range(3, 60):
        lam = grid.get((rr, 1), "")
        dll = grid.get((rr, 2), "")
        try:                                   # only real data rows; skip blanks
            float(lam)                         # and free-text notes (e.g. the
        except (TypeError, ValueError):        # distortion caveat in column 1)
            continue
        cells = [grid.get((rr, 3 + i), "") for i in range(6)]
        cand = [(parse(c)[0], s) for s, c in zip(slits, cells)
                if parse(c)[0] is not None and not parse(c)[1] and parse(c)[0] <= 20000]
        rec = max(cand)[1] if cand else None
        disp = []
        for s, c in zip(slits, cells):
            disp.append(("**%s**" % c) if (s == rec and c) else (c if c else "·"))
        if rec:
            cps = dict((s, parse(c)[0]) for s, c in zip(slits, cells))[rec]
            recstr = "**%s** (%s cps)" % (rec, "{:,}".format(int(cps)))
        else:
            recstr = "— (none ≤ 20k)"
        lines.append("| %s | %s%% | " % (lam, dll) + " | ".join(disp) + " | %s |" % recstr)
    return "\n".join(lines)


# --- locations -------------------------------------------------------------

DOC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOC_DIR)                      # the machine-physics folder
ASSETS_DIR = os.path.join(DOC_DIR, "assets")

# Path shown to users on the page. The folder is mounted at both /SNS/... and
# /gpfs/...; users refer to it by the /SNS path, so display that regardless of
# which mount the generator happens to run from.
DISPLAY_ROOT = "/SNS/EQSANS/shared/NeXusFiles/EQSANS"

CYCLE_RE = re.compile(r"^(\d{4})([AB])_mp$")

# distance tokens found in sensitivity / flux file names -> metres
DIST_TOKENS = [
    ("1o3m", 1.3), ("2o5m", 2.5), ("2o0m", 2.0),
    ("4m", 4.0), ("5m", 5.0), ("8m", 8.0), ("2m", 2.0),
]

# Only copy plots below this size, and cap how many per category, so the git
# repo stays small.
MAX_PLOT_BYTES = 3 * 1024 * 1024
MAX_PLOTS_PER_CATEGORY = 8
MAX_FLUX_POINTS = 500


# --- helpers ---------------------------------------------------------------

def display_path(abspath):
    """Absolute path, but rooted at DISPLAY_ROOT for what users see."""
    rel = os.path.relpath(abspath, ROOT)
    return os.path.normpath(os.path.join(DISPLAY_ROOT, rel))


def human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0


def mtime_iso(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path),
                                      tz=timezone.utc).strftime("%Y-%m-%d")
    except OSError:
        return ""


def distance_of(name):
    low = name.lower()
    for tok, metres in DIST_TOKENS:
        if tok in low:
            return metres
    return None


def run_number(name):
    """Last run-length number in a file name (the run id, usually trailing)."""
    nums = re.findall(r"(\d{4,7})", name)
    return nums[-1] if nums else None


def file_entry(abspath):
    try:
        size = os.path.getsize(abspath)
    except OSError:
        size = 0
    return {
        "name": os.path.basename(abspath),
        "path": display_path(abspath),
        "size": size,
        "size_h": human_size(size),
        "mtime": mtime_iso(abspath),
    }


# --- artifact detection ----------------------------------------------------

def find_dark_current(cycle_dir):
    """Raw dark-current NeXus files at the top level of the cycle folder."""
    out = []
    for f in sorted(os.listdir(cycle_dir)):
        low = f.lower()
        if not low.startswith("eqsans_"):
            continue
        if low.endswith(".nxs.h5") or low.endswith("_event.nxs") or \
           (low.endswith(".nxs") and "sensitivity" not in low):
            e = file_entry(os.path.join(cycle_dir, f))
            e["run"] = run_number(f)
            out.append(e)
    # Prefer the largest as the primary (dark current is a long measurement).
    out.sort(key=lambda e: e["size"], reverse=True)
    return out


def find_sensitivity(cycle_dir):
    """Sensitivity (flood) files at the top level, one per distance."""
    out = []
    for f in sorted(os.listdir(cycle_dir)):
        low = f.lower()
        if low.startswith("sensitivity") and low.endswith(".nxs"):
            e = file_entry(os.path.join(cycle_dir, f))
            e["distance"] = distance_of(f)
            e["run"] = run_number(f)
            out.append(e)
    out.sort(key=lambda e: (e["distance"] or 99, e["name"]))
    return out


#  Preserved/superseded directories kept on disk for comparison but off the page
#  (e.g. agbe_37618.OLD_drtsans1.33/, reduced.OLD_drtsans1.33/).
PRESERVED_RE = re.compile(r"\.old|old_drtsans|superseded|backup|choppertmp", re.I)
#  Superseded/backup flux copies to keep off the page (renamed originals kept
#  on disk for comparison, e.g. *.OLD_drtsans1.33_choppertmp.txt).
FLUX_SKIP_RE = re.compile(r"\.old|old_|superseded|backup|choppertmp|\bprev\b", re.I)
#  Pipeline scaffold folders whose deliverable is already copied to top level.
FLUX_SKIP_SUBDIR = {"flux"}


def find_flux(cycle_dir):
    """Beam flux spectrum text files. Prefer a top-level / 'final' one."""
    candidates = []
    # top level
    for f in sorted(os.listdir(cycle_dir)):
        if "flux" in f.lower() and f.lower().endswith(".txt") \
                and not FLUX_SKIP_RE.search(f):
            candidates.append(os.path.join(cycle_dir, f))
    # one level down (e.g. final_flux/, flux_4m/) if nothing at top level
    subdir_hits = []
    for sub in sorted(os.listdir(cycle_dir)):
        subpath = os.path.join(cycle_dir, sub)
        if not os.path.isdir(subpath) or sub.lower() in FLUX_SKIP_SUBDIR:
            continue
        for f in sorted(os.listdir(subpath)):
            if "flux" in f.lower() and f.lower().endswith(".txt") \
                    and not FLUX_SKIP_RE.search(f):
                subdir_hits.append((sub, os.path.join(subpath, f)))

    entries = []
    for p in candidates:
        e = file_entry(p)
        e["subdir"] = ""
        entries.append(e)
    for sub, p in subdir_hits:
        e = file_entry(p)
        e["subdir"] = sub
        entries.append(e)

    # Choose the primary: a 'final' one wins, else newest top-level, else newest.
    def score(e):
        s = 0
        if "final" in e["subdir"].lower():
            s += 100
        if not e["subdir"]:
            s += 10
        return (s, e["mtime"])

    entries.sort(key=score, reverse=True)
    for i, e in enumerate(entries):
        e["primary"] = (i == 0)
    return entries


def read_flux_curve(display_flux_path):
    """Read a flux .txt (columns x, Y, Yerr) back from disk for plotting."""
    # Map the display path back to a real path under ROOT.
    rel = os.path.relpath(display_flux_path, DISPLAY_ROOT)
    real = os.path.join(ROOT, rel)
    xs, ys, es = [], [], []
    try:
        with open(real, "r", errors="replace") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    x = float(parts[0]); y = float(parts[1])
                except ValueError:
                    continue          # header row
                err = 0.0
                if len(parts) >= 3:
                    try:
                        err = float(parts[2])
                    except ValueError:
                        err = 0.0
                xs.append(x); ys.append(y); es.append(err)
    except OSError:
        return None
    if not xs:
        return None
    # Downsample uniformly if very long.
    if len(xs) > MAX_FLUX_POINTS:
        step = len(xs) // MAX_FLUX_POINTS + 1
        xs, ys, es = xs[::step], ys[::step], es[::step]
    return {"x": xs, "y": ys, "yerr": es}


def find_flux_compare(cycle_dir, cycle_id):
    """Curated old-vs-new flux comparison PNG (from tools/flux/compare_flux.py).

    Lives in the flux/ scaffold, which collect_plots skips; surface it
    deliberately in the Details flux section as a re-reduction diagnostic.
    """
    src = os.path.join(cycle_dir, "flux", "flux_compare_dev_vs_stable.png")
    if not os.path.isfile(src):
        return None
    dest_dir = os.path.join(ASSETS_DIR, cycle_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "flux_compare.png")
    shutil.copy2(src, dest)
    return f"assets/{cycle_id}/flux_compare.png"


AGBE_KEYS = {
    "scale_y": re.compile(r"scale_y\s*:?\s*=?\s*([0-9.]+)", re.I),
    "scale_all": re.compile(r"scale_all\s*:?\s*=?\s*([0-9.]+)", re.I),
    "detoffset": re.compile(r"detoffset\s*:?\s*=?\s*([0-9.]+)", re.I),
    "samoffset": re.compile(r"samoffset\s*:?\s*=?\s*([0-9.]+)", re.I),
}


def parse_calibration_report(path):
    vals = {}
    try:
        with open(path, "r", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    for key, rx in AGBE_KEYS.items():
        m = rx.search(text)
        if m:
            vals[key] = float(m.group(1))
    m = re.search(r"scalecomp\s*=\s*\[([^\]]+)\]", text)
    if m:
        try:
            vals["scalecomp"] = [float(x) for x in m.group(1).split(",")]
        except ValueError:
            pass
    vals["source"] = os.path.basename(path)
    vals["report_text"] = text            # shown verbatim on the details page
    return vals


def parse_checkpoint(path):
    try:
        with open(path, "r", errors="replace") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    res = data.get("results", {})
    if not res:
        return None
    vals = {}
    for k in ("scale_y", "scale_all", "detoffset"):
        if k in res and isinstance(res[k], (int, float)):
            vals[k] = float(res[k])
    if isinstance(res.get("scalecomp"), list):
        vals["scalecomp"] = [float(x) for x in res["scalecomp"]]
    vals["source"] = os.path.relpath(path, ROOT)
    vals["partial"] = len(data.get("completed_steps", [])) < 4
    return vals


def find_agbe(cycle_dir):
    """Instrument variables from AgBe calibration.

    Preference: a full calibration_report.txt, else the most complete
    checkpoint.json, else a result_scale_all_detoffset.txt note.
    """
    reports, checkpoints, notes = [], [], []
    ipts = None
    for dirpath, dirnames, filenames in os.walk(cycle_dir):
        # do not descend into huge scan trees
        dirnames[:] = [d for d in dirnames
                       if not d.startswith("scaleall_")
                       and not d.startswith("scale_detoffset")
                       and d != "__pycache__" and d != ".git"
                       and not PRESERVED_RE.search(d)]
        m = re.search(r"agbe_(\d{4,7})", os.path.basename(dirpath))
        if m and ipts is None:
            ipts = m.group(1)
        for f in filenames:
            full = os.path.join(dirpath, f)
            if f == "calibration_report.txt":
                reports.append(full)
            elif f == "checkpoint.json":
                checkpoints.append(full)
            elif f == "result_scale_all_detoffset.txt":
                notes.append(full)

    vals = None
    if reports:
        reports.sort(key=os.path.getmtime, reverse=True)
        vals = parse_calibration_report(reports[0])
    if vals is None and checkpoints:
        parsed = [parse_checkpoint(c) for c in checkpoints]
        parsed = [p for p in parsed if p]
        if parsed:
            # most complete first, then newest
            parsed.sort(key=lambda p: (not p.get("partial", False),), reverse=True)
            vals = parsed[0]
    if vals is None and notes:
        try:
            with open(notes[0], errors="replace") as fh:
                vals = {"note": fh.read().strip(),
                        "source": os.path.relpath(notes[0], ROOT)}
        except OSError:
            pass
    if vals is not None:
        vals["ipts"] = ipts
    return vals, ipts


# --- plots -----------------------------------------------------------------

def categorize_plot(name, relpath):
    low = (name + " " + relpath).lower()
    if "sensitivity" in low or "flood" in low:
        return "sensitivity"
    if "flux" in low or "ixiy" in low or "overlay_ix" in low:
        return "flux"
    if "agbe" in low or "q1_" in low or "offset" in low or "iq" in low:
        return "agbe"
    return "other"


def collect_plots(cycle_dir, cycle_id):
    """Find representative PNG plots and copy them into assets/<cycle>/."""
    found = {"sensitivity": [], "flux": [], "agbe": [], "other": []}
    for dirpath, dirnames, filenames in os.walk(cycle_dir):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith("scaleall_")
                       and "gridsnap" not in d.lower()
                       and d != "__pycache__" and d != ".git"
                       and d != "beam_spectra"   # has its own monoWL3 tab
                       and d != "flux"           # pipeline scaffold; curated below
                       and not PRESERVED_RE.search(d)]   # preserved *.OLD_* dirs
        for f in filenames:
            if not f.lower().endswith(".png"):
                continue
            full = os.path.join(dirpath, f)
            try:
                if os.path.getsize(full) > MAX_PLOT_BYTES:
                    continue
            except OSError:
                continue
            rel = os.path.relpath(full, cycle_dir)
            cat = categorize_plot(f, rel)
            found[cat].append((full, rel))

    # Names of the informative summary plots -- surface these first.
    priority_rx = re.compile(
        r"sensitivity_qc|overlay_sensitivity|overlay_ixiy|"
        r"q1_vs_scale_y_plot|offset_mean_variance|"
        r"agbe_10a\w*_iq\.png|flux", re.I)

    def rank(item):
        full, rel = item
        pri = 0 if priority_rx.search(os.path.basename(rel)) else 1
        return (pri, rel.count(os.sep), rel)

    # A per-step scan series (one plot per scaleall_/sy/offset value) should
    # collapse to a single representative; distinct verification figures
    # (per-wavelength Iq/Iqxqy, fit peaks) must all be kept.
    scan_rx = re.compile(r"scaleall_|_sy\d|detoffset|q1_vs_offset", re.I)

    # Prefer summary plots, then shallower paths; de-duplicate scan series.
    plots = []
    dest_dir = os.path.join(ASSETS_DIR, cycle_id)
    for cat, items in found.items():
        items.sort(key=rank)
        picked = 0
        seen_stems = set()
        for full, rel in items:
            if picked >= MAX_PLOTS_PER_CATEGORY:
                break
            base = os.path.basename(rel)
            if scan_rx.search(base):
                stem = re.sub(r"[0-9.]+", "#", base)
                if stem in seen_stems:
                    continue
                seen_stems.add(stem)
            os.makedirs(dest_dir, exist_ok=True)
            safe = rel.replace(os.sep, "__")
            shutil.copy2(full, os.path.join(dest_dir, safe))
            plots.append({
                "category": cat,
                "title": os.path.basename(rel),
                "subpath": rel,
                "src": f"assets/{cycle_id}/{safe}",
            })
            picked += 1
    return plots


# --- standard samples ------------------------------------------------------

def collect_standards(cycle_dir, cycle_id):
    """Reduced standard-sample results from reduction/reduced/standards.json.

    Written by tools/reduce/report_standards.py. Copies the 2D (and 1D) plot
    PNGs into assets/<cycle>/standards/ and returns the datasets with embedded
    I(q) curves for client-side plotting.
    """
    reduced = os.path.join(cycle_dir, "reduction", "reduced")
    sjson = os.path.join(reduced, "standards.json")
    if not os.path.isfile(sjson):
        return []
    try:
        with open(sjson, errors="replace") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return []

    dest_dir = os.path.join(ASSETS_DIR, cycle_id, "standards")
    out = []
    for d in payload.get("datasets", []):
        rec = {
            "sample": d.get("sample"),
            "config": d.get("config"),
            "dist": d.get("dist"),
            "wl": d.get("wl"),
            "run": d.get("run"),
            "total_counts": d.get("total_counts"),
            "duration": d.get("duration"),
            "iq": d.get("iq"),
            "error": d.get("error"),
            "abs_scale": d.get("abs_scale"),
            "abs_scale_npts": d.get("abs_scale_npts"),
            "abs_scale_spread": d.get("abs_scale_spread"),
            "abs_scale_note": d.get("abs_scale_note"),
            "abs_scale_range": d.get("abs_scale_range"),
            "iqxqy_src": None,
            "iq_png_src": None,
            "abs_scale_src": None,
        }
        for key, dstkey in (("iqxqy_png", "iqxqy_src"), ("iq_png", "iq_png_src"),
                            ("abs_scale_png", "abs_scale_src")):
            name = d.get(key)
            if not name:
                continue
            src = os.path.join(reduced, name)
            if os.path.exists(src) and os.path.getsize(src) <= MAX_PLOT_BYTES:
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(dest_dir, name))
                rec[dstkey] = f"assets/{cycle_id}/standards/{name}"
        out.append(rec)
    return out


# --- monochromatic vary-spread series --------------------------------------

def collect_varyspread(cycle_dir, cycle_id):
    """Monochromatic vary-spread results from reduction/reduced_varyspread/varyspread.json.

    Written by tools/reduce/report_varyspread.py. Copies any plot PNGs into
    assets/<cycle>/varyspread/ and returns the datasets (with error reasons and
    embedded I(Q) curves for the spreads that reduced).
    """
    reduced = os.path.join(cycle_dir, "reduction", "reduced_varyspread")
    vjson = os.path.join(reduced, "varyspread.json")
    if not os.path.isfile(vjson):
        return []
    try:
        with open(vjson, errors="replace") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return []
    dest_dir = os.path.join(ASSETS_DIR, cycle_id, "varyspread")
    out = []
    for d in payload.get("datasets", []):
        rec = {"sample": d.get("sample"), "spread": d.get("spread"),
               "run": d.get("run"), "total_counts": d.get("total_counts"),
               "duration": d.get("duration"), "iq": d.get("iq"),
               "error": d.get("error"), "iqxqy_src": None, "iq_png_src": None}
        for key, dstkey in (("iqxqy_png", "iqxqy_src"), ("iq_png", "iq_png_src")):
            name = d.get(key)
            if not name:
                continue
            src = os.path.join(reduced, name)
            if os.path.exists(src) and os.path.getsize(src) <= MAX_PLOT_BYTES:
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(dest_dir, name))
                rec[dstkey] = f"assets/{cycle_id}/varyspread/{name}"
        out.append(rec)
    return out


# --- beam spectra (monochromatic beam character) ---------------------------

def collect_beam_spectra(cycle_dir, cycle_id):
    """Monochromatic beam-character spectra from beam_spectra/beam_spectra.json.

    Written by tools/beam_spectra/make_beam_spectra.py. Each record is one
    empty-flux run: raw TOF + drtsans wavelength spectrum in a side-by-side PNG.
    Copies the PNGs into assets/<cycle>/beam_spectra/ and returns the records
    (run/title/counts/duration/wavelength/spread + figure src), plus the name of
    the generating script for display.
    """
    bdir = os.path.join(cycle_dir, "beam_spectra")
    bjson = os.path.join(bdir, "beam_spectra.json")
    if not os.path.isfile(bjson):
        return None
    try:
        with open(bjson, errors="replace") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return None
    dest_dir = os.path.join(ASSETS_DIR, cycle_id, "beam_spectra")
    records = []
    for d in payload.get("records", []):
        rec = {k: d.get(k) for k in ("run", "title", "counts", "duration",
                                     "wavelength", "spread", "wl_ok")}
        png = d.get("png")
        if png:
            src = os.path.join(bdir, png)
            if os.path.exists(src) and os.path.getsize(src) <= MAX_PLOT_BYTES:
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(dest_dir, png))
                rec["src"] = f"assets/{cycle_id}/beam_spectra/{png}"
        records.append(rec)
    return {"script": payload.get("script"),
            "run_range": payload.get("run_range"),
            "records": records}


# --- masks -----------------------------------------------------------------

def collect_masks(cycle_dir, cycle_id):
    """Detector masks from masks/*_mask.params.json (written by make_mask.py).

    Copies each raw-vs-mask comparison PNG into assets/<cycle>/masks/ and
    returns the preparation record (run, config, beam, bands, tubes, command).
    """
    mdir = os.path.join(cycle_dir, "masks")
    if not os.path.isdir(mdir):
        return []
    dest = os.path.join(ASSETS_DIR, cycle_id, "masks")
    out = []
    for name in sorted(os.listdir(mdir)):
        if not name.endswith("_mask.params.json"):
            continue
        try:
            with open(os.path.join(mdir, name), errors="replace") as fh:
                p = json.load(fh)
        except (OSError, ValueError):
            continue
        png = p.get("compare_png")
        if png:
            src = os.path.join(mdir, png)
            if os.path.exists(src) and os.path.getsize(src) <= MAX_PLOT_BYTES:
                os.makedirs(dest, exist_ok=True)
                shutil.copy2(src, os.path.join(dest, png))
                p["compare_src"] = f"assets/{cycle_id}/masks/{png}"
        if p.get("mask_nxs"):
            p["mask_path"] = display_path(os.path.join(mdir, p["mask_nxs"]))
        out.append(p)
    return out


# --- readme ----------------------------------------------------------------

def read_readme(cycle_dir):
    for name in ("README.md", "readme.md", "README.txt"):
        p = os.path.join(cycle_dir, name)
        if os.path.isfile(p):
            try:
                with open(p, errors="replace") as fh:
                    return fh.read()
            except OSError:
                return None
    return None


# --- data provenance (which script produced each on-page product) ----------

# Shared toolkit scripts: one master copy under tools/, stable relative paths.
TOOLKIT = {
    "report_standards":  "tools/reduce/report_standards.py",
    "find_absscale":     "tools/reduce/find_absscale.py",
    "report_varyspread": "tools/reduce/report_varyspread.py",
    "run_flux":          "tools/flux/run_flux.py",
}


def _script(cycle_dir, *rel):
    """Display path of the first of these cycle-local scripts that exists."""
    for r in rel:
        p = os.path.join(cycle_dir, r)
        if os.path.isfile(p):
            return display_path(p)
    return None


def load_reduction_provenance(cycle_dir):
    """Optional per-cycle reduction_provenance.json.

    Maps an on-page product (flux, agbe, standards, sensitivity, varyspread,
    beam_spectra) to {script, drtsans, date, note}. Each reduction step appends
    its entry so the page can show *when* a product was generated and with
    which drtsans build, not just which script. Missing file -> {}.
    """
    p = os.path.join(cycle_dir, "reduction_provenance.json")
    if not os.path.isfile(p):
        return {}
    try:
        with open(p) as fh:
            data = json.load(fh)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception as exc:                               # noqa: BLE001
        print(f"  ! reduction_provenance.json parse failed in {cycle_dir}: {exc}",
              file=sys.stderr)
        return {}


def _stamp(meta, key):
    """' · drtsans <ver>, <date>' suffix for product `key`, or '' if none."""
    m = meta.get(key)
    if not m:
        return ""
    bits = []
    ver = m.get("drtsans")
    if ver:
        # 1.34.0.dev20260814133834 -> 1.34dev; 1.33.0 -> 1.33
        short = ver
        mm = re.match(r"(\d+\.\d+).*?(dev)?", ver)
        if mm:
            short = mm.group(1) + ("dev" if "dev" in ver else "")
        bits.append("drtsans " + short)
    if m.get("date"):
        bits.append(m["date"])
    return (" · " + ", ".join(bits)) if bits else ""


def build_provenance(cycle_dir, has_flux, has_dark):
    """Map each on-page data product to the script(s) that produced it.

    Cycle-local scripts are detected by presence, so historical cycles that
    predate the toolkit are never mislabeled. Shared toolkit scripts (which
    leave no per-cycle file) are cited only when a cycle-local reduction script
    proves the cycle used the current MP toolkit. Dark current is a raw file
    (not reduced/plotted) whose fetch tool leaves no trace, so it is not tagged.
    """
    meta = load_reduction_provenance(cycle_dir)
    prov = {}
    agbe_s = _script(cycle_dir, "agbe_calibration/agbe_reducenfit.py",
                     "agbe_reducenfit.py")
    if agbe_s:
        prov["agbe"] = agbe_s + _stamp(meta, "agbe")

    prep = _script(cycle_dir, "prepare_sensitivity.py")
    qc = _script(cycle_dir, "check_sensitivity.py")
    flood = _script(cycle_dir, "plot_flood.py")
    if prep or qc or flood:
        parts = []
        if prep:
            parts.append("data: " + prep)
        plots = [p for p in (qc, flood) if p]
        if plots:
            parts.append("QC plots: " + ", ".join(plots))
        prov["sensitivity"] = " · ".join(parts) + _stamp(meta, "sensitivity")

    red_std = _script(cycle_dir, "reduction/reduce_standards_fixedbb.py",
                      "reduction/reduce_standards.py")
    if red_std:
        prov["standards"] = ("reduced by " + red_std + " · tabulated by " +
                             TOOLKIT["report_standards"] +
                             " · absolute scale by " + TOOLKIT["find_absscale"] +
                             _stamp(meta, "standards"))

    red_vs = _script(cycle_dir, "reduction/reduce_varyspread_dev.py",
                     "reduction/reduce_varyspread.py")
    if red_vs:
        prov["varyspread"] = ("reduced by " + red_vs + " · tabulated by " +
                              TOOLKIT["report_varyspread"] +
                              _stamp(meta, "varyspread"))

    # Flux: prefer a cycle-local pipeline (scaffolded in <cycle>_mp/flux) and
    # fall back to the shared master. Attribute it only when a cycle-local
    # reduction script proves current-toolkit use.
    flux_s = _script(cycle_dir, "flux/run_flux.py")
    toolkit_era = bool(agbe_s or red_std or red_vs)
    if has_flux and (flux_s or toolkit_era):
        prov["flux"] = (flux_s or TOOLKIT["run_flux"]) + " (fluxlib.py)" + \
            _stamp(meta, "flux")
    return prov


# --- per-cycle scan --------------------------------------------------------

def sort_key(year, half):
    return year + (0.2 if half == "B" else 0.1)


def scan_cycle(folder):
    cycle_dir = os.path.join(ROOT, folder)
    m = CYCLE_RE.match(folder)
    year, half = int(m.group(1)), m.group(2)
    cid = f"{year}{half}"

    dark = find_dark_current(cycle_dir)
    sens = find_sensitivity(cycle_dir)
    flux = find_flux(cycle_dir)
    agbe, ipts = find_agbe(cycle_dir)
    plots = collect_plots(cycle_dir, cid)
    standards = collect_standards(cycle_dir, cid)
    varyspread = collect_varyspread(cycle_dir, cid)
    beam_spectra = collect_beam_spectra(cycle_dir, cid)
    masks = collect_masks(cycle_dir, cid)
    readme = read_readme(cycle_dir)

    # per-cycle attenuation-for-transmission study (W. Heller), if measured
    attenuation = None
    axlsx = os.path.join(cycle_dir, "attenuation_for_trans.xlsx")
    if os.path.isfile(axlsx) and os.path.getsize(axlsx) > 0:
        try:
            attenuation = build_atten_table(axlsx)
        except Exception as exc:                       # noqa: BLE001
            print(f"  ! attenuation parse failed for {folder}: {exc}", file=sys.stderr)

    flux_curve = None
    primary_flux = next((f for f in flux if f.get("primary")), None)
    if primary_flux:
        flux_curve = read_flux_curve(primary_flux["path"])
        if flux_curve:
            flux_curve["label"] = primary_flux["name"]

    if ipts is None and readme:
        mm = re.search(r"IPTS[- ]?(\d{4,7})", readme)
        if mm:
            ipts = mm.group(1)

    provenance = build_provenance(cycle_dir, bool(flux), bool(dark))
    prov_meta = load_reduction_provenance(cycle_dir)
    flux_compare = find_flux_compare(cycle_dir, cid)

    return {
        "id": cid,
        "folder": folder,
        "path": display_path(cycle_dir),
        "year": year,
        "half": half,
        "sort": sort_key(year, half),
        "mtime": mtime_iso(cycle_dir),
        "ipts": ipts,
        "dark_current": dark,
        "sensitivity": sens,
        "flux": flux,
        "flux_curve": flux_curve,
        "flux_compare": flux_compare,
        "agbe": agbe,
        "plots": plots,
        "standards": standards,
        "varyspread": varyspread,
        "beam_spectra": beam_spectra,
        "masks": masks,
        "readme": readme,
        "attenuation": attenuation,
        "provenance": provenance,
        "prov_meta": prov_meta,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="scan and print a summary; write nothing")
    args = ap.parse_args()

    folders = sorted(f for f in os.listdir(ROOT)
                     if CYCLE_RE.match(f) and os.path.isdir(os.path.join(ROOT, f)))
    if not folders:
        print("No cycle folders (like 2026B_mp) found under", ROOT, file=sys.stderr)
        return 1

    if not args.check and os.path.isdir(ASSETS_DIR):
        shutil.rmtree(ASSETS_DIR)   # rebuild assets cleanly each run

    cycles = []
    for folder in folders:
        try:
            c = scan_cycle(folder)
            cycles.append(c)
        except Exception as exc:               # noqa: BLE001 - keep going
            print(f"  ! skipped {folder}: {exc}", file=sys.stderr)

    cycles.sort(key=lambda c: c["sort"], reverse=True)

    # Console summary.
    print(f"Scanned {len(cycles)} cycles under {DISPLAY_ROOT}")
    for c in cycles:
        agbe = c["agbe"] or {}
        av = ("scale_all=%s detoffset=%s" % (agbe.get("scale_all"),
              agbe.get("detoffset"))) if agbe else "no agbe"
        print(f"  {c['id']:6} dark:{len(c['dark_current'])} "
              f"sens:{len(c['sensitivity'])} flux:{len(c['flux'])} "
              f"plots:{len(c['plots'])}  {av}")

    if args.check:
        return 0

    # Instrument-level chopper documentation (rendered on the Choppers tab).
    chopper_md = None
    cp = os.path.join(DOC_DIR, "chopper.md")
    if os.path.isfile(cp):
        try:
            with open(cp, errors="replace") as fh:
                chopper_md = fh.read()
        except OSError:
            chopper_md = None

    # Monochromatic reduction diagnosis (rendered on the monoWL tab). Its plots
    # live in doc/monowl_assets/ (committed) and are copied into assets/monowl/
    # each run, since assets/ is wiped and rebuilt above.
    monowl_md = None
    mp = os.path.join(DOC_DIR, "monowl.md")
    if os.path.isfile(mp):
        try:
            with open(mp, errors="replace") as fh:
                monowl_md = fh.read()
        except OSError:
            monowl_md = None
    # Second monochromatic page (peak position / wavelength binning study).
    monowl2_md = None
    mp2 = os.path.join(DOC_DIR, "monowl2.md")
    if os.path.isfile(mp2):
        try:
            with open(mp2, errors="replace") as fh:
                monowl2_md = fh.read()
        except OSError:
            monowl2_md = None
    # Fourth monochromatic page (no-transmission-hack test on drtsans --dev, and
    # how I(Q,lambda) is recovered despite the dev build's single-bin override).
    monowl4_md = None
    mp4 = os.path.join(DOC_DIR, "monowl4.md")
    if os.path.isfile(mp4):
        try:
            with open(mp4, errors="replace") as fh:
                monowl4_md = fh.read()
        except OSError:
            monowl4_md = None

    # Attenuation-for-transmission tab: generic intro (doc/attenuation.md); the
    # count-rate TABLE is per-cycle (each cycle's own attenuation_for_trans.xlsx),
    # stored in cycle["attenuation"] and rendered under the selected cycle.
    attenuation_md = None
    ap = os.path.join(DOC_DIR, "attenuation.md")
    if os.path.isfile(ap):
        try:
            with open(ap, errors="replace") as fh:
                attenuation_md = fh.read()
        except OSError:
            attenuation_md = None

    # monoWL plots live in doc/monowl_assets/ (committed) -> assets/monowl/ each
    # run; both monowl.md and monowl2.md reference assets/monowl/*.png.
    src = os.path.join(DOC_DIR, "monowl_assets")
    if (monowl_md or monowl2_md or monowl4_md) and os.path.isdir(src):
        dest = os.path.join(ASSETS_DIR, "monowl")
        os.makedirs(dest, exist_ok=True)
        for f in os.listdir(src):
            if f.lower().endswith(".png"):
                shutil.copy2(os.path.join(src, f), os.path.join(dest, f))

    payload = {
        "generated": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "display_root": DISPLAY_ROOT,
        "cycles": cycles,
        "chopper_md": chopper_md,
        "monowl_md": monowl_md,
        "monowl2_md": monowl2_md,
        "monowl4_md": monowl4_md,
        "attenuation_md": attenuation_md,
    }
    out = os.path.join(DOC_DIR, "data.js")
    with open(out, "w") as fh:
        fh.write("// Auto-generated by generate.py -- do not edit by hand.\n")
        fh.write("window.EQSANS_DATA = ")
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(";\n")
    print(f"\nWrote {os.path.relpath(out, ROOT)} "
          f"({human_size(os.path.getsize(out))}) and assets/ "
          f"for {len(cycles)} cycles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
