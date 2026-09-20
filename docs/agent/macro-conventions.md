# Macro conventions

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
Macro variables may be typed booleans: the inspected Kalico source parses
`variable_*` using `ast.literal_eval`. String inputs such as parameters still need
normalization; the non-empty string `"False"` is truthy. Where an input may be either
a boolean or a boolean string, use:
```jinja2
{% set flag = true if value|default(false)|lower == 'true' else false %}
```
Never rely on bare truthiness — non-empty strings (including `"False"`) are truthy in Jinja2.

### Klipper Macro Notes
- Macro names are **case-insensitive** (`CASE_LIGHTS_ON` == `case_lights_on`)
- Last definition wins for duplicate macro names (include order matters)
- `[danger_options]` indicates this is **Kalico** (not stock Klipper)
