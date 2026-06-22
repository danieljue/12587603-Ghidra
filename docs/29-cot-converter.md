# P59 OS 12587603 — COT / Catalytic Converter Over-Temp Protection

> Traced from 68k disassembly — 2026-06-22
> COT protects the catalytic converter from meltdown by enriching the fuel
> mixture when the predicted catalyst temperature exceeds calibrated thresholds.
> It uses a predictive temperature model based on airflow, RPM, vehicle speed,
> spark retard, and equivalence ratio.

---

## 1. Overview

Catalytic converter over-temperature protection (COT) is safety-critical. If
the catalyst substrate exceeds ~900-1000°C, it can melt, causing:
- Complete catalyst failure (P0420/P0430)
- Exhaust restriction and power loss
- Vehicle fire risk in extreme cases

The P59 predicts catalyst temperature from indirect inputs (airflow, RPM,
vehicle speed, spark, EQ ratio) rather than using a physical temperature
sensor. The model estimates a "stabilized temperature" based on stoichiometric
conditions, then applies offsets for current operating conditions.

When the predicted temperature exceeds one of four thresholds (Low, Medium,
High, Extreme), COT enriches the fuel mixture to cool the catalyst. The
enrichment is additive — it layers on top of normal closed-loop or PE
fueling, with configurable minimum and maximum EQ ratio limits.

**On the 2004 Corvette M6:** COT is enabled (KE_COT_HOT_DETERMINATION_ENABLE = 1).
The four temperature thresholds are calibrated around 0x5300-0x5C00 (internal
units, need scaling factor).

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_7BC70 | 0x07BC70 | 295112 | Main COT temperature prediction and enrichment — called from DoLoopG+12A |
| sub_276D4 | 0x0276D4 | — | Timer utility used for COT delay timing |
| sub_316EA | 0x0316EA | — | PE enrichment with COT hysteresis interaction |

---

## 3. Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                    COT TEMPERATURE MODEL                               │
│                                                                        │
│  DoLoopG ──▶ sub_7BC70                                                 │
│               │                                                        │
│               ├─ State check: FFFFAD23 == 3? (engine running)          │
│               │                                                        │
│               ├─ Input Capture:                                         │
│               │   TPS → FFFFAB66                                       │
│               │   Airflow → FFFFA0DC → FFFFACB2                        │
│               │   RPM → FFFFA562 → FFFFACBE                            │
│               │                                                        │
│               ├─ Update Timing:                                         │
│               │   If TPS ≤ KE_COT_THROTTLE_CLOSED AND                  │
│               │      airflow drop ≥ KE_COT_AIRFLOW_DELTA:              │
│               │     → Delay update (KE_COT_TEMPERATURE_DELAY_TIME)     │
│               │   If TPS ≥ KE_COT_THROTTLE_OPENED:                     │
│               │     → Immediate update                                 │
│               │                                                        │
│               ├─ Stabilized Temperature Base:                           │
│               │   From KA_COT_TEMPERATURE_STOICH_STABLE table          │
│               │   Indexed by EQ ratio and airflow/RPM                  │
│               │                                                        │
│               ├─ Temperature Offsets (additive):                        │
│               │   + KV_COT_VEH_SPEED_TEMP_OFFSET[VSS]                  │
│               │   + KV_COT_DFCO_TEMPERATURE_OFFSET (during DFCO)       │
│               │   + KV_COT_RETARDED_SPARK_OFFSET[spark_retard]         │
│               │   + KV_COT_EQ_RATIO_TEMP_OFFSET[EQ_ratio]              │
│               │   × KV_COT_BARO_MULTIPLIER (barometric correction)     │
│               │   × KV_COT_FFS_MULTIPLIER (ethanol composition)        │
│               │                                                        │
│               ├─ Filtering:                                             │
│               │   If temp increasing:                                   │
│               │     filter = KV_COT_INC_TEMPERATURE_FILTER_CO          │
│               │     × KV_COT_INC_COEF_TEMP_DELTA_MULT                  │
│               │   If temp decreasing:                                   │
│               │     If NOT rich (EQ < limit):                           │
│               │       filter = KV_COT_DEC_TEMPERATURE_FILTER_CO        │
│               │     If rich: use KE_COT_DEC_TEMP_FILTER_RICH_RATE      │
│               │                                                        │
│               ├─ Initialization:                                        │
│               │   Power-up soak temp from KV_COT_INITIAL_TEMP_SOAK_MULT│
│               │   If coolant > KE_COT_TEMPERATURE_COOL_THRESHOL:       │
│               │     Initialize to KE_COT_TEMPERATURE_INITIAL           │
│               │                                                        │
│               └─ Threshold Comparison:                                  │
│                   LEVEL 1: temp > KE_COT_TEMPERATURE_LOW               │
│                     → Mild enrichment, EQ limited by MIN/MAX           │
│                   LEVEL 2: temp > KE_COT_TEMPERATURE_MEDIUM            │
│                     → Increased enrichment                             │
│                   LEVEL 3: temp > KE_COT_TEMPERATURE_HIGH              │
│                     → Heavy enrichment                                 │
│                     → If > HIGH for KE_COT_HOT_TIME_THRESHOLD:         │
│                       HOT determination set                            │
│                   LEVEL 4: temp > KE_COT_TEMPERATURE_EXTREME           │
│                     → Maximum enrichment                               │
│                                                                        │
│  Output: COT EQ ratio offset → added to fuel calculation              │
│          Limited between KE_COT_MIN_EQ_ALLOWED and KE_COT_MAX_EQ_ALLOWED│
│          FFFFACAA ← COT active flag (read by CCP, PE logic)            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

### 4.1 Temperature Filters (0x8B22-0x8B4C)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08B22 | KV_COT_INC_TEMPERATURE_FILTER_CO | table | — | 0-1 | Filter coef when temp increasing |
| 0x08B4C | KV_COT_DEC_TEMPERATURE_FILTER_CO | table | — | 0-1 | Filter coef when temp decreasing (normal) |

### 4.2 Temperature Offsets (0x8B76-0x8BEE)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08B76 | KV_COT_DFCO_TEMPERATURE_OFFSET | table | — | °C | Temp offset during DFCO |
| 0x08B88 | KV_COT_EQ_RATIO_TEMP_OFFSET | table | — | °C | Temp offset vs EQ ratio |
| 0x08BAA | KV_COT_FFS_MULTIPLIER | word | 0x1000 | Scaler 1 | Ethanol composition multiplier |
| 0x08BB4 | KV_COT_INITIAL_TEMP_SOAK_MULT | word | 0x800 | Scaler_2 | Soak timer modifier at powerup |
| 0x08BC2 | KV_COT_RETARDED_SPARK_OFFSET | table | — | °C | Temp offset vs spark retard |
| 0x08BD8 | KV_COT_VEH_SPEED_TEMP_OFFSET | table | — | °C | Temp offset vs vehicle speed |
| 0x08BEA | KE_COT_TEMPERATURE_COOL_THRESHOL | word | 0x800 | °C | Coolant above which uses init temp |
| 0x08BEC | KE_COT_TEMPERATURE_INITIAL | word | 0x2800 | °C | Initial temp at startup (if coolant hot) |
| 0x08BEE | KA_COT_TEMPERATURE_STOICH_STABLE | table | — | °C | Stabilized temp at stoich (base) |

### 4.3 Update Timing (0x8E64-0x8E76)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08E64 | KE_COT_THROTTLE_OPENED | word | 0x100 | Percent | TPS ≥ this → immediate update |
| 0x08E66 | KE_COT_THROTTLE_CLOSED | word | 0x9A | Percent | TPS ≤ this → airflow determines timing |
| 0x08E68 | KE_COT_AIRFLOW_DELTA | word | 0xC00 | gm/S | Airflow drop threshold for delay |
| 0x08E6A | KE_COT_TEMPERATURE_DELAY_TIME | word | 0x320 | Seconds | Overrun delay duration |
| 0x08E6C | KE_COT_EQ_RATIO_DEC_FILTER_LIMIT | word | 0x40A | Equiv_Ratio | EQ below which uses normal dec filter |
| 0x08E6E | KE_COT_DEC_TEMP_FILTER_RICH_RATE | word | 0x1800 | 0-4 | Rich-condition decreasing filter rate |
| 0x08E70 | KE_COT_HOT_DETERMINATION_ENABLE | byte | 1 | BOOLEAN | Enable hot determination logic |
| 0x08E72 | KE_COT_HOT_TIME_THRESHOLD | word | 0x640 | Seconds | Time above HIGH to set HOT flag |
| 0x08E74 | KE_COT_1PERCENT_TIME_THRESHOLD | word | 0x1680 | Seconds | 1% timer threshold |
| 0x08E76 | KE_COT_1PERCENT_CYCLE_TIME | long | — | Seconds | 1% cycle time period |

### 4.4 Temperature Thresholds (0x8E7A-0x8E84)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08E7A | KE_COT_TEMPERATURE_LOW | word | 0x5300 | °C (scaled) | Level 1 — lowest threshold |
| 0x08E7C | KE_COT_TEMPERATURE_MEDIUM | word | 0x5400 | °C (scaled) | Level 2 |
| 0x08E7E | KE_COT_TEMPERATURE_HIGH | word | 0x5500 | °C (scaled) | Level 3 — hot determination |
| 0x08E80 | KE_COT_TEMPERATURE_EXTREME | word | 0x5C00 | °C (scaled) | Level 4 — maximum |

### 4.5 Enrichment Limits (0x8E82-0x8E9C)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x08E82 | KE_COT_MIN_EQ_ALLOWED | word | 0x41A | Equiv_Ratio | Min EQ that COT will command |
| 0x08E84 | KE_COT_MAX_EQ_ALLOWED | word | 0x500 | Equiv_Ratio | Max EQ authority for COT |
| 0x08E86 | KV_COT_BARO_MULTIPLIER | table | — | 0-2 | Barometric pressure multiplier |
| 0x08E90 | KV_COT_INC_COEF_TEMP_DELTA_MULT | table | — | 0-1 | Delta-temp multiplier on inc filter |
| 0x08E9C | KV_COT_EQ_RATIO_OFFSET | table | — | Equiv_Ratio | EQ ratio offset vs temperature |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFACB8 | word | sub_7BC70+14 | Current TPS (from FFFFAB66) |
| FFFFACB2 | word | sub_7BC70+1A | Current airflow (from FFFFA0DC) |
| FFFFACB4 | word | sub_7BC70+3C | Previous airflow (for delta calc) |
| FFFFACBE | word | sub_7BC70+22 | Current RPM (from FFFFA562) |
| FFFFACC4 | word | sub_7BC70+56 | COT update delay timer |
| FFFFACB0 | word | sub_7BC70+D8 | DFCO temperature offset accumulator |
| FFFFACAA | byte | sub_7BC70 / CCP doc | COT active flag (1 = enriching for COT) |
| FFFFAB66 | word | sub_7BC70+E | Throttle position |
| FFFFA0DC | word | sub_7BC70+16 | Mass airflow |
| FFFFA562 | word | sub_7BC70+1E | Engine RPM |
| FFFFAD23 | byte | sub_7BC70+A | Operating state |
| FFFF984A | word | sub_7BC70+8E | Spark-related — possibly net spark advance |
| FFFF9842 | word | sub_7BC70+92 | Spark-related — base or modifier |
| FFFFAEBC | word | sub_7BC70+96 | Vehicle speed |
| FFFFA93A | byte | sub_7BC70+BC | DFCO active flag |
| FFFF9848 | word | sub_7BC70+FA | Spark retard value (for offset lookup) |
| FFFFB544 | word | sub_7BC70+56 | System timer |

---

## 6. Algorithm Detail

### 6.1 Temperature Prediction Model

The COT temperature prediction runs each DoLoopG cycle (100ms loop):

```
1. Capture inputs:
   TPS → FFFFACB8
   Airflow → FFFFACB2
   RPM → FFFFACBE

2. Update timing decision:
   IF TPS ≤ KE_COT_THROTTLE_CLOSED:
     IF (previous_airflow - current_airflow) ≥ KE_COT_AIRFLOW_DELTA:
       → Delay update (overrun/decel condition — exhaust cooling)
     ELSE:
       → Continue with update
   IF TPS ≥ KE_COT_THROTTLE_OPENED:
     → Immediate update (engine under load)

3. Stabilized temperature base:
   Lookup KA_COT_TEMPERATURE_STOICH_STABLE[EQ_ratio]
   This gives the steady-state catalyst temperature at stoichiometric AFR.

4. Apply offsets:
   VSS offset = KV_COT_VEH_SPEED_TEMP_OFFSET[vehicle_speed]
   DFCO offset = KV_COT_DFCO_TEMPERATURE_OFFSET[RPM] (if DFCO active)
   Spark offset = KV_COT_RETARDED_SPARK_OFFSET[spark_retard]
   EQ offset = KV_COT_EQ_RATIO_TEMP_OFFSET[EQ_ratio]
   Total = base + VSS + DFCO + spark + EQ

5. Apply multipliers:
   Total ×= KV_COT_BARO_MULTIPLIER[baro]
   Total ×= KV_COT_FFS_MULTIPLIER (ethanol composition)

6. Filter:
   IF total > previous_filtered:
     filter_coef = KV_COT_INC_TEMPERATURE_FILTER_CO ×
                   KV_COT_INC_COEF_TEMP_DELTA_MULT[|total - prev_1s|]
   ELSE:
     IF EQ_ratio < KE_COT_EQ_RATIO_DEC_FILTER_LIMIT:
       filter_coef = KV_COT_DEC_TEMPERATURE_FILTER_CO (normal)
     ELSE:
       filter_coef = KE_COT_DEC_TEMP_FILTER_RICH_RATE (rich — faster cooling)
   filtered = prev + (total - prev) × filter_coef

7. Startup initialization:
   IF just powered up:
     IF coolant > KE_COT_TEMPERATURE_COOL_THRESHOL:
       Initialize to KE_COT_TEMPERATURE_INITIAL
     ELSE:
       Initialize from soak model with KV_COT_INITIAL_TEMP_SOAK_MULT
```

### 6.2 Enrichment Response

```
Level 1: predicted_temp > KE_COT_TEMPERATURE_LOW
  → COT_EQ_offset = KV_COT_EQ_RATIO_OFFSET[predicted_temp]
  → Final EQ = base_EQ + COT_EQ_offset
  → Clamped to [KE_COT_MIN_EQ_ALLOWED, KE_COT_MAX_EQ_ALLOWED]

Level 2: predicted_temp > KE_COT_TEMPERATURE_MEDIUM
  → Larger EQ offset (separate table region)
  → More aggressive cooling

Level 3: predicted_temp > KE_COT_TEMPERATURE_HIGH
  → If KE_COT_HOT_DETERMINATION_ENABLE:
    Start hot timer
    If temp stays above HIGH for KE_COT_HOT_TIME_THRESHOLD:
      Set HOT determination = TRUE
  → Heavy enrichment
  → May reduce CCP purge flow (KE_CCP_COT_MULTIPLIER applied)

Level 4: predicted_temp > KE_COT_TEMPERATURE_EXTREME
  → Maximum enrichment
  → Force open loop with rich target
  → May trigger DTC for catalyst damage

1% cycle logic:
  If temp above KE_COT_1PERCENT_TIME_THRESHOLD:
    Count cycles
    If cycles > KE_COT_1PERCENT_CYCLE_TIME:
      → Catalyst may be damaged — set diagnostic flag
```

### 6.3 Interaction with PE and CCP

COT enrichment takes priority over normal fuel control:
- During COT, PE entry thresholds may be bypassed (COT enrichment IS PE)
- CCP purge flow is reduced: final_purge ×= KE_CCP_COT_MULTIPLIER
  (purge vapors are additional fuel — reducing them helps cool catalyst)
- The COT active flag (FFFFACAA) is read by sub_2D1C4 (CCP) and sub_316EA (PE)

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoopG | Calls sub_7BC70 each 100ms cycle |
| Fuel System (doc 07) | COT EQ offset added to base fueling |
| PE Mode | COT overrides/replaces PE enrichment at high temps |
| CCP/EVAP (doc 23) | COT reduces purge flow via KE_CCP_COT_MULTIPLIER |
| DFCO (doc 10) | DFCO offsets catalyst temp (cooling effect) |
| Spark Control | Spark retard increases exhaust temp → COT model |
| DTC/MIL (doc 18) | Catalyst damage DTCs from overtemp |
| Ethanol | FFS multiplier compensates for different exhaust temps |

---

## 8. Gaps & Unresolved

1. **Temperature scaling factor**: The internal temperature units (0x5300 =
   ~850°C?) need verification. The conversion from raw calibration values to
   degrees Celsius requires finding the scaling factor in the code.

2. **1% cycle logic detail**: The "1% cycle" diagnostic that tracks how long
   the catalyst spends in overtemp and sets cumulative damage flags needs
   full tracing from sub_7BC70+342-416.

3. **Soak model at powerup**: The initial temperature estimation when the
   engine has been off (soak timer) uses KV_COT_INITIAL_TEMP_SOAK_MULT but
   the exact multiplier application is not traced.

4. **EQ offset table structure**: KV_COT_EQ_RATIO_OFFSET is applied as a
   function of predicted temperature, but the precise lookup mechanism
   (which axes, how many breakpoints) is not documented.

5. **Spark retard interaction**: The COT model adds a spark retard offset
   (KV_COT_RETARDED_SPARK_OFFSET) because retarded spark increases exhaust
   temperature. The exact spark value used as the index comes from FFFF9848
   which needs verification.

---

## 9. How To Verify

```bash
# Verify COT enabled and threshold values
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_COT_HOT_DETERMINATION_ENABLE @ 0x08E70: {data[0x08E70]:02X} (1=enabled)')
print(f'KE_COT_TEMPERATURE_LOW @ 0x08E7A: 0x{int.from_bytes(data[0x08E7A:0x08E7C],\"big\"):04X}')
print(f'KE_COT_TEMPERATURE_HIGH @ 0x08E7E: 0x{int.from_bytes(data[0x08E7E:0x08E80],\"big\"):04X}')
print(f'KE_COT_TEMPERATURE_EXTREME @ 0x08E80: 0x{int.from_bytes(data[0x08E80:0x08E82],\"big\"):04X}')
"
```

```bash
# Verify sub_7BC70 called from DoLoopG
grep -n "sub_7BC70" 12587603-2004-Corvette-M6.sanitized.asm | grep "DoLoopG\|CODE XREF"
```

---

## 10. Community Knowledge

- **COT delete**: Some tuners disable COT (set KE_COT_HOT_DETERMINATION_ENABLE = 0
  and max out thresholds). This is DANGEROUS on forced induction — boost
  dramatically increases EGTs and can melt catalysts in seconds at WOT.

- **COT and aftermarket cats**: High-flow aftermarket catalytic converters have
  different thermal characteristics. The stock COT temperature model may not
  protect them correctly. Tuners often adjust the thresholds after measuring
  actual EGTs with a thermocouple.

- **Turbo applications**: The turbine housing acts as a heat sink, reducing EGT
  before the catalyst. The stock COT model overestimates catalyst temperature
  on turbo cars, causing unnecessary enrichment. Tuners add a scaling factor
  or raise thresholds.

- **COT vs PE**: COT enrichment can override PE enrichment. If you see richer-
  than-expected AFR at WOT that doesn't match your PE table, COT may be active.
  Check FFFFACAA flag in logs.
