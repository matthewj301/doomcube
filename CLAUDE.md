# Doomcube Klipper Configuration

## Project Overview

Klipper/Kalico firmware configuration for a CoreXY 3D printer ("Doomcube") with:
- **AFC** (Armored Turtle Filament Changer) multi-material system
- **Beacon** probe (contact mode with thermal expansion compensation)
- **KAMP** (Klipper Adaptive Meshing & Purging)
- **Spoolman** filament tracking integration
- Sensorless homing on X/Y

## Hardware Summary

- **Frame**: 300mm CoreXY
- **Steppers X/Y**: LDO-42STH48-2804AH on TMC5160 at 2.6A, 48V, 0.075Ω sense resistor
- **Steppers Z**: LDO-42STH48-2004AC on TMC2209, quad Z (Z/Z1/Z2/Z3)
- **Toolhead**: Xol-Metrix (M2 hardware flex concern — SnappingTurtle cutter replacement on order, ETA ~mid-2026)
- **Extruder**: Orbiter 2.0 (replaced LGX Lite Pro due to repeated motor thermal failures)
- **Hotend**: Chube Compact ("Teakettle" / tk) — high flow, proven 54+ mm³/s
- **Probe**: Beacon (contact mode)
- **MCU toolboard**: EBB36 (aliased as `toolboard_t0`)
- **AFC**: BoxTurtle (Turtle_1), 4 lanes, AFC Lite board, BTIO buffer board
- **Primary materials**: ABS/ASA

## Sensorless Homing Tuning

- Uses `tmc_autotune` module — SGT values set in `custom/tuning/tmc_autotune.cfg`, not in sensorless homing configs
- X motor connection: molex replaced with wagos (in-chamber) to fix intermittent connection issues
- Y homing from extreme front (Y≈0) is sensitive to SGT threshold — too low causes false StallGuard triggers during long travel
- tmc_autotune recommends higher homing speeds; tune SGT before reducing speed
- `home_current` is intentionally commented out — user prefers homing at full run current

## AFC Notes

- BTIO buffer board has different pin mapping than stock TurtleNeck — `TN_ADV`/`TN_TRL` labels may not match advance/trailing function
- Bowden length is 1885mm (hub to toolhead) — long path, calibration-sensitive
- `AFC_Macro_Vars.cfg` brush/park/poop locations must respect `position_max` (300 for both X/Y) — brush_loc + brush_depth/2 must stay within bounds
- Lane 1 has intermittent sensor issues (shows not ready when lanes 2-4 are fine)
- Hub cutter hardware is present but disabled (`cut: False`) — user has mixed past experience with hub cutting reliability

## Extruder Notes

- **Orbiter 2.0** is the active extruder (replaced LGX Lite Pro due to repeated Bondtech motor thermal failures)
- Orbiter 2.0 confirmed working well both with and without AFC
- LGX Lite Pro config retained in `custom/extruders/lgx_lite_pro.cfg` but no longer included
- Flow rate limit is primarily hotend melt capacity, not extruder — do not assume extruder specs limit flow
- Sherpa Mini on K3 reliably pushes 70mm³/s; Chube Compact is the enabler
- Do not cite generic extruder flow limits without real-world context

## Directory Structure

```
printer.cfg                  # Main config — includes everything, defines _PRINTER_VARS
├── custom/
│   ├── macros.cfg           # [include macros/*.cfg]
│   ├── macros/
│   │   ├── print.cfg        # PRINT_START, PRINT_END, PAUSE, RESUME, CANCEL_PRINT, M600
│   │   ├── park.cfg         # _PARK (parameterized X/Y), PICK_PARK_LOCATION
│   │   ├── homing.cfg       # MAYBE_HOME, _CENTER_AXIS, safe homing helpers
│   │   ├── heating_cooling.cfg  # PREHEAT, COOLDOWN_SEQUENCE
│   │   ├── fans.cfg         # Chamber/bed/filter/part-cooling fan macros
│   │   ├── utils.cfg        # MAYBE_LOAD_SKEW_CORRECTION, _FALLBACK_PURGE, idle_timeout, motor helpers
│   │   ├── thermal_expansion_compensation.cfg  # Beacon nozzle thermal expansion (from YanceyA/BeaconPrinterTools)
│   │   ├── spoolman.cfg     # Spoolman integration
│   │   ├── fast_QGL.cfg     # Fast quad gantry level
│   │   └── dynamic_macros/
│   │       └── toolhead_assisted_chamber_heating.cfg  # TA_CHAMBER_HEAT
│   ├── dynamic_macros.cfg   # [include dynamic_macros/*.cfg] — loaded via dynamic_macros Klipper module
│   ├── default_includes.cfg # [respond], [pause_resume], [display_status], [exclude_object], [save_variables]
│   ├── doomcube/            # Machine-specific: limits, steppers, bed_mesh, QGL, sensorless homing
│   ├── toolheads/           # Toolhead config (currently xol.cfg)
│   ├── extruders/           # Extruder config (active: orbiter_2.0.cfg)
│   ├── fans/                # Hardware fan definitions ([fan_generic], [controller_fan], etc.)
│   ├── leds/                # LED definitions
│   ├── sensors/             # Temperature sensors (chamber thermistor, etc.)
│   ├── mcus/                # MCU board definitions
│   ├── tuning/              # Input shaper, pressure advance tuning results
│   └── probes/              # Probe hardware config
├── AFC/                     # Armored Turtle Filament Changer plugin (DO NOT MODIFY — see below)
├── KAMP/                    # Klipper Adaptive Meshing & Purging (DO NOT MODIFY — see below)
└── KAMP_Settings.cfg        # User-owned KAMP configuration
```

## Critical Rules

### Files we OWN (safe to edit)
- Everything under `custom/`
- `printer.cfg` (the `_PRINTER_VARS` section and includes)
- `KAMP_Settings.cfg`
- `AFC/AFC_Macro_Vars.cfg` (user-owned AFC variable overrides)

### Files we DO NOT modify
- **`AFC/` macro files** — Overwritten by AFC plugin updates via moonraker. Changes will be lost. `AFC_Macro_Vars.cfg` is the only user-owned file.
- **`KAMP/` files** — Symlinked/managed by moonraker. Changes will be lost.
- **`#*# SAVE_CONFIG` block** in printer.cfg — Auto-generated by Klipper.

### Do NOT use `rename_existing` wrappers for external macros
The user explicitly rejected wrapping AFC/KAMP macros with `rename_existing`. Instead, use `SET_VELOCITY_LIMIT` in the orchestrating macro (PRINT_START) to control acceleration before/after calling external macros.

## Architecture & Conventions

### Central Configuration: `_PRINTER_VARS`
All user-tunable settings live in `_PRINTER_VARS` (printer.cfg). Macros read from this via:
```jinja2
{% set vars = printer["gcode_macro _PRINTER_VARS"] %}
```

### Variable Naming Convention (standardized)
- Speeds: `travel_speed`, `z_speed`, `z_travel_speed`, `move_speed`, `retract_speed` (all mm/s)
- Temps: `hotend_temp`, `bed_temp`, `chamber_target_temp`
- Macro parameters: `HOTEND_TEMP`, `BED_TEMP`, `TARGET_CHAMBER_TEMP`, `MATERIAL`, `TOOL`
- Fan names: `filter_fan`, `chamber_fan`, `bed_fan`
- Feedrates in G-code: Always convert mm/s to mm/min at point of use: `(speed|float * 60)|int`

### Acceleration Management Pattern
All macros making travel moves must save/set/restore acceleration:
```jinja2
{% set travel_accel = vars.travel_accel|float %}
{% set saved_accel = printer.toolhead.max_accel %}
SET_VELOCITY_LIMIT ACCEL={travel_accel}
# ... G0/G1 moves ...
SET_VELOCITY_LIMIT ACCEL={saved_accel}
```
System `max_accel` is 15,000 mm/s² (in limits.cfg). `travel_accel` is 4,000 mm/s².

### Jinja2 Template Timing
All `{% set %}` variables evaluate BEFORE any G-code executes. You cannot read runtime state that changes mid-macro. `printer.toolhead.max_accel` captured at template expansion reflects the value at macro call time.

### Boolean Variables from Klipper
Klipper stores `True`/`False` as strings. Always use:
```jinja2
{% set flag = true if value|default(false)|lower == 'true' else false %}
```
Never rely on bare truthiness — non-empty strings (including `"False"`) are truthy in Jinja2.

### Klipper Macro Notes
- Macro names are **case-insensitive** (`CASE_LIGHTS_ON` == `case_lights_on`)
- Last definition wins for duplicate macro names (include order matters)
- `[danger_options]` indicates this is **Kalico** (not stock Klipper)

## PRINT_START Flow

1. Clear state (CLEAR_PAUSE, RESET_MULTIPLIERS, BED_MESH_CLEAR, zero Z offset)
2. G90, lights on, MAYBE_HOME
3. Save material to variables
4. PREHEAT (bed + hotend, chamber fans, optional TA_CHAMBER_HEAT for high-temp materials)
5. Clean nozzle (if CLEAN_NOZZLE macro exists)
6. Beacon Z calibration (if Beacon present)
7. QGL or Z_TILT_ADJUST (auto-detected)
8. BED_MESH_CALIBRATE ADAPTIVE=1
9. MAYBE_LOAD_SKEW_CORRECTION
10. Final Beacon Z calibration
11. SET_VELOCITY_LIMIT ACCEL={travel_accel} — limit accel for travel section
12. Park (AFC_PARK → SMART_PARK → PICK_PARK_LOCATION fallback)
13. Heat hotend to final temp, load tool
14. Park again post-toolchange
15. Beacon thermal expansion compensation (if configured)
16. LINE_PURGE
17. SET_VELOCITY_LIMIT ACCEL={saved_accel} — restore full print accel
18. Start print

## Known Quirks

- `variable_skew_profile` is defined AFTER `gcode:` in `_PRINTER_VARS` (line 61). In Klipper, variables must be before the `gcode:` line. This may need to be moved up if skew loading fails at runtime.
- `_FALLBACK_PURGE` is only used if KAMP's `LINE_PURGE` is not available.
- AFC's `AFC_ENABLE_SKEW` / `AFC_DISABLE_SKEW` macros handle skew during tool changes independently.
- The `dynamic_macros` directory uses a Klipper module that allows runtime macro reloading.
