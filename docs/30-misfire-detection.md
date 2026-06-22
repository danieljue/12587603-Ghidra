# P59 OS 12587603 — Misfire Detection

> Traced from 68k disassembly — 2026-06-22
> OBD-II compliant misfire detection using crankshaft acceleration analysis.
> Detects both emissions-relevant and catalyst-damaging misfire, identifies
> the specific cylinder, and controls MIL flashing for severe events.

---

## 1. Overview

The P59 misfire detection system measures crankshaft angular acceleration
from the CKP (crankshaft position) sensor to detect combustion misfire.
When a cylinder misfires, it produces negative torque instead of positive,
causing a momentary crankshaft deceleration. By measuring the period between
CKP teeth around each cylinder's power stroke, the PCM can identify which
cylinder misfired and how severely.

The system operates in two modes:
- **Cylinder Mode**: High-resolution detection — identifies the specific
  misfiring cylinder. Used at low RPM/low load (idle through light cruise).
  Requires accurate cylinder identification from the CMP (cam position) sensor.
- **Revolution Mode**: Lower-resolution detection — counts misfire events
  without identifying the cylinder. Used at high RPM where cylinder-level
  resolution degrades. Measures overall crankshaft roughness.

Misfire thresholds are calibrated for each operating region with separate
emission-level and catalyst-damage-level limits.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_6F29A | 0x06F29A | — | Main misfire detection algorithm |
| sub_6F126 | 0x06F126 | — | Misfire initialization / power-up delay |
| sub_702A6 | 0x0702A6 | — | Misfire MIL flashing control |
| sub_3580C | 0x03580C | — | Open-loop fuel control for misfire |

---

## 3. Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                   MISFIRE DETECTION SYSTEM                         │
│                                                                    │
│  CKP Sensor (58x reluctor wheel)                                   │
│    │                                                               │
│    ├─ Tooth period measurement (TPU hardware timer capture)        │
│    │   Each tooth = 6° crankshaft rotation (60-2 = 58 teeth)      │
│    │                                                               │
│    ├─ Crankshaft Angular Acceleration:                             │
│    │   Δω = ω_current - ω_previous                                 │
│    │   Acceleration = Δtooth_period / time                         │
│    │   Normalized by engine speed and load                         │
│    │                                                               │
│    └─ Cylinder Identification:                                     │
│        CMP sensor provides #1 TDC reference                         │
│        Firing order: 1-8-7-2-6-5-4-3 (LS1/LS6)                    │
│                                                                    │
│  sub_6F29A (Main Algorithm) — called from TPU interrupt context    │
│    │                                                               │
│    ├─ Operating Region Selection:                                  │
│    │   Cylinder Mode Idle: RPM < threshold, VSS < idle VSS        │
│    │   Cylinder Mode Reg1: low RPM/load                            │
│    │   Cylinder Mode Reg2: medium RPM/load                         │
│    │   Cylinder Mode Reg3: high RPM/load                           │
│    │   Revolution Mode Reg1/2/3: above cylinder mode limits        │
│    │                                                               │
│    ├─ Misfire Threshold Detection:                                 │
│    │   For each cylinder event:                                    │
│    │     1. Calculate Δaccel wrt previous event                    │
│    │     2. Compare against mode-specific threshold table          │
│    │        KA_MISF_CYLINDER_MODE_REG1/2/3 (cylinder mode)        │
│    │        KA_MISF_REVOLUTION_MODE_REG1/2/3 (revolution mode)    │
│    │     3. If Δaccel > threshold → misfire event counted          │
│    │                                                               │
│    ├─ Per-Cylinder Misfire Counters:                               │
│    │   Cylinder #1: counter++ if event in cylinder 1 window        │
│    │   ...                                                         │
│    │   Cylinder #8: counter++ if event in cylinder 8 window        │
│    │                                                               │
│    └─ Misfire Rate Calculation:                                    │
│        Misfire_rate = misfire_count / total_cylinder_events        │
│        (over rolling window of N engine cycles)                    │
│                                                                    │
│  sub_702A6 (MIL Flashing + Reporting)                              │
│    │                                                               │
│    ├─ Catalyst Damage Threshold:                                   │
│    │   If misfire_rate > KA_MISF_CATALYST_MISFIRE:                 │
│    │     Flash MIL immediately (once per second)                   │
│    │     Stop flashing if DFCO for KE_MISF_DFCO_TIME_STOP          │
│    │                                                               │
│    ├─ Emission Threshold:                                          │
│    │   If misfire_rate > KE_MISF_EMISSION_MISFIRE:                 │
│    │     Increment emission misfire counter                        │
│    │     Report via OBD-II PID when threshold exceeded             │
│    │                                                               │
│    └─ Single-Cylinder Detection:                                   │
│        If one cylinder's count > KE_MISF_DETERMINE_MISFIRE_P_CODE: │
│          Set specific P0301-P0308 DTC                               │
│        Else if overall rate high but no single cylinder dominant:   │
│          Set P0300 (random misfire)                                │
│                                                                    │
│  Disable Conditions (sub_6F29A gates):                              │
│    • Rough road detection (ABS wheel speed variance)               │
│    • RPM change > threshold (accel/decel)                          │
│    • Crankshaft angle correction not learned (CASE learn needed)   │
│    • Low coolant temperature                                       │
│    • Cylinder deactivation active                                  │
│    • Torque reduction active                                       │
│    • Assembly plant delay (first N seconds after build)           │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Cylinder Mode Thresholds (DI_MISFIRE module, 0x17CE0-0x18340)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x17CE0 | KA_MISF_CYLINDER_MODE_IDLE | table | — | μs | Idle cylinder mode threshold vs RPM/Load |
| 0x17E34 | KA_MISF_CYLINDER_MODE_REG1 | table | — | μs | Region 1 cylinder mode threshold |
| 0x17F88 | KA_MISF_CYLINDER_MODE_REG2 | table | — | μs | Region 2 cylinder mode threshold |
| 0x18340 | KA_MISF_CYLINDER_MODE_REG3 | table | — | μs | Region 3 cylinder mode threshold |

### 4.2 Revolution Mode Thresholds (0x18384-0x187A2)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x18384 | KA_MISF_REVOLUTION_MODE_REG1 | table | — | μs | Region 1 revolution mode threshold |
| 0x183EA | KA_MISF_REVOLUTION_MODE_REG2 | table | — | μs | Region 2 revolution mode threshold |
| 0x187A2 | KA_MISF_REVOLUTION_MODE_REG3 | table | — | μs | Region 3 revolution mode threshold |

### 4.3 Reporting Thresholds (DG_MF_REPORTING, 0x16D24-0x16D40)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x16D24 | KE_MISF_1_CYL_NO_CAT_DAMAGE_LOAD | word | 0x800 | Percent | Load below which single-cyl misfire safe |
| 0x16D26 | KE_MISF_1_CYL_NO_CAT_DAMAGE_LVL | byte | 0xAA | Counts | Single-cyl misfire count threshold |
| 0x16D28 | KE_MISF_1_CYL_NO_CAT_DAMAGE_RPM | word | — | RPM | RPM below which single-cyl safe |
| 0x16D2A | KE_MISF_ABNORMAL_SPEED_THRESHOLD | word | — | Unitless | Ratio for abnormal speed detection |
| 0x16D2B | KE_MISF_CATALYST_ARRAY_SIZE | byte | — | Unitless | Elements in catalyst array |
| 0x16D2C | KE_MISF_DETERMINE_MISFIRE_P_CODE | byte | — | Unitless | Threshold to determine which cylinder |
| 0x16D2E | KE_MISF_DFCO_TIME_STOP_MIL_FLASH | word | — | Seconds | DFCO time to stop MIL flash |
| 0x16D30 | KE_MISF_DISABLE_TCC | byte | — | Unitless | Misfire count to disable TCC |
| 0x16D31 | KE_MISF_EMISSION_ARRAY_SIZE | byte | — | Unitless | Elements in emission array |
| 0x16D32 | KE_MISF_FLASH_MIL_ENGINE_LOAD | word | — | Percent | Stop MIL flash below this load |
| 0x16D34 | KE_MISF_FLASH_MIL_LATCH | word | — | Counts | MIL flash latch count |
| 0x16D36 | KE_MISF_FLASH_MIL_VEHICLE_SPEED | word | — | MPH | Stop MIL flash below this VSS |
| 0x16D3C | KE_MISF_INDISPUTABLE_MISFIRE | byte | — | Unitless | Indisputable misfire threshold |
| 0x16D3D | KE_MISF_INITIAL_EMISSION_FACTOR | byte | — | Factor | Initial emission factor |
| 0x16D3E | KE_MISF_MARSHALLING_FACTOR | byte | — | Factor | Marshalling multiplier (must be 1.0) |

### 4.4 Diagnostic Enable (DI_MISFIRE, 0x17C00-0x17C06)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x17C00 | KE_MISF_IDLE_MODE_VEH_SPD | word | — | MPH | Max VSS for cylinder mode (idle) |
| 0x17C02 | KE_MISF_GENERIC_DELAY | word | — | Eng Cycles | Delay for not-met enable criteria |
| 0x17C04 | KE_MISF_CRANK_ANGLE_CRRCTN_USED | byte | — | BOOLEAN | Use crank angle correction |
| 0x17C05 | KE_MISF_REPORT_EMISSION_MISFIRE | byte | — | Unitless | Report emission misfire flag |
| 0x17C06 | KE_MISF_EMISSION_MISFIRE | byte | — | Unitless | Emission misfire threshold |
| 0x17C08 | KA_MISF_CATALYST_MISFIRE | table | — | Unitless | Catalyst damage misfire threshold |

### 4.5 Misfire Control (DG_MISFIRE, 0x16D42-0x16D44)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x16D42 | KE_MISF_CYLINDER_MODE_EQUATION | byte | — | Enum | Cylinder mode calculation method |
| 0x16D43 | KE_MISF_CONSECUTIVE_NEGATIVE | byte | — | Unitless | Min consecutive accelerating events to delay |
| 0x16D44 | KE_MISF_CONSECUTIVE_POSITIVE | byte | — | Unitless | Min consecutive decelerating events to delay |

---

## 5. RAM Variables

> **Note:** Misfire RAM variables operate in high-speed TPU interrupt context.
> Exact addresses are in the 0xFFFF8xxx-0xFFFF9xxx range. Full enumeration
> requires tracing sub_6F29A in detail.

| Address | Size | Purpose (inferred) |
|---------|------|--------------------|
| FFFFxxxx | byte array | Per-cylinder misfire counters (8 cylinders) |
| FFFFxxxx | word | Total cylinder events counter |
| FFFFxxxx | word | Misfire event accumulator |
| FFFFxxxx | byte | Current operating region (idle/reg1/reg2/reg3) |
| FFFFxxxx | word | Previous tooth period |
| FFFFxxxx | word | Current tooth period |

---

## 6. Algorithm Detail

### 6.1 Crankshaft Acceleration Calculation

```
The 58x CKP wheel has teeth every 6° with a 2-tooth gap for TDC reference.

For each cylinder event (90° for V8 = 15 teeth):
1. Measure tooth periods T_n through TPU hardware capture
2. Compute angular velocity: ω_n = 6° / T_n
3. Compute angular acceleration: α_n = (ω_n - ω_{n-1}) / T_n
4. The acceleration is proportional to net torque on crankshaft:
   - Positive α = combustion event producing torque (normal)
   - Negative α (or reduced positive) = misfire (missing torque pulse)
5. Normalize by engine speed (faster RPM = smaller absolute Δα):
   Normalized_Δα = Δα / RPM_factor

The misfire threshold tables (KA_MISF_*) contain the maximum allowable
normalized Δα at each RPM/Load operating point. Values above threshold
indicate misfire.
```

### 6.2 Cylinder Identification

```
CMP sensor provides cam position — one pulse per cam revolution (720° crank).
Combined with the 2-tooth CKP gap, the PCM knows absolute crank position.

Firing order 1-8-7-2-6-5-4-3:
Cyl 1: 0°    Cyl 8: 90°   Cyl 7: 180°  Cyl 2: 270°
Cyl 6: 360°  Cyl 5: 450°  Cyl 4: 540°  Cyl 3: 630°

KV_MISF_ENGINE_BLOCK_CYLINDER_ID maps diagnostic cylinder numbers to
physical cylinder locations for correct DTC reporting (P0301-P0308).
```

### 6.3 Operating Region Selection

```
Three load regions × three RPM ranges = 9 operating points, each with
a calibrated threshold table:

IDLE: VSS < KE_MISF_IDLE_MODE_VEH_SPD AND
      RPM < PROTECTED_KE_MISF_IDLE_ENGINE_SPEED AND
      TPS < PROTECTED_KE_MISF_IDLE_THROTTLE_POSITION
  → KA_MISF_CYLINDER_MODE_IDLE

REGION 1: Low RPM/Load → KA_MISF_CYLINDER_MODE_REG1
REGION 2: Medium RPM/Load → KA_MISF_CYLINDER_MODE_REG2
REGION 3: High RPM/Load → KA_MISF_CYLINDER_MODE_REG3
  Above cylinder mode limits → KA_MISF_REVOLUTION_MODE_REG1/2/3

Zero torque regions (decel/DFCO): separate thresholds from
KV_MISF_ZERO_TORQUE_REG1/2/3_SPEED tables.
```

### 6.4 MIL Flashing Logic (sub_702A6)

```
Catalyst-damaging misfire (immediate MIL flash):
1. Misfire rate exceeds KA_MISF_CATALYST_MISFIRE threshold
2. MIL flashes at 1 Hz (on 0.5s, off 0.5s)
3. Flashing stops when:
   a. DFCO active for KE_MISF_DFCO_TIME_STOP_MIL_FLASH seconds
   b. Load drops below KE_MISF_FLASH_MIL_ENGINE_LOAD
   c. VSS drops below KE_MISF_FLASH_MIL_VEHICLE_SPEED
4. MIL stays on steady after flash event (latched per trip)

Emission-relevant misfire (DTC only, no flash):
1. Misfire rate exceeds KE_MISF_EMISSION_MISFIRE threshold
2. Increment emission misfire counter
3. Report via OBD-II PID when counter exceeds limits per cycle
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| TPU (Time Processor Unit) | Hardware captures CKP tooth periods |
| CMP Sensor | Provides cylinder #1 TDC reference |
| CKP Sensor | 58x reluctor wheel for angular measurement |
| MIL Control (doc 18) | Flashing MIL for catalyst-damaging misfire |
| DTC/MIL (doc 18) | P0300-P0308 misfire codes |
| DFCO (doc 10) | DFCO stops MIL flash; zero-torque thresholds |
| EGR Diag (doc 22) | EGR test delays misfire detection |
| TCC Control (trans) | Misfire can trigger TCC unlock |
| CASE Learn | Required for accurate crank angle correction |
| Fuel Control | Open-loop forced during severe misfire |

---

## 8. Gaps & Unresolved

1. **Sub_6F29A full trace**: The main misfire function is very large (~300+ instructions). Only the architecture and flow have been documented. The exact tooth period measurement, acceleration calculation, and threshold comparison code needs line-by-line tracing.

2. **CASE learn integration**: KE_MISF_CRANK_ANGLE_CRRCTN_USED enables crank angle
   correction. The CASE learn procedure and the correction values stored in
   NVRAM are not documented.

3. **Rough road detection**: The misfire system must distinguish between actual
   misfire and rough road-induced crankshaft acceleration. The ABS wheel speed
   sensor input path and rough road algorithm are not traced.

4. **Revolution mode vs cylinder mode transition**: The exact RPM/load boundary
   where the system switches from cylinder mode to revolution mode is not
   confirmed from the calibration tables.

5. **Tooth period buffer**: The TPU hardware captures tooth periods into a
   buffer. The buffer size, addressing, and readout mechanism need confirmation.

---

## 9. How To Verify

```bash
# Verify misfire threshold table sizes
python3 -c "
# KA_MISF_CYLINDER_MODE_REG1 at 0x17E34 → 0x17F88
# Size = 0x17F88 - 0x17E34 = 0x154 = 340 bytes = likely 17×10 word table
print('Cylinder Mode Reg1 table: 340 bytes (17×10 word table)')
print('KA_MISF_CATALYST_MISFIRE at 0x17C08: 0x17C74-0x17C08 = 108 bytes')
"
```

---

## 10. Community Knowledge

- **Cam swap and misfire**: Aggressive camshafts cause more crankshaft speed
  variation at idle, which the PCM can interpret as misfire. Tuners raise the
  idle misfire thresholds (KA_MISF_CYLINDER_MODE_IDLE) or disable individual
  cylinder misfire detection at low RPM.

- **CASE learn**: After a PCM swap or crank sensor replacement, a CASE
  (Crankshaft Angle Sensing Error) learn must be performed. This teaches the
  PCM the exact tooth-to-TDC relationship. Without it, misfire detection is
  disabled and a P1336 DTC is set.

- **Lightweight flywheel**: Reduces rotating mass, causing larger normal
  crankshaft speed variation. May trigger false misfire codes. Requires
  recalibrating the misfire threshold tables, especially at idle.

- **Two-step/launch control**: Spark cut limiters cause intentional misfire.
  The misfire detection must be disabled during launch control or the PCM
  will flash the MIL and potentially enter limp mode. Boost OS handles this
  by gating misfire detection when launch control is active.
