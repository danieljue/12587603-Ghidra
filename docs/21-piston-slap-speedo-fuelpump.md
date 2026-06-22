# P59 OS 12587603 — Piston Slap, Speedometer & Fuel Pump

> Traced from 68k disassembly — 2026-06-22

---

## 1. Piston Slap Protection

### Functions

| Function | Address | Purpose |
|----------|---------|---------|
| sub_3A6D0 | +0x3A from FFS spark | Piston slap spark retard |
| sub_3A63E | +0x6A | FFS E80 spark shift |

### How It Works

Cold engines have larger piston-to-wall clearance, causing audible "piston slap." The PCM applies spark retard to reduce combustion pressure during cold operation, reducing noise.

```
1. Read coolant temperature
2. If coolant < threshold: apply piston slap spark retard
3. Retard amount from SPARK_ADVANCE_KA_PISTON_SLAP_SPARK_RETARD table
4. Coolant multiplier from KV_PISTON_SLAP_COOLANT_MULT
5. Final retard = table_value × coolant_multiplier
6. Applied as subtractive modifier to main spark advance
7. Gradually removed as engine warms up
```

### Calibrations

| Calibration | Purpose |
|-------------|---------|
| SPARK_ADVANCE_KA_PISTON_SLAP_SPARK_RETARD | Base retard vs RPM/Load |
| SPARK_ADVANCE_KV_PISTON_SLAP_COOLANT_MULT | Coolant temp multiplier |
| SPARK_ADVANCE_KA_FFS_E80_SPARK_SHIFT | FFS ethanol spark shift |

### Piston Protection (Fuel)

Separate from slap — piston protection enrichment adds fuel to cool pistons:
```
FUEL_EQ_KV_PISTON_PROTECTION_EQUIVALENCE → extra fuel EQ ratio
```
Used under sustained high load to prevent piston overheating/detonation.

---

## 2. Speedometer Signal Output

### Functions

| Function | Address | Purpose |
|----------|---------|---------|
| sub_79A3E | OS3 | VSS output signal generator |

### How It Works

The PCM generates speedometer output pulses from the VSS signal:

```
1. Read VSS raw value (FFFFAEC0)
2. Convert to PPM (Pulses Per Mile):
   Primary output: divide by KE_PRIMARY_OUTPUT_PPM
   Secondary output: divide by KE_SECONDARY_OUTPUT_PPM
3. Output pulses:
   Primary → FFFFFF44/FFFFFF6A (TPU channel outputs)
   Secondary → FFFFFF54/FFFFFF7A
4. These TPU output channels drive the speedometer and any other
   vehicle speed-dependent devices
```

### Calibrations

| Calibration | Stock Value | Purpose |
|-------------|-------------|---------|
| KE_PRIMARY_OUTPUT_PPM | 0x400 (1024) | Primary VSS output (speedo) |
| KE_SECONDARY_OUTPUT_PPM | 0x8000 (32768) | Secondary VSS output (cruise/ABS) |

### Output Pins

The speedometer signal is a 0-5V square wave:
- 4000 pulses per mile (typical GM)
- Frequency proportional to vehicle speed
- Also feeds: cruise control module, radio volume, ABS module

---

## 3. Fuel Pump Control

### Functions

| Function | Address | Purpose |
|----------|---------|---------|
| sub_7F000 | OS3 | Fuel pump relay control |
| sub_7F36C | OS3 | Fuel level / transfer pump |
| sub_265BA | OS2 | Fuel pump timer utility |

### Operation

```
Key-On Prime:
  1. Ignition ON → fuel pump runs for ~2 seconds
  2. If engine doesn't start, pump stops
  3. Pump restarts when cranking detected

Engine Running:
  Pump runs continuously while engine RPM > 0

Speed Density Mode (no MAF):
  Some calibrations enable PWM fuel pump control for:
  - Reduced noise at idle
  - Voltage savings
  - Fuel pressure modulation

Fuel Pump Speed Control:
  KV_FLOW_RATE_PUMP_CORRECTION: injector flow correction
  based on fuel pump voltage (accounts for pressure changes)
```

### Calibrations

The fuel pump prime timer and other calibrations are in the FUEL_IO module.

### Fuel Tank Transfer Pump

Some vehicles (trucks, dual-tank) have a transfer pump between tanks:
- sub_7F36C manages fuel level sensing and transfer
- F_TANK_KE_VSS_XFER_PUMP enables transfer above certain speed

---

## 4. After-Start Enrichment (Detail)

### How It Works

After crank→run transition, extra fuel is injected:

```
1. On transition to Run mode:
2. Read startup coolant temperature
3. Initial enrichment factor from table (more when colder)
4. Decay rate from table (faster decay when warmer)
5. After-start timer starts counting
6. Fuel multiplier = initial × exp(-time / decay_rate)
7. Applied to base fuel calculation
8. Disabled when timer expires or coolant > threshold
```

### Calibrations (from CSV)

Found in the FUEL module:
- B3632 After-start enrichment decay delay table
- B3627 After-start enrichment delay vs coolant
- B3628 After-start enrichment decay rate
- B3633 After-start intake temp enrichment
