# Operating context

Reported repository context carried forward on 2026-09-20; live status was not rechecked.
Verify relevant config and printer state before relying on version, health, or calibration claims.
This reference is context, not an assignment to fix every listed issue.

## Project Overview

Klipper/Kalico firmware configuration for a CoreXY 3D printer ("Doomcube") with:
- **Happy Hare** v3.42 MMU plugin — BoxTurtle (4-lane) with AFC-Lite board, FPS analog sync feedback, tip cutting. **Live and printing** (since 2026-05-24); FPS psensor calibrated 2026-06-01. Analog cal values (`sync_feedback_analog_max_compression`/`_max_tension`/`_neutral_point`) live in `mmu_hardware.cfg` `[mmu_sensors]`; enable/buffer-range/multipliers in `mmu_parameters.cfg`. Neutral point is the calibration midpoint (0.0139) — see Known Quirks; a 2026-08-11 attempt to move it to the idle rest failed.
- **FPS** (Filament Pressure Sensor) board — CAN bridge replacing U2C, USB hub for AFC-Lite
- **Beacon** probe (contact mode with thermal expansion compensation)
- **KAMP** (Klipper Adaptive Meshing & Purging)
- **Spoolman** filament tracking — ⚠ HH↔Moonraker integration currently **broken**: `spoolman_push_gate_map` and `moonraker_push_lane_data` are not registered; every HH restart logs these errors.
- Sensorless homing on X/Y
- **A4T toolhead** (`custom/toolheads/A4T.cfg` is the active include; `xol.cfg` and `calamity.cfg` are inactive alternates)

## PRINT_START Flow

Beacon path (this printer's active config):

0. **Guard + early heat** (before homing): abort via `action_raise_error` if `HOTEND_TEMP < 150` (missing/cold-extrude protection); then `M140 S{bed_temp}` + `M104 S{warmup_hotend}` fired immediately so bed/hotend warm-up overlaps homing. On the Beacon path `warmup_hotend` = contact-cal temp (150 °C), not final print temp; PREHEAT (step 4) re-issues these idempotently.
1. Reset state: CLEAR_PAUSE, RESET_MULTIPLIERS, BED_MESH_CLEAR, zero Z offset, G90
2. Lights on, MAYBE_HOME
3. Save material to `save_variables`; `_SET_MPC_MATERIAL` if MPC active
4. PREHEAT — hotend goes to `BEACON_VARS.beacon_contact_calibration_temp` (150 °C), NOT the final print temp; bed/chamber per params; then SET_SLOW_CHAMBER_FAN_SPEED
5. `G28 Z METHOD=CONTACT CALIBRATE=1` — full Beacon model + Z offset, done hot
6. QUAD_GANTRY_LEVEL or Z_TILT_ADJUST (auto-detected; QGL here)
7. CALIBRATE_BED_MESH (adaptive scan + deviation validation)
8. CLEAN_NOZZLE (if the macro is defined — it is, in `mmu_macros.cfg`)
9. `G28 Z METHOD=CONTACT CALIBRATE=0` — final Z offset; then `M104` starts ramping hotend to print temp
10. `SET_VELOCITY_LIMIT ACCEL={travel_accel}` — limit accel for the travel section
11. Park (SMART_PARK if KAMP provides it, else PICK_PARK_LOCATION)
12. `M109` — wait for final hotend temp
13. `T{initial_tool}` if `gcode_macro T0` is defined (HH provides T0–T3); else "No MMU detected" and skip. There is no HH-specific startup sequence beyond this.
14. Park again post-toolchange
15. `_BEACON_SET_NOZZLE_TEMP_OFFSET` (thermal expansion compensation, if configured)
16. LINE_PURGE (called unconditionally — KAMP must be present; see Known Quirks)
17. `SET_VELOCITY_LIMIT ACCEL={saved_accel}` — restore full print accel
18. MAYBE_LOAD_SKEW_CORRECTION
19. `SAVE_VARIABLE VARIABLE=is_printing_gcode VALUE=True`, start print

Non-Beacon path differences (fleet machines): plain `G28 Z`, PREHEAT goes straight to final hotend temp, CLEAN_NOZZLE runs before leveling instead of after bed mesh.

## Known Quirks

- **SAVE_CONFIG overrides config-level heater control**: `control = pid` (or `mpc`) in the SAVE_CONFIG block takes priority over config files. Switching modes requires reconciling both config and the saved control value. The root prohibition on hand-editing SAVE_CONFIG still applies: use the supported calibration/save workflow; if manual removal is necessary, obtain an explicit exception before editing that block — just adding params won't expose the new mode's commands (e.g., `MPC_CALIBRATE` is unavailable while PID is active in SAVE_CONFIG). Current state: extruder `control = mpc`, bed `control = pid`.
- **`error_on_unused_config_options` is `True`** (flipped 2026-06-03 after MPC was calibrated + saved). Any newly-added unused config option will fault at restart.
- **Thermal-runaway protection** is explicit in `custom/sensors/verify_heater.cfg` (overrides Klipper's auto-generated defaults). Bed uses a longer `check_gain_time` (90s) so the slow 300mm@105°C bed doesn't false-trip.
- **Unattended pause thermal/timeout behavior** (preserve the deliberate timeout policy; this is not a safety certification):
  - MMU path (Happy Hare — the common runout/M600 trigger): hotend is cut by `mmu_parameters.cfg disable_heater` (600s / 10 min); bed + watercooled motors stay live until `timeout_pause` (43200s / 12h), then full shutdown. Bed is held hot this long deliberately to prevent warping.
  - Non-MMU path (fleet machines w/o HH): our PAUSE macro calls `SET_IDLE_TIMEOUT TIMEOUT={pause_idle_timeout}` (25200s / 7h); RESUME restores the configured `idle_timeout`. When idle_timeout fires it runs `CANCEL_PRINT` (everything off) per `[idle_timeout]` in `utils.cfg`.
  - `_PRINTER_VARS` `pause_standby_extruder_delta` / `pause_min_standby_temp` are still **unwired** (declared, not used) — the hotend is not dropped to a standby temp on pause, it's only cut by the timeout above.
- **HH hooks in our PAUSE/RESUME/CANCEL** (all behind `printer.mmu is defined and printer.mmu.enabled`):
  - PAUSE: `_MMU_SAVE_POSITION` → `PAUSE_BASE` → `_MMU_PARK OPERATION="pause"`. HH owns parking + position save/restore — do NOT add our own park/SAVE_GCODE_STATE in the MMU branch or it double-parks and corrupts the saved position.
  - RESUME: reheat + reapply Beacon offset while parked, then `RESUME_BASE`; HH restores the toolhead position itself. Do NOT restore position here.
  - CANCEL_PRINT: `MMU_TTG_MAP RESET=1 QUIET=1`.
- **`variable_user_post_load_extension: 'CLEAN_NOZZLE'`** in `mmu_macro_vars.cfg` calls our standalone CLEAN_NOZZLE macro after every tool load.
- **LINE_PURGE is called unconditionally** in PRINT_START — there is no fallback branch. `_FALLBACK_PURGE` exists in `utils.cfg` but is NOT wired in; removing KAMP would break PRINT_START.
- Spoolman integration config is in `custom/macros/spoolman.cfg`; see the reported status in Project Overview above.
- AFC's `trsync_update: False` — trsync values are managed globally in `[danger_options]` so they persist even if AFC is removed. `single_mcu_trsync_timeout` was raised to `1.0` (2026-08-11) to absorb transient AFC-Lite USB stalls during gear homing/preload (the board is on USB through the FPS hub; comms are otherwise healthy).
- **FPS sync-feedback neutral = calibration midpoint (0.0139); do NOT move it to the idle rest.** HH's `MMU_CALIBRATE_SYNC_FEEDBACK` sets `neutral_point = (max_compression + max_tension)/2`. On 2026-08-11 this was mistaken for a bug: the buffer's *idle* rest sits at the tension end (`value_raw ≈ 0.0064`), so neutral was moved there — this **broke printing** (severe under-extrusion, toolhead extruder fighting the BoxTurtle). Cause: with neutral at the tension stop, nearly every print sample reads as *compression*, so the loop continuously cuts gear feed and starves the extruder. The buffer floating near the tension end *during a print* is the control loop doing its job (a spring buffer that the gear keeps loaded), **not** a miscalibration — idle rest ≠ control setpoint. Reverted to `0.0139` (known-good since 2026-05). If sync feedback ever needs real tuning, adjust `max_compression`/`max_tension` and buffer multipliers, and judge by print quality, not by where the buffer parks at idle.
- **Cutter departure must clear the plunger in X before moving in Y.** The Crossbow A4T cutter pin is at Xmin/front (`pin_loc_xy ≈ 1,30.5`); after the cut the toolhead evacuates to ~`(1,25)`. `post_form_tip_position` is set to `60,25,5` (in `mmu_macro_vars.cfg`) so the departure is a pure +X move away from the plunger; sending it straight to a back park (e.g. `0,295`) diagonals through the plunger's Y band at X≈1 and strikes it (lost steps). Keep the post-cut Y near the cut row.
- The `dynamic_macros/` subdirectory under `macros/` is included via `custom/macros.cfg` as regular Klipper macros (no special module).
