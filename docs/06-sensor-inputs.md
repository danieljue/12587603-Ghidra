# GM P59 PCM Hardware Pinout & I/O Reference

> **Sources:** lt1swap.com, pcmhacking.net, HP Tuners forum, LS1TECH, 24xracing.com, corvetteforum.com
> **Last Updated:** 2026-06-22

---

## 1. P59 PCM Overview

The **P59** is the GM Gen III LS-based Powertrain Control Module used in 2003–2007 full-size trucks and SUVs (4.8L, 5.3L, 6.0L), as well as some 2003–2004 Corvettes.

| Property | P59 | P01 (for reference) |
|----------|-----|---------------------|
| Years | 2003–2007 | 1999–2002 |
| Connectors | **BLUE (C1)** + **GREEN (C2)** | BLUE (C1) + RED (C2) |
| Pins per connector | 80 | 80 |
| Flash chip | Intel AB28F800 / AMD AM29F800 | Intel AB28F800 / AMD AM29F800 |
| ADC resolution | 10-bit (shifted to 8-bit in code) | 10-bit (shifted to 8-bit) |
| OS IDs | 12587603 (most common), 12575502, etc. | 12212156, 12202088, etc. |
| VPW Protocol | J1850 VPW (Class 2) | J1850 VPW (Class 2) |

**Connector Part Numbers:**
- C1 (BLUE): 12191489, TPA: 12176408
- C2 (GREEN): 12191488, TPA: 12176410
- Connector cover: 12191108

**Color Legend (lt1swap.com):**
- 🔵 **Blue/Cyan highlight** = Required for standalone, goes to external connection
- 🟡 **Yellow highlight** = Can be removed, NOT needed for standalone
- No highlight = Remains untouched, goes directly from PCM to sensor/device

---

## 2. Spare ADC Inputs for Wideband O2 / Pressure Sensors

The P59 has multiple 0–5V analog-to-digital converter (ADC) inputs that can be repurposed for wideband O2 sensors, fuel pressure sensors, boost pressure sensors, etc.

### 2.1 Primary Wideband Input: EGR Pintle Position (C1 Pin 55)

| Parameter | Detail |
|-----------|--------|
| **Connector/Pin** | **C1 BLUE Pin 55** |
| **Stock Function** | EGR Pintle Position Sensor Signal |
| **Wire Color** | BRN (Brown) — Circuit 1456 (when equipped) |
| **Signal Type** | 0–5V Analog (ADC input) |
| **Notes** | The most commonly used wideband input. Even on vehicles NOT equipped with EGR from the factory, this ADC channel is still active. Wire your wideband controller's 0–5V analog output to this pin. |

**Companion Pins (C1 Blue):**
- **Pin 56** — 5V Reference for EGR pintle position sensor (can be used to power external sensors if available)
- **Pin 41** — EGR Pintle Position Sensor Ground / Low Reference

**Wideband Wiring Example (AEM 30-0300 / Spartan 2 / LC-2):**
```
Wideband White (0-5V Analog Out) → C1 Blue Pin 55 (EGR Signal)
Wideband Brown (Analog Ground)    → PCM ground (C1 Pin 1 or C1 Pin 40)
Wideband Red (12V Power)          → Switched 12V (key-on)
Wideband Black (Chassis Ground)   → Chassis ground
```

**Tuning Software:**
- Log "EGR Position" or "EGR Voltage" PID; apply transfer function (e.g., 0V=10.0 AFR, 5V=20.0 AFR)
- In Boost OS / custom OS: EGR channel can be redefined as a wideband lambda input for closed-loop fueling

### 2.2 Secondary ADC Input: Fuel Tank Pressure (C2 Pin 64)

| Parameter | Detail |
|-----------|--------|
| **Connector/Pin** | **C2 GREEN Pin 64** |
| **Stock Function** | Fuel Tank Pressure Sensor Signal |
| **Wire Color** | GRY (Gray) — Circuit 2705 (when equipped) |
| **Signal Type** | 0–5V Analog (ADC input) |
| **Notes** | Excellent secondary analog input. Often unused in swap applications. Can be used for fuel pressure, oil pressure, or a second wideband. |

### 2.3 Tertiary ADC Input: A/C Pressure Sensor (C1 Pin 14 on some OS)

| Parameter | Detail |
|-----------|--------|
| **Connector/Pin** | **C1 BLUE Pin 14** (varies by OS) |
| **Stock Function** | A/C Refrigerant Pressure Sensor Signal |
| **Signal Type** | 0–5V Analog (ADC input) |
| **Notes** | When A/C is not used or when using Analog (cycling) A/C request mode, this ADC can be repurposed. Verify availability in your specific OS calibration. |

### 2.4 ADC Input Summary Table

| Priority | Connector | Pin | Stock Function | Wire Color | Circuit | Notes |
|----------|-----------|-----|----------------|------------|---------|-------|
| ⭐ Primary | C1 Blue | 55 | EGR Pintle Position | BRN | 1456 | Default wideband input |
| ⭐⭐ Secondary | C2 Green | 64 | Fuel Tank Pressure | GRY | 2705 | Good second analog input |
| ⭐⭐⭐ Tertiary | C1 Blue | 14 | A/C Pressure Signal | ORN/BLK | 1061 | If A/C not using pressure transducer |
| Spare | C1 Blue | 56 | EGR 5V Reference | GRY | 474 | Power external 5V sensor |

**Important Notes:**
- The P59 ADC is 10-bit hardware (0–1023 raw counts) but the code shifts to 8-bit (0–255). This means 5V / 256 ≈ 0.0195V per count of resolution, which is more than adequate for wideband AFR.
- When using a non-stock input, set the related DTC to "No Error Reported" (e.g., P0401, P0403, P0404, P0405 for EGR; P0452, P0453 for FTP).
- You may need to define a custom PID/AUX input in your tuning software with the correct transfer function.

---

## 3. Spare PWM / Low-Side Driver Outputs for Boost Control

The P59 has several spare low-side driver (LSD) outputs that can be used for boost control solenoids, electric fan relays, or other PWM-controlled devices.

### 3.1 LS1 Boost OS Boost Control Output

The **LS1 Boost OS** (by Bubbadavis on pcmhacking.net) repurposes existing PCM outputs for boost control:

| Parameter | Detail |
|-----------|--------|
| **Boost Control Output** | **C2 GREEN Pin 3** — EVAP Canister Vent Solenoid Control |
| **Output Type** | Low-side driver (ground-switching, PWM capable) |
| **Wire Color** | Varies (typically DK GRN/WHT when equipped) |
| **Max Current** | ~0.5A continuous (tested with MAC 35A-AAA-DDBA-1BA boost solenoid @ 5.4W) |
| **PWM Frequency** | Configurable in Boost OS (typically 20–32 Hz for MAC valves) |

**Boost Solenoid Wiring (P59 Boost OS):**
```
Boost Solenoid Pin 1 → Switched 12V (key-on, fused 5A)
Boost Solenoid Pin 2 → C2 Green Pin 3 (PCM low-side driver)
```

**Reference (P01):** C2 Pin 7 = Solenoid Power (12V), C2 Pin 41 = Solenoid Control

### 3.2 Electric Fan Control Outputs

Two spare low-side drivers are available specifically for electric fan control:

| Fan | Connector | Pin | Stock Status | Notes |
|-----|-----------|-----|--------------|-------|
| **Fan 1 (Low Speed)** | C2 Green | **42** | Not Used (add pin) | 2005+ may already have pin installed |
| **Fan 2 (High Speed)** | C2 Green | **33** | Not Used (add pin) | — |

**Fan Relay Wiring:**
```
PCM C2 Pin 42 → Fan 1 Relay coil (ground side)
PCM C2 Pin 33 → Fan 2 Relay coil (ground side)
Relay coil + side → Switched 12V (key-on)
```

### 3.3 All Spare / Repurposable Low-Side Driver Outputs

| Connector | Pin | Stock Function | Status | Reuse Potential |
|-----------|-----|----------------|--------|-----------------|
| C2 Green | **3** | EVAP Vent Solenoid | Removable (yellow) | ⭐ **Boost control (primary)** |
| C2 Green | **42** | Fan 1 Relay | Not Used / add pin | ⭐ Electric Fan 1 |
| C2 Green | **33** | Fan 2 Relay | Not Used / add pin | ⭐ Electric Fan 2 |
| C2 Green | **43** | A/C Clutch Relay | Removable if no A/C | Spare LSD |
| C2 Green | **39** | Starter Enable Relay | Removable (yellow) | Spare LSD |
| C2 Green | **9** | Fuel Pump Relay Control | Required (blue) | Do not repurpose |

---

## 4. CCP (Clutch Pedal Position) Circuit

### 4.1 P59 Clutch Switch Inputs

The P59 has **two** clutch-related switch inputs:

| Parameter | C2 Green Pin 35 | C2 Green Pin 18 |
|-----------|-----------------|-----------------|
| **Function** | CPP Switch Signal (M/T) | Clutch Start Switch Signal (M/T) |
| **Wire Color** | GRY (Gray) | DK GRN (Dark Green) |
| **Circuit No.** | 48 | 1433 |
| **Usage** | Clutch Pedal Position (CPP) for PCM logic | Clutch safety start switch |
| **Availability** | Manual transmission only | Manual transmission only |

### 4.2 CPP Circuit Description

**C2 Pin 35 — CPP Switch Signal:**
- This is a **switch-to-ground** input
- The CPP switch is typically a normally-open switch that **closes to ground** when the clutch pedal is **depressed**
- The PCM internally pulls this pin HIGH (typically 5V or 12V through a pull-up resistor) and detects a LOW (ground) when the clutch is pressed
- Used by the PCM for: idle control (anticipate load change), rev-matching, cruise control deactivation, and shift logic

**C2 Pin 18 — Clutch Start Switch:**
- This is the safety interlock switch
- Typically wired in series with the starter relay circuit
- PCM reads this to determine if clutch is depressed for starting

### 4.3 Typical CPP Wiring

```
CPP Switch Terminal 1 → C2 Green Pin 35 (CPP Signal, Gray wire)
CPP Switch Terminal 2 → Chassis Ground
```

**For swap applications:**
- If using an automatic transmission, these pins are unused and can be repurposed
- C2 Pin 35 can be set to ignore in the tune (transmission type = automatic)
- If you need a discrete digital input (on/off), C2 Pin 35 can be used as a switched ground input

### 4.4 Clutch Anticipate Switch (P01 reference)

On P01 (1999–2002) PCMs, the clutch anticipate switch is on **C1 Blue Pin 32**. The switch is normally closed (grounded when pedal released) and opens when clutch is depressed. The P01 uses this differently than the P59.

---

## 5. VSS (Vehicle Speed Sensor) Circuit

### 5.1 VSS Input Pins

| Connector | Pin | Signal | Wire Color | Circuit No. |
|-----------|-----|--------|------------|-------------|
| C2 Green | **20** | VSS Low Signal (Reference Low) | LT GRN/BLK | 822 |
| C2 Green | **21** | VSS High Signal | PPL/WHT | 821 |

### 5.2 VSS Output Pin

| Connector | Pin | Signal | Wire Color | Circuit No. |
|-----------|-----|--------|------------|-------------|
| C2 Green | **50** | VSS Output to Speedometer | DK GRN/WHT | 817 |

### 5.3 VSS Circuit Description

The VSS is a **2-wire magnetic (VR) sensor** on the transmission tailshaft (2WD) or transfer case (4WD). It generates an AC sine wave whose frequency is proportional to vehicle speed.

**Wiring:**
```
VSS Sensor Pin A → C2 Green Pin 20 (VSS Low)
VSS Sensor Pin B → C2 Green Pin 21 (VSS High)
```

- The PCM converts the raw AC signal to a digital pulse train and outputs it on **C2 Pin 50** for the speedometer, cruise control, and other modules
- The PCM can be calibrated for different tire sizes, gear ratios, and VSS pulse-per-mile settings
- Typical VSS resistance: 800–2000 ohms (varies by sensor)

### 5.4 4L80E Front VSS (ISS)

For 4L80E transmission swaps, the Input Speed Sensor (ISS) is wired to:

| Connector | Pin | Signal | Wire Color | Circuit No. |
|-----------|-----|--------|------------|-------------|
| C2 Green | **22** | AT ISS High Signal | RED/BLK | 1230 |
| C2 Green | **23** | AT ISS Low Signal | DK BLU/WHT | 1231 |

Note: On P01 PCMs (red/blue), these pins may be on the RED (C2) connector, Pins 22 and 23.

---

## 6. Complete Connector Pinouts

### 6.1 C1 BLUE Connector Pinout (2004 Truck - P59)

Source: lt1swap.com — 2004 4.8/5.3/6.0

| Pin | Wire Color | Circuit | Function | Notes |
|-----|------------|---------|----------|-------|
| 1 | BLK/WHT | 451 | PCM Ground | Required |
| 2 | LT GRN | 1867 | 12V Reference (CKP Sensor B+) | Required |
| 3 | PNK/BLK | 1746 | Fuel Injector 3 Control | Required |
| 4 | LT GRN/BLK | 1745 | Fuel Injector 2 Control | Required |
| 5 | -- | -- | **Not Used** | **Spare** |
| 6 | -- | -- | Not Used | Spare |
| 7 | GRY | 2705 | 5V Reference (Oil Pressure) | Removable |
| 8 | GRY | -- | 5V Reference (TPS Pin A, Cable TB Only) | Required (DBC) |
| 9 | -- | -- | Not Used | Spare |
| 10 | -- | -- | Not Used | Spare |
| 11 | LT BLU | 1876 | Knock Sensor 2 Signal | Required |
| 12 | DK BLU/WHT | 1869 | CKP Sensor Signal | Required |
| 13 | ORN/BLK | 463 | Requested Torque Signal (NW7) | Removable |
| 14 | ORN/BLK | 1061 | **A/C Pressure Sensor Signal** | Removable / **Spare ADC** |
| 15 | -- | -- | Not Used | Spare |
| 16 | -- | -- | Not Used | Spare |
| 17 | DK GRN | 890 | Fuel Tank Pressure Sensor Signal (EVA) | Removable |
| 18 | YEL | 410 | 5V Reference (ECT) | Required |
| 19 | PNK | 439 | Ignition 1 Voltage | Required |
| 20 | ORN | 440 | Battery Positive Voltage | Required |
| 21 | YEL | 1868 | CKP Sensor Low Reference | Required |
| 22 | BRN/WHT | 312 | Tachometer Signal | Required (blue) |
| 23 | PPL | 1672 | 5V Reference (APP Sensor 2) | Removable |
| 24 | LT BLU | 1673 | 5V Reference (APP Sensor 3) | Removable |
| 25 | TAN | 472 | IAT Sensor Signal | Required |
| 26 | PPL | 2121 | Ignition Coil 1 Control | Required |
| 27 | RED | 2127 | Ignition Coil 7 Control | Required |
| 28 | LT BLU/WHT | 2126 | Ignition Coil 6 Control | Required |
| 29 | DK GRN/WHT | 2124 | Ignition Coil 4 Control | Required |
| 30 | -- | -- | Not Used | Spare |
| 31 | YEL | 492 | MAF Sensor Signal | Required |
| 32 | LT GRN | 432 | MAP Sensor Signal | Required |
| 33 | -- | -- | Not Used | Spare |
| 34 | WHT | 776 | PRND P Input (A/T) | Removable |
| 35 | GRY | 48 | **CPP Switch Signal (M/T)** | ⭐ Manual trans |
| 36 | BLK | 1744 | Fuel Injector 1 Control | Required |
| 37 | YEL/BLK | 846 | Fuel Injector 6 Control | Required |
| 38 | PNK/WHT | 1101 | Damping Lift/Dive Signal | Removable |
| 39 | YEL/BLK | 625 | Starter Enable Relay Control | Removable / **Spare LSD** |
| 40 | BLK/WHT | 451 | PCM Ground | Required |
| 41 | -- | -- | **Not Used** | **Spare** (P01: EGR position ground) |
| 42 | -- | -- | Not Used — **ADD PIN FOR FAN 1 RELAY** | ⭐ **Spare LSD** |
| 43 | RED/BLK | 877 | Fuel Injector 7 Control | Required |
| 44 | LT BLU/BLK | 844 | Fuel Injector 4 Control | Required |
| 45 | GRY | 2700 | 5V Reference (A/C) | Removable |
| 46 | GRY | 474 | 5V Reference (EVA) | Removable |
| 47 | -- | -- | Not Used | Spare (P01: EGR 5V ref) |
| 48 | GRY | 416 | 5V Reference (MAP Sensor) | Required |
| 49 | PNK/BLK | 1748 | Fuel Injector 5 Control | Required |
| 50 | DK GRN/WHT | 465 | Fuel Pump Relay Control | Required (blue) |
| 51 | DK BLU | 496 | Knock Sensor 1 Signal | Required |
| 52 | GRY | 1786 | Park/Neutral Signal | Removable |
| 53 | BRN/WHT | 419 | MIL Control | Required |
| 54 | PNK/BLK | 1747 | Fuel Injector 8 Control | Required |
| **55** | **BRN** | **1456** | **EGR Pintle Position Sensor Signal** | ⭐ **WIDEBAND ADC INPUT** |
| **56** | GRY | 474 | **5V Reference (EGR)** | Removable / Power sensor |
| 57 | BLK | 552 | Low Reference (IAT) | Required |
| 58 | DK GRN | 335 | Low Reference (ECT) | Required |
| 59 | YEL | 450 | CAN Bus Serial Data (Export) | Removable |
| 60 | ORN/BLK | 451 | Low Reference (O2) | Required |
| 61 | TAN | 472 | Low Reference (Oil Level) | Removable |
| 62 | -- | -- | Not Used | Spare |
| 63 | BRN | 1174 | Oil Level Switch Signal | Removable |
| 64 | -- | -- | Not Used | Spare |
| 65 | TAN | 1669 | HO2S Low Signal Bank 1 Sensor 2 | Removable |
| 66 | PPL/WHT | 2128 | Ignition Coil 8 Control | Required |
| 67 | RED/WHT | 2122 | Ignition Coil 2 Control | Required |
| 68 | WHT | 1310 | ECT Sensor Signal | Required |
| 69 | DK GRN | 2125 | Ignition Coil 5 Control | Required |
| 70 | LT BLU | 2123 | Ignition Coil 3 Control | Required |
| 71 | -- | -- | Not Used | Spare |
| 72 | BLK/WHT | 3113 | HO2S Heater Low Control Bank 1 S1 | Required |
| 73 | -- | -- | Not Used | Spare |
| 74 | LT GRN | 3212 | HO2S Heater Low Control Bank 2 S1 | Required |
| 75 | GRY | 23 | Generator Field Duty Cycle Signal | Required |
| 76 | YEL | 447 | Generator Turn On Signal | Required |
| 77 | -- | -- | Not Used | Spare |
| 78 | -- | -- | Not Used | Spare |
| 79 | -- | -- | Not Used | Spare |
| 80 | -- | -- | Not Used | Spare |

> **Note:** Pin assignments may vary by vehicle platform (truck vs. Corvette vs. F-body). Always verify with a vehicle-specific service manual. The above is for a 2004 Truck calibration.

### 6.2 C2 GREEN Connector Pinout (2004 Truck - P59)

Source: lt1swap.com — 2004 4.8/5.3/6.0

| Pin | Wire Color | Circuit | Function | Notes |
|-----|------------|---------|----------|-------|
| 1 | BLK/WHT | 451 | PCM Ground | Required |
| 2 | BRN | 418 | TCC PWM Solenoid Valve Control (A/T) | Removable (M/T) |
| **3** | -- | -- | **Not Used** (EVAP Vent Solenoid) | ⭐ **Boost Control LSD** |
| 4 | -- | -- | Not Used | Spare |
| 5 | BLK | 464 | Low Reference (Trans Fluid Pressure, A/T) | Removable (M/T) |
| 6 | RED/BLK | 1228 | PC Solenoid Valve High Control (A/T) | Removable (M/T) |
| 7 | -- | -- | Not Used | Spare |
| 8 | LT BLU/WHT | 1229 | PC Solenoid Valve Low Control (A/T) | Removable (M/T) |
| 9 | DK GRN/WHT | 465 | Fuel Pump Relay Control | Required (blue) |
| 10 | WHT | 121 | Engine Speed Signal (Tach Output) | Required (blue) |
| 11 | -- | -- | Not Used | Spare |
| 12 | -- | -- | Not Used | Spare |
| 13 | -- | -- | Not Used | Spare |
| 14 | RED/BLK | 380 | A/C Refrigerant Pressure Sensor Signal | Removable |
| 15 | BRN | 25 | Charge Indicator Control | Removable |
| 16 | GRY/BLK | 1694 | 5V Reference (A/C) | Removable |
| 17 | -- | -- | Not Used | Spare |
| **18** | **DK GRN** | **1433** | **Clutch Start Switch Signal (M/T)** | ⭐ M/T start safety |
| 19 | BLK/WHT | 1695 | Low Reference (A/C) | Removable |
| **20** | **LT GRN/BLK** | **822** | **VSS Low Signal** | ⭐ Required |
| **21** | **PPL/WHT** | **821** | **VSS High Signal** | ⭐ Required |
| 22 | RED/BLK | 1230 | AT ISS High Signal (4WD MT1) | Removable |
| 23 | DK BLU/WHT | 1231 | AT ISS Low Signal (4WD MT1) | Removable |
| 24 | DK BLU | -- | Not Used | Spare |
| 25 | TAN | 472 | IAT Sensor Signal | Required |
| 26 | PPL | 2121 | IC 1 Control | Required |
| 27 | RED | 2127 | IC 7 Control | Required |
| 28 | LT BLU/WHT | 2126 | IC 6 Control | Required |
| 29 | DK GRN/WHT | 2124 | IC 4 Control | Required |
| 30 | -- | -- | Not Used | Spare |
| 31 | YEL | 492 | MAF Sensor Signal | Required |
| 32 | LT GRN | 432 | MAP Sensor Signal | Required |
| **33** | -- | -- | Not Used — **ADD PIN FOR FAN 2 RELAY** | ⭐ **Spare LSD** |
| 34 | WHT | 776 | PRND P Input (A/T) | Removable |
| **35** | **GRY** | **48** | **CPP Switch Signal (M/T)** | ⭐ Clutch pedal position |
| 36 | -- | -- | Not Used | Spare |
| 37 | -- | -- | Not Used | Spare |
| 38 | -- | -- | Not Used | Spare |
| 39 | RED | 631 | 12V Reference (CMP) | Required |
| 40 | BLK/WHT | 451 | PCM Ground | Required |
| 41 | -- | -- | Not Used | Spare |
| **42** | TAN/BLK | 422 | TCC Solenoid Control (M30/M32) | **Repurpose for Fan 1** |
| **43** | -- | -- | **A/C Compressor Clutch Relay Control** | Removable / Spare LSD |
| 44 | -- | -- | Not Used | Spare |
| 45 | -- | -- | Not Used | Spare |
| 46 | -- | -- | Not Used | Spare |
| 47 | YEL/BLK | 1223 | 2-3 Shift Solenoid Valve Control (A/T) | Removable (M/T) |
| 48 | LT GRN | 1222 | 1-2 Shift Solenoid Valve Control (A/T) | Removable (M/T) |
| 49 | -- | -- | Not Used | Spare |
| **50** | **DK GRN/WHT** | **817** | **VSS Output (to Speedometer)** | ⭐ Required |
| 51 | YEL/BLK | 1227 | TFT Sensor Signal (A/T) | Removable (M/T) |
| 52 | -- | -- | Not Used | Spare |
| 53 | -- | -- | Not Used | Spare |
| 54 | -- | -- | Not Used | Spare |
| 55 | -- | -- | Not Used | Spare |
| 56 | -- | -- | Not Used | Spare |
| 57 | BLK | 552 | Low Reference (IAT) | Required |
| 58 | -- | -- | Not Used | Spare |
| 59 | -- | -- | Not Used | Spare |
| 60 | BRN | 2129 | IC Reference Low Bank 1 | Required |
| 61 | BRN/WHT | 2130 | IC Reference Low Bank 2 | Required |
| 62 | GRY | 773 | Trans Range Switch Signal C (A/T) | Removable (M/T) |
| 63 | PNK | 1224 | Trans Fluid Pressure Switch A (A/T) | Removable (M/T) |
| **64** | GRY | 2705 | **Fuel Tank Pressure Sensor Signal** | ⭐ **Spare ADC #2** |
| 65 | -- | -- | Not Used | Spare |
| 66 | PPL/WHT | 2128 | IC 8 Control | Required |
| 67 | RED/WHT | 2122 | IC 2 Control | Required |
| 68 | DK GRN | 2125 | IC 5 Control | Required |
| 69 | LT BLU | 2123 | IC 3 Control | Required |
| 70 | -- | -- | Not Used | Spare |
| 71 | -- | -- | Not Used | Spare |
| 72 | BLK/WHT | 3113 | HO2S Heater Low Control Bank 1 S1 | Required |
| 73 | -- | -- | Not Used | Spare |
| 74 | LT GRN | 3212 | HO2S Heater Low Control Bank 2 S1 | Required |
| 75 | GRY | 23 | Generator Field Duty Cycle Signal | Required |
| 76 | -- | -- | Not Used | Spare |
| 77 | -- | -- | Not Used | Spare |
| 78 | -- | -- | Not Used | Spare |
| 79 | -- | -- | Not Used | Spare |
| 80 | -- | -- | Not Used | Spare |

> **Note:** C2 pinout above has been cross-referenced between multiple sources. Some pin functions may differ between truck, SUV, and Corvette applications. Pins marked "Not Used" on one application may have functions on others.

---

## 7. Key I/O Summary for Tuning Projects

### 7.1 Spare ADC Inputs (0–5V Analog)

| Pin | Stock Function | Best Use |
|-----|----------------|----------|
| **C1 Blue 55** | EGR Pintle Position | ⭐ Wideband O2 primary |
| **C2 Green 64** | Fuel Tank Pressure | ⭐ Wideband O2 secondary / Fuel pressure |
| C1 Blue 14 | A/C Pressure Signal | Wideband #3 / Boost pressure |
| C1 Blue 8 | TPS 5V Reference | Power external sensor |

### 7.2 Spare PWM / Low-Side Driver Outputs

| Pin | Stock Function | Best Use |
|-----|----------------|----------|
| **C2 Green 3** | EVAP Vent Solenoid | ⭐ Boost control solenoid |
| **C2 Green 42** | Unused / Fan 1 | ⭐ Fan 1 relay |
| **C2 Green 33** | Unused / Fan 2 | ⭐ Fan 2 relay |
| C2 Green 43 | A/C Clutch Relay | Spare LSD output |
| C1 Blue 39 | Starter Enable | Spare LSD output |

### 7.3 Manual Transmission Signals

| Pin | Signal | Function |
|-----|--------|----------|
| **C2 Green 35** | CPP Switch | Clutch pedal position (ground when depressed) |
| **C2 Green 18** | Clutch Start Switch | Safety start interlock |

### 7.4 Vehicle Speed Sensor

| Pin | Signal |
|-----|--------|
| **C2 Green 20** | VSS Low (Reference) |
| **C2 Green 21** | VSS High (Signal) |
| **C2 Green 50** | VSS Output (to speedometer) |

### 7.5 P01 → P59 Migration Notes

When upgrading from P01 (1999–2002, Red/Blue) to P59 (2003–2007, Blue/Green):

| Function | P01 (Red/Blue) | P59 (Blue/Green) | Action |
|----------|---------------|------------------|--------|
| Generator Field Duty | Red C2 Pin 52 | Green C2 Pin 75 | Move wire |
| Generator Turn On | Red C2 Pin 75 | Blue C1 Pin 76 | Move wire |
| EGR Position Signal | Blue C1 Pin 55 | Blue C1 Pin 55 | Same pin |
| CPP Switch | Red C2 Pin 35 | Green C2 Pin 35 | Same pin number |
| VSS Low | Red C2 Pin 20 | Green C2 Pin 20 | Same pin number |
| VSS High | Red C2 Pin 21 | Green C2 Pin 21 | Same pin number |
| Fan 1 Relay | Red C2 Pin 42 | Green C2 Pin 42 | Same pin number |
| O2 Heater Power | PCM triggers relay | PCM triggers relay | C2 pin-out differs |

---

## 8. Bench Harness / Programming Harness

For bench programming the P59 PCM:

| Pin | Signal | Notes |
|-----|--------|-------|
| C1 Blue 19 | PNK - Ignition 12V Switched | Key-on power |
| C1 Blue 20 | ORN - 12V Constant (Battery) | Always hot |
| C1 Blue 1, 40 | BLK/WHT - Ground | PCM grounds |
| C2 Green 1, 40 | BLK/WHT - Ground | PCM grounds |
| C1 Blue 59 | YEL - Class 2 Serial Data | J1850 VP+ (pin 2 of OBD2) |
| C1 Blue 60 | ORN/BLK - Ground | Also ground |

**OBD2 Connector:**
| OBD2 Pin | PCM Pin | 
|----------|---------|
| Pin 2 (J1850+) | C1 Blue 59 (YEL) |
| Pin 4/5 (Ground) | C1 or C2 Ground |
| Pin 16 (12V) | 12V constant |

---

## 9. References & Resources

1. **lt1swap.com** — 2004 Vortec PCM Pinouts: https://www.lt1swap.com/2004vortec_pcm.htm
2. **pcmhacking.net** — LS1 Boost OS V3: https://pcmhacking.net/forums/viewtopic.php?t=8172
3. **pcmhacking.net** — Boost OS Development Thread: https://pcmhacking.net/forums/viewtopic.php?t=7195
4. **pcmhacking.net** — P59 Pinouts Thread: https://pcmhacking.net/forums/viewtopic.php?t=9238
5. **24xracing.com** — P01 vs P59 DBC Pinout Comparison: https://www.24xracing.com/p01_vs_p59_DBC_Info.php
6. **ewaltsautotuning.com** — Standalone PCM Pinouts P01 & P59: https://www.ewaltsautotuning.com/standalone-pcm-pinouts-p01-p59
7. **corvetteforum.com** — Connecting Wideband via EGR or A/C Pressure: https://www.corvetteforum.com/forums/c5-scan-and-tune/1705471
8. **HP Tuners Forum** — PCM Pinout Diagram: https://forum.hptuners.com/showthread.php?9604
9. **pcmhacking.net** — RTLS1 Wiki (P59 addresses): https://pcmhacking.net/forums/viewtopic.php?t=8581
10. **ls1tech.com** — P59 PCM Schematic/Pinout Diagram: https://ls1tech.com/forums/pcm-diagnostics-tuning/1974674

---

## 10. Document Notes

- Pinouts are based primarily on the 2004 GM Truck (4.8L/5.3L/6.0L) calibration. Verify against your specific vehicle/OS.
- Corvette C5 P59 (2003–2004) uses the same Blue/Green connectors but pin assignments differ in several locations.
- P01 PCMs (1999–2002) use Red/Blue connectors and have different pinouts — included here only for migration reference.
- "Spare" pins marked "Not Used" may still have internal pull-ups/pull-downs or may be completely floating. Test before committing to use.
- Low-side drivers switch to ground — always wire the load between switched +12V and the PCM pin.
- Always use a relay for high-current devices (fans, fuel pumps). PCM low-side drivers are rated for ~0.5A–1A max.
