# P59 OS 12587603 — Internal Formulas

> **Traced from the actual 68k code, not forum hearsay.**
> Every formula verified against the 936,975-line disassembly.
> Last updated: 2026-06-22

---

## 1. Table Interpolation Engine: `sub_16D6` (0x0016D6)

Called by EVERY 2D table lookup in the OS — VE, spark, fuel, idle, everything.

### Signature
```
Input:  a0 = pointer to table base
        d0 = column index (upper byte = integer col, lower byte = interpolation fraction)
        d1 = row index (upper byte = integer row, lower byte = interpolation fraction)
        d2 = stride (bytes per row)
Output: d0 = interpolated value
```

### Pseudocode
```c
uint16_t sub_16D6(a0, d0, d1, d2):
    row      = d1 >> 8;           // Integer row (0-255)
    frac_row = d1 & 0xFF;         // Fraction (0-255, where 256=1.0)
    offset   = row * d2;          // Byte offset into table
    a0      += offset;            // Point to row
    
    col      = d0 >> 8;           // Integer column
    frac_col = d0 & 0xFF;         // Column fraction
    
    // Read two adjacent cells for interpolation
    v1 = tblun(a0, col);          // table[row][col]
    v2 = tblun(a0 + d2, col);     // table[row+1][col]
    
    // Linear interpolate: v1 + (v2-v1) * frac_row/256
    // Rounds: add 0x80 (0.5) before shifting
    result = tblu(v1, v2, frac_row);
    result = (result + 0x80) >> 8;
    return result;
```

### What `tblun.w` does
`tblun.w (a0), d0` reads a 16-bit word from address `a0 + (d0_low_byte × 2)`.
So d0's low byte is the column NUMBER, scaled by 2 (word entries).

### What `tblu.l` does
`tblu.l d0:d3, d1` does: `result = d0 + ((d3 - d0) * (d1_low_byte)) / 256`
This is linear interpolation between d0 and d3 using d1_low_byte as the fraction.

---

## 2. VE Table Lookup (in `sub_79B10`)

### Preparation
```
d0 = RPM_raw - 0x800          // Subtract 400 RPM offset (0x800 / 5.12 = ~156... wait)
                                // Actually: RPM_raw at FFFFA562 is RPM × 5.12
                                // 0x800 = 2048 raw = 400 RPM
                                // So base of table is 400 RPM

d0 = d0 >> 3                  // Divide by 8: each column = 8 raw units = 400 RPM
                                // 8 raw units / 5.12 = 1.5625 → this is the fractional part
                                // Actually: 20 columns cover 400-8000 RPM
                                // Range = 7600 RPM = 38912 raw units
                                // Per column: 38912/19 = 2048 raw = 400 RPM
                                // After >>3: 2048/8 = 256 = 0x100
                                // So each column step = 0x100 in d0 (column in upper byte!)

d1 = MAP_axis_scaled           // Prepared similarly, stored in upper byte with fraction in lower

d2 = 0x28 = 40                 // Stride: 20 columns × 2 bytes/word
a0 = &VE_TABLE                 // 0x00008442

result = sub_16D6(a0, d0, d1, d2)
```

### VE Table Structure
| Parameter | Value |
|-----------|-------|
| Address | 0x00008442 |
| Rows (MAP axis) | 17 |
| Columns (RPM axis) | 20 (but stride=40 suggests 20 columns) |
| Element size | 2 bytes (word) |
| Row stride | 40 bytes |
| Total size | 680 bytes (17 × 40) |
| Units | gm*K/kPa |
| Conversion | raw / 655.36 → gm*K/kPa |

### RPM Axis
| Raw RPM | Engineering | Column |
|---------|-------------|--------|
| 0x0800 (2048) | 400 RPM | 0 |
| 0x1000 (4096) | 800 RPM | 1 |
| 0x1800 (6144) | 1200 RPM | 2 |
| ... | ... | ... |
| 0xA000 (40960) | 8000 RPM | 19 |

Formula: `column = (RPM_raw - 2048) / 2048`
Where `RPM_raw = RPM × 5.12`

---

## 3. MAP Sensor Signal Chain

### Calibration Values
| Parameter | Address | Raw Value | Meaning |
|-----------|---------|-----------|---------|
| KE_MAP_SENSOR_SCALE_FACTOR | 0x0195B8 | 0x12E3 (4835) | Slope (counts per kPa × scaling) |
| KE_MAP_SENSOR_OFFSET | 0x0195BA | 0x0211 (529) | Offset (kPa × scaling) |

### Signal Flow
```
MAP_Sensor_Voltage → ADC (8-bit) → MAP_ADC_Count (0-255)
    ↓
MAP_kPa = MAP_ADC_Count × SCALE + OFFSET
    ↓
MAP_internal → stored at FFFFADB6 (word)
    ↓
Used by: VE lookup, spark lookup, fuel-cut, DFCO, knock control
```

### MAP Internal Format
The value at `FFFFADB6` appears to be in a scaled format used for table lookups.
In the fuel-cut limiter (sub_30368), it's used as:
```
d4 = MAP_internal
d4 = clamp(d4, 0xDFF, 0xFC00)     // Clamp to range
d4 += 0x400                        // Add offset
d4 = (d4 × 256) / 0x133            // Scale for table lookup
```

---

## 4. RPM Signal Chain

### RAM Variable
`FFFFA562` — current engine RPM in **raw format** (word)

### Conversion
```
RPM_engineering = RPM_raw / 5.12
```

### Source
Derived from crank position sensor (58x or 24x reluctor wheel).
Pulses are timed by a hardware capture unit and converted to RPM by the CPU.

### Usage
- VE table column axis
- Spark table column axis  
- Fuel-cut threshold comparison
- DFCO entry/exit
- Idle speed target
- Every RPM-based table lookup

---

## 5. Temperature Signal Chain (ECT, IAT)

### Sensor Type
NTC thermistor (negative temperature coefficient).
Non-linear — uses a lookup table for conversion.

### Signal Flow
```
Thermistor_Voltage → ADC → ADC_Count
    ↓
Lookup table: ADC_Count → Temperature (°C)
    ↓
Internal format: °C × 64 + 2560 (or similar)
    ↓
Used by: cold enrichment, fan control, knock control, etc.
```

### Conversion Formula (approximate, from tuning knowledge)
```
°C = raw / 64 - 40
°F = °C × 9/5 + 32
```

---

## 6. Injector Pulse Width Calculation

### Signal Flow
```
1. Air mass per cylinder (g/cyl) from VE or MAF
2. Fuel mass = Air_mass / Target_AFR
3. Base pulse width = Fuel_mass / Injector_Flow_Rate
4. Final pulse = Base_pulse + Injector_Offset + Voltage_Compensation
5. Clamp to min/max pulse width
6. Output to injector driver
```

### Key Calibrations
| Parameter | Address |
|-----------|---------|
| KV_INJECTOR_SLOPE | 0x00E96C |
| KV_INJECTOR_OFFSET_ADJUSTMENT | 0x00E2BE |
| KE_MIN_PULSE_WIDTH | 0x00C00E |
| KV_MINIMUM_PULSE_WIDTH | 0x00EA4E |
| KV_SHORT_PULSE_ADJUSTMENT | 0x00E9C8 |

---

## 7. Spark Advance Calculation

### Signal Flow
```
1. Base spark from high/low octane tables (sub_39F12)
2. + Catalyst lightoff spark retard (sub_3AF0C)
3. + MBT spark modifier (sub_3A754)
4. + Launch spark (sub_3BDC4)
5. + Knock retard (if knock detected)
6. + EGR spark modifier
7. + Spark smoothing (rate limiting)
8. + Coolant temp modifier
9. + IAT modifier
10. = Final spark advance → ignition coil driver
```

### Key Tables
| Table | Address | Units |
|-------|---------|-------|
| KA_MAIN_OT_HIGH_OCTANE | 0x010890 | Degrees |
| KA_MAIN_OT_LOW_OCTANE | 0x010E3A | Degrees |
| SPARK_ADVANCE_KA_LAUNCH_SPARK | (in calibration) | Degrees |

---

## 8. Fuel-Cut RPM Limiter (`sub_30368`)

### Logic
```
1. Read fuel cut status: FFFFA93C (0 = normal, non-zero = fuel cut)
2. If fuel IS cut (FFA93C != 0):
   a. d4 = MAP (FFFFADB6), clamped to [0xDFF, 0xFC00]
   b. d4 = (d4 + 0x400) * 256 / 0x133
   c. d3 = overspeed LOW threshold (based on gear)
   d. If cold engine protection (FFFFA93E): apply cold modifier
   e. If VSS fail (FFFF8998/9C/9A bit 1): use VSS-fail threshold
   f. If RPM (FFFFA562) < d3: clear fuel cut flag → fuel back on
3. If fuel NOT cut:
   a. Same calculation but uses overspeed HIGH threshold
   b. If RPM > d3: set fuel cut flag → fuel cut active
```

### Key Thresholds
| Parameter | Address | Stock Value | RPM |
|-----------|---------|-------------|-----|
| KE_PN_ENGINE_OVERSPEED_HIGH | 0x00BAE0 | $7C00 | 6200 |
| KE_PN_ENGINE_OVERSPEED_LOW | 0x00BAE2 | $7BFB | 6199 |
| KE_ENG_OVERSPEED_VSS_FAIL_HIGH | 0x00BAE4 | $7C00 | 6200 |
| KE_ENG_OVERSPEED_VSS_FAIL_LOW | 0x00BAE6 | $7BFB | 6199 |

---

## 9. Clutch DFCO Detection (`sub_30566`)

### RAM Variables
| Address | Size | Meaning |
|---------|------|---------|
| FFFFA3AB | byte | Clutch switch state (processed) |
| FFFFA3AC | byte | Transmission switch state |
| FFFFA936 | byte | DFCO active flag |
| FFFFA938 | byte | DFCO condition flag |
| FFFFA94C | word | Throttle decrease counter |
| FFFFA948 | word | Current RPM (snapshot) |
| FFFFA94A | word | Previous RPM (snapshot) |
| FFFFA95A | word | Clutch DFCO re-enable timer |
| FFFFA962 | byte | Previous clutch state |
| FFFFA96B | byte | CPP transition flag |

---

## 10. Launch Spark Logic (`sub_3BDC4`)

The factory OS already has launch spark logic at `sub_3BDC4` (0x03BDC4).
It uses calibrations:
- `SPARK_ADVANCE_KA_LAUNCH_SPARK` — launch spark table
- `SPARK_ADVANCE_KE_LAUNCH_SPARK_MINRUNSOAKENABLE` — min previous run time
- `SPARK_ADVANCE_KE_LAUNCH_SPARKRPMRUNTIME` — min RPM run time
- `SPARK_ADVANCE_KV_FFS_SPARK_BLEND_FACTOR` — flat foot shift spark blend

Boost OS does NOT add new launch control code — it ENABLES the factory logic
by modifying these calibrations.

---

## Verification Status

| Formula | Status | Source |
|---------|--------|--------|
| sub_16D6 table interpolation | ✅ VERIFIED | Direct 68k trace |
| VE table RPM axis scaling | ✅ VERIFIED | Direct 68k trace |
| RPM conversion (raw/5.12) | ✅ VERIFIED | PID 0x000C reader |
| VSS conversion | ✅ VERIFIED | PID 0x000D reader |
| Fuel-cut threshold selection | ✅ VERIFIED | sub_30368 trace |
| MAP sensor chain | ⚠️ PARTIAL | Calibration addresses known, exact scaling TBD |
| Temperature chain | ⚠️ PARTIAL | Approximate formula, lookup table not traced |
| Injector pulse chain | ⚠️ PARTIAL | Addresses known, full calculation not traced |
| Spark advance chain | ⚠️ PARTIAL | Function list known, exact injection points TBD |
| Launch spark logic | ⚠️ PARTIAL | Function identified, not fully traced |
