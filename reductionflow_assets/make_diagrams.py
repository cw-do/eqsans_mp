#!/usr/bin/env python3
"""Reduction-flow page: Graphviz diagrams of the drtsans EQSANS workflow (drtsans 1.34.0,
tof/eqsans/api.py, reduction_api.py, load.py, correct_frame.py, normalization.py, transmission.py,
momentum_transfer.py, prepare_sensivities_correction.py). Run: python3 make_diagrams.py
Writes flow_*.png next to this script."""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Helvetica"
COMMON = f'''
  graph [fontname="{FONT}", fontsize=13, bgcolor="white", pad=0.25, nodesep=0.35, ranksep=0.42];
  node  [fontname="{FONT}", fontsize=12, shape=box, style="rounded,filled", fillcolor="#f4f3ef", color="#8f8d85", penwidth=1.1, margin="0.18,0.08"];
  edge  [fontname="{FONT}", fontsize=10.5, color="#5b5a55", arrowsize=0.75];
'''
# colours: input #e8f0fb (blue), load #fdf0e2 (orange), per-run #eaf6ef (green), combine #f3ecfa (purple),
#          Q/binning #fbeaea (red), output #f4f3ef (grey), config note #fffbe6 (yellow)
IN = 'shape=note, fillcolor="#e8f0fb", color="#6f93c6"'
LD = 'fillcolor="#fdf0e2", color="#d59a55"'
PR = 'fillcolor="#eaf6ef", color="#5fae83"'
CB = 'fillcolor="#f3ecfa", color="#9b7ac4"'
QB = 'fillcolor="#fbeaea", color="#cf7070"'
OUT = 'shape=folder, fillcolor="#f4f3ef", color="#8f8d85"'
CFG = 'shape=box, style="filled", fillcolor="#fffbe6", color="#d8c66a", fontsize=10'

D = {}

D["flow_overview"] = f'''digraph G {{ {COMMON} rankdir=TB;
  json [label="reduction JSON\\n(sample / background / transmission / empty / beam-centre runs,\\nfiles, and all switches)", {IN}];
  runs [label="event NeXus files\\n(EQSANS_*.nxs.h5)", {IN}];
  files [label="calibration files\\ndark current · flux spectrum · sensitivity (flood) · mask", {IN}];
  L [label="1  LOAD every run\\ngeometry · beam centre · time of flight → wavelength (0.1 Å bins)", {LD}];
  P [label="2  PROCESS each run, per pixel × per λ\\ndark → ÷ flux → − blocked beam → mask → ÷ solid angle → ÷ sensitivity", {PR}];
  T [label="3  TRANSMISSION\\nsample (and background) vs empty beam, within a radius → T(λ), fitted", {PR}];
  C [label="4  COMBINE and SCALE\\n÷ T(λ, 2θ) → sample − background → ÷ thickness → × absolute scale", {CB}];
  Q [label="5  Q, per-λ CORRECTIONS, BINNING\\nQ and resolution per pixel × λ → frames → [k(λ) elastic ref.] → [b(λ) incoherent] → bin 1D / 2D", {QB}];
  O [label="outputs\\n_Iq.dat · _Iqxqy.dat/.h5 · _processed.nxs · _trans.txt · I(Q, λ) profiles · reduction log", {OUT}];
  json -> L; runs -> L; files -> P; L -> P; L -> T; T -> C [label=" T(λ)"]; P -> C [label=" I(pixel, λ)"]; C -> Q; Q -> O;
  files -> T [style=dashed, label=" flux, sensitivity"];
  C -> O [style=dashed, label=" _processed.nxs"];
  T -> O [style=dashed, label=" _trans.txt"];
}}'''

D["flow_load"] = f'''digraph G {{ {COMMON} rankdir=TB;
  f [label="event file of one run\\n(neutron events: pixel id + time of flight)", {IN}];
  g [label="geometry\\nsample–detector distance = detectorZ (log) + detectorOffset − sampleOffset\\nscaleComponents (x, y, z pixel scaling) · optional pixel calibration", {LD}];
  t [label="time-of-flight corrections\\nframe (which pulse the neutron came from, incl. frame skipping)\\npath to each pixel · moderator emission-time delay", {LD}];
  c [label="beam centre\\ncentre of mass of the beam-centre run (direct beam)\\n→ detector shifted so the beam is at (0, 0)", {LD}];
  b [label="wavelength band(s)\\nfrom the chopper phases/speeds in the logs\\n(1 band at 60 Hz; 2 bands with frame skipping at 30 Hz)", {LD}];
  clip [label="clip the band edges\\ncutTOFmin / cutTOFmax (µs) removed at each end of the frame", {LD}];
  h [label="histogram in wavelength\\nwavelengthStep (0.1 Å) → workspace: counts(pixel, λ)\\n+ initial uncertainties √N", {LD}];
  o [label="raw run (counts per pixel × λ bin)", {OUT}];
  oth [label="all OTHER runs of the reduction\\n(background, transmission, empty, blocked beam)\\nare loaded in the SAMPLE's band\\n(must match within 0.1 Å); the dark run is loaded on its own", shape=box, style="filled,dashed", fillcolor="#ffffff", color="#d59a55", fontsize=10.5];
  cfg [label="config: sampleOffset, detectorOffset, scaleComponents,\\nusePixelCalibration, beamCenter.runNumber, cutTOFmin, cutTOFmax,\\nwavelengthStep, wavelengthStepType", {CFG}];
  f -> g -> t -> c -> b -> clip -> h -> o;
  h -> oth [style=dashed, arrowhead=none];
  cfg -> g [style=dotted, arrowhead=none];
}}'''

D["flow_process"] = f'''digraph G {{ {COMMON} rankdir=TB; compound=true;
  subgraph cluster_run {{ label="prepare_data_workspaces — the SAME chain for the sample and for the background run"; fontsize=12; color="#5fae83"; style="rounded";
    r [label="raw run: counts(pixel, λ)", {OUT}];
    d [label="① − dark current\\n(dark run scaled by run time and by the TOF window)", {PR}];
    n [label="② ÷ flux(λ) × proton charge   (normalization = \\"Total charge\\")\\n(or ÷ monitor × flux-to-monitor ratio, or ÷ time)", {PR}];
    bb [label="③ − blocked beam\\n(blocked-beam run, itself dark-subtracted and ÷ flux × charge;\\nsubtracted per pixel and per λ)", {PR}];
    m [label="④ mask\\n(mask file + default mask; optional: back tubes, bank/tube/pixel)", {PR}];
    sa [label="⑤ ÷ solid angle of each pixel\\n(from the geometry after offsets and scaling)", {PR}];
    s [label="⑥ ÷ sensitivity (flood file)\\nONE value per pixel, the same for every λ", {PR}];
    r -> d -> n -> bb -> m -> sa -> s;
  }}
  tr [label="⑦ ÷ transmission\\nθ-dependent: T(λ)^((1 + sec 2θ)/2)   (useThetaDepTransCorrection)\\nor ÷ T(λ); T from stage 3 or a fixed value", {CB}];
  sub [label="⑧ sample − background\\n(background went through ①–⑦ with its own transmission)", {CB}];
  th [label="⑨ ÷ sample thickness (cm)", {CB}];
  ab [label="⑩ × absolute scale (StandardAbsoluteScale)", {CB}];
  pn [label="processed: I(pixel, λ) in cm⁻¹  →  saved as _processed.nxs", {OUT}];
  s -> tr [ltail=cluster_run];
  tr -> sub -> th -> ab -> pn;
  cfg [label="config: darkFileName, normalization, beamFluxFileName (or fluxMonitorRatioFile),\\nblockedBeamRunNumber, maskFileName, useDefaultMask, useMaskBackTubes,\\nuseSolidAngleCorrection, sensitivityFileName, useThetaDepTransCorrection,\\nsample.thickness, StandardAbsoluteScale", {CFG}];
}}'''

D["flow_trans"] = f'''digraph G {{ {COMMON} rankdir=LR;
  ts [label="sample transmission run\\n(direct beam through the sample,\\nattenuated, beamstop out)", {IN}];
  te [label="empty-beam transmission run\\n(emptyTransmission)", {IN}];
  p1 [label="÷ flux × charge\\n÷ sensitivity\\n(no solid angle)", {PR}];
  p2 [label="÷ flux × charge\\n÷ sensitivity\\n(no solid angle)", {PR}];
  r [label="sum counts within\\nmmRadiusForTransmission\\nof the beam centre, per λ", {PR}];
  rat [label="raw T(λ) =\\nsample ÷ empty", {PR}];
  fit [label="fit T(λ) per band\\n(linear in λ)", {PR}];
  o1 [label="_raw_trans.txt", {OUT}];
  o2 [label="_trans.txt  → used in ⑦", {OUT}];
  ts -> p1 -> r; te -> p2 -> r; r -> rat -> fit -> o2; rat -> o1;
  note [label="the background (e.g. empty cell) can have its own transmission run,\\nor a fixed value (background.transmission.value)", shape=box, style="filled,dashed", fillcolor="#ffffff", color="#5fae83", fontsize=10.5];
  fit -> note [style=invis];
}}'''

D["flow_q"] = f'''digraph G {{ {COMMON} rankdir=TB;
  pn [label="processed I(pixel, λ)", {OUT}];
  q [label="Q for every pixel × λ bin: Q = 4π sin θ / λ   (1D |Q| and 2D Qx, Qy)\\n+ resolution σQ (apertures, pixel size, λ spread, moderator time)", {QB}];
  fr [label="split by frame\\n(frame skipping: the two bands are kept apart)", {QB}];
  el [label="[optional] elastic-reference normalization k(λ)\\neach λ slice × k(λ) from a reference run, so all slices share one scale", {QB}];
  inc [label="[optional] inelastic-incoherent correction b(λ)   (fitInelasticIncoh)\\nbin each λ slice → subtract a constant b(λ) so each slice matches the reference slice\\n(selectMinIncoh: reference = slice with the smallest b; Q range: incohfit_qmin/qmax/factor)", {QB}];
  bin [label="final binning of all (pixel, λ) points together\\n1D: scalar / wedge / annular · log or linear · numQBins or LogQBinsPerDecade · Qmin, Qmax\\n2D: numQxQyBins · useErrorWeighting (1/σ² weights)", {QB}];
  o [label="_Iq.dat (1D)  ·  _Iqxqy.dat / .h5 (2D)  ·  plots\\ninfo/…/IQ_<λ>_before/after_b_correction.dat   (outputWavelengthDependentProfile)\\n_reduction_log.hdf · .json (all parameters)", {OUT}];
  pn -> q -> fr -> el -> inc -> bin -> o;
}}'''

D["flow_sens"] = f'''digraph G {{ {COMMON} rankdir=TB;
  fl [label="flood run(s)\\n(thin PMMA, or water in a cell)", {IN}];
  db [label="direct-beam run\\n(to find the beam centre)", {IN}];
  c [label="beam centre (centre of mass)", {LD}];
  ld [label="load flood: geometry (offsets, scaleComponents)\\ncounts SUMMED over the whole band (no λ bins, no flux division)", {LD}];
  m [label="mask (mask file, bad pixels)\\n÷ solid angle", {PR}];
  bs [label="mask a circle around the beam centre\\n(radius, e.g. 40 mm)", {PR}];
  tr [label="[BIOSANS only] flood self-absorption (transmission) correction\\nnot available for EQSANS in drtsans", shape=box, style="filled,dashed", fillcolor="#ffffff", color="#9a9a9a", fontsize=10.5];
  pat [label="patch the masked centre: polynomial (order 2) along each tube", {PR}];
  thr [label="thresholds: pixels outside [min, max] × mean → masked (NaN)\\nnormalise to mean 1", {PR}];
  o [label="Sensitivity_*.nxs\\none number per pixel", {OUT}];
  db -> c -> ld; fl -> ld -> m -> bs -> tr -> pat -> thr -> o;
}}'''

for name, src in D.items():
    dot = os.path.join(HERE, name + ".dot")
    open(dot, "w").write(src)
    subprocess.run(["dot", "-Tpng", "-Gdpi=110", dot, "-o", os.path.join(HERE, name + ".png")], check=True)
    # tall diagrams are shown full width on the site: pad them onto a wider white canvas
    try:
        from PIL import Image
        png = os.path.join(HERE, name + ".png")
        im = Image.open(png)
        w, h = im.size
        target = 1.7 if name != "flow_process" else 1.25
        if w < target * h:
            W = int(target * h)
            canvas = Image.new("RGB", (W, h), "white")
            canvas.paste(im, ((W - w) // 2, 0))
            canvas.save(png)
    except ImportError:
        pass
    print("wrote", name + ".png")
