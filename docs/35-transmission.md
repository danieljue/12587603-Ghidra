# P59 OS 12587603 — Automatic Transmission Control

> Traced from 68k disassembly — 2026-06-22
> Full automatic transmission control for 4L60E/4L65E/4L80E applications.
> 1,271 calibration entries across 50+ modules. Shift scheduling, pressure
> control, TCC lockup, adaptation, and diagnostics.

**Note:** The 2004 Corvette M6 is a manual transmission. Most auto-trans
calibrations are zeroed in the Corvette bin. This documentation describes
the full auto-trans subsystem as implemented in OS 12587603 (shared across
Corvette, Silverado, Escalade, and other GMT800 platforms).

---

## 1. Overview

The P59 PCM directly controls the 4L60E/4L65E/4L80E automatic transmission.
This is a full-featured transmission controller with:
- **Shift Scheduling**: Throttle vs MPH shift tables for multiple modes
- **Shift Pressure Control**: Force motor PWM for line pressure
- **TCC Lockup**: Torque converter clutch apply/release scheduling
- **Adaptive Learning**: Shift time adaptation, pressure trimming
- **Diagnostics**: Gear ratio error, slip detection, temperature monitoring
- **Abuse Protection**: Stall torque management, shift torque reduction

The transmission control is integrated with engine torque management — shift
torque reduction momentarily retards spark or reduces throttle during shifts
to extend clutch/band life and improve shift feel.

---

## 2. Key Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_4DD5C | 0x04DD5C | 213853 | Main shift scheduler — called from DoLoopE+AE |
| sub_4D97C | 0x04D97C | — | Shift stabilization / quality control |
| sub_24716 | 0x024716 | 136421 | Driveline torque calculation (TCC, gear ratio) |
| sub_5A582 | 0x05A582 | — | TCC apply/release control |

---

## 3. Module Catalog

### 3.1 Shift Scheduling (T_SHIFT_TABLES, X_SHIFT, XPRS_SHIFT)

Shift points are defined as throttle vs MPH tables for each shift:

```
1→2 shift: Normal, Cruise, Performance, Hot modes
2→3 shift: Normal, Cruise, Performance, Hot modes
3→4 shift: Normal, Cruise, Performance, Hot modes
4→3 kickdown: various TPS/MPH thresholds
3→2 kickdown: various TPS/MPH thresholds
2→1 kickdown: various TPS/MPH thresholds

WOT shifts:
  KE_WOT_SHIFT_RPM_1_2, KE_WOT_SHIFT_RPM_2_3, KE_WOT_SHIFT_RPM_3_4
  Separate tables for Normal, Hot, Performance, 4WD Lo

Shift speed tables (MPH-based, not RPM):
  KE_WOT_SHIFT_SPEED_1_2 through 3_4
```

### 3.2 Pressure Control (XPRS_BRAKING_PRESSURE, XPRS_GARAGE_PRESSURE, XPRS_RATIO, XPRS_STEADY_STATE)

The force motor PWM controls line pressure:

```
Base pressure tables:
  XPRS_STEADY_STATE: line pressure vs torque in each gear
  XPRS_SHIFT: pressure during shifts (higher than steady-state)

Garage shift (P→R, P→D, N→D, N→R):
  Fill phase: high pressure to fill clutch quickly
  Ramp phase: pressure blends to steady-state
  Temperature compensation for cold/hot fluid

Braking pressure:
  Pressure during engine braking (decel fuel cut)
```

### 3.3 TCC Lockup (XTCC_EXECUTION, XTCC_CONTROL, T_TCC_TABLES)

Torque converter clutch control:

```
TCC apply tables: TPS vs MPH for each gear (3rd, 4th)
TCC release tables: TPS vs MPH for each gear
TCC slip control: PWM for modulated apply (ECCC — Electronically
  Controlled Converter Clutch) for smooth engagement

TCC lockup integrator (shared with cruise control):
  KE_LOCKUP_CLAMP_HIGH/LOW
  KE_LOCKUP_INT_FILTER (doc 31)

TCC diagnostics:
  XDTP_TCC_SLIP: stuck on/off detection
  XDTS_TCC_REL_SWCH: release switch monitoring
```

### 3.4 Shift Adaptation (XSHFT_ADAPT, XTIM_ADAPT)

The PCM learns and compensates for clutch wear:

```
Shift time targets:
  Desired shift time vs torque for each shift (1→2, 2→3, 3→4)

Adaptive pressure trimming:
  If shift time > target: increase pressure (faster shift)
  If shift time < target: decrease pressure (smoother shift)
  Temperature limits: KE_1_2_DETENT_HIGH_TEMP_ENABLE etc.
  Gear ratio change during shift verified

Adapt limits:
  Maximum pressure correction learned over time
  Separate limits for each shift and temperature range
```

### 3.5 Diagnostics (TRAN_DIAGNOSTICS, XDTP_*, XDTS_*)

```
Gear ratio error (XDTP_TRANS_RATIO):
  Calculated gear ratio (ISS/OSS) vs expected ratio
  KE_LOW_RATIO_TRAN_TEMP_THRESH for enable temperature

Slip detection (XDTP_SLIP_COMPONENT):
  Clutch slip during steady-state (worn clutches)
  TCC slip when commanded locked

Temperature monitoring (XDTP_TEMP):
  KE_TRANS_OVER_TEMPERATURE_HIGH/LOW
  Transmission fluid temperature performance test
  Fail case 1/2 with absolute delta thresholds

Input/output speed sensors (XDTS_INPT_SPD_SENSOR, XDTS_OUTPT_SPD_SENSOR):
  Rationality checks
  Range sensor (XDTS_RANGE): PRNDL position validation
  Brake switch (XDTS_BRAKE): TCC release verification
```

### 3.6 Abuse / Torque Management (XSEM_ABUSE_TORQUE, XSEM_STALL_TORQUE)

```
Stall torque management:
  Limits torque during torque converter stall
  Prevents excessive driveline loading

Shift torque management:
  Momentary torque reduction during shifts
  Spark retard → faster, limited authority
  Throttle reduction → slower, full authority

Garage shift torque reduction:
  Reduces engine torque during P→R and P→D shifts
  Protects transmission and driveline mounts
```

---

## 4. Key Calibration Areas

| Module | Entries | Purpose |
|--------|---------|---------|
| T_SHIFT_TABLES, X_SHIFT | ~200 | Shift scheduling: TPS vs MPH for all shifts |
| T_TCC_TABLES, XTCC_* | ~100 | TCC apply/release scheduling |
| T_PRESSURE_TABLES, XPRS_* | ~150 | Pressure control: base, shift, garage, braking |
| XSHFT_ADAPT, XTIM_ADAPT | ~80 | Adaptive learning limits and rates |
| XDTP_*, XDTS_*, TRAN_DIAGNOSTICS | ~200 | Diagnostic thresholds and test parameters |
| XSEM_*, XPRS_* abuse | ~60 | Abuse protection and shift torque management |
| T_SEM, XSEM_* | ~40 | Shift energy management |
| X_RATIO, X_INP_SPEED | ~30 | Gear ratio and speed calculations |
| Other (XDT*, X_LIBRARY, etc.) | ~410 | Infrastructure, data tables, common routines |

**Total: ~1,271 calibration entries**

---

## 5. Corvette M6 Specifics

The 2004 Corvette with manual transmission (M6/M12) has different transmission
code paths:

```
KE_TYPE_OF_TRANSMISSION or equivalent calibration selects:
  Manual: most auto-trans functions bypassed
  Auto: full transmission control active

On M6:
  - Shift scheduling is inactive (no shift solenoids driven)
  - TCC control is inactive (no torque converter clutch)
  - Pressure control force motor may still be driven at 0%
  - Shift light (sub_4A71A, doc 25) is the ONLY active trans feature
  - Reverse lockout solenoid is a separate simple control
  - CAGS (Computer Aided Gear Selection) — skip-shift for 1→4
    forced shift at low throttle — is controlled by a separate
    solenoid and simple TPS/RPM/VSS conditions
```

---

## 6. Gaps & Unresolved

1. **CAGS (skip-shift)**: The 1→4 forced shift solenoid for Corvette M6 is
   not documented. This is a simple TPS/RPM/VSS state machine.

2. **Reverse lockout**: The M6 reverse lockout solenoid prevents shifting
   into reverse above ~5 mph. The control logic is not traced.

3. **Full shift scheduling trace**: sub_4DD5C was not line-traced. The shift
   table structure described is inferred from the CSV module catalog.

4. **Adaptive learning algorithm**: The exact pressure correction equation
   (how shift time error maps to pressure adjustment) is not documented.

---

## 7. Community Knowledge

- **4L60E vs 4L80E**: The same OS 12587603 supports both transmissions.
  Segment swap changes the calibration tables to match the transmission
  hardware. The control code is identical.

- **Shift kit tuning**: Aftermarket shift kits increase line pressure
  mechanically. Tuners compensate by reducing the force motor PWM tables
  to avoid excessively harsh shifts.

- **TCC tuning**: Raising TCC apply speeds improves fuel economy but can
  cause lugging/bucking at low RPM. Lowering them improves driveability.

- **Segment swap**: Changing from 4L60E to 4L80E requires a full transmission
  segment swap (not just calibration changes). The 4L80E uses different shift
  solenoid patterns and has an additional input speed sensor.
