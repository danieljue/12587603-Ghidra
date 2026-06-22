# P59 OS 12587603 — Calibration Table Reference (Extracted Values)

> Raw binary extraction — 2026-06-22
> Actual calibration values from the 2004 Corvette M6 stock binary
> `12587603-2004-Corvette-M6.bin` (1,048,576 bytes, MD5: 4205CE0B...)

---

## 1. Main VE Table

**Address:** 0x008442
**Size:** 680 bytes (17 rows × 20 columns × 2 bytes)
**Units:** gm·K/kPa
**Conversion:** raw_value / 655.36

```
Row 0 (lowest MAP):
  7.46  9.05  7.87  9.57  8.97  10.46  9.85  10.65  11.70  12.80
  14.11  14.63  15.73  15.93  16.96  18.13  18.96  18.44  18.13  19.66

Row 1:
  8.30  8.96  9.20  10.42  9.83  11.29  10.60  11.66  12.50  13.72
  15.00  15.74  16.73  17.02  18.25  19.21  20.08  19.80  18.78  20.48

Row 8 (mid-MAP):
  15.86  14.79  15.83  17.27  16.29  18.72  17.43  19.35  19.35  21.17
  23.20  24.85  26.05  27.09  29.19  30.72  32.14  32.24  31.50  32.91

Row 16 (highest MAP):
  29.81  29.44  29.76  29.52  29.41  30.07  30.85  31.71  31.42  31.90
  32.24  32.41  32.57  32.70  32.79  34.02  35.16  35.10  35.07  35.35
```

> Full 340-word table extracted. Values increase with MAP (down rows) and
> peak around 4000-5600 RPM (columns 10-16) where the LS1 makes peak torque.

---

## 2. High-Octane Spark Table

**Address:** 0x010890
**Size:** 680 bytes (17×20 word table — confirmed structure)
**Conversion:** GM spark formula `raw × 0.3515625 - 22.5` produces values
  outside expected range. Actual conversion factor TBD — values listed raw.

```
Raw values (0x0523-0x07xx range, monotonically increasing):
  [0]  0x0523   0x057A   0x05CC   0x0610   0x0650   0x0686   0x06B8   0x06E1   0x0706   0x0721
  [10] 0x0738   0x075C   0x076A   0x076E   0x076A   0x0761   0x0753   0x0745   0x073C   0x073C

Low-octane at 0x010E3A: identical structure, values match high-octane for
this region (Corvette M6 likely uses same table for both).
```

> **Note:** The spark table values increase from low RPM (left) to ~4800 RPM
> (column ~14) then decrease — classic spark table shape with MBT timing.
> The conversion to degrees needs verification against a known-good XDF.
> Typical LS1 spark is 18-30° at cruise, not 50-70°.

---

## 3. RPM Limiters

| Address | Label | Raw | Engineering | Description |
|---------|-------|-----|-------------|-------------|
| 0x09A82 | KV_ENGINE_SPEED_LIMIT | 0xB400 | 9000 RPM | ETC governor max (soft limiter) |
| 0x0BAE2 | KE_PN_ENGINE_OVERSPEED_HIGH | 0x7BFB | 6199 RPM | Fuel-cut entry |
| 0x0BAE0 | KE_PN_ENGINE_OVERSPEED_LOW | 0x7C00 | 6200 RPM | Fuel-cut re-enable |
| 0x09A96 | KE_ENGINE_OVERSPEED_LAMP | 0xB400 | 9000 RPM | Overspeed warning lamp |

**Conversion:** RPM = raw / 5.12

The 6200 RPM fuel cut is the effective redline. The 9000 RPM ETC governor
is a safety cap — actual rev limit is controlled by fuel cut.

---

## 4. Cooling Fan Thresholds

| Address | Label | Raw | Engineering | Description |
|---------|-------|-----|-------------|-------------|
| 0x1FA58 | KE_ECT_FAN1_HIGH_THRESHOLD | 0x0ACD | 108°C (226°F) | Fan1 ON |
| 0x1FA5A | KE_ECT_FAN1_LOW_THRESHOLD | — | — | Fan1 OFF (hysteresis) |
| 0x1FA78 | KE_ECT_FAN2_HIGH_THRESHOLD | 0x0B4D | 113°C (235°F) | Fan2 ON |
| 0x1FA7A | KE_ECT_FAN2_LOW_THRESHOLD | — | — | Fan2 OFF (hysteresis) |

**Conversion:** °C = raw / 25.6

---

## 5. Stoichiometric AFR Table

**Address:** 0x00C7D4
**Structure:** Ethanol content axis at 0xC7C0 (4 entries: 0x800, 0x800, 0x800, 0x800),
  data at 0xC7D4 (repeated 0x0117 = 279 decimal)
**Conversion:** AFR ≈ raw / 18.98 → 279/18.98 = 14.70

```
Ethanol %   Raw Stoich   AFR
    0%         0x0117     14.70
    (E10?)     0x0117     14.70
    (E85?)     0x0117     14.70
```

> The stock Corvette M6 is not flex-fuel capable (KE_FLEX_FUEL_EQUIPPED
> likely = FALSE). All ethanol rows show the same 14.70 value — E0 gasoline.

---

## 6. AC System Calibrations

| Address | Label | Raw | Engineering | Description |
|---------|-------|-----|-------------|-------------|
| 0x1F842 | KE_TYPE_OF_AC_ON_VEHICLE | 0x02 | Type 2 | Standard AC with pressure sensor |
| 0x1F846 | KE_AC_STATUS_INPUT_EQUIPPED | 0x01 | TRUE | Clutch feedback wired to PCM |
| 0x1F85C | KE_AC_ENGINE_SPEED_LOWER_LIMIT | 0x5AE6 | 4,545 RPM | Enable AC below this |
| 0x1F85E | KE_AC_ENGINE_SPEED_UPPER_LIMIT | 0x61E6 | 4,895 RPM | Disable AC above this |

---

## 7. COT Temperature Thresholds

| Address | Label | Raw | Description |
|---------|-------|-----|-------------|
| 0x08E7A | KE_COT_TEMPERATURE_LOW | 0x5300 | Level 1 threshold |
| 0x08E7C | KE_COT_TEMPERATURE_MEDIUM | 0x5400 | Level 2 threshold |
| 0x08E7E | KE_COT_TEMPERATURE_HIGH | 0x5500 | Level 3 — hot determination |
| 0x08E80 | KE_COT_TEMPERATURE_EXTREME | 0x5C00 | Level 4 — maximum |

**Conversion:** Internal units. Temperature scaling factor not yet confirmed.

---

## 8. EGR Configuration

| Address | Label | Raw | Description |
|---------|-------|-----|-------------|
| 0x09458 | KE_EGR_ENABLED | 0x00 | DISABLED (Corvette M6) |

---

## 9. Shift Light Configuration

| Address | Label | Raw | Description |
|---------|-------|-----|-------------|
| 0x10174 | KE_EXECUTE_UPSHIFT_LIGHT_ALGORIT | 0x00 | DISABLED |
| 0x10175 | KE_CONTROL_UPSHIFT_LIGHT | 0x00 | Class 2 message (not direct output) |

---

## 10. Idle RPM Targets

**Address range:** 0x8500-0x8600 area
**Conversion:** RPM = raw / 5.12

```
Approximate idle targets (ECT-dependent table):
  Cold:    1304 → 1452 → 1573 → 1662 RPM
  Warm:    1422 → 1501 → 1595 → 1684 RPM
  Hot:     1501 → 1579 → 1532 → 1569 RPM
```

Corvette M6 idles at ~700-800 RPM hot. These values appear to be the
target RPM adder or a different table — the actual commanded idle
includes IAC compensation.

---

## 11. Segment Header Data

**Boot sector (0x000500):**
```
Operating System Checksum:  0xD2E80001
Calibration Segment Checksum: 0x00C01253
Operating System Level ID:  0x44430000
```

**OSID string "12587603"** stored at address **0x08A7CA** (ASCII).

---

## 12. Key Binary Parameters

| Parameter | Value |
|-----------|-------|
| Binary size | 1,048,576 bytes (1 MB) |
| MD5 | 4205CE0BFA308E4C0658F077898931D0 |
| CRC32 | 33B42E60 |
| Processor | 68330 (CPU32) |
| Vehicle | 2004 Corvette M6 (Y-body, manual) |
| OS ID | 12587603 |
| VIN | (stored in calibration segment) |

---

## 13. Injector Pulse Width / Offset Table

**Address range:** 0x00C010-0x00C0BC
**Structure:** 6 rows × 11 columns (word table)
**Units:** ms (raw / 1000)
**Conversion:** pulse_width_ms = raw / 1000

```
Row 0 (lowest MAP?):  5.73  5.73  5.73  5.73  5.73  5.63  5.12  4.43  3.73  3.04  2.42 ms
Row 1:                 5.73  5.73  5.73  5.73  5.73  5.63  5.12  4.43  3.73  3.04  2.42 ms
Row 2:                 5.73  5.73  5.73  5.73  5.73  5.63  5.12  4.43  3.73  3.04  2.42 ms
Row 3:                 5.73  5.73  5.73  5.73  5.73  5.63  5.12  4.43  3.73  3.04  2.42 ms
Row 4:                 5.73  5.73  5.73  5.73  5.73  5.63  5.12  4.43  3.73  3.04  2.42 ms
Row 5:                 5.73  5.73  5.73  5.73  5.73  5.63  5.12  4.43  3.73  3.04  2.42 ms
```

> All rows identical — likely an injector offset (dead time) table that
> varies only by voltage (rows = voltage, columns = MAP). The 5.73 ms max
> is high for a dead time; may be minimum pulse width or IFR correction.

**Second table at 0xC0CE-0xC0FE (11×2?):**
```
Row 0: 4.08  4.07  4.07  4.07  4.06  4.06  4.04  3.99  4.01  4.02  4.00 ms
Row 1: 3.95  3.85  3.44  2.76  (incomplete)
```

## 14. MAF Calibration Table

**Address:** 0x00F85A
**Label:** KV_MASS_AIRFLOW
**Units:** g/s (raw conversion TBD — likely raw / 256 or similar)

```
Raw values (monotonically increasing):
  [ 0] 0x00BD  [ 1] 0x00E6  [ 2] 0x0110  [ 3] 0x013F  [ 4] 0x0172
  [ 5] 0x01AA  [ 6] 0x01E7  [ 7] 0x022B  [ 8] 0x0274  [ 9] 0x02C5
  [10] 0x031C  [11] 0x0379  [12] 0x03DD  [13] 0x0448  [14] 0x04BA
  [15] 0x0531  [16] 0x05B0  [17] 0x0639  [18] 0x06CD  [19] 0x076D
```

> MAF transfer function: frequency (Hz) → mass airflow (g/s). The raw
> values increase with frequency. Conversion factor needs XDF verification.

## 15. After-Start Enrichment

**Address range:** 0x00B800-0x00B9FE
**Units:** seconds (raw / 1000 for timers, raw / 65536 for multipliers)

```
Decay timer table at 0xB8A6 (8 entries, ECT-dependent):
  Cold: 28.8  19.2  13.6  8.0  5.6  4.0  2.2  1.6 sec
  Hot:   1.6  1.6  1.6  1.6  1.6  1.6  1.6  1.6 sec

Decay multiplier at 0xB8CC:
  0xFA00 = 0.977 (near 1.0 — minimal multiplier for warm engine)
```

> After-start enrichment decays exponentially from initial value over the
> calibrated duration. Hot engines get 1.6s decay, cold engines up to 28.8s.

## 16. Extraction Methodology

All values extracted using Python `struct.unpack_from(">H", data, addr)`
(big-endian 16-bit unsigned). Conversions verified against known GM
scaling factors where available:

- RPM: raw / 5.12
- Temperature: raw / 25.6
- VE: raw / 655.36
- Duty cycle: raw / 51.2 (0-100% mapped to 0-0x1400)
- AFR / EQ ratio: raw / 65536 or raw / 18.98 (varies by parameter)

> **Caution:** Some parameters use different scaling. Always cross-reference
> with a known-good XDF before modifying calibrations.
