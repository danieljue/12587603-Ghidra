# P59 OS 12587603 — Verified RAM Address Map

> Traced from LegacyNsfw's 936,975-line disassembly on 2026-06-22
> All addresses verified against actual 68k code

## Engine Sensors

| Address | Size | Description | Verified |
|---------|------|-------------|----------|
| FFFFA562 | word | Current engine RPM | PID 0x000C reader |
| FFFFADB6 | word | MAP / engine load (scaled) | sub_30368 fuel-cut |
| FFFFAEC0 | word | VSS raw (frequency/period) | PID 0x000D Speed in KPH |
| FFFFA3AF | byte | Gear position (0-7, >5=in gear) | sub_30368+34 |
| FFFFA3B8 | byte | Transmission gear/type index | sub_30368+3C |
| FFFF93F1 | byte | Clutch switch raw (GPIO input) | sub_83986 |
| FFFFA3AB | byte | Clutch switch state (processed) | sub_3090C+C |
| FFFFA3AC | byte | Transmission switch / CPP state | sub_30566+76 |

## Fuel Cut / Limiter

| Address | Size | Description | Verified |
|---------|------|-------------|----------|
| FFFFA93C | byte | Fuel cut status (0=normal, !=0=cut) | sub_30368+8 |
| FFFFA93E | byte | Cold engine protection flag | sub_30368+60 |
| FFFF8998 | byte | VSS fail / brake flag (bit 1) | sub_30368+6E |
| FFFF899C | byte | VSS fail / brake flag (bit 1) | sub_30368+76 |
| FFFF899A | byte | VSS fail / brake flag (bit 1) | sub_30368+7A |

## DFCO / Clutch

| Address | Size | Description | Verified |
|---------|------|-------------|----------|
| FFFFA936 | byte | DFCO / fuel cut active | sub_3090C+66 |
| FFFFA938 | byte | DFCO condition | sub_30566 |
| FFFFA946 | word | Delta RPM for DFCO exit | sub_3090C |
| FFFFA948 | word | Current RPM (stored) | sub_30566 |
| FFFFA94A | word | Previous RPM | sub_30566 |
| FFFFA94C | word | Throttle decrease counter | sub_30566 |
| FFFFA952 | word | Clutch DFCO timer | sub_30566 |
| FFFFA954 | word | DFCO timer | sub_30566 |
| FFFFA958 | word | Clutch DFCO hold time (loaded cal) | sub_30566 |
| FFFFA95A | word | Clutch DFCO re-enable delay (loaded) | sub_30566 |
| FFFFA95C | word | Clutch DFCO counter | sub_3090C |
| FFFFA95E | word | Throttle window counter | sub_30566 |
| FFFFA960 | word | Engine run time snapshot | sub_3090C |
| FFFFA962 | byte | Previous clutch state | sub_3090C+6C |
| FFFFA963 | byte | DFCO active flag | sub_3090C+C |
| FFFFA96B | byte | CPP transition flag | sub_30566+76 |
| FFFFA96C | byte | DFCO hold active | sub_30566 |

## Launch Control (Factory)

| Address | Size | Description | Verified |
|---------|------|-------------|----------|
| FFFFAD23 | byte | Cylinder mode trigger (=3 for launch spark) | sub_3BDC4 |
| FFFFAC47 | byte | Cylinder index | sub_3BDC4 |
| FFFFAEEA | word | Spark retard / knock energy | sub_3BDC4+40 |
| FFFFFB292 | word | Knock sensor input | sub_3BDC4+70 |

## Spark Calculation

The factory has existing launch spark logic in `sub_3BDC4` with calibrations:
- SPARK_ADVANCE_KA_LAUNCH_SPARK — launch spark table
- SPARK_ADVANCE_KE_LAUNCH_SPARK_MINRUNSOAKENABLE — min run time
- SPARK_ADVANCE_KE_LAUNCH_SPARKRPMRUNTIME — min RPM runtime
- SPARK_ADVANCE_KV_FFS_SPARK_BLEND_FACTOR — flat foot shift blend

## Key Functions

| Function | Address | Purpose |
|----------|---------|---------|
| sub_30368 | 0x030368 | Fuel-cut RPM limiter |
| sub_30566 | 0x030566 | Clutch DFCO / launch condition detection |
| sub_3090C | 0x03090C | DFCO entry/exit logic |
| sub_3BDC4 | 0x03BDC4 | Launch spark / knock energy calculation |

## Boost OS Strategy

Boost OS V3.4 likely:
1. Enables factory launch control via calibrations (not new code)
2. Hooks VE lookup (3 JSR patches) → redirects to expanded table
3. Adds boost spark adder table — needs hook into spark chain (TBD)
4. Adds wideband CL flag — needs fuel trim hook (TBD)
5. Adds boost cut scalars — needs MAP check hook (TBD)

The VE expansion (item 2) IS new code — the factory can't handle MAP > 105 kPa.
But everything else may just be calibration changes on existing logic.
