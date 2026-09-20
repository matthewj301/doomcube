# Master findings and promotion status — 2026-09-20

Candidate baseline only. No consumer macro port or live deployment was performed.
This is the current disposition of findings from establishing the shared layer;
it is not a complete firmware audit or a standing assignment during unrelated work.

| Finding | Resolution and evidence | Promotion status |
| --- | --- | --- |
| Documentation says booleans are always strings | Corrected macro conventions. Local Kalico `klippy/extras/gcode_macro.py` at `84a41057` uses `ast.literal_eval`; Jinja 3.1.6 tests exercise boolean and string inputs. | Documentation corrected; installed-version behavior still requires matching source |
| MAYBE_HOME with X/Y/Z parameters silently skips requested homing | Fixed master selection logic to collect only requested unhomed axes, with no parameters selecting all. The old template failed both requested-axis regression cases; fixed template passes. | Source fix verified; live homing not yet qualified; do not port until appropriate runtime/physical verification |
| MAYBE_HOME treats persisted string `"False"` as printing | Normalize the print-state flag at the input boundary. Old template failed the string-false regression; fixed template passes boolean/string true and false cases. | Same homing promotion hold |
| Config map implies root klipper-variables.cfg is active | Active include inspection resolves `[save_variables]` in MMU config to `mmu/mmu_vars.cfg`. Configuration map corrected to distinguish the legacy root file. | Documentation corrected from local include evidence |
| Missing local external HH/KAMP files | Read-only scanner reports unresolved dependencies rather than claiming macros missing on the printer. No external managed file edited. | Installed dependency resolution remains open |
| Doomcube-specific capabilities are not portable defaults | Profiles retain K3D Python/cold-home behavior, Rat Race explicit HH restore, and Mini-Trip ZeroClick/triple-Z requirements. | Adaptation required; no blanket synchronization |

Verification performed:

- Eight homing render regressions: 3 failed against original, all 8 pass after fix.
- Eight scanner fixture tests: sorted and relative/absolute includes, cycles,
  external symlink boundaries, missing files, Python syntax, commented includes,
  parameter inventory and section merging.
- All 53 non-Python G-code templates under Doomcube `custom/macros/` compile with
  Jinja 3.1.6 and the inspected Kalico environment delimiters/extensions. This
  checks template syntax only, not every runtime branch or hardware command.
- Fleet scan: Doomcube 10 unresolved dependencies; K3D 2; Rat Race 11; Mini-Trip 8.
  Missing Mini-Trip lifecycle definitions are expected in this incomplete local
  scan because the RatOS source symlink is external, not proof the old printer
  lacks them. Duplicate-section counts are observations, not confirmed defects.

The eight-file source baseline intentionally retains its pre-fix hash for homing.
The scanner reports one changed master file. Do not repin merely to silence that
finding; repin only with the evidence needed for the intended adoption stage.
All runtime macros in K3D, Rat Race and Mini-Trip remain unchanged.

Run tests using Python with Jinja2 3.1.6 installed:
`python -m unittest discover -s scripts/fleet -p 'test_*.py'`.
The scanner itself uses only the standard library. Self-review and local rendering
are not independent review, installed firmware validation, or physical qualification.
