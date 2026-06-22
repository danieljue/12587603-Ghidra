# P59 OS 12587603 — EGR (Exhaust Gas Recirculation)

> Traced from 68k disassembly — 2026-06-22
> EGR recirculates exhaust gas into the intake to reduce NOx emissions and
> combustion temperatures. The P59 implements a full closed-loop position
> control system with ADC feedback, PID control, and vacuum compensation.

---

## 1. Overview

The EGR system meters exhaust gas into the intake manifold via a vacuum-actuated
pintle valve. The PCM reads pintle position from an ADC channel (potentiometer)
and drives a PWM solenoid to control vacuum to the EGR valve diaphragm. The
control loop is PID-based with vacuum/baro compensation for consistent response
across engine load conditions.

**On the 2004 Corvette M6:** `KE_EGR_ENABLED = 0` (disabled). The code and
calibration infrastructure exists but EGR is not active. This is typical for
the Corvette — EGR was used on trucks/SUVs for NOx control. For Boost OS, the
EGR solenoid output (C2 Pin 3) and pintle ADC input (C1 Pin 55) are repurposed
for boost control and wideband O2 respectively.

The EGR system interfaces with the Dyna-Air calculation via
`AIRFLOW_KA_EGR_AIR_FLOW`, `KE_EGR_AIR_FLOW_FILT_COEF`, and
`KE_EGR_DUTY_CYCLE_DYNAAIR` — when EGR is active, the calculated EGR mass flow
is subtracted from the cylinder air estimate.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_2D9E4 | 0x02D9E4 | 152375 | Main EGR control — called from DoLoopB+1F4 |
| sub_2DA2A | 0x02DA2A | 152413 | Read EGR pintle position from ADC, filter, convert to percent |
| sub_2DAA6 | 0x02DAA6 | 152480 | Initialize EGR closed position learning |
| sub_2DACE | 0x02DACE | 152499 | EGR offset learning and relearn management — called from DoLoopC+4C |
| sub_2DED8 | 0x02DED8 | 152932 | EGR desired position calculation with multipliers |
| sub_2E27C | 0x02E27C | 153408 | EGR duty cycle PID controller — generates PWM output |
| sub_2E010 | 0x02E010 | — | EGR vehicle speed disable check |
| sub_62B70 | 0x062B70 | 251796 | EGR enable/disable conditions — called from sub_2D9E4 |
| sub_7AA26 | 0x07AA26 | — | Dyna-Air EGR mass flow calculation |
| sub_79AB0 | 0x079AB0 | — | Dyna-Air: EGR diagnostic finish timer check |

---

## 3. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EGR CONTROL LOOP                             │
│                                                                     │
│  ADC Channel         sub_2DA2A          sub_2DED8                    │
│  (unk_FFFFF2C0)  ──▶ Raw → Percent  ──▶ Desired Position            │
│                      filtering          (multipliers: coolant,       │
│                                         EQ ratio, TPS, TCC, baro)   │
│                                                                     │
│  sub_2D9E4 (Gate)                                                    │
│  checks operating state (2/3/4)                                     │
│  calls sub_62B70 for enable conditions                              │
│                                                                     │
│  sub_2E27C (PID)                                                     │
│  ┌──────────────────────────────────────────┐                       │
│  │ Position Error = Desired - Actual         │                       │
│  │ Integrator (vacuum-compensated)           │                       │
│  │ Proportional (vacuum-compensated)         │                       │
│  │ Initial Duty Cycle (feed-forward)         │                       │
│  │ → Final Duty Cycle (0-0x1400 = 0-100%)   │                       │
│  └──────────────────────────────────────────┘                       │
│                                                                     │
│  Output: PWM solenoid → EGR valve diaphragm → pintle movement       │
│  Feedback: pintle position potentiometer → ADC → sub_2DA2A          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Core EGR Module (0x9458-0x98FE area)

| Address | CSV Label | Type | Range | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------|-------------|
| 0x09458 | KE_EGR_ENABLED | byte | 0-1 | 0 | BOOLEAN | Master EGR enable (0=disabled on Corvette) |
| 0x0945A | KE_EGR_FULL_SCALE_GAIN | word | — | 0x3B6 | % / Count | ADC → percent conversion gain |
| 0x0945C | KE_EGR_OFFSET_FILTER_COEFF | byte | — | 6 | Seconds | Filter coef for closed position offset learning |
| 0x0945E | KE_EGR_POSITION_CLOSED_MIN | word | — | 0x800 | A/D Counts | Min valid closed position |
| 0x09460 | KE_EGR_POSITION_CLOSED_MAX | word | — | 0x3700 | A/D Counts | Max valid closed position |
| 0x09462 | KE_EGR_POSITION_FILTER_COEF | word | — | 0x3025 | Seconds | Lag filter for pintle position |
| 0x09464 | KE_DESIRED_EGR_POSITION_MINIMUM | word | — | 0x100 | Percent | Min desired position before setting to 0 |
| 0x09466 | KE_EGR_OFF_VACUUM_HYST_THRES | word | — | 0x19A | kPa | Hysteresis for enabling from off state |
| 0x09468 | KE_EGR_OFF_VACUUM_THRESHOLD | word | — | 0x100 | kPa | Disable EGR below this vacuum |
| 0x0946A | KE_EGR_FULL_VACUUM_THRESHOLD | word | — | 0x200 | kPa | Enable full EGR above this vacuum |
| 0x0946C | KE_EGR_TCC_RPM_HIGH_HYST | word | — | 0 | RPM | Disable TCC multiplier above this RPM |
| 0x0946E | KE_EGR_TCC_RPM_LOW_HYST | word | — | 0 | RPM | Enable TCC multiplier below this RPM |
| 0x09470 | KE_EGR_LEARN_ENABLE_TIME | word | — | 0xA0 | Seconds | Time before offset learning starts |
| 0x09472 | KE_EGR_INIT_LEARN_CMPT_TIME | word | — | 0x1E0 | Seconds | Time to complete initial offset learn |
| 0x09474 | KE_EGR_INIT_LOW_POSITION | word | — | 0x1C00 | A/D Counts | Min valid initial closed position |
| 0x09476 | KE_EGR_INIT_HIGH_POSITION | word | — | 0x3100 | A/D Counts | Max valid initial closed position |
| 0x09478 | KE_EGR_OFFSET_IGN_COUNT_MAX | word | — | 0x3E8 | Count | Ignition cycles before offset relearn |
| 0x0947A | KE_EGR_PINTLE_GROWTH_MAX | word | — | 0x900 | A/D Counts | Max offset change from initial learn |
| 0x0947C | KE_EGR_MIN_NOISE_POSITION | word | — | 0x100 | Percent | Below this = valve considered closed |

### 4.2 EGR Multiplier Tables

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0947E | KV_COOLANT_TEMPERATURE_MULTIPLIE | word | 0 | Multiplier | Coolant temp multiplier on desired position |
| 0x094AA | KV_EQUIVALENCE_RATIO_MULTIPLIER | word | 0xCCD | Multiplier | EQ ratio multiplier on desired position |
| 0x094CC | KV_THROTTLE_POSITION_MULTIPLIER | word | 0 | Multiplier | Delta TPS multiplier on desired position |
| 0x094E6 | KV_TORQUE_CONVERTER_MULTIPLIER | word | — | Multiplier | TCC multiplier on desired position |
| 0x09506 | KV_BAROMETER_MULTIPLIER | word | — | Multiplier | Barometric pressure multiplier |
| 0x09518 | KA_EGR_DESIRED_POSITION | table | — | Percent | Desired EGR position vs RPM × Air/Cyl |

### 4.3 EGR Speed/Filter Coefficients

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0980A | KE_EGR_VEHICLE_SPEED_THRESHOLD | word | 0x680 | MPH | Speed threshold for filter switching |
| 0x0980C | KV_HIGH_VEHICLE_SPEED_COEFFICIEN | word | 0x199A | Coeff. | Filter coef above speed threshold (increasing) |
| 0x09816 | KV_LOW_VEHICLE_SPEED_COEFFICIENT | word | 0x199A | Coeff. | Filter coef below speed threshold (increasing) |
| 0x09820 | KV_EGR_VEHICLE_SPEED_COEFFICIENT | word | 0xFFFF | Coeff. | Filter coef for decreasing desired position |

### 4.4 EGR PID Gains (Vacuum-Compensated)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0982A | KV_INITIAL_DUTY_CYCLE | word | 0x600 | Percent | Feed-forward duty cycle vs desired position |
| 0x09834 | KV_INITIAL_INTEGRAL_VACUUM_CORRE | word | — | Multiplier | Vacuum correction on initial integrator |
| 0x09854 | KV_POSITION_INTEGRAL_GAIN | word | 0xFD | Multiplier | Integral gain vs position error |
| 0x0986A | KV_INTEGRAL_VACUUM_CORRECTION | word | — | Multiplier | Vacuum correction on integral term |
| 0x0988A | KV_POSITION_PROPORTIONAL_GAIN | word | 0x80D | Multiplier | Proportional gain vs position error |
| 0x098A0 | KV_PROPORTIONAL_VACUUM_CORRECTIO | word | — | Multiplier | Vacuum correction on proportional term |

### 4.5 EGR Enable/Disable Thresholds

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x098C0 | KE_VEHICLE_SPEED_DISABLE_THRESHO | word | 0x300 | MPH | Speed below which EGR disabled |
| 0x098C2 | KE_VEHICLE_SPEED_ENABLE_THRESHOL | word | — | MPH | Speed above which EGR enabled |
| 0x098C4 | KE_THROTTLE_POSITION_DISABLE_THR | word | — | Percent | TPS below which EGR disabled |
| 0x098C6 | KE_THROTTLE_POSITION_ENABLE_THRE | word | — | Percent | TPS above which EGR enabled |
| 0x098C8 | KE_LOWER_IAT_ENABLE_THRESHOLD | word | — | °C | IAT above which EGR enabled |
| 0x098CA | KE_LOWER_IAT_DISABLE_THRESHOLD | word | — | °C | IAT below which EGR disabled |
| 0x098CC | KE_EGR_HIGH_AIRFLOW_THRESHOLD | word | — | g/s | High airflow EGR disable |
| 0x098CE | KE_EGR_LOW_AIRFLOW_THRESHOLD | word | — | g/s | Low airflow EGR disable |
| 0x098D0 | KE_LOWER_MAP_ENABLE_THRESHOLD | word | — | kPa | MAP above which EGR enabled |
| 0x098D2 | KE_LOWER_MAP_DISABLE_THRESHOLD | word | — | kPa | MAP below which EGR disabled |
| 0x098D4 | KE_CLUTCH_TRANSITION_TIMER_THRES | word | — | Seconds | EGR disable after AC clutch engage |
| 0x098D6 | KE_EGR_PWRUP_COOLANT_DELAY_THRES | word | — | °C | Coolant delay threshold at powerup |
| 0x098D8 | KE_EGR_COOLANT_ENABLE_THRESHOLD | word | — | °C | Coolant above which EGR enabled |
| 0x098DA | KE_EGR_ENABLE_COOLANT_TIME | word | — | Seconds | Time after coolant met before enabling |
| 0x098DC | KE_UPPER_TPS_ENABLE_THRESHOLD | word | — | Percent | Upper TPS below which EGR enabled |
| 0x098DE | KE_UPPER_TPS_DISABLE_THRESHOLD | word | — | Percent | Upper TPS above which EGR disabled |

### 4.6 EGR Multi-Stroke (Pintle Cleaning)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x098E0 | KE_EGR_MULTI_STROKE_ENABLED | byte | — | TRUE/FALSE | Enable multi-stroke pintle cleaning |
| 0x098E2 | KE_EGR_STRK_LOW_COOLANT_TEMP | word | — | °C | Min coolant for stroking |
| 0x098E4 | KE_EGR_STRK_HIGH_COOLANT_TEMP | word | — | °C | Max coolant for stroking |
| 0x098E6 | KE_EGR_STRK_LOW_EGR_POSITION | word | — | Percent | Min desired EGR for stroking |
| 0x098E8 | KE_EGR_STROKE_COUNTER_LMT | word | — | Strokes | Max strokes per ignition cycle |
| 0x098EA | KE_EGR_STROKE_TIME_DELAY | word | — | Seconds | Min open time to count as stroke |
| 0x098EC | KE_EGR_STROKE_STABILIZATION | word | — | Seconds | Min stable time before stroke |
| 0x098EE | KE_EGR_STROKE_RESET_TIME_PERIOD | word | — | Seconds | Re-enable interval |
| 0x098F2 | KE_EGR_STRK_MAX_OPEN_TIME | word | — | Seconds | Max open time per stroke |

### 4.7 Airflow Integration

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08110 | KA_EGR_AIR_FLOW | byte | 0 | g/s | EGR air flow through valve (stock=0, EGR disabled) |
| 0x081D6 | KE_EGR_AIR_FLOW_FILT_COEF | word | 1 | 0-1 | Filter coef for calculated EGR flow |
| 0x081D8 | KE_EGR_DUTY_CYCLE_DYNAAIR | word | 0x66 | Percent | Min duty cycle to enable EGR air mass calc |
| 0x08920 | KE_EGR_DIAG_FINISHED_TIME | word | 0 | Seconds | Dyna-Air learn disable after EGR diag test |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFF2C0 | word | sub_2DA2A+8 | EGR pintle position ADC raw value |
| FFFF8280 | word | sub_2DAA6+A, sub_2DA2A+10 | Learned EGR closed position (A/D counts) |
| FFFF8282 | word | sub_2DACE+E2 | Initial learned closed position |
| FFFF8284 | byte | sub_2DACE+D4 | Offset learning complete flag (1=done) |
| FFFF8285 | byte | sub_2DAA6+4, sub_2DA2A+100 | Initial learn in progress flag (1=init, 0=normal) |
| FFFF8286 | byte | sub_2DACE+ED | EGR position fault flag (1=fault) |
| FFFF827E | word | sub_2DACE+DA | Ignition cycle counter for offset relearn |
| FFFFA248 | word | sub_2DAA6+C | Current learned closed position |
| FFFFA24A | word | sub_2DAA6+12 | Learn timer baseline (system timer snapshot) |
| FFFFA24C | word | sub_2DACE+130 | Continuous learn timer accumulator |
| FFFFA24E | byte | sub_2DACE+104 | Ignition cycle elapsed flag |
| FFFFA250 | word | sub_2DACE+D0 | Previous learned closed position |
| FFFFA252 | word | sub_2DA2A+C | Current raw EGR position (A/D counts scaled) |
| FFFFA254 | word | sub_2E27C+24 | Commanded EGR desired position (clamped to min) |
| FFFFA256 | word | sub_2E27C+8 | Raw desired EGR position (from lookup/multiplier) |
| FFFFA258 | word | sub_2DA2A+4A | Filtered EGR position (percent pintle opening) |
| FFFFA25A | word | sub_2E27C+30 | EGR PWM duty cycle output (0-0x1400) |
| FFFFA25C | word | sub_2E27C+78 | EGR integral term accumulator |
| FFFFA25E | word | sub_2E27C+C0 | Position error = desired - actual |
| FFFFA246 | byte | sub_2E27C+12 | EGR disable flag (non-zero = disabled) |
| FFFFA29E | byte | sub_2E27C+3C | Transition flag — EGR disable during some transient |
| FFFFA29F | byte | sub_2DED8+28 | TCC multiplier enable flag |
| FFFFA272 | word | sub_2DED8+62 | TCC/torque converter multiplier value |
| FFFFA290 | word | sub_2E27C+56 | EGR vacuum correction accumulator |
| FFFFAA09 | byte | sub_2D9E4+4 | Operating state (2/3/4 = EGR active states) |
| FFFFAD23 | byte | sub_2DACE+2A | State/condition 3 check for offset learning |
| FFFFB298 | word | sub_2E27C+8E | Engine vacuum / baro (internal format) |
| FFFFADB0 | word | sub_2DED8+78 | Coolant temperature (internal format) |
| FFFFA1EE | word | sub_2DED8+B0 | Equivalence ratio (×256 format) |
| FFFFAE9E | word | sub_2E27C+30 | Unknown — loaded during EGR disabled state |
| FFFFB544 | word | sub_2DAA6+12 | System free-running timer |

---

## 6. Algorithm Detail

### 6.1 Main Entry: sub_2D9E4

Called from DoLoopB (the main engine control loop). Gates execution based on
operating state at `FFFFAA09`:

```
1. Read operating state from FFFFAA09
2. If state is 2, 3, or 4:
   a. Call sub_2DA2A to read and filter pintle position
   b. Call sub_62B70 to evaluate enable/disable conditions
   c. If still in state 2/3/4: call sub_2E27C for PID control
3. Return
```

States 2, 3, and 4 appear to be the "engine running" states. State 2 may
correspond to idle/cruise, 3 to normal operation, and 4 to some transient.
The exact state semantics are determined by the scheduler in DoLoopB.

### 6.2 Position Reading: sub_2DA2A

Reads the raw pintle position from ADC channel `FFFFF2C0` and converts to
percent opening:

```
1. d1 = FFFFF2C0 >> 2       // Scale raw ADC
2. d1 = d1 << 8              // Promote to 16.8 fixed point
3. Store at FFFFA252 (raw position)
4. d1 = d1 - FFFF8280        // Subtract learned closed position offset
5. If underflow: d1 = 0
6. d1 = d1 × KE_EGR_FULL_SCALE_GAIN  // Convert to percent
7. d1 = d1 >> 8 >> 5         // Scale down (gain is in 8.5 fixed point)
8. Clamp d1 to 0x0000-0x1400 (0-100% range)
9. Select filter coefficient:
   - If operating state 2/3/4 (EGR flow test active):
     Use DI_EGRQ_KE_EGR_HS_POSITION_FILTER (high-speed filter)
   - Otherwise:
     Use EGR_KE_EGR_POSITION_FILTER_COEF (normal filter)
10. Apply first-order lag filter via sub_26608
11. If filtered position < KE_EGR_MIN_NOISE_POSITION: set to 0
12. Store filtered position at FFFFA258
```

**ADC Conversion Formula:**
```
Percent = (ADC_counts - Closed_Offset) × KE_EGR_FULL_SCALE_GAIN / 8192
```
Where 8192 = 256 × 32 (the two right-shifts).

### 6.3 Enable/Disable: sub_62B70

Called from sub_2D9E4 with operating state context. Evaluates all EGR
enable/disable conditions from calibrations:

```
Enable conditions (all must be met):
- Operating state 2/3/4
- Vehicle speed > KE_VEHICLE_SPEED_ENABLE_THRESHOLD
- TPS within window (between disable and enable thresholds)
- IAT within window
- Airflow within window
- MAP within window
- Coolant > KE_EGR_COOLANT_ENABLE_THRESHOLD + timer delay
- Not in AC clutch transition
- EGR diagnostic not active (DFCO stable, ethanol content check)

Disable conditions (any will disable):
- Vehicle speed < KE_VEHICLE_SPEED_DISABLE_THRESHO
- TPS outside window
- IAT outside window
- Airflow outside high/low thresholds
- MAP outside window
- Coolant too low
```

The function sets `FFFFA246` (EGR disable flag) and populates
calibration-dependent disable reason flags.

### 6.4 Desired Position Calculation: sub_2DED8

Calculates the desired EGR pintle position by applying multipliers to a base
lookup value:

```
1. Read base desired position from KA_EGR_DESIRED_POSITION table
   (indexed by RPM and Air/Cyl)
2. Apply TCC multiplier:
   - If TCC engaged (RPM within window):
     Use KV_TORQUE_CONVERTER_MULTIPLIER
   - Else: use 1.0 (0x1000)
3. Apply coolant temperature multiplier:
   - Read coolant temp from FFFFADB0
   - Lookup KV_COOLANT_TEMPERATURE_MULTIPLIE
4. Apply EQ ratio multiplier:
   - Read EQ ratio from FFFFA1EE
   - Lookup KV_EQUIVALENCE_RATIO_MULTIPLIER
5. Apply throttle position multiplier:
   - Lookup KV_THROTTLE_POSITION_MULTIPLIER
6. Apply barometer multiplier:
   - Lookup KV_BAROMETER_MULTIPLIER
7. Final desired position = base × TCC × coolant × EQ × TPS × baro
8. Store result for PID controller
```

### 6.5 PID Control: sub_2E27C

This is the core EGR duty cycle controller implementing a feed-forward + PID
structure with vacuum compensation:

```
1. Read desired position from sub_2DED8 output
2. If desired < KE_DESIRED_EGR_POSITION_MINIMUM: set to 0
3. If EGR disabled (FFFFA246 != 0): clear integrator, output 0, exit

4. Calculate position error:
   error = desired_position - actual_position (FFFFA258)
   Store at FFFFA25E

5. Feed-forward (initial duty cycle):
   base_duty = KV_INITIAL_DUTY_CYCLE[desired_position / 5]
   Multiply by vacuum correction from table at KV_INITIAL_INTEGRAL_VACUUM_CORRE
   Clamp to 0x1400 (100%)

6. Integral term:
   - Read position error from FFFFA25E
   - Use half of position error magnitude as index
   - Lookup KV_POSITION_INTEGRAL_GAIN with this index
   - Apply vacuum correction via KV_INTEGRAL_VACUUM_CORRECTION table
     (indexed by engine vacuum at FFFFB298)
   - Multiply gain × error, accumulate into integrator at FFFFA25C

7. Proportional term:
   - Read position error
   - Use half of error magnitude as index
   - Lookup KV_POSITION_PROPORTIONAL_GAIN
   - Apply vacuum correction via KV_PROPORTIONAL_VACUUM_CORRECTIO
   - Multiply gain × error

8. Final duty cycle = feed_forward + integral + proportional
   Clamp to 0x0000-0x1400
   Store at FFFFA25A

9. During EGR flow test (DI_EGRQ active):
   Use the DI_EGRQ commanded duty cycle instead of PID output
```

Duty cycle range is 0x0000-0x1400, corresponding to 0-100% PWM. The output
drives the EGR vacuum solenoid to position the pintle valve.

### 6.6 Offset Learning: sub_2DACE

The EGR system learns the closed pintle position to compensate for carbon
buildup and mechanical wear:

```
Initial Learn (FFFF8285 == 1):
1. Wait for operating state 3
2. Wait for KE_EGR_LEARN_ENABLE_TIME seconds
3. Read ADC position from FFFFA252
4. Verify position is between KE_EGR_POSITION_CLOSED_MIN and MAX
5. Apply first-order filter with KE_EGR_OFFSET_FILTER_COEFF
6. After KE_EGR_INIT_LEARN_CMPT_TIME:
   - Store learned position to FFFF8282, FFFF8280, FFFFA250
   - Set FFFF8284 (learn complete flag)
   - If learned position outside KE_EGR_INIT_LOW/HIGH_POSITION:
     Set FFFF8286 (fault flag)
   - Clear FFFF8285 (init done)

Continuous Learn (FFFF8284 == 1):
1. Track ignition cycles via FFFF827E
2. If cycles > KE_EGR_OFFSET_IGN_COUNT_MAX: force relearn
3. On each cycle: check if position drifted
4. Drift = current_position - initial_learned_position
5. If |drift| > KE_EGR_PINTLE_GROWTH_MAX / 32:
   - Relearn closed position (update FFFF8280)
6. Filter update uses percentage of change
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| Dyna-Air (sub_79B10) | EGR mass flow subtracted from cylinder air estimate |
| sub_7AA26 | Calculates EGR air flow from duty cycle and MAP delta |
| sub_79AB0 | Disables Dyna-Air learn during intrusive EGR diagnostic |
| ETAS Slew (sub_27C78) | Allows real-time EGR position slewing via ETAS calibration |
| Airflow Module | KA_EGR_AIR_FLOW stores nominal EGR flow rate |
| OBD-II PID $11BB, $11BD, $11C1 | Reports EGR closed position, test count, position error |
| DoLoopB | Calls sub_2D9E4 each engine control cycle |
| DoLoopC | Calls sub_2DACE for offset learning each cycle |
| CCP (Canister Purge) | EGR and CCP share the PWM manifold vacuum circuit |

### Hardware Pinout

| Signal | PCM Pin | Description |
|--------|---------|-------------|
| EGR Solenoid Control | C2 Green Pin 3 | PWM output to EGR vacuum solenoid |
| EGR Pintle Position | C1 Blue Pin 55 | ADC input from pintle position potentiometer (0-5V) |

### Boost OS Repurposing

Boost OS V3.4 repurposes both EGR signals:
- **C2 Pin 3** → boost control solenoid (wastegate/boost controller PWM)
- **C1 Pin 55** → wideband O2 sensor analog input (0-5V AFR signal)

The Boost OS binary diff confirms EGR-related calibration changes in the
0x0D0000-0x0E0000 custom code region.

---

## 8. Gaps & Unresolved

1. **Sub_62B70 full trace**: The complete enable/disable condition evaluation
   is complex (~100 instructions). Only the structure has been identified;
   specific branch conditions and their calibration sources need full tracing.

2. **DI_EGRQ flow test subroutines**: The intrusive EGR flow diagnostic
   (DG_EGRQ and DI_EGRQ modules with 30+ calibrations) uses a separate
   control path through sub_62B70. The test state machine (TEST_STARTED →
   SAMPLE_CALCULATION → COMPLETE) has not been fully documented.

3. **EGR multi-stroke logic**: The pintle cleaning stroking routine uses
   separate timing thresholds. The exact stroking PWM profile and interaction
   with the main PID controller is not traced.

4. **EGR solenoid PWM output address**: The actual hardware register where
   the duty cycle from sub_2E27C is written has not been identified. The
   duty cycle is stored at FFFFA25A but the final output writing function
   has not been traced.

5. **Operating states 2/3/4 semantics**: The meaning of these states at
   FFFFAA09 needs verification against the DoLoopB scheduler documentation.

6. **Pintle position ADC channel number**: FFFFF2C0 is the ADC result register
   but the QADC channel assignment (which physical ADC channel this maps to)
   has not been confirmed.

---

## 9. How To Verify

```bash
# Verify EGR disabled on Corvette M6 stock bin
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_EGR_ENABLED @ 0x09458: {data[0x09458]:02X} (0=disabled, 1=enabled)')
print(f'KA_EGR_AIR_FLOW @ 0x08110: {data[0x08110]:02X} (0=no flow)')
print(f'KE_EGR_DIAG_FINISHED_TIME @ 0x08920: {data[0x08920]:04X} (0=no test)')
"
```

```bash
# Verify EGR subroutines exist and are cross-referenced
grep -c "sub_2D9E4\|sub_2DA2A\|sub_2DAA6\|sub_2DACE\|sub_2DED8\|sub_2E27C" \
  12587603-2004-Corvette-M6.sanitized.asm
# Should show multiple references (function definitions + cross-references)
```

```bash
# Count EGR calibrations vs documented
grep "^EGR," Resources/12587603.csv | wc -l
# Should match our calibration table entries
```

---

## 10. Community Knowledge

- **pcmhacking.net**: EGR is commonly deleted on performance applications.
  Disabling requires setting KE_EGR_ENABLED = 0 AND disabling the associated
  DTCs (P0400-P0409 range) to prevent MIL illumination.

- **EFILive/HPTuners**: EGR parameters are typically hidden in the "Airflow"
  and "Emissions" tabs. The EGR desired position table (KA_EGR_DESIRED_POSITION)
  is accessible in most tuning suites.

- **Boost OS**: EGR hardware is repurposed entirely. The solenoid driver
  provides a convenient 0-12V PWM output for boost control without adding
  external hardware. The pintle ADC channel provides a 0-5V analog input
  for wideband O2 feedback.

- **EGR effect on fueling**: When EGR is active, inert exhaust gas displaces
  oxygen in the cylinder, requiring less fuel for the same AFR. The PCM
  compensates by subtracting EGR mass from the Dyna-Air calculation. Without
  this compensation, adding EGR would cause rich conditions.
