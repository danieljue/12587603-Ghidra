# P59 OS 12587603 — OS Infrastructure & Hardware Interface

> Traced from CSV catalog and 68k disassembly — 2026-06-22
> Low-level OS services: memory management, critical sections, sensor
> interfaces, ignition dwell, barometric pressure estimation, and pedal
> progression. These are the hardware-proximate layers below the functional
> subsystems.

---

## 1. MEM_MANAGER — Memory Management

### 1.1 RAM Test

The PCM runs a power-on RAM test to verify memory integrity before executing
code. If RAM cells fail:

```
KE_MAX_RAM_FAIL_CTR_THRESHOLD: max failures before latching permanent fault
KE_IGNORE_RAM_TEST: if TRUE, RAM test results are ignored (development only)
```

A RAM failure sets a hard DTC (P0601 — Internal Control Module Memory Check
Sum Error) and prevents engine start.

### 1.2 ROM / Flash Checksum

The OS computes a cyclic checksum over each flash segment at power-up:

```
KE_MAX_ROM_FAIL_CTR_THRESHOLD: max checksum failures before permanent fault
KE_IGNORE_FLASH_CHECKSUM: if TRUE, skip checksum verification
```

Flash segment checksums (CVN — Calibration Verification Number) are stored
in each segment header. If a mismatch is detected:
- P0601 DTC set (same as RAM failure)
- Engine may run in limp-home mode with default calibrations
- Flash reprogramming required to clear

### 1.3 Service / Engineering Mode

```
KE_SERVICE_CALIBRATION (0x8020): if TRUE, PCM is in service/engineering mode
  → RAM test may be bypassed
  → Checksum verification may be relaxed
  → Additional diagnostic PIDs enabled
  → Used by dealership tools during PCM replacement/programming
```

---

## 2. CRITICAL_REGION — System State Management

### 2.1 Ignition State Transitions

```
KE_IGNITION_OFF_TIME (0x9A9E): Ignition must be OFF for this long before
  state machine transitions from RUN → OFF. Debounces ignition switch.
  Stock: varies by application (~2-10 seconds).

KE_EXTENDED_POWEROFF_ON_TIME (0x9AA0): After ignition off, PCM stays in
  Extended Poweroff state for this long to allow:
  - EVAP diagnostic (natural vacuum decay test)
  - Fan after-run (doc 27)
  - Keep-alive memory write
  After this time → full power-off (sleep mode).
```

### 2.2 Crank-to-Run Transition

```
KV_STARTRUN_RPM (0x9AC4): Engine speed threshold for crank→run transition.
KV_STARTRUN_PULSES (0x9AA4): Number of consecutive low-resolution reference
  pulses above KV_STARTRUN_RPM before transitioning.

The transition requires BOTH:
  1. RPM > KV_STARTRUN_RPM
  2. KV_STARTRUN_PULSES consecutive CKP pulses at this RPM

This dual-criteria prevents false transition from starter noise.
```

---

## 3. PROTECTED — Protected/Factory Calibrations

"Protected" calibrations are not user-adjustable in production tuning tools.
They are set at the factory and require engineering-level access (ETAS CCP
or specialized programming tools) to modify.

### 3.1 RPM & Governor

| Address | Label | Type | Stock | Units | Description |
|---------|-------|------|-------|-------|-------------|
| 0x09A82 | KV_ENGINE_SPEED_LIMIT | word | — | RPM | ETC governor target max engine speed |
| 0x09A96 | KE_ENGINE_OVERSPEED_LAMP | word | — | RPM | RPM threshold for overspeed warning lamp |
| 0x09A98 | KE_TACH_PULLUP_ENABLE | byte | — | BOOLEAN | Internal tach pullup resistor enable |
| 0x09A99 | KE_ENGINE_SPEED_FILTER_COEF | byte | — | Unitless | RPM first-order lag filter coefficient |
| 0x09A9A | KE_FANLOCKUPRPMLIMIT | word | 0x7800 | RPM | Fan lockup RPM limit |

### 3.2 Voltage Limits

| Address | Label | Type | Stock | Units | Description |
|---------|-------|------|-------|-------|-------------|
| 0x0F7F0 | KE_IGN_VOLT_TOO_HIGH | word | — | Volts | Ignition voltage high fault threshold |
| 0x0F7F2 | KE_IGN_VOLT_TOO_LOW | word | — | Volts | Ignition voltage low fault threshold |

### 3.3 Misfire Engineering Parameters

```
KE_MISF_CALIBRATE_MODE (0x16CF9): Development-only flag that enables
  simultaneous cylinder mode AND revolution mode data collection.
  Production = FALSE. Engineering = TRUE for calibration development.

KE_MISF_OPP_CYL_SINGLE_PEAK (0x16D03): Selects single-peak vs multi-peak
  method for opposing cylinder misfire detection.

KE_MISF_REV_MODE_CYLINDER_OFFSET (0x16D06): Phase delay compensation for
  revolution mode — corrects for angular offset between the detected
  deceleration and the actual misfiring cylinder.

KE_MISF_RING_FILTER (0x16D07): Number of engine cycles to ignore after a
  misfire to avoid false detection from drivetrain ringing (torsional
  oscillation).
```

---

## 4. EXECUTIVE — Scheduler Control

```
KE_STOP_ENABLED (0x9A4F): When TRUE, the CPU executes a STOP instruction
  to fill dead time between DoLoop tasks rather than busy-waiting.
  STOP = Motorola 68k low-power state. CPU halts until next interrupt.

This is a power-saving measure. When disabled (FALSE), the scheduler
busy-waits (NOP loops). STOP mode reduces:
  - CPU current consumption (~70% reduction)
  - EMI from continuous clock switching
  - Heat generation in the PCM enclosure
```

---

## 5. ENGINE_STATE — Engine Run Detection

```
KE_NO_REF_TIME (0x9A9C): Engine is considered STOPPED if no reference
  pulses from CKP sensor have occurred in this time.
  Stock: varies, typically 0.5-2.0 seconds.

ENGINE_STATE also contains:
  KE_REV_MODE_ENABLE (RPM threshold for revolution mode detection)
  KE_DEFAULT_STATE (initial state at powerup)
```

---

## 6. CYLINDER_NUMBER — Cylinder Identification

### 6.1 CAM/CKP Synchronization

```
KV_CYLINDER_AT_CAM (0x16510): Which cylinder number is at TDC compression
  when the CMP sensor transitions. Used to synchronize the 4-stroke cycle.

  For LS1/LS6 (1-8-7-2-6-5-4-3 firing order):
    CMP transition → identifies cylinder #1 TDC
    Then CKP tooth count tracks subsequent cylinders:
      +15 teeth (90°) → cylinder 8
      +30 teeth → cylinder 7
      etc.

KV_SYNC_REFERENCES (0x16512): Number of low-resolution reference pulses
  that must occur before a cam signal transition is considered valid.
  Prevents false sync from CMP sensor noise during cranking.
```

---

## 7. SPARK_DWELL — Ignition Coil Dwell Time

### 7.1 Dwell Control

Dwell time is the duration the ignition coil primary is energized before
firing (spark). Longer dwell = higher spark energy, but excessive dwell
overheats the coil.

| Address | Label | Type | Stock | Units | Description |
|---------|-------|------|-------|-------|-------------|
| 0x13EFE | KA_MAIN_DWELL_TIME | table | — | ms | Base dwell vs RPM and voltage |
| 0x1436C | KA_MODIFIER_DWELL_TIME | table | — | 0-2 | Dwell modifier vs RPM and MAP |
| 0x14588 | KE_100MS_STEADY_STATE_RPM | word | — | RPM | RPM threshold for steady-state dwell |
| 0x1458A | KE_CRANK_BOOST_DWELL | word | — | 0-4 | Cold start crank dwell boost multiplier |
| 0x1458C | KE_INITIAL_DWELL | word | — | ms | Dwell initialized to this at powerup |

### 7.2 Dwell Algorithm

```
Base dwell = KA_MAIN_DWELL_TIME[RPM, Voltage]
Modified dwell = Base × KA_MODIFIER_DWELL_TIME[RPM, MAP]

During cranking:
  dwell ×= KE_CRANK_BOOST_DWELL  (extra energy for cold start)

Dwell is time-based (milliseconds), not angle-based. At high RPM,
the available time between ignition events decreases, so dwell
must be reduced to prevent coil overheating.

The SPARK_IO module handles the actual output pin toggling:
  - Dwell start: energize coil primary (output low)
  - Dwell end / spark: de-energize coil (output high → spark)
```

---

## 8. BAROMETER — Barometric Pressure Estimation

### 8.1 Overview

The P59 does not have a dedicated barometric pressure sensor. It estimates
barometric pressure from the MAP sensor at key-on (before engine start) or
at wide-open throttle (MAP ≈ baro).

### 8.2 Part-Throttle Baro Update

```
KE_BARO_TPS_LIMIT (0x893E): Min TPS for part-throttle baro update
KE_BARO_TPS_DELTA_LIMIT (0x8940): Max TPS change in last 100ms
KE_BARO_MAP_DELTA_LIMIT (0x8942): Max MAP change in last 100ms
KE_BARO_STABILITY_TIME (0x8944): Min stable time before update
KE_MIN_RPM_FOR_BARO_UPDATE (0x8946): Min RPM for update
KE_MAX_RPM_FOR_BARO_UPDATE (0x8948): Max RPM for update
KE_MAX_BARO_OFFSET_FOR_UPDATE (0x894A): Max baro-MAP delta allowed
KE_BARO_FILTER_COEFFICIENT (0x894C): Lag filter time constant
KA_BARO_OFFSET (0x8960): Sea level pressure offset added to baro
KE_BARO_DEFAULT_MAP_FAILED (0x893C): Default baro if MAP sensor failed
```

Baro is critical for fueling — it compensates for altitude changes.

---

## 9. ETC Pedal / Serial Data

### 9.1 Pedal Progression

```
KA_PEDAL_AREA_A (0x0A90C): Pedal progression table — maps pedal
  rotation to throttle area. Non-linear: more aggressive at low
  pedal (sporty feel), less sensitive at high pedal (control).

KA_PEDAL_AREA_B (0x0ABA0): Alternative progression for trailer mode.

KV_PEDAL_AREA_REDUCED (0x0A886): Reduced performance pedal map
  (limp-home mode, engine protection active).

KE_RELAXED_PEDAL_DEADBAND (0x0A884): Deadband subtracted from
  pedal position before lookup. Prevents throttle twitch from
  pedal vibration (~1-2%).

KV_PEDAL_HYSTERESIS (0x0A8C8): Hysteresis map for pedal position.
  Opening: uses main table. Closing: subtracts hysteresis to
  prevent oscillation when driver holds steady pedal.

KE_PEDAL_TRANSITION_INTERVAL (0x0A880): Time to transition to
  reduced performance mode (linear ramp, not instantaneous).
```

### 9.2 ETC System Parameters

```
KE_MAX_PPS_IND (0x0B4C4): Max pedal position sensor value (10-bit ADC).
KE_TPS_WOT_10BIT_EQUIVALENT (0x0B4C2): WOT throttle position (10-bit).
KE_IND_THROTTLE_POSITION_SCALER (0x0B592): Counts → percent conversion.

KE_ETC_LOW_VOLTAGE_THRESHOLD (0x0B58C): Voltage below which pedal/TAC
  module may not function (typically 6-7V).

KA_ETC_PM_TORQUE (0x0B4C6): Power management torque lookup based on
  desired throttle position and RPM — used to determine how much
  torque reduction is needed for protection modes.

KE_SHUTDOWN_VACUUM_TOO_LOW + TIME: Brake booster vacuum monitoring.
  If vacuum drops too low, power management may reduce engine power
  to preserve braking ability (failure of one-way check valve).
```

---

## 10. Sensor Interface Details

### 10.1 IAT (Intake Air Temperature)

```
KE_INDUCTION_AIR_TEMPERATURE_DEF (0x0F908): Default IAT if sensor failed.
KV_AIR_TEMP (0x0F90A): A/D counts → °C conversion table.

KV_CHARGE_TEMPERATURE_SQUARE_ROO (0x0F7F4): sqrt(Kelvin) — used in
  speed-density airflow calculation for charge temperature correction.
  The ideal gas law requires √T in the mass flow equation.
```

### 10.2 MAF (Mass Airflow Sensor)

```
KV_MASS_AIRFLOW (0x0F85A): Frequency → g/s conversion table.
  The MAF sensor outputs a frequency proportional to mass flow.
  This table converts Hz to grams/sec.
```

### 10.3 Voltage Monitoring

```
KE_IGN_VOLT_TOO_HIGH (0x0F7F0): System voltage > this → overvoltage fault
KE_IGN_VOLT_TOO_LOW (0x0F7F2): System voltage < this → undervoltage fault
  → Can set P0560 (System Voltage) DTC
  → May force reduced power mode
  → Injector dead time compensation affected (doc 07)
```

---

## 11. Gaps & Unresolved (NSA Round 1)

1. **Interrupt Vector Table**: The 68k CPU32+ has 256 exception vectors at
   0x000000-0x0003FF. Only the reset vector (SSP=0x00FFCE00, PC=0x00000440)
   has been identified. The remaining 254 vectors (TPU, QADC, SCI, periodic
   timer, etc.) are not documented.

2. **TPU Channel Assignments**: The Time Processor Unit has 16 channels.
   Channel assignments for CKP, CMP, VSS, injector timing, spark dwell,
   and tachometer output are not mapped.

3. **QADC Channel Assignments**: The Queued Analog-to-Digital Converter
   channels for MAP, MAF, IAT, ECT, TPS, O2 sensors, AC pressure, EGR
   position, and fuel level/tank pressure are not mapped.

4. **Chip Select / Memory Map**: The 68332 uses chip selects to map flash,
   RAM, and I/O peripherals. CS0-CS10 base addresses and block sizes are
   not documented from the disassembly.

5. **Watchdog Configuration**: The Computer Operating Properly (COP) watchdog
   timer is at SIM registers 0xFFFA27 (COP1) and 0xFFD006 (COP2 — external).
   The timeout period and service routine have not been traced.

6. **SCI / Class 2 Serial**: The J1850 VPW transceiver is memory-mapped at
   0xFFF600-0xFFF60F. The exact register layout (DLC, message buffers,
   interrupt flags) matches the MC68HC58 DLC chip. Not documented in our
   VPW protocol docs.

7. **Checksum Algorithm**: The CVN calculation for each flash segment uses
   a specific CRC polynomial. The algorithm has not been reverse-engineered
   (Universal Patcher handles it externally).

8. **Boot ROM**: The first 16KB (0x000000-0x003FFF) contains boot code.
   Only the reset vector has been identified. The boot sequence, chip
   initialization, and flash programming kernel loader are not traced.

**NSA question for round 2:** If an NSA engineer spent 40 MORE hours, they
would map every interrupt vector, every TPU channel, every QADC channel,
and document the complete boot sequence. These are the things we haven't
done yet.
