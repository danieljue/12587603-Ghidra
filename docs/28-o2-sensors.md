# P59 OS 12587603 — O2 Sensor System

> Traced from 68k disassembly — 2026-06-22
> The O2 sensor system provides closed-loop fuel control feedback, post-catalyst
> monitoring, and heater management. It supports up to 4 sensors (2 pre-cat,
> 2 post-cat) with resistance-based heater temperature estimation.

---

## 1. Overview

The P59 oxygen sensor system manages:
- **Pre-catalyst O2 sensors (Bank 1/2 Sensor 1)**: Narrowband 0-1V switching
  sensors used for closed-loop fuel control. Generate the short-term and
  long-term fuel trims.
- **Post-catalyst O2 sensors (Bank 1/2 Sensor 2)**: Monitor catalyst efficiency.
  Used for catalyst diagnostics and post-O2 fuel trim.
- **O2 Heater Control**: PWM-controlled heaters with resistance-based
  temperature estimation. The heater resistance changes predictably with
  temperature, allowing the PCM to estimate sensor temperature without a
  separate temp sensor.

The closed-loop fuel control chain is documented in doc 07 (Fuel System).
This doc covers the O2 sensor hardware interface, heater control, and
diagnostic readiness.

**On the 2004 Corvette M6:** 4 O2 sensors (2 pre-cat, 2 post-cat). Heated
narrowband sensors with PCM-controlled heater duty cycle.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_33CBE | 0x033CBE | — | O2 sensor ready detection (voltage-based) |
| sub_33D02 | 0x033D02 | — | Post-O2 integral control (bank exhaust config) |
| sub_33E7E | 0x033E7E | — | Post-O2 mode selection (decel/cruise/light accel) |
| sub_33EC8 | 0x033EC8 | — | Post-O2 time constant filtering |
| sub_33FC6 | 0x033FC6 | — | Post-O2 integrator calculation |
| sub_3442A | 0x03442A | — | Post-O2 proportional/idle factor |
| sub_344B6 | 0x0344B6 | — | Post-O2 derivative term filter |
| sub_334F8 | 0x0334F8 | — | LTFT enleanment rate with O2 feedback |
| sub_34B00 | 0x034B00 | — | Short-term O2 switching / fast O2 filter |

---

## 3. Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                     O2 SENSOR SYSTEM                               │
│                                                                    │
│  Pre-Cat O2 Sensors (Bank 1/2 S1):                                 │
│    ADC → O2 voltage (mV) → KE_OXYGEN_SENSOR_SCALE_FACTOR          │
│    │                                                               │
│    ├─ Short-Term Fuel Trim (sub_34B00):                            │
│    │   Fast switching: O2 crosses rich/lean threshold →            │
│    │     adjust injector pulse width directly                      │
│    │   Slow O2 filter (KV_SLOW_O2_FILTER)                          │
│    │   Proportional + Integral terms                               │
│    │                                                               │
│    └─ Long-Term Fuel Trim (sub_334F8):                             │
│        Accumulates STFT corrections into cell-based LTFT            │
│        Adaptive learn: updates KAM (keep-alive memory)              │
│                                                                    │
│  Post-Cat O2 Sensors (Bank 1/2 S2):                                │
│    ADC → O2 voltage → post-cat monitoring                          │
│    │                                                               │
│    ├─ Catalyst Efficiency: compares pre/post O2 activity            │
│    ├─ Post-O2 Fuel Trim: secondary fuel correction                 │
│    │   • P (proportional): KV_POST_O2_PROPORTIONAL_OFFSET          │
│    │   • I (integral): KV_POST_OXYGEN_INTEGRAL_DELAY              │
│    │   • D (derivative): KV_POST_OXYGEN_DERIVATIVE_OFFSET         │
│    │   • Mode-based: decel/cruise/light_accel thresholds           │
│    │   • Idle factor: reduced proportional aggressiveness          │
│    └─ Sensor Ready: voltage must leave middle range                │
│        for KE_POST_OXYGEN_READY_COUNTER samples                    │
│                                                                    │
│  Heater Control (OXYGEN_SENSOR module):                            │
│    │                                                               │
│    ├─ Resistance-Based Temp Estimate:                              │
│    │   Measure heater current → resistance                         │
│    │   R = V_heater / I_heater                                     │
│    │   Temp = f(R) via KA_O2_HEATER_DEGREES_PER_OHM               │
│    │   Base: KV_O2_HEATER_ROOM_TEMP_RESIST at room temp            │
│    │                                                               │
│    ├─ PWM Heater Drive:                                            │
│    │   Turn on when temp < KV_O2_HEATER_TURN_ON_TEMP               │
│    │   Turn off when temp > KV_O2_HEATER_TURN_OFF_TEMP             │
│    │   Cold start delay: KV_COLD_O2_HEATER_DELAY                   │
│    │   Overvoltage shutdown: KE_O2_HEATER_OVERVOLTAGE_LIMIT        │
│    │                                                               │
│    └─ Heater Learn:                                                │
│        Rezero at power-up if engine was off long enough            │
│        Limit part error learn within temp window                   │
│        Inrush current stabilization                                │
│                                                                    │
│  Diagnostic Readiness:                                             │
│    • Sensor ready: voltage outside lean-to-rich middle              │
│    • Heater ready: temp in operating range, current valid           │
│    • Closed-loop enable: all readiness + coolant + run time        │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 O2 Sensor Configuration (OXYGEN_SENSOR module, 0xFC88-0xFCA6)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0xFC88 | KE_DEV_CNTL_O2_HTR_AIRFLOW_LIMIT | word | — | g/s | Max airflow for heater control |
| 0xFC8A | KE_O2_HEATER_OVERVOLTAGE_LIMIT | word | — | Volts | Voltage above which heaters disabled |
| 0xFC8C | KE_OXYGEN_SENSOR_SCALE_FACTOR | word | — | mV/AD | ADC count → millivolt conversion |
| 0xFC8E | KE_INRUSH_CURRENT_STABILIZE_TIME | word | — | Seconds | Heater inrush stabilization time |
| 0xFC90 | KE_HEATER_INRUSH_OHMS_FILT_COEF | word | — | Filt Coef | Inrush resistance filter |
| 0xFC92 | KE_HEATER_OHMS_FILTER_COEF | word | — | Filter Coef | Heater resistance filter |
| 0xFC94 | KE_HEATER_ON_SAMPLE_DELAY | word | — | Seconds | Delay after heater on for sampling |
| 0xFC96 | KE_LPL_ABS_TEMP_DIFF | word | — | °C | Limit learn absolute temp diff |
| 0xFC98 | KE_LIMIT_LEARN_RUN_TIME_ABORT | word | — | Seconds | Max time for limit part learn |
| 0xFC9A | KE_MEASURED_HEATER_CURRENT_MIN | word | — | Amps | Min valid heater current |
| 0xFC9C | KE_O2_HEATER_REZERO_OFF_TIME | word | — | Seconds | Min engine-off time for rezero |
| 0xFCA0 | KE_O2_HEATER_REZERO_TEMP_DIFF | word | — | °C | Max ambient-coolant diff for rezero |
| 0xFCA2 | KE_O2_HEATER_ROOM_TEMP | word | — | °C | Room temp for resistance equation |
| 0xFCA4 | KE_POST_O2_HTR_STARTUP_COOL_MIN | word | — | °C | Min coolant for post-O2 heater startup |
| 0xFCA6 | KE_PRE_O2_SENSORS | word | — | 1-2 | Number of pre-cat O2 sensors |

### 4.2 Heater Temperature Control

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0xFCAC | KV_COLD_O2_HEATER_DELAY | table | — | Seconds | Cold start heater delay vs ECT |
| 0xFCBC | KV_HEATER_INRUSH_RESIST_MAX | table  | — | Ohms | Max inrush resistance for filter |
| 0xFCC4 | KV_LIMIT_PART_ERROR_MAX | table | — | Ohms | Max limit learn error |
| 0xFCCC | KV_LIMIT_PART_ERROR_MIN | table | — | Ohms | Min limit learn error |
| 0xFCD4 | KV_O2_HEATER_CKT_VOLTAGE_ADJ | table | — | Volts | Heater circuit voltage adjustment |
| 0xFCDC | KV_O2_HEATER_PRESENT | table | — | O2_Heater_Present | Sensor installed (0/1 per sensor) |
| 0xFCE0 | KV_O2_HEATER_ROOM_TEMP_RESIST | table | — | Ohms | Resistance at room temp per sensor |
| 0xFCE8 | KV_O2_HEATER_TURN_OFF_TEMP | table | — | °C | Temp above which heater off |
| 0xFCF0 | KV_O2_HEATER_TURN_ON_TEMP | table | — | °C | Temp below which heater on |
| 0xFCF8 | KA_O2_HEATER_DEGREES_PER_OHM | table | — | °C | °C per ohm per sensor |

### 4.3 Post-O2 Fuel Trim (FUEL_O2 module)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0xE844 | KE_POST_DERIVATIVE_TERM_FILTER | byte | 0x4D | 0-1 | Derivative filter time constant |
| 0xE846 | KE_POST_PROPORTIONAL_IDLE_FACTOR | word | 0x800 | Scaler 2 | Idle proportional reduction factor |
| 0xE848 | KE_LONG_TERM_IDLETHROTTLE_THRESH | word | 0x4D | Percent | TPS threshold for idle detection |
| 0xE84A | KE_LONG_TERM_IDLE_VEH_SPD_THRESH | word | 0x180 | SHORTCARD | VSS threshold for idle detection |
| 0xE84C | KE_POST_OXYGEN_LEAN_READY | word | — | mV | Low voltage for sensor ready |
| 0xE84E | KE_POST_OXYGEN_RICH_READY | word | — | mV | High voltage for sensor ready |
| 0xE850 | KE_POST_OXYGEN_READY_COUNTER | byte | 0x50 | Counts | Samples to confirm sensor ready |
| 0xE851 | KE_BANK_EXHAUST | byte | 1 | Value | Exhaust bank configuration |
| 0xE852 | KE_POST_OXYGEN_INTEGRAL_COOLANT | word | 0x700 | °C | Min coolant for post-O2 integral |
| 0xE854 | KV_POST_OXYGEN_BANK1_INTEGRATOR | table | — | 0-2 | Bank 1 integrator enable criteria |
| 0xE85E | KV_POST_OXYGEN_BANK2_INTEGRATOR | table | — | 0-2 | Bank 2 integrator enable criteria |
| 0xE868 | KE_POST_O2_DECEL_UPPER_LIMIT | word | 0x1500 | 0-64 | Decel mode upper limit |
| 0xE86A | KE_POST_O2_CRUISE_UPPER_LIMIT | word | 0x2000 | 0-64 | Cruise mode upper limit |
| 0xE86C | KE_POST_O2_LIGHT_ACCEL_UPPER_LIM | word | 0x3000 | 0-64 | Light accel mode upper limit |
| 0xE86E | KE_POST_TIME_CONSTANT | byte | 0x20 | 0-1 | Post-O2 time constant |
| 0xE870 | KV_POST_OXYGEN_INT_OFFSET_MAX | table | — | mV | Max integral offset |
| 0xE87A | KV_POST_OXYGEN_INT_OFFSET_MIN | table | — | mV | Min integral offset |
| 0xE884 | KV_BANK1_POST_LEAN_THRESHOLD | table | — | mV | Bank 1 lean threshold |
| 0xE88E | KV_BANK2_POST_LEAN_THRESHOLD | table | — | mV | Bank 2 lean threshold |
| 0xE898 | KV_BANK1_POST_RICH_THRESHOLD | table | — | mV | Bank 1 rich threshold |
| 0xE8A2 | KV_BANK2_POST_RICH_THRESHOLD | table | — | mV | Bank 2 rich threshold |
| 0xE8AC | KE_POST_OXYGEN_INTEGRATE | word | 0x80 | mV | Integration step size |
| 0xE8AE | KV_POST_OXYGEN_INTEGRAL_DELAY | table | — | Seconds | Integral delay time |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFADB0 | word | doc 07 | Coolant temperature (ECT) |
| FFFFA1EE | word | doc 07 | Equivalence ratio |

> **Note:** The O2 sensor system's specific RAM variables (O2 voltages per
> bank, STFT/LTFT cells, heater states, sensor ready flags) are primarily
> documented in doc 07 (Fuel System) and doc 02 (RAM Address Map).

---

## 6. Algorithm Detail

### 6.1 O2 Sensor Ready Detection

```
Pre-cat sensors:
  Ready when voltage crosses rich/lean thresholds repeatedly
  Engine run time minimum
  Heater temperature in operating range

Post-cat sensors (sub_33CBE):
  1. Read post-O2 voltage (ADC → mV via KE_OXYGEN_SENSOR_SCALE_FACTOR)
  2. Sensor NOT ready if voltage between:
     KE_POST_OXYGEN_LEAN_READY and KE_POST_OXYGEN_RICH_READY
     (middle range = sensor cold, not switching)
  3. Count samples outside this range
  4. When count > KE_POST_OXYGEN_READY_COUNTER → sensor ready
```

### 6.2 Heater Control

```
Resistance-based temperature estimation:
  T = T_room + (R_measured - R_room) / KA_O2_HEATER_DEGREES_PER_OHM
  where:
    R_measured = V_heater / I_heater
    R_room = KV_O2_HEATER_ROOM_TEMP_RESIST[sensor]
    T_room = KE_O2_HEATER_ROOM_TEMP

Heater PWM control:
  - If T < KV_O2_HEATER_TURN_ON_TEMP: turn heater ON
  - If T > KV_O2_HEATER_TURN_OFF_TEMP: turn heater OFF
  - Cold start: delay KV_COLD_O2_HEATER_DELAY[ECT] before enabling
  - Inrush: stabilize KE_INRUSH_CURRENT_STABILIZE_TIME before sampling
  - Filter: KE_HEATER_INRUSH_OHMS_FILT_COEF for inrush,
            KE_HEATER_OHMS_FILTER_COEF for steady-state

  Protection:
  - Overvoltage: V_ignition > KE_O2_HEATER_OVERVOLTAGE_LIMIT → heaters OFF
  - Current min: I < KE_MEASURED_HEATER_CURRENT_MIN → invalid, fault
  - Airflow max: MAF > KE_DEV_CNTL_O2_HTR_AIRFLOW_LIMIT → disable

Heater Rezero/Learn:
  - At power-up: if engine was off > KE_O2_HEATER_REZERO_OFF_TIME
    AND |T_ambient - T_coolant| < KE_O2_HEATER_REZERO_TEMP_DIFF
    → Rezero heater resistance baseline
  - Limit part error learn during engine run:
    ECT between KE_RCOHT_LEARN_COOLANT_TEMP_MIN and MAX
    Time limit: KE_LIMIT_LEARN_RUN_TIME_ABORT
    Error clamped between KV_LIMIT_PART_ERROR_MIN and MAX
```

### 6.3 Post-O2 Fuel Trim

```
Post-catalyst O2 sensors provide secondary fuel correction:

1. Mode selection (sub_33E7E):
   Based on closed-loop integrator value:
   - < KE_POST_O2_DECEL_UPPER_LIMIT → DECEL mode
   - < KE_POST_O2_CRUISE_UPPER_LIMIT → CRUISE mode
   - < KE_POST_O2_LIGHT_ACCEL_UPPER_LIM → LIGHT_ACCEL mode
   - > LIGHT_ACCEL_UPPER_LIM → HEAVY_ACCEL mode (no correction)

2. Proportional term:
   Offset = KV_POST_O2_PROPORTIONAL_OFFSET[O2_voltage]
   If idle (TPS < KE_LONG_TERM_IDLETHROTTLE_THRESH
        AND VSS < KE_LONG_TERM_IDLE_VEH_SPD_THRESH):
     Offset ×= KE_POST_PROPORTIONAL_IDLE_FACTOR
   Disabled for KV_POST_PROP_DISABLE_TIME after start
   Ramped in over KV_POST_PROP_RAMP_IN_TIME

3. Integral term:
   Integrate O2 voltage error at rate KE_POST_OXYGEN_INTEGRATE
   Delay between updates: KV_POST_OXYGEN_INTEGRAL_DELAY
   Enable: coolant > KE_POST_OXYGEN_INTEGRAL_COOLANT
   Clamp between KV_POST_OXYGEN_INT_OFFSET_MIN and MAX
   Bank-specific integrator criteria per KV_POST_OXYGEN_BANKx_INTEGRATOR

4. Derivative term:
   Filtered derivative of O2 voltage
   Filter time constant: KE_POST_DERIVATIVE_TERM_FILTER
   Offset from KV_POST_OXYGEN_DERIVATIVE_OFFSET
   Disabled for KV_POST_DERIV_DISABLE_TIME after start
   Ramped in over KV_POST_DERIV_RAMP_IN_TIME

5. Total post-O2 correction = P + I + D
   Added to base fuel calculation (see doc 07)
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| Fuel System (doc 07) | STFT/LTFT based on pre-cat O2; post-O2 trim added to final fuel |
| Closed Loop Enable | O2 sensor ready + heater ready + coolant + run time |
| DTC/MIL (doc 18) | Diagnostic trouble codes for sensor performance |
| Catalyst Monitor | Pre vs post O2 activity ratio = catalyst efficiency |
| CCP/EVAP (doc 23) | O2 feedback used for purge vapor compensation |
| AIR Pump (doc 24) | O2 response verifies AIR system function |
| Heater Circuit | PWM outputs driving O2 heater elements |
| ADC Hardware | Multiple QADC channels for O2 voltage inputs |

---

## 8. Gaps & Unresolved

1. **O2 sensor ADC channels**: The specific QADC channels mapping to each of
   the 4 O2 sensors have not been identified.

2. **Heater PWM output pins**: The hardware registers driving the O2 heater
   PWM for each sensor bank are not traced.

3. **STFT algorithm detail**: The short-term fuel trim switching logic (fast
   O2 filter, rich/lean thresholds, proportional+integral gains) is complex
   and only summarized here. Full trace requires reading sub_34B00 in detail.

4. **LTFT cell structure**: The long-term fuel trim cell map (RPM × MAP grid,
   number of cells, cell boundaries) and adaptive learn conditions are not
   fully documented.

5. **Post-O2 disable conditions**: The specific conditions (DFCO, PE, open
   loop, CCP active, EGR diag) that disable post-O2 correction need
   enumeration from the code.

---

## 9. How To Verify

```bash
# Verify O2 sensor heater configuration
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_PRE_O2_SENSORS @ 0x0FCA6: {data[0x0FCA6]:02X} (1-2)')
print(f'KE_BANK_EXHAUST @ 0x0E851: {data[0x0E851]:02X} (1=single,2=dual)')
"
```

---

## 10. Community Knowledge

- **O2 sensor delete (rear)**: Removing post-cat O2 sensors requires disabling
  DTCs P0420/P0430. Many tuners use "O2 simulators" that generate a fake
  switching signal to fool the PCM into thinking the catalyst is working.

- **Heater delete**: Removing O2 heaters causes slow sensor response at idle.
  Not recommended except on race-only vehicles that stay at high RPM/load.

- **Wideband O2**: Stock P59 uses narrowband sensors. Wideband requires
  external controller. The EGR ADC input (C1 Pin 55) is repurposed for
  wideband in Boost OS applications.

- **Long tube headers**: Moving O2 sensors farther downstream with long tubes
  causes slow sensor response and potential closed-loop instability. Tuners
  adjust O2 switching thresholds and heater duty cycle to compensate.
