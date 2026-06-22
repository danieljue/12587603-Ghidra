# P59 OS 12587603 — Cruise Control

> Traced from 68k disassembly — 2026-06-22
> Electronic throttle cruise control integrated with the ETC system. Uses
> vehicle speed PID control to maintain set speed, with resume, accel, coast,
> and tap-up/down functions.

---

## 1. Overview

The P59 implements cruise control through the electronic throttle control
(ETC) system — no separate cruise actuator is needed. The PCM adjusts the
throttle blade directly to maintain vehicle speed. Cruise commands (Set,
Resume, Accel, Coast, Cancel) are received from the cruise control switches
via Class 2 serial data from the BCM or steering wheel controls.

The cruise control uses a PID speed governor with:
- Proportional gain based on speed error
- Integral term with windup limits
- Vehicle acceleration filtering
- Scheduled accel/coast gain for smooth transitions
- TCC lockup control integration

**On the 2004 Corvette M6:** Cruise is standard. Manual transmission cruise
adds clutch and gear-dependent logic not present on automatic applications.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_76516 | 0x076516 | 285436 | Main cruise control — called from DoLoopF+308 |
| sub_76844 | 0x076844 | — | Cruise speed error and effective speed calculation |

---

## 3. Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     CRUISE CONTROL SYSTEM                        │
│                                                                  │
│  Cruise Switches (Class 2 serial)                                │
│    │                                                             │
│    ├─ Set/Coast switch                                           │
│    ├─ Resume/Accel switch                                        │
│    ├─ Cancel (brake, clutch, P/N, TCS event)                     │
│    ├─ Tap-Up (brief Resume press)                                │
│    └─ Tap-Down (brief Set press)                                 │
│                                                                  │
│  DoLoopF ──▶ sub_76516                                           │
│    │                                                             │
│    ├─ State Machine:                                              │
│    │   OFF → no cruise activity                                  │
│    │   STANDBY → cruise enabled, waiting for Set                 │
│    │   ACTIVE → maintaining set speed                            │
│    │   RESUME → accelerating to previous set speed               │
│    │   ACCEL → driver holding Resume/Accel (increasing speed)    │
│    │   COAST → driver holding Set/Coast (decreasing speed)       │
│    │                                                             │
│    ├─ Speed Error Calculation:                                    │
│    │   Error = Set_Speed - Actual_Speed (FFFFAEBC)               │
│    │   Filtered through KE_CRUISE_VEH_ACCEL_FILTER               │
│    │   Clamped to ±KE_CRUISE_EFF_SPD_ERROR_MAX                   │
│    │                                                             │
│    ├─ PID Speed Governor:                                         │
│    │   P: proportional to speed error                            │
│    │   I: integral of speed error                                │
│    │     Limited: [KE_CRUISE_INTEGRATOR_LOW, HIGH]               │
│    │     Gain: KE_CRUISE_INTEGRATOR_GAIN                         │
│    │     Suspended during Resume/Accel modes                     │
│    │   D: vehicle acceleration feedback                          │
│    │                                                             │
│    ├─ Scheduled Accel/Coast:                                      │
│    │   Resume mode: apply KE_SCHEDULED_ACCEL_GAIN_OVER           │
│    │   Coast mode: apply KE_SCHEDULED_ACCEL_GAIN_UNDER           │
│    │   Provides smooth throttle transitions                      │
│    │                                                             │
│    ├─ TCC Lockup Integration:                                     │
│    │   Lockup integrator for torque converter clutch              │
│    │   Filtered: KE_LOCKUP_INT_FILTER                            │
│    │   Clamped: [KE_LOCKUP_CLAMP_LOW, HIGH]                      │
│    │   Power limit: KE_LOCKUP_POWER_LIMIT (disable above)        │
│    │                                                             │
│    ├─ Gear Compensation:                                          │
│    │   KV_CRUISE_GEAR_COMP_GAIN per gear                         │
│    │   Adjusts integrator multiplier for different gear ratios   │
│    │                                                             │
│    └─ Output: Desired throttle position → ETC pedal progression  │
│              Throttle command blended with driver pedal input     │
│                                                                  │
│  Disengage Conditions:                                           │
│    • Brake switch active                                         │
│    • Clutch switch active (manual trans)                         │
│    • P/N position (auto trans)                                   │
│    • Traction control event                                      │
│    • Vehicle speed < minimum (~25 mph)                           │
│    • Engine speed > maximum                                      │
│    • Cruise cancel switch pressed                                │
│    • System fault detected                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Core Cruise (CRUIS_CONTROL module, 0x92A8-0x935C)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x092A8 | KE_CRUISE_INTEGRATOR_HIGH | word | 0x400 | MPH | Integrator max clamp |
| 0x092AA | KE_CRUISE_INTEGRATOR_LOW | word | 0xFC00 | MPH | Integrator min clamp (negative) |
| 0x092B0 | KE_CRUISE_INTEGRATOR_GAIN | word | 0x266 | 0-1 | Integrator gain (non-Resume/Accel modes) |
| 0x092B4 | KE_SCHEDULED_ACCEL_GAIN_OVER | word | 0xE | — | Accel gain when speed is over target |
| 0x092B6 | KE_SCHEDULED_ACCEL_GAIN_UNDER | word | 0xE | — | Accel gain when speed is under target |
| 0x092B6 | KE_LOCKUP_CLAMP_HIGH | word | 0x80 | MPH | Lockup integrator high clamp |
| 0x092B8 | KE_LOCKUP_CLAMP_LOW | word | 0xFF80 | MPH | Lockup integrator low clamp |
| 0x092BA | KE_LOCKUP_INT_FILTER | word | 0x1994 | Seconds | Lockup integrator filter coefficient |
| 0x092BC | KE_LOCKUP_POWER_LIMIT | word | 0xB9A | Percent | Power above which lockup suspended |
| 0x092BE | KE_CRUISE_VEH_SPEED_DELTA_HIGH | word | 0x13 | MPH/100ms | Positive acceleration limit |
| 0x092C0 | KE_CRUISE_VEH_SPEED_DELTA_LOW | word | 0xFFED | MPH/100ms | Negative acceleration limit |
| 0x093C4 | KE_CRUISE_VEH_ACCEL_FILTER | word | 0x1AEC | — | Vehicle acceleration filter coefficient |
| 0x0935C | KV_CRUISE_GEAR_COMP_GAIN | byte | 0x38 | Scaler | Gear compensation integrator multiplier |

### 4.2 Cruise Speed Error (0x93C6 area)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x09xxx | KE_CRUISE_EFF_SPD_ERROR_MAX | word | 0x500 | — | Max effective speed error clamp |

### 4.3 Cruise Module (CRUISE, 0x810F)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0810F | KE_PERFORM_CRUISE_SEQUENCING | byte | — | BOOLEAN | Enable cruise sequencing logic |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFAEBC | word | sub_7BC70 (COT) | Vehicle speed (used as cruise feedback) |
| FFFFAB66 | word | sub_7BC70 (COT) | Throttle position (pedal + cruise command) |

> **Note:** Cruise-specific RAM (set speed, integrator value, state machine
> state, switch states) requires detailed tracing of sub_76516.

---

## 6. Algorithm Detail

### 6.1 Main Control: sub_76516

Called from DoLoopF+308 each 100ms cycle.

```
1. Read cruise switch states from Class 2 serial data
2. State machine transition evaluation:
   - Any cancel condition → OFF
   - OFF + Set pressed at speed > min → ACTIVE (capture set speed)
   - STANDBY + Resume pressed → RESUME (accelerate to last set speed)
   - ACTIVE + Accel held → ACCEL (increase set speed)
   - ACTIVE + Coast held → COAST (decrease set speed)
   - ACTIVE + Tap-Up → increment set speed by ~1 mph
   - ACTIVE + Tap-Down → decrement set speed by ~1 mph

3. Speed error calculation:
   error = set_speed - FFFFAEBC (vehicle speed)
   Filter via KE_CRUISE_VEH_ACCEL_FILTER
   Clamp to ±KE_CRUISE_EFF_SPD_ERROR_MAX

4. PID calculation:
   P_term = speed_error (direct proportional)
   I_term = previous_I + speed_error × KE_CRUISE_INTEGRATOR_GAIN
   I_term clamped to [KE_CRUISE_INTEGRATOR_LOW, HIGH]
   D_term from filtered vehicle acceleration

5. Scheduled accel/coast compensation:
   If speed < set_speed:
     throttle_adder = KE_SCHEDULED_ACCEL_GAIN_UNDER × error
   If speed > set_speed:
     throttle_adder = KE_SCHEDULED_ACCEL_GAIN_OVER × error

6. Gear compensation:
   throttle_command ×= KV_CRUISE_GEAR_COMP_GAIN[gear]
   (Higher gain in lower gears for smoother response)

7. Lockup integrator (automatic trans only):
   Separate integrator for TCC lockup control
   Filtered and clamped independently
   Disabled above KE_LOCKUP_POWER_LIMIT

8. Output:
   Final throttle command → ETC pedal progression logic
   Blended with driver pedal position (driver can override)
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoopF | Calls sub_76516 each 100ms |
| ETC Throttle (doc 08) | Cruise throttle commands through ETC blade control |
| Class 2 Serial | Switch states received via VPW messages |
| Brake Switch | Hardware input → immediate cruise cancel |
| Clutch Switch | Hardware input → cruise cancel (M6 only) |
| Traction Control | TCS event → cruise cancel |
| TCC Control | Lockup integrator interacts with torque converter |
| VSS | Vehicle speed feedback for PID |

---

## 8. Gaps & Unresolved

1. **Sub_76516 full trace**: The function body was not read in detail. The
   algorithm described is inferred from calibration names, cross-references,
   and known cruise control architecture.

2. **Class 2 message format**: The specific J1850 VPW message IDs and bit
   positions for cruise switches (Set, Resume, Cancel, etc.) have not been
   decoded from the serial message handler.

3. **Set speed storage**: Where the set speed is stored in RAM and how it
   survives Resume after Cancel need verification.

4. **Tap-Up/Down increment**: The exact mph increment per tap (likely 1 mph)
   and the tap detection debounce timing are not confirmed.

5. **Minimum engagement speed**: The calibration for minimum vehicle speed
   to engage cruise (~25 mph) has not been identified in the CSV.

---

## 9. How To Verify

```bash
# Verify cruise integrator gains
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
ihi = int.from_bytes(data[0x092A8:0x092AA],'big',signed=True)
ilo = int.from_bytes(data[0x092AA:0x092AC],'big',signed=True)
igain = int.from_bytes(data[0x092B0:0x092B2],'big')
print(f'Integrator High: {ihi} (0x{ihi&0xFFFF:04X})')
print(f'Integrator Low: {ilo} (0x{ilo&0xFFFF:04X})')
print(f'Integrator Gain: 0x{igain:04X}')
"
```

---

## 10. Community Knowledge

- **Cruise control delete**: Some race builds remove the cruise control
  switches and disable the feature. Setting KE_PERFORM_CRUISE_SEQUENCING = 0
  disables cruise entirely without DTCs.

- **ETC cruise vs cable throttle**: Because the P59 cruise uses ETC, it's
  smoother and more precise than cable-throttle cruise systems. The PID
  gains can be tuned for different vehicle weight/power configurations.

- **Cruise on engine swaps**: If the BCM is not present (standalone harness),
  cruise switches may not work because they're wired through the BCM. Some
  standalone harnesses provide direct-wired cruise switches that the PCM
  can read as discrete inputs.
