# Configuration map

## Directory Structure

```
printer.cfg                  # Main config — includes everything, defines _PRINTER_VARS
├── custom/
│   ├── macros.cfg           # [include macros/*.cfg] + [include macros/dynamic_macros/*.cfg]
│   ├── macros/
│   │   ├── print.cfg        # PRINT_START, PRINT_END, PAUSE, RESUME, CANCEL_PRINT, M600
│   │   ├── park.cfg         # _PARK (parameterized X/Y), PICK_PARK_LOCATION
│   │   ├── homing.cfg       # MAYBE_HOME, _CENTER_AXIS, safe homing helpers
│   │   ├── heating_cooling.cfg  # PREHEAT, COOLDOWN_SEQUENCE
│   │   ├── fans.cfg         # Chamber/bed/filter/part-cooling fan macros
│   │   ├── mmu_macros.cfg   # CLEAN_NOZZLE, POOP_PURGE (MMU support macros)
│   │   ├── utils.cfg        # MAYBE_LOAD_SKEW_CORRECTION, CALIBRATE_BED_MESH, RESET_MULTIPLIERS, _FALLBACK_PURGE, idle_timeout, motor helpers
│   │   ├── slicer_gcode.cfg # Slicer-facing helper macros
│   │   ├── debug.cfg        # Debug helpers
│   │   ├── thermal_expansion_compensation.cfg  # Beacon nozzle thermal expansion (from YanceyA/BeaconPrinterTools); BEACON_VARS
│   │   ├── spoolman.cfg     # Spoolman integration
│   │   ├── fast_QGL.cfg     # Overrides [gcode_macro QUAD_GANTRY_LEVEL] with fast version
│   │   ├── preflight.cfg    # early input/capability checks; post-tool readiness gate
│   │   ├── notifications.cfg # local alerts and optional Moonraker notifier transport
│   │   ├── python/          # startup, scheduled chamber controller and alert helpers
│   │   └── dynamic_macros/
│   │       └── toolhead_assisted_chamber_heating.cfg  # TA_CHAMBER_HEAT
│   ├── default_includes.cfg # [respond], [pause_resume], [display_status], [exclude_object], [save_variables]
│   ├── doomcube/            # Machine-specific: limits, steppers, bed_mesh, QGL, sensorless homing
│   ├── steppers/            # Motor preset library
│   ├── toolheads/           # A4T.cfg (ACTIVE), xol.cfg, calamity.cfg
│   ├── hotends/             # tk.cfg (included by toolhead cfgs), chube-air.cfg
│   ├── extruders/           # Extruder config
│   ├── fans/                # Hardware fan definitions ([fan_generic], [controller_fan], etc.)
│   ├── leds/                # LED definitions
│   ├── sensors/             # Chamber thermistor + verify_heater.cfg (thermal-runaway protection)
│   ├── mcus/                # MCU board definitions (Octopus Pro, EBB36, RPi, FPS)
│   ├── tuning/              # Input shaper, pressure advance tuning results
│   └── probes/              # Probe hardware config
├── mmu/                     # Happy Hare MMU plugin
│   ├── base/                # Core HH configs (ours + HH symlinks — see Critical Rules)
│   ├── optional/            # HH symlinks, NOT included
│   ├── addons/              # HH addon configs (blobifier, erec cutter, eject buttons) — present but NOT included
│   └── mmu_vars.cfg         # Active save_variables target, including HH/runtime state (do not edit)
├── AFC/                     # Legacy AFC plugin (DISABLED — replaced by Happy Hare)
├── KAMP/                    # Klipper Adaptive Meshing & Purging (DO NOT MODIFY)
├── KAMP_Settings.cfg        # User-owned KAMP configuration
├── klipper-variables.cfg    # Legacy root file; active save_variables target is mmu/mmu_vars.cfg
└── moonraker.conf, crowsnest.conf, KlipperScreen.conf, mmu_klipperscreen.conf,
    timelapse.cfg, mainsail.cfg, AFC_menu.conf   # Service configs (several are symlinks)
```

## MCU Topology

```
Pi (USB) ──► Octopus Pro H723    XY/Z steppers, heater bed, fans
Pi (USB) ──► FPS Board           CAN bridge + USB hub + Hall effect sensor
               ├─ CAN ──► EBB36 v1.2 (toolboard_t0)   Extruder, heater, fans, ADXL345
               └─ USB ──► AFC-Lite (mmu)                4-lane BoxTurtle filament changer
Pi (host) ─► RPi MCU             Temperature monitoring
```

- **FPS** replaces the U2C CAN adapter (canbus_uuid: `0e8ab784e48c`). STM32G0B1, 8 MHz crystal, Katapult bootloader. Config: `custom/mcus/fps.cfg`. Analog sync feedback pin `fps:PA2` is wired in `mmu_hardware.cfg`.
- **EBB36** (canbus_uuid: `1586f2c37eaf`). Katapult bootloader.
- **AFC-Lite** (serial: `usb-Klipper_stm32h723xx_17003D000951333235393937-if00`). STM32H723, Katapult bootloader. This is a replacement board — the original AFC-Lite (STM32G0B1) was damaged. Connected through FPS USB hub. Klipper MCU name is `mmu` (Happy Hare convention), defined in `mmu/base/mmu.cfg`.
- Firmware updates for FPS + AFC-Lite go through `katapult-helper` (`~/git/katapult-helper`).
- Original hardware bring-up procedure: `docs/Doomcube_FPS_AFC-Lite_Setup.md` (see its status preamble for what has changed since).
