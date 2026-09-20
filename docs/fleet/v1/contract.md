# Fleet macro contract v1

Accepted direction (2026-09-20): Doomcube is the master for shared macro behavior
and infrastructure. Consumers are K3D, Rat Race and the Tri-Zero rebuild.
Tri-Zero’s design-only `tri-zero` checkout is not a fleet consumer.
Snapmaker U1 is excluded: its vendor firmware/macros and backup workflow remain
independent. Positron is not enrolled by this decision.

This is a behavioral contract and adoption workflow, not certification that
Doomcube or a consumer already satisfies every requirement. `baseline.json` pins
the source revision and hashes inspected when v1 was established. Updating that
baseline requires reviewing the delta and its impact on every consumer. Never
silently refresh hashes to make drift disappear.

## Promotion gate

This baseline is a candidate, not an approved macro release. Any discovered
Doomcube defect blocks promotion of the affected behavior until its cause is
established, the master fix is reviewed, and regression checks reproduce the
failure before the fix and pass afterward. Runtime/physical checks remain required
where source tests cannot establish correctness. Do not propagate known defects
or label unresolved findings as accepted exceptions merely to unblock adoption.
The master can be more mature without every behavior being portable or qualified.

## Ownership and architecture

- Doomcube `custom/macros/` is the reference implementation. Keep fixes and new
  shared behavior there first, or upstream a consumer fix there after assessing
  applicability. Consumers may retain different syntax and hardware integration.
- Root `printer.cfg` selects capabilities and includes. `custom/macros.cfg` selects
  macro modules. Machine geometry, MCU pins, heaters, sensors, motors and tuning
  stay in machine-specific config; installed external packages keep their ownership.
- `_PRINTER_VARS` holds tunable macro settings. Hardware profiles and constants
  retain their own ownership; do not flatten K3D's established constants layers.
- Every consumer has `fleet.json` recording contract version, source locations,
  capability evidence and intentional differences. Values are repository
  observations, not live-machine discovery or calibration proof.
- No macro release includes another machine's currents, acceleration limits,
  input shaping, pressure advance, probe offsets or calibration store.
- Preserve per-repo operating rules when adapting the master. If a local safeguard
  conflicts with a proposed shared change, resolve it with evidence before porting.

## Common behavior

1. **Interfaces:** keep the public lifecycle names PRINT_START, PRINT_END, PAUSE,
   RESUME, CANCEL_PRINT, PREHEAT and COOLDOWN_SEQUENCE. Temperature interfaces use
   HOTEND_TEMP, BED_TEMP and TARGET_CHAMBER_TEMP where applicable; MATERIAL selects
   material behavior. TOOL applies only with a supported tool-selection integration.
   Document defaults and caller changes together; absence of an optional parameter
   is not automatically a defect. Do not silently rename a slicer-facing interface.
2. **Units and state:** settings named `*_speed` are mm/s; G-code feedrates are
   mm/min. Convert at the boundary. Travel routines preserve the caller's motion
   state/acceleration as appropriate; examine success, error, cancel and repeat
   paths. A save/restore pair in the text alone does not prove correct timing.
3. **Evaluation:** Jinja expansion and later command execution are different stages.
   Use a later macro/runtime read when a preceding command must change observed
   state. Python macros must use the installed Kalico helper API. Preserve typed
   literals; explicitly normalize string inputs rather than trusting `"False"`.
4. **Startup and heat:** reject invalid extrusion-temperature requests, preserve
   probe-specific homing/leveling/contact temperatures, and heat to extrusion
   temperature before extrusion. Wipe, tool selection, mesh and purge ordering
   must fit the target hardware. KAMP purge may be required or have an explicitly
   tested fallback; a fallback definition is not proof it is actually called.
5. **Pause/resume/cancel:** one coherent owner of position and parking per branch.
   Reheat before unretraction, preserve the intended timeout/bed policy, and
   restore normal timeout/state on resume. MMU and non-MMU paths need separate
   scenarios. Rat Race's explicit restore and Doomcube's HH-owned resume remain
   distinct until tested integration evidence justifies a change.
6. **Thermal and shutdown:** keep heater protection and intended cooldown/filter
   ordering. Reconcile heater mode with saved calibration using each repo's
   permitted workflow. Do not copy fixed pause durations or thermal limits from
   the master into a consumer without machine-specific justification.
7. **Persistence and dependencies:** resolve the active save_variables filename
   from included config; never infer it from similarly named files. Preserve
   keys/calibration or provide a migration. Resolve managed macros against the
   installed packages; dangling checkout symlinks mean incomplete evidence.

## Required review for a shared change

Run `scripts/fleet/check.py` against Doomcube and every consumer. Review active
includes, duplicate definitions, public parameter inventory and source differences.
Follow dynamic calls and variable/parameter chains manually or with the real runtime;
the scanner does not execute templates or prove references are valid.

Record the change identifier, master source hash, affected interfaces and a result
for each consumer: adopted with evidence, already equivalent with evidence,
intentional exception with rationale, or pending with a concrete dependency.
Tri-Zero lives in `mini-trip`. Its existing RatOS macro/probe dependencies must
be migrated deliberately before enabling the shared lifecycle.
A pending consumer is not silently counted as upgraded. Never synchronize all
files simply because the master changed.

For each affected behavior exercise the applicable cases:

| Scenario | Evidence required |
| --- | --- |
| Ordinary start/end and repeated invocation | Parameter flow, state restoration, startup order and end policy |
| Missing capability (MMU, Beacon, chamber fan or KAMP) | Valid selected branch or clear dependency failure; no nonexistent hardware use |
| Pause → resume; runout; cancel while paused | Position owner, reheat/unretract order, timeout restoration, shutdown behavior |
| Invalid temperature, missing command or interrupted routine | Reported failure and defined state; no claimed successful completion |
| Saved heater control or variable migration | Active file ownership, calibration preserved, runtime mode verified |
| Release with only static results | Explicitly unqualified for deployment/physical operation until remaining checks are satisfied |

Evidence stages are separate: source review; installed-version parser/template
checks; live registration/restart and state checks; physical motion/thermal/print
qualification. Run only the stages authorized for the task. Track a multi-host
change list so rollback restores every modified system. Documentation or source
comparison does not authorize deployment, restarts or motion.

## Checker scope

`python3 scripts/fleet/check.py --repos . ../K3D ../rat-race ../mini-trip`

Add `--json` for full observations. Run from the Doomcube repository, or use absolute
paths. Python 3.9+ and the standard library suffice. The scanner resolves local
includes in sorted order, maps the declared printer config root into the checkout,
reports external/dangling dependencies and cycles, inventories sections/macros and
observed parameters, inspects variable literals, and parses referenced Python files.
It does not read files outside a target checkout, execute macros, access a printer,
write config, verify pins, simulate branches or replace Klipper's parser.

Duplicate sections and different files are review findings, not automatic bugs.
Literal diagnostics are provisional because this is not the firmware lexer.
Unresolved includes leave macro inventory incomplete. Exit 0 means the report was
produced, not a pass: every result explicitly says qualification NOT_EVALUATED.
