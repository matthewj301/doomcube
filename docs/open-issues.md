# Open issues (assignable)

Unlike audits and historical notes, entries here ARE assignments. Pick one, fix it in the
fleet master first (see docs/fleet.md and the fleet contract), port to consumers, and
delete the entry in the same change. Record each entry with date, origin and evidence.

## MPC

- **Manual `_SET_MPC_MATERIAL` calls are unvalidated** (2026-11-16, review of the
  FILAMENT_DENSITY change). `PRINT_START_PREFLIGHT` validates `FILAMENT_DENSITY`
  (0.5-3.0 g/cm3) on the PRINT_START path only. A hand-typed
  `_SET_MPC_MATERIAL FILAMENT_DENSITY=abc` becomes `|float` = 0.0 on Doomcube and Rat Race
  and is accepted by `MPC_SET` (no minimum); K3D's Python macro raises instead, so the
  fleet is inconsistent, and `nan` passes everywhere. Fix structurally: one owner of the
  density rule that both preflight (fail before heat/motion) and the applying macro use;
  do not just copy the range check into the macro.
- **Unknown materials fall back silently** (2026-11-16, same review). `_SET_MPC_MATERIAL`
  uses heat capacity 1.80 for any MATERIAL not in `capacity_map` with no console warning,
  so a slicer `filament_type` typo or new material goes unnoticed. Emit a visible warning
  (fleet-wide).
- **Physical validation of the 2026-11-16 heat-capacity table is pending.** Print PETG
  with large flow changes and compare the extruder temperature trace before/after (old
  PETG value 1.17 vs 1.75). See docs/mpc-heat-capacity.md. Not a code task; needs the user.
- **Tri-Zero (mini-trip) runs MPC with no per-material values.** Its Kalico branch
  (`codex/trizero-kalico`, not yet the printer's live `main`) includes
  `custom/hotends/tk.cfg` with `control: mpc` and fixed `filament_density: 1.07` /
  `filament_heat_capacity: 1.30` (ASA's old room-temperature value), but has no
  `_SET_MPC_MATERIAL` call, so every material uses those. When it adopts the shared
  lifecycle, adopt the master `_SET_MPC_MATERIAL` + preflight + slicer
  `FILAMENT_DENSITY=` together.

## Test harness

- **Two lifecycle tests error before any assertion** (seen 2026-11-16, pre-existing):
  `test_lifecycle.LifecycleTests.test_cancel_critical_actions_precede_optional_integrations`
  and `test_cancel_preserves_motionless_compensation_cleanup` fail with
  `UndefinedError: 'dict object' has no attribute 'print_stats'` — `macro_test_support.state()`
  lacks `print_stats`, which CANCEL_PRINT now reads. Decide whether the harness state or
  the macro is wrong; do not just add a dummy key without checking the macro's intent.

## Upstream (not this repo)

- Kalico `docs/MPC.md` gives FILAMENT_DENSITY in g/mm^3; `control_mpc.py` uses g/cm^3.
  Candidate upstream docs fix; nothing to change here.
