
# Doomcube WWBMG / Chube Compact FIN — Extrusion Failure Investigation

**Date:** November 5, 2026  
**Status:** Original motor-pinion engagement issue apparently corrected by Garolite plate; subsequent filament-grinding failure unresolved.

**Leading hypothesis:** Long-glass-fiber ABS-MD-GF15 is intermittently restricted by the 0.4 mm nozzle. Test with a 0.5 mm FIN nozzle planned.

**Evidence standard:** Measurements and observed behavior are separated from interpretations. A successful nozzle swap will support—but alone not definitively prove—the nozzle hypothesis.

---

## 1. Installed Hardware and Material

| Component | Details |
|---|---|
| Machine | Doomcube / Voron 2.4 derivative, heated enclosure |
| Toolhead | Original A4T, detachable as a fully assembled operational unit from X carriage |
| Extruder | WWBMG |
| Motor | LDO-36STH20-1004AHG-E, high-temperature stepper |
| Motor current | 0.7 A configured run current |
| Motor plate | Garolite replacement for printed motor mount/plate |
| Cutter | Crossbow, with short PTFE guide between cutter and Chube Chalice |
| Hotend | Beta Chube Compact FIN variant, tested by user before production decisions |
| Hotend cooling | Active A4T hotend fan |
| Material | Luke's Laboratory ABS-MD-GF15; unusually long glass fibers plus mineral filler |
| Original nozzle | 0.4 mm, below manufacturer's reported 0.5 mm minimum |
| Replacement available | 0.5 mm hardened-steel FIN nozzle from Luke's Lab |
| Torque tool | Slice Engineering 1.5 N·m torque tool with driver socket |
| Thermal measurement | UNI-T UTi120S thermal imager |
| Toolboard | EBB36 |

### FIN Variant Background

According to the user:

- The user was a beta tester for the FIN-compatible Chube Compact.
- The FIN variant likely had an improved heatsink, reducing temperatures by approximately 5°C.
- Production constraints, including moving manufacturing in-house in Wisconsin, contributed to the decision not to mass-produce both variants.
- There is no known technical defect established by that decision.

This is user-reported background, not an independently verified manufacturer statement.

### A4T Versus A4Tv2 Geometry

- **Original A4T:** Fan starts near the top of the Chube hotend/heatsink.
- **A4Tv2:** Fan is positioned approximately midway down the heatsink.

Earlier discussion accidentally reversed these positions. The above is the corrected interpretation.

No controlled airflow comparison was completed. Given subsequent thermal-soak results, there is no current justification for changing toolheads solely to alter fan position.

---

## 2. Distinguishing Two Similar Failures

### Failure A — Original Mechanical Problem

**Observed mechanism:**

At elevated temperatures, the printed motor mounting plate experienced creep, allowing the motor pinion to disengage from the WWBMG gear train.

**Implemented fix:**

Replaced the printed mounting plate with Garolite.

**Current assessment:**

Subsequent behavior suggests the motor pinion remains engaged. The Garolite plate may have successfully corrected the original problem.

### Failure B — Current Filament Grinding

During printing with ABS-MD-GF15:

- Motor and drive gears continue turning.
- No characteristic motor clicking or stalling.
- Gears grind a deep notch into the filament.
- Filament stops advancing.
- Usually requires pushing filament from upstream to reengage undamaged filament with the gears.
- One pause-only recovery occurred but was an outlier.

Possible mechanisms include:

- Nozzle or melt-path restriction.
- Filament softening.
- Excessive extrusion backpressure.
- Inadequate gear traction.
- Mechanical alignment problems.

### Central Working Interpretation

The Garolite modification may have fixed Failure A.

The 0.4 mm nozzle, combined with unusually long glass fibers, may have introduced or exposed Failure B during subsequent troubleshooting.

Both failures stop extrusion, but their mechanical causes could be entirely different.

**This remains unconfirmed until the nozzle change and sustained printing test.**

---

## 3. Real Print Failures

| Run | Chamber | Motor casing | Other measurements | Result |
|---|---|---|---|---|
| Original | Started 46°C at 12:05 CST; 53°C at 12:10; peaked at 57°C at 12:16 | Up to 103°C | Printed parts ~70°C | Failure estimated ~10 minutes after start |
| Motor heatsink + thermal tape | Started 50.6°C; 55°C after 5 minutes; peak 55.7°C | 85°C | Heatsink 90°C; EBB36 hotspot 94.9°C | Failed after 7.5 minutes |
| Cooler-toolhead print | 52°C at failure | 80°C | Front 45–50°C; Crossbow 52°C; EBB36 ~90°C | Grinding failure after ~10 minutes; progressed farther into print |

### Additional Crossbow Measurement

Earlier Crossbow exterior measurements reached 75–78°C, while most ABS toolhead components measured around 60°C.

These temperatures were not reliable predictors of failure.

### Interpretation

The experiments demonstrated:

1. Reducing motor temperature did not eliminate the grinding failure.
2. Reducing Crossbow temperature did not eliminate the failure.
3. The failure occurred at 52°C chamber temperature, so 53°C is not a hard threshold.
4. The Garolite plate apparently prevented the previously observed motor-pinion disengagement.

**Important limitation:** Initial thermal conditions, measurement timing, and surface emissivity differed between tests.

The shorter failure time with the heatsink does not demonstrate that the heatsink made the problem worse.

---

## 4. Filament Appearance

Observations:

- Deep ground notch at the drive gear contact.
- Downstream filament, near the PTFE between Crossbow and Chalice, sometimes appeared glossy.
- Some surface shaping appeared consistent with contact against the PTFE bore.
- No definitive gross swelling was observed.
- PTFE guide had recently been replaced.
- After an extreme-retraction test, withdrawn filament showed a glossy, tapered plug.

### Interpretation

The filament appearance could result from:

- Softened material being withdrawn through a restriction.
- Compression against a downstream obstruction.
- Thermal deformation.
- Friction against the PTFE or heatbreak.
- Deformation during filament removal.

The photographs alone do not establish heat creep or fiber bridging.

---

## 5. Detached but Fully Assembled A4T Test

### Test Configuration

The A4T was detached from the X-axis carriage without dismantling the extrusion assembly.

The following remained assembled and operational:

- WWBMG extruder and motor.
- Crossbow cutter.
- PTFE filament guide.
- Chube Compact FIN hotend.
- Nozzle.
- Hotend fan.
- Toolboard and electrical connections.

Filament was extruded through the actual installed hotend and nozzle, without depositing material against a print surface.

### Thermal Conditions

Initially:

- Hotend: 260°C
- Bed: 80°C

Later raised to:

- Hotend: 280°C
- Bed: 105°C

The chamber progressed through approximately 43°C, 50°C, 54°C, 56°C and 58°C.

### Thermal Measurements

| Chamber | Chube heatsink fins | Printed Crossbow-to-Chube joiner |
|---|---|---|
| 43.3°C | 43°C | 58°C |
| ~50°C | 45°C | 62°C |
| ~54°C | 51°C | 64°C |
| 54.4°C | 54°C | 71.2°C |
| Later thermal soak | 63°C | 72°C |

No localized hotspots were apparent across the finned section of the Chube using the thermal camera.

Other readings during successful extrusion:

- Motor casing: approximately 71°C.
- EBB36 hotspot: approximately 87°C.
- Chamber: approximately 58°C.

### Successful Extrusion Tests

**Test 1**

- Filament distance: 25 mm
- Filament speed: 25 mm/s
- Approximate volumetric flow: 60.1 mm³/s
- Duration: 1 second
- Result: Successful

**Test 2**

- Filament distance: 100 mm
- Filament speed: 12 mm/s
- Approximate volumetric flow: 28.9 mm³/s
- Duration: approximately 8.3 seconds
- Result: Successful

The second test succeeded with the chamber reaching 58°C.

### What This Establishes

The fully assembled A4T can feed ABS-MD-GF15 through the installed 0.4 mm nozzle during short stationary extrusion tests at temperatures comparable to, or higher than, previous failures.

This argues against:

- A simple chamber-temperature cutoff.
- An immediate permanent obstruction.
- Grossly inadequate cooling of the exposed Chube fins.

### What It Does Not Establish

These tests do not eliminate:

- Intermittent fiber bridging.
- Restrictions developing during sustained printing.
- Repeated extrusion/retraction effects.
- Extrusion pressure during actual printing.
- Filament-feed geometry under toolhead motion.
- Localized internal heatbreak temperatures.

The UNI-T thermal camera measures apparent surface temperatures, which may be affected by emissivity differences.

---

## 6. Extreme Extrusion/Retraction Test

### Test Conditions

Repeated alternating extrusion and retraction:

- Distance: approximately 15–25 mm.
- Speed: 25 mm/s.
- Chamber: 55°C.
- Motor: 73–75°C.

### Result

The extruder eventually stopped feeding, producing another glossy, tapered filament plug.

### Critical Limitation

**This experiment did not reproduce the actual print's retraction settings.**

The normal G-code uses approximately:

- Retraction distance: 0.34 mm.
- Retraction speed: 45 mm/s.
- Deretraction speed: 40 mm/s.

The experimental 15–25 mm retractions were approximately 44–74 times longer than those used during printing.

Such long retractions can pull softened material upstream and produce a jam in an otherwise functioning hotend.

Therefore:

- The test does not prove normal retraction-induced heat creep.
- The resulting plug may not share the original failure mechanism.
- It does establish that a similar failure can occur with motor temperature below 80°C.

Further repetition of this extreme-retraction test is not recommended.

---

## 7. G-code Inspection

### Source

`Crossbow cutter holder with top cap - WW-BMG (Sherpa-Mini spacing)_ABS-MD-GF15_37m6s.gcode`

Generated by OrcaSlicer 2.5.0-rc.

### Print Configuration

| Setting | Value |
|---|---|
| Material | Luke's Lab ABS-MD-GF15 |
| Objects | Four SteppedRiser.stl instances |
| Layer count | 130 |
| Maximum Z | 26 mm |
| Configured nozzle | 0.4 mm |
| First-layer hotend | 285°C |
| Subsequent hotend | 280°C |
| First-layer bed | 105°C |
| Subsequent bed | 100°C |
| Requested chamber | 45°C |
| Maximum volumetric speed | 35 mm³/s |
| Filament flow ratio | 0.978 |
| Pressure advance | 0.0205 |
| Retraction distance | 0.34 mm |
| Retraction speed | 45 mm/s |
| Deretraction speed | 40 mm/s |
| Nominal print time | 37 minutes 6 seconds |

### Start G-code

```gcode
PRINT_START HOTEND_TEMP=285 BED_TEMP=105 TARGET_CHAMBER_TEMP=45 MATERIAL="ABS-MD-GF15" TOOL=0
```

### Pressure Advance

```gcode
SET_PRESSURE_ADVANCE ADVANCE=0.0205
```

### Observations

The G-code requested a 45°C chamber even though actual chamber temperatures during printing reached 52–57°C.

The 0.4 mm nozzle setting is especially important because the material manufacturer recommends a larger nozzle for its long-fiber formulation.

---

## 8. Research: Long Glass Fibers and Nozzle Restrictions

### Manufacturer Recommendation

Luke's Laboratory recommends:

- 0.6 mm nozzle preferred.
- 0.5 mm minimum.
- 0.4 mm below its published recommendation.

This guidance is specific to the material's unusually long glass fibers.

### Proposed Failure Mechanism

Long glass fibers can bridge or accumulate in a narrow nozzle passage.

A possible failure sequence:

1. Filament extrudes normally.
2. Fibers intermittently accumulate or bridge within the nozzle.
3. Extrusion pressure increases.
4. The WWBMG cannot advance filament against the resistance.
5. Drive gears grind a notch in the filament.
6. Extrusion stops.
7. The restriction may partially clear during unloading or subsequent extrusion.

**No actual fiber blockage has been directly observed.**

This is therefore a plausible explanation, not a confirmed diagnosis.

### Why Normal CF Filaments May Behave Differently

Many conventional carbon-fiber and glass-fiber filaments contain relatively short fibers.

These formulations can often work with 0.4 mm nozzles.

Luke's ABS-MD-GF15 uses unusually long glass fibers, which can behave differently in narrow passages.

The important distinction is fiber aspect ratio and formulation, not merely the presence of mineral filler.

### Research References

Luke's Lab material page:

https://www.lukeslabonline.com/products/abs-gf-two-step-process-filament

FIN6/V6 nozzle listing:

https://www.lukeslabonline.com/products/two-step-process-plated-copper-nozzle-fin6-v6

A4T project:

https://github.com/Armchair-Heavy-Industries/A4T

Community reports of successful A4T + Chube Compact operation at high chamber temperatures were also reviewed. These are anecdotal rather than controlled evidence.

---

## 9. Beta FIN Compact and Nozzle Installation

### Beta Hotend

The user was a beta tester for the FIN-compatible Chube Compact.

The beta FIN interface should not automatically be assumed identical to the production Chube Compact nozzle arrangement.

### Available Replacement

- Luke's Lab hardened-steel FIN nozzle.
- Diameter: 0.5 mm.
- Slice Engineering 1.5 N·m torque tool.
- Driver socket.

### Installation Plan

The standard FIN torque guidance discussed was:

- Hot-tighten at approximately 280°C.
- Apply 1.5 N·m.
- Counterhold the heater block.
- Avoid applying torque through the Chalice or heatbreak.

**Important:** Beta-specific installation and torque requirements from Luke's Lab take precedence over generic FIN guidance. The 1.5 N·m value has not been independently confirmed for this particular beta assembly.

Installation checks:

1. Confirm correct FIN interface and nozzle compatibility.
2. Inspect mating surfaces for contamination.
3. Engage nozzle threads by hand.
4. Heat the hotend to the appropriate tightening temperature.
5. Counterhold the heater block.
6. Use a correctly fitting socket and torque tool.
7. Verify the nozzle seals against its intended mating surface.

---

## 10. Next Controlled Experiment

### Objective

Determine whether the subsequent extrusion-grinding failures were caused by the 0.4 mm nozzle with Luke's long-glass-fiber filament, after the Garolite plate corrected the original motor-pinion engagement problem.

### Changes

Replace the 0.4 mm nozzle with the 0.5 mm hardened-steel FIN nozzle.

Reslice the print with appropriate 0.5 mm nozzle settings.

### Keep Unchanged

- Garolite motor plate.
- WWBMG assembly.
- LDO motor.
- Motor run current: 0.7 A.
- A4T cooling.
- Crossbow cutter.
- PTFE filament guide.
- Chube Compact FIN hotend.
- Luke's Lab ABS-MD-GF15 filament.

### Preparation

1. Install the 0.5 mm FIN nozzle using appropriate torque guidance.
2. Clean filament dust from the WWBMG drive gear teeth.
3. Verify the motor pinion is correctly engaged.
4. Confirm the PTFE is properly seated into the Chalice.
5. Avoid modifying idler geometry or tension unless an actual fault is identified.

### Initial Print Settings

| Setting | Target |
|---|---|
| Nozzle | 0.5 mm FIN hardened steel |
| First-layer temperature | 285°C |
| Subsequent temperature | 280°C |
| Bed | 105°C initially, 100°C subsequently |
| Chamber | 55–60°C |
| Initial volumetric flow cap | 18–20 mm³/s |
| Retraction | 0.34 mm |
| Pressure advance | 0.0205 initially |
| Motor current | 0.7 A |

The conservative flow limit is intended to reduce extrusion load during initial validation.

It is not necessarily the maximum achievable flow for this material and hotend.

### Evaluation

**If the print completes successfully:**

- Repeat for confidence.
- Raise volumetric flow incrementally.
- Check for grinding or intermittent extrusion.
- Evaluate whether the original Garolite modification remains stable.

**If the print still clogs:**

- The 0.5 mm nozzle is only the manufacturer's minimum.
- A 0.6 mm nozzle remains the next direct test for fiber bridging.
- Reinspect the Chalice/PTFE interface.
- Check Crossbow clearance and alignment.
- Verify WWBMG gear engagement and idler pressure.
- Avoid assuming the Garolite fix failed merely because extrusion stopped.

---

## 11. Testing Log

| Trial | Nozzle | Chamber | Hotend / Bed | Flow cap | Motor temperature | Result |
|---|---|---|---|---|---|---|
| Original print | 0.4 mm | 52–57°C | 285/280°C; 105/100°C | 35 mm³/s | 80–103°C across tests | Grinding after ~7.5–10 minutes |
| Next trial | 0.5 mm FIN | Target 55–60°C | 285/280°C; 105/100°C | 18–20 mm³/s | TBD | Pending |
| Follow-up if necessary | 0.6 mm | Comparable | Comparable | Conservative | TBD | Pending |

### Notes for Next Session

Record:

- Actual chamber temperature.
- Motor casing temperature.
- Print duration before failure or completion.
- Whether the motor pinion remains engaged.
- Whether the gears grind filament.
- Whether the nozzle exhibits a partial obstruction.
- Whether the print succeeds at higher volumetric flow.

---

## 12. Current Conclusions

### Established

- The original printed motor plate experienced creep and pinion disengagement.
- A Garolite replacement was installed.
- Subsequent failures involved filament grinding.
- Normal forward extrusion works with the assembled toolhead at 58°C chamber temperature.
- The original G-code used a 0.4 mm nozzle.
- Luke's long-glass-fiber ABS-MD-GF15 is recommended for nozzles of at least 0.5 mm.
- Extreme 15–25 mm retractions induced a plug but are not representative of the print's normal retractions.

### Plausible but Unconfirmed

- Garolite fully resolved the original motor-pinion problem.
- The 0.4 mm nozzle created intermittent fiber-related restrictions.
- The glossy filament plug is secondary deformation from extrusion resistance.
- Today's failures were a separate problem that superficially resembled the original mechanical failure.

### Not Established

- A defective Chube Compact.
- Insufficient A4T hotend cooling.
- Incorrect fan placement.
- Motor overheating as the primary cause.
- Mineral filler alone requiring a larger nozzle.
- A confirmed nozzle blockage caused by glass fibers.

### Leading Working Hypothesis

**Two separate faults produced nearly identical visible symptoms:**

1. Printed mounting plate deformation caused motor-pinion disengagement.
2. After fitting Garolite, the undersized 0.4 mm nozzle caused intermittent restrictions when printing long-glass-fiber ABS-MD-GF15.

The planned 0.5 mm FIN nozzle test is intended to validate the second hypothesis while preserving the successful mechanical modification.

---

*Prepared from the November 5, 2026 troubleshooting conversation and inspected G-code. All temperatures are user-reported. This is a troubleshooting record, not an independent expert inspection.*
