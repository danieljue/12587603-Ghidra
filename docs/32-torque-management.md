# P59 OS 12587603 — Torque Management & Drivetrain Protection

> Traced from 68k disassembly — 2026-06-22
> Engine torque management coordinates spark retard, throttle reduction, and
> fuel cut to protect the drivetrain. Covers brake torque management (BTM),
> traction control (TCS), drivetrain abuse protection, and the engine torque
> calculation model.

---

## 1. Overview

The P59 torque management system protects the drivetrain by limiting engine
output during:
- **Brake Torque Management (BTM)**: Reduces torque when brakes are applied
  with throttle open (power-braking, brake-torquing at launch). Prevents
  transmission damage from excessive torque converter stall.
- **Traction Control (TCS)**: Reduces torque when wheel slip is detected
  by the EBCM (Electronic Brake Control Module). TCS events arrive via
  Class 2 serial.
- **Drivetrain Abuse**: Detects neutral-drops and over-rev events that
  could damage the transmission, driveshaft, or differential.
- **Shift Torque Management**: Reduces torque during transmission shifts
  (automatic) for smoother engagement and clutch/band longevity.
- **AC Bump**: Momentary spark retard when AC compressor engages (doc 26).

The PCM calculates delivered engine torque from airflow, spark advance, and
accessory losses. This calculated torque is compared against allowed torque
limits from each protection system, and the most restrictive limit is applied.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_7B33A | 0x07B33A | — | Brake Torque Management — called from DoLoop |
| sub_24716 | 0x024716 | — | Traction control / driveline torque calculation |
| sub_7C8A2 | 0x07C8A2 | — | Drivetrain Abuse Management |
| sub_7E0BC | 0x07E0BC | — | Engine torque calculation (accessory + compressor) |
| sub_27C78 | 0x027C78 | — | ETAS slewing (TCS calibration overrides) |

### 2.1 Torque Reduction Strategies

The system can reduce torque through three mechanisms, applied in priority order:

| Priority | Method | Response Time | Effect |
|----------|--------|---------------|--------|
| 1 (fastest) | Spark Retard | <10ms (next ignition event) | Immediate torque drop, limited range |
| 2 | ETC Throttle Reduction | 50-100ms | Slower but larger authority |
| 3 (slowest) | Fuel Cut / Cylinder Deactivation | 100-200ms | Severe torque reduction for abuse |

---

## 3. Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                    TORQUE MANAGEMENT SYSTEM                        │
│                                                                    │
│  Torque Consumers (demand reduction):                              │
│    ├─ BTM: brake switch + TPS + low VSS → torque limit            │
│    ├─ TCS: EBCM over Class 2 → torque reduction request           │
│    ├─ Shift: transmission shift in progress → momentary reduction │
│    ├─ Abuse: P/N + high RPM + TPS → severe cut                    │
│    └─ AC Bump: compressor engage → spark retard ramp (doc 26)    │
│                                                                    │
│  Engine Torque Calculation (sub_7E0BC):                             │
│    │                                                               │
│    ├─ Indicated Torque (from combustion):                          │
│    │   Based on air-per-cylinder, spark advance, EQ ratio          │
│    │   Thermal efficiency from KA_INDICATED_MBT_TORQUE_EFF tables │
│    │                                                               │
│    ├─ Friction Losses:                                             │
│    │   Engine inertia (KE_ENGINE_INERTIA) × RPM rate               │
│    │   Accessory drive torque (KV_ACCESSORY_DRIVE_TORQUE)          │
│    │   AC compressor torque (KV_AC_COMPRESSOR_TORQUE)              │
│    │                                                               │
│    └─ Net Torque = Indicated - Friction - Accessory - AC           │
│        Units: ft-lb (scaled internal format)                       │
│                                                                    │
│  Torque Limiting (applied in priority order):                       │
│    1. Spark Retard: retards timing from MBT                         │
│       Torque loss from KA_TORQUE_LOSS_FROM_SPARK_RETARD table      │
│       This is the fastest response — used for TCS and shift TM     │
│    2. ETC Throttle: closes blade to reduce airflow                 │
│       Slower response, used by BTM                                 │
│    3. Fuel Cut: disables injectors on selected cylinders            │
│       Used by drivetrain abuse for severe torque reduction         │
│                                                                    │
│  Ramps:                                                             │
│    Torque reduction ramps IN quickly (spark is instant)            │
│    Torque recovery ramps OUT slowly (KE_LOOPS_BETWEEN_RAMP_STEPS)  │
│    Hysteresis prevents cycling: KE_BTM_TORQUE_HYSTERESIS           │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Brake Torque Management (BRAKE_TORQUE_CONTROL module, 0x8AEC-0x8B14)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08AEC | KE_TRANSFER_CASE_RATIO | word | 0x800 | Scaler_8 | Transfer case ratio (4WD LO) |
| 0x08AEE | KE_DRIVELINE_EFFICIENCY | word | 0x6A4 | Scaler_1 | Trans+axle efficiency for torque transfer |
| 0x08AF0 | KE_TCS_FAIL_TRQ_ALLOWED_FACTOR | word | 0x800 | 0-1 | Torque allowed factor when TCS inactive |
| 0x08AF2 | KE_BTM_RPM_OVERSPEED_ENABLE_LO | word | 0 | RPM | Maintain BTM: RPM > idle + this |
| 0x08AF4 | KE_BTM_RPM_OVERSPEED_ENABLE_HI | word | — | RPM | Enable BTM: RPM > idle + this |
| 0x08AF6 | KE_BTM_TORQUE_HYSTERESIS | word | 0 | ft-lb | Hysteresis to prevent BTM cycling |
| 0x08AF8 | KE_LOOPS_BETWEEN_RAMP_STEPS | byte | 2 | Counts | Loops between torque ramp-out steps |
| 0x08AFA | KE_TORQUE_ALLOW_OFFSET | word | 0 | ft-lb | Offset below max for control target |
| 0x08AFC | KE_TORQUE_RAMP | word | 0x400 | ft-lb | Torque step size when ramping out |
| 0x08AFE | KE_BTM_THROTTLE_OPEN | word | 0x1400 | Percent | TPS above which BTM active |
| 0x08B00 | KE_BTM_THROTTLE_CLOSED | word | 0x13CD | Percent | TPS below which BTM inactive |
| 0x08B02 | KV_BRAKE_CAPACITY_VACUUM | table | — | ft-lb vs kPa | Max brake torque capacity per wheel |
| 0x08B14 | KV_EFFECTIVE_GEAR_RATIO | table | — | Ratio | Effective gear ratio per gear |

### 4.2 Drivetrain Abuse (DT_ABUSE_MGMT module, 0x9426-0x9438)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x09426 | KE_ABUSE_DRIVE_RPM_HIGH | word | 0x8400 | RPM | Drive: abuse RPM high threshold |
| 0x09428 | KE_ABUSE_DRIVE_RPM_LOW | word | 0x8200 | RPM | Drive: abuse RPM low threshold |
| 0x0942A | KE_ABUSE_PN_RPM_HIGH | word | 0x8400 | RPM | P/N: abuse RPM high threshold |
| 0x0942C | KE_ABUSE_PN_RPM_LOW | word | 0x8200 | RPM | P/N: abuse RPM low threshold |
| 0x0942E | KE_ABUSE_THROTTLE_HIGH | word | — | Percent | TPS above which abuse enabled |
| 0x09430 | KE_ABUSE_THROTTLE_LOW | word | — | Percent | TPS below which abuse disabled |
| 0x09432 | KE_ABUSE_VEHICLE_SPEED_THRESH | word | — | MPH | VSS above which abuse disabled |
| 0x09434 | KE_ABUSE_EQUIVALENCE_RATIO | word | — | Equiv_Ratio | EQ ratio during abuse event |
| 0x09436 | KV_ABUSE_CYLINDER_DISABLE_PN | byte | — | BOOLEAN | Cylinder disable vector (P/N) |
| 0x09437 | KV_ABUSE_CYLINDER_DISABLE_NOT_PN | byte | — | BOOLEAN | Cylinder disable vector (in-gear) |
| 0x09438 | KV_ABUSE_TIME | word | — | Seconds | Max abuse event duration |

### 4.3 Engine Torque Model (ENG_TORQUE module, 0x9AE4-0x9B48)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x09AE4 | KE_ENGINE_MAX_TORQUE | word | — | ft-lb | Max net engine torque |
| 0x09AE6 | KE_ENGINE_INERTIA | word | — | Mult0to2 | Engine rotating inertia |
| 0x09AE8 | KV_THERMAL_EFF_BLEND_FACTOR | word | — | 0-1 | Ethanol blend factor for MBT torque |
| 0x09CC2 | KE_UNITS_CONSTANT | word | — | lb-ft-RPM-s/g | Units conversion constant |
| 0x09CC6 | KA_INDICATED_MBT_TORQUE_EFF_E0 | table | — | 0-1 | MBT thermal efficiency (E0 fuel) |
| 0x09F66 | KA_INDICATED_MBT_TORQUE_EFF_E80 | table | — | 0-1 | MBT thermal efficiency (E80 fuel) |
| 0x0A206 | KA_TORQUE_LOSS_FROM_SPARK_RETARD | table | — | Percent | Torque loss vs spark retard from MBT |
| 0x0A2BA | KV_AC_COMPRESSOR_TORQUE | table | 0x33 | lb-ft | AC compressor friction torque |
| 0x0A2D0 | KV_AC_COMP_IAT_TORQUE | table | — | lb-ft | AC torque correction vs IAT |
| 0x0A2F0 | KV_ACCESSORY_DRIVE_TORQUE | table | — | lb-ft | Parasitic: PS pump + alternator |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFACAA | byte | sub_7BC70 (COT) | TCS/COT active flag |
| FFFFA562 | word | doc 02 | Engine RPM |
| FFFFA0DC | word | doc 07 | Mass airflow |
| FFFFAB66 | word | sub_7BC70 | Throttle position |

> **Note:** Torque management-specific RAM (calculated torque, torque limits,
> reduction type, TCS request flags) requires tracing sub_7B33A and sub_24716.

---

## 6. Algorithm Detail

### 6.1 Brake Torque Management (BTM)

```
Detect power-braking: brake applied + throttle open + low VSS

1. Entry conditions:
   - TPS > KE_BTM_THROTTLE_OPEN
   - RPM > desired_idle + KE_BTM_RPM_OVERSPEED_ENABLE_HI
   - Vehicle nearly stationary (VSS ~ 0)

2. Torque limit calculation:
   - Brake_capacity = KV_BRAKE_CAPACITY_VACUUM[manifold_vacuum] × wheels
   - Driveline_torque = Brake_capacity / KE_DRIVELINE_EFFICIENCY
   - Engine_torque = Driveline_torque / KV_EFFECTIVE_GEAR_RATIO[gear]
   - Transfer case adjustment: × KE_TRANSFER_CASE_RATIO

3. Torque reduction applied:
   - Target = Engine_torque - KE_TORQUE_ALLOW_OFFSET
   - Reduce spark first (fastest), then throttle if needed

4. Exit conditions:
   - TPS < KE_BTM_THROTTLE_CLOSED
   - RPM < desired_idle + KE_BTM_RPM_OVERSPEED_ENABLE_LO

5. Ramp-out:
   - Increase torque by KE_TORQUE_RAMP every KE_LOOPS_BETWEEN_RAMP_STEPS
   - Hysteresis KE_BTM_TORQUE_HYSTERESIS prevents re-entry oscillation

Purpose: prevents transmission damage from excessive torque converter
stall during brake-torquing (common at drag strip launches).
```

### 6.2 Traction Control (TCS)

```
TCS request received from EBCM over Class 2 serial:

1. EBCM detects wheel slip (ABS sensors compare wheel speeds)
2. EBCM sends torque reduction request to PCM
3. PCM applies spark retard and/or throttle reduction
4. Multiple reduction levels available:
   - TCS discrete: on/off torque reduction
   - TCS duty cycle: variable reduction amount
   - ETAS allows calibration tool override for development

5. TCS failure fallback:
   If TCS system is known inactive (fault):
   → Apply KE_TCS_FAIL_TRQ_ALLOWED_FACTOR to restore full torque
```

### 6.3 Drivetrain Abuse Management

```
Detect events that could damage the drivetrain:

P/N Abuse (neutral-drop):
1. Vehicle in P or N
2. RPM > KE_ABUSE_PN_RPM_HIGH
3. TPS > KE_ABUSE_THROTTLE_HIGH
4. VSS < KE_ABUSE_VEHICLE_SPEED_THRESH
→ Severe torque reduction:
  - Disable cylinders per KV_ABUSE_CYLINDER_DISABLE_PN
  - Command fuel EQ ratio per KE_ABUSE_EQUIVALENCE_RATIO
  - Duration limited to KV_ABUSE_TIME

In-Gear Abuse (over-rev with clutch in):
1. Vehicle in gear (not P/N)
2. RPM > KE_ABUSE_DRIVE_RPM_HIGH
3. Similar conditions
→ Disable cylinders per KV_ABUSE_CYLINDER_DISABLE_NOT_PN

Hysteresis:
  RPM < KE_ABUSE_DRIVE_RPM_LOW (or P/N low) to exit abuse mode
```

### 6.4 Torque Calculation Model

```
Engine torque is calculated (not measured) for drivetrain protection:

1. Indicated Torque:
   Air_per_cylinder = f(VE, MAP, RPM)
   Fuel_mass = Air_per_cylinder / AFR
   Indicated_Torque = Fuel_mass × thermal_efficiency × constants

   Thermal efficiency from KA_INDICATED_MBT_TORQUE_EFF tables
   (indexed by RPM and air-per-cylinder)
   Ethanol blend: interpolate between E0 and E80 tables via
   KV_THERMAL_EFF_BLEND_FACTOR

2. Spark retard loss:
   Spark_retard = MBT_timing - actual_timing
   Torque_loss = KA_TORQUE_LOSS_FROM_SPARK_RETARD[spark_retard]
   Indicated_Torque ×= (1 - Torque_loss)

3. Friction losses:
   Engine_friction = f(RPM, coolant_temp, oil_temp)
   Accessory = KV_ACCESSORY_DRIVE_TORQUE[RPM]
   AC = KV_AC_COMPRESSOR_TORQUE × KV_AC_COMP_IAT_TORQUE[IAT]
     (only when AC clutch engaged)

4. Net Torque = Indicated_Torque - friction - accessory - AC
   Units conversion via KE_UNITS_CONSTANT to ft-lb
   Clamped to KE_ENGINE_MAX_TORQUE
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| Spark Control (doc 09) | Primary torque reduction method |
| ETC Throttle (doc 08) | Throttle reduction for BTM |
| Fuel System (doc 07) | Cylinder deactivation for abuse |
| AC Control (doc 26) | AC bump spark retard integration |
| EBCM / ABS | TCS request via Class 2 serial |
| Brake Switch | Hardware input for BTM detection |
| Transmission | Shift torque management requests |
| COT (doc 29) | COT interacts with torque limits |

---

## 8. Gaps & Unresolved

1. **TCS Class 2 message format**: The specific J1850 message from the EBCM
   containing the TCS torque reduction request has not been decoded.

2. **Shift torque management**: For automatic transmissions, torque reduction
   during shifts is a major subsystem. The subroutines in the XPRS_*, XSHFT_*,
   XTIM_* modules (Phase 5 transmission modules) are not traced.

3. **Torque calculation exact formula**: The indicated torque equation with
   all conversion constants needs line-by-line verification from the .asm.

4. **Accessory torque baseline**: KV_ACCESSORY_DRIVE_TORQUE table dimensions
   and axis breakpoints are not confirmed.

---

## 9. Community Knowledge

- **BTM delete**: Many tuners disable BTM entirely for drag racing. This allows
  full power during brake-torquing for maximum launch RPM. This is safe on
  built transmissions but can destroy stock units.

- **Abuse mode and two-step**: Two-step rev limiters (launch control) hold RPM
  at a set point. If the abuse mode RPM thresholds overlap with the two-step
  RPM, the PCM may activate abuse mode and cut fuel/cylinders. Tuners must
  set abuse thresholds above the two-step RPM.

- **Torque model accuracy**: The PCM torque model is conservative. Tuners
  sometimes scale the torque calculation upward to prevent unnecessary
  torque management intervention, especially on modified engines.

- **TCS on engine swaps**: TCS requires the EBCM and ABS sensors. Standalone
  harnesses without these components cannot use TCS. Setting
  KE_TCS_FAIL_TRQ_ALLOWED_FACTOR = 1.0 restores full torque.
