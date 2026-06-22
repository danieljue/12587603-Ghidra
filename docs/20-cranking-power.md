# P59 OS 12587603 — Cranking, Alternator, Oil & Power Management

> Traced from 68k disassembly — 2026-06-22

---

## 1. Cranking / Starter Motor Control

### Functions

| Function | Address | Purpose |
|----------|---------|---------|
| sub_831BA | OS4 | Main starter motor control (called from DoLoopD) |
| sub_8336E | OS4 | Starter inhibit logic |
| sub_833C4 | OS4 | BCM starter request handler |
| sub_833EC | OS4 | Starter relay control |
| sub_8345E | OS4 | Starter RPM threshold check |
| sub_8347E | OS4 | Starter reference pulse counter |

### Starter Enable Types

```
KE_STARTER_ENABLE_TYPE:
  0 = No starter control (PCM doesn't control starter)
  1 = PCM controls starter relay (keyless start or BCM-based)
```

### Crank-to-Run Transition

```
1. Engine cranking detected (RPM > 0, cranking flag set)
2. Count reference pulses from crank sensor
3. When ref pulses >= KV_STARTER_REF_PULSES:
   → Transition to Run mode
4. If RPM >= KV_STARTRUN_RPM immediately:
   → Fast transition (no pulse count needed)
5. Crank VE table (B0102) used during cranking
   → Switches to main VE table after transition
```

### Key Calibrations

| Calibration | Purpose |
|-------------|---------|
| KV_STARTRUN_RPM | RPM threshold for crank→run |
| KE_STARTRUN_PULSES | Reference pulses for transition |
| KV_STARTER_RPM_THRESH | Min RPM to consider "cranking" |
| KE_STARTER_MAX_CRANK_TIME | Max crank before abort |
| KE_LOW_VOLTAGE_CRANK_TIME | Low voltage extended crank |

### RAM Variables

| Address | Description |
|---------|-------------|
| FFFFAE0A | Starter enable flag |
| FFFFAE0D | Starter relay state |
| FFFFAE02 | Starter timer value |
| FFFFAE0F | Low voltage flag |
| FFFFB4A2 | Starter RPM counter |
| FFFFADFC | Engine run timer snapshot |
| FFFFADFE | Crank timeout value |
| FFFFB544 | System timer |

---

## 2. Alternator / Generator Control

### System

The P59 controls the alternator field duty cycle to regulate system voltage. Uses a PWM output to the alternator field winding.

### Calibrations

Key alternator calibrations exist in the `ALTERNATOR` module (from CSV). The PCM adjusts field duty based on:
- System voltage (target ~14.0V)
- Electrical load (fans, fuel pump, lights)
- Engine RPM (minimum RPM for charging)
- Battery temperature estimate

### Relevant RAM

The alternator field duty cycle and voltage target are stored in RAM but the specific addresses need further tracing.

---

## 3. Oil Pressure / Oil Life

### Functions

| Function | Purpose |
|----------|---------|
| sub_7D0BE | Oil temperature calculation |
| sub_7D262 | Oil life calculation |
| sub_7D490 | Oil life indicator control |
| sub_7D508 | Oil change light control |

### Oil Life Algorithm

```
1. Track engine revolutions since last oil change
2. Apply modifiers for:
   - Oil temperature (hotter = faster degradation)
   - Engine load (higher load = faster degradation)
   - Cold starts (more condensation)
3. Oil_life_remaining = f(revolutions, temp_factor, load_factor)
4. When remaining < KE_OIL_LIFE_CHANGE_SOON: "Change Oil Soon" light
5. When remaining < KE_OIL_LIFE_CHANGE_NOW: "Change Oil Now" light
```

### Key Calibrations

| Calibration | Purpose |
|-------------|---------|
| KE_OIL_LIFE_CHANGE_SOON | Oil life % for "change soon" |
| KE_OIL_LIFE_CHANGE_NOW | Oil life % for "change now" |
| KE_EFFECTIVE_REVOLUTION_LIMIT | Revs per oil change unit |

---

## 4. Power Management / Sleep/Wake

The P59 enters low-power sleep mode when:
1. Ignition off
2. No communication activity for ~10 seconds
3. All tasks complete

Wake conditions:
1. Ignition on
2. VPW bus activity (J1850 message received)
3. Class 2 serial wake-up

Sleep entry involves:
- Disabling unused modules
- Entering CPU STOP mode (low-power)
- Watchdog timer keeps running

---

## 5. After-Start Enrichment

### Function

Runs for a calibrated time after crank→run transition. Provides extra fuel to compensate for:
- Cold intake manifold walls (fuel condensation)
- Cold cylinder walls
- Cold start emissions requirements

### Key Calibrations

The `FUEL` module has after-start enrichment tables:
- Decay rate vs coolant temp
- Initial enrichment vs coolant temp
- Duration vs coolant temp

---

## 6. Catalytic Converter Protection (COT)

### Function

If catalyst temperature model exceeds threshold, the PCM enriches the mixture to cool the catalyst. This is separate from normal PE enrichment and takes priority when active.

### Calibrations

| Calibration | Purpose |
|-------------|---------|
| B0701 COT Enable | Enable/disable COT protection |
| B0702 COT Low Temp | COT activation threshold (low) |
| B0703 COT Medium Temp | COT activation threshold (medium) |
| B0704 COT High Temp | COT activation threshold (high) |
| B0705 COT Extreme Temp | COT threshold (extreme) |

---

## 7. Desoot Mode

### Function

GM-specific enrichment mode for reducing carbon deposits. Enriches mixture under specific conditions (high load, certain RPM) to burn off carbon from pistons and valves.

### Calibrations

Found in `FUEL_IO` module: `KE_DESOOT_MAP_THRESH_HYSTERESIS` and related desoot calibrations.
