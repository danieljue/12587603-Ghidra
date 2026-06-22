# P59 OS 12587603 — Corvette-Specific Features

> Traced from 68k disassembly — 2026-06-22
> Features specific to C5 Corvette platform: column lock, oil starvation
> protection, and Check Gauges/Information Center interface.

---

## 1. Column Lock (COLUMN_LOCK)

### 1.1 Overview

The C5 Corvette (1997-2004) has an electronic steering column lock as an
anti-theft measure. The PCM communicates with the BCM to control the column
lock motor. If the column fails to unlock, the PCM enforces a fuel cut
above a calibrated speed to prevent driving with a locked column.

This feature is Corvette-only (`KE_COLUMN_LOCK_PRESENT = TRUE` ONLY for
Y-body). It has been a notorious failure point on C5s, leading to a GM
recall and many aftermarket bypass modules.

### 1.2 Calibrations

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1FA50 | KE_COLUMN_LOCK_PRESENT | byte | TRUE | Boolean | Enable column lock (Y-body only) |
| 0x1FA52 | KE_COLUMN_LOCK_VSS_FUEL_DISABLE | word | — | MPH | VSS above which fuel cut if column locked |

### 1.3 Operation

```
1. At key-on: PCM queries BCM for column lock status
2. If column locked and cannot unlock:
   - VSS > KE_COLUMN_LOCK_VSS_FUEL_DISABLE → fuel cut
   - Prevents driving with locked steering column
3. Normal operation:
   - Unlock column after VATS authentication (doc 19)
   - Lock column after key-off and driver door open
```

---

## 2. CIC — Check Gauges / Information Center

### 2.1 Overview

The CIC module controls the "Check Gauges" warning lamp and message center
display on the Corvette instrument cluster. The PCM sends warning messages
over Class 2 serial to the IPC (Instrument Panel Cluster).

### 2.2 Calibration

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08021 | KE_CIC_MEDIUM_RES_REF_FILTER | word | — | μs | Medium resolution reference filter |

---

## 3. OISTER — Oil Starvation Protection

### 3.1 Overview

"OISTER" = **OI**l **S**tarva**T**ion **E**ngine **R**esponse.

This is a Corvette-specific track-use protection system. During sustained
high-G cornering (common on road courses with sticky tires), engine oil
can slosh away from the pickup tube, causing momentary oil pressure loss.
The OISTER system detects this condition through lateral acceleration
sensing and responds by:
- Limiting engine RPM
- Forcing transmission upshifts (to lower RPM)
- Reducing ETC vehicle speed governor

This prevents engine damage from oil starvation during track driving.

### 3.2 Lateral G Sensing

The P59 does not have a dedicated lateral G sensor. The OISTER system
likely derives lateral G from:
- Vehicle speed and steering angle (if available)
- ABS wheel speed differential (Corvette has 4-channel ABS)
- Yaw rate sensor (if equipped — late C5s have Active Handling)

### 3.3 Calibrations

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0F92C | KE_OIL_STARVE_ENABLE | byte | — | BOOLEAN | Master enable for oil starvation protection |
| 0x0F92E | KE_DRIVER_WARNING_DELAY_TIME | word | — | Seconds | Warning to powertrain action delay |
| 0x0F930 | KE_HIGH_G_MINIMUM_TIME | word | — | Seconds | Min sustained high-G for activation |
| 0x0F932 | KE_INTEGRAL_RESET_DELAY | word | — | Seconds | Prevent G spikes from resetting integrator |
| 0x0F934 | KE_LAT_G_SPIKE_REJECTION_TIME | word | — | Seconds | G spike ignore time |
| 0x0F936 | KE_LOWEST_GEAR_ALLOWED_LIMIT | word | — | Gear | Lowest gear allowed during protection |
| 0x0F938 | KE_MINIMUM_VEHICLE_SPEED_FOR_OIS | word | — | MPH | Min VSS for OISTER activation |
| 0x0F93A | KE_MAXIMUM_VEHICLE_SPEED_FOR_OIS | word | — | MPH | Max VSS for OISTER activation |
| 0x0F93C | KE_OIL_PRESSURE_G_ENABLE | word | — | Gs | Lateral G threshold (pressure-based) |
| 0x0F93E | KE_OIL_PRESSURE_NOISE_REJECTION | word | — | Seconds | Oil pressure signal noise rejection |
| 0x0F940 | KV_OIL_LEVEL_FILTER_COEFFICIENT | table | — | Unitless | Lat G filter vs threshold |
| 0x0F96A | KE_OIL_LEVEL_FILTER_COEFFICIENT | word | — | Unitless | Max lat G seconds filter |
| 0x0F96C | KE_OIL_LOWEST_GEAR_RESET_SPEED | word | — | MPH | Reset lowest gear below this VSS |
| 0x0F96E | KE_OIL_MINIMUM_VEHICLE_SPEED | word | — | MPH | Min ETC speed governor during protection |
| 0x0F970 | KE_OIL_SPEED_LIMIT_DECREASE | word | — | MPH | Speed gov decrease rate during protection |
| 0x0F972 | KE_OIL_SPEED_LIMIT_INCREASE | word | — | MPH | Speed gov increase rate after protection |
| 0x0F974 | KE_POWERTRAIN_ACTION_TIME | word | — | Seconds | Min time powertrain action stays active |
| 0x0F976 | KE_PROTECTION_G_HIGH_HYSTERESIS | byte | — | Gs | High-G timer enable threshold |
| 0x0F977 | KE_PROTECTION_G_LOW_HYSTERESIS | byte | — | Gs | Low-G condition threshold |
| 0x0F978 | KE_THROTTLE_MAX_TO_RESUME_DRIVER | word | — | Percent | TPS must close below this to resume driver control |
| 0x0F97A | KE_OIL_FILTER_COEFFICIENT | word | — | Unitless | Lat G first-order lag filter |
| 0x0F97C | KV_OIL_MIN_ENGINE_RUN_TIME | table | — | Seconds | Min run time before OIS criteria active |
| 0x0F9A2 | KV_OIL_PRESSURE_DISABLE_LEVEL | table | — | kPa | Oil pressure above which OIS disabled |
| 0x0F9C0 | KV_OIL_PRESSURE_ENABLE_LEVEL | table | — | kPa | Oil pressure below which OIS enabled |
| 0x0F9DE | KV_OIL_TEMPERATURE_OFFSET | table | — | G_Seconds | Oil temp compensation for lat G threshold |
| 0x0F9FE | KV_RESET_INTEGRAL_LATERAL_GS | table | — | RPM | RPM below which G integrator reset |
| 0x0FA30 | KA_OIL_BASE_LEVEL_LH | table | — | G_Seconds | Left-hand turn G-seconds threshold |
| 0x0FB5C | KA_OIL_BASE_LEVEL_RH | table | — | G_Seconds | Right-hand turn G-seconds threshold |

### 3.4 Algorithm

```
1. Engine must have run for KV_OIL_MIN_ENGINE_RUN_TIME[ECT]
2. Calculate lateral G from vehicle dynamics:
   Lat_G = f(VSS, wheel_speed_differential, steering_angle)

3. Filter lateral G through first-order lag:
   Filtered_G = prev + (Lat_G - prev) × KE_OIL_FILTER_COEFFICIENT

4. Track "G-Seconds" — the integral of lateral G over time:
   G_seconds = ∫ Filtered_G dt

5. Spike rejection:
   Ignore G spikes shorter than KE_LAT_G_SPIKE_REJECTION_TIME
   Wait KE_INTEGRAL_RESET_DELAY before resetting integrator

6. Compare against base level thresholds:
   Left turn: G_seconds > KA_OIL_BASE_LEVEL_LH
   Right turn: G_seconds > KA_OIL_BASE_LEVEL_RH
   Temperature-compensated via KV_OIL_TEMPERATURE_OFFSET

7. OR detect low oil pressure directly:
   Oil_P < KV_OIL_PRESSURE_ENABLE_LEVEL
   Debounce: KE_OIL_PRESSURE_NOISE_REJECTION

8. Activation (any condition met for KE_HIGH_G_MINIMUM_TIME):
   → Force transmission upshift to KE_LOWEST_GEAR_ALLOWED_LIMIT
   → Reduce ETC vehicle speed governor by KE_OIL_SPEED_LIMIT_DECREASE
   → Minimum governor: KE_OIL_MINIMUM_VEHICLE_SPEED
   → Warning to driver after KE_DRIVER_WARNING_DELAY_TIME

9. Exit conditions:
   → G_seconds below threshold AND oil pressure > KV_OIL_PRESSURE_DISABLE_LEVEL
   → Throttle < KE_THROTTLE_MAX_TO_RESUME_DRIVER (driver lifted)
   → Maintain for KE_POWERTRAIN_ACTION_TIME minimum
   → Gradually restore speed governor at KE_OIL_SPEED_LIMIT_INCREASE rate
   → Reset lowest gear to 1st below KE_OIL_LOWEST_GEAR_RESET_SPEED
```

---

## 4. BRAKE_IO — Brake Switch Diagnostics

### 4.1 Overview

The Corvette monitors brake switch inputs for multiple systems:
- Cruise control cancel (doc 31)
- Brake Torque Management (doc 32)
- TCC release verification
- Extended travel brake diagnostics

### 4.2 Calibrations

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x1639A | KE_EXTENDED_TRAVEL_BRAKE_FAIL_CO | byte | — | Counts | Extended travel brake fail threshold |
| 0x1639B | KE_EXTENDED_TRAVEL_BRAKE_SAMPLE_ | byte | — | Counts | Extended travel brake pass threshold |
| 0x1639C | KE_BRAKE_ETM_FAIL_COUNT | byte | — | Counts | ETM brake diagnostic fail count |
| 0x1639D | KE_BRAKE_ETM_SAMPLE_COUNT | byte | — | Counts | ETM brake diagnostic sample count |
| 0x1639E | KE_BRAKE_CRZ_FAIL_COUNT | byte | — | Counts | TCC brake diagnostic fail count |
| 0x1639F | KE_BRAKE_CRZ_SAMPLE_COUNT | byte | — | Counts | TCC brake diagnostic pass count |
| 0x163A0 | KE_BRAKE_DIAG_SPEED_DELTA | word | — | MPH | Speed delta over 250ms for brake check |
| 0x163A2 | KE_BRAKE_TEST_ENGINE_SPEED | word | — | RPM | Min RPM for brake monitoring |
| 0x163A4 | KE_BRAKE_TEST_RUN_TIME | word | — | Seconds | Time above min RPM for brake monitor |
| 0x163A6 | KE_BRAKE_ENABLE_WHEEL_SPD | word | — | MPH | Wheel speed to begin monitoring |
| 0x163A8 | KE_BRAKE_DISABLE_WHEEL_SPD | word | — | MPH | Wheel speed to end monitoring |

---

## 5. INSTRUMENTATION

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x163B9 | KE_ENABLE_MALF_DISPLAY | byte | — | BOOLEAN | Store data for malfunction code display |

Enables the IPC to display DTC descriptions on the Driver Information Center
(DIC) — a Corvette/Cadillac feature where trouble codes can be read and
displayed through the instrument cluster without a scan tool.

---

## 6. Gaps & Unresolved

1. **OISTER lateral G source**: The exact input for lateral acceleration
   (ABS-based, steering angle, yaw sensor) is not confirmed. C5 Corvettes
   with Active Handling have a yaw/lateral G sensor; base models may not.

2. **Column lock BCM communication**: The exact Class 2 message sequence
   for column lock status query/response is not decoded.

3. **CIC message format**: The Class 2 message that triggers the "Check
   Gauges" lamp is part of the C2_NORMAL_MSGS module — specific message
   ID and data bytes not decoded.

4. **BRAKE_IO on manual transmission**: The TCC brake diagnostic
   (KE_BRAKE_CRZ_FAIL/SAMPLE_COUNT) is for automatic transmissions.
   On the M6, only extended travel and ETM diagnostics apply.
