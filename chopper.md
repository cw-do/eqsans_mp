# EQSANS chopper system — 6-chopper upgrade (2026B)

## Overview

Starting in the **2026B** cycle (IPTS-37618), EQSANS was upgraded from a
**4-chopper** to a **6-chopper** system. The two added disks (the "a" disks at
stations 1 and 2) let each of the three stations define **both** edges of the
transmitted wavelength band, which enables a new **monochromatic beam** mode in
addition to the standard bandwidth (white-beam / TOF) mode.

Both the chopper-to-moderator distances and the per-disk **phase offsets**
changed with the upgrade; the disk **opening angles** did not.

## Chopper reference — the finalized values

**This is the final answer.** These distances and phase offsets were finalized
in March 2026 (W. Heller, C. Do, M. Backman, B. Krishna) and are the values
deployed in the drtsans configuration
(`EQSANS_chopper_configurations.json`). Order is the array order used by that
JSON and by the reduction code (array indices 0–5); the *EPICS index* is the
1-based chopper number.

| array idx | EPICS index | Chopper | Distance to source (m) | Opening angle (°) | Phase offset (µs) |
|----------:|:-----------:|:-------:|-----------------------:|------------------:|------------------:|
| 0 | 1 | **1b** | 5.6757668 | 129.600 | 14954.46 |
| 1 | 2 | **2b** | 7.7757668 | 180.000 | 14805.40 |
| 2 | 3 | **3a** | 9.4978    | 230.010 | 14726.06 |
| 3 | 4 | **3b** | 9.5078    | 230.007 | 14565.69 |
| 4 | 5 | **1a** | 5.6601247 | 129.600 | 15072.89 |
| 5 | 6 | **2a** | 7.7601247 | 180.000 | 14834.04 |

- Stations pair up as **1a + 1b** (idx 4, 0), **2a + 2b** (idx 5, 1) and
  **3a + 3b** (idx 2, 3).
- The phase offsets are the per-disk calibration constants added to the
  computed phase (the JSON `offsets`). The 30 Hz frame-skip offsets are twice
  these (the JSON `skip` values).
- **Choppers 1a (EPICS index 5) and 2a (index 6) are not currently running**
  because of the heat load they create. With the two upstream "a" disks off,
  full monochromatic operation is limited.

### Naming — this table is authoritative

The disk labels above (**1b, 2b, 3a, 3b, 1a, 2a** in array order) are the
finalized convention and match the chopper engineer's physical naming
(B. McHargue): the new/upstream disk at each of stations 1 and 2 is the **"a"**
disk (e.g. `1a` at 5.6601247 m, 15.6421 mm upstream of `1b` at 5.6757668 m).

Beware: the C source comments in `hexaSub.c` (`chopper 1A (1)`, `chopper 1B (5)`,
…) label the **stations-1 and -2 disks with the opposite a/b sense** — they call
array index 0 "1A" when it is physically **1b**. The compiled *numbers* in that
file are correct (they match this table); only the comment labels are wrong.
That mislabeling is the source of the long-running "chopper naming confusion."
Station 3 (3a/3b) is consistent everywhere.

## How drtsans uses these (Y. Shang, 2026-03-13)

The EQSANS chopper module is a hybrid:

- **From the run logs** (`SampleLogs`): the chopper **speeds, phases**, and
  pulse **frequency** (`Speed1`, `Phase1`, `frequency`, …).
- **From `EQSANS_chopper_configurations.json`**, selected by **run start date**:
  the number of choppers, opening angles, **distances to source**, and the
  **skip / not-skip phase offsets** — i.e. the values in the table above. They
  are *not* read from the NeXus metadata.

The code distinguishes the pre-2026 4-chopper configuration from the 2026
6-chopper configuration by date (drtsans PR #1094, *"Use different EQSANS
chopper configuration depending on the experiment date"*; JSON + `chopper.py`
added 2026-02-16).

- Config JSON: `src/drtsans/configuration/EQSANS_chopper_configurations.json`
- Module: `src/drtsans/tof/eqsans/chopper.py`

Because reduction picks the JSON entry by date, **the entry that applies to a
run must carry the finalized values above**. A JSON entry with different
distances/offsets (see *Open issues*) produces bad wavelength center/spread.

## Physical geometry (B. McHargue, 2026-03-10)

- Each of **stations 1 and 2** gained a second disk; the two disks of a station
  are **15.6421 mm** apart. The new **"a"** disk is the upstream one (smaller
  distance to source), the reused **"b"** disk (previous chopper mount) is
  downstream. Relative to the single previous chopper, the "a" disk is
  **42.6753 mm** and the "b" disk **27.0332 mm** upstream.
- **Station 3**'s two disks are **14.0468 mm** apart and remain in their
  previous physical locations.
- The **1b** and **3a** disks are monitored by infrared thermocouples (IR TC).

## Operation algorithm

Chopper phases are computed by the beamline IOC **`bl6-SkfChopper`**, in the
EPICS aSub routines in `bl6-SkfChopperApp/src/hexaSub.c` — `calc6Phases`
(wavelength → phases) and `calc6Wavelengths` (phases → transmitted band). Both
are C ports of `calcChopperByStartingWavelength()` and `calcBandWidth()` from
`eqsans_scans.py`; the monochromatic branch was added 2026-03-07. *(The a/b
comment labels in that file are swapped for stations 1 and 2 — see above.)*

### Neutron kinematics

```
TOF [s] = L * λ / 3.956e6            # 3.9560346 mm·Å/µs  (= h / m_n)
bandwidth_60Hz [Å] = 3.956e6 / detector_location / 60
```

`detector_location` is the moderator-to-detector flight path in mm
(≈ moderator distance + SDD), with a small corner-pixel correction.

### Building each disk phase

For a disk, the phase is the TOF at which the chosen band edge reaches it,
shifted to the **center** of the opening, plus the disk's calibration offset,
wrapped into one frame:

```
phase  = L * λ_edge / 3.956e6                 # TOF to the disk for the edge wavelength
phase ±= (opening_angle / 360) / speed / 2    # from the edge to the aperture center
phase  = 1e6 * phase + phase_offset           # to µs, add the disk's offset
phase  = phase mod (1e6 / speed)              # wrap into one frame
```

The three disks that define the **short-λ** edge use the opening edge (`+`); the
three that define the **long-λ** edge use the closing edge (`−`).

- **Bandwidth (60 Hz):** `wl1 = start_λ`, `wl2 = wl1 + bandwidth_60Hz`, with a
  `λ > 13 Å` vs `≤ 13 Å` branch to suppress leakage.
- **Monochromatic (60 Hz, new):** `wl1 = λ₀(1 − spread/2)`,
  `wl2 = λ₀(1 + spread/2)`, requiring `spread·λ₀ ≤ bandwidth_60Hz`. Each station
  brackets the band — one disk opens at `wl1`, its partner closes at `wl2`.
  60 Hz only (no frame-skip).
- **Frame-skip (30 Hz):** two bands per skipped pulse; **SDD ≤ 5 m** required.

`calc6Wavelengths` inverts this: from the six set phases it recovers each disk's
open/close edge wavelengths and returns the transmitted band (its center and
spread) — the quantity reduction needs.

## Configuration snapshots

`EQSANS_chopper_configurations.json` carries dated entries. The finalized set
above corresponds to this entry (array order; `aperture` = opening angle in
degrees):

**Finalized values (deployed) — `to_source`/`offsets` matching the table above**
```
aperture:  [129.600, 180.000, 230.010, 230.007, 129.600, 180.000]
to_source: [5.6757668, 7.7757668, 9.4978, 9.5078, 5.6601247, 7.7601247]
not_skip:  [14954.46, 14805.40, 14726.06, 14565.69, 15072.89, 14834.04]
skip:      [29908.92, 29610.80, 29452.12, 29131.38, 30145.78, 29668.08]
```

A separate entry with **different** distances and offsets
(`to_source ≈ [5.6978, 7.7978, …]`, `not_skip = [14640.1, 14533.6, …]`) also
exists in the file. It does **not** match the finalized values and is the cause
of the bad monochromatic wavelengths below — reduction selects it by date for
recent runs. The fix is to make the applicable entry match the table above.

## Open issues — monochromatic-mode reduction

Seen on monochromatic runs **186204–186280** (autoreduction failures, reported
2026-08-07):

- With the finalized offsets/distances (the table above) drtsans reproduces the
  requested wavelength center/spread, checked against processing variables
  **MCWL16** (center) and **MCWLSpread16** (spread). With the mismatched entry
  it returns unreliable values.
- drtsans returns a slightly **smaller center wavelength** than MCWL16 —
  expected: it accounts for the moderator emission delay.
- drtsans returns a slightly **wider spread** than requested (no confirmed
  explanation yet).
- **TOF clipping must be disabled in monochromatic mode** — the default
  clippings remove the entire wavelength band.
- **Interim workaround:** use the finalized chopper entry, or override drtsans
  with the MCWL16 / MCWLSpread16 values.

## Sources

- **Finalized values:** table from W. Heller / C. Do, confirmed by M. Backman as
  the values added to drtsans in March 2026 (thread *"drtsans code"*,
  2026-03-16); to be recorded in the instrument electronic notebook as the final
  answer.
- drtsans mechanism: Y. Shang (2026-03-13); config
  `src/drtsans/configuration/EQSANS_chopper_configurations.json`, module
  `src/drtsans/tof/eqsans/chopper.py`, PR #1094.
- IOC algorithm: `bl6-SkfChopper` — `bl6-SkfChopperApp/src/hexaSub.c`
  (`calc6Phases`, `calc6Wavelengths`).
- Geometry & naming: B. McHargue (2026-03-10, 2026-08-10); threads
  *"potential chopper naming confusion"* and *"Autoreduction errors."*
