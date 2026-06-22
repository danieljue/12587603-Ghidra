# P59 OS 12587603 — AC / Air Conditioning Control

> Traced from 68k disassembly — 2026-06-22
> The A/C system manages the compressor clutch, handles AC requests from the
> HVAC module via Class 2 serial, and integrates with engine torque management
> for smooth clutch engagement and disengagement.

---

## 1. Overview

The P59 PCM controls the A/C compressor clutch relay based on:
- HVAC request (Class 2 serial message from the climate control module)
- Engine conditions (RPM, TPS, coolant temp, vehicle speed)
- System conditions (voltage, refrigerant pressure)
- Performance protection (WOT disable, high RPM disable, police mode)

The "AC Bump" spark retard system momentarily retards timing during clutch
engagement to prevent RPM dip. A separate "AC Slugging" feature (for hot
restarts with high IAT) preemptively runs the compressor during cranking
to clear liquid refrigerant from the compressor.

**On the 2004 Corvette M6:** KE_TYPE_OF_AC_ON_VEHICLE = 2 (standard system
with pressure sensor). The AC compressor is PCM-controlled with full
integration into torque management.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_2BA40 | 0x02BA40 | 148806 | Main AC control — called from DoLoopC+158 |
| sub_2C35A | 0x02C35A | 149752 | AC request debounce and state change detection |
| sub_5F4A6 | 0x05F4A6 | — | AC clutch relay diagnostic (DG_AC) |
| sub_5F566 | 0x05F566 | — | AC pressure diagnostic (P0531) |
| OS3:7EAF2 | 0x07EAF2 | — | AC Bump spark control — torque management integration |
| OS3:7EB28 | 0x07EB28 | — | AC Bump clutch delay timing |
| sub_7E0BC | 0x07E0BC | — | Engine torque calculation (includes AC compressor torque) |

---

## 3. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AC CONTROL FLOW                               │
│                                                                     │
│  HVAC Module (Class 2)                                              │
│    │                                                                │
│    ├─ AC Request On/Off                                             │
│    ├─ Recirculation Mode Request                                    │
│    ▼                                                                │
│  sub_2C35A (Debounce)                                               │
│    │  AC request must be stable for calibrated time                 │
│    │  FFFFBF32 bit 1 → raw request                                  │
│    │  FFFFAD8B bit 6 → debounced request state                     │
│    ▼                                                                │
│  sub_2BA40 (Main Control) — called from DoLoopC                     │
│    │                                                                │
│    ├─ AC Type detection (KE_TYPE_OF_AC_ON_VEHICLE)                  │
│    │   0 = No AC                                                    │
│    │   1 = AC with clutch feedback                                  │
│    │   2 = AC without feedback (pressure switch only)               │
│    │   5 = AC not supported                                         │
│    │                                                                │
│    ├─ Enable Conditions (all must pass):                            │
│    │   RPM: between KE_AC_ENGINE_SPEED_LOWER/UPPER_LIMIT            │
│    │   TPS: < KE_AC_HIGH_TPS_DISABLE_THRESHOLD                     │
│    │   Coolant: between KE_AC_HOT_COOLANT_LOWER/UPPER_LIMIT         │
│    │   Voltage: > KE_AC_LOW_VOLTAGE_UPPER_LIMIT (engage)            │
│    │            > KE_AC_LOW_VOLTAGE_LOWER_LIMIT (maintain)          │
│    │   Pressure: between high/low pressure limits                   │
│    │                                                                │
│    ├─ Disable Conditions (any triggers):                            │
│    │   WOT: TPS > threshold → disable for calibrated time           │
│    │   High RPM: > KE_AC_ENGINE_SPEED_UPPER_LIMIT                   │
│    │   Launch: VSS < KE_AC_VEH_SPEED_LAUNCH_DISABLE                │
│    │   Coolant overheat: > KE_AC_HOT_COOLANT_UPPER_LIMIT           │
│    │   Low voltage: < KE_AC_LOW_VOLTAGE_LOWER_LIMIT                │
│    │   High pressure: > KE_AC_HIGH_PRESSURE_UPPER_LIMIT             │
│    │   Low pressure: < KE_AC_LOW_PRESSURE_LOWER_LIMIT              │
│    │   Police mode: KE_AC_TPS_DISABLE_FOR_POLICE                   │
│    │                                                                │
│    ├─ AC Slugging (Hot Restart):                                    │
│    │   During crank if:                                             │
│    │   • IAT > KE_AC_SLUGGING_IAT                                   │
│    │   • IAT_last_keyoff > KE_AC_SLUGGING_IAT_LAST_KEY_OFF         │
│    │   • Coolant < KE_AC_COOLANT_TEMP_SLUGGING_HIGH                │
│    │   • RPM > KE_AC_SLUGGING_ENG_SPEED_ENABLE                     │
│    │   • Run for KE_AC_SLUGGING_MAX_ALLOWABLE_TIM                  │
│    │   • Stop when RPM > KE_AC_SLUGGING_ENG_SPEED_TURN_OF          │
│    │                                                                │
│    └─ Output: AC Clutch Relay state                                 │
│                                                                     │
│  AC Bump Spark (OS3 Torque Mgmt):                                   │
│    │  On clutch engagement:                                         │
│    │    • Wait KE_AC_BUMP_CLUTCH_DELAY                              │
│    │    • Ramp spark retard in (KE_AC_BUMP_TORQUE_RAMP_IN)          │
│    │    • Apply AC compressor torque (KV_AC_COMPRESSOR_TORQUE)      │
│    │    • Limit by KA_AC_BUMP_SPARK_RETARD_LIMIT                    │
│    │    • Duration limit: KE_AC_BUMP_SPARK_DURATION_LIMIT           │
│    │    • Ramp spark retard out (KE_AC_BUMP_TORQUE_RAMP_OUT)        │
│    │  Disabled at idle (KE_AC_BUMP_SPARK_IDLE_OFF)                  │
│    ▼                                                                │
│  AC Pressure Sensor → KV_AC_PRESSURE_CONVERSION → PSI               │
│  Auto Recirculation → FFFFAD8B bits for recirc control              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Core AC Configuration (0x1F81C-0x1F84C)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F81C | KE_AUTO_RECIRCULATION_OPTION | byte | — | boolean | Auto recirculation equipped |
| 0x1F81E | KV_AC_PRESSURE_CONVERSION | table | — | PSI | ADC→PSI conversion for pressure sensor |
| 0x1F842 | KE_TYPE_OF_AC_ON_VEHICLE | byte | 2 | Unitless | AC system type (2=standard) |
| 0x1F844 | KE_AC_SLUGGING_MAX_ALLOWABLE_TIM | word | 0x320 | Seconds | Max slugging (compressor-on-crank) time |
| 0x1F846 | KE_AC_STATUS_INPUT_EQUIPPED | byte | 1 | BOOLEAN | Clutch relay feedback hardwired |
| 0x1F848 | KE_IGN_VOLT_LOW_DISABLE_SLUGGING | word | 0x600 | Volts | Min voltage for slugging during crank |
| 0x1F84A | KE_REFERENCE_PULSES_AC_SLUGGING | word | 0x20 | Counts | Min ref pulses for AC slugging |
| 0x1F84C | KE_AC_REQUEST_DEBOUNCE_TIME | word | 0x20 | Seconds | AC request debounce time |
| 0x1F84E | KE_AC_STARTUP_FAST_DEBOUNCE_TIME | word | 0x10 | Seconds | Fast debounce during startup window |
| 0x1F850 | KE_AC_INITIAL_STARTUP_WINDOW | word | 0x50 | Seconds | Startup window for fast debounce |

### 4.2 AC Disable/Re-enable Timing (0x1F852-0x1F85A)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F852 | KE_AC_ENGINE_SPEED_TIME | word | 0x10 | Seconds | Time RPM must be maintained to disable |
| 0x1F854 | KE_AC_TURN_OFF_DELAY | word | — | Seconds | Off delay to prevent engine flare |
| 0x1F856 | KE_AC_HIGH_TPS_RE_ENABLE_TIME | word | 0 | Seconds | Time before re-enable after WOT disable |
| 0x1F858 | KE_AC_LOW_TPS_RE_ENABLE_TIME | word | 0 | Seconds | Time before re-enable after PE disable |
| 0x1F85A | KE_AC_HIGH_TPS_REPEAT_TIME | word | 0 | Seconds | Min time between high-TPS disables |

### 4.3 RPM Limits (0x1F85C-0x1F862)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F85C | KE_AC_ENGINE_SPEED_LOWER_LIMIT | word | 0x5AE6 | RPM | Enable AC if RPM below this |
| 0x1F85E | KE_AC_ENGINE_SPEED_UPPER_LIMIT | word | 0x61E6 | RPM | Disable AC above this RPM |
| 0x1F860 | KE_AC_SLUGGING_ENG_SPEED_ENABLE | word | — | RPM | Enable slugging above this RPM |
| 0x1F862 | KE_AC_SLUGGING_ENG_SPEED_TURN_OF | word | — | RPM | Turn off slugging above this RPM |

### 4.4 Temperature Limits (0x1F864-0x1F86C)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F864 | KE_AC_HOT_COOLANT_LOWER_LIMIT | word | — | °C | Enable AC below this coolant temp |
| 0x1F866 | KE_AC_HOT_COOLANT_UPPER_LIMIT | word | — | °C | Disable AC above this coolant temp |
| 0x1F868 | KE_AC_COOLANT_TEMP_SLUGGING_HIGH | word | — | °C | Slugging disabled above this coolant |
| 0x1F86A | KE_AC_SLUGGING_IAT | word | — | °C | Slugging enabled above this IAT |
| 0x1F86C | KE_AC_SLUGGING_IAT_LAST_KEY_OFF | word | — | °C | Slugging if last-keyoff IAT above this |

### 4.5 TPS / Vehicle Speed Disable (0x1F86E-0x1F88F)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F86E | KE_AC_HIGH_TPS_DISABLE_THRESHOLD | word | — | Percent | TPS above which AC disabled |
| 0x1F870 | KE_AC_HIGH_TPS_RE_ENABLE_THRESH | word | — | Percent | TPS below which AC re-enabled |
| 0x1F872 | KE_AC_VEH_SPEED_LAUNCH_DISABLE | word | — | MPH | VSS below which launch disable |
| 0x1F874 | KE_AC_VEHICLE_SPEED_RE_ENABLE | word | — | MPH | VSS above which re-enable |
| 0x1F88E | KE_AC_TPS_DISABLE_FOR_POLICE | byte | — | BOOLEAN | Police mode — AC off entire cycle |
| 0x1F88F | KE_AC_GEARS_FOR_LAUNCH_DISABLE | byte | — | Gear | Gears ≤ this for launch disable |

### 4.6 Pressure Limits (0x1F876-0x1F87E)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F876 | KE_AC_HIGH_PRESSURE_UPPER_LIMIT | word | — | PSI | Disable AC above this pressure |
| 0x1F878 | KE_AC_HIGH_PRESSURE_LOWER_LIMIT | word | — | PSI | Re-enable AC below this pressure |
| 0x1F87A | KE_AC_LOW_PRESSURE_LOWER_LIMIT | word | — | PSI | Disable AC below this pressure |
| 0x1F87C | KE_AC_LOW_PRESSURE_UPPER_LIMIT | word | — | PSI | Re-enable AC above this pressure |
| 0x1F87E | KE_AC_PRESSURE_SLUGGING | word | — | PSI | Min pressure for slugging |

### 4.7 Voltage Limits (0x1F880-0x1F882)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F880 | KE_AC_LOW_VOLTAGE_UPPER_LIMIT | word | — | volts | Min voltage to engage clutch |
| 0x1F882 | KE_AC_LOW_VOLTAGE_LOWER_LIMIT | word | — | volts | Min voltage to maintain clutch |

### 4.8 Auto Recirculation (0x1F884-0x1F88C)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F884 | KE_AUTO_RECIRC_ENABLE_DELAY_TIME | word | — | seconds | Delay before recirc after conditions met |
| 0x1F886 | KE_AUTO_RECIRC_MIN_ON_TIME | word | — | seconds | Min recirc on time |
| 0x1F888 | KE_AUTO_RECIRC_ON_MPH | word | — | MPH | Speed below which recirc enabled |
| 0x1F88A | KE_AUTO_RECIRC_OFF_MPH | word | — | MPH | Speed above which recirc disabled |
| 0x1F88C | KE_AC_PRESSURE_INITIAL_DELAY_TIM | word | — | seconds | Initial pressure check delay |

### 4.9 AC Bump Spark Control (ENG_TORQUE module)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x09B48 | KA_AC_BUMP_SPARK_RETARD_LIMIT | word | — | Degrees | Max spark retard for AC Bump |
| 0x09Bxx | KE_AC_BUMP_SPARK_ENABLE | byte | 1 | BOOLEAN | Enable AC bump spark |
| 0x09Bxx | KE_AC_BUMP_CLUTCH_DELAY | word | 0 | Seconds | Delay after clutch before spark retard |
| 0x09Bxx | KE_AC_BUMP_TORQUE_RAMP_IN | word | 0xCD | — | Spark retard ramp-in rate |
| 0x09Bxx | KE_AC_BUMP_TORQUE_RAMP_OUT | word | 0xCD | — | Spark retard ramp-out rate |
| 0x09Bxx | KE_AC_BUMP_SPARK_DURATION_LIMIT | word | 0x1E0 | Seconds | Max AC bump spark duration |
| 0x09Bxx | KE_AC_BUMP_SPARK_IDLE_OFF | byte | 0 | BOOLEAN | Disable AC bump at idle |
| — | KV_AC_COMPRESSOR_TORQUE | word | 0x33 | — | AC compressor torque (for engine model) |
| — | KE_MAXIMUM_AC_BUMP_THROTTLE_AREA | word | 0x100 | — | Max throttle area for AC bump active |

### 4.10 Off Timing

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1F890 | KV_AC_MINIMUM_OFF_TIME | word | — | Seconds | Min time clutch must stay off |
| 0x1F8A6 | KV_AC_IAT_ON_DELAY_TIME | word | — | Seconds | Turn-on delay to prevent stall |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFAD8B | byte | sub_2BA40+20 | AC status byte — bit 5 = clutch feedback, bit 6 = debounced request |
| FFFFAD8A | byte | sub_2BA40+68 | AC state byte — bits 0/1 = AC control state |
| FFFFADAC | byte | sub_2BA40+9A | AC slugging active flag (1 = slugging) |
| FFFFAD9C | word | sub_2C35A+3C | AC request debounce timer baseline |
| FFFFADA2 | word | sub_2BA40+7A | AC timer/counter value |
| FFFFBF32 | byte | sub_2C35A+6 | Class 2 serial — bit 1 = raw AC request |
| FFFFAD1E | long | sub_2C35A+18 | Engine run time (for startup window check) |
| FFFF9E20 | word | sub_2BA40+B2 | AC-related reference (RPM-scaled) |
| FFFFB544 | word | sub_2C35A+3E | System free-running timer |
| FFFFB5DE | long | sub_2BA40+74 | Pointer to AC-related data structure |

---

## 6. Algorithm Detail

### 6.1 Main Control: sub_2BA40

Called from DoLoopC+158 each control cycle.

```
1. Check AC system type (KE_TYPE_OF_AC_ON_VEHICLE):
   - Type 5 → AC not supported → exit
   - Type 2 → standard system with pressure sensor

2. AC clutch status feedback check:
   - If KE_AC_STATUS_INPUT_EQUIPPED == TRUE:
     Read hardware feedback (bit 5 of port at off_134C+2)
     Set FFFFAD8B bit 5 accordingly
   - If not equipped:
     Clear FFFFAD8B bit 5, use bit 1 as proxy

3. AC request processing (call sub_2C35A):
   - Debounce raw AC request from FFFFBF32 bit 1
   - Set FFFFAD8B bit 6 when request is stable

4. Evaluate enable/disable conditions:
   a. Engine speed: between lower and upper limits
   b. TPS: below WOT disable threshold
   c. Coolant: below hot coolant upper limit
   d. System voltage: above low voltage limit
   e. AC pressure: within valid window

5. AC Slugging (hot restart compressor-on-crank):
   If IAT > KE_AC_SLUGGING_IAT AND
      IAT_last_keyoff > KE_AC_SLUGGING_IAT_LAST_KEY_OFF AND
      Coolant < KE_AC_COOLANT_TEMP_SLUGGING_HIGH:
   - Enable slugging: run compressor during crank
   - Continue for KE_AC_SLUGGING_MAX_ALLOWABLE_TIM
   - Disable when RPM > KE_AC_SLUGGING_ENG_SPEED_TURN_OF

6. Output clutch relay command:
   - Set appropriate output to engage/disengage compressor clutch
   - Respect KV_AC_MINIMUM_OFF_TIME (minimum off duration)

7. Auto recirculation control:
   - If pressure high AND VSS < KE_AUTO_RECIRC_ON_MPH:
     Enable recirc mode
   - Delay KE_AUTO_RECIRC_ENABLE_DELAY_TIME before activating
   - Minimum on time: KE_AUTO_RECIRC_MIN_ON_TIME
```

### 6.2 AC Bump Spark Control

When the AC clutch engages, the compressor loads the engine. To prevent RPM
dip, the PCM momentarily retards spark timing:

```
1. AC clutch engagement detected (FFFFAD8B bit 5 transition)
2. If KE_AC_BUMP_SPARK_ENABLE == TRUE:
   a. If KE_AC_BUMP_SPARK_IDLE_OFF AND at idle → skip
   b. Wait KE_AC_BUMP_CLUTCH_DELAY seconds
   c. Ramp in spark retard at rate KE_AC_BUMP_TORQUE_RAMP_IN
   d. Retard limited to KA_AC_BUMP_SPARK_RETARD_LIMIT degrees
   e. AC compressor torque from KV_AC_COMPRESSOR_TORQUE
   f. Duration limited to KE_AC_BUMP_SPARK_DURATION_LIMIT
   g. Ramp out spark retard at rate KE_AC_BUMP_TORQUE_RAMP_OUT
```

### 6.3 Diagnostic (DG_AC)

The AC diagnostic module monitors:
- **P1539**: AC clutch relay stuck high (voltage high when commanded off)
  - KE_AC_CLUTCH_HIGH_FAIL_THRESHOLD failures before DTC
  - KE_AC_CLUTCH_HIGH_PASS_THRESHOLD passes to clear
- **P1546**: AC clutch relay stuck low (voltage low when commanded on)
  - KE_AC_CLUTCH_LOW_FAIL/PASS_THRESHOLD
- **P0531**: AC pressure sensor performance
  - Must see KE_P0531_AC_PRESSURE_DELTA PSI rise after engagement
  - Within KE_P0531_AC_ON_TIME seconds
  - After KE_P0531_AC_OFF_TIME delay for pressure decay
  - Enable: pressure > KE_P0531_AC_PRESS_ENABLE_TEST OR IAT > KE_P0531_IAT_ENABLE_TEST

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoopC | Calls sub_2BA40 each cycle |
| HVAC Module (Class 2) | AC request bit in serial message (FFFFBF32 bit 1) |
| Spark Control | AC Bump retards timing during clutch engagement |
| Torque Management | AC compressor torque added to engine torque model |
| Idle Control | AC engagement triggers IAC compensation (idle-up) |
| Fan Control | AC pressure can trigger cooling fan operation |
| EGR (doc 22) | AC clutch transition disables EGR (KE_CLUTCH_TRANSITION_TIMER_THRES) |
| Pressure Sensor | Analog input → KV_AC_PRESSURE_CONVERSION → PSI |
| Coolant Temperature | Disables AC during overheat conditions |

---

## 8. Gaps & Unresolved

1. **AC clutch relay output pin**: The exact hardware output pin and register
   for the AC clutch relay driver has not been identified.

2. **Class 2 AC message format**: The specific J1850 VPW message from the HVAC
   module that carries the AC request bit has not been fully traced. The bit
   appears at FFFFBF32 but the message decoding is assumed.

3. **AC Bump ramp rates**: KE_AC_BUMP_TORQUE_RAMP_IN (0xCD) and RAMP_OUT
   require conversion from raw units to degrees/second.

4. **AC pressure sensor ADC channel**: The QADC channel for the AC pressure
   transducer has not been mapped.

5. **Auto recirculation logic**: The recirculation mode control (sends
   command back to HVAC over Class 2) has not been traced from sub_2BA40.

6. **Police mode**: KE_AC_TPS_DISABLE_FOR_POLICE disables AC for the entire
   ignition cycle. The logic path is not traced.

---

## 9. How To Verify

```bash
# Verify AC configuration on Corvette M6
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_TYPE_OF_AC_ON_VEHICLE @ 0x1F842: {data[0x1F842]:02X} (2=standard)')
print(f'KE_AC_STATUS_INPUT_EQUIPPED @ 0x1F846: {data[0x1F846]:02X} (1=wired)')
print(f'KE_AC_ENGINE_SPEED_UPPER_LIMIT @ 0x1F85E: {int.from_bytes(data[0x1F85E:0x1F860],\"big\")/5.12:.0f} RPM')
print(f'KE_AC_BUMP_SPARK_ENABLE @ 0x09Bxx: (check via CSV for exact addr)')
"
```

```bash
# Verify AC subroutines
grep -c "sub_2BA40\|sub_2C35A" 12587603-2004-Corvette-M6.sanitized.asm
```

---

## 10. Community Knowledge

- **AC delete**: Removing AC on performance builds is common. The compressor
  and condenser are physically removed. Must disable DTCs P0531, P1539, P1546.
  Some tuners set KE_TYPE_OF_AC_ON_VEHICLE to 5 (not supported).

- **AC Bump tuning**: The AC bump spark retard prevents the RPM dip when the
  compressor engages. Aggressive cams with low vacuum at idle may need more
  AC bump spark retard or higher IAC compensation.

- **Slugging**: The AC slugging feature runs the compressor momentarily during
  cranking on hot restarts. This clears liquid refrigerant from the compressor
  that condenses during heat soak. Without it, the compressor can hydraulic
  lock and damage the clutch or belt.

- **High RPM AC cut**: The Corvette disengages AC above ~6,100 RPM (0x61E6/5.12
  ≈ 6,200 RPM). This is standard across all P59 applications — the compressor
  has a maximum safe operating RPM.

- **IAT on delay**: KV_AC_IAT_ON_DELAY_TIME provides a brief delay before
  engaging AC after the request, allowing IAC to stabilize first. This
  prevents engine stall on vehicles with weak idle control.
