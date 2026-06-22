# P59 OS 12587603 — Electronic Throttle Control (ETC)

> Traced from 68k disassembly — 2026-06-22

## System Architecture

```
Accelerator Pedal (APP) → Dual Potentiometers → ADC → Pedal Position (%)
                ↓
        KA_PEDAL_AREA_A (0xA90C) — pedal % → desired throttle area %
        KA_PEDAL_AREA_B (0xABA0) — same, but with trailer mode
                ↓
        Desired Throttle Area (driver request)
                ↓
        ┌───────────────────────────────────────┐
        │     Governor Min-Select               │
        │                                       │
        │  Engine Speed Governor (sub_21094)    │ — limits area if RPM too high
        │  Vehicle Speed Governor               │ — limits area if VSS too high
        │  Torque Management                    │ — reduces for traction/abuse
        │  Transmission Torque Reduction        │ — reduces for shift quality
        │                                       │
        │  Final Desired Area = min(all above)  │
        └───────────────────────────────────────┘
                ↓
        Throttle Motor PID Controller
                ↓
        H-Bridge Driver → Throttle Blade Motor
                ↓
        TPS Feedback (dual potentiometers)
```

## Key Calibrations

| Calibration | Address | Type | Purpose |
|-------------|---------|------|---------|
| KA_PEDAL_AREA_A | 0x00A90C | 2D table | Pedal % → throttle area % (normal mode) |
| KA_PEDAL_AREA_B | 0x00ABA0 | 2D table | Same with trailer mode |
| KV_PEDAL_AREA_REDUCED | 0x00A886 | 2D table | Limp/reduced power pedal map |
| KV_PEDAL_HYSTERESIS | 0x00A8C8 | 2D table | Pedal position hysteresis |
| KE_PEDAL_ROTATION_SCALER | 0x00A882 | Scalar | Pedal rotation to load scaler |
| KE_RELAXED_PEDAL_DEADBAND | 0x00A884 | % | Deadband subtracted from pedal |
| KE_PEDAL_TRANSITION_INTERVAL | 0x00A880 | Seconds | Time to transition to reduced perf |

## Engine Speed Governor (sub_21094 at 0x021094)

Called from DoLoopD. Limits throttle area to keep engine RPM below target.

| Calibration | Address | Purpose |
|-------------|---------|---------|
| KV_ENGINE_SPEED_LIMIT | 0x009A82 | Target RPM limit |
| KV_ENG_SPEED_GOV_PROP_GAIN | 0x00A7CE | PID proportional gain |
| KV_ENGINE_SPEED_GOV_INT_GAIN | 0x00A77A | PID integral gain |
| KV_ENG_SPEED_GOV_DERIVATIVE_GAIN | 0x00A7A4 | PID derivative gain |
| KV_ENG_SPEED_GOV_AREA_INITIAL | 0x00A82E | Initial throttle area (per gear) |
| KE_ENG_SPD_GOV_EXIT_HYSTERESIS | 0x00A860 | RPM below target to exit governing |

## Vehicle Speed Governor

Limits vehicle speed via throttle control (not just fuel cut).

| Calibration | Address | Purpose |
|-------------|---------|---------|
| KE_VEHICLE_SPEED_LIMIT | 0x01FED6 | Target speed limit |
| KV_VEH_SPEED_GOV_PROP_GAIN | 0x00A7FE | Proportional gain |
| KV_VEH_SPEED_GOV_INT_GAIN | 0x00A7F8 | Integral gain |
| KE_VEH_SPEED_DERIVATIVE_GAIN | 0x00A866 | Derivative gain |
| KE_VEH_SPEED_GOV_AREA_INITIAL | 0x00A864 | Initial throttle area |

## Throttle Position Limits

Factory-set maximum blade openings (safety limits):

| Calibration | Address | Notes |
|-------------|---------|-------|
| B2702 ETC Max Throttle Position | (in CSV) | Main max limit vs RPM |
| B2706 ETC Max Idle Contribution | (in CSV) | Max idle airflow via ETC |
| B2713 ETC Max Position for Idle | (in CSV) | Max blade angle at idle |
| B2717 Minimum Throttle Blade Position | (in CSV) | Minimum allowed opening |

## Redundant Safety

All critical ETC calibrations have REDUNDANT copies stored at different addresses. If the primary and redundant values disagree, the PCM enters reduced power mode.

## Task Dispatcher

The main scheduler calls ETC functions in sequence:

```
OS1 dispatcher (0x2B800 range):
  DoLoopA → Spark, knock, launch spark
  DoLoopB → Fuel-cut limiter, DFCO
  DoLoopC → Idle control, IAC, ETC idle
  DoLoopD → Transmission, ETC governing
  DoLoopE → Fuel calculation
  DoLoopF → O2 sensors, fuel trim, EVAP
  DoLoopG → Vehicle speed, diagnostics
  ...

Pre-loop calls:
  sub_7C2F0 (0x07C2F0) ← Hardware init
  sub_7C7E8 (0x07C7E8) ← IOC init
  sub_223EA (0x0223EA) ← Mode control
  sub_87270 (0x087270) ← Main task scheduler
  sub_2984E (0x02984E) ← Pre-loop task
  sub_299AC (0x0299AC) ← Pre-loop task
```

## ETC RAM Variables

| Address | Size | Description |
|---------|------|-------------|
| FFFFA594 | byte | ETC mode flags (bit 3: enable, bit 4: mode) |
| FFFFB2BE | byte | ETC status flags (bit 1-2: mode select) |
| FFFFB2C0 | word | ETC timing/counter |
| FFFFB2C6 | word | ETC counter B |
| FFFFB2C8 | word | ETC counter C |
| FFFFB2CA | word | ETC counter D |
| FFFF9024 | byte | ETC state machine |
| FFFF9028 | byte | ETC sub-state |
| FFFF902E | word | ETC timing |
| FFFFB1C4 | word | Current throttle position |
| FFFFB1D2 | word | Desired throttle position |

## How Boost OS Interacts with ETC

Boost OS doesn't modify ETC code directly. However:
- The engine speed governor limits throttle at the RPM limit — relevant for launch control
- The vehicle speed governor is separate from the fuel-cut limiter
- Launch control works via FUEL CUT, not throttle cut (ETC remains unaffected)
- New RPM limits set in fuel-cut calibrations don't affect the ETC governor
