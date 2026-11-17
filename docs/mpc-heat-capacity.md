# MPC filament heat capacity (fleet table)

Owner of the `capacity_map` in `_SET_MPC_MATERIAL` (Doomcube `custom/macros/utils.cfg`;
consumers K3D and Rat Race carry copies, kept equal by
`scripts/fleet/test_consumer_ports.py::MpcDensityPortTests`). Adopted 2026-11-16.

## What the value must be

Kalico `klippy/extras/control_mpc.py` (`_update_filament_const`, `temperature_update`):
filament loss = (block temp - filament temp) x extrude speed x pi r^2 x density x heat
capacity. `filament_temperature_source` defaults to `ambient`. So the value is the MEAN
specific heat from ambient to print temperature (enthalpy change / dT, including any
melting heat), not a room-temperature cp. Polymer cp rises about 50-60% from room
temperature to the melt and steps up at Tg.

Density is NOT in this table: the slicer profile's `filament_density` is its single owner
(`PRINT_START FILAMENT_DENSITY=`, fallback `[extruder] filament_density`).

## Table (J/g/K)

| Material | Old | Now | Basis | Confidence |
| --- | --- | --- | --- | --- |
| PLA | 1.80 | 1.95 | Pyda/Bopp/Wunderlich 2004 liquid Cp (120.17 + 0.076 T J/mol/K, 72.06 g/mol); glass ~1.2-1.3; mean 25->210 C ~1.92 | High |
| PETG | 1.17 | 1.75 | Eastman Eastar 6763 DSC: 1.30 @60, 1.76 @100, 1.88 @150, 1.97 @200, 2.05 @250 C; trapezoid mean 25->240 C = 1.73 | High (measured) |
| ABS | 2.00 | 1.80 | Glass to Tg ~105 C, melt ~2.0-2.1 at 240 C; integrated estimate | Medium |
| ASA | 1.30 | 1.80 | Same polymer family as ABS; INEOS Luran S melt cp 1.86 / 2.16 | Medium |
| ABS-MD-GF15 | (none, fell back) | 1.65 | 0.85 x 1.80 + 0.15 x 0.95 (glass, mean) | Medium |
| PC | 1.15 | 1.60 | Glass 1.2->1.55 to Tg 145 C, melt ~1.7-1.95; mean 25->270 C | Medium |
| PA / NYLON | 1.70 | 2.30 | Melt ~2.7; sensible mean ~2.2 + fusion (230 J/g x ~28% over 235 K) | Medium-low |
| PA-CF | 1.50 | 2.00 | 0.8 x 2.4 + 0.2 x 0.9 (carbon, mean) | Low-medium |
| PA-GF | 1.40 | 2.00 | 0.75 x 2.4 + 0.25 x 0.95; cross-check Ultramid B3EG6 melt 2.23 | Medium |
| PET-CF | 1.10 | 1.70 | PET matrix ~1.9 incl. fusion; 0.85 x 1.9 + 0.15 x 0.9 | Low-medium |
| PC-CF | 1.10 | 1.50 | 0.85 x 1.6 + 0.15 x 0.9 | Low-medium |
| TPU | 1.50 | 1.90 | Rubbery from room temperature; melt ~2.0-2.1 | Low |
| unknown | 1.50 | 1.80 | Most materials fall in 1.6-2.0 | - |

The old ABS/PLA/PETG values match Marlin `Configuration.h` MPC comments converted to
J/g/K (PLA 1.88, ABS 2.06, PETG 1.18) — room-temperature-ish figures. The old ABS 2.00 vs
ASA 1.30 split was an artefact of mixing a near-melt and a room-temperature value.

Assumptions: fibre mass fractions (CF 15-20%, GF 15-25%) and fibre mean cp (glass ~0.95,
carbon ~0.9) are estimates; check a specific filament's datasheet. PC, PA, TPU and
fibre values are partly from handbook values not re-fetched.

## Sensitivity

FFF power = flow x density x cp x dT. At 20 mm3/s, density 1.2, dT 215 K, a cp error of
0.5 is ~2.6 W of feed-forward. Steady state is corrected by feedback; the symptom is a
transient dip/overshoot at flow changes. +/-10% is within other model noise.

Physical validation (pending): a high-flow-change PETG print, extruder temperature trace
before vs after.

## Sources

- Kalico `klippy/extras/control_mpc.py`, `klippy/extras/heaters.py` (filament_temperature_source default), `docs/MPC.md` (note: it says g/mm^3; the code uses g/cm^3)
- Marlin `Configuration.h` MPC comments: https://raw.githubusercontent.com/MarlinFirmware/Marlin/bugfix-2.1.x/Marlin/Configuration.h
- Eastman Eastar 6763 datasheet: https://protolabs.com/media/pzub5tfo/eastar-6763.pdf
- INEOS Luran S 778T (CAMPUS): https://materialdatacenter.com/ms/en/Luran/INEOS+Styrolution/Luran®+S+778T/07a9fa55/345
- BASF Ultramid B3EG6 (CAMPUS): https://materialdatacenter.com/ms/en/Ultramid B/BASF+SE/Ultramid%C2%AE+B3EG6+UN/6da097e1/4337
- Pyda, Bopp, Wunderlich, J. Chem. Thermodyn. 2004 (PLA heat capacity)
- MatWeb ABS: https://www.matweb.com/search/DataSheet.aspx?MatGUID=eb7a78f5948d481c9493a67f0d089646
