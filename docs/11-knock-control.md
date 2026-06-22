# P59 OS 12587603 — Knock Control & Sensor Signal Chains

> Traced from 68k disassembly — 2026-06-22

---

## 1. Knock Control System

### Architecture Overview
```
Knock Sensor → Bandpass Filter (Hardware?) → ADC → Knock_Energy
                                                      ↓
                                              sub_3BDC4: Compare vs threshold
                                                      ↓
                                              If knock detected:
                                                Fast retard: immediately pull timing
                                                Slow recovery: gradually restore
                                                      ↓
                                              sub_3B3DA: Limit total retard
```

### Key Functions

| Function | Address | Purpose |
|----------|---------|---------|
| sub_3BDC4 | 0x03BDC4 | Launch spark + knock energy calculation |
| sub_3B3DA | 0x03B3DA | Spark advance/retard limiter |
| sub_3C68C | 0x03C68C | Called by sub_3BDC4 (knock sub-function) |
| sub_39F12 | 0x039F12 | Base spark from high/low octane tables |

### RAM Variables

| Address | Size | Meaning |
|---------|------|---------|
| FFFFB292 | word | Knock sensor signal / knock energy |
| FFFFB37A | byte | Knock detection mode / HVS flag |
| FFFFAEE6 | word | Knock retard load index |
| FFFF9400 | word | Knock retard accumulator |
| FFFF9844 | word | Dynamic spark modifier (added to max advance/retard) |
| FFFF9853 | byte | Spark retard active flag |
| FFFF9884 | word | Knock retard accumulation value |

### Knock Detection (sub_3BDC4 analyzed)

At line 180153+. Reads FFFFAD23 (cylinder mode = 3 for launch spark), FFFFAC47 (cylinder index), FFFFB292 (knock energy). Uses table lookups with calibrations:

```
KA_KNOCK_ENERGY_MAD      — knock threshold vs RPM×load
KA_KNOCK_ENERGY_MAD_GAIN — threshold gain
SPARK_KNOCK_KV_TIP_IN_KNOCK_ENERGY_MAD — tip-in knock threshold
```

Logic:
1. If cylinder mode != 3: use integrated knock energy path
2. If cylinder mode = 3: use launch spark / individual cylinder knock path
3. Read FFFFB292 (knock sensor energy)
4. RPM (FFFFA562) → scaled index
5. Lookup threshold from calibration tables
6. Compare energy vs threshold → determine knock
7. Apply launch spark modifier if enabled

### Spark Retard Limiter (sub_3B3DA traced)

```
Input:  d0 = current spark advance (degrees, scaled)
        FFFF9400 = accumulated retard value
        FFFFAEE6 = load index for table lookup
Output: d0 = limited spark advance
        FFFF9884 = updated retard accumulator

Algorithm:
  1. d2 = tbls(SPARK_ADVANCE_KV_LIMIT_MAX_RETARD, FFFFAEE6)
  2. If HVS mode (FFFFB37A):
     d4 = SPARK_ADVANCE_KE_LIMIT_MAX_ADVANCE + FFFF9844, clamp to ±0xAAB
     d5 = SPARK_ADVANCE_KE_HVS_MAX_RETARD + FFFF9844
     d2 = max(d2, d5)
  3. d0 = clamp(d0, d2, d4)  // between max retard and max advance
  4. If d0 < d2: FFFF9884 = FFFF9400 + d2 - d0  (accumulate retard)
     If d0 >= d2: FFFF9884 = FFFF9400 (reset accumulator)
  5. If retarding: FFFF9853 = 1 (retard active)
     If not: FFFF9853 = 0 (retard inactive)
```

### Knock Recovery

Fast attack: `KV_KNOCK_FAST_IR_ATTACK_RATE` — how fast to pull timing when knock detected
Fast recovery: `KV_KNOCK_FAST_RECOVER_RATE` — how fast to restore timing after knock ends

Both are tables indexed by RPM, found near 0x014942 and 0x0149CA.

---

## 2. MAP Sensor Signal Chain

### Hardware

The P59 uses a 1-bar MAP sensor (GM part). Factory scaling:

| Parameter | Address | Stock Value | Units |
|-----------|---------|-------------|-------|
| KE_MAP_SENSOR_SCALE_FACTOR | 0x0195B8 | 0x12E3 | kPa/Count |
| KE_MAP_SENSOR_OFFSET | 0x0195BA | 0x0211 | kPa |

### Signal Flow
```
MAP Sensor → Analog Voltage (0-5V) → QADC → ADC Count (0-255)
    ↓
kPa = ADC_Count × SCALE_FACTOR + OFFSET
    ↓
Internal format → stored directly by hardware at FFFFADB6
    ↓                                  ↑
Read by: sub_30368 (fuel cut) ← Hardware register (QADC result)
         sub_79B10 (VE lookup)
         Various diagnostic functions
```

### Key Discovery: FFFFADB6 is a hardware-mapped register

`FFFFADB6` is NEVER written by main loop code — only READ. This means it's:
- A QADC (Queued ADC) result register, OR
- A TPU-captured value from a MAP sensor input channel

The MC68336 QADC result registers are auto-updated by hardware when conversions complete. The CPU reads them but doesn't write them.

### Internal MAP Format

In sub_30368 (fuel-cut limiter), MAP from FFFFADB6 is processed:
```
d4 = FFFFADB6
d4 = clamp(d4, 0x0DFF, 0xFC00)    // Clamp to valid range
d4 = d4 + 0x0400                    // Add offset
d4 = (d4 × 256) / 0x0133           // Scale by 256/307
tblu.w(cold_engine_table, d4)      // Table lookup
```

The scaling `×256 / 0x133` suggests FFFFADB6 is in units of kPa × (some scaling factor) and this converts it to a table index.

---

## 3. MAF Sensor Signal Chain

### Signal Flow
```
MAF Sensor → Frequency Output → TPU Capture → Frequency (Hz)
    ↓
sub_80A78: Convert frequency to airflow (grams/sec)
    ↓
FFFFAC82 ← MAF airflow (grams/sec)
FFFFAC86 ← Same value (when VSS valid)
```

### Processing (sub_80A78)
```
1. Read MAF frequency from TPU
2. d3 = MAF_freq - 0xC00  (subtract offset)
3. d3 = tblu(KV_MASS_AIRFLOW, d3)  // Table lookup: Hz → g/s
4. Store result at FFFFAC82, FFFFAC86 (if VSS valid)
```

---

## 4. RPM Signal Chain

### Source
Crankshaft position sensor (58x or 24x reluctor wheel) → VR sensor → TPU input capture

### Processing
The TPU (Time Processor Unit) measures time between crank pulses and converts to RPM. The result is stored at `FFFFA562` as raw RPM (RPM × 5.12).

### Conversion
```
RPM_engineering = FFFFA562 / 5.12
RPM_engineering = FFFFA562 × 0.1953125
```

PID 0x000C confirms: `move.w (FFFFA562).w, d0` then `mulu.w #$19, d0; lsr.l #5, d0` to convert to OBD-II format.

---

## 5. Temperature Sensors (ECT, IAT)

### Hardware
NTC thermistors — resistance varies with temperature. PCM applies a pull-up resistor and reads voltage via ADC.

### Processing
ADC count → lookup table → temperature (°C internal format)
Internal format: `temp = °C × 64 + 2560` (to be verified)

### Calibration Tables
- Temperature sensor calibration table (ADC counts → degrees)
- Located in calibration section (address TBD from CSV)

---

## 6. Complete RAM Variable Reference (Updated)

| Address | Size | Category | Meaning |
|---------|------|----------|---------|
| FFFFA562 | word | RPM | Engine speed (raw = RPM × 5.12) |
| FFFFADB6 | word | MAP | Manifold pressure (hardware ADC result) |
| FFFFAC86 | word | MAF | Mass airflow (grams/sec, from MAF) |
| FFFFAC82 | word | MAF | Same as AC86 (backup?) |
| FFFFAEC0 | word | VSS | Vehicle speed (raw frequency period) |
| FFFFA3AB | byte | Trans | Clutch switch state (processed) |
| FFFFA3AF | byte | Trans | Gear position |
| FFFFA3B8 | byte | Trans | Transmission type/gear index |
| FFFF93F1 | byte | Input | Clutch switch raw (GPIO) |
| FFFFA93C | byte | Fuel | Fuel cut status |
| FFFFA936 | byte | Fuel | DFCO active flag |
| FFFFA0D6 | word | Airflow | VE lookup result |
| FFFFA0CC | word | Airflow | Calculated air per cylinder |
| FFFFB292 | word | Knock | Knock sensor energy |
| FFFFB37A | byte | Knock | HVS / knock mode flag |
| FFFFAEE6 | word | Knock | Knock load index |
| FFFF9400 | word | Knock | Knock retard accumulator |
| FFFF9884 | word | Knock | Knock retard value |
| FFFF9853 | byte | Knock | Spark retard active |
| FFFF9844 | word | Spark | Dynamic spark modifier |
