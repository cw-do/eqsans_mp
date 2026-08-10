# EQSANS chopper system — 6-chopper upgrade (2026B)

## Overview

Starting in the **2026B** cycle (IPTS-37618), EQSANS was upgraded from a
**4-chopper** to a **6-chopper** system. The two added disks — the "A" disks at
stations 1 and 2 — enable a **monochromatic beam** setting in addition to the
standard bandwidth (white-beam / TOF) mode.

Because the chopper array changed, both the instrument geometry (each disk's
distance to the moderator) and the chopper **phase offsets** in
`EQSANS_chopper_configurations.json` changed. The **aperture** sizes did not
change.

## Chopper reference (effective 2026B onward)

The six disks, in the order used by `EQSANS_chopper_configurations.json`
(array indices 0–5):

| idx | Disk (physical) | EPICS-order label | Distance to source (m) | Aperture (mm) | Phase, not-skip | Phase, skip |
|----:|:--------------:|:-----------------:|-----------------------:|--------------:|----------------:|------------:|
| 0 | **1B** | 1A | 5.6757668 | 129.600 | 14640.1 | 29280.2 |
| 1 | **2B** | 2A | 7.7757668 | 180.000 | 14533.6 | 29067.2 |
| 2 | **3A** | 3A | 9.4978    | 230.010 | 14620.9 | 29241.8 |
| 3 | **3B** | 3B | 9.5078    | 230.007 | 14509.0 | 29018.0 |
| 4 | **1A** | 1B | 5.6601247 | 129.600 | 14525.1 | 29050.2 |
| 5 | **2A** | 2B | 7.7601247 | 180.000 | 14536.3 | 29072.6 |

- **Distances** are the measured values confirmed by B. McHargue (2026-08-10).
  In the 2026-03-04 config the station-1 and station-2 distances were interim
  estimates (`5.6978, 7.7978, …, 5.7078, 7.8078`) and were replaced by these
  measured values. The station-3 distances (indices 2, 3) never changed.
- **Phase offsets** (`not_skip`, `skip`) shown are the **2026-03-04** set from
  `EQSANS_chopper_configurations.json` (daystamp 20260304), listed in the same
  array order as the distances. See *Open issues* below — for monochromatic
  reduction these 2026-03-04 phases are currently suspect.

### Naming caveat (read this before configuring reduction)

There are **two labelings of the same array**:

- **Physical disk name** (chopper engineer / McHargue): `1B, 2B, 3A, 3B, 1A, 2A`
- **EPICS channel order** (as the team had been using): `1A, 2A, 3A, 3B, 1B, 2B`

For **stations 1 and 2 the A/B labels are swapped** between the two
conventions; station 3 agrees. The physical naming is anchored in geometry: at
each of stations 1 and 2 the new **A** disk sits slightly **upstream** (closer
to the moderator, smaller `to_source`) of the **B** disk. Array index 4
(`5.6601247 m`) is 15.6421 mm upstream of index 0 (`5.6757668 m`), so index 4
is **1A** and index 0 is **1B** — which is the difference McHargue quotes.
Always state which convention you mean.

## Physical geometry (B. McHargue, 2026-03-10)

**Station 1**
- **1A** — new chopper/disk in a new physical location.
- **1B** — on the previous chopper-1 mount and orientation; this disk is
  monitored by an infrared thermocouple (IR TC).
- 1A disk center is **15.6421 mm upstream** of 1B.
- 1A is **42.6753 mm upstream** of the previous chopper-1 disk; 1B is
  **27.0332 mm upstream** of the previous chopper-1 disk.

**Station 2** (identical offsets to station 1)
- **2A** — new chopper/disk, new location; **2B** — on the previous chopper-2
  mount.
- 2A is **15.6421 mm upstream** of 2B; 2A is **42.6753 mm** and 2B is
  **27.0332 mm** upstream of the previous chopper-2 disk.

**Station 3** (unchanged locations)
- **3A** and **3B** remain in the same physical locations as before; the **3A**
  disk is monitored by an IR TC.
- 3A disk center is **14.0468 mm upstream** of 3B.

## Configuration snapshots

`EQSANS_chopper_configurations.json` carries dated entries. The two relevant to
the 6-chopper era (array order = indices 0–5 above):

**daystamp 20260101** — measured distances; gives sensible monochromatic reduction
```
aperture:  [129.600, 180.000, 230.010, 230.007, 129.600, 180.000]
to_source: [5.6757668, 7.7757668, 9.4978, 9.5078, 5.6601247, 7.7601247]
not_skip:  [14954.46, 14805.4, 14726.06, 14565.69, 15072.89, 14834.04]
skip:      [29908.92, 29610.8, 29452.12, 29131.38, 30145.78, 29668.08]
```

**daystamp 20260304** — interim distances for stations 1 & 2; updated phases
```
aperture:  [129.600, 180.000, 230.010, 230.007, 129.600, 180.000]
to_source: [5.6978, 7.7978, 9.4978, 9.5078, 5.7078, 7.8078]
not_skip:  [14640.1, 14533.6, 14620.9, 14509.0, 14525.1, 14536.3]
skip:      [29280.2, 29067.2, 29241.8, 29018.0, 29050.2, 29072.6]
```

Only the chopper-to-moderator distances and the phase offsets change between
entries; the apertures are constant.

## Open issues — monochromatic-mode reduction

Seen on monochromatic runs **186204–186280** (autoreduction failures, reported
2026-08-07):

- With the **20260304** chopper settings, drtsans computes unreliable
  wavelength center/spread. With the **20260101** settings it reproduces the
  requested values well, checked against the processing variables **MCWL16**
  (center) and **MCWLSpread16** (spread).
- drtsans returns a slightly **smaller center wavelength** than MCWL16 —
  expected: it accounts for the moderator emission delay (neutrons must travel
  a little faster to reach the choppers on time).
- drtsans returns a slightly **wider spread** than the requested MCWLSpread16
  (no confirmed explanation yet).
- **TOF clipping must be disabled in monochromatic mode** — applying the
  default TOF clippings removes the entire wavelength band.
- **Interim workaround** for monochromatic reduction: use the 20260101 chopper
  settings, or override drtsans with the MCWL16 / MCWLSpread16 processing
  variables.

## Sources

Email threads *"Autoreduction errors"* (2026-08-07 → 2026-08-10) and
*"potential chopper naming confusion"* (2026-03-10): B. McHargue (neutron
choppers engineer), W. Heller, J. Borreguero, C. Do, Y. Shang, G. Nagy.
