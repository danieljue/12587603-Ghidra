# P59 OS 12587603 — VE Table Lookup Axis Scaling

> Traced from 68k disassembly — 2026-06-22
> Critical for VE expansion feature

## VE Table Structure

| Parameter | Value |
|-----------|-------|
| Address | 0x00008442 |
| Rows (pressure axis) | 17 |
| Columns (RPM axis) | 20 |
| Element size | 2 bytes (word, unsigned) |
| Stride per row | 0x28 = 40 bytes |
| Total size | 680 bytes |
| Units | gm·K/kPa |
| Conversion | raw / 655.36 |

## Row Axis (Pressure)

The VE table row axis is the **barometric-referenced manifold pressure** stored at **FFFFB292**.

### Data Flow
```
MAP Sensor → ADC (FFFFF2BC) → sub_807E0:
  kPa_internal = (ADC × 0x12E3) / 65536 + 0x0211
  → stored at FFFFB296 (MAP kPa, ×51.2 format)

Baro Reference:
  FFFFF2BA → sub_8093C (same formula) → FFFFB292

VE Lookup:
  d1 = FFFFB292 (baro/MAP, internal format)
  d1 = min(d1, 0x300)     ← clamp to minimum
  d1 = d1 - 0x300           ← subtract base offset
  → d1 becomes row index with fraction in low byte
```

### Internal Pressure Format

The pressure value at FFFFB292/FFFFB296 is stored as:
```
internal = kPa × 51.2  (approximate — 1 LSB ≈ 0.0195 kPa)
```

### Row Index Preparation

```
d1 = FFFFB292 (baro pressure, internal format)
d1 = clamp_to_min(d1, 0x300)
d1 = d1 - 0x300          ; subtract base (0x300 = ~6 kPa)

Row 0 = 0x300 (minimum pressure ≈ 6 kPa)
Row 16 = 0x300 + 16 × Δ (maximum pressure ≈ 100+ kPa)

The step Δ between rows yields the fractional part for interpolation.
```

## RPM Axis (Column)

```
d0 = FFFFA562 (RPM, raw: RPM × 5.12)
d0 = clamp(d0, 0x800, 0xA000)    ; 400–8000 RPM
d0 = d0 - 0x800                   ; subtract base (400 RPM)
d0 = d0 >> 3                      ; shift for column index
```

Column 0 = 400 RPM
Column 19 = 8000 RPM

Each column step is 400 RPM = 2048 raw units.
After >>3: 2048/8 = 256 = 0x100 per column.
The upper byte of d0 contains the integer column; the lower byte is the interpolation fraction.

## VE Lookup in sub_79B10

There are TWO VE table lookups in sub_79B10:

### Lookup 1 (at +0x82 from function start)
```
d1 = FFFFA0D0  ← set from FFFFB292 (baro/MAP)
d0 = FFFFA562  ← RPM
d2 = 0x28      ← stride
a0 = &VE_TABLE ← 0x00008442
→ sub_16D6(a0, d0, d1, d2)
→ result stored at FFFFA0D6
```

### Lookup 2 (at +0x530 from function start)
```
Same setup, different operating mode (steady-state detection)
```

### Boost OS Hooks
Boost OS patches BOTH lookups with JSR to the VE expansion routine:
- 0x079B92 → JSR 0x0D0558 (lookup 1)
- 0x07A176 → JSR 0x0D0558 (lookup 2)
- 0x07A95E → JSR 0x0D0558 (lookup 3 — third VE reference)

## Boost OS VE Expansion Logic

From reverse-engineering the Boost OS routine at 0x0D0558:

```
VE_Expansion:
    read d1 = MAP/baro value

    if d1 > 0x28FF:       ← very high MAP (probably 200+ kPa)
        a0 = &expanded_VE_high (0x0E069A)
    elif d1 > 0x11FF:     ← moderate MAP (probably 100+ kPa)
        a0 = &expanded_VE_mid (0x0E000A)
    else:                 ← normal MAP (< 100 kPa)
        a0 = &factory_VE (0x0008442)
    rts
```

The exact kPa thresholds depend on the internal format. Approximate:
- 0x11FF / 46.07 ≈ 100 kPa (atmospheric)
- 0x28FF / 46.07 ≈ 227 kPa (approx 18 psi boost)

## For VE Expansion Implementation

To build our own VE expansion, we need to:

1. Read d1 (the pressure row index) in our hook routine
2. Compare against a boost threshold
3. If in boost: set a0 to the expanded VE table, adjust d2 (stride) if the expanded table has different dimensions
4. If not in boost: set a0 to the factory VE table, keep d2 = 0x28
5. Return — sub_16D6 will use the new a0 and d2 for the lookup

The expanded VE table should have:
- More pressure rows (for higher MAP values)
- Same or different RPM columns
- New stride value matching the new column count
