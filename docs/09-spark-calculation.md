# P59 PCM OS 12587603 — Complete Spark Calculation Chain

## Overview

The spark advance calculation in the P59 PCM is a multi-stage pipeline that computes the final spark timing from numerous contributing factors. The main entry point is `loc_3A8A8`, called from the main event loop (`DoLoopA+19A`).

---

## Data Flow Diagram

```
                       ┌──────────────────────────────────────────────┐
                       │             loc_3A8A8 (main spark loop)      │
                       │  Called from DoLoopA+19A every ~12.5ms       │
                       └──────────────────┬───────────────────────────┘
                                          │
         ┌────────────┬──────────┬────────┼───────────┬───────────┬───────────┐
         ▼            ▼          ▼        ▼           ▼           ▼           ▼
    sub_3B38C    sub_39F12   sub_3A2A8 sub_3A330   sub_3A436   sub_3A4CE   sub_3A5CE
   Throttle/     Base       Coolant    EGR        EQ Ratio    Idle        IAT
   VSS State    Spark       Spark      Spark      Spark       Spark       Spark
         │            │          │        │           │           │           │
         │    ┌───────┼──────────┼────────┼───────────┼───────────┼───────────┘
         │    │       ▼          ▼        ▼           ▼           ▼
         │    │  ┌─────────────────────────────────────────┐
         ▼    │  │         sub_3AF0C                       │
  FFFF984E   │  │     Catalyst Lightoff                    │
  (CT flag)  │  │     FFFF983C (retard)                   │
         │    │  └─────────────────────────────────────────┘
         │    │       │
         │    │       ▼
         │    │  ┌─────────────────────────────────────────┐
         │    │  │         sub_3A63E                       │
         │    │  │     FFS E80 Spark Shift                 │
         │    │  │     FFFF988A (FFS offset)              │
         │    │  └─────────────────────────────────────────┘
         │    │       │
         │    │       ▼
         │    │  ┌─────────────────────────────────────────┐
         │    │  │         sub_3A6D0                       │
         │    │  │     Piston Slap Spark Retard            │
         │    │  │     FFFF989E (retard)                  │
         │    │  └─────────────────────────────────────────┘
         │    │       │
         │    │       ▼
         │    │  ┌─────────────────────────────────────────┐
         │    │  │         loc_3A96C                       │
         │    │  │     Spark SUM + Smoothing               │
         │    │  │                                         │
         │    │  │  d1 = FFFF983A (base) + sub+adds       │
         │    │  │  + FFFF9D34 (launch spark)              │
         │    │  │  + FFFF989E (piston slap)               │
         │    │  │  + FFFF983C (cat lightoff)              │
         │    │  │  → FFFF9880 (final spark out)           │
         │    │  │  → FFFF987C (smoothed spark)            │
         │    │  └─────────────────────────────────────────┘
         │    │
         │    └─────────────────────────────────────────────── FFFF9880 is
         │                                                     final spark
         │
         └─── sub_3B38C sets FFFF984E (closed-throttle flag)
              based on TPS and vehicle speed thresholds
```

---

## Separately Called Functions

### sub_3BDC4 — Launch Spark / Knock Energy (DoLoopA+BC)

```
RAM INPUTS:  FFFFAD23 (run state, must == 3)
             FFFFAC47 (cylinder counter)
             FFFF8254 (knock fault bits)
             FFFFA1F6 (PE active flag)
             FFFFAEE0 (coolant temp)
             FFFFAEE6 (engine speed)
             FFFFAEEA (MAP)
             FFFFAEEC (baro)
             FFFFAD1E (engine run time)
             FFFFADB0 (coolant temp raw)
             FFFF9D90 (launch countdown)
             FFFF9D91 (ramp-out done flag)
             FFFF9D99 (knock enable)
             FFFF9D32 (knock event flag)
             FFFF9D68 (knock detected)
RAM OUTPUTS: FFFF9D34 (launch spark value)
             FFFF9D30 (knock retard accumulator)
             FFFF9D76 (run time ramp multiplier)
             FFFF9D7C (delta cyl air threshold)
             FFFF9D78 (soak time multiplier)
             FFFF9D7A (RPM multiplier)
             FFFF9D90 (launch hold pulses)
             FFFF9D91 (ramp out done)
             FFFF9C/9D36-9D6x (knock energy thresholds per cylinder)
CAL TABLES:  SPARK_KNOCK_KA_KNOCK_ENERGY_MAD
             SPARK_KNOCK_KV_KNOCK_ENERGY_MAD
             SPARK_KNOCK_KV_KNOCK_ENERGY_MAD_GAIN
             SPARK_KNOCK_KA_KNOCK_ENERGY_MAD_GAIN
             SPARK_KNOCK_KV_TIP_IN_KNOCK_ENERGY_MAD
             SPARK_KNOCK_KV_KNOCK_FAST_IR_ATTACK_RATE
             SPARK_KNOCK_KV_KNOCK_FAST_ATTACK_COOL_GAIN
             SPARK_KNOCK_KV_KNOCK_FAST_ATTACK_BARO_GAIN
             SPARK_KNOCK_KV_KNOCK_RETARD_LIMIT_LOAD
             SPARK_KNOCK_KV_KNOCK_RETARD_LIMIT_SPEED
             SPARK_KNOCK_KV_KNOCK_RETARD_DEFAULT_LOAD
             SPARK_ADVANCE_KA_LAUNCH_SPARK
             SPARK_ADVANCE_KE_LAUNCH_SPARK_MAXCLTSOAKENABLE
             SPARK_ADVANCE_KE_LAUNCH_SPARK_MINRUNSOAKENABLE
             SPARK_ADVANCE_KV_LAUNCH_SPARK_SOAK_MULT
             SPARK_ADVANCE_KE_LAUNCH_SPARKRPMMULTCOOLENABLE
             SPARK_ADVANCE_KE_LAUNCH_SPARKRPMRUNTIME
             SPARK_ADVANCE_KV_LAUNCH_SPARK_RPM_MULTIPLIER
             SPARK_ADVANCE_KV_LAUNCH_SPARK_DELTA_CYLAIRMASS
             SPARK_ADVANCE_KV_LAUNCH_SPARK_DELTA_CYLAIRMULT
             SPARK_ADVANCE_KV_LAUNCH_SPARK_DELT_CA_TPS_MULT
             SPARK_ADVANCE_KV_LAUNCH_SPARK_DURATION
             SPARK_ADVANCE_KV_LAUNCH_SPARK_RAMP_OUT_MULT
             SPARK_KNOCK_KE_MUX_PATTERN_CONTROL
ALGORITHM:
  1. MUST be in run state 3 (running), cyl counter not at 8
  2. Phase 1 - Knock Energy MAD Setup:
     - If Global detection mode: simple 1D table lookup for gain
     - If Individual cylinder: 2D lookup (MAP×RPM) for gain, per-cylinder energy thresholds
     - Calls sub_3C68C for per-cylinder knock setup
  3. Phase 2 - Knock Retard Fast Attack:
     - If knock detected (FFFF9D68 != 0):
       - Set FFFF9D32 = 1
       - Calculate attack rate: speed table × coolant gain × baro gain
       - Multiply by knock integrator and add to retard accumulator (FFFF9D30)
     - Apply retard limit (load-based or speed-based for PE)
     - If knock system fault: use default retard value
  4. Phase 3 - Knock Retard Limit:
     - Against SPARK_KNOCK_KV_KNOCK_RETARD_LIMIT_LOAD or _SPEED
     - Clamp FFFF9D30 to limit
  5. Phase 4 - Launch Spark Initiation:
     - Compute run-time ramp multiplier: (engine_run_time × 0x1000) / LIGHTOFF_AND_LAUNCHRAMPINTIME
     - Clamp to 0x1000 max → FFFF9D76
     - Compute delta cylinder airmass threshold from coolant+speed tables
     - Apply TPS multiplier if coolant low → FFFF9D7C
  6. Phase 5 - Launch Spark Activation:
     - If launch countdown (FFFF9D90) == 0 and CLOSED THROTTLE and delta cyl air > threshold:
       - Set FFFF9D90 = launch_duration_table(coolant)
       - Compute engine runtime for lookup (clamp 0-0x600)
       - Look up SPARK_ADVANCE_KA_LAUNCH_SPARK (coolant × runtime) → FFFF9D34
       - Apply soak time multiplier if coolant and run time conditions met
       - Apply RPM multiplier if coolant and run time conditions met
       - Apply run-time ramp multiplier → final FFFF9D34
  7. Phase 6 - Launch Spark Countdown:
     - Decrement FFFF9D90 each call
     - When FFFF9D90 reaches 0 and ramp not done:
       - Apply ramp-out multiplier each ref pulse
       - When result < 5 degrees: set FFFF9D91 (ramp done), clear FFFF9D34
  8. Phase 7 - Knock Mux Control:
     - If individual knock detection: handle cylinder mux sequencing
```

### sub_2FAFC + sub_2FC1E — Flat Foot Shift Spark (sub_2F780+36E / loc_2FC3E)

#### sub_2FAFC (precursor)
```
RAM INPUTS:  FFFF8242 (alcohol content)
             FFFFAEE0 (coolant temp)
             FFFFAEF8 (this is the key output)
RAM OUTPUTS: FFFF9FC4 (stoichiometric fuel/air ratio for flex fuel)
             FFFFAEF8 (alcohol blend factor for FFS, computed from FFFF8242)
             FFFF9FC6 (open loop EQ ratio blend factor)
             FFFF9FCE (fuel blend calc 1)
             FFFF9FCC (stomp comp delta limit)
             FFFF9FCA (stomp comp delta low limit)
             FFFF9FD0 (fuel blend calc 2)
             FFFF9FD2 (fuel blend calc 3)
             FFFF9FD4 (fuel blend calc 4)
             FFFF9FD6 (fuel blend calc 5)
             FFFF9FD8 (thermal efficiency blend factor)
CAL TABLES:  FUEL_EQ_KV_STOICHIOMETRIC_FUEL_AIR
             FUEL_EQ_KV_OPEN_LP_EQ_RATIO_BLEND_FACTOR
             FUEL_DY_KV_K4_STOMP_COMP_DELTA_LIMIT
             FUEL_DY_KV_K5_STOMP_COMP_DELTA_LOW_LIMIT
             ENG_TORQUE_KV_THERMAL_EFF_BLEND_FACTOR
             Various tables at 0xBC3E, 0xBD10, 0xBDCE, 0xBE8C, 0xBF4A (fuel related)
ALGORITHM:
  1. Compute stoichiometric fuel/air ratio from ethanol content via table
  2. Compute alcohol blend factor (FFFFAEF8): linear from ethanol content
     - If ethanol < 0x400: divide by 2
     - If ethanol 0x400-0x1000: linear interpolate 0x200-0x400
     - If ethanol >= 0x1000: clamp to 0x400
  3. Multiple 2D table lookups for fuel dynamics and torque efficiency
```

#### sub_2FC1E (FFS spark blend)
```
RAM INPUTS:  FFFFAEF8 (alcohol blend factor, from sub_2FAFC)
RAM OUTPUTS: FFFF9FC8 (FFS spark blend factor)
CAL TABLES:  SPARK_ADVANCE_KV_FFS_SPARK_BLEND_FACTOR
ALGORITHM:
  1. Load alcohol blend factor from FFFFAEF8
  2. 1D table lookup: SPARK_ADVANCE_KV_FFS_SPARK_BLEND_FACTOR[FFFFAEF8]
  3. Store result to FFFF9FC8
  NOTE: This is an extremely short function (6 instructions). The blend factor
        is then used by sub_3A63E and sub_3A754 to blend FFS spark offsets.
```

---

## Detailed Function Analysis

### sub_3B38C — Closed Throttle / Vehicle Speed State Detection

**Address:** 0x3B38C

```
INPUTS:
  FFFFAB66  (TPS raw)
  FFFFAEBC  (vehicle speed)
  FFFF984E  (current closed-throttle state)

OUTPUTS:
  FFFF984E  (closed-throttle flag: 0 = open throttle driving, 1 = closed throttle)

CAL TABLES:
  SPARK_ADVANCE_KE_CT_TPS_THRESHOLD       (TPS threshold for CT, %)
  SPARK_ADVANCE_KE_CT_TPS_HYSTERESIS      (TPS hysteresis, %)
  SPARK_ADVANCE_KE_CT_VEH_SPD_THRESHOLD   (VSS threshold for CT, MPH)
  SPARK_ADVANCE_KE_CT_VEH_SPD_HYSTERESIS  (VSS hysteresis, MPH)

ALGORITHM:
  1. If already closed-throttle (FFFF984E != 0):
     - Check if TPS > (THRESHOLD + HYSTERESIS) OR VSS > (THRESHOLD + HYSTERESIS)
     - If so: SET FFFF984E = 1 (still closed throttle)
     - If not: CLEAR FFFF984E = 0 (exit closed throttle)
  2. If not closed-throttle (FFFF984E == 0):
     - Check if TPS < THRESHOLD AND VSS < THRESHOLD
     - If so: CLEAR FFFF984E = 0 (enter closed throttle)
     - If not: SET FFFF984E = 1 (stay open throttle)

  This is a classic hysteresis state machine for closed-throttle detection.
```

---

### sub_39F12 — Base Spark Calculation

**Address:** 0x39F12

This is the core base spark function. It handles the state machine for selecting between:
- Closed Throttle Park/Neutral (CT_PARK)
- Closed Throttle Drive (CT_DRIVE)
- Open Throttle Low Octane (OT_LOW_OCTANE)
- Open Throttle High Octane (OT_HIGH_OCTANE)

```
INPUTS:
  FFFFA3AF  (unknown, compared to #5 — likely transmission PRNDL status)
  FFFF984E  (closed-throttle flag from sub_3B38C)
  FFFF98D0  (spark state flag - "park mode active")
  FFFF98D3  (spark state flag - "drive mode active") 
  FFFF98D5  (spark state flag - "park intermediate")
  FFFF98D2  (spark state flag - "drive confirmed")
  FFFF98D4  (spark state flag - "park-D intermediate")
  FFFF98D7  (spark state flag - "drive mode 2 active")
  FFFF98D9  (spark state flag - "drive intermediate")
  FFFF98D6  (spark state flag - "park confirmed")
  FFFF98D8  (spark state flag - "park-D intermediate 2")
  FFFFA0EA  (airflow / cylinder airmass — divided by 2 for table axis)
  FFFFA562  (engine speed RPM)
  FFFFAEDA  (MAP sensor reading)
  FFFFAEDC  (barometric pressure)
  FFFF82DA  (octane scalar/modifier)
  FFFF989A  (octane blend factor source)
  FFFF98C2  (unknown — ramp timer for PN→DR transition)
  FFFF98C0  (unknown — ramp timer for DR→PN transition)
  FFFFB544  (current time reference)

OUTPUTS:
  FFFF983A  (base spark advance — final output, degrees × 0.015259)
  FFFF984A  (raw base spark, before octane blend)
  FFFF9858  (octane blend interpolant)
  FFFF98A0  (ramp target for PN→DR transition)
  FFFF9882  (ramp target for DR→PN transition)
  FFFF98D0  (park mode active flag)
  FFFF98D2  (drive confirmed flag)
  FFFF98D3  (drive mode active flag)
  FFFF98D4  (park-D intermediate flag)
  FFFF98D5  (park intermediate flag)
  FFFF98D6  (park confirmed flag)
  FFFF98D7  (drive mode 2 active flag)
  FFFF98D8  (park-D intermediate 2 flag)
  FFFF98D9  (drive intermediate flag)

CAL TABLES:
  SPARK_ADVANCE_KA_MAIN_CT_PARK       (CT park/neutral spark, 13×? table, RPM×Airflow)
  SPARK_ADVANCE_KA_MAIN_CT_DRIVE      (CT drive spark, 13×? table, RPM×Airflow)
  SPARK_ADVANCE_KA_MAIN_OT_HIGH_OCTANE (OT high octane, 25×? table, MAP×Baro)
  SPARK_ADVANCE_KA_MAIN_OT_LOW_OCTANE  (OT low octane, 25×? table, MAP×Baro)
  SPARK_ADVANCE_KE_SHIFT_PN_TO_DR_RAMP (ramp rate PN→DR, degrees per step)
  SPARK_ADVANCE_KE_SHIFT_DR_TO_PN_RAMP (ramp rate DR→PN, degrees per step)

JSR CALLS:
  sub_3CD16 (table lookup for CT tables — RPM×Airflow)
  SurfaceTableLookup (for OT tables — MAP×Baro)
  sub_276D4 (ramp timer check — determines if target reached)

ALGORITHM (state machine):

  STATE: CT PARK (initial cold start)
  Conditions: closed throttle + transmission in Park/Neutral + no previous state
  → Look up SPARK_ADVANCE_KA_MAIN_CT_PARK(RPM, Airflow/2)
  → Set FFFF983A, FFFF984A, FFFF98D0=1

  STATE: CT DRIVE (transmission in Drive, closed throttle)
  Conditions: closed throttle + transmission in Drive + no previous state
  → Look up SPARK_ADVANCE_KA_MAIN_CT_DRIVE(RPM, Airflow/2)
  → Set FFFF983A, FFFF984A, flags

  STATE: OT OCTANE BLEND (open throttle, both high and low octane)
  Conditions: NOT closed throttle
  → Look up SPARK_ADVANCE_KA_MAIN_OT_LOW_OCTANE(MAP, Baro)
  → Look up SPARK_ADVANCE_KA_MAIN_OT_HIGH_OCTANE(MAP, Baro)
  → Compute octane blend:
    blend_factor = ((0x1000 - FFFF82DA) * FFFF989A) >> 12
    base_spark = HIGH_OCTANE - ((HIGH_OCTANE - LOW_OCTANE) * blend_factor) >> 12
  → Set FFFF983A, FFFF984A, FFFF9858 (blend factor)

  TRANSITIONS:
  - CT Park → CT Drive: Ramp using SPARK_ADVANCE_KE_SHIFT_PN_TO_DR_RAMP
    (add ramp value each iteration until drive table value reached)
  - CT Drive → CT Park: Ramp using SPARK_ADVANCE_KE_SHIFT_DR_TO_PN_RAMP
    (subtract ramp value each iteration until park table value reached)
  - All transitions use sub_276D4 for timer-based ramping
```

---

### sub_3A2A8 — Coolant Temperature Spark Contribution

**Address:** 0x3A2A8

```
INPUTS:
  FFFFAEDE  (coolant temperature scaled)
  FFFFAEDC  (barometric pressure)
  FFFFA562  (engine speed RPM)

OUTPUTS:
  FFFF983E  (coolant temp spark contribution, degrees × 0.015259)

CAL TABLES:
  SPARK_ADVANCE_KA_CLT_SPARK      (coolant temp spark, 37×? table)
  SPARK_ADVANCE_KA_CLT_RPM_MODIFIER (RPM modifier for CLT spark, 0-2 multiplier)

ALGORITHM:
  1. Look up base CLT spark: SPARK_ADVANCE_KA_CLT_SPARK(Baro, CLT) → d6
  2. Compute RPM modifier axis:
     - If RPM < 0x5000 (5120 RPM): axis = RPM / 4
     - Else: axis = 0x1400 (max)
  3. Look up RPM modifier: sub_2696E(SPARK_ADVANCE_KA_CLT_RPM_MODIFIER, RPM_axis, CLT_axis) → d0
  4. Result = (d6 * d0) / 0x1000
  5. Store to FFFF983E
```

---

### sub_3A330 — EGR Spark Contribution

**Address:** 0x3A330

```
INPUTS:
  EGR_KE_EGR_ENABLED     (EGR enable flag)
  FFFFA25A               (EGR duty cycle)
  FFFFA258               (EGR mass flow)
  FFFFA254               (engine mass flow)
  FFFFA262               (EGR spark scalar)
  FFFFA0EA               (airflow / cylinder airmass)
  FFFFA562               (engine speed RPM)
  FFFF9886               (EGR timer)
  FFFFB544               (current time)
  FFFF9842               (previous EGR spark?)

OUTPUTS:
  FFFF9898  (EGR spark contribution, degrees × 0.015259)
  FFFF9886  (EGR timer update)

CAL TABLES:
  SPARK_ADVANCE_KE_EGR_DUTY_CYCLE_SPARK  (duty cycle threshold, %)
  SPARK_ADVANCE_KE_EGR_SPARK_DELAY       (time delay, seconds)
  SPARK_ADVANCE_KE_EGR_SPARK_MULT_LIMIT  (multiplier limit)
  SPARK_ADVANCE_KA_EGR_SPARK             (EGR spark contribution table)

ALGORITHM:
  1. Check EGR enabled
  2. Check EGR duty cycle > threshold
  3. Check time delay since last state change (using sub_276F4 timer)
  4. Compute EGR fraction multiplier:
     - multiplier = (EGR_mass_flow << 12) / engine_mass_flow
     - Clamp to SPARK_ADVANCE_KE_EGR_SPARK_MULT_LIMIT
  5. Look up base EGR spark: sub_3CD16(SPARK_ADVANCE_KA_EGR_SPARK, RPM, CylAir/2)
  6. Apply EGR fraction multiplier and EGR spark scalar:
     - result = (base_EGR_spark * multiplier * EGR_scalar) / 0x1000
  7. Store to FFFF9898
```

---

### sub_3A436 — Equivalence Ratio Spark Contribution

**Address:** 0x3A436

```
INPUTS:
  FFFFACAA  (??? flag)
  FFFFA1F6  (PE active flag)
  FFFFA1FC  (??? flag)
  FFFFA1F5  (??? flag)
  FFFFA1EE  (EQ ratio / commanded AFR)
  FFFFAEE6  (engine speed RPM)
  FFFFAEEA  (MAP sensor)

OUTPUTS:
  FFFF9888  (EQ ratio spark contribution, degrees × 0.015259)

CAL TABLES:
  SPARK_ADVANCE_KA_EQ_RATIO_SPARK      (EQ ratio spark, RPM×EQ ratio table)
  SPARK_ADVANCE_KV_EQ_RATIO_MAP_MODIFIER (MAP modifier, 0-2 multiplier)

ALGORITHM:
  1. If any enrichment flag set (PE, etc.):
     a. Scale EQ ratio axis: (EQ_ratio - 0x333) / 0x33, clamp 0-0xF00
     b. Look up: SurfaceTableLookup(SPARK_ADVANCE_KA_EQ_RATIO_SPARK, RPM, EQ_axis)
     c. Look up MAP modifier from 1D table
     d. Result = (base_EQ_spark * MAP_modifier) / 0x1000
     e. Store to FFFF9888
  2. If no enrichment: clear FFFF9888 = 0
```

---

### sub_3A4CE — Idle Spark Control (Overspeed/Underspeed)

**Address:** 0x3A4CE

```
INPUTS:
  FFFFA7DF  (bit 3 = ??? disable)
  FFFF984E  (closed throttle flag)
  FFFFA6F7  (idle state flag — 3 = idle flare mode)
  FFFFA6F0  (idle RPM error — positive = overspeed, negative = underspeed)
  FFFF988E  (idle flare multiplier)

OUTPUTS:
  FFFF9846  (idle spark contribution, degrees × 0.015259)

CAL TABLES:
  SPARK_ADVANCE_KV_IDLE_FLARE_CONTROL       (flare spark table based on RPM error)
  SPARK_ADVANCE_KV_IDLE_OVERSPEED_ERROR     (overspeed spark table)
  SPARK_ADVANCE_KV_IDLE_UNDERSPEED_ERROR    (underspeed spark table)
  SPARK_ADVANCE_KE_POWER_STEERING_PRESS_MOD (P/S pressure spark modifier)

JSR CALLS:
  sub_81B3C (P/S pressure switch check)

ALGORITHM:
  1. Check disable flag (FFFFA7DF bit 3)
  2. Check closed throttle (must be CT)
  3. IDLE FLARE MODE (FFFFA6F7 == 3):
     - Scale RPM error axis (0 to 0xA00)
     - Look up: SPARK_ADVANCE_KV_IDLE_FLARE_CONTROL
     - Multiply by FFFF988E (flare multiplier)
  4. OVERSPEED (RPM error > 0):
     - Scale RPM error to axis:
       * 0-0x100: error * 4
       * 0x100-0x600: (error - 0x100) + 0x400
       * ≥0x600: 0x900
     - Look up: SPARK_ADVANCE_KV_IDLE_OVERSPEED_ERROR
  5. UNDERSPEED (RPM error < 0):
     - Scale RPM error to axis:
       * -0x600: error + 0x600 (0x000-0x100)
       * -0x100-0: error + 0x100 (0x100-0x500)
       * 0: 0x900
     - Look up: SPARK_ADVANCE_KV_IDLE_UNDERSPEED_ERROR
  6. Check P/S pressure switch (sub_81B3C)
  7. If P/S active: add SPARK_ADVANCE_KE_POWER_STEERING_PRESS_MOD
  8. Store to FFFF9846
```

---

### sub_3A5CE — Intake Air Temperature Spark

**Address:** 0x3A5CE

```
INPUTS:
  FFFFB3E8  (IAT sensor — intake air temperature)
  FFFFAEDC  (barometric pressure)
  FFFFAEE6  (engine speed RPM)
  FFFF988C  (IAT spark base?)

OUTPUTS:
  FFFF9890  (IAT spark contribution, degrees × 0.015259)

CAL TABLES:
  SPARK_ADVANCE_KA_IAT_SPARK       (IAT spark, RPM×IAT? table)
  SPARK_ADVANCE_KV_IAT_RPM_MODIFIER (RPM modifier, multiplier)

ALGORITHM:
  1. Scale IAT axis:
     - If IAT < -0x100 (negative): 0
     - If -0x100 ≤ IAT < 0x900: (IAT + 0x100) * 2
     - If IAT ≥ 0x900: 0x1400 (max)
  2. Look up base IAT spark: SurfaceTableLookup(SPARK_ADVANCE_KA_IAT_SPARK, Baro, IAT_axis) → d0
  3. Look up RPM modifier from 1D table: SPARK_ADVANCE_KV_IAT_RPM_MODIFIER[RPM] → d3
  4. Result = (d0 * FFFF988C * d3) >> 12
  5. Store to FFFF9890
```

---

### sub_3AF0C — Catalyst Lightoff Spark Retard

**Address:** 0x3AF0C

```
INPUTS:
  FFFF986D  (lightoff complete flag — if set, skip)
  FFFFAD1E  (engine run time, seconds)
  FFFFAEE0  (coolant temperature)
  FFFFAB66  (TPS position)
  FFFFA562  (engine speed RPM)
  FFFFAEDC  (barometric pressure)
  FFFF986C  (vacuum enable latch)
  FFFF986E  (vacuum disable latch)
  FFFF986F  (lightoff re-enable flag)
  FFFF989C  (previous vacuum state)
  FFFF9866  (re-enable ref pulse counter)
  FFFF9868  (re-enable timer)
  FFFF986A  (re-enable ramp time)
  FFFF9D34  (launch spark — will disable lightoff if active)
  FFFFB298  (manifold vacuum, kPa)

OUTPUTS:
  FFFF983C  (catalyst lightoff spark retard, degrees POSITIVE = retard)
  FFFF9870  (run time ramp multiplier)
  FFFF985E  (coolant multiplier)
  FFFF9860  (TPS multiplier)
  FFFF9862  (re-enable ramp factor)
  FFFF986D  (lightoff complete flag)
  FFFF986C  (vacuum enable latch)
  FFFF986E  (vacuum disable latch)
  FFFF986F  (lightoff re-enable latch)
  FFFF989C  (previous vacuum state for hysteresis)
  FFFF9866  (re-enable ref pulse counter)
  FFFF9864  (re-enable ramp factor per ref)

CAL TABLES:
  SPARK_ADVANCE_KE_LIGHTOFF_AND_LAUNCHRAMPINTIME  (ramp in time, sec)
  SPARK_ADVANCE_KV_CAT_LIGHTOFF_COOLANT_MULT      (coolant multiplier, 0-2)
  SPARK_ADVANCE_KV_CAT_LIGHTOFF_THROTTLE_MULT     (TPS multiplier, 0-1)
  SPARK_ADVANCE_KA_CAT_LIGHTOFF_SPARK_RETARD      (base retard table, RPM×Baro)
  SPARK_ADVANCE_KE_CAT_LIGHTOFF_SPARK_VACUUM_ENA  (vacuum enable threshold, kPa)
  SPARK_ADVANCE_KE_CAT_LIGHTOFF_SPARK_VACUUM_DIS  (vacuum disable threshold, kPa)
  SPARK_ADVANCE_KE_CAT_LIGHTOFF_REENABLE_REFS     (re-enable ramp ref pulses)

ALGORITHM:
  1. If FFFF986D != 0 (lightoff complete), skip entire function
  2. Compute run time ramp multiplier:
     - If engine_run_time < LIGHTOFF_AND_LAUNCHRAMPINTIME:
       ramp = (engine_run_time * 0x1000) / LIGHTOFF_AND_LAUNCHRAMPINTIME
       clamp to 0x1000 max
     - Else: ramp = 0x1000 (fully ramped in)
     - Store to FFFF9870
  3. Look up coolant multiplier: SPARK_ADVANCE_KV_CAT_LIGHTOFF_COOLANT_MULT[CLT] → FFFF985E
  4. Look up TPS multiplier: SPARK_ADVANCE_KV_CAT_LIGHTOFF_THROTTLE_MULT[TPS/2] → FFFF9860
  5. Scale RPM axis (same as others: ÷4 or clamp 0x1400)
  6. Base retard lookup: SurfaceTableLookup(SPARK_ADVANCE_KA_CAT_LIGHTOFF_SPARK_RETARD, RPM, Baro)
  7. Apply multipliers:
     - result = base_retard * ramp_multiplier * coolant_mult / 0x1000
     - result = result * TPS_multiplier / 0x1000
  8. VACUUM DISABLE HANDLING:
     - If launch spark is active (FFFF9D34 != 0) and lightoff not already disabled:
       - Latch vacuum disable: set FFFF986C, clear FFFF986E
     - Check vacuum against thresholds:
       - ENABLE: if vacuum < SPARK_ADVANCE_KE_CAT_LIGHTOFF_SPARK_VACUUM_ENA
       - DISABLE: if vacuum > SPARK_ADVANCE_KE_CAT_LIGHTOFF_SPARK_VACUUM_DIS
     - If disabled (vacuum or launch): clear FFFF983C
  9. RE-ENABLE RAMP:
     - If enabled and NOT active: compute ramp factor
     - factor = (ref_count * 0x1000) / REENABLE_REFS, clamp to 0x1000
     - result = base_result * factor
     - Increment ref counter
     - When ref_count reaches REENABLE_REFS: set FFFF986F (fully re-enabled)
  10. STORE final value to FFFF983C
```

---

### sub_3A63E — FFS E80 Spark Shift

**Address:** 0x3A63E

```
INPUTS:
  FFFFA562  (engine speed RPM)
  FFFFA0EA  (airflow / cylinder airmass)
  FFFF9FC8  (FFS spark blend factor — from sub_2FC1E)

OUTPUTS:
  FFFF988A  (FFS E80 spark shift, degrees × 0.015259)

CAL TABLES:
  SPARK_ADVANCE_KA_FFS_E80_SPARK_SHIFT  (FFS E80 spark offset table, RPM×Airflow)

ALGORITHM:
  1. Scale airflow axis: (airflow/2 - 0x148) / 0xA3D, clamp 0-0x1407
  2. Scale RPM axis: (RPM - 0x800) / 8, clamp 0-0x1100
  3. Look up: SurfaceTableLookup(SPARK_ADVANCE_KA_FFS_E80_SPARK_SHIFT, RPM_scaled, Airflow_scaled)
  4. Apply FFS blend factor from FFFF9FC8:
     result = (table_value * FFFF9FC8) >> 12
  5. Store to FFFF988A
```

---

### sub_3A6D0 — Piston Slap Spark Retard

**Address:** 0x3A6D0

```
INPUTS:
  FFFFA0E6  (cylinder airmass — raw, undivided)
  FFFFA562  (engine speed RPM)
  FFFFAEE0  (coolant temperature)

OUTPUTS:
  FFFF989E  (piston slap spark retard, degrees × 0.015259)

CAL TABLES:
  SPARK_ADVANCE_KA_PISTON_SLAP_SPARK_RETARD   (piston slap table, RPM×Airflow)
  SPARK_ADVANCE_KV_PISTON_SLAP_COOLANT_MULT   (coolant modifier, unitless)

ALGORITHM:
  1. Scale airflow axis: (airflow - 0x148) / 0x147B, clamp 0-0xE00
  2. Scale RPM axis: RPM / 8, clamp 0-0xA00
  3. Look up: SurfaceTableLookup(SPARK_ADVANCE_KA_PISTON_SLAP_SPARK_RETARD, RPM_scaled, Airmass_scaled)
  4. Look up coolant modifier: SPARK_ADVANCE_KV_PISTON_SLAP_COOLANT_MULT[CLT]
  5. Result = (table_value * coolant_modifier) >> 12
  6. Store to FFFF989E
```

---

### sub_3A754 — MBT Spark (Mean Best Timing)

**Address:** 0x3A754 — Called from sub_7E0BC+100 (torque management, NOT the main spark chain)

```
INPUTS:
  FFFFA562  (engine speed RPM)
  FFFFA0EA  (airflow / cylinder airmass)
  FFFF9FC8  (FFS spark blend factor)
  FFFF9848  (??? base spark reference)
  FFFF98C4  (??? coolant temp spark reference)
  FFFF9884  (torque control spark offset)

OUTPUTS:
  FFFF9834  (MBT delta from base spark, no FFS)
  FFFF9836  (MBT delta from coolant temp spark)
  FFFF9838  (MBT delta final, with torque offset)

CAL TABLES:
  SPARK_ADVANCE_KA_FFS_E80_MBT_SPARK_SHIFT  (FFS E80 MBT offset, RPM×Airflow)
  SPARK_ADVANCE_KA_MBT_SPARK                (MBT spark target, RPM×Airflow)

ALGORITHM:
  1. FIRST PASS: FFS E80 MBT SHIFT
     a. Scale airflow: (airflow/2 - 0x148) / 0x147B, clamp 0-0xA03
     b. Scale RPM: (RPM - 0x800) / 8, clamp 0-0x1100
     c. Look up: SurfaceTableLookup(SPARK_ADVANCE_KA_FFS_E80_MBT_SPARK_SHIFT, RPM, Airflow)
     d. Apply FFS blend: d6 = (table_value * FFFF9FC8) >> 12
  2. SECOND PASS: MBT SPARK
     a. Scale airflow: (airflow/2 - 0x148) / 0x147B, clamp 0-0xE00
     b. Scale RPM: (RPM - 0x800) / 8, clamp 0-0x1300
     c. Look up: sub_2696E(SPARK_ADVANCE_KA_MBT_SPARK, RPM, Airflow)
     d. Add FFS offset: d3 = MBT + d6 (with overflow clamp)
  3. COMPUTE DELTAS:
     - FFFF9834 = d3 - FFFF9848  (MBT delta from base spark)
     - FFFF9836 = d3 - FFFF98C4  (MBT delta from coolant spark)
     - FFFF9838 = FFFF9834 + FFFF9884  (delta + torque control offset)
```

---

### loc_3A96C — Spark Summation and Smoothing

**Address:** 0x3A96C — This is the final stage after all sub-functions return

```
INPUTS (from sub-function outputs):
  FFFF989E  (piston slap spark retard)
  FFFF983C  (catalyst lightoff spark retard — NEGATIVE = retard)
  FFFF983A  (base spark advance)
  FFFF9D34  (launch spark from sub_3BDC4)
  FFFFAEE6  (engine speed, for tables)

INTERMEDIATE:
  FFFF98BE  (pre-smooth spark — raw sum)
  FFFF984C  (???)

OUTPUTS:
  FFFF9880  (final spark advance — THE KEY OUTPUT)
  FFFF987C  (smoothed/spark that goes to HVS)

CAL TABLES (internal addresses):
  0xBA88   (spark smoothing rate table, 1D indexed by RPM)
  0xBAB2   (spark smoothing step size table, 1D indexed by RPM)
  0xBA12   (DFCO continue spark, high TPS)
  0xBA3C   (DFCO continue spark, low TPS)

ALGORITHM:
  1. SELECT WORST-CASE RETARD:
     - d3 = max(piston_slap_retard, cat_lightoff_retard)
     - This ensures the more retarding value dominates
  2. SUM SPARK:
     - d1 = base_spark + launch_spark - worst_retard = raw spark
     - Store to FFFF98BE and FFFF984C
  3. SMOOTHING (state machine on FFFF9854):
     IF FFFF9854 == 0 (not currently smoothing):
       - If FFFFA938 AND FFFF9854 clear:
         - Set FFFF9880 = d1 (raw spark)
         - Set FFFF9854 = 1 (start smoothing)
         - FFFF987A = d1 - smoothing_rate_table[RPM]  (target floor)
     THEN (smoothing active, FFFF9854 == 1):
       - If FFFFA938 is 0 and spark_floor not reached:
         - step = smoothing_step_table[RPM] * FFFF987A >> 12
         - if step == 0: step = 1
         - FFFF9880 = max(FFF9880 - step, smoothing_rate_table[RPM])
         - If FFFF9880 <= smoothing_rate_table[RPM]: set FFFF9851=1
  4. DFCO SMOOTHING STATES:
     - Multiple states handle DFCO entry/exit:
       * DFCO interrupt ramp (FFFF98CE)
       * DFCO continue hold (FFFF98CF, FFFF987E)
       * DFCO continue spark (FFFF98CC, FFFF98CD)
     - DFCO exit ramp rates from calibration tables
     - Clamp final spark to raw spark value (d1)
  5. ENGINE PROTECTION OVERRIDE:
     - If FFFFABDA set: use SPARK_ADVANCE_KV_ENG_PROTECTION_SPARK_ADVANCE[RPM]
  6. STORE final to FFFF987C
```

---

## RAM Address Reference

| Address | Name | Type | Description |
|---------|------|------|-------------|
| FFFF983A | Base spark | Word | Base spark advance output (sub_39F12) |
| FFFF9834 | MBT delta (no FFS) | Word | MBT - base spark delta |
| FFFF9836 | MBT delta (CLT) | Word | MBT - coolant spark delta |
| FFFF9838 | MBT delta final | Word | MBT delta + torque offset |
| FFFF983C | Cat lightoff | Word | Catalyst lightoff spark retard |
| FFFF983E | CLT spark | Word | Coolant temp spark contribution |
| FFFF9842 | EGR ref | Word | Previous EGR spark for comparison |
| FFFF9844 | ??? offset | Word | Angle offset added to limits |
| FFFF9846 | Idle spark | Word | Idle over/underspeed spark |
| FFFF9848 | Base ref | Word | Base spark reference for MBT delta |
| FFFF984A | Raw base spark | Word | Base spark before octane blend |
| FFFF984C | Pre-smooth raw | Word | Raw spark before smoothing |
| FFFF984E | CT flag | Byte | Closed throttle state (0=OT, 1=CT) |
| FFFF984F | DFCO mode | Byte | DFCO spark mode flag |
| FFFF9851 | Smooth done | Byte | Spark smoothing complete flag |
| FFFF9853 | Retard limit act. | Byte | Retard limit active flag |
| FFFF9854 | Smooth active | Byte | Spark smoothing active flag |
| FFFF9858 | Octane blend | Word | Octane blend interpolant |
| FFFF985E | CLT mult | Word | Cat lightoff coolant multiplier |
| FFFF9860 | TPS mult | Word | Cat lightoff TPS multiplier |
| FFFF9862 | Re-enable ramp | Word | Cat lightoff re-enable ramp factor |
| FFFF9864 | Ref pulse factor | Word | Re-enable per-ref-pulse factor |
| FFFF9866 | Re-enable count | Word | Re-enable ref pulse counter |
| FFFF9868 | Re-enable timer | Word | Re-enable timer start |
| FFFF986A | Re-enable time | Word | Re-enable ramp time |
| FFFF986C | Vac enable latch | Byte | Vacuum enable latch |
| FFFF986D | CL off complete | Byte | Catalyst lightoff complete |
| FFFF986E | Vac disable latch | Byte | Vacuum disable latch |
| FFFF986F | Re-enable latch | Byte | Lightoff re-enable latch |
| FFFF9870 | Runtime ramp | Word | Runtime ramp multiplier |
| FFFF9876 | Crank spark | Word | Cranking spark advance |
| FFFF987A | Smooth floor | Word | Spark smoothing target floor |
| FFFF987C | Smoothed spark | Word | Final smoothed spark output |
| FFFF987E | DFCO hold count | Byte | DFCO hold ref pulse count |
| FFFF9880 | Final spark | Word | **FINAL SPARK ADVANCE OUTPUT** |
| FFFF9882 | DR→PN ramp target | Word | Drive to Park ramp target |
| FFFF9884 | Torque spark offset | Word | Torque control spark offset |
| FFFF9886 | EGR timer | Word | EGR spark timer |
| FFFF9888 | EQ ratio spark | Word | Equivalence ratio spark |
| FFFF988A | FFS E80 offset | Word | FFS E80 spark shift |
| FFFF988C | IAT base | Word | IAT spark base value |
| FFFF988E | Flare multiplier | Word | Idle flare multiplier |
| FFFF9890 | IAT spark | Word | IAT spark contribution |
| FFFF9898 | EGR spark | Word | EGR spark contribution |
| FFFF989A | Octane source | Word | Octane blend source factor |
| FFFF989C | Vac state prev | Byte | Previous vacuum state |
| FFFF989E | Piston slap | Word | Piston slap spark retard |
| FFFF98A0 | PN→DR ramp target | Word | Park to Drive ramp target |
| FFFF98BE | Pre-smooth spark | Word | Raw spark before smoothing |
| FFFF98C0 | DR→PN timer | Word | Drive to Park ramp timer |
| FFFF98C2 | PN→DR timer | Word | Park to Drive ramp timer |
| FFFF98C4 | CLT spark ref | Word | Coolant spark for MBT delta |
| FFFF98C6-8| RDSC timers | Word | RPM derivative spark control timers |
| FFFF98CC | DFCO continue ct | Byte | DFCO continue ref count |
| FFFF98CD | DFCO cont.act. | Byte | DFCO continue active |
| FFFF98CE | DFCO int.ramp | Byte | DFCO interrupt ramp active |
| FFFF98CF | DFCO hold | Byte | DFCO hold active |
| FFFF98D0 | Park state | Byte | Park/Neutral state active |
| FFFF98D1 | RDSC bit | Byte | RDSC enable bit (bit 6) |
| FFFF98D2 | Drive confirmed | Byte | Drive state confirmed |
| FFFF98D3 | Drive active | Byte | Drive state active |
| FFFF98D4 | PN→DR interm | Byte | Park to Drive intermediate |
| FFFF98D5 | Park interm | Byte | Park intermediate |
| FFFF98D6 | Park confirmed | Byte | Park confirmed |
| FFFF98D7 | Drive2 active | Byte | Drive mode 2 active |
| FFFF98D8 | DR→PN interm2 | Byte | Drive to Park intermediate 2 |
| FFFF98D9 | Drive interm | Byte | Drive intermediate |
| FFFF9D30 | Knock ret.accum | Word | Knock retard accumulator |
| FFFF9D32 | Knock event | Byte | Knock event active |
| FFFF9D34 | Launch spark | Word | Launch spark value |
| FFFF9D68 | Knock detected | Word | Knock detected flag |
| FFFF9D76 | Runtime mult | Word | Launch runtime ramp multiplier |
| FFFF9D78 | Soak mult | Word | Launch soak time multiplier |
| FFFF9D7A | RPM mult | Word | Launch RPM multiplier |
| FFFF9D7C | Delta cyl thr. | Word | Launch delta cyl air threshold |
| FFFF9D90 | Launch countdown | Byte | Launch spark hold pulse counter |
| FFFF9D91 | Ramp out done | Byte | Launch ramp out complete |
| FFFF9D92 | Delta cyl air | Word | Delta cylinder airmass |
| FFFF9D99 | Knock enable | Byte | Knock detection enable |
| FFFF9FC8 | FFS blend | Word | **FFS spark blend factor** |
| FFFFAEF8 | Alcohol blend | Word | Alcohol blend factor |
| FFFFB298 | Manifold vacuum | Word | Manifold vacuum, kPa |

---

## Main Spark Calculation Chain — Execution Order

The main spark loop (`loc_3A8C8`) executes these functions in order whenever the engine is running (state == 3):

```
Order  Function            Output RAM      Description
─────  ────────            ──────────      ───────────
  1    sub_3B38C           FFFF984E        CT/OT state detection
  2    sub_39F12           FFFF983A        Base spark (from tables)
  3    sub_3A2A8           FFFF983E        Coolant temp spark
  4    sub_3A330           FFFF9898        EGR spark
  5    sub_3A436           FFFF9888        EQ ratio spark
  6    sub_3A4CE           FFFF9846        Idle spark
  7    sub_3A5CE           FFFF9890        IAT spark
  8    sub_3AF0C           FFFF983C        Cat lightoff spark
  9    sub_3A63E           FFFF988A        FFS E80 spark shift
 10    sub_3A6D0           FFFF989E        Piston slap spark
 11    (loc_3A96C)         FFFF9880        SUM + SMOOTHING → FINAL SPARK
```

Note: sub_3BDC4 (launch/knock) runs separately in `DoLoopA+BC`, writing FFFF9D34 which is read during step 11.

Note: sub_3A754 (MBT) is NOT in the main chain — it's called from torque management (sub_7E0BC).

Note: sub_2FAFC/sub_2FC1E (FFS blend) runs separately in `sub_2F780`, writing FFFF9FC8 which feeds into sub_3A63E and sub_3A754.

---

## Key Calibration Tables Summary

| Table | Type | Axes | Usage |
|-------|------|------|-------|
| SPARK_ADVANCE_KA_MAIN_CT_PARK | 13×? | RPM × CylAir/2 | Base spark, CT park |
| SPARK_ADVANCE_KA_MAIN_CT_DRIVE | 13×? | RPM × CylAir/2 | Base spark, CT drive |
| SPARK_ADVANCE_KA_MAIN_OT_HIGH_OCTANE | 25×? | MAP × Baro | Base spark, OT high octane |
| SPARK_ADVANCE_KA_MAIN_OT_LOW_OCTANE | 25×? | MAP × Baro | Base spark, OT low octane |
| SPARK_ADVANCE_KA_CLT_SPARK | 37×? | Baro × CLT | Coolant temp spark |
| SPARK_ADVANCE_KA_CLT_RPM_MODIFIER | 2D | RPM × CLT | CLT spark RPM modifier |
| SPARK_ADVANCE_KA_EGR_SPARK | 13×? | RPM × CylAir/2 | EGR spark |
| SPARK_ADVANCE_KA_EQ_RATIO_SPARK | 2D | RPM × EQ | EQ ratio spark |
| SPARK_ADVANCE_KA_IAT_SPARK | 2D | Baro × IAT | IAT spark |
| SPARK_ADVANCE_KA_CAT_LIGHTOFF_SPARK_RETARD | 2D | RPM × Baro | Cat lightoff retard |
| SPARK_ADVANCE_KA_FFS_E80_SPARK_SHIFT | 2D | RPM × CylAir/2 | FFS E80 spark shift |
| SPARK_ADVANCE_KA_PISTON_SLAP_SPARK_RETARD | 2D | RPM × CylAir | Piston slap retard |
| SPARK_ADVANCE_KA_MBT_SPARK | 2D | RPM × CylAir/2 | MBT spark target |
| SPARK_ADVANCE_KA_FFS_E80_MBT_SPARK_SHIFT | 2D | RPM × CylAir/2 | FFS E80 MBT shift |
| SPARK_ADVANCE_KA_LAUNCH_SPARK | 2D | CLT × RunTime | Launch spark base |
| SPARK_KNOCK_KA_KNOCK_ENERGY_MAD | 2D | Per-cyl | Knock energy threshold |
| SPARK_KNOCK_KA_KNOCK_ENERGY_MAD_GAIN | 2D | MAP × RPM | Knock energy gain |

---

## Spark Smoothing Logic (Detailed)

The spark smoothing is a simple rate-limited approach with DFCO-aware transitions:

```
State Machine States:
  FFFF9854 = 0: NOT smoothing
  FFFF9854 = 1: Smoothing DOWNWARD (retarding)

Smoothing initiation:
  - On first entry (FFFF9854 == 0):
    Set FFFF9854 = 1
    Set FFFF9880 = raw_spark (d1)
    Set FFFF987A = raw_spark - spark_floor_table[RPM]

Smoothing step:
  - While FFFF9854 == 1 and spark > target:
    step = step_table[RPM] * (raw_spark - target) / 0x1000
    if step == 0: step = 1
    FFFF9880 -= step
    if FFFF9880 <= spark_floor_table[RPM]:
      FFFF9851 = 1 (smoothing complete)
      FFFF9880 = spark_floor_table[RPM]

DFCO spark hold (FFFF98CF):
  - When DFCO ends, spark is held at retard value for N ref pulses
  - Then ramps back using calibration ramp rates
  - Clamped to not exceed raw spark target (d1)
```
