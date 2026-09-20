# Lifecycle candidate — 2026-09-20

Status: source implementation and independent stage reviews; **not deployed or
qualified for physical operation**. The v1 baseline is intentionally not repinned.
The user requested all lifecycle fixes/features and one review agent after each stage.

## Changes

1. Cancellation switches heaters off and cancels the underlying job before optional
   cleanup, without parking/homing. HH cancel parking is disabled in owned enable lists.
   Non-MMU PAUSE snapshots through firmware before parking; RESUME reheats, checks
   readiness in a later helper, unretracts only the recorded amount, and uses one
   firmware return. MMU position ownership and existing thermal timeouts are retained.
2. New-print/filter-on boundaries cancel obsolete filter timers. Cooldown arms its
   timer after turning the filter on. Skew clears before startup/end travel and after
   cancellation. Beacon offset removal clears its applied-offset bookkeeping.
   Preflight validates configured temperature limits, tool availability, material
   quoting and dependencies. Lighting/ventilation/fan hooks are optional.
3. Scheduled chamber steps replace the synchronous mixing loop. Wall-clock deadlines,
   soak checks, one move per tick, state restoration, stop and failure cleanup are
   explicit. PRINT_START holds and releases its own SD job through a continuation.
   PREHEAT is now asynchronous; port its callers together. Console starts do not
   inherit a historical SD error. Defaults remain PREHEAT bed/chamber=0 versus
   TA_CHAMBER_HEAT's configured chamber defaults. Startup aborts on warmup failure;
   standalone preheat can explicitly choose ON_TIMEOUT=continue, still gated on
   bed/hotend readiness. Pause during startup is unsupported; cancel/stop is available.
4. Completion, startup failure, print failure and one prolonged-pause alert per pause
   episode are supported. Startup's internal SD hold does not produce pause alerts.
   Empty notification_name means console only; remote delivery requires a configured
   Moonraker notifier and destination. Delivery failures do not interrupt printer work.

## Verification and reviews

- Read live config baseline ce5358dcae425077c3ac7e8634c3c593101b4f92; tracked source
  matched local baseline before edits. Live mmu/mmu_vars.cfg is modified and untouched.
- Installed Kalico 29e8ef4123377b94b0748d7810ae2d79905eda2e and HH
  a880ac0adccf532cf98a20567c47e10efdee5576. Verified the installed Python helper shape
  and HH cancel wrapper by read-only SSH. The printer was idle/ready.
- Original live snapshot fails three targeted regression checks: cancel ordering,
  pause snapshot ordering and stale filter timer. Fixed source passes those checks.
- Stage 1 review: restored motionless mesh/Beacon cleanup on cancel; reviewer confirmed.
- Stage 2 review: fixed already-hot startup timer cancellation and optional fan hook;
  reviewer confirmed.
- Stage 3 review: restored PREHEAT zero defaults and gated historical SD errors on
  ownership; reviewer confirmed.
- Stage 4 review: reset alert tracking at each new SD attempt and before SD release,
  fixing missed alerts on same-file retries; reviewer confirmed. All four stages
  received one independent review agent, with every reported finding resolved.
- Final static verification: 50 tests pass; 69 templates compile locally and in the
  installed Python 3.9.2 / Jinja 3.1.6 environment. No printer commands were executed.
  No stale removed chamber-stop references or missing _PRINTER_VARS references were
  found in the affected source scan. Full config parsing/restart is still pending.

Run `python scripts/fleet/verify_release.py --json-output /tmp/doomcube-evidence.json`
with Jinja2 available. This runs behavioral source regressions, compiles owned macro
syntax and inventories all consumers. Generated hashes identify the exact candidate;
they do not approve it. The command never deploys or refreshes the contract baseline.

The test sink models helper dispatch and changing status but is not a firmware or
motion simulator. Installed-interpreter syntax compilation is not a restart test.
Live SD handoff, HH tool loading/error behavior, pause/resume positioning and physical
thermal/motion behavior still require qualification before propagation.

## Consumer impact

| Consumer | Disposition | Required adaptation |
| --- | --- | --- |
| Doomcube | Candidate implemented locally | Restart/registration and physical qualification, including HH cancel, tool-load errors and back-to-back prints; notification destination |
| K3D | Pending; unchanged | Preserve native-Python/constants architecture, cold-home-before-hotend order, fallback purge and motor-retention policy; migrate PREHEAT caller and continuation together |
| Rat Race | Pending; unchanged | Preserve explicit HH restore integration, AWD synchronization, root save_variables and git deployment; migrate PREHEAT caller/stop behavior together |
| Mini-Trip / Tri-Zero | Pending; unchanged | Fresh Kalico runtime and deliberate RatOS lifecycle replacement; preserve ZeroClick docking and triple-Z sequence; adopt full controller dependencies together |

The scanner reports unresolved managed/local dependencies (Doomcube 10, K3D 2,
Rat Race 11, Mini-Trip 8). These are not proof of missing live commands. Machine
currents, input shaping, pressure advance, geometry and calibration were not copied.
Snapmaker and Positron remain outside this fleet change.

## Notification connection

Configure a Moonraker notifier with `events: gcode` and `body: {event_message}`;
set `_PRINTER_VARS.notification_name` to its section name. Store credentials using
Moonraker's secrets support. Do not commit a recipient URL or token into shared macros.
`notification_pause_seconds` controls alert timing only, not heater or pause timeout.
Actual delivery is pending the user's destination and is not claimed as verified.
