# P59 OS 12587603 — Flex Fuel System

> Traced from 68k disassembly — 2026-06-22

## Factory Flex Fuel Support

The P59 PCM has **built-in flex fuel capability** from the factory. It's disabled on non-flex-fuel vehicles via the calibration flag `KE_FLEX_FUEL_EQUIPPED` (0x00B7AC).

## Signal Chain

```
Flex Fuel Sensor → Frequency Output → TPU Capture → Frequency (Hz)
    ↓
Convert Hz → Ethanol Percentage (0-100%)
    ↓
FFFF8242: ethanol content (internal format)
    ↓
sub_2FAFC: calculate blend factors
    ↓
├── FFFF9FC4: stoich AFR (from KV_STOICHIOMETRIC_FUEL_AIR table)
├── FFFFAEF8: flex fuel composition factor
├── FFFF9FC6: open loop EQ blend factor
├── FFFF9FCE: calculated blend result
└── FFFF9FCC: stomp compensation limit
```

## Blend Factor Calculation (sub_2FAFC at 0x02FAFC)

```
Input:  FFFF8242 = ethanol content (internal format, 0-0x1000 range)
Output: FFFFAEF8 = composition factor (0-0x400 range)

Algorithm:
  d3 = FFFF8242 × 4 / 5        ← scale ethanol reading
  stoich_afr = tblu(KV_STOICHIOMETRIC_FUEL_AIR, d3)
  FFFF9FC4 = stoich_afr        ← updated stoich AFR for ethanol blend

  d3 = FFFF8242
  if d3 < 0x400:               ← < 25% ethanol
    d3 = d3 / 2
  elif d3 < 0x1000:            ← 25-100% ethanol
    d3 = (d3 - 0x400) / 6 + 0x200
  else:                        ← > 100% (clamped)
    d3 = 0x400
  FFFFAEF8 = d3                ← stored as composition factor

  open_loop_factor = tblu(KV_OPEN_LP_EQ_RATIO_BLEND_FACTOR, d3)
  FFFF9FC6 = open_loop_factor
```

## Key Calibrations

| Calibration | Address | Purpose |
|-------------|---------|---------|
| KE_FLEX_FUEL_EQUIPPED | 0x00B7AC | Enable/disable flex fuel |
| KV_STOICHIOMETRIC_FUEL_AIR | 0x00C7D4 | Stoich AFR vs ethanol % |
| KV_OPEN_LP_EQ_RATIO_BLEND_FACTOR | (cal) | Open loop EQ blend vs ethanol |
| B3103 Ethanol Default % | (cal) | Default ethanol % if sensor fault |
| B3104 Ethanol Max Frequency | (cal) | 155 Hz = sensor max |
| B3105 Ethanol Min Frequency | (cal) | 45 Hz = sensor min |

## Spark Interaction

The flex fuel composition factor (FFFFAEF8) feeds into:
- High/low octane spark table blending (more ethanol = closer to high octane)
- Knock control sensitivity adjustment
- FFS spark blend factor (sub_2FC1E uses it)

## Fuel Interaction

Ethanol content affects:
- Stoichiometric AFR (E10 = 14.1:1, E85 = 9.8:1)
- Injector flow rate (more ethanol = richer needed)
- Cold start enrichment
- Open loop EQ targets
- PE enrichment targets

## RAM Variables

| Address | Size | Description |
|---------|------|-------------|
| FFFF8242 | word | Ethanol content (internal format) |
| FFFF9FC4 | word | Calculated stoich AFR |
| FFFFAEF8 | word | Flex fuel composition factor |
| FFFF9FC6 | word | Open loop EQ blend factor |
| FFFF9FCE | word | Blend calculation result |
| FFFF9FCC | word | Stomp compensation limit |
| FFFFAEE0 | word | Additional blend input |

## What This Means for open12587603

Flex fuel does NOT require new code — the factory OS has complete support. To enable it:
1. Set `KE_FLEX_FUEL_EQUIPPED` = TRUE
2. Configure the flex fuel sensor frequency range
3. Set the stoich AFR table for ethanol blends
4. Connect the flex fuel sensor to the correct PCM input pin

Boost OS V4+ adds dual wideband + flex fuel — the flex fuel part is just enabling factory code, while the dual wideband requires new ADC processing code.
