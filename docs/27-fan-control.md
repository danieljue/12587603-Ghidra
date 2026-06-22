# P59 OS 12587603 — Fan Control (Cooling Fan)

> Traced from 68k disassembly — 2026-06-22
> The PCM controls one or two electric cooling fans based on coolant
> temperature, AC pressure, vehicle speed, and engine oil temperature.
> Supports both relay-based dual-speed and PWM variable-speed fan systems.

---

## 1. Overview

The P59 fan control system manages engine cooling through electric fans. Two
operating modes are supported:
- **Relay-based**: Type 2 or 3 — simple on/off control with Fan1 (low speed)
  and Fan2 (high speed) relays
- **PWM variable-speed**: Default type — continuously variable fan speed via
  PWM duty cycle, with optional fan speed feedback sensor

The system integrates multiple temperature and pressure inputs to determine
fan speed demand, with protections for WOT (reduced fan load), fan lockup
detection, and after-run cooling (key-off fan operation).

**On the 2004 Corvette M6:** Uses relay-based fan control (KE_TYPE_OF_FANS
classifies the system). The stock calibration enables Fan1 at ~108°C ECT,
Fan2 at ~113°C ECT.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_2E726 | 0x02E726 | 153979 | Main fan control — called from DoLoopE+1C4 |
| sub_2E716 | 0x02E716 | — | Fan1 temperature threshold query |
| sub_2E71E | 0x02E71E | 153968 | Fan2 temperature threshold query |
| sub_7DD88 | 0x07DD88 | — | Fan lockup / overspeed protection |
| sub_3622E | 0x03622E | — | IAC inhibit during fan engagement |
| sub_66F48 | 0x066F48 | — | Fan speed delta diagnostic |
| sub_6720E | 0x06720E | — | Fan pump-out diagnostic |
| sub_67010 | 0x067010 | — | Fan speed high diagnostic |
| sub_6716E | 0x06716E | — | Fan overspeed diagnostic |
| sub_670C2 | 0x0670C2 | — | Fan speed sensor diagnostic |

---

## 3. Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     FAN CONTROL LOGIC                            │
│                                                                  │
│  DoLoopE ──▶ sub_2E726 (Main)                                    │
│               │                                                  │
│               ├─ Fan type check (KE_TYPE_OF_FANS_ON_VEHICLE)     │
│               │   Types 2/3: relay-based (Fan1/Fan2 on/off)      │
│               │   Other: PWM variable speed control              │
│               │                                                  │
│               ├─ Minimum run time: KE_ENGINE_RUNNING_FAN1_TIME   │
│               │   No fans until engine has run for this long     │
│               │                                                  │
│               ├─ ECT Demand:                                     │
│               │   KV_ECT_PCT_FANREQ[ECT] → fan speed %           │
│               │   Fan1 on: ECT > KE_ECT_FAN1_HIGH_THRESHOLD     │
│               │   Fan1 off: ECT < KE_ECT_FAN1_LOW_THRESHOLD     │
│               │   Fan2 on: ECT > KE_ECT_FAN2_HIGH_THRESHOLD     │
│               │   Fan2 off: ECT < KE_ECT_FAN2_LOW_THRESHOLD     │
│               │                                                  │
│               ├─ AC Pressure Demand:                             │
│               │   KV_AC_PCT_FANREQ[AC_PSI] → fan speed %         │
│               │   Fan1 on: AC PSI > KE_AC_PRESSURE_FAN1_HIGH    │
│               │   Fan2 on: AC PSI > KE_AC_PRESSURE_FAN2_HIGH    │
│               │   VSS overrides: low speed forces on,            │
│               │   high speed allows off (AC engaged only)        │
│               │                                                  │
│               ├─ Transmission Oil Demand:                        │
│               │   KV_TRANS_TEMP_PCT_FANREQ[trans_temp]           │
│               │                                                  │
│               ├─ Engine Oil Demand:                              │
│               │   KV_ENG_OIL_TEMP_PCT_FANREQ[oil_temp]           │
│               │   If > KE_TEMPENGINEOILHI → 100% fan             │
│               │                                                  │
│               ├─ WOT Reduction:                                  │
│               │   If TPS > KE_WOT_FANSPEEDLIMIT                  │
│               │   AND ECT < KE_WOT_COOLANTTEMP                  │
│               │   → Reduce fan to KE_WOT_PCT_FAN                 │
│               │   Limiter: KE_WOT_MAXDISABLE timeout             │
│               │                                                  │
│               ├─ Speed Ramps:                                    │
│               │   Increase rate limit: KE_FANSPEED_INCR_RATE     │
│               │   Decrease rate limit: KE_FANSPEED_DECR_RATE     │
│               │                                                  │
│               └─ Output: PWM duty cycle to fan controller        │
│                         or Fan1/Fan2 relay outputs                │
│                                                                  │
│  Fan Speed Feedback (PWM systems):                               │
│    Fan speed sensor → KE_FANRPM_OFFSET + PWM × range             │
│    Lockup detection: RPM > KE_FANFAILSPEEDRPM for lockup time    │
│    Slip management: adjusts PWM at low fan drive speeds          │
│                                                                  │
│  After-Run (Key-Off):                                            │
│    If ECT > KE_ECT_FAN1_KEYOFF at key-off:                       │
│    Run Fan1 for KE_FAN1_ON_KEYOFF_TIME seconds                   │
│                                                                  │
│  Sensor Fault: KE_FANCOMMAND_FOR_CTS_FAULT → fixed fan speed     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 AC Pressure Fan Thresholds (0x1FA54-0x1FA76)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA54 | KE_AC_PRESSURE_FAN1_HIGH_THRESHO | word | — | PSI | Fan1 on above this AC pressure |
| 0x1FA56 | KE_AC_PRESSURE_FAN1_LOW_THRESHOL | word | — | PSI | Fan1 off below this AC pressure |
| 0x1FA74 | KE_AC_PRESSURE_FAN2_HIGH_THRESHO | word | — | PSI | Fan2 on above this AC pressure |
| 0x1FA76 | KE_AC_PRESSURE_FAN2_LOW_THRESHOL | word | — | PSI | Fan2 off below this AC pressure |

### 4.2 ECT Fan Thresholds (0x1FA58-0x1FA7A)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA58 | KE_ECT_FAN1_HIGH_THRESHOLD | word | 0xACD | °C | Fan1 on above this ECT (~108°C) |
| 0x1FA5A | KE_ECT_FAN1_LOW_THRESHOLD | word | — | °C | Fan1 off below this ECT |
| 0x1FA5C | KE_ECT_FAN1_AC_ON_THRESHOLD | word | — | °C | Fan1 off below this ECT when AC on |
| 0x1FA78 | KE_ECT_FAN2_HIGH_THRESHOLD | word | 0xB4D | °C | Fan2 on above this ECT (~113°C) |
| 0x1FA7A | KE_ECT_FAN2_LOW_THRESHOLD | word | — | °C | Fan2 off below this ECT |

### 4.3 Timing (0x1FA5E-0x1FA86)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA5E | KE_ECT_FAN1_KEYOFF | word | — | °C | After-run fan if ECT above at key-off |
| 0x1FA60 | KE_ENGINE_RUNNING_FAN1_TIME | word | — | Seconds | Min run time before fan allowed |
| 0x1FA6C | KE_MINIMUM_FAN1_ON_TIME | word | — | Seconds | Min Fan1 on duration |
| 0x1FA6E | KE_MINIMUM_FAN1_OFF_TIME | word | — | Seconds | Min Fan1 off duration |
| 0x1FA70 | KE_FAN1_DELAY_OFF_AFTER_FAN2_TUR | word | — | Seconds | Delay turning off Fan1 after Fan2 off |
| 0x1FA72 | KE_FAN2_ON_DELAY_TIME | word | — | Seconds | Delay Fan2 after Fan1 enabled |
| 0x1FA7C | KE_MINIMUM_FAN2_ON_TIME | word | — | Seconds | Min Fan2 on duration |
| 0x1FA7E | KE_FAN1_TURN_ON_DELAY | word | — | Seconds | Fan1 off→on transition delay |
| 0x1FA80 | KE_FAN1_TURN_OFF_DELAY | word | — | Seconds | Fan1 on→off transition delay |
| 0x1FA82 | KE_FAN2_TURN_ON_DELAY | word | — | Seconds | Fan2 off→on transition delay |
| 0x1FA84 | KE_FAN2_TURN_OFF_DELAY | word | — | Seconds | Fan2 on→off transition delay |
| 0x1FA86 | KE_FAN1_ON_KEYOFF_TIME | word | — | Seconds | After-run fan duration |
| 0x1FA98 | KE_FANPWRUPDELAY | word | — | Seconds | Fan delay on power-up for idle stabilization |

### 4.4 Vehicle Speed / WOT (0x1FA64-0x1FAC4)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA64 | KE_HI_VEH_SPD_FANS_OFF_AC_THRESH | word | — | MPH | High speed fans-off threshold (AC) |
| 0x1FA66 | KE_VEHICLE_SPEED_HIGH_AC_FAN1_TH | word | — | MPH | VSS above which Fan1 can turn off (AC on) |
| 0x1FA68 | KE_VEHICLE_SPEED_LOW_AC_FAN1_THR | word | — | MPH | VSS below which Fan1 forced on (AC on) |
| 0x1FABE | KE_WOT_COOLANTTEMP | word | — | °C | ECT below which WOT fan reduction active |
| 0x1FAC0 | KE_WOT_FANSPEEDLIMIT | word | — | Percent | TPS above which WOT fan reduction |
| 0x1FAC2 | KE_WOT_MAXDISABLE | word | — | Seconds | Max WOT fan reduction time |
| 0x1FAC4 | KE_WOT_PCT_FAN | word | — | Percent | Fan power during WOT reduction |

### 4.5 Fan Speed Control (PWM Systems) (0x1FA8A-0x1FAA8)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA8A | KE_COOLANTTEMPOVERRIDE | word | — | °C | ECT override threshold |
| 0x1FA8C | KE_FANFAILSPEEDRPM | word | — | RPM | Fan speed above which structural failure risk |
| 0x1FA8E | KE_FANLOCKUPTIME | word | — | Seconds | Time above fail speed to declare lockup |
| 0x1FA90 | KE_FANSPEED_INCR_RATE_LIMIT | word | — | RPM | Max fan speed increase rate |
| 0x1FA92 | KE_FANSPEED_DECR_RATE_LIMIT | word | — | RPM | Max fan speed decrease rate |
| 0x1FA94 | KE_FANSPEEDLOW | word | — | RPM | Min fan speed threshold |
| 0x1FA96 | KE_LOWSPEEDPWM | word | — | Percent | PWM when fan speed too low |
| 0x1FA9A | KE_FANRPM_MAX | word | — | RPM | Max possible fan blade speed |
| 0x1FA9C | KE_FANRPM_OFFSET | word | — | RPM | Min possible fan blade speed (0% PWM) |
| 0x1FAA0 | KE_MAXFANPWMGRADIENTNEG | word | — | %/s | Max decreasing PWM rate |
| 0x1FAA2 | KE_MAXFANPWMGRADIENTPOS | word | — | %/s | Max increasing PWM rate |
| 0x1FAA8 | KE_SERVICEOVERRIDEALLOWED | word | — | Percent | Service tool override threshold |

### 4.6 Slip Power Management (0x1FAAA-0x1FAB2)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FAAA | KE_SLIP_ECT_MAXHI | word | — | °C | ECT above which slip management disabled |
| 0x1FAAC | KE_SLIP_ECT_MAXLO | word | — | °C | ECT below which slip management allowed |
| 0x1FAAE | KE_SLIP_PCT_FANHI | word | — | Percent | Fan power at high slip drive speed |
| 0x1FAB0 | KE_SLIPFANDRIVEHI | word | — | RPM | Fan drive speed → high slip power |
| 0x1FAB2 | KE_SLIPFANDRIVELO | word | — | RPM | Fan drive speed → slip management needed |

### 4.7 Temperature Demand Tables

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FAC6 | KV_AC_PCT_FANREQ | table | — | Percent | AC pressure → fan speed demand |
| 0x1FAE8 | KV_ECT_PCT_FANREQ | table | — | Percent | ECT → fan speed demand |
| 0x1FB0A | KV_MAXFAN_PCT_CMD | table | — | Percent | RPM → max allowed fan speed |
| 0x1FB2C | KV_TRANS_TEMP_PCT_FANREQ | table | — | Percent | Trans temp → fan speed demand |
| 0x1FB3E | KV_ENG_OIL_TEMP_PCT_FANREQ | table | — | Percent | Oil temp → fan speed demand |

### 4.8 Fan Speed/PWM Correction

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FB50 | KA_DELTA | table | — | %/s | PWM adjustment from speed feedback |
| 0x1FC82 | KA_PCT_PWM | table | — | Percent | Base PWM → output driver duty cycle |

### 4.9 Other Limits

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA62 | KE_FANCOMMAND_FOR_CTS_FAULT | word | — | Percent | Fan speed when CTS sensor faulted |
| 0x1FA6A | KE_MIN_RPM_TO_DETECT_FANLOCKUP | word | — | RPM | Min engine RPM for lockup detection |
| 0x1FA9E | KE_MAXVEHICLESPEED | word | — | kPH | Max vehicle speed for fan model |
| 0x1FAB4 | KE_TEMPTRANSOILHI | word | — | °C | Trans oil temp for 100% fan |
| 0x1FAB6 | KE_TEMPENGINEOILHI | word | — | °C | Engine oil temp for 100% fan |
| 0x1FAB8 | KE_VEHICLESPDFANADJUSTLO | word | — | kPH | VSS below which no speed adjustment |
| 0x1FABA | KE_VEHICLESPDFANADJUSTHI | word | — | kPH | VSS above which no speed adjustment |
| 0x1FABC | KE_WATER_PUMP_PULLEY_RATIO | word | — | 0-16 | Accessory drive pulley ratio |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFAD23 | byte | sub_2E726+1C | Engine operating state |
| FFFFAD1E | long | sub_2E726+26 | Engine run time (min run time check) |
| FFFF9DA5 | byte | sub_2E726+3A | AC compressor on flag |
| FFFF9DA2 | byte | sub_2E726+7C | Fan disable flag (sensor fault) |
| FFFFAD8B | byte | sub_2E726+8C | AC clutch status (bit 5) and AC request (bit 7) |
| FFFFAEBC | word | sub_2E726+98 | Vehicle speed reference |
| FFFFADB0 | word | sub_2E726+9E | Coolant temperature (ECT) |
| FFFF9DBA | word | sub_2E726+A6 | Fan minimum off timer baseline |
| FFFFAD8E | word | sub_2E726+B6 | AC pressure value |
| FFFFAD8C | byte | sub_2E726+BA | AC state byte (bit 7) |
| FFFF88DC | byte | sub_2E726+6A | Sensor fault flag (bit 1) |
| FFFF88DA | byte | sub_2E726+72 | Sensor fault flag (bit 1) |
| FFFF8A46 | byte | sub_2E726+76 | Sensor fault flag (bit 1) |
| FFFFB544 | word | sub_2E726+AA | System timer |

---

## 6. Algorithm Detail

### 6.1 Main Control: sub_2E726

Called from DoLoopE+1C4 each control cycle.

```
1. Check fan system type (KE_TYPE_OF_FANS_ON_VEHICLE):
   - Type 2 or 3: simplified relay-based control → skip complex logic
   - Other types: PWM variable-speed with full feature set

2. Check engine state:
   - If state == 4: skip fan control (cranking?)
   - Engine must have run for KE_ENGINE_RUNNING_FAN1_TIME

3. Sensor fault check:
   - Check bit 1 of FFFF88DC, FFFF88DA, FFFF8A46
   - Any set → use KE_FANCOMMAND_FOR_CTS_FAULT (fixed speed)
   - Set FFFF9DA2 fault flag

4. Determine fan demand — take MAXIMUM of:
   a. ECT demand: KV_ECT_PCT_FANREQ[ECT]
   b. AC pressure demand: KV_AC_PCT_FANREQ[AC_PSI]
      (only when AC active: FFFFAD8B bit 5 set, bit 7 clear)
   c. Trans oil temp demand: KV_TRANS_TEMP_PCT_FANREQ
   d. Engine oil temp demand: KV_ENG_OIL_TEMP_PCT_FANREQ
      If oil temp > KE_TEMPENGINEOILHI → 100% fan

5. WOT reduction:
   If TPS > KE_WOT_FANSPEEDLIMIT AND ECT < KE_WOT_COOLANTTEMP:
   - Reduce fan to KE_WOT_PCT_FAN
   - Timeout: KE_WOT_MAXDISABLE
   - Reduces parasitic load for maximum engine output

6. Vehicle speed adjustment:
   Between KE_VEHICLESPDFANADJUSTLO and HI → interpolate fan
   Outside range → no speed-based adjustment

7. Actuator control (relay-based, Types 2/3):
   Fan1 on: ECT > KE_ECT_FAN1_HIGH OR AC_PSI > KE_AC_PRESSURE_FAN1_HIGH
   Fan1 off: ECT < KE_ECT_FAN1_LOW AND AC_PSI < KE_AC_PRESSURE_FAN1_LOW
   Fan2 on: ECT > KE_ECT_FAN2_HIGH OR AC_PSI > KE_AC_PRESSURE_FAN2_HIGH
   Fan2 off: ECT < KE_ECT_FAN2_LOW AND AC_PSI < KE_AC_PRESSURE_FAN2_LOW

   Timing constraints:
   - Fan1 off→on: delayed KE_FAN1_TURN_ON_DELAY
   - Fan1 on→off: delayed KE_FAN1_TURN_OFF_DELAY
   - Fan1 minimum on: KE_MINIMUM_FAN1_ON_TIME
   - Fan1 minimum off: KE_MINIMUM_FAN1_OFF_TIME
   - Fan2 only after Fan1 on for KE_FAN2_ON_DELAY_TIME
   - Fan1 stays on KE_FAN1_DELAY_OFF_AFTER_FAN2_TUR after Fan2 off

8. PWM actuator control (variable-speed types):
   Apply ramp rate limits:
   - Increasing: KE_FANSPEED_INCR_RATE_LIMIT
   - Decreasing: KE_FANSPEED_DECR_RATE_LIMIT
   - PWM gradient: KE_MAXFANPWMGRADIENTPOS/NEG
   Convert percentage to PWM via KA_PCT_PWM table
   Apply speed feedback correction via KA_DELTA table

9. Fan lockup detection (PWM systems):
   If fan speed > KE_FANFAILSPEEDRPM for KE_FANLOCKUPTIME:
   - Fan mechanically locked → disable to prevent damage
   - Only check when engine RPM > KE_MIN_RPM_TO_DETECT_FANLOCKUP

10. After-run control:
    At key-off: if ECT > KE_ECT_FAN1_KEYOFF:
    - Run Fan1 for KE_FAN1_ON_KEYOFF_TIME seconds
    - PCM stays awake to control fan, then enters sleep

11. Power-up delay:
    KE_FANPWRUPDELAY: no fans for this long after engine start
    Allows idle to stabilize first
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoopE | Calls sub_2E726 each cycle |
| AC Control (doc 26) | AC pressure and clutch status feed fan demands |
| Coolant Temperature | Primary fan trigger |
| Transmission Oil Temp | Can demand additional fan speed |
| Engine Oil Temp | Can demand additional fan speed |
| TPS / WOT | Reduces fan load during WOT |
| IAC / Idle | Fan engagement triggers IAC compensation |
| Vehicle Speed | Modifies fan demand (ram air at speed) |
| Service Tool | Can override fan speed for diagnostics |

---

## 8. Gaps & Unresolved

1. **Fan output pins**: The exact PCM pin numbers for Fan1 and Fan2 relay
   control have not been identified from the disassembly.

2. **KE_TYPE_OF_FANS value**: The actual fan type configured on the 2004
   Corvette M6 needs to be read from the binary to determine if it uses
   relay or PWM control.

3. **PWM fan controller interface**: For PWM systems, the communication
   protocol between the PCM and the fan controller module is not documented.

4. **Fan speed sensor**: The input path for the fan speed feedback signal
   (hall effect sensor on fan motor) has not been traced.

5. **After-run logic**: The key-off fan run-on uses a separate timer and
   wake-up mechanism. This path is assumed but not traced from sub_2E726.

---

## 9. How To Verify

```bash
# Verify fan thresholds on Corvette M6
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
# ECT thresholds are in °C (scaled — need conversion factor)
fan1_hi = int.from_bytes(data[0x1FA58:0x1FA5A],'big')
fan2_hi = int.from_bytes(data[0x1FA78:0x1FA7A],'big')
print(f'KE_ECT_FAN1_HIGH @ 0x1FA58: 0x{fan1_hi:04X}')
print(f'KE_ECT_FAN2_HIGH @ 0x1FA78: 0x{fan2_hi:04X}')
# Need to determine scaling factor — likely °C × 256/5 or similar
# Stock values: 0xACD ≈ 108°C, 0xB4D ≈ 113°C suggests °C × 25.6
"
```

---

## 10. Community Knowledge

- **Fan tuning**: Lowering the ECT fan thresholds is common on performance
  builds to keep engine temps lower. 180°F thermostat tunes typically set
  Fan1 ~93°C and Fan2 ~98°C.

- **Fan delete / manual switch**: Some race cars use manual fan switches,
  bypassing PCM control. This requires setting KE_TYPE_OF_FANS to a type
  that doesn't set DTCs for open circuit.

- **Aftermarket fans**: High-current aftermarket fans may exceed the stock
  relay rating. Many tuners install separate relay harnesses triggered by
  the PCM's low-current Fan1/Fan2 outputs.

- **Low-speed fan operation**: In heavy traffic with AC on, Fan1 cycles
  frequently. The KE_MINIMUM_FAN1_OFF_TIME prevents short-cycling that
  could burn out the relay.
