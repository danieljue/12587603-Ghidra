# GM P59 PCM Fuel Calculation Chain
## OS 12587603 (2004 Corvette M6) — Motorola 68000

---

## Overview: DoLoopA Calling Sequence

The fuel calculation chain is invoked from `DoLoopA` (line ~146284), which executes every 12.5ms (80Hz loop). The call order within DoLoopA is:

```
DoLoopA:
  sub_79B10      (Dynamic Airflow — DynaAir)          @ line 291164
  sub_30CA4      (Wall Wetting Time Constant)          @ line 158433
  sub_34694      (Injector Flow Rate / Slope)          @ line 165482
  sub_F1C        (Injector Offset)                      @ line 1508
  sub_31FCA      (Afterstart Enrichment Decay)         @ line 160834
  sub_321E2      (Fuel Cut / DFCO)                     @ line 161111
  sub_31AE2      (Overall Equivalence Ratio)           @ line 160238
  sub_307A6      (Crank Fuel)                          @ line 158432 area
  sub_3284E      (Transient Fuel / Wall Wetting II)
  sub_30DA8      (Wall Wetting Fuel Mass)              @ line 158567
  sub_347DC      (Final Pulse Width Calculation)       @ line 165649
  sub_32A0C      (Injector Output Scheduling)          @ line 162131
  sub_7D082      (Injector Driver)
```

---

## 1. Dynamic Airflow: `sub_79B10` (Dyna-Air)

**File location:** Line 291164  
**Called from:** `DoLoopA+B6`  
**Purpose:** Calculates the dynamic air-per-cylinder prediction (Dyna-Air). This is the foundation of the speed-density air model.

### Algorithm Summary

The function implements a sophisticated air-per-cylinder model with multiple operating modes:

#### Phase 1: Cylinder Air (g·K/kPa)
```
1. Read manifold absolute pressure (MAP) from RAM_FFFFB292
2. If flex fuel sensor fault active:
     Use backup MAP from RAM_FFFFA2FA
   Else:
     Use TPS-derived MAP from RAM_FFFFAB62
   Store to RAM_FFFFA0D8 (used for prediction)

3. Engine speed clamp: [800, 40960] RPM → RAM_FFFFA0CA (raw air term)
4. Lookup VE from AIRFLOW_K_MAIN_VOLUMETRIC_EFFICIENCY (1D table, 40 cells)
   Index = (RPM - 2048) / 8
5. Cylinder_Air = VE * MAP / Charge_Temp(RAM_FFFFA0F6)
6. Subtract EGR mass (RAM_FFFFA0DA) → Sensed_Air_Per_Cylinder (RAM_FFFFA0CC)
```

#### Phase 2: Fault Handling
```
7. If MAP, TPS, BARO, or MAF sensor faults active → fallback to backup air model
   - Uses filtered backup (AIRFLOW_KE_BACKUP_AIR_FLOW_FILTER_COEF)
   - Sets RAM_FFFFA123 (backup mode flag)
```

#### Phase 3: High-Speed Dyna-Air Bypass
```
8. If RPM > AIRFLOW_KE_HI_SPEED_DYNA_AIR_THRESH:
   Use filtered Sensed_Air_Per_Cylinder instead of Dyna-Air prediction
   Hysteresis: AIRFLOW_KE_HI_SPEED_DYNA_AIR_HYSTERESIS
   Sets RAM_FFFFA125 (high-speed flag)
```

#### Phase 4: Steady-State Detection
```
9. Evaluate steady-state conditions:
   - TPS < AIRFLOW_KE_IDLE_SS_TPS_THRESH
   - MPH < AIRFLOW_KE_IDLE_SS_MPH_THRESH  
   - MAP delta integrator check
   - Counter threshold: AIRFLOW_KE_IDLE_SS_COUNTER_THRESH
   Sets RAM_FFFFA0F8 (steady-state flag)
```

#### Phase 5: Dyna-Air Prediction Model
```
10. When in steady state:
    - Calculate Model_Of_Air_Per_Cylinder using state-space model
    - Filter: AIRFLOW_K_MODEL_OF_AIR_FILTER_COEF
    - Store to RAM_FFFFA0D2

11. State-space prediction coefficients from AIRFLOW_K_DYNA_AIR_COEFFICIENT table:
    - 20-byte entries × number of flow zones
    - Predicts: RAM_FFFFA0E4 (Air_Per_Cylinder_1_Ahead)
    - Predicts: RAM_FFFFA0C6 (Air_Per_Cylinder_0_Ahead)
```

#### Phase 6: Maximum Airflow Safety
```
12. Calculate max airflow limit:
    - AIRFLOW_K_MAXFLOW_SAFETY_FACTOR applied
    - Clip RAM_FFFFA0C4, RAM_FFFFA0C6 to max
```

#### Phase 7: Crank-to-Run Blending
```
13. If PCM state = Crank/Run:
    - Blend Dyna-Air with speed-density g/cyl
    - Crank-to-run ratio from AIRFLOW_KE_CRANK_TO_RUN_RATIO
    - Store to RAM_FFFFA0E6 (Crank_Air_Per_Cylinder)
```

#### Phase 8: Spark Air Blend
```
14. Calculate blended air-per-cylinder for spark:
    - SPARK_ADVANCE_KE_AIR_PER_CYLINDER_BLEND_RATIO
    - Blend last 5 cylinders of air mass
    - Store to RAM_FFFFA0C8 (for spark lookup)
```

#### Phase 9: Output
```
15. Convert g/cyl to g/sec:
    - Mass_Flow = Air_Per_Cyl_0 * 0xFC9 / 4 / Engine_Speed
    - → RAM_FFFFA0F4 (Dyna_Air_Mass_Flow)
    
    - Sensed_Mass_Flow = Sensed_Air_Per_Cyl * 0xFC9 / 4 / Engine_Speed  
    - → RAM_FFFFA0E0
    
    - Filtered_Mass_Flow = Filtered_Air * 0xFC9 / Engine_Speed
    - → RAM_FFFFA0DE
```

### Key Output RAM Addresses
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFA0C6 | Air_Per_Cyl_0 | Dyna-Air prediction for current cylinder (g/cyl) |
| 0xFFFFA0E4 | Air_Per_Cyl_1 | Dyna-Air prediction 1 cylinder ahead (g/cyl) |
| 0xFFFFA0C4 | Filtered_Air_Per_Cyl | Filtered air-per-cylinder (g/cyl) |
| 0xFFFFA0C2 | Air_Per_Cyl_2_Ahead | Air 2 cylinders ahead (g/cyl) |
| 0xFFFFA0C8 | Blended_Air_Per_Cyl | Blended air for spark (g/cyl) |
| 0xFFFFA0CC | Sensed_Air_Per_Cyl | Sensed (speed-density) air-per-cylinder (g/cyl) |
| 0xFFFFA0D2 | Model_Of_Air_Per_Cyl | Model-predicted air-per-cylinder (g/cyl) |
| 0xFFFFA0E6 | Crank_Air_Per_Cyl | Crank-mode air-per-cylinder (g/cyl) |
| 0xFFFFA0F4 | Dyna_Air_Mass_Flow | Dynamic air mass flow (g/sec) |
| 0xFFFFA0DC | Air_Per_Cyl_for_Fuel | Air-per-cylinder used for fuel (g/cyl) |
| 0xFFFFA0FC | Speed_Density_g_per_cyl | Speed-density grams-per-cylinder (g/cyl) |
| 0xFFFFA0DE | Filtered_Mass_Flow | Filtered mass air flow (g/sec) |
| 0xFFFFA0E0 | Sensed_Mass_Flow | Sensed mass air flow (g/sec) |
| 0xFFFFA0D0 | MAP_Used | MAP value used (kPa) |
| 0xFFFFA0D8 | TPS_MAP | TPS-derived MAP (kPa) |
| 0xFFFFA0F6 | Charge_Temp | Charge temperature (K) |
| 0xFFFFA0DA | EGR_Mass | EGR mass (g) |
| 0xFFFFA0F8 | Steady_State_Flag | Steady state mode flag |
| 0xFFFFA123 | Backup_Mode_Flag | Sensor-fault backup mode |
| 0xFFFFA125 | Hi_Speed_Mode_Flag | High-speed Dyna-Air bypass |

### Key Calibration Tables
| Name | Description | Units |
|------|-------------|-------|
| AIRFLOW_K_MAIN_VOLUMETRIC_EFFICIENCY | VE table (40 cells) | gm·K/kPa |
| AIRFLOW_KE_BACKUP_AIR_FLOW_FILTER_COEF | Sensor fault filter coef | 0-1 |
| AIRFLOW_KE_HI_SPEED_DYNA_AIR_THRESH | High-speed threshold | RPM |
| AIRFLOW_KE_HI_SPEED_DYNA_AIR_HYSTERESIS | Speed hysteresis | RPM |
| AIRFLOW_K_MAXFLOW_SAFETY_FACTOR | Safety multiplier | 0-2 |
| AIRFLOW_K_MODEL_OF_AIR_FILTER_COEF | Model filter coef | 0-1 |
| AIRFLOW_K_STEADY_STATE_RPM_THRESHOLD | SS RPM threshold | RPM |
| AIRFLOW_K_STEADY_STATE_MAP_THRESHOLD | SS MAP threshold | kPa |
| AIRFLOW_K_STEADY_STATE_LOW_MAP_DELTA | SS low MAP delta | kPa |
| AIRFLOW_K_STEADY_STATE_HIGH_MAP_DELTA | SS high MAP delta | kPa |
| AIRFLOW_K_STEADY_STATE_LOW_TPS_DELTA | SS low TPS delta | % |
| AIRFLOW_K_STEADY_STATE_HIGH_TPS_DELTA | SS high TPS delta | % |
| AIRFLOW_KE_IDLE_SS_TPS_THRESH | Idle SS TPS threshold | % |
| AIRFLOW_KE_IDLE_SS_MPH_THRESH | Idle SS MPH threshold | MPH |
| AIRFLOW_KE_IDLE_SS_INT_THRESH | Idle SS integrator threshold | kPa |
| AIRFLOW_KE_IDLE_SS_COUNTER_THRESH | Idle SS counter threshold | Counter |
| AIRFLOW_KE_IDLE_TRANS_COUNTER_THRESH | Idle transient counter threshold | Counter |
| AIRFLOW_KE_IDLE_TRANS_INT_THRESH | Idle transient integrator threshold | kPa |
| AIRFLOW_K_USE_MAX_AIR_FIRST_TIME_IN_1 | Max air on zone entry | Boolean |
| AIRFLOW_KE_CRANK_TO_RUN_RATIO | Crank-to-run blend ratio | Scaler |
| AIRFLOW_K_DYNA_AIR_COEFFICIENT | Dyna-Air prediction coefficients | Various |
| SPARK_ADVANCE_KE_AIR_PER_CYLINDER_BLEND_RATIO | Spark air blend ratio | Scaler_2_S |
| AIRFLOW_KE_EGR_DUTY_CYCLE_DYNAAIR | EGR DC threshold for EGR mass | % |
| AIRFLOW_KE_EGR_DIAG_FINISHED_TIME | EGR diag finished delay | Seconds |

---

## 2. Injector Flow Rate / Slope: `sub_34694`

**File location:** Line 165482  
**Called from:** `DoLoopA:loc_29CE2` and `DoLoopA:loc_29D6A`  
**Purpose:** Calculates the injector flow rate constant (grams/sec) from the injector slope calibration, modified by fuel pump voltage and fuel flow.

### Algorithm
```
Inputs:
  - Battery/Ignition voltage: RAM_FFFFB4A2
  - Manifold vacuum pressure: RAM_FFFFAEF2
  - Base injector slope: FUEL_PL_KV_INJECTOR_SLOPE

1. Map voltage → pump flow correction:
   - If voltage < 0x480 (1152 raw): correction = 0
   - If 0x480 ≤ voltage < 0x1200 (4608 raw): correction = (voltage*2 - 0x900)
   - If voltage ≥ 0x1200: correction = 0x1B00
   - Lookup FUEL_PL_KV_FLOW_RATE_PUMP_CORRECTION → multiplier d1

2. If FUEL_PL_KE_USE_INJ_SLOPE_MODIFIER enabled AND PCM state = CRANK:
   a. Calculate fuel flow:
      Fuel_Flow = Air_per_Cyl * RPM * 25
      / 0x1000
      * Wall_Mass_Error (RAM_FFFFB274)
      / 0x800
      / 0x78 (120 decimal)
      → RAM_FFFFB0F4 (Fuel_Flow_g_per_sec)

   b. Map fuel flow → slope modifier:
      FUEL_PL_KV_INJ_SLOPE_FUEL_FLOW_MOD
      → RAM_FFFFB0F2 (Injector_Slope_Modifier)

   c. Calculate final flow rate:
      IFR = Base_Slope * Pump_Correction * Slope_Modifier / 0x8000
      → RAM_FFFFB0EC

3. If slope modifier disabled:
   IFR = Base_Slope * Pump_Correction / 0x1000
   → RAM_FFFFB0EC
```

### Output
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFB0EC | Injector_Flow_Rate | Final injector flow rate (g/sec) |
| 0xFFFFB0F2 | Injector_Slope_Modifier | Slope modifier from fuel flow |
| 0xFFFFB0F4 | Fuel_Flow_g_per_sec | Calculated fuel flow |

### Calibration Tables
| Name | Description | Units |
|------|-------------|-------|
| FUEL_PL_KV_INJECTOR_SLOPE | Base injector slope | Grams/Sec |
| FUEL_PL_KV_FLOW_RATE_PUMP_CORRECTION | Pump voltage correction | Mult0to8 |
| FUEL_PL_KE_USE_INJ_SLOPE_MODIFIER | Enable slope modifier | Boolean |
| FUEL_PL_KV_INJ_SLOPE_FUEL_FLOW_MOD | Fuel flow modifier | Unitless |

---

## 3. Injector Offset: `sub_F1C`

**File location:** Line 1508  
**Called from:** `DoLoopA+274`  
**Purpose:** Calculates the injector opening dead time (offset) and maximum achievable pulse width.

### Algorithm
```
Inputs:
  - Battery/Ignition voltage: RAM_FFFFB4A2
  - Manifold vacuum: RAM_FFFFAEF2

1. Map voltage → index:
   - If voltage < 0x480: index = 0
   - If 0x480 ≤ voltage < 0x1200: index = (voltage*2 - 0x900)
   - If voltage ≥ 0x1200: index = 0x1B00

2. Lookup injector offset from FUEL_IO_KA_INJECTOR_OFFSET (3D table)
   Base_Offset = lookup(voltage_index, vacuum)

3. Apply vacuum adjustment:
   Vac_Adj = FUEL_IO_KV_INJECTOR_OFFSET_ADJUSTMENT(vacuum)
   Final_Offset = Base_Offset - Vac_Adj
   (clamp ≥ 0)

4. Calculate maximum pulse width:
   Max_PW = 0x7FF0 - Final_Offset
   (clamp ≥ 0)
```

### Output
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFB26E | Injector_Offset | Injector opening dead time (ms) |
| 0xFFFFB270 | Max_Inj_Pulse_Width | Maximum achievable pulse width (ms) |
| 0xFFFFE0B2 | Injector_Offset (TPU) | Copy for TPU hardware |

### Calibration Tables
| Name | Description | Units |
|------|-------------|-------|
| FUEL_IO_KA_INJECTOR_OFFSET | 3D offset table (voltage × vacuum) | Milliseconds |
| FUEL_IO_KV_INJECTOR_OFFSET_ADJUSTMENT | Vacuum adjustment | Milliseconds |
| FUEL_IO_KE_MINIMUM_INJECTOR_OFF_TIME | Minimum off time | Milliseconds |

---

## 4. Equivalence Ratio Calculation: `sub_31AE2`

**File location:** Line 160238  
**Called from:** `DoLoopA:loc_29DB2`  
**Purpose:** Computes the final overall equivalence ratio (phi) by selecting the maximum from all enrichment sources and mixing in O2 trim.

### Algorithm

#### 4a. Crank Mode (PCM state = 1)
```
1. Check clear-flood mode:
   TPS > FUEL_EQ_KE_CLEAR_FLOOD_THROTTLE_ENTER → zero fuel
   Hysteresis: FUEL_EQ_KE_CLEAR_FLOOD_THROTTLE_EXIT

2. Crank equivalence ratio lookup:
   - Normal crank: up to FUEL_EQ_KE_NORMAL_CRANK_EVENT_LIMIT refs
   - Extended crank: FUEL_EQ_KE_EXTENDED_CRANK_EVENT_LIMIT refs
   - Lookup from FUEL_EQ_KA_CRANK_EQUIVALENCE_RATIO table
   - Coolant modifier from FUEL_EQ_KA_CRANK_EQ_RATIO_BLEND_FACTOR
   - E80 modifier from FUEL_EQ_KV_CRANK_EQ_RATIO_E80_FACTOR

3. Hexane/Octifire prime modifier:
   FUEL_CRANK_KV_OCTIFIRE2_SOAKTIMER_MODIFIER
   Based on soak time

4. RPM multiplier from FUEL_EQ_KA_CRANK_RPM_MULTIPLIER table
   → RAM_FFFFA1EC (Crank_Equivalence_Ratio)
```

#### 4b. Run Mode (PCM state ≠ 1)
```
5. Start with base equivalence ratio from rich/lean select:
   - If in open-loop lean cruise: RAM_FFFFA21E
   - Otherwise: MAX of multiple enrichment sources

6. Enrichment Selection (pick maximum of):
   a. Power Enrichment EQ:      RAM_FFFFA1F8 (PE equivalence ratio)
   b. COT Protection EQ:        RAM_FFFFACAC (Catalytic over-temp enrich)
   c. Component Protection EQ:  RAM_FFFFA202
   d. Hot Enrichment EQ:        RAM_FFFFA1F0 (Hot mode enrich)
   e. Piston Protection EQ:     RAM_FFFFA20A
   f. Drivetrain Abuse EQ:      RAM_FFFFB354
   g. Forced enrichment:        RAM_FFFFA1FE

   If in open-loop idle: apply FUEL_EQ_KE_OPEN_LOOP_LEAN_LIMIT

7. Forsed Induction / Octane modifier:
   - Apply octane scalar if enabled
   - Apply flex fuel / composition modifier

8. Final Equivalence Ratio → RAM_FFFFA1EE

9. Calculate target fuel/air ratio from equivalence ratio:
   Target_FA = Stoich_FA * Equivalence_Ratio
   where Stoich_FA comes from RAM_FFFF9FC4 (fuel composition)
   → RAM_FFFFA1F2 (Target_Fuel_Air_Ratio)
```

### Output
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFA1EE | Final_EQ_Ratio | Final overall equivalence ratio |
| 0xFFFFA1F2 | Target_Fuel_Air_Ratio | Target fuel/air mass ratio |
| 0xFFFFA1EC | Crank_EQ_Ratio | Crank-mode equivalence ratio |
| 0xFFFFA1E8 | Inverse_FA_Ratio | 1/target fuel/air ratio |

### Calibration Tables
| Name | Description | Units |
|------|-------------|-------|
| FUEL_EQ_KA_CRANK_EQUIVALENCE_RATIO | Crank fuel table | Equiv_Ratio_Type |
| FUEL_EQ_KV_CRANK_EQ_RATIO_BLEND_FACTOR | Crank EQ coolant blend | Scaler |
| FUEL_EQ_KV_CRANK_EQ_RATIO_E80_FACTOR | E80 crank modifier | Scaler |
| FUEL_EQ_KE_NORMAL_CRANK_EVENT_LIMIT | Normal crank refs | 1-32 |
| FUEL_EQ_KE_EXTENDED_CRANK_EVENT_LIMIT | Extended crank refs | Count |
| FUEL_EQ_KE_CLEAR_FLOOD_THROTTLE_ENTER | Clear flood enter TPS | % |
| FUEL_EQ_KE_CLEAR_FLOOD_THROTTLE_EXIT | Clear flood exit TPS | % |
| FUEL_CRANK_KV_OCTIFIRE2_SOAKTIMER_MODIFIER | Prime soak modifier | 0-2 |
| FUEL_EQ_KE_OPEN_LOOP_LEAN_LIMIT | Open loop lean limit | Equiv_Ratio_Type |
| FUEL_EQ_KE_FAST_AFTERSTART_ENRICH_ENBLD | Fast afterstart enable | Boolean |
| FUEL_EQ_KA_FAST_AFTERSTART_ENRICHMENT | Fast afterstart table | 0-4 |
| FUEL_EQ_KV_FAST_AFTERSTART_DECAY_INTRVL | Decay interval | Ref Pulses |
| FUEL_EQ_KV_FAST_AFTERSTART_DECAY_STEPS | Decay step size | Equiv_Ratio |

---

## 5. Power Enrichment & Hot Enrichment: `sub_316EA`

**File location:** Line 159716  
**Called from:** `DoLoopE+3E`  
**Purpose:** Determines if Power Enrichment (PE) mode should be active and calculates the PE equivalence ratio. Also contains hot enrichment logic.

### Algorithm

#### 5a. Hot Enrichment
```
Inputs: Coolant temp (RAM_FFFFADB0), MAP (RAM_FFFFB292), TPS (RAM_FFFFAB66), MPH (RAM_FFFFAEBE)

1. If hot enrichment currently active:
   Exit thresholds: FUEL_EQ_KE_HOT_ENRICHMENT_COOLANT_EXIT_T
                    FUEL_EQ_KE_HOT_ENRICHMENT_MAP_EXIT_THRES
                    FUEL_EQ_KE_HOT_ENRICHMENT_THROTTLE_EXIT_
                    FUEL_EQ_KE_HOT_ENRICHMENT_VEH_SPEED_EXIT
   Else:
   Entry thresholds: FUEL_EQ_KE_HOT_ENRICHMENT_COOLANT_ENTRY_
                     FUEL_EQ_KE_HOT_ENRICHMENT_MAP_ENTRY_THRE
                     FUEL_EQ_KE_HOT_ENRICHMENT_THROTTLE_ENTRY
                     FUEL_EQ_KE_HOT_ENRICHMENT_VEH_SPEED_ENTR

2. If all entry conditions met → set RAM_FFFFA1F4 (hot enrich active)
3. Calculate hot enrichment EQ:
   Temp_above_thresh = Coolant - FUEL_EQ_KE_HOT_ENRICHMENT_EQUIVALENCE_OF
   multiplier = Temp_above_thresh * FUEL_EQ_KE_HOT_ENRICHMENT_EQUIVALENCE_MU * 5 / 0x200
   Add 0x400 (stoich base)
   Clamp to FUEL_EQ_KE_MAXIMUM_ENRICHMENT_EQUIVALENC
   → RAM_FFFFA1F0 (Hot_Enrich_EQ_Ratio)

   If not active: RAM_FFFFA1F0 = 0, RAM_FFFFA1F4 = 0
```

#### 5b. Power Enrichment Enable
```
4. PE throttle threshold lookup:
   If coolant > FUEL_EQ_KE_POWER_ENRICHMENT_HOT_TEMP:
     throttle_thresh = FUEL_EQ_KV_POWER_ENRICHMENT_HOT_THRESHOL(RPM_idx)
   Else:
     throttle_thresh = FUEL_EQ_KV_POWER_ENRICHMENT_COLD_THRESHO(RPM_idx)

5. Apply hysteresis when PE already active:
   If PE active: subtract FUEL_EQ_KE_POWER_ENRICHMENT_THROTTLE_HYS
   If COT active: subtract FUEL_EQ_KE_POWER_ENRICHMENT_COT_HYSTERES

   Also apply torque-based enable:
   Pct_Trq_Des > FUEL_EQ_KE_PCT_TRQ_DES_TO_ENABLE_PE
   Hysteresis: FUEL_EQ_KE_HYST_PCT_TRQ_FOR_PE

6. MAP threshold with hysteresis:
   Enable: MAP > FUEL_EQ_KE_POWER_ENRICHMENT_MAP_THRESHOL
   Hysteresis: FUEL_EQ_KE_POWER_ENRICHMENT_MAP_HYSTERES

7. RPM threshold:
   RPM > FUEL_EQ_KV_POWER_ENRICHMENT_RPM_THRESHOL (from table)
   → sets RAM_FFFFA227

8. PE delay logic:
   Can be bypassed if:
   - Coolant outside [FUEL_EQ_KE_PE_DELAY_TEMPERATURE_LOW, FUEL_EQ_KE_PE_DELAY_TEMPERATURE_HIGH]
   - RPM > FUEL_EQ_KE_PE_DELAY_ENGINE_SPEED
   - Throttle rise > FUEL_EQ_KE_PE_DELAY_THROTTLE_RISE AND MPH < FUEL_EQ_KE_PE_DELAY_THROTTLE_RISE_MPH
   - RPM rise > FUEL_EQ_KE_PE_DELAY_ENGINE_SPEED_RISE AND MPH > FUEL_EQ_KE_PE_DELAY_ENGINE_SPEED_RISE_MP

   Sets RAM_FFFFA226 (PE delay bypass)
   Sets RAM_FFFFA1F6 (PE active flag)
```

#### 5c. Power Enrichment Equivalence Ratio
```
9. Base PE EQ from RPM-based table:
   FUEL_EQ_KV_POWER_ENRICHMENT_RPM_EQUIVALE → d3

10. Coolant modifier:
    FUEL_EQ_KV_POWER_ENRICHMENT_COOLANT_EQUI → signed 12.4 fixed
    ASR #4 → add to base

11. IAT modifier (Holden application):
    FUEL_EQ_KV_POWER_ENRICHMENT_IAT_EQUIV → signed 12.4 fixed
    ASR #4 → add to base

12. Final PE EQ → RAM_FFFFA1FA (PE_Target_EQ)

13. PE EQ ramping:
    - Ramp IN: at FUEL_EQ_KE_PE_EQ_RAMP_IN_RATE, step FUEL_EQ_KE_PE_EQ_STEPSIZE
    - Ramp OUT: at FUEL_EQ_KE_PE_EQ_RAMP_OUT_RATE, step FUEL_EQ_KE_PE_EQ_STEPSIZE
    - Ramping tracked in RAM_FFFFA1F8, timers RAM_FFFFA236/RAM_FFFFA238

    When PE inactive: ramp down to 0x400 (stoich)
```

### Output
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFA1F6 | PE_Active_Flag | PE mode active |
| 0xFFFFA1FA | PE_Target_EQ | Target PE equivalence ratio |
| 0xFFFFA1F8 | PE_Current_EQ | Ramped PE equivalence ratio |
| 0xFFFFA1F4 | Hot_Enrich_Active | Hot enrichment active |
| 0xFFFFA1F0 | Hot_Enrich_EQ | Hot enrichment EQ ratio |
| 0xFFFFA226 | PE_Delay_Bypass | PE delay bypass flag |
| 0xFFFFA227 | PE_Enable_Met | All PE conditions met |
| 0xFFFFA228 | PE_Min_Clamp | Minimum PE EQ (0x400 stoich) |
| 0xFFFFA22E | PE_Delay_Timer | PE delay countdown |

### Calibration Tables
| Name | Description | Units |
|------|-------------|-------|
| FUEL_EQ_KV_POWER_ENRICHMENT_HOT_THRESHOL | Hot PE TPS threshold | Percent |
| FUEL_EQ_KV_POWER_ENRICHMENT_COLD_THRESHO | Cold PE TPS threshold | Percent |
| FUEL_EQ_KE_POWER_ENRICHMENT_HOT_TEMP | Hot temp threshold | Degrees_C |
| FUEL_EQ_KE_POWER_ENRICHMENT_THROTTLE_HYS | TPS hysteresis | Percent |
| FUEL_EQ_KE_POWER_ENRICHMENT_COT_HYSTERES | COT hysteresis | Percent |
| FUEL_EQ_KE_POWER_ENRICHMENT_MAP_THRESHOL | MAP threshold | kPa |
| FUEL_EQ_KE_POWER_ENRICHMENT_MAP_HYSTERES | MAP hysteresis | kPa |
| FUEL_EQ_KV_POWER_ENRICHMENT_RPM_THRESHOL | RPM threshold table | RPM |
| FUEL_EQ_KV_POWER_ENRICHMENT_RPM_EQUIVALE | PE EQ vs RPM table | Equiv_Ratio_Type |
| FUEL_EQ_KV_POWER_ENRICHMENT_COOLANT_EQUI | Coolant EQ modifier | Equiv_Ratio_Type |
| FUEL_EQ_KV_POWER_ENRICHMENT_IAT_EQUIV | IAT EQ modifier | Equiv_Ratio_Type |
| FUEL_EQ_KE_PE_EQ_STEPSIZE | PE ramp step size | Equiv_Ratio_Type |
| FUEL_EQ_KE_PE_EQ_RAMP_IN_RATE | PE ramp-in rate | Seconds |
| FUEL_EQ_KE_PE_EQ_RAMP_OUT_RATE | PE ramp-out rate | Seconds |
| FUEL_EQ_KE_PE_DELAY_TEMPERATURE_LOW | Delay bypass temp low | Degrees_C |
| FUEL_EQ_KE_PE_DELAY_TEMPERATURE_HIGH | Delay bypass temp high | Degrees_C |
| FUEL_EQ_KE_PE_DELAY_ENGINE_SPEED | Delay bypass RPM | RPM |
| FUEL_EQ_KE_PE_DELAY_THROTTLE_RISE | Delay bypass TPS delta | Percent |
| FUEL_EQ_KE_PE_DELAY_THROTTLE_RISE_MPH | Delay bypass MPH for TPS | MPH |
| FUEL_EQ_KE_PE_DELAY_ENGINE_SPEED_RISE | Delay bypass RPM rise | RPM |
| FUEL_EQ_KE_PE_DELAY_ENGINE_SPEED_RISE_MP | Delay bypass MPH for RPM | MPH |
| FUEL_EQ_KE_PCT_TRQ_DES_TO_ENABLE_PE | Torque-based PE enable | Percent_0_To_200 |
| FUEL_EQ_KE_HYST_PCT_TRQ_FOR_PE | Torque-based PE hysteresis | Percent_0_To_200 |
| FUEL_EQ_KE_TRQ_MGT_PWR_ENRICH_THROT_HYS | ETC torque mgt TPS hys | Percent |
| FUEL_EQ_KE_MAXIMUM_ENRICHMENT_EQUIVALENC | Maximum EQ clamp | Equiv_Ratio_Type |
| FUEL_EQ_KE_HOT_ENRICHMENT_COOLANT_ENTRY_ | Hot enrich cool entry | Degrees_C |
| FUEL_EQ_KE_HOT_ENRICHMENT_COOLANT_EXIT_T | Hot enrich cool exit | Degrees_C |
| FUEL_EQ_KE_HOT_ENRICHMENT_THROTTLE_ENTRY | Hot enrich TPS entry | Percent |
| FUEL_EQ_KE_HOT_ENRICHMENT_THROTTLE_EXIT_ | Hot enrich TPS exit | Percent |
| FUEL_EQ_KE_HOT_ENRICHMENT_MAP_ENTRY_THRE | Hot enrich MAP entry | kPa |
| FUEL_EQ_KE_HOT_ENRICHMENT_MAP_EXIT_THRES | Hot enrich MAP exit | kPa |
| FUEL_EQ_KE_HOT_ENRICHMENT_VEH_SPEED_ENTR | Hot enrich MPH entry | MPH |
| FUEL_EQ_KE_HOT_ENRICHMENT_VEH_SPEED_EXIT | Hot enrich MPH exit | MPH |
| FUEL_EQ_KE_HOT_ENRICHMENT_EQUIVALENCE_OF | Hot enrich EQ offset temp | Degrees_C |
| FUEL_EQ_KE_HOT_ENRICHMENT_EQUIVALENCE_MU | Hot enrich EQ multiplier | Mult_0_to_2 |

---

## 6. Closed Loop Fuel Control

### 6a. Closed Loop Enable: `sub_3580C`

**File location:** Line 167620  
**Called from:** `DoLoopC+B2`  
**Purpose:** Determines whether the PCM should enter closed loop fuel control.

#### Algorithm
```
1. Call sub_3593C → checks O2 sensor readiness and warmup timers

2. Force open loop if fault active:
   - O2 sensor DTCs (RAM_FFFF88EA through RAM_FFFF8A2A bits)
   - Misfire DTC + FUEL_ST_KE_OPEN_LOOP_FOR_MISFIRE
   → sets RAM_FFFFB2FC (Force_Open_Loop)

3. Evaluate closed loop entry:
   d4 = 0 (open loop default)
   
   IF any of these true → stay open loop (d4 stays 0):
   - RPM ref pulse not received (RAM_FFFFA7DC bit 1 + RAM_FFFFA7E2 bit 5)
   - Power steering active (RAM_FFFFABDA)
   - Engine shutdown (RAM_FFFFA59F)
   - PE active (RAM_FFFFB2D0) — wait, this might be another flag
   - DFCO active (RAM_FFFFB352)
   - Forced open loop (RAM_FFFFB2FC)
   
   IF O2 ready (RAM_FFFFB2F8) AND NOT flex fuel unlearned (RAM_FFFF81B9):
     d4 = 2 (closed loop with trim)
   
   Additional coolant temp check:
   IF coolant > FUEL_ST_KV_CLOSED_LOOP_COOLANT_TEMPERATU:
     d4 = 1 (closed loop, no trim initially)
   IF FUEL_ST_KE_USE_AIRFUEL_CLOSED_LOOP_STATE:
     d4 = 2 (closed loop with trim)
     If bank 2 O2 lean (RAM_FFFF9F5A): set bank 2 to mode 3
     If bank 1 O2 lean (RAM_FFFF9F5B): set bank 1 to mode 3

4. Store closed loop state:
   RAM_FFFFB2EF (Closed_Loop_State):
     0 = Open Loop
     1 = Closed Loop (no trim yet)  
     2 = Closed Loop (with fuel trim)
     3 = Closed Loop (lean — O2 exhausted additional fuel)
```

### 6b. O2 Sensor Readiness: `sub_3593C`

**File location:** Line 167760  
**Called from:** `sub_3580C+2`  
**Purpose:** Determines O2 sensor warmup and readiness.

#### Algorithm
```
1. Check cold/warm/hot startup timers:
   If startup coolant < FUEL_ST_KE_COLD_CLOSED_LOOP_TEMPERATURE:
     Timer = FUEL_ST_KE_COLD_WAIT_TIME
   Elif startup coolant < FUEL_ST_KE_HOT_CLOSED_LOOP_TEMPERATURE:
     Timer = FUEL_ST_KE_WARM_WAIT_TIME
   Else:
     Timer = FUEL_ST_KE_HOT_WAIT_TIME

   If engine run time (RAM_FFFFAD1E) < Timer → exit (not ready)

2. Check O2 sensor voltage transitions:
   Bank 1:
   - O2 voltage (RAM_FFFF9F00) must cross BOTH:
     Below: FUEL_ST_KE_OXYGEN_LOWER_READY_VOLTAGE
     Above: FUEL_ST_KE_OXYGEN_UPPER_READY_VOLTAGE
   - If sensor already "ready" (RAM_FFFFB2F0), check timeout:
     Not-ready timer (RAM_FFFFB2F4) accumulates
     If > FUEL_ST_KE_OXYGEN_NOT_READY_TIME → unready
   - If not ready, counter RAM_FFFFB2FA increments
     If ≥ FUEL_ST_KE_O2_READY_COUNTER_THRESHOLD → ready
     Sets RAM_FFFFB2F0

   Bank 2: same logic with RAM_FFFF9F06, RAM_FFFFB2F1, RAM_FFFFB2FB, RAM_FFFFB2F6

3. Both banks ready → RAM_FFFFB2F8 (O2_Ready) = 1
```

### 6c. Closed Loop Integrator State: `sub_35A7A`

**File location:** Line 167912  
**Called from:** `DoLoopF+29C`  
**Purpose:** Sets the closed loop fuel trim integrator mode.

#### Algorithm
```
1. If forced open loop (RAM_FFFFB2FC) → set integrator state = 4 (disabled)

2. Check closed loop entry conditions:
   Must be in run mode (RAM_FFFFAD22)
   O2 sensors ready (RAM_FFFFB2F8)  
   Coolant temp check via FUEL_ST_KV_CLOSED_LOOP_COOLANT_TEMPERATU
   NOT in PE (RAM_FFFFA1F6)
   NOT in hot enrichment (RAM_FFFFA1F4)
   NOT in COT (RAM_FFFFACAA)
   NOT in DFCO (RAM_FFFFA93B)
   NOT in decel enleanment (RAM_FFFFABDC)
   NOT in misfire
   NOT in injector disable
   NOT in factory test
   NOT in CPP mode (RAM_FFFFB26C)

   If any condition fails → integrator state = 1 (reset)
   
   If all conditions met AND closed_loop_enable (RAM_FFFFB2EF) == 1:
     Integrator state = 2 (active)
     If bank 1 lean (RAM_FFFF9F5A) → bank 1 = 3
     If bank 2 lean (RAM_FFFF9F5B) → bank 2 = 3

3. Output:
   RAM_FFFFB2F2 = Bank 1 integrator state
   RAM_FFFFB2F3 = Bank 2 integrator state
```

### 6d. O2 Integrator Reset Functions

The actual O2 sensor integration loop is dispatched through `sub_35C4E` (line 168094), which jumps to mode-specific handlers. These reset the idle air/fuel trim variables:

| Function | Called From | Purpose |
|----------|-------------|---------|
| sub_393DC | loc_35C8C | Full reset of all idle trim adaptives |
| sub_3942C | loc_35C84, loc_35CAA | Partial reset (no learned values) |
| sub_3944C | loc_35C9C | Partial reset |
| sub_3946C | loc_35C6A | Full reset incl transmission-specific |
| sub_39530 | loc_35C94 | RPM snapshot only |

### Key RAM Addresses (Closed Loop)
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFB2EF | Closed_Loop_State | 0=OL, 1=CL no trim, 2=CL with trim, 3=CL lean |
| 0xFFFFB2F2 | Bank1_Integrator_State | 0=inactive, 1=reset, 2=active, 3=lean-fault, 4=disabled |
| 0xFFFFB2F3 | Bank2_Integrator_State | Same as above |
| 0xFFFFB2F8 | O2_Sensors_Ready | Both O2 sensors ready flag |
| 0xFFFFB2FC | Force_Open_Loop | Forced open loop from DTC |
| 0xFFFFB2F0 | Bank1_O2_Ready | Bank 1 O2 sensor ready |
| 0xFFFFB2F1 | Bank2_O2_Ready | Bank 2 O2 sensor ready |
| 0xFFFF9F00 | O2_Voltage_Bank1 | Bank 1 O2 sensor mV |
| 0xFFFF9F06 | O2_Voltage_Bank2 | Bank 2 O2 sensor mV |

### Calibration Tables (Closed Loop)
| Name | Description | Units |
|------|-------------|-------|
| FUEL_ST_KE_COLD_CLOSED_LOOP_TEMPERATURE | Cold CL temp threshold | Degrees_C |
| FUEL_ST_KE_HOT_CLOSED_LOOP_TEMPERATURE | Hot CL temp threshold | Degrees_C |
| FUEL_ST_KE_COLD_WAIT_TIME | Cold CL wait time | Seconds |
| FUEL_ST_KE_WARM_WAIT_TIME | Warm CL wait time | Seconds |
| FUEL_ST_KE_HOT_WAIT_TIME | Hot CL wait time | Seconds |
| FUEL_ST_KV_CLOSED_LOOP_COOLANT_TEMPERATU | CL enable coolant min | Degrees_C |
| FUEL_ST_KE_OXYGEN_LOWER_READY_VOLTAGE | O2 low voltage ready | Millivolts |
| FUEL_ST_KE_OXYGEN_UPPER_READY_VOLTAGE | O2 high voltage ready | Millivolts |
| FUEL_ST_KE_O2_READY_COUNTER_THRESHOLD | O2 ready count threshold | Counter |
| FUEL_ST_KE_OXYGEN_NOT_READY_TIME | O2 not-ready timeout | Seconds |
| FUEL_ST_KE_USE_AIRFUEL_CLOSED_LOOP_STATE | Force AF-based CL state | Boolean |
| FUEL_ST_KE_OPEN_LOOP_FOR_MISFIRE | Force OL on misfire | Boolean |
| CCP_KE_COLD_START_CLOSED_LOOP_TIME | Cold start CL delay | Seconds |
| CCP_KE_WARM_START_CLOSED_LOOP_TIME | Warm start CL delay | Seconds |

---

## 7. Wall Wetting / Transient Fuel: `sub_30DA8` & `sub_30CA4`

### 7a. Wall Wetting Time Constant: `sub_30CA4`

**File location:** Line 158433  
**Called from:** `DoLoopA+280`  
**Purpose:** Calculates the wall wetting time constant (tau) and wall mass fraction.

```
1. Lookup boiling time constant:
   - SurfaceTableLookup(ECT, ECT_at_startup) → boiling constant
   
2. Modify by air flow:
   FUEL_DY_KV_BOILING_TIME_MODIFIER(airflow_index) → modifier
   
3. Apply wall mass fraction:
   - From FUEL_DY_KE_WALL_MASS_FACTOR
   - Clamp to 0x800

4. Time constant = Reference_Period / modifier
   → RAM_FFFFA148 (Wall_Wetting_Tau)
```

### 7b. Wall Wetting Fuel Mass: `sub_30DA8`

**File location:** Line 158567  
**Called from:** `DoLoopA+350`  
**Purpose:** Calculates the final fuel mass including wall wetting compensation.

```
1. Calculate target fuel mass:
   If DFCO active (RAM_FFFFA93B): Fuel_Mass = 0
   Else: Fuel_Mass = Crank_Air_Per_Cylinder(RAM_FFFFA0E6) * FA_Ratio(RAM_FFFFA1F2) / 0x1000
   → RAM_FFFFA126 (Desired_Fuel_Mass)

2. Wall Wetting model:
   - Delay: FUEL_DY_KV_INITIAL_WW_DELAY_REFS reference pulses  
   - Counter: RAM_FFFFA14E tracks ref pulses per cylinder
   - Tau value from RAM_FFFFA148
   - Calculate puddle mass and vapor mass
   - Calculate wall mass error → RAM_FFFFA186

3. Apply injector flow rate to convert fuel mass to pulse width:
   IFR from RAM_FFFFB0EC

4. Final fuel mass per cylinder bank:
   Stored in RAM_FFFFA13E array (one entry per cylinder)
```

### Key RAM Addresses (Wall Wetting)
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFA126 | Desired_Fuel_Mass | Target fuel mass (g) |
| 0xFFFFA148 | Wall_Wetting_Tau | Wall wetting time constant |
| 0xFFFFA14C | Wall_Mass_Fraction | Wall mass fraction |
| 0xFFFFA14E | WW_Ref_Counter | Ref pulse counter per cylinder |
| 0xFFFFA17C | WW_Active | Wall wetting active flag |
| 0xFFFFA186 | Wall_Mass_Error | Wall mass error (g) |
| 0xFFFFA13E | Fuel_Mass_Per_Cyl | Per-cylinder fuel mass array |

### Calibration Tables (Wall Wetting)
| Name | Description | Units |
|------|-------------|-------|
| FUEL_DY_KV_INITIAL_WW_DELAY_REFS | Initial WW delay | SHORTCARD |
| FUEL_DY_KE_WALL_MASS_FACTOR | Wall mass stability factor | 0-2 |
| FUEL_DY_KV_BOILING_TIME_MODIFIER | Boiling time modifier | 0-1 |
| FUEL_DY_KE_FUEL_IGNORE_WALL_WETTING_RPM | WW disable RPM | RPM |
| FUEL_DY_KE_FUEL_IGNORE_WALL_WETTING_TPS | WW disable TPS | Percent |
| FUEL_DY_KE_MIN_PULSE_WIDTH | Minimum pulse width | (raw) |
| FUEL_DY_KE_DFCO_STOMP_COMP_TPS_MIN | DFCO stomp comp TPS | Percent |
| FUEL_DY_KE_MAKEUP_FUEL_ENABLED | Makeup fuel enable | Boolean |
| FUEL_DY_KE_STARTUP_MAKEUP_DELAY | Startup makeup delay | Ref pulses |

---

## 8. Final Pulse Width Calculation: `sub_34550` & `sub_347DC`

### 8a. Individual Cylinder Pulse Width: `sub_34550`

**File location:** Line 165295  
**Called from:** `sub_345E6`  
**Purpose:** Converts per-cylinder fuel mass to injector pulse width.

```
Inputs:
  d0 = fuel mass per cylinder
  d1 = cylinder number (bank select)

1. Minimum pulse width lookup:
   FUEL_PL_KV_MINIMUM_PULSE_WIDTH(RPM) → min_pw
   
2. Short pulse compensation:
   If pulse < FUEL_PL_KE_SHORT_PULSE_LIMIT:
     Add FUEL_PL_KV_SHORT_PULSE_ADJUSTMENT(pulse_index)
   
3. If pulse < minimum:
   Use FUEL_PL_KV_DEFAULT_PULSE_WIDTH(RPM) instead
   
4. Clamp to Max_Inj_Pulse_Width (RAM_FFFFB270)

5. Add injector offset (RAM_FFFFB26E):
   Final_PW = Base_PW + Injector_Offset
   
6. Store per-cylinder PW in array:
   RAM_FFFFB0E4[w*2 + cylinder] or RAM_FFFFB0E8[w*2 + cylinder]
```

### 8b. Pulse Width Assembly: `sub_347DC`

**File location:** Line 165649  
**Called from:** `DoLoopA+356`  
**Purpose:** Converts fuel mass to pulse width for both banks of injectors.

```
1. For cylinder 0 and 1 (bank 0 and bank 1):
   - If PCM state = CRANK (4):
     Clear PW registers (RAM_FFFFB0E4, RAM_FFFFB0E8)
   
   - Get fuel mass from RAM_FFFFA13E or RAM_FFFFA126
   - Convert to pulse width:
     PW = Fuel_Mass * 0xFC9 / 2 / IFR(RAM_FFFFB0EC)
   
   - Call sub_34550(PW, cylinder_num) → final trimmed PW
   - Store in output array
```

### Key RAM Addresses (Pulse Width)
| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFB0E4 | Inj_PW_Bank1 | Bank 1 final pulse width (ms) |
| 0xFFFFB0E8 | Inj_PW_Bank2 | Bank 2 final pulse width (ms) |
| 0xFFFFB0EC | Injector_Flow_Rate | Current injector flow rate (g/sec) |
| 0xFFFFB26E | Injector_Offset | Injector dead time (ms) |
| 0xFFFFB270 | Max_Pulse_Width | Maximum pulse width (ms) |
| 0xFFFFB0F0 | Fuel_Mass_Base | Base fuel mass before trim |

### Calibration Tables (Pulse Width)
| Name | Description | Units |
|------|-------------|-------|
| FUEL_PL_KV_MINIMUM_PULSE_WIDTH | Minimum PW vs RPM | Milliseconds |
| FUEL_PL_KV_DEFAULT_PULSE_WIDTH | Default PW vs RPM | Milliseconds |
| FUEL_PL_KE_SHORT_PULSE_LIMIT | Short pulse threshold | Milliseconds |
| FUEL_PL_KV_SHORT_PULSE_ADJUSTMENT | Short pulse compensation | (table) |
| FUEL_IO_KV_INJECTOR_TRIM_FACTOR | Final PW scaling (demo) | Scaler_0_to_2 |
| FUEL_IO_KE_MINIMUM_TRIM_PULSE_WIDTH | Minimum trim PW | (raw) |

---

## 9. Injector Output Scheduling: `sub_32A0C`

**File location:** Line 162131  
**Called from:** `DoLoopA+35C`  
**Purpose:** Schedules the injector output events onto the TPU (Time Processing Unit) channels.

```
1. If injector output enabled (RAM_FFFFB272):
   - Get current cylinder (RAM_FFFFAC47)
   - Check for injector disable conditions:
     * Cylinder 8 active?
     * Injector cut flags (RAM_FFFF803D)
     * Misfire DTC
     * Factory test mode
   - Determine injection timing from lookup table at $E690/$E742

2. Apply injector trim factor:
   FUEL_IO_KV_INJECTOR_TRIM_FACTOR[cylinder] × PW / 0x800

3. For each cylinder:
   - Load PW into RAM_FFFFE000[cylinder] array
   - Schedule TPU output event

4. Makeup fuel delivery:
   If FUEL_DY_KE_MAKEUP_FUEL_ENABLED:
   - Calculate makeup fuel from vapor/puddle mass
   - Add to scheduled PW
   - Clamp to RAM_FFFFB270

5. Injector timing calculation (loc_32C02):
   - Calculate start-of-injection angle
   - Convert to TPU timing ticks
   - Store to RAM_FFFFE1E6 area for TPU
```

---

## 10. Complete Fuel Mass → Pulse Width Chain (Summary)

```
DYNAIR (sub_79B10)
  MAP → VE lookup → Cylinder_Air (g/cyl)
  Dyna-Air prediction model
  → RAM_FFFFA0DC: Air_Per_Cyl_for_Fuel

WALL WETTING (sub_30CA4 + sub_30DA8)
  Air_Per_Cyl_for_Fuel × Target_FA_Ratio ÷ 0x1000
  + Wall wetting compensation
  → RAM_FFFFA126: Desired_Fuel_Mass (g)

PULSE WIDTH (sub_34550 + sub_347DC)
  Fuel_Mass × 0xFC9 ÷ 2 ÷ IFR
  + Short pulse compensation
  + Injector offset
  → RAM_FFFFB0E4/B0E8: Injector_Pulse_Width (ms)

OUTPUT (sub_32A0C + sub_7D082)
  PW × Injector_Trim_Factor ÷ 0x800
  Schedule TPU event
  → Hardware injector driver
```

### Key Unit Conversions:
- g/cyl air → g fuel: multiply by target FA ratio (scaled ÷ 0x1000)
- g fuel → pulse width ms: multiply by 0xFC9/2 ÷ IFR (where IFR is g/sec)
- The 0xFC9 constant is (120 × 1000) / (Ncyl × cycles_per_rev) for a V8

---

## 11. Key Global RAM Map

| Address | Name | Description |
|---------|------|-------------|
| 0xFFFFA0C6 | Dyna_Air_0_Ahead | Current cylinder air prediction |
| 0xFFFFA0DC | Air_for_Fuel | Air mass used for fuel calc |
| 0xFFFFA126 | Desired_Fuel_Mass | Target fuel mass per cylinder |
| 0xFFFFA1EE | Final_EQ_Ratio | Overall equivalence ratio |
| 0xFFFFA1F2 | Target_FA_Ratio | Target fuel/air ratio |
| 0xFFFFA1F6 | PE_Active | Power enrichment active |
| 0xFFFFA1F8 | PE_Current_EQ | Ramped PE equivalence ratio |
| 0xFFFFB0E4 | Bank1_PW | Bank 1 injector pulse width |
| 0xFFFFB0E8 | Bank2_PW | Bank 2 injector pulse width |
| 0xFFFFB0EC | IFR | Injector flow rate (g/sec) |
| 0xFFFFB26E | Inj_Offset | Injector dead time (ms) |
| 0xFFFFB270 | Max_PW | Maximum pulse width (ms) |
| 0xFFFFB2EF | CL_State | Closed loop state |
| 0xFFFFB2F2 | Bank1_CL_Integ | Bank 1 integrator state |
| 0xFFFFB2F3 | Bank2_CL_Integ | Bank 2 integrator state |
| 0xFFFFB2F8 | O2_Ready | O2 sensors ready |
| 0xFFFFADB0 | ECT | Engine coolant temperature |
| 0xFFFFA562 | RPM | Engine speed |
| 0xFFFFB292 | MAP | Manifold absolute pressure |
| 0xFFFFAB66 | TPS | Throttle position |
| 0xFFFFB4A2 | Batt_Voltage | Battery/ignition voltage |
| 0xFFFFAEF2 | Vacuum | Manifold vacuum (Baro - MAP) |
| 0xFFFFB544 | Clock_Ticks | System time counter |
| 0xFFFFAD23 | PCM_State | PCM operating state (1=crank,3=run) |
| 0xFFFFAC47 | Cylinder_ID | Current firing cylinder (0-7) |

---

*Document traced from 12587603-2004-Corvette-M6.sanitized.asm (936,975 lines)*  
*P59 PCM / Motorola 68000 / OS 12587603*
