# Shared infrastructure route

Doomcube owns the versioned [fleet contract v1](../../doomcube/docs/fleet/v1/contract.md)
and read-only checker. This repo's [fleet.json](../fleet.json) records membership,
capabilities and intentional differences. Read the contract for shared-macro work,
then the affected macros and local operating safeguards.

The sibling checkout is an explicit local dependency, not an automatic instruction
import. If unavailable, locate the Doomcube checkout/revision identified by the
contract baseline before changing shared behavior; do not substitute stale copies.
Ordinary work unrelated to shared macros can continue using local instructions.

Run from Doomcube: `python3 scripts/fleet/check.py --repos . ../K3D ../rat-race ../mini-trip`.
Use `--json` for full observations. A generated report is not firmware validation.

User decision, 2026-09-20: Doomcube is master; Tri-Zero rebuild in mini-trip joins; Snapmaker
remains independent of this fleet. Per-machine tuning and hardware are never copied.
