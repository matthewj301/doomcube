# Kalico Configuration Audit — Portable Findings

Findings from a deep audit of a Kalico CoreXY printer config. These apply to any Kalico printer with similar hardware (Beacon probe, TMC drivers, CPAP fan). Items are grouped by category with exact config syntax.

---

## Kalico Features to Enable

### `limited_corexy` kinematics (stable)
Enables independent per-axis acceleration limits. X and Y often have different mass/stiffness — input shaper data usually confirms this. `scale_xy_accel` dynamically decomposes diagonal moves so neither axis exceeds its individual limit.

```ini
# In your kinematics config:
[printer]
kinematics: limited_corexy
max_accel: 60000
max_x_accel: 60000       # tune per-axis after Shake&Tune
max_y_accel: 60000
scale_xy_accel: True

# Start equal, then tune independently based on AXES_SHAPER_CALIBRATIONS results.
```

### MPC extruder temperature control (stable)
Replaces PID with model-predictive control. PID is tuned at a single target temp — MPC models the heater/sensor/environment system and anticipates temperature changes from flow rate. One calibration covers all temperatures.

```ini
# In your hotend config:
[extruder]
control: mpc
heater_power: <nameplate_watts>    # e.g., 70, 100, 120
cooling_fan: fan                    # your part cooling fan name
filament_diameter: 1.75
filament_density: 1.07              # default material (g/cm3)
filament_heat_capacity: 1.30        # default material (J/g/K)
```

**Deployment:** Run `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7` then `SAVE_CONFIG`. The SAVE_CONFIG block replaces PID values with MPC calibration data.

**Per-material adjustment:** Call `MPC_SET` in PRINT_START to set filament properties based on material type. Reference values:

| Material | Density (g/cm3) | Heat Capacity (J/g/K) |
|----------|----------------:|----------------------:|
| PLA      | 1.24            | 1.80                  |
| ABS      | 1.04            | 2.00                  |
| ASA      | 1.07            | 1.30                  |
| PETG     | 1.27            | 1.17                  |
| PET-CF   | 1.35            | 1.10                  |
| PC       | 1.20            | 1.15                  |
| PC-CF    | 1.30            | 1.10                  |
| PA/Nylon | 1.14            | 1.70                  |
| PA-CF    | 1.30            | 1.50                  |
| PA-GF    | 1.40            | 1.40                  |
| TPU      | 1.21            | 1.50                  |

Example macro:
```ini
[gcode_macro _SET_MPC_MATERIAL]
gcode:
  {% set material = params.MATERIAL|default("PLA")|upper %}
  {% set density_map = {
    "PLA": 1.24, "ABS": 1.04, "ASA": 1.07,
    "PETG": 1.27, "PET-CF": 1.35,
    "PC": 1.20, "PC-CF": 1.30,
    "PA": 1.14, "NYLON": 1.14, "PA-CF": 1.30, "PA-GF": 1.40,
    "TPU": 1.21,
  } %}
  {% set capacity_map = {
    "PLA": 1.80, "ABS": 2.00, "ASA": 1.30,
    "PETG": 1.17, "PET-CF": 1.10,
    "PC": 1.15, "PC-CF": 1.10,
    "PA": 1.70, "NYLON": 1.70, "PA-CF": 1.50, "PA-GF": 1.40,
    "TPU": 1.50,
  } %}
  {% set density = density_map[material] if material in density_map else 1.20 %}
  {% set capacity = capacity_map[material] if material in capacity_map else 1.50 %}
  MPC_SET HEATER=extruder FILAMENT_DENSITY={density} FILAMENT_HEAT_CAPACITY={capacity}
```

### `adaptive_horizontal_move_z` for z_tilt_ng (stable)
Automatically reduces probe travel height after the first leveling pass based on measured error. Eliminates the need for manual `HORIZONTAL_MOVE_Z` overrides in multi-pass z-tilt macros.

```ini
[z_tilt_ng]
adaptive_horizontal_move_z: True
```

If using a two-pass fast z-tilt macro, you can remove `HORIZONTAL_MOVE_Z` overrides — Kalico handles it:
```ini
[gcode_macro Z_TILT_ADJUST]
rename_existing: BASE_Z_TILT_ADJUST
gcode:
    BASE_Z_TILT_ADJUST RETRY_TOLERANCE=1
    BASE_Z_TILT_ADJUST
```

### `BED_MESH_CHECK` (stable)
Validates mesh quality after calibration. Catches warped build plates or failed probing before a print starts.

```ini
# Macro wrapping mesh + validation:
[gcode_macro CALIBRATE_BED_MESH]
gcode:
  {% set vars = printer["gcode_macro _PRINTER_VARS"] %}
  {% set max_deviation = params.MAX_DEVIATION|default(vars.max_mesh_deviation)|float %}
  BED_MESH_CALIBRATE
  BED_MESH_CHECK MAX_DEVIATION={max_deviation}
```

Add `variable_max_mesh_deviation: 0.200` to your `_PRINTER_VARS`.

### `multi_mcu_trsync_timeout` in danger_options (stable)
Default is 0.025s. Multi-MCU setups (main board + toolboard + RPi) benefit from 0.05s to prevent spurious "communication timeout during homing" errors.

```ini
[danger_options]
multi_mcu_trsync_timeout: 0.05
```

### Smooth input shapers (bleeding edge)
`smooth_mzv` provides better vibration cancellation than standard `mzv`. Key differences from standard shapers:
- Frequency parameter is `smoother_freq_x` / `smoother_freq_y` (not `shaper_freq_*`)
- Damping ratios are NOT supported — remove `damping_ratio_*` lines when switching
- Retune via Shake&Tune after switching

```ini
[input_shaper]
shaper_type_x: smooth_mzv
smoother_freq_x: 119.2       # retune after switching
shaper_type_y: smooth_mzv
smoother_freq_y: 83.2        # retune after switching
```

---

## Beacon Contact Mode Recommended Settings

If using Beacon RevH with contact probing, add these beyond the minimal config:

```ini
[beacon]
home_method: contact
home_method_when_homed: proximity     # faster re-homes when already homed
home_autocalibrate: unhomed           # autocal on cold start only
home_z_hop_speed: 30
home_xy_move_speed: 300
autocal_speed: 3
autocal_sample_count: 3
autocal_tolerance: 0.008
autocal_max_retries: 3
```

`home_method_when_homed: proximity` speeds up mid-print re-homes. Explicit `G28 Z METHOD=CONTACT` in PRINT_START overrides this when contact is needed.

### Thermal expansion compensation safety
If using BeaconPrinterTools thermal expansion compensation, add a bounds check before applying the offset. Clamp to a max value and warn instead of crashing the nozzle:

```jinja2
{% set expansion_offset = multiplier * (temp_offset * (coefficient / 100)) %}
{% set max_offset = printer["gcode_macro _PRINTER_VARS"].max_thermal_offset|default(0.1)|float %}
{% if expansion_offset|abs > max_offset %}
  RESPOND TYPE=error MSG={"'Thermal offset %.4fmm exceeds limit — clamping'" % (expansion_offset)}
  {% set expansion_offset = max_offset if expansion_offset > 0 else -max_offset %}
{% endif %}
```

---

## TMC Autotune

### Don't forget the extruder
TMC Autotune configs commonly include XY and Z steppers but miss the extruder. Add it:

```ini
[autotune_tmc extruder]
motor: <your_motor_from_database>     # e.g., moons-cse14hra1l410a
tuning_goal: auto                     # resolves to silent for extruders
voltage: 24
```

Check the motor database for your motor: https://github.com/andrewmcgr/klipper_tmc_autotune/blob/main/motor_database.cfg

### `overvoltage_vth`
This is optional (defaults to disabled). The "measured voltage + 0.8V" recommendation in the README is specifically for BTT SB2240 toolhead boards. For 48V TMC5160 setups, a value like 58V is reasonable — it activates the overvoltage snubber only for significant regen braking spikes.

---

## CPAP Fan Configuration

CPAP blowers need two settings that the default `[fan]` config lacks:

```ini
[fan]
kick_start_time: 0.5    # full-power burst to spin up centrifugal impeller
off_below: 0.15          # below 15% duty, turn off instead of stalling
```

Tune `off_below` to your specific blower — test the minimum PWM that reliably spins the fan.

Note: `min_power` does NOT exist as a Klipper `[fan]` parameter. Use `off_below`.

---

## PAUSE/RESUME Thermal Offset

If using Beacon thermal expansion compensation, re-apply the offset on RESUME after reheating. During pause, hotend drops to standby temp but the offset stays calibrated for print temp. After `M109` restores print temp in RESUME:

```jinja2
{% if printer.configfile.config["gcode_macro _BEACON_SET_NOZZLE_TEMP_OFFSET"] is defined %}
  _BEACON_SET_NOZZLE_TEMP_OFFSET
{% endif %}
```

---

## Chamber Heating Safety

If using recursive toolhead-assisted chamber heating, add a max iteration counter to prevent infinite loops when the target is unreachable:

- Add `variable_chamber_heat_max_cycles: 300` to `_PRINTER_VARS`
- Pass `REMAINING={max_cycles}` from the orchestrator to the cycle macro
- Decrement on each recursion: `REMAINING={remaining - 1}`
- Bail at zero with an error message instead of looping forever

---

## COOLDOWN_SEQUENCE

If you have a COOLDOWN_SEQUENCE macro for stepped bed cooldown (warp-prone materials), make sure it's actually called in PRINT_END. A common pattern is having it commented out during debugging and forgetting to re-enable it. When active, remove the standalone `TURN_OFF_HEATERS` and `ALL_FANS_OFF` calls since COOLDOWN_SEQUENCE handles those internally.

---

## M600 Color Change

Make M600 defensive about what filament management system is available:

```ini
[gcode_macro M600]
gcode:
  PAUSE
  {% if printer.configfile.config["gcode_macro MMU_EJECT"] is defined %}
    MMU_EJECT
  {% elif printer.extruder.can_extrude %}
    G91
    G1 E-50 F300
    G90
  {% endif %}
```

---

## Common Mistakes

- **`hold_current` on TMC drivers**: Klipper docs explicitly warn against this — "changing motor current may itself introduce motor movement." Don't set it.
- **`min_power` on fans**: Not a valid Klipper parameter. Use `off_below` for `[fan]`.
- **motors_sync `microsteps`**: This is the sync procedure's stepping resolution, NOT the motor driver microstep setting. It does not need to match your stepper config. Values above 16 are not recommended for GT2 20T pulleys.
- **`z_positions` vs `points` in z_tilt_ng**: These are separate concepts. `z_positions` = lead screw physical locations. `points` = where the probe measures. Both are required.
- **`high_precision_step_compress`**: This is a bleeding edge feature requiring recompiled firmware with the option enabled in menuconfig. It is NOT a stable config-only option.
