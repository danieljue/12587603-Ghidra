# GM P59 / LS1 PCM Tuning Formulas Reference

> **PCM:** P59 (1MB) / P01 (512KB) — OS 12587603  
> **Compiled from:** pcmhacking.net, ls1tech.com, forum.hptuners.com, forum.efilive.com, sloppywiki  
> **Date:** 2026-06-22

---

## Table of Contents

1. [VE Table (Volumetric Efficiency)](#1-ve-table-volumetric-efficiency)
2. [Spark Timing](#2-spark-timing)
3. [MAP Sensor Scaling](#3-map-sensor-scaling)
4. [RPM Scaling](#4-rpm-scaling)
5. [Temperature (ECT/IAT) Scaling](#5-temperature-ectiat-scaling)
6. [Injector Constants & Flow Rate](#6-injector-constants--flow-rate)
7. [MAF Calibration](#7-maf-calibration)
8. [AFR / Lambda / EQ Ratio](#8-afr--lambda--eq-ratio)
9. [Injector Pulse Width](#9-injector-pulse-width)
10. [G/Cyl Air Mass Calculation](#10-gcyl-air-mass-calculation)
11. [Additional Conversion Factors](#11-additional-conversion-factors)

---

## 1. VE Table (Volumetric Efficiency)

The VE table in the LS1 PCM stores values in **g·K/kPa** units in the binary. This is a "normalized airmass" that gets divided by temperature and multiplied by pressure to arrive at actual cylinder airmass (g/cyl).

### 1.1 Raw VE → g·K/kPa (Display Units)

```
VE (g·K/kPa) = X / 5120
```

- `X` = Raw VE value in binary (16-bit integer)
- `5120` = Scaler to g·K/kPa
- **Source:** [pcmhacking.net - Engine VE Percent](https://pcmhacking.net/forums/viewtopic.php?t=7261)

### 1.2 Raw VE → VE Percent (%)

```
VE (%) = (X / 5120) * (28.96 / A)
```

- `X` = Raw VE value
- `5120` = Scaler to g·K/kPa
- `28.96` = Gas constant for air (g/mol)
- `A` = Cylinder volume (liters)
- **Source:** [pcmhacking.net - Engine VE Percent](https://pcmhacking.net/forums/viewtopic.php?t=7261)

### 1.3 Cylinder Volume from Raw

```
Cylinder Volume (liters) = Y / 32768
```

- `Y` = Raw cylinder volume value in binary
- `32768` = Scaler to liters
- **Source:** [pcmhacking.net - Engine VE Percent](https://pcmhacking.net/forums/viewtopic.php?t=7261)

### 1.4 VE (g·K/kPa) → g/cyl (Air Mass per Cylinder)

```
g/cyl = VE * MAP / MAT
```

- `VE` = VE table value (g·K/kPa)
- `MAP` = Manifold absolute pressure (kPa)
- `MAT` = Manifold air temperature (Kelvin)
- **Source:** [forum.efilive.com - VE table units](https://forum.efilive.com/showthread.php?29763-VE-table-units)

### 1.5 Raw g/cyl in RAM → g/cyl

```
g/cyl = X / 8192
```

- `X` = Raw value from RAM (for P01/P59 Boost OS)
- `8192` = Scaler
- **Source:** [pcmhacking.net - P01 ram address](https://pcmhacking.net/forums/viewtopic.php?t=7643)

### 1.6 VE Table Unit Conversion Notes

The units conversion from g·K/kPa to % or g/cyl is **not trivial** — it requires additional information: cylinder volume, MAP, charge temperature, RPM, etc.

- In EFILive: VE can be viewed in **g·K/kPa, g/cyl, g/sec, or % volume**
- In HP Tuners: VE is shown in **g·K/kPa** (default binary units) or g/cyl
- **Source:** [ls1tech.com - HP Tuner people, favorite way to tune VE](https://ls1tech.com/forums/pcm-diagnostics-tuning/1870186-hp-tuner-people-whats-your-favorite-way-tune-ve-table.html)

---

## 2. Spark Timing

### 2.1 Raw Spark Value → Crank Degrees

```
Spark Advance (deg) = Raw * 0.3515625
```

- `Raw` = Raw spark value stored in binary (8-bit or 16-bit depending on table)
- `0.3515625` = Degree per bit scaler (exactly 360/1024, or 0.3515625 deg/bit)
- **Sources:**
  - [pcmhacking.net - Camira Ignition Module, Page 2](https://pcmhacking.net/forums/viewtopic.php?t=5402) — "A raw value of 30 = 0.351563*30 = 10.55 deg"
  - [pcmhacking.net - End of Injector Pulse](https://pcmhacking.net/forums/viewtopic.php?t=6396) — "X * 0.3515625"

### 2.2 Alternative Spark Conversion (Delco $8D Style)

Some definitions use an offset-based form:

```
Spark Advance (deg) = Raw * 0.351563 - 22.5
```

- `-22.5` = Offset for negative spark range encoding
- **Source:** thirdgen.org / pcmhacking.net discussions (used in some older Delco PCMs; may apply to certain LS1 tables)

### 2.3 Spark Table Axis

- **RPM axis:** Steps of 200 or 400 RPM depending on table
- **Air Mass axis (g/cyl):** Steps of 0.04 g/cyl, typically starting at 0.08 g/cyl
- **Source:** [pcmhacking.net - Segment Swap utility](https://pcmhacking.net/forums/viewtopic.php?t=6642&start=440)

### 2.4 Spark Boundary / Injection Timing Conversion

```
Boundary (degrees ATDC) = Raw * 0.3515625
```

- Used for injector end-of-pulse timing calculations
- HP Tuners shows this as "reference periods" (each unit = 90 crank degrees in 8-cyl)
- Injection Timing Boundary stock = 6.5/24 * 360 = **97.5 deg ATDC**
- Normal Injection Target vs ECT further adds: 5.55/24 * 360 = **83.25 deg ATDC**
- **Sources:**
  - [pcmhacking.net - End of Injector Pulse](https://pcmhacking.net/forums/viewtopic.php?t=6396)
  - [forum.hptuners.com - Injector Timing](https://forum.hptuners.com/showthread.php?18549-Please-Help-Define-Injector-Timing)

---

## 3. MAP Sensor Scaling

### 3.1 Stock 1-Bar MAP Sensor (GM 0-105 kPa)

**Formula:**
```
MAP (kPa) = (AD_Count / 255) * MAP_Sensor_Scale_Factor + MAP_Sensor_Offset
```
or equivalently:
```
MAP (kPa) = (Voltage / 5.0) * Linear + Offset
```

**Stock Values:**
| Parameter | Value |
|-----------|-------|
| MAP Sensor Scale Factor (Linear) | 94.43 kPa |
| MAP Sensor Offset | 10.33 kPa |
| AD_Count (8-bit) | 0–255 |

- **Source:** [pcmhacking.net - LS1 Boost OS V2.1](https://pcmhacking.net/forums/viewtopic.php?t=7482)

### 3.2 Common GM MAP Sensor Settings (HP Tuners / EFILive)

| Sensor | Linear (kPa) | Offset (kPa) | Max kPa |
|--------|-------------|-------------|---------|
| GM 1 Bar | 94.43 | 10.33 | 105 |
| GM 2 Bar | 188 | 10.2 | 210 |
| GM 3 Bar | 283 | 10.2 | 315 |

- **Source:** [Sloppy Mechanics Wiki - GM MAP Sensor Identification](https://sites.google.com/site/sloppywiki/everything-ls/gm-map-sensor-identification)

### 3.3 GM 3-Bar MAP Voltage Conversion

```
MAP (kPa) = Voltage * 8.94 - 14.53
```

- For 0–5V sensor output (approx.)
- **Source:** [Sloppy Mechanics Wiki - GM MAP Sensor Identification](https://sites.google.com/site/sloppywiki/everything-ls/gm-map-sensor-identification)

### 3.4 MAP kPa → PSI (gauge)

```
PSI (gauge) = (kPa / 204.8) * 0.14503773800722 - 14.6959494
```

- Converts kPa to PSI relative to atmospheric pressure
- **Source:** [pcmhacking.net - MAP sensor scaling with P59 ECU and Tuner Pro](https://pcmhacking.net/forums/viewtopic.php?t=8652)

### 3.5 MAP Axis in VE Table

- Stock VE table MAP axis: **15–105 kPa**
- For boosted applications: axis can be extended to 2-bar or 3-bar range
- **Source:** [pcmhacking.net - 2 bar MAP sensor hack](https://pcmhacking.net/forums/viewtopic.php?f=42&t=6632)

### 3.6 Raw MAP ADC → Display

The PCM converts 0–5V MAP sensor voltage to an 8-bit digital value (0–255), then:

```
MAP_kPa = (Raw_AD / 255) * 94.43 + 10.33   # 1-bar sensor
```

---

## 4. RPM Scaling

### 4.1 RPM from Raw Value

The exact formula depends on how the RPM value is stored in the specific data structure:

```
RPM = Raw / 4
```
or:
```
RPM = Raw * 25   (when raw is stored in 25 RPM units)
```

- Many tables in the P59 use **200 RPM step increments**, starting at 0
- Air per cylinder axis: starts at 0.08 g/cyl, steps of **0.04 g/cyl**
- **Source:** [pcmhacking.net - Segment Swap utility](https://pcmhacking.net/forums/viewtopic.php?t=6642&start=440)

### 4.2 Common RPM Axis Values (VE & Spark Tables)

```
0, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400,
2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600, 6000, 6400, 6800, 7200, 7600, 8000
```

- Standard P59 VE/Spark table RPM axis resolution
- **Source:** pcmhacking.net / universalpatcher XDF definitions

### 4.3 RPM in LOGRP Data Streams

```
RPM = (X * 25)   (displayed directly in most tools)
```

---

## 5. Temperature (ECT/IAT) Scaling

### 5.1 Thermistor Lookup Table

ECT and IAT sensors are **NTC thermistors** — the PCM uses a **nonlinear lookup table** to convert ADC counts to temperature. There is no single linear formula; the conversion is table-driven.

However, the raw value stored in calibration tables uses a conversion factor:

```
Display_Celsius = Lookup_Table[ADC_Count]
```

- ADC is 8-bit (0–255), 0–5V range
- The sensor linearization table maps ADC count → °C
- The linearization is fed with the **complement** of the ADC value in some implementations
- **Source:** [pcmhacking.net - M1.5.4](https://pcmhacking.net/forums/viewtopic.php?t=3786&start=10)

### 5.2 Common Thermistor Curve Points (GM LS-Series)

Typical GM thermistor response (approximate):

| ADC Count | Temperature (°C) |
|-----------|-----------------|
| 255 | -40 |
| 50 | ~30 |
| 25 | ~80 |
| 10 | ~120 |

- **Note:** Actual values depend on the specific calibration (pulled from XDF definitions)
- **Source:** pcmhacking.net multiple threads

### 5.3 IAT & ECT Sensor Check

When engine is cold (before first start), ECT and IAT should both read approximately **ambient temperature**. This is a quick sanity check for sensor function.

- **Source:** [pcmhacking.net - MAT sensor](https://pcmhacking.net/forums/viewtopic.php?t=6529)

### 5.4 Temperature Sensor Raw → Celsius (Linear Approximation)

For a rough linear approximation of some GM thermistor circuits (not the PCM internal table):

```
Temp_C = (ADC - offset) * scale   (varies by calibration)
```

The actual PCM conversion is always a **nonlinear lookup**.

---

## 6. Injector Constants & Flow Rate

### 6.1 Injector Flow Rate (IFR) Table

The P59 PCM uses an **Injector Flow Rate vs. MAP (kPa)** table. Values are stored in **grams per second (g/sec)**.

```
IFR (g/sec) = Raw / scaler
```

- Stock LS1 injectors: ~3.11–3.64 g/sec (varies by year/engine)
- **Units:** grams per second (mass flow)
- The IFR table compensates for varying fuel pressure across the injectors (referenced to manifold pressure)
- **Source:** [forum.efilive.com - Fuel Injector Rates](https://forum.efilive.com/showthread.php?23651-Fuel-Injector-Rates)

### 6.2 Injector Flow Rate Conversion

**lb/hr → g/sec:**
```
g/sec = lb/hr * 0.1259979
```
or approximately:
```
g/sec = lb/hr / 7.937
```

**cc/min → g/sec (for gasoline, density ~0.74 g/cc):**
```
g/sec = (cc/min / 60) * 0.74
```

**Example:**
- 28.87 lb/hr injectors → 3.64 g/sec (TunerCats)
- 187 g/min → 3.11 g/sec (EFILive)
- **Source:** Multiple forum threads (pcmhacking, efilive, hotrodders)

### 6.3 Injector Constant (Base Pulse Constant)

```
Injector Constant = Cylinder_Displacement_Liters / Injector_Flow_Rate_gps
```

or as the **BPC (Base Pulse Constant)** on older Delco ECUs:

```
BPC = Cylinder_Displacement_Liters / (IFR_gps * Number_Injector_Pulses_Per_Cycle)
```

- For LS1 (5.7L, 8 cylinders):
  - Cylinder displacement = 5.7 / 8 = 0.7125 L
  - Injector constant = 0.7125 / IFR_gps
- **Source:** [pcmhacking.net - Injector size/BPC Calculation](https://pcmhacking.net/forums/viewtopic.php?t=284)

### 6.4 Injector Flow Rate Table vs. MAP

The IFR table is indexed by **Delta MAP** (manifold pressure). On a vacuum-referenced fuel system, the table can be flat (constant flow rate across MAP).

- Stock table: 0 kPa (highest vacuum) through 80 kPa (near WOT)
- Flow rate **increases** at lower MAP (higher vacuum) — counterintuitive because injector flow rate is affected by pressure differential across the injector
- **Source:** [forum.efilive.com - Rich Idle Help](https://forum.efilive.com/showthread.php?7574-Rich-Idle-Please-Help!/page2)

### 6.5 Injector Scaling for Large Injectors

When injectors exceed the 63.5 g/sec IFR table limit (or the 512 g/sec MAF limit), **double/half scaling** is used:

1. Scale IFR table by 50% (cut in half)
2. Scale all airflow-related tables by 50% (VE, MAF, spark air mass axis, etc.)
3. Result: PCM "thinks" it has smaller injectors but everything is scaled proportionally

- **Source:** [forum.hptuners.com - IFR only goes to 63](https://forum.hptuners.com/showthread.php?28242-IFR-only-goes-to-63-I-have-83-injectors/page2)

---

## 7. MAF Calibration

### 7.1 MAF Transfer Function

The MAF calibration is a **Frequency (Hz) → Airflow (g/sec)** lookup table:

```
MAF_Airflow_gps = Lookup_Table(MAF_Frequency_Hz)
```

- Stock table: typically 0 Hz → 12,000 Hz range
- Stock maximum: **511.99 g/sec** (limited by 16-bit signed value)
- **Source:** LS1 tune files, HP Tuners/EFILive definitions

### 7.2 MAF Airflow Scaling

The MAF transfer table values directly correlate to engine airflow. Changing the **injector constant (IFR) effectively scales the MAF** because the PCM derives fueling from airflow and IFR.

```
Fuel_Mass = Air_Mass / Desired_AFR
Injector_Pulse_Width = Fuel_Mass / IFR_gps
```

- **Source:** [pcmhacking.net - LS1 Boost OS Development](https://pcmhacking.net/forums/viewtopic.php?t=7195&start=230)

### 7.3 MAF to Cylinder Airmass

```
g/cyl = 15 * MAF(g/sec) / RPM
```

- `15` = V8 4-stroke constant: (60 sec/min) / (4 strokes/cycle) * (8 cyl / 2 revs) = 15
- Derivation: For a V8, each cylinder fires every 2 revolutions. At RPM, the number of cylinder events per second = RPM * 4 / 60. MAF / (events/sec) = MAF * 15 / RPM
- **Source:** [scribd.com - LS1 Tuning Info PDF](https://www.scribd.com/document/81123686/LS1-Tuning-Info-1) (widely cited on ls1tech/pcmhacking)

### 7.4 MAF Hz → g/sec Reference Points (Stock LS1)

Typical stock LS1 MAF curve (85mm, approximate):

| Freq (Hz) | g/sec |
|-----------|-------|
| 1500 | 2.5 |
| 3000 | 10 |
| 5000 | 30 |
| 7000 | 70 |
| 9000 | 150 |
| 10500 | 250 |
| 11500 | 360 |

- Actual values vary by specific MAF sensor and intake configuration
- **Source:** LS1 stock calibrations (various)

---

## 8. AFR / Lambda / EQ Ratio

### 8.1 EQ Ratio (Equivalence Ratio)

The P59 PCM commands fuel in terms of **Equivalence Ratio (EQ Ratio)**, not AFR directly.

```
EQ Ratio = Desired_AFR_Stoichiometric / Commanded_AFR
```

- **Stoichiometric AFR for gasoline:** 14.68:1 (GM factory) or 14.7:1 (common)
- EQ Ratio > 1.0 = richer than stoichiometric
- EQ Ratio < 1.0 = leaner than stoichiometric
- **Source:** [forum.hptuners.com - EQ Ratio Discussion](https://forum.hptuners.com/showthread.php?55098-Equivalence-Ratio-(EQ)-Discussion)

### 8.2 EQ Ratio → AFR Conversion

```
AFR = Stoichiometric_AFR / EQ_Ratio
```

- Example: EQ 1.17 → 14.68 / 1.17 = 12.55 AFR (PE enrichment)
- **Source:** [HP Tuners Help - Air/Fuel Ratio](https://www.hptuners.eu/help/vcm_editor_tuning_how_to_basics_afr.htm)

### 8.3 Lambda ↔ EQ Ratio

```
Lambda = 1 / EQ_Ratio
EQ_Ratio = 1 / Lambda
```

- Lambda 1.0 = stoichiometric (regardless of fuel type)
- Lambda 0.85 = EQ 1.176 (rich)
- **Source:** [pcmhacking.net - Command air fuel ratio](https://pcmhacking.net/forums/viewtopic.php?t=8762)

### 8.4 PE (Power Enrichment) EQ Ratio

PE enrichment multiplies the base EQ ratio:
```
Commanded_EQ = Base_EQ * PE_Multiplier
```

- Typical PE targets: 1.14–1.18 EQ (12.9–12.4 AFR on gasoline)
- Leaner after peak torque: ~1.13 EQ (13.0 AFR)
- **Source:** [ls1tech.com - Tuning in OLSD](https://ls1tech.com/forums/pcm-diagnostics-tuning/1751475-tuning-olsd-pe-ol-eq-ratio-values.html)

### 8.5 EQ Ratio → Wideband Lambda/AFR for Display

For datalogging display conversion:

```
X / 230   → 0–5V range (wideband analog input scaling)
X / 51    → 0–5V alternate scaling
```

- **Source:** [pcmhacking.net - Wideband closed loop AFR targets](https://pcmhacking.net/forums/viewtopic.php?t=6257)

---

## 9. Injector Pulse Width

### 9.1 Base Injector Pulse Width

The final injector pulse width is calculated from:

```
Base_PW_ms = (Cylinder_Airmass_g / Desired_AFR) / IFR_gps * 1000
```

Then modified by:
- **Short pulse adder** (low pulse width compensation)
- **Injector offset (dead time)** vs. battery voltage
- **Cranking fuel multipliers** (startup enrichment vs. coolant temp)

### 9.2 Injector Offset (Dead Time) vs. Battery Voltage

```
Final_PW_ms = Base_PW_ms + Injector_Offset_ms
```

- Injector offset compensates for opening delay
- Table: **Offset (ms) vs. Battery Voltage (V)**
- Typical values: 0.4–1.2 ms for stock LS1 injectors at 14V
- **Source:** [forum.efilive.com - How do I add fuel](https://forum.efilive.com/showthread.php?148-How-do-I-add-fuel/page2)

### 9.3 Cranking Fuel Pulse Width

```
Crank_PW_ms = Base * Cranking_Multiplier_vs_ECT + Offset
```

- Cranking fuel pulse width multiplier vs. CTS (Coolant Temp Sensor)
- Maximum cranking PW: ~65 ms
- **Source:** [pcmhacking.net - Injector pulse for coolant temp](https://pcmhacking.net/forums/viewtopic.php?t=4902)

### 9.4 Injector End of Pulse Timing

```
EOI_degrees_ATDC = Boundary + Normal_Target_vs_ECT + Makeup_Pulse_Offset
```

- **Boundary:** 6.5 reference periods = **97.5° ATDC** (stock)
- **Normal Target vs ECT:** adds 5.55 periods = **83.25° ATDC** (stock warm)
- Each reference period = 90° crank in V8
- Conversion: `degrees = Raw * 0.3515625`
- **Source:** [forum.hptuners.com - Injector Timing](https://forum.hptuners.com/showthread.php?18549-Please-Help-Define-Injector-Timing)

---

## 10. G/Cyl Air Mass Calculation

### 10.1 From VE Table (Speed Density)

```
g/cyl = VE_table(g*K/kPa) * MAP(kPa) / Charge_Temp(K)
```

### 10.2 From MAF Sensor

```
g/cyl = 15 * MAF(g/sec) / RPM
```

- Constant `15` = (60 sec) / (2 rev/event * 4 events/rev) for V8 4-stroke
- For 6-cylinder: use constant `20` = (60) / (2 * 3)
- For 4-cylinder: use constant `30` = (60) / (2 * 2)

### 10.3 Air Mass per Cylinder RAM Address

```
g/cyl = Raw_RAM_Value / 8192
```

- Applicable to P01/P59 Boost OS RAM variables
- **Source:** [pcmhacking.net - P01 ram address](https://pcmhacking.net/forums/viewtopic.php?t=7643)

---

## 11. Additional Conversion Factors

### 11.1 Pressure Conversions

| From | To | Formula |
|------|-----|---------|
| kPa | PSI (absolute) | PSI = kPa × 0.1450377 |
| kPa | PSI (gauge) | PSIg = (kPa × 0.1450377) - 14.7 |
| kPa | inHg | inHg = kPa × 0.2953 |
| kPa | bar | bar = kPa / 100 |

### 11.2 Temperature Conversions

| From | To | Formula |
|------|-----|---------|
| °C | Kelvin | K = °C + 273.15 |
| °F | °C | °C = (°F - 32) × 5/9 |
| °C | °F | °F = °C × 9/5 + 32 |

### 11.3 Mass Flow Conversions

| From | To | Formula |
|------|-----|---------|
| lb/hr | g/sec | g/sec = lb/hr × 0.126 |
| g/sec | lb/hr | lb/hr = g/sec × 7.937 |
| cc/min | g/sec | g/sec = (cc/min / 60) × 0.74 |
| g/min | g/sec | g/sec = g/min / 60 |

### 11.4 Resolution Notes

- **VE table:** 5120 counts per g·K/kPa unit (raw resolution ~0.000195 g·K/kPa per bit)
- **Spark:** 0.3515625 deg per raw bit (360/1024)
- **MAP ADC:** 8-bit (0–255), ~0.37 kPa per count (1-bar sensor)
- **g/cyl in RAM:** 8192 counts per g/cyl
- **MAF airflow:** Limited to 511.99 g/sec in 16-bit signed, scales differently with IFR changes

---

## Source Links Summary

| Topic | Primary Source |
|-------|---------------|
| VE table formula | [pcmhacking.net - Engine VE Percent](https://pcmhacking.net/forums/viewtopic.php?t=7261) |
| VE unit conversion | [forum.efilive.com - VE table units](https://forum.efilive.com/showthread.php?29763-VE-table-units) |
| VE table tuning | [ls1tech.com - VE Table Cracked](https://ls1tech.com/forums/pcm-diagnostics-tuning/149741-ve-table-cracked.html) |
| Spark conversion | [pcmhacking.net - Camira Ignition Module](https://pcmhacking.net/forums/viewtopic.php?t=5402) |
| Spark / injection timing | [pcmhacking.net - End of Injector Pulse](https://pcmhacking.net/forums/viewtopic.php?t=6396) |
| MAP sensor scaling (1-bar) | [pcmhacking.net - LS1 Boost OS V2.1](https://pcmhacking.net/forums/viewtopic.php?t=7482) |
| MAP sensor identification | [Sloppy Wiki - GM MAP Sensor](https://sites.google.com/site/sloppywiki/everything-ls/gm-map-sensor-identification) |
| MAP to PSI conversion | [pcmhacking.net - MAP scaling P59 Tuner Pro](https://pcmhacking.net/forums/viewtopic.php?t=8652) |
| Injector constant / BPC | [pcmhacking.net - Injector size/BPC](https://pcmhacking.net/forums/viewtopic.php?t=284) |
| Injector timing definition | [forum.hptuners.com - Injector Timing](https://forum.hptuners.com/showthread.php?18549-Please-Help-Define-Injector-Timing) |
| EQ Ratio / AFR | [forum.hptuners.com - EQ Ratio Discussion](https://forum.hptuners.com/showthread.php?55098-Equivalence-Ratio-(EQ)-Discussion) |
| g/cyl RAM conversion | [pcmhacking.net - P01 ram address](https://pcmhacking.net/forums/viewtopic.php?t=7643) |
| Temperature scaling | [pcmhacking.net - M1.5.4](https://pcmhacking.net/forums/viewtopic.php?t=3786) |
| Wideband conversion | [pcmhacking.net - Wideband closed loop AFR targets](https://pcmhacking.net/forums/viewtopic.php?t=6257) |
| Tuning reference docs | [ls1tech.com - Tuning Docs/FAQ](https://ls1tech.com/forums/pcm-diagnostics-tuning/287094-read-me-first-tuning-docs-ve-maf-ses-lights-faqs-more-01-31-07-a.html) |
| LS1 Boost OS | [pcmhacking.net - LS1 Boost OS V2.1](https://pcmhacking.net/forums/viewtopic.php?t=7482) |
| 12587603 XDF (GitHub) | [LegacyNsfw/12587603](https://github.com/LegacyNsfw/12587603) |

---

## Notes

1. **Resolution context:** The raw binary values use integer scaling. All conversions presented here reflect the scalers used by the PCM firmware and confirmed by the tuning community.

2. **OS-specific variations:** While this reference targets OS 12587603 (P59), most formulas apply broadly to P01 (512KB) PCMs as well. Always verify against the specific XDF definition for your OS.

3. **Injector data format:** The LS1 PCM uses the "Gen 3" injector data format (IFR vs. MAP in g/sec). Gen 4 (E38/E67) uses a different format (flow rate vs. pressure delta, offset vs. pressure). Conversion spreadsheets exist to adapt Gen 4 injector data to Gen 3 format.

4. **Temperature conversion:** Unlike other sensors which use linear formulas, ECT/IAT conversion is strictly via lookup table. The raw values stored in calibration tables are temperatures (°C) — the XDF definitions handle the raw-to-temperature lookup internally.

5. **Verification:** All formulas should be verified against the specific XDF definitions for OS 12587603 in the [LegacyNsfw/12587603 GitHub repository](https://github.com/LegacyNsfw/12587603).

---

*Compiled from public forum knowledge on pcmhacking.net, ls1tech.com, forum.hptuners.com, forum.efilive.com, and sloppywiki. If you find errors or missing formulas, please contribute updates.*
