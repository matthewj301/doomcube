# Doomcube agent instructions

Kalico CoreXY printer configuration. Start at `printer.cfg` and trace active
includes; alternate hardware files and historical examples are not active config.

## Work and completion

Finish the requested outcome and verify the affected behavior. Read only the
applicable references below, expanding when dependencies require it. Old audits,
setup guides and operating notes are context, not assignments or proof that a
change shipped. Separate config inspection, parser checks, live restart checks
and physical print validation in the result; do not imply one proves another.
Documentation maintenance does not authorize deployment, flashing or printer motion.
Preserve unrelated work and user decisions. Lead with a recommendation backed by
evidence; resolve routine choices rather than handing them back to the user.

## Boundaries that apply before editing

- Do not modify HH-managed symlinks in `mmu/base/`: `mmu_software.cfg`,
  `mmu_sequence.cfg`, `mmu_form_tip.cfg`, `mmu_cut_tip.cfg`, `mmu_state.cfg`,
  `mmu_leds.cfg`, `mmu_heater_vent.cfg`, `mmu_purge.cfg`.
- Do not modify `mmu/optional/`, `mmu/mmu_vars.cfg` (HH runtime state),
  legacy disabled `AFC/`, managed `KAMP/`, or the generated `#*# SAVE_CONFIG`
  block in `printer.cfg`. Heater-mode changes must reconcile saved control
  without silently overriding this prohibition; see operating context.
- Owned config: `custom/`, `printer.cfg` variables/includes, `KAMP_Settings.cfg`,
  `klipper-variables.cfg`, and `mmu/base/{mmu.cfg,mmu_hardware.cfg,mmu_parameters.cfg,mmu_macro_vars.cfg}`.
  Check symlink ownership before editing other service files.
- No `rename_existing` wrappers for external macros. Do not include HH's
  `client_macros.cfg`. Our guarded HH hooks own the integration.
- Before pause/resume/cancel or MMU changes, read operating context: HH owns
  position save/restore and parking. Do not add a second park or state restore.
- Before FPS tuning, read the failed-neutral-change evidence: never move neutral
  to idle rest. Before cutter travel changes, preserve X clearance before Y travel.
- Before thermal, startup or timeout changes, read operating context: preserve
  thermal protection, intentional pause timeouts, Beacon sequencing and the
  unconditional KAMP `LINE_PURGE` dependency.
- Travel macros must save/set/restore acceleration and convert mm/s to mm/min
  at G-code use. Read macro conventions for Jinja timing and boolean handling.

## Read by task

These links are explicit reading routes, not a claim that runtimes preload them.
Keep this entry near 700 words; retain safeguard triggers when moving detail.

| Task | Smallest useful reference set |
| --- | --- |
| Locate config, hardware, MCU or includes | [Configuration map](docs/agent/configuration-map.md), then active config |
| Any macro edit | [Macro conventions](docs/agent/macro-conventions.md), affected macro and callers |
| PRINT_START, Beacon, heaters, pause/resume, MMU, FPS, cutter, Spoolman | [Operating context](docs/agent/operating-context.md), conventions for macro edits, relevant active config |
| Firmware flashing or board recovery | Configuration map, [setup guide status preamble](docs/Doomcube_FPS_AFC-Lite_Setup.md), actual board inventory; routine FPS/AFC-Lite updates use `~/git/katapult-helper` |
| Kalico/Beacon API or behavior verification | [Local source index](docs/local-docs-index.md); verify source revision against the target |
| Old tuning recommendations | [Historical audit](docs/kalico-config-audit-2026-05-08.md); validate applicability and measured evidence before adopting |

For domain work use the applicable available skill: `happy-hare` for MMU,
`klipper-prod` for firmware tuning, `orca-prod` for slicer profiles. Instruction
maintenance alone does not trigger these domain workflows. When handing the user
content to edit/review, use `phone-editor` and preserve unpulled edits before any
rebuild; a completed maintenance summary does not require a publishing project.

## Shared fleet infrastructure

Read [the fleet route](docs/fleet.md) before changing shared macros or their
interfaces. Doomcube is the master; K3D and Rat Race retain documented integration
exceptions. Tri-Zero's rebuild in mini-trip adopts this infrastructure. Snapmaker is excluded.
A master update requires consumer impact review, not blind file synchronization.
