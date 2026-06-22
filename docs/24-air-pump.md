# P59 OS 12587603 — AIR Pump (Secondary Air Injection)

> Traced from 68k disassembly — 2026-06-22
> Secondary air injection pumps fresh air into the exhaust manifold during cold
> start to accelerate catalyst light-off. The system uses a dedicated electric
> air pump and a solenoid valve, with staggered on/off timing.

---

## 1. Overview

The secondary air injection (AIR) system operates during cold engine starts to
reduce hydrocarbon (HC) and carbon monoxide (CO) emissions. By injecting fresh
air into the exhaust stream before the catalytic converter, the system provides
oxygen to complete combustion of unburned fuel in the exhaust. This generates
exothermic reactions that rapidly heat the catalyst to operating temperature.

The P59 controls two outputs:
- **AIR pump relay**: Powers the electric air pump motor
- **AIR solenoid**: Opens/closes the air injection path to the exhaust

The pump and solenoid have staggered timing — the solenoid opens first, then
the pump starts after a delay. On shutdown, the pump stops first, then the
solenoid closes. This prevents pressure spikes and backflow.

**On the 2004 Corvette M6:** KE_AIR_HOT_RESTART_TIME_ON = 0, meaning the hot
restart feature is disabled. The cold start AIR function uses the remaining
calibrations.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_2C6DE | 0x02C6DE | — | Main AIR control — called from DoLoop |
| sub_2C4F4 | 0x02C4F4 | — | AIR enable/disable condition evaluation |
| sub_2C60E | 0x02C60E | — | AIR pump/solenoid timing control |

Supporting references:
- OS1:0002C76E — Hot restart time check
- OS1:loc_2C778 — Total pump time check

---

## 3. Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     AIR PUMP CONTROL FLOW                        │
│                                                                 │
│  DoLoop ──▶ sub_2C6DE (Gate)                                     │
│               │                                                 │
│               ├─ Engine just started? (crank→run transition)     │
│               ├─ Hot restart eligible?                           │
│               │   KE_AIR_HOT_RESTART_TIME_ON > 0                │
│               │                                                  │
│               ▼                                                  │
│             sub_2C4F4 (Enable Conditions)                         │
│               │                                                  │
│               ├─ ECT ≥ KE_AIR_ECT_DISABLE? → DISABLE             │
│               ├─ MAP < KE_AIR_OVERRUN_DISABLE_THRESHOLD?         │
│               │   AND extended overrun time elapsed? → DISABLE   │
│               ├─ RPM > KE_AIR_HIGH_RPM_DISABLE_THRESHOL?         │
│               │   AND high RPM time exceeded? → DISABLE          │
│               ├─ VSS > KE_AIR_HIGH_VSS_DISABLE_THRESHOL? → DISABLE│
│               ├─ MAP > KE_AIR_HIGH_MAP_DISABLE_THRESHOL? → DISABLE│
│               │                                                  │
│               ▼                                                  │
│             sub_2C60E (Timing Control)                            │
│               │                                                  │
│               ├─ Wait KE_AIR_DELAY_AFTER_START seconds           │
│               ├─ Open AIR solenoid                                │
│               ├─ Wait KE_AIR_PUMP_TURN_ON_DELAY seconds           │
│               ├─ Start AIR pump                                   │
│               ├─ Run for calibrated time                          │
│               ├─ Stop AIR pump                                    │
│               ├─ Wait KE_AIR_PUMP_TURN_OFF_DELAY seconds          │
│               └─ Close AIR solenoid                                │
│                                                                  │
│  Outputs:                                                        │
│    AIR Pump Relay  → dedicated output pin                        │
│    AIR Solenoid    → dedicated PWM/solenoid output               │
│                                                                  │
│  Safety: KE_MAX_TOTAL_PUMP_TIME_ON limits total run time per      │
│  ignition cycle. After this, forced off for rest of cycle.       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08924 | KE_AIR_HOT_RESTART_TIME_ON | word | 0 | Seconds | Hot restart AIR run time (0 = disabled on Corvette) |
| 0x08926 | KE_MAX_TOTAL_PUMP_TIME_ON | word | 0x9600 | Seconds | Max total AIR on-time per ignition cycle |
| 0x08928 | KE_AIR_DELAY_AFTER_START | word | 0 | Seconds | Delay after engine start before AIR activates |
| 0x0892A | KE_AIR_ECT_DISABLE | word | 0xFF00 | °C | Disable AIR if coolant temp below this |
| 0x0892C | KE_AIR_OVERRUN_DISABLE_THRESHOLD | word | 0x400 | kPa | Disable AIR if MAP drops below this (decel) |
| 0x0892E | KE_AIR_EXTENDED_OVERRUN_TIME | word | 0xA0 | Seconds | Time to keep AIR disabled after overrun |
| 0x08930 | KE_AIR_HIGH_RPM_DISABLE_THRESHOL | word | 0x3880 | RPM | Disable AIR above this RPM for KE_AIR_HIGH_RPM_TIME |
| 0x08932 | KE_AIR_HIGH_RPM_TIME | word | 0x320 | Seconds | Time before AIR re-enables after high RPM |
| 0x08934 | KE_AIR_HIGH_VSS_DISABLE_THRESHOL | word | 0x1E00 | MPH | Disable AIR above this VSS |
| 0x08936 | KE_AIR_HIGH_MAP_DISABLE_THRESHOL | word | 0x1333 | kPa | Disable AIR above this MAP (high load) |
| 0x08938 | KE_AIR_PUMP_TURN_ON_DELAY | word | 0x10 | Seconds | Delay between solenoid open and pump start |
| 0x0893A | KE_AIR_PUMP_TURN_OFF_DELAY | word | 0x10 | Seconds | Delay between pump stop and solenoid close |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFA6XX | word | sub_2C6DE/2C4F4/2C60E | AIR pump state variable region |
| FFFFB544 | word | — | System timer (used for run time tracking) |

> **Note:** Exact RAM addresses for AIR pump state, solenoid state, run timer,
> and total timer need detailed tracing of sub_2C6DE, sub_2C4F4, and sub_2C60E.

---

## 6. Algorithm Detail

### 6.1 Main Control: sub_2C6DE

```
1. Engine start detection: transition from crank to run
2. Check hot restart eligibility:
   - If KE_AIR_HOT_RESTART_TIME_ON > 0 AND hot restart conditions:
     - Use hot restart timer
   - Else: use cold start AIR

3. Check total time limit:
   - If accumulated AIR on-time > KE_MAX_TOTAL_PUMP_TIME_ON:
     - Disable AIR for rest of ignition cycle
     - Prevents pump overheating and excessive battery drain

4. Call sub_2C4F4 to evaluate enable conditions
5. If enabled, call sub_2C60E for timing control
```

### 6.2 Enable Conditions: sub_2C4F4

```
AIR is enabled only when ALL conditions are met:

1. ECT check:
   - Coolant temperature > KE_AIR_ECT_DISABLE
   - If colder: AIR disabled (engine too cold, condensation risk)

2. Overrun (decel) check:
   - MAP > KE_AIR_OVERRUN_DISABLE_THRESHOLD
   - If MAP drops below: AIR disabled
   - Remains disabled for KE_AIR_EXTENDED_OVERRUN_TIME after overrun ends

3. High RPM check:
   - RPM ≤ KE_AIR_HIGH_RPM_DISABLE_THRESHOL
   - If RPM exceeds: AIR disabled
   - Remains disabled for KE_AIR_HIGH_RPM_TIME after falling back below

4. High VSS check:
   - VSS ≤ KE_AIR_HIGH_VSS_DISABLE_THRESHOL
   - If speed exceeds: AIR disabled (not needed — cat already hot)

5. High MAP check:
   - MAP ≤ KE_AIR_HIGH_MAP_DISABLE_THRESHOL
   - If load exceeds: AIR disabled (exhaust too hot)

All conditions use hysteresis — once disabled for a reason, that reason
must be cleared before AIR can re-enable.
```

### 6.3 Pump/Solenoid Timing: sub_2C60E

```
The pump and solenoid are controlled with staggered timing:

Start Sequence:
1. Wait KE_AIR_DELAY_AFTER_START seconds from engine start
2. Energize AIR solenoid (opens air path to exhaust)
3. Wait KE_AIR_PUMP_TURN_ON_DELAY seconds
4. Energize AIR pump relay (starts pump motor)

Stop Sequence:
1. De-energize AIR pump relay (stops pump motor)
2. Wait KE_AIR_PUMP_TURN_OFF_DELAY seconds
3. De-energize AIR solenoid (closes air path)

The staggered timing prevents:
- Start: backflow of exhaust gas into the pump before solenoid opens
- Stop: pressure spike from pump running against closed solenoid
```

### 6.4 Diagnostic (DG_AIR / DI_AIR)

The AIR system has a comprehensive diagnostic with two test phases:

**Passive Test (Part 1):**
- Runs during normal AIR operation
- Monitors O2 sensor response to injected air
- Cold start: uses KV_AIRD_PASV_COLD thresholds
- Hot start: uses KV_AIRD_PASV_HOT thresholds
- Measures lean/rich O2 ratio and response time

**Active Test (Part 2):**
- Intrusive — takes control of AIR system for testing
- Commands AIR solenoid to specific position
- Monitors fuel trim response via O2 sensor
- Uses KA_AIRD_ACTIVE_FUEL_TRIM_DELTA for pass/fail
- Limited by engine airflow, load, speed, vehicle speed thresholds

**Enable conditions for diagnostic:**
- Engine run time ≥ KE_AIRD_ENGINE_RUN_TIME_MIN
- Coolant within window (KE_AIRD_COOLANT_TEMP_MIN/MAX)
- IAT within window (KE_AIRD_INTAKE_AIR_TEMP_MIN/MAX)
- Airflow ≥ KE_AIRD_AIRFLOW_MIN
- Baro ≥ KE_AIRD_BARO_MIN
- System voltage ≥ KE_AIRD_SYSTEM_VOLTAGE_MIN
- Engine load ≥ KE_AIRD_ENGINE_LOAD_MIN

**Failure:** KE_AIRD_FAILED_TEST_MAX consecutive failures → DTC set

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoop | Calls sub_2C6DE each engine control cycle |
| O2 Sensors | Diagnosed via O2 response to AIR injection |
| Fuel Trim | Active test monitors short-term fuel trim response |
| Coolant Temperature | Enables/disables based on ECT |
| VSS, MAP, RPM | Disable conditions under high load/speed/RPM |

---

## 8. Gaps & Unresolved

1. **Exact RAM addresses for AIR state machine**: The specific RAM variables
   tracking pump state, solenoid state, run timers, and cumulative time need
   detailed tracing of sub_2C6DE.

2. **AIR pump and solenoid output pins**: The specific PCM pin numbers and
   hardware output registers driving the pump relay and solenoid have not
   been identified from the disassembly.

3. **Hot restart logic**: The hot restart detection uses oil temperature and
   soak time modeling. The exact subroutine path for hot restart enablement
   is separate from sub_2C6DE and not traced.

4. **DG_AIR passive/active test subroutines**: The 50+ diagnostic calibrations
   have not been individually traced to specific subroutines. The diagnostic
   state machine for AIR testing is in the DG_AIR module area (~0x1653C).

---

## 9. How To Verify

```bash
# Verify AIR pump calibrations on Corvette M6 stock bin
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_AIR_HOT_RESTART_TIME_ON @ 0x08924: {int.from_bytes(data[0x08924:0x08926],\"big\"):04X} (0=hot restart disabled)')
print(f'KE_MAX_TOTAL_PUMP_TIME_ON @ 0x08926: {int.from_bytes(data[0x08926:0x08928],\"big\"):04X}')
print(f'KE_AIR_ECT_DISABLE @ 0x0892A: {int.from_bytes(data[0x0892A:0x0892C],\"big\"):04X} (0xFF00 = disabled above ~-0.8°C)')
print(f'KE_AIR_HIGH_RPM_DISABLE_THRESHOL @ 0x08930: {int.from_bytes(data[0x08930:0x08932],\"big\")/5.12:.0f} RPM')
"
```

---

## 10. Community Knowledge

- **AIR delete**: Common on headers/cam installs and race cars. The pump,
  solenoid, and plumbing are physically removed. Requires disabling DTCs
  P0410-P0418 and P041C. Unlike EGR, AIR delete does NOT require calibration
  changes beyond DTC suppression — if the pump relay and solenoid are
  disconnected, the PCM just detects an open circuit and sets DTCs.

- **AIR block-off plates**: Available aftermarket for sealing the AIR
  injection ports on exhaust manifolds/headers when the system is removed.

- **Forced induction applications**: AIR should be retained and functional
  for emissions compliance. On turbo applications, the check valves in the
  AIR plumbing prevent boost pressure from entering the pump.

- **Corvette M6 specifics**: The 2004 Corvette came with AIR from the factory.
  Many owners delete it for weight savings (~5 lbs) and engine bay cleanup.
  Stock tune has hot restart disabled (0 seconds) — only cold start AIR
  operates.
