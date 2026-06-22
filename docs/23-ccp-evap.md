# P59 OS 12587603 — CCP / EVAP (Canister Purge / Evaporative Emissions)

> Traced from 68k disassembly — 2026-06-22
> The CCP system manages fuel vapor from the charcoal canister into the intake
> manifold. It uses a PWM solenoid to meter purge flow, with closed-loop O2
> feedback to compensate for the unmetered fuel vapor entering the engine.

---

## 1. Overview

The evaporative emissions system captures fuel tank vapors in a charcoal
canister. Under controlled conditions, the PCM opens a purge solenoid to draw
these vapors into the intake manifold. Because purge vapors are unmetered fuel
(bypassing the MAF and injectors), the PCM must compensate using O2 sensor
feedback to maintain correct AFR.

The P59 implements a sophisticated purge control strategy with:
- Multi-condition enable logic (coolant, speed, airflow, run time)
- Closed-loop O2 feedback adjustment
- BLM (Block Learn Multiplier) purge compensation
- Hot Restart Purge (HRP) mode for heat-soak vapor management
- Open-loop purge option for export vehicles without O2 sensors
- PE (Power Enrichment) and COT (Catalytic Over-Temp) flow multipliers
- Pressure/vacuum threshold hysteresis for enable/disable

**Note:** "CCP" is overloaded in this codebase. It means both "Canister Purge"
(emissions, this doc) and "CAN Calibration Protocol" (ETAS, doc 19).

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_2CC22 | 0x02CC22 | 150800 | Main CCP control — called from DoLoopF+14C |
| sub_2CC1A | 0x02CC1A | — | Purge max flow calculation |
| sub_2D1C4 | 0x02D1C4 | 151370 | Purge duty cycle calculation and HRP control |
| sub_2D6D2 | 0x02D6D2 | — | CCP pressure enable threshold check |
| sub_2D6FA | 0x02D6FA | — | CCP vacuum enable threshold check |
| sub_265AE | 0x0265AE | — | First-order filter utility (used for O2 adjust filtering) |

---

## 3. Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CCP CONTROL FLOW                              │
│                                                                      │
│  DoLoopF ──▶ sub_2CC22 (Gate)                                        │
│                │                                                     │
│                ├─ State check: FFFFAD23 == 3? (engine running)       │
│                ├─ Cylinder count: FFFFB274 >= KE_CYLINDERS?          │
│                ├─ O2 sensor faults: check multiple flags             │
│                ├─ Open loop purge: KE_CCP_OPEN_LOOP_PURGE_ENABLE     │
│                ├─ HRP check: FFFF81B9 (Hot Restart Purge active)     │
│                │                                                     │
│                ▼                                                     │
│              Enable Conditions (all must pass):                       │
│                ├─ Coolant > KE_CCP_COOLANT_TEMPERATURE               │
│                ├─ VSS > KE_CCP_VEHICLE_SPEED_FILTERED                │
│                ├─ MAF > KE_CCP_MASS_AIRFLOW                          │
│                └─ Run time > KE_CCP_ENGINE_RUN_TIME                  │
│                                                                      │
│  sub_2D1C4 (Purge Flow + Duty Cycle)                                 │
│                │                                                     │
│                ├─ HRP mode? → calculate HRP enrichment factor        │
│                ├─ Base flow from KV_CCP_BASE_FLOW tables             │
│                │   (idle: KV_CCP_BASE_FLOW_IDLE_MAF)                 │
│                │   (off-idle: KV_CCP_BASE_FLOW_OFF_IDLE_MAF)         │
│                ├─ Apply COT multiplier (KE_CCP_COT_MULTIPLIER)       │
│                ├─ Apply PE multiplier (KE_CCP_PE_MULTIPLIER)         │
│                ├─ Oxygen adjustment factor applied                   │
│                ├─ BLM adjustment factor applied                       │
│                ├─ Flow limited by KV_CCP_MAX_ALLOWED_PURGE_FLOW      │
│                ▼                                                     │
│              Duty cycle from KV_CANISTER_PURGE_DUTY_CYCLE table      │
│              (indexed by normalized flow)                             │
│              Rate-limited by KE_CCP_DUTY_CYCLE_CHANGE_LIMIT          │
│                                                                      │
│  Output: Purge solenoid PWM → FFFFA62A (duty cycle)                  │
│  Feedback: O2 voltage → oxygen adjust multiplier                     │
│            BLM value → BLM adjust multiplier                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Enable Conditions (0x8EBC-0x8EC2)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08EBC | KE_CCP_COOLANT_TEMPERATURE | word | 0x300 | °C | Coolant temp above which purge enabled |
| 0x08EBE | KE_CCP_VEHICLE_SPEED_FILTERED | word | 0x500 | MPH | VSS above which purge enabled |
| 0x08EC0 | KE_CCP_MASS_AIRFLOW | word | 0x600 | g/s | MAF above which purge enabled |
| 0x08EC2 | KE_CCP_ENGINE_RUN_TIME | long | — | Seconds | Run time above which purge enabled |

### 4.2 Start/Run Delay Timing (0x8EC6-0x8ED2)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08EC6 | KE_COOLANT_TEMPERATURE_STARTRUN | word | 0x700 | °C | Coolant threshold for delay from closed loop |
| 0x08EC8 | KE_COLD_START_CLOSED_LOOP_TIME | word | 0x2580 | Seconds | Delay after closed loop (cold start) |
| 0x08ECA | KE_WARM_START_CLOSED_LOOP_TIME | word | 0x640 | Seconds | Delay after closed loop (warm start) |
| 0x08ECC | KE_CCP_COOLANT_STARTRUN | word | 0x500 | °C | Coolant threshold for purge enable delay |
| 0x08ECE | KE_CCP_COLD_OPEN_LOOP_TIME | word | 0x5DC0 | Seconds | Delay after engine run (cold start, OL) |
| 0x08ED0 | KE_CCP_WARM_OPEN_LOOP_TIME | word | 0x1C20 | Seconds | Delay after engine run (warm start, OL) |
| 0x08ED2 | KE_CCP_OPEN_LOOP_PURGE_ENABLE | byte | 0 | BOOLEAN | Enable purge during open loop fuel |
| 0x08ED3 | KE_CYLINDERS_ENABLED_ALLOW_CCP | byte | 8 | — | Min cylinders enabled to allow purge |

### 4.3 Oxygen Feedback Adjustment (0x8ED4-0x8EFA)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08ED4 | KE_CANISTER_PURGE_OXYGEN_INITIAL | word | 0x19A | Unitless | Initial O2 multiplier at purge start |
| 0x08ED6 | KV_CANISTER_OXYGEN_VOLTAGE_HIGH | word | — | mV | O2 voltage high threshold |
| 0x08EDA | KE_CCP_MIN_OXYGEN_ADJUST | word | 0 | Unitless | Min O2 adjust multiplier |
| 0x08EDC | KE_CCP_OPEN_LOOP_OXYGEN_ADJUST | word | 0x1000 | 0-2 | O2 adjust in open loop (1.0 nominal) |
| 0x08EDE | KE_CCP_SHORT_DELAY_RATE | word | 0x50 | Seconds | Short delay when O2 voltage high |
| 0x08EE0 | KE_CCP_LEARN_RATE_NORMAL | word | 0x40 | Seconds | Normal O2 learn rate (increasing) |
| 0x08EE2 | KE_CCP_LEARN_RATE_MULTIPLIER | word | 0x800 | Unitless | Learn rate multiplier |
| 0x08EE4 | KV_CANISTER_OXYGEN_VOLTAGE_LOW | word | — | mV | O2 voltage low threshold |
| 0x08EE8 | KA_CCP_OXYGEN_ADJUST_SIZE | word | — | Unitless | Step size (normal) |
| 0x08EF0 | KV_CCP_OXYGEN_ADJUST_TIMED_SIZE | word | — | Unitless | Step size (timed) |
| 0x08EF4 | KE_CCP_CHOOSE_OXYGEN_DATA | byte | 0 | Unitless | O2 sensor data selection |
| 0x08EF6 | KE_CCP_MAX_FLOW | word | 0x90 | GPS | Max purge flow value |
| 0x08EF8 | KE_CCP_PRESSURE_HIGH | word | 0x49A | kPa | MAP high threshold (enable) |
| 0x08EFA | KE_CCP_PRESSURE_LOW | word | 0x433 | kPa | MAP low threshold (disable) |

### 4.4 Vacuum Thresholds (0x8EFC-0x8F00)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08EFC | KE_CCP_VACUUM_HIGH | word | 0x19A | kPa | Vacuum high threshold (enable) |
| 0x08EFE | KE_CCP_VACUUM_LOW | word | 0xB3 | kPa | Vacuum low threshold (disable) |
| 0x08F00 | KV_CCP_OXYGEN_VOLTAGE_HIGH_TIME | word | 0xA0 | Seconds | Time O2 must stay high for short delay |

### 4.5 Flow Tables (0x8F22-0x8F86)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08F22 | KV_CCP_MAX_ALLOWED_PURGE_FLOW | table | 0 | GPS | Max purge flow vs manifold vacuum |
| 0x08F44 | KV_CCP_BASE_DESIRED_PURGE_FLOW | table | 0 | GPS | Base desired purge flow table |
| 0x08F86 | KA_CCP_MAX_OXYGEN_ADJUST | table | — | Unitless | Max O2 adjust multiplier |

### 4.6 BLM (Block Learn) Purge Adjustment (0x8FD2-0x8FE8)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08FD2 | KE_CCP_OPEN_LOOP_BLM_ADJUST | word | 0x1000 | 0-2 | BLM adjust in open loop (1.0 nominal) |
| 0x08FD4 | KE_CCP_MAX_BLM_SENSOR_ADJUST | word | 0x1000 | Unitless | Max BLM multiplier |
| 0x08FD6 | KE_CCP_MIN_BLM_SENSOR_ADJUST | word | 0x800 | Unitless | Min BLM multiplier |
| 0x08FD8 | KV_CANISTER_BLM_HIGH_THRESHOLD | word | — | Unitless | BLM above this → decrease multiplier |
| 0x08FDC | KE_CCP_INITIAL_BLM_ADJUST | word | — | Unitless | BLM adjust initial value at powerup |
| 0x08FDE | KV_CANISTER_BLM_LOW_THRESHOLD | word | — | Unitless | BLM below this → increase multiplier |
| 0x08FE2 | KV_CCP_BLM_ADJUST_SIZE | word | — | Unitless | BLM adjust step size |
| 0x08FE6 | KE_CANISTER_PURGE_CHOOSE_BLM | byte | 0 | Unitless | BLM data source for purge |
| 0x08FE8 | KE_BLM_INITIAL_VALUE | word | 0x800 | Scaler_2 | BLM value after closed loop reset |

### 4.7 Flow Modifiers (0x8FEA-0x9034)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08FEA | KE_CCP_PE_MULTIPLIER | word | 0x1000 | 0-1 | PE multiplier (1.0 = no reduction) |
| 0x08FEC | KE_CCP_COT_MULTIPLIER | word | — | 0-1 | COT multiplier (reduces purge when cat hot) |
| 0x08FEE | KE_HRP_HOLD_ACTIVE_TIME | word | — | Seconds | HRP hold time before decay |
| 0x08FF0 | KE_HRP_EXIT_DECAY_TIME | word | — | Seconds | HRP decay time to zero |
| 0x08FF2 | KV_CCP_BASE_FLOW_OFF_IDLE_MAF | table | — | GPS | Base flow off-idle vs MAF |
| 0x09034 | KV_CCP_BASE_FLOW_IDLE_MAF | table | — | GPS | Base flow at idle vs MAF |

### 4.8 Duty Cycle (0x904A-0x9148)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0904A | KV_CANISTER_PURGE_DUTY_CYCLE | table | — | Percent | Duty cycle vs normalized flow |
| 0x09146 | KE_CCP_DUTY_CYCLE_CHANGE_LIMIT | word | — | Percent | Max duty cycle delta per loop |
| 0x09148 | KE_CCP_VEHICLE_SPEED_THRESHOLD | word | — | MPH | Speed for high/low filter switching |

### 4.9 Hot Restart Purge (0x923E-0x9242)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0923E | KE_HRP_ENGINE_OIL_TEMPERATURE | word | — | °C | Oil temp above which HRP enabled |
| 0x09240 | KE_HRP_COOLANT_TEMPERATURE | word | — | °C | Coolant above which HRP enabled |
| 0x09242 | KE_HRP_INDUCTION_AIR_TEMPERATURE | word | — | °C | IAT above which HRP enabled |

### 4.10 Idle Purge (0x91EC-0x91EE)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x091EC | KE_IDLE_PURGE_PWRUP_IAT_THRESH | word | — | °C | IAT above which idle purge delay is skipped |
| 0x091EE | KE_IDLE_PURGE_PWRUP_COOL_THRESH | word | — | °C | Coolant for idle purge powerup delay |

### 4.11 Reduction Integral (0x929A)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0929A | KE_CCP_REDUCTION_INTEGRAL | long | 0x7A12000 | Grams | Purge volume before flow reduction starts |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFA620 | byte | sub_2CC22+BE | Purge active flag (1 = purge enabled and flowing) |
| FFFFA622 | byte | sub_2CC22+2E | Purge conditions met flag |
| FFFFA623 | byte | sub_2D1C4+138 | Idle/off-idle state flag for flow lookup |
| FFFFA624 | word | sub_2D1C4+112 | Calculated desired purge flow |
| FFFFA628 | word | sub_2D1C4+15A | Purge flow output (g/s after modifiers) |
| FFFFA62A | word | sub_2D1C4+106 | Purge solenoid PWM duty cycle |
| FFFFA62E | word | sub_2CC22+28 | Purge condition timer |
| FFFFA630 | word | sub_2CC22+48 | Open loop fuel control flag |
| FFFFA632 | byte | sub_2CC22+58 | Open loop purge enable state |
| FFFFA633 | byte | sub_2CC22+6C | Cylinder/DFCO disable flag |
| FFFFA635 | byte | sub_2CC22+D4 | Purge disable reason flag |
| FFFFA636 | byte | sub_2CC22+D0 | Additional disable condition flag |
| FFFFA63C | word | sub_2D1C4+114 | O2 adjust + BLM adjust combined multiplier |
| FFFFA648 | word | sub_2CC22+1C | Purge timer baseline (system timer snapshot) |
| FFFFA652 | byte | sub_2CC22+EE | Another disable condition |
| FFFFA656 | word | sub_2D1C4+B0 | HRP enrichment factor |
| FFFF81B9 | byte | sub_2D1C4+CA | HRP active flag |
| FFFFAD23 | byte | sub_2CC22+A | Engine operating state (3 = running) |
| FFFFB2EF | byte | sub_2CC22+12 | Unknown — purge-related flag |
| FFFFB274 | word | sub_2CC22+5E | Cylinders enabled count |
| FFFFA93B | byte | sub_2CC22+6A | DFCO/DTC-related flag |
| FFFFA0DC | word | sub_2D1C4+13C | MAF airflow (g/s, internal format) |
| FFFFB298 | word | sub_2D1C4+18E | Engine vacuum / baro reading |
| FFFFA1F6 | byte | sub_2D1C4+11A | PE (Power Enrichment) active flag |
| FFFFACAA | byte | sub_2D1C4+128 | COT (Catalytic Over-Temp) active flag |
| FFFFB544 | word | sub_2CC22+20 | System free-running timer |

---

## 6. Algorithm Detail

### 6.1 Main Control: sub_2CC22

Called from DoLoopF each control cycle. Implements the purge enable/disable
decision:

```
1. Check operating state (FFFFAD23 == 3) — must be engine running
2. Check purge condition timer decay:
   - If FFFFB2EF == 1 (some condition met):
     - Compare elapsed time vs FFFFA62E
     - If enough time passed: set FFFFA622 (conditions met)
3. Open-loop purge check:
   - If KE_CCP_OPEN_LOOP_PURGE_ENABLE:
     - Allow purge during open loop fuel control
   - Store at FFFFA632
4. Cylinder enable check:
   - FFFFB274 >> 11 >= KE_CYLINDERS_ENABLED_ALLOW_CCP?
   - OR FFFFA93B (DFCO flag)
   - Set FFFFA633
5. O2 sensor fault check (8 fault flags checked):
   - bit 1 of FFFF88F0, FFFF8906, FFFF88EA, FFFF8900,
     FFFF88EC, FFFF8902, FFFF8930
   - bit 5 of FFFF9B2E
   - FFFFABDA flag
   - ANY set → disable purge (FFFFA620 = 0)
6. HRP check (FFFF81B9):
   - If HRP active AND no disable conditions:
     - Enable purge (FFFFA620 = 1)
     - Reset purge timer
7. Standard enable conditions evaluation:
   a. FFFFA633 == 0? (no cylinder/DFCO disable)
   b. FFFFA622 == 1? (condition timer expired)
   c. Open loop purge allowed or in closed loop
   d. FFFFA652 == 0? (no additional disable)
   e. FFFFA635 == 0 AND FFFFA636 == 0

8. If all conditions pass:
   - Evaluate enable thresholds:
     a. Coolant ≥ KE_CCP_COOLANT_TEMPERATURE
     b. VSS ≥ KE_CCP_VEHICLE_SPEED_FILTERED
     c. MAF ≥ KE_CCP_MASS_AIRFLOW
     d. Run time ≥ KE_CCP_ENGINE_RUN_TIME
   - All met → enable purge, call sub_2D1C4
   - Any not met → disable purge
```

### 6.2 Purge Flow Calculation: sub_2D1C4

Calculates desired purge flow and solenoid duty cycle:

```
HRP Mode (FFFF81B9 == 1):
1. Calculate HRP enrichment factor:
   - Decay from hold value over KE_HRP_EXIT_DECAY_TIME
   - Factor stored at FFFFA656
2. Factor scaled: if < 0x280 → multiply, else → cap at 0x7D00
3. HRP flow from KV_CANISTER_PURGE_DUTY_CYCLE lookup

Standard Mode:
1. Base flow lookup:
   - If idle (FFFFA623 == 0):
     Flow from KV_CCP_BASE_FLOW_IDLE_MAF[MAF]
   - If off-idle:
     Flow from KV_CCP_BASE_FLOW_OFF_IDLE_MAF[MAF]
2. Apply O2 adjust + BLM adjust multiplier (FFFFA63C)
3. Apply COT multiplier (if active):
   flow ×= KE_CCP_COT_MULTIPLIER
4. Apply PE multiplier (if active):
   flow ×= KE_CCP_PE_MULTIPLIER
5. Clamp flow to KV_CCP_MAX_ALLOWED_PURGE_FLOW
6. Convert flow to duty cycle via KV_CANISTER_PURGE_DUTY_CYCLE table
7. Rate-limit duty cycle change:
   If |new - old| > KE_CCP_DUTY_CYCLE_CHANGE_LIMIT: filter
8. Store duty cycle at FFFFA62A

Pressure/Vacuum conditions (sub_2D6D2, sub_2D6FA):
- MAP > KE_CCP_PRESSURE_HIGH → enable (hysteresis)
- MAP < KE_CCP_PRESSURE_LOW → disable
- Vacuum > KE_CCP_VACUUM_HIGH → enable
- Vacuum < KE_CCP_VACUUM_LOW → disable
```

### 6.3 O2 Feedback Adjustment

When purge is active with O2 feedback enabled:

```
1. Monitor O2 sensor voltage
2. If O2 voltage > KV_CANISTER_OXYGEN_VOLTAGE_HIGH:
   - Purge vapors are rich → decrease oxygen multiplier
   - Decrease rate controlled by KA_CCP_OXYGEN_ADJUST_SIZE
3. If O2 voltage < KV_CANISTER_OXYGEN_VOLTAGE_LOW:
   - Purge vapors are lean → increase oxygen multiplier
   - Increase rate controlled by KE_CCP_LEARN_RATE_NORMAL
4. If O2 voltage stays high for KV_CCP_OXYGEN_VOLTAGE_HIGH_TIME:
   - Use KE_CCP_SHORT_DELAY_RATE (faster correction)
   - Use KV_CCP_OXYGEN_ADJUST_TIMED_SIZE (larger step)
5. Clamp between KE_CCP_MIN_OXYGEN_ADJUST and KA_CCP_MAX_OXYGEN_ADJUST
```

### 6.4 BLM Purge Adjustment

Separate from O2 adjustment, the BLM-based purge compensation:

```
1. Monitor BLM (Block Learn Multiplier) values
2. If BLM > KV_CANISTER_BLM_HIGH_THRESHOLD: decrease BLM adjust
3. If BLM < KV_CANISTER_BLM_LOW_THRESHOLD: increase BLM adjust
4. Step size: KV_CCP_BLM_ADJUST_SIZE
5. Clamp between KE_CCP_MIN_BLM_SENSOR_ADJUST and KE_CCP_MAX_BLM_SENSOR_ADJUST
6. On closed loop reset: reset to KE_BLM_INITIAL_VALUE
```

### 6.5 Startup Delay Logic

```
After engine start:
1. Determine cold vs warm start:
   - Cold: coolant at startup < KE_COOLANT_TEMPERATURE_STARTRUN
   - Warm: coolant at startup ≥ KE_COOLANT_TEMPERATURE_STARTRUN

2. Closed Loop Mode (O2 sensors active):
   - Cold: delay KE_COLD_START_CLOSED_LOOP_TIME after closed loop entry
   - Warm: delay KE_WARM_START_CLOSED_LOOP_TIME after closed loop entry

3. Open Loop Mode (export/no O2):
   - Cold: delay KE_CCP_COLD_OPEN_LOOP_TIME after engine run start
   - Warm: delay KE_CCP_WARM_OPEN_LOOP_TIME after engine run start

4. After delay expires: begin purge enable evaluation
```

### 6.6 Hot Restart Purge (HRP)

Activated after a hot engine restart to manage heat-soak vapors:

```
Enable conditions:
- Engine oil temp > KE_HRP_ENGINE_OIL_TEMPERATURE
- Coolant temp > KE_HRP_COOLANT_TEMPERATURE
- IAT > KE_HRP_INDUCTION_AIR_TEMPERATURE
- All three must be met

Operation:
1. Enable purge flow independent of normal enable conditions
2. Hold at high flow for KE_HRP_HOLD_ACTIVE_TIME
3. Decay flow to zero over KE_HRP_EXIT_DECAY_TIME
4. Clear HRP flag (FFFF81B9) when decay complete
5. Transition to normal CCP control
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoopF | Calls sub_2CC22 each cycle |
| O2 Sensors | Feedback for closed-loop purge adjustment |
| BLM (Fuel Trims) | BLM purge adjustment compensates for vapor fuel |
| PE Mode | PE multiplier reduces purge flow during enrichment |
| COT Mode | COT multiplier reduces purge when catalyst is hot |
| Cylinder Deactivation | Disables purge when cylinders deactivated |
| DFCO | Disables purge during deceleration fuel cut |
| EGR | Shares manifold vacuum source; EGR and CCP interact at idle |
| ETAS Slew | KE_ETAS_SLEW_CCP_MODE allows real-time CCP adjustment |
| Pressure/Vacuum | MAP and vacuum thresholds from sub_2D6D2, sub_2D6FA |

---

## 8. Gaps & Unresolved

1. **O2 adjust + BLM adjust interaction**: The exact arithmetic combining O2
   adjust and BLM adjust into the FFFFA63C multiplier needs detailed tracing.

2. **Purge solenoid output pin**: The physical pin and PWM output register
   that drives the canister purge solenoid has not been identified.

3. **Vapor pressure sensor**: Some vehicles have a fuel tank pressure sensor
   for EVAP leak detection. The DI_EVAP and DG_EVAP diagnostic modules
   reference it but the sensor input path is not traced.

4. **Reduction integral logic**: KE_CCP_REDUCTION_INTEGRAL accumulates purge
   volume and eventually reduces flow — the exact reduction threshold and
   strategy needs tracing.

5. **Speed-dependent filtering**: Two filter coefficient tables are selected
   based on vehicle speed threshold (KE_CCP_VEHICLE_SPEED_THRESHOLD) but the
   actual filter coefficients and their effect are not fully traced.

6. **Open-loop operation**: Corvette M6 stock bin has KE_CCP_OPEN_LOOP_PURGE_ENABLE = 0.
   The open-loop path (for export vehicles) exists but is inactive. Full tracing
   would require a different calibration.

---

## 9. How To Verify

```bash
# Verify CCP calibrations in stock bin
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_CCP_OPEN_LOOP_PURGE_ENABLE @ 0x08ED2: {data[0x08ED2]:02X} (0=disabled)')
print(f'KE_CCP_COOLANT_TEMPERATURE @ 0x08EBC: {int.from_bytes(data[0x08EBC:0x08EBE],\"big\"):04X}')
print(f'KE_CCP_VEHICLE_SPEED_FILTERED @ 0x08EBE: {int.from_bytes(data[0x08EBE:0x08EC0],\"big\"):04X}')
print(f'KE_CCP_MASS_AIRFLOW @ 0x08EC0: {int.from_bytes(data[0x08EC0:0x08EC2],\"big\"):04X}')
"
```

```bash
# Count CCP calibrations vs documented
grep "^CCP," Resources/12587603.csv | wc -l
# Should be ~50+ entries
```

```bash
# Verify sub_2CC22 is called from DoLoopF
grep -n "sub_2CC22" 12587603-2004-Corvette-M6.sanitized.asm | grep "DoLoopF\|CODE XREF"
```

---

## 10. Community Knowledge

- **Evap delete**: Common on race cars and engine swaps. Disabling requires
  setting KE_CCP_OPEN_LOOP_PURGE_ENABLE = 0 and disabling DTCs P0440-P0455.
  Unlike EGR, CCP delete requires capping the purge port on the intake
  manifold to prevent vacuum leaks.

- **No-start from CCP issues**: A stuck-open purge solenoid creates a large
  vacuum leak that can cause hard starting and rough idle. The PCM cannot
  detect this directly — it only sees O2 feedback showing lean condition.

- **Export calibrations**: Vehicles without O2 sensors (some overseas markets)
  use open-loop purge with KE_CCP_OPEN_LOOP_PURGE_ENABLE = 1 and O2 feedback
  disabled. The KE_CCP_OPEN_LOOP_OXYGEN_ADJUST provides a fixed multiplier.

- **Blower/supercharger applications**: Purge must be disabled under boost
  because the canister is referenced to atmospheric pressure. Boost pressure
  at the purge port would pressurize the canister. Custom OSes typically
  disable CCP entirely for forced induction.
