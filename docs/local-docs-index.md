# Local docs index — Kalico & Beacon

Kalico and Beacon source/docs are cloned locally under `~/git/`. Read them with the Read tool instead of WebFetching `klipper3d.org`, `kalico.gg`, or `docs.beacon3d.com`.

## Kalico (Klipper fork)

- **Repo:** `~/git/kalico/` — remote `KalicoCrew/kalico`
- **Docs:** `~/git/kalico/docs/*.md` (70 markdown files, source for kalico.gg)
- **mkdocs nav:** `~/git/kalico/docs/_kalico/mkdocs.yml` — authoritative ordering of doc sections

### Files most relevant to a Klipper/Kalico printer config

- `Config_Reference.md` — every `[section]` and parameter, stable features
- `Config_Reference_Bleeding_Edge.md` — params behind bleeding-edge flags
- `Kalico_Additions.md` — what Kalico adds on top of upstream Klipper (formerly "Danger_Features")
- `Bleeding_Edge.md` — opt-in unstable features and how to enable them
- `Migrating_from_Klipper.md` — diffs vs upstream Klipper
- `Config_Changes.md` — chronological breaking changes (consult when bumping commit)
- `G-Codes.md` — every gcode command Kalico exposes
- `Status_Reference.md` — printer object fields available to macros/templates
- `Command_Templates.md` — Jinja template reference for macros
- `Pressure_Advance.md`, `Nonlinear_Pressure_Advance.md`, `MPC.md`, `PID.md` — tuning model docs
- `Resonance_Compensation.md`, `Measuring_Resonances.md` — input shaper
- `Bed_Mesh.md`, `Axis_Twist_Compensation.md`, `Skew_Correction.md` — bed/geometry calibration
- `Load_Cell.md` — load cell probe (relevant if Beacon Contact is in scope)
- `TMC_Drivers.md`, `Rotation_Distance.md` — stepper config
- `CANBUS.md`, `CANBUS_Troubleshooting.md`, `CANBUS_protocol.md` — CAN toolhead

To refresh: `cd ~/git/kalico && git pull`.

## Beacon (eddy current probe)

The public-facing docs at `docs.beacon3d.com` are **not** in a public repo. What we have locally:

- **`~/git/beacon_klipper/`** — the Klipper module (`beacon3d/beacon_klipper`)
  - `beacon.py` — single ~3944-line source file. Authoritative for every config parameter, gcode command, and behavior. **When in doubt about a Beacon config option, grep `beacon.py` rather than guessing.**
  - `README.md` — firmware release notes (Beacon 1.0.0 → 2.1.0)
  - `install.sh`, `update_firmware.py`, `firmware/` — installation/firmware update flow

- **`~/git/beacon_docs/`** — the `beacon3d/docs` repo, which is actually CAD/hardware files only
  - `mcad/beacon/` — mounting CAD sources
  - `stls/assembly_jigs/` — printable jigs
  - No markdown docs — don't look here for config or gcode info

### Where to look for Beacon info

1. **Config parameters / commands:** grep `~/git/beacon_klipper/beacon.py` for `cmd_*` (gcodes), `config.get*(` (config options), `register_command`, `register_event_handler`.
2. **Firmware behavior / version changes:** `~/git/beacon_klipper/README.md`.
3. **Load-cell/contact-probe theory:** `~/git/kalico/docs/Load_Cell.md` (Kalico's generic load-cell doc, relevant background for Beacon Contact).
4. **Last resort (web):** `docs.beacon3d.com` — only when the source doesn't answer the question.

To refresh: `cd ~/git/beacon_klipper && git pull` and `cd ~/git/beacon_docs && git pull`.

## Related index

`~/git/K3D/docs/local-docs-index.md` is the canonical version of this file (annotated for K3D's specific config). It and this file are kept in sync manually — if you find a more useful pointer while answering a question, update both.
