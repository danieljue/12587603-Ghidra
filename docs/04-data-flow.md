# P59 OS 12587603 — Data Flow

> How data flows through the PCM: sensor input → calculation → actuator output

## Overview

The P59 PCM runs a tick-based real-time scheduler. Each "loop" (DoLoopA through DoLoopG) handles a subsystem on a fixed schedule. The main loop dispatcher `sub_AA0` calls each loop in sequence.

```
                    ┌──────────────┐
                    │   Sensors    │
                    │ MAP, MAF,    │
                    │ IAT, ECT,    │
                    │ TPS, VSS, O2 │
                    └──────┬───────┘
                           │ A/D + pulse counting
                           ▼
┌──────────────────────────────────────────────────────┐
│                 Main Loop (sub_AA0)                   │
│                                                      │
│  DoLoopA → Spark calc, knock, launch spark           │
│  DoLoopB → Fuel-cut limiter, DFCO, RPM limits        │
│  DoLoopC → Idle control, IAC, throttle follower      │
│  DoLoopD → Transmission control                      │
│  DoLoopE → Diagnostics, DTCs                         │
│  DoLoopF → O2 sensors, fuel trim, closed loop        │
│  DoLoopG → Vehicle speed, ETC governor               │
│                                                      │
│  Each loop reads RAM variables,                     │
│  computes new values, writes back to RAM             │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 Output Drivers                        │
│                                                      │
│  Spark timing → Ignition coil drivers                │
│  Fuel pulse width → Injector drivers                 │
│  IAC position → Stepper motor driver                 │
│  ETC position → Throttle motor driver                │
│  Fan speed → PWM relay driver                        │
│  Fuel pump → Relay driver                            │
│  Transmission → Solenoid drivers                     │
└──────────────────────────────────────────────────────┘
```

## Key Data Flows

### Spark Calculation Chain
```
DoLoopA:
  1. Read RPM (FFFFA562), MAP (FFFFADB6), IAT, ECT from RAM
  2. sub_39F12: Base spark from KA_MAIN_OT_HIGH_OCTANE (0x10890) or LOW (0x10E3A)
  3. sub_3AF0C: Catalyst lightoff spark retard modifier
  4. sub_3A754: MBT spark modifier
  5. sub_3BDC4: Launch spark and knock energy calculation
  6. Knock detection: modifies spark based on knock sensor
  7. Spark smoothing: limits rate of change
  8. Write final spark advance to ignition output register
```

### Fuel Calculation Chain
```
DoLoopF + related:
  1. sub_79B10: Dynamic Airflow (Dyna-Air) calculation
     - Read MAP, RPM, IAT, ECT
     - VE table lookup: lea (K_MAIN_VOLUMETRIC_EFFICIENCY),a0 → sub_16D6
     - Calculate grams/cylinder of air
  2. Target AFR from B3605 (open loop) or stoichiometric
  3. Injector pulse = (air mass / AFR) / injector flow rate
  4. + injector offset (KV_INJECTOR_OFFSET_ADJUSTMENT)
  5. Fuel trim from O2 sensor closed loop (if active)
  6. Write final pulse width to injector driver
```

### RPM Limiter Chain
```
DoLoopB:
  1. sub_30368: Fuel-Cut RPM Limiter
     - Read current RPM (FFFFA562)
     - Check gear position (FFFFA3AF) → select P/N or in-gear threshold
     - Check cold engine protection (FFFFA93E)
     - Check VSS fail flags (FFFF8998, FFFF899C, FFFF899A bit 1)
     - Compare RPM vs threshold
     - If over: set fuel cut flag (FFFFA93C), clear injector pulses
     - If under: clear fuel cut flag, re-enable injectors
```

### DFCO (Decel Fuel Cut-Off) Chain
```
DoLoopB:
  1. sub_30566: Clutch DFCO Detection
     - Read TPS, MAP, RPM, clutch switch (FFFFA3AB)
     - Detect throttle decrease near clutch press → activate DFCO
  2. sub_3090C: DFCO Entry/Exit
     - Check enabling conditions (coolant temp, RPM, TPS, VSS)
     - Entry: cut fuel on decel
     - Exit: restore fuel on throttle increase or RPM drop
```

## RAM Variable Flow

```
SENSOR INPUTS (updated by hardware interrupts / ADC reads)
  │
  ├── FFFFA562 ← RPM (crank position sensor pulse timing)
  ├── FFFFADB6 ← MAP (manifold absolute pressure sensor ADC)
  ├── FFFFAEC0 ← VSS (vehicle speed sensor pulse frequency)
  ├── FFFF93F1 ← Clutch switch (raw GPIO input)
  ├── FFFFA3AB ← Clutch switch (processed state)
  ├── FFFFA3AF ← Gear position (PRNDL switch)
  └── FFFFAD23 ← Cylinder mode trigger

CALCULATED VALUES (computed by DoLoop functions)
  │
  ├── FFFFA93C ← Fuel cut status (set by sub_30368)
  ├── FFFFA936 ← DFCO active flag (set by sub_30566)
  ├── FFFFA0D6 ← VE lookup result (set by sub_79B10)
  ├── FFFFA0CC ← Calculated air per cylinder
  └── FFFF9D4C ← Knock detection state (set by sub_3BDC4)
```

## Injection Points for Custom Code

| Hook Address | Original Instruction | What It Does | Custom Code Can |
|-------------|---------------------|--------------|-----------------|
| 0x03039E | `move.w (OVERSPEED_LO).l, d3` | Load RPM cut threshold | Override with launch RPM |
| 0x0303F8 | `move.w (OVERSPEED_HI).l, d3` | Load RPM re-enable threshold | Same as above |
| 0x079B92 | `lea (VE_TABLE).l, a0` | Load VE table pointer | Redirect to expanded VE |
| 0x07A176 | `lea (VE_TABLE).l, a0` | Second VE lookup | Same as above |
| 0x07A95E | `lea (VE_TABLE).l, a0` | Third VE lookup | Same as above |

## Free Space for Custom Code

| Region | Address Range | Size | Visibility |
|--------|--------------|------|------------|
| OS5 gap | 0x0A0000–0x0AFFFF | 64 KB | Open space, no checksum |
| OS6 gap | 0x0C0000–0x0CFFFF | 64 KB | Open space |
| OS5-OS6 gap | 0x0B0000–0x0BFFFF | 64 KB | Open space |
| OS7 | 0x0E0000–0x0EFFFF | 64 KB | Open space |
| **Total** | | **256 KB** | |

Custom 68k routines go in the OS5 gap (0x0A0000). Calibration tables go in OS7 (0x0E0000).
Boost OS uses this exact layout.
