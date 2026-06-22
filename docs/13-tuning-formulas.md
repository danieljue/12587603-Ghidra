# P59 OS 12587603 — Tuning Formulas

> Conversion formulas for all calibration values
> Raw binary value → real-world engineering units

## RPM Scaling

| Formula | Range | Notes |
|---------|-------|-------|
| `RPM = raw / 5.12` | 0–12,500 RPM | Standard RPM scaling |
| `RPM = raw * 0.1953125` | | Same formula, different constant |
| `RPM = raw / 4` | 0–16,000 RPM | Some RPM tables use /4 |

**Example**: `$7C00` = 31744 raw → 31744/5.12 = **6200 RPM** (Corvette fuel cut)

## MAP (Manifold Pressure)

| Formula | Range | Notes |
|---------|-------|-------|
| `kPa = raw / 5.12` | 0–128 kPa | Factory MAP scaling |
| `kPa = raw * 0.1953125` | | Same |
| `PSI = kPa / 6.895` | | Boost gauge conversion |

**Example**: Factory 1-bar MAP sensor maxes at ~105 kPa (`$0358` raw)

## Spark Advance

| Formula | Notes |
|---------|-------|
| `Degrees = raw * 0.3515625 - 22.5` | Main spark tables (KA_MAIN_OT) |
| `Degrees = raw * 0.3515625` | Some spark modifiers |
| `Degrees = (raw - 128) * 0.3515625` | Signed spark values |

**Example**: `$50` = 80 raw → 80 * 0.3515625 - 22.5 = **5.6° BTDC**

## Volumetric Efficiency

| Formula | Units | Notes |
|---------|-------|-------|
| `VE = raw / 655.36` | gm*K/kPa | Standard VE scaling |
| `VE = raw * 0.0015258789` | | Same |

**Example**: `$8000` = 32768 raw → 32768/655.36 = **50.0 gm*K/kPa**

## Temperature (ECT, IAT)

| Formula | Range | Notes |
|---------|-------|-------|
| `°C = raw / 64 - 40` | -40 to 215°C | Standard temp scaling |
| `°F = °C * 9/5 + 32` | -40 to 419°F | Convert to Fahrenheit |

**Example**: `$5000` = 20480 raw → 20480/64 - 40 = **280°C** (overheat threshold)

## Throttle Position (TPS)

| Formula | Notes |
|---------|-------|
| `% = raw / 2.55` | Standard TPS scaling |
| `% = raw * 0.39215686` | Same |

**Example**: `$FF` = 255 raw → 255/2.55 = **100%**

## Vehicle Speed (VSS)

| Formula | Notes |
|---------|-------|
| `MPH = raw / 256` | Standard VSS scaling |
| `MPH = raw / 128` | Some vehicle speed tables |
| `KPH = MPH * 1.60934` | Convert to metric |

Raw VSS value at `FFFFAEC0` = frequency/period of VSS pulses.
Final speed = `(FFFFAEC0 * 0x19BE * 0x0D) / 0x14EAC` then `*2 / 0x9F`

## Fuel / AFR / Lambda

| Formula | Notes |
|---------|-------|
| `Lambda = raw / 65535` | EQ ratio to lambda |
| `AFR = Lambda * 14.7` | Lambda to AFR (gasoline) |
| `EQ Ratio = 65535 / raw` | Lambda to equivalence ratio |
| `ms = raw / 65536` | Millisecond pulse widths |
| `g/s = raw / 26214` | Injector flow rate scaling |

**Example**: `$8000` = 32768 raw → 32768/65535 = **0.50 Lambda** (7.35:1 AFR)

## Injector Constants

| Formula | Notes |
|---------|-------|
| `ms = raw / 65536` | Injector pulse width |
| `g/s = raw / 26214` | Injector flow rate |
| `ms = raw * 0.015259` | Injector offset |

## Mass Air Flow (MAF)

| Formula | Notes |
|---------|-------|
| `g/s = raw * 0.015259` | MAF sensor scaling |
| `Hz = raw * 0.390625` | MAF frequency |

## Knock Control

| Formula | Notes |
|---------|-------|
| `Degrees/V = raw / 91.022` | Knock retard attack rate |
| `Multiplier = raw / 65536` | Knock gain multipliers |

## Speed / Gear

| Byte | Meaning |
|------|---------|
| 0 | Park |
| 1 | Reverse |
| 2 | Neutral |
| 3 | Drive 4 (overdrive) |
| 4 | Drive 3 |
| 5 | Drive 2 |
| 6 | Manual 1 |
| 7 | Manual 2 |
| 8+ | Manual 3+ |

Gear stored at `FFFFA3AF`. Compare with `#5` to detect P/N (≤5) vs in-gear (>5).

## Fuel Cut Status

Byte at `FFFFA93C`:
- `0x00` — Fuel enabled (normal operation)
- `0x01` — Fuel cut by RPM limiter
- Other bits — various cut conditions (DFCO, VSS fail, etc.)

## Data Types in Calibration

| Type | Size | Signed | Range |
|------|------|--------|-------|
| BOOLEAN | 1 byte | No | 0 or 1 |
| CARDINAL | 2 bytes | No | 0–65535 |
| SHORTCARD | 1 byte | No | 0–255 |
| Degrees | 2 bytes | Yes | Varies |
| Percent | 1 byte | No | 0–255 (0–100%) |
| Seconds | 2 bytes | No | Varies (scaled) |
| RPM | 2 bytes | No | 0–12750 (scaled) |
| MPH | 2 bytes | No | Varies (scaled) |

## Common Raw Values

| RPM | Raw Value |
|-----|-----------|
| 6000 | $7800 (30720) |
| 6200 | $7C00 (31744) |
| 6500 | $81E0 (33248) |
| 6800 | $8800 (34816) |
| 7200 | $9000 (36864) |

| MAP (kPa) | Raw Value |
|-----------|-----------|
| 100 | $0320 (800) |
| 105 | $0348 (840) |
| 150 | $04B0 (1200) |
| 210 | $0690 (1680) |
| 300 | $0960 (2400) |

| Spark (°BTDC) | Raw Value (rounded) |
|---------------|---------------------|
| 0 | $40 (64) |
| 10 | $5D (93) |
| 20 | $79 (121) |
| 30 | $95 (149) |
| 40 | $B2 (178) |
