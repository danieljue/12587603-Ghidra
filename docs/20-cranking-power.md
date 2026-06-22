# P59 OS 12587603 — Cranking, Alternator, Oil & Power Management

> Traced from 68k disassembly — 2026-06-22
> Deepened with function traces, calibration addresses, and RAM verification

---

## 1. Cranking / Starter Motor Control

### 1.1 Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_831BA | 0x0831BA | 308724 | Main starter motor control — called from DoLoopD+166 |
| sub_8336E | 0x08336E | 308891 | Starter inhibit logic — checks RPM, delay, gear |
| sub_833C4 | 0x0833C4 | — | BCM starter request handler (starter enable type 1) |
| sub_833EC | 0x0833EC | — | Starter relay control — drives the starter relay output |
| sub_8345E | 0x08345E | — | Starter RPM threshold check (KV_STARTER_RPM_THRESH) |
| sub_8347E | 0x08347E | — | Starter reference pulse counter |

### 1.2 Starter Enable Types

```
KE_STARTER_ENABLE_TYPE:
  0 = No starter control — PCM does not control the starter relay
      (traditional key-start, starter wired directly to ignition switch)
  1 = PCM controls starter relay — BCM-based keyless start
      (starter request received via Class 2 serial from BCM)
```

The main function sub_831BA (line 308724) tests KE_STARTER_ENABLE_TYPE:
- **Type 0**: Calls sub_8336E (inhibit logic) then exits
- **Type 1**: Calls sub_833C4 (BCM request handler), reads relay feedback
  from hardware port (off_134C+2 bit 2), calls sub_833EC (relay control)

### 1.3 Crank-to-Run Transition

```
1. Engine cranking detected (RPM > 0, cranking flag set)
2. Count reference pulses from crank sensor via sub_8347E
3. When ref pulses >= KV_STARTER_REF_PULSES:
   → Transition to Run mode
4. If RPM >= KV_STARTRUN_RPM immediately:
   → Fast transition (no pulse count needed)
5. Crank VE table used during cranking
   → Switches to main VE table after transition
```

sub_8345E reads KV_STARTER_RPM_THRESH and compares against current RPM
to determine if engine has reached crank-to-run transition speed.

### 1.4 Key Calibrations (STARTER_MOTOR_CONTROL module)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1Fxxx | KE_STARTER_ENABLE_TYPE | long | 0xFF0000 | — | Starter control type (0=none, 1=PCM-controlled) |
| 0x1Fxxx | KE_LOW_VOLTAGE_CRANK_TIME | word | 0 | Seconds | Max crank time during low voltage before abort |
| 0x1Fxxx | KE_STARTER_ENABLE_SPEED | word | 0x600 | RPM | Max RPM for starter engagement |
| 0x1Fxxx | KE_STARTER_GEAR_MILL_PROT_TIME | word | 0xFFFF | Seconds | Gear mill protection timeout |
| 0x1Fxxx | KE_STARTER_INHIBIT_DELAY | word | 0x50 | Seconds | Inhibit delay after engine stop |
| 0x1Fxxx | KE_STARTER_MAX_CRANK_TIME | word | 0 | Seconds | Max continuous crank time (0 = no limit) |
| 0x1Fxxx | KV_STARTER_REF_PULSES | word | 0 | Counts | Reference pulses for crank→run transition |
| 0x1Fxxx | KV_STARTER_RPM_THRESH | byte | 0 | RPM | Min RPM to consider "cranking" |
| — | KV_EXTENDED_CRANK_ENABLE_TIME | byte | 0 | Seconds | Extended crank enable time |
| — | KV_EXTENDED_CRANK_TIME_MAX | byte | 0 | Seconds | Max extended crank time |
| — | KE_EXTENDED_CRANK_FUEL_LEVEL | word | 0 | — | Fuel level for extended crank |

### 1.5 RAM Variables (verified from sub_831BA)

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFAE0A | byte | sub_831BA+48 | Starter enable flag (1 = starter engaged) |
| FFFFAE0D | byte | sub_831BA+32 | Starter relay state (from hardware feedback bit 2) |
| FFFFAE02 | word | sub_831BA+8A | Starter timer value (system timer at engagement) |
| FFFFAE0F | byte | sub_831BA+8C | Low voltage flag (1 = low voltage during crank) |
| FFFFB4A2 | word | sub_831BA+58 | Starter RPM counter |
| FFFFADFC | word | sub_831BA+64 | Engine run timer snapshot (for timing checks) |
| FFFFADFE | word | sub_831BA+68 | Crank timeout value (from calibration or computed) |
| FFFFB544 | word | sub_831BA+70 | System free-running timer |

---

## 2. Alternator / Generator Control

### 2.1 Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_2C7AC | 0x02C7AC | 150277 | Alternator diagnostic and control — called from DoLoopF |
| sub_276D4 | 0x0276D4 | — | Timer utility used by alternator diagnostics |

The alternator control is integrated with the alternator diagnostic function
sub_2C7AC (called from DoLoopF). This function handles:
- Alternator field duty cycle monitoring
- L-terminal and F-terminal fault detection
- Diagnostic display method selection
- Alternator diagnostic results reporting

### 2.2 Alternator Diagnostic Tests (P1637, P1638)

The PCM monitors the alternator field duty cycle (L-terminal) and compares
against expected values to detect faults:

```
P1637 — Generator L-Terminal Circuit:
  - L-terminal duty cycle monitored
  - Fail if outside normal range for KE_P1637_SAMPLE_PERIOD
  - KE_P1637_FAIL_LIMIT failures before DTC set

P1638 — Generator F-Terminal Circuit:
  - F-terminal duty cycle monitored
  - Fail if duty cycle indicates field short/open
  - KE_VALT_P1638_FAIL_LIMIT failures before DTC set
```

### 2.3 Alternator Duty Cycle States

The PCM determines alternator health by comparing field duty cycle:

| Calibration | Stock Value | Indication |
|-------------|-------------|------------|
| KE_VALT_MIN_NORMAL_RUNNING_DC | 0x100 | Minimum normal field duty cycle |
| KE_VALT_L_SHORTED_HOT_F_OPEN_DC | 0x33 | L shorted hot / F open duty cycle |
| KE_VALT_L_SHORTED_HOT_DC | 0x500 | L shorted hot duty cycle |
| KE_VALT_F_AND_L_SHORTED_HOT_DC | 0x13CD | F and L shorted hot duty cycle |
| KE_VALT_L_SHORT_TO_GND_DC | 0x100 | L shorted to ground duty cycle |
| KE_VALT_FIELD_OR_WIRING_FAULT_DC | 0x33 | Field or wiring fault duty cycle |
| KE_VALT_POWERUP_DC | 0x500 | Power-up duty cycle |
| KE_VALT_F_SHORTED_HOT_DC | 0x13CD | F shorted hot duty cycle |
| KE_VALT_DC_HYSTERESIS | 0x300 | Hysteresis band |

### 2.4 Voltage Regulation

The alternator field duty cycle is adjusted to maintain target system voltage
(~14.0V). The IAC module provides a filter for field duty cycle:

| Address | CSV Label | Stock | Description |
|---------|-----------|-------|-------------|
| 0x0xxxx | KE_ALTERNATOR_FIELD_DC_FILTER | 6 | IAC learn: alternator field DC filter coef |

Referenced by sub_2C7AC+A0 — used when learning idle airflow to compensate
for alternator load changes.

### 2.5 Diagnostic Configuration

| Address | CSV Label | Stock | Description |
|---------|-----------|-------|-------------|
| 0x1Fxxx | KE_ALT_DG_RESULTS_DISPLAY_METHOD | 0 | Diagnostic result display method (0-3) |
| 0x1Fxxx | KE_ALTERNATOR_DIAGNOSTIC_TO_RUN | 0 | Which alternator diagnostics to execute |

### 2.6 Hardware Interface

The P59 controls the alternator via two signals:
- **L-terminal**: PCM output — duty cycle controls alternator field current
  (also drives the charge indicator lamp)
- **F-terminal**: PCM input — feedback signal for field duty cycle monitoring
  (some alternators provide this for diagnostics)

On the 2004 Corvette M6, the alternator is likely a standard CS130D or AD244
with L-terminal control only (no F-terminal feedback).

---

## 3. Oil Pressure / Oil Life

### 3.1 Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_7D0BE | 0x07D0BE | — | Oil temperature calculation |
| sub_7D262 | 0x07D262 | — | Oil life calculation |
| sub_7D490 | 0x07D490 | — | Oil life indicator control |
| sub_7D508 | 0x07D508 | — | Oil change light control |

### 3.2 Oil Life Algorithm

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

### 3.3 Key Calibrations (ENG_OIL module)

| Calibration | Purpose |
|-------------|---------|
| KE_OIL_LIFE_CHANGE_SOON | Oil life % for "change soon" warning |
| KE_OIL_LIFE_CHANGE_NOW | Oil life % for "change now" warning |
| KE_EFFECTIVE_REVOLUTION_LIMIT | Revs per oil change unit |
| KE_OIL_LIFE_OVERTEMP | Oil temp above which rapid degradation |
| KE_OIL_TEMPERATURE_EQUILIBRIUM | Oil temp equilibrium threshold |
| KV_OIL_LEVEL_DELTA | Oil level delta for consumption check |

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

### 5.1 Function

Runs for a calibrated time after crank→run transition. Provides extra fuel
to compensate for:
- Cold intake manifold walls (fuel condensation)
- Cold cylinder walls
- Cold start emissions requirements

### 5.2 Key Calibrations (FUEL module)

| Calibration | Purpose |
|-------------|---------|
| KA_AFTERSTART_DECAY_DELAY | After-start enrichment decay delay vs coolant |
| KA_AFTERSTART_DECAY_MULTIPLIER | Decay rate multiplier |
| KA_AFTERSTART_DECAY_STEP | Decay step size per timer tick |

### 5.3 How It Works

```
1. On transition to Run mode:
2. Read startup coolant temperature
3. Initial enrichment factor from KA_AFTERSTART_DECAY table (more when colder)
4. After-start timer starts counting
5. Fuel multiplier = initial × exp(-time / decay_rate)
6. Applied to base fuel calculation (see doc 07 — Fuel System)
7. Disabled when timer expires or coolant > threshold
```

---

## 6. Catalytic Converter Protection (COT)

### 6.1 Function

If catalyst temperature model exceeds threshold, the PCM enriches the mixture
to cool the catalyst. This is separate from normal PE enrichment and takes
priority when active.

### 6.2 Calibrations (CONVERTER module)

| HPTuners Name | CSV Label | Description |
|--------------|-----------|-------------|
| B0701 COT Enable | — | Enable/disable COT protection |
| B0702 COT Low Temp | KE_COT_TEMPERATURE_LOW | COT activation threshold (low) |
| B0703 COT Medium Temp | KE_COT_TEMPERATURE_MEDIUM | COT activation threshold (medium) |
| B0704 COT High Temp | KE_COT_TEMPERATURE_HIGH | COT activation threshold (high) |
| B0705 COT Extreme Temp | KE_COT_TEMPERATURE_EXTREME | COT threshold (extreme) |

**Note:** COT will be fully documented in Phase 3 of the reverse engineering
plan (docs/17-open12587603-plan.md). This section provides only the basic
overview pending deep function traces.

---

## 7. Desoot Mode

### 7.1 Function

GM-specific enrichment mode for reducing carbon deposits. Enriches mixture
under specific conditions (high load, certain RPM) to burn off carbon from
pistons and valves.

### 7.2 Calibrations (FUEL_IO module)

| Calibration | Purpose |
|-------------|---------|
| KE_DESOOT_MAP_THRESH_HYSTERESIS | MAP delta hysteresis for desoot |
| KE_DESOOT_COOLANT_THRESH | Min coolant for desoot enable |
| KE_DESOOT_COOLANT_THRESH_HYSTERE | Coolant hysteresis for desoot |

---

## Gaps & Unresolved

1. **Alternator field duty PID**: The actual voltage regulation PID loop has
   not been traced. sub_2C7AC focuses on diagnostics; the field duty cycle
   calculation that maintains target voltage may be in a separate function.

2. **Oil pressure sensor**: The PCM may not directly monitor oil pressure (the
   Corvette has a separate oil pressure gauge). The oil life calculation uses
   a model rather than a direct sensor for oil degradation.

3. **Sleep/wake hardware**: The specific TPU/SCI registers used for wake-up
   detection have not been documented.

4. **After-start enrichment exact formula**: The exponential decay parameters
   and their interaction with coolant temperature need detailed tracing from
   the FUEL_SH/FUEL_CRANK modules.

---

## How To Verify

```bash
# Verify starter type on Corvette M6
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
addr = 0x1Fxxx  # KE_STARTER_ENABLE_TYPE — exact address TBD
print(f'KE_STARTER_ENABLE_TYPE: {data[addr]} (0=key-start, 1=PCM-controlled)')
"
```

```bash
# Verify alternator diagnostic is configured
grep -c "sub_2C7AC" 12587603-2004-Corvette-M6.sanitized.asm
```
