# P59 OS 12587603 — Injector Timing / EOIT (End of Injection Timing)

> Traced from 68k disassembly — 2026-06-22
> EOIT controls when in the engine cycle fuel injection completes. Proper
> timing ensures fuel enters the cylinder during the intake stroke rather
> than puddling on a closed intake valve. Affects idle quality, emissions,
> and fuel economy.

---

## 1. Overview

End of Injection Timing (EOIT) determines the crankshaft angle at which the
injector pulse finishes. The PCM calculates injection timing in units of
"low-resolution periods" (lores periods) — each lores period corresponds to
one crank sensor low-resolution pulse (every 90° on a V8).

The injection event is timed backward from the boundary angle:
1. **Boundary**: A reference crankshaft angle (typically aligned with intake
   valve opening or a fixed offset from TDC)
2. **EOIT Target**: How many lores periods after the boundary injection
   should end
3. **Pulse Width**: Calculated from the fuel mass requirement (doc 07)
4. **Start of Injection** = EOIT_target - pulse_width

The system has separate EOIT targets for:
- Normal operation (coolant-temperature dependent)
- Cranking (fixed target)
- Desoot mode (separate target)
- Engine protection mode (separate trim)

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_32738 | 0x032738 | 161720 | EOIT calculation — selects target based on operating mode |
| sub_327CA | 0x0327CA | 161799 | Boundary offset application |
| sub_7989E | 0x07989E | — | Injector output scheduling finalization |
| sub_32A0C | 0x032A0C | — | Injector output scheduling (calls sub_327CA) |

---

## 3. Data Flow

```
┌───────────────────────────────────────────────────────────────────┐
│                    EOIT CALCULATION                               │
│                                                                   │
│  sub_32738 (EOIT Target Selection)                                │
│    │                                                              │
│    ├─ Operating Mode Selection:                                   │
│    │   Cranking: KV_END_OF_INJECTION_CRANK_TARGET[ECT]           │
│    │   Desoot: KE_DESOOT_EOIT (fixed)                             │
│    │   Engine Protection: trim from KE_ENG_PROTECTION_TRIM_EOIT  │
│    │   Normal: KV_NORMAL_END_OF_INJECTION_COOLA[ECT]             │
│    │                                                              │
│    ├─ Custom OS check (FFFFB27C):                                 │
│    │   Flag indicates custom OS active (Boost OS, etc.)           │
│    │   → Uses custom EOIT tables if set                           │
│    │                                                              │
│    └─ Coolant temp index: ECT → scaled → table lookup            │
│                                                                   │
│  sub_327CA (Boundary + Output)                                    │
│    │                                                              │
│    ├─ KE_BOUNDARY_OFFSET: base boundary in lores periods         │
│    │   Stock: 0x680 = 1664 (units need conversion)                │
│    │                                                              │
│    ├─ EOIT = boundary + target                                    │
│    │   Normal target from KV_NORMAL_END_OF_INJECTION_COOLA       │
│    │   Plus trim from KV_TRIM_END_OF_INJECTION_COOLANT[ECT]     │
│    │                                                              │
│    └─ Output → sub_7989E → injector driver hardware              │
│                                                                   │
│  Timing Chain:                                                    │
│    CAM sensor → TDC reference point                               │
│    CKP sensor → lores pulse every 90°                             │
│    EOIT boundary = TDC + KE_BOUNDARY_OFFSET × 90°                 │
│    End of injection = boundary + EOIT_target × 90°                │
│    Start of injection = EOIT_target - PW_to_degrees(pulse_width) │
└───────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters (FUEL_IO module)

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x0E276 | KE_BOUNDARY_OFFSET | word | 0x680 | Lores_Periods | Base boundary angle offset |
| 0x0E27C | KV_NORMAL_END_OF_INJECTION_COOLA | table | 0x28D | Lores_Periods | Normal EOIT vs coolant temp |
| 0x0E29C | KV_TRIM_END_OF_INJECTION_COOLANT | table | 0x58D | Lores_Periods | EOIT trim vs coolant temp |
| 0x0E70F | KE_USE_CRANK_EOIT | byte | — | BOOLEAN | Use crank EOIT instead of desoot EOIT |
| 0x0E710 | KE_DESOOT_EOIT | word | — | Lores_Periods | EOIT during desoot mode |
| 0x0E712 | KV_END_OF_INJECTION_CRANK_TARGET | table | 0 | Lores_Periods | EOIT during cranking vs ECT |
| — | KE_ENG_PROTECTION_TRIM_END_OF_IN | word | — | Lores_Periods | EOIT trim during engine protection |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFADB0 | word | sub_32738+32 | Coolant temperature (ECT, for table lookup) |
| FFFFB27C | byte | sub_32738+26 | Custom OS active flag (0=stock, ≠0=custom) |

---

## 6. Algorithm Detail

### 6.1 EOIT Target Selection (sub_32738)

```
1. Check engine state:
   IF cranking:
     EOIT = KV_END_OF_INJECTION_CRANK_TARGET[ECT]
   ELSE IF FFFFB27C != 0 (custom OS flag):
     EOIT = custom table (not in stock calibration)
   ELSE IF desoot mode active:
     IF KE_USE_CRANK_EOIT:
       EOIT = KV_END_OF_INJECTION_CRANK_TARGET[ECT]
     ELSE:
       EOIT = KE_DESOOT_EOIT (fixed)
   ELSE (normal):
     EOIT = KV_NORMAL_END_OF_INJECTION_COOLA[ECT]

2. Coolant index calculation:
   index = (ECT + 0x400) × 5 / 6
   ECT is in internal units (×5/6 gives table index)

3. Apply trim:
   IF engine protection active:
     EOIT += KE_ENG_PROTECTION_TRIM_END_OF_IN
   ELSE:
     trim = KV_TRIM_END_OF_INJECTION_COOLANT[ECT]
     EOIT += trim
```

### 6.2 Timing Physics

```
Lores pulse: one per 90° of crankshaft rotation (8 per V8 revolution)
Boundary: reference angle from TDC (typically near intake valve opening)

Boundary angle = KE_BOUNDARY_OFFSET × 90°  (in crank degrees)
EOIT angle = boundary + EOIT_target × 90°

Timing constraint: injection must complete before intake valve closes
                   to avoid fuel puddling on a closed valve.
                   injection must START after exhaust valve closes
                   to avoid fuel short-circuiting to exhaust.

Typical EOIT values (stock):
  KE_BOUNDARY_OFFSET = 0x680 = 1664 → needs conversion
  KV_NORMAL EOIT ≈ 0x28D at operating temp → ~653 units

The exact conversion from calibration units to crank degrees requires
the lores period scaling factor from the engine constants module.
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| Fuel System (doc 07) | Injector pulse width drives injection start timing |
| CMP Sensor | Cam position provides TDC reference for boundary |
| CKP Sensor | Lores pulses provide angular reference |
| Injector Driver (sub_7D082) | Hardware output scheduling |
| Desoot Mode | Separate EOIT target when active |
| Engine Protection | Trimmed EOIT during overheat protection |
| Cranking | Separate EOIT table for start-up |

---

## 8. Gaps & Unresolved

1. **Boundary angle conversion**: KE_BOUNDARY_OFFSET = 0x680. The conversion
   from this calibration value to actual crank degrees needs the lores period
   scaling factor from engine constants.

2. **Custom OS EOIT table**: The FFFFB27C flag indicates a custom OS has
   alternate EOIT tables. Boost OS may use this to adjust EOIT for forced
   induction. The custom table addresses are not documented.

3. **Make-up pulse timing**: Some P59 calibrations support a second "make-up"
   injection pulse per cycle. The timing interaction between the main and
   make-up pulses is not traced.

4. **Sequential vs batch injection**: The Corvette uses sequential injection
   (one pulse per cylinder per cycle, timed to intake stroke). The transition
   from batch (cranking) to sequential (running) is not fully documented.

---

## 9. Community Knowledge

- **EOIT tuning**: Advancing EOIT (larger value = earlier completion) sprays
  fuel onto a hotter, closed intake valve, improving vaporization. Retarding
  EOIT sprays into the open valve for better cylinder filling. The sweet spot
  varies with cam profile, RPM, and manifold design.

- **Big cam EOIT**: Aggressive cams with lots of overlap may need significantly
  different EOIT to prevent fuel from going straight out the exhaust during
  overlap. Tuners typically advance EOIT (spray on closed valve) to use the
  intake valve as a heat source for vaporization.

- **EOIT and fuel economy**: At cruise, the factory calibration sprays fuel
  onto the back of a hot intake valve. This improves atomization and fuel
  economy. At WOT, spraying into the open intake port maximizes cylinder fill.

- **Boost applications**: Under boost, intake air temperature is higher and
  fuel vaporizes more readily. Some tuners retard EOIT slightly under boost
  to prevent pre-ignition from overly vaporized fuel.
