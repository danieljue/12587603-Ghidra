# P59 OS 12587603 — Shift Light (Performance Shift Indicator)

> Traced from 68k disassembly — 2026-06-22
> The shift light indicates the optimal RPM for upshifting. It uses engine
> speed, throttle position, coolant temperature, MAP, and current gear ratio
> to determine when to illuminate.

---

## 1. Overview

The P59 implements an upshift indicator light (common on Corvette Z06 and other
performance models) that tells the driver when to shift for optimal performance.
The algorithm considers:
- Engine RPM vs gear-dependent lower thresholds
- Throttle position (must be between low and high thresholds)
- MAP (disables light during low-load conditions)
- Coolant temperature (different thresholds when cold)
- Gear ratio calculation from RPM / vehicle speed
- Clutch transition inhibit timer

The shift light can be configured for either direct output control (PCM drives
the light) or Class 2 serial message (IPC controls the light).

**On the 2004 Corvette M6:** KE_EXECUTE_UPSHIFT_LIGHT_ALGORIT = 0 (disabled).
The upshift light feature exists in the code but is not active in the stock
calibration.

---

## 2. Functions

| Function | Address | .asm Line | Purpose |
|----------|---------|-----------|---------|
| sub_4A71A | 0x04A71A | 207090 | Main shift light algorithm — evaluates all conditions |

---

## 3. Data Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    SHIFT LIGHT LOGIC                           │
│                                                                │
│  sub_4A71A (Called from DoLoop)                                │
│    │                                                           │
│    ├─ KE_EXECUTE_UPSHIFT_LIGHT_ALGORIT == TRUE? → continue    │
│    │                                                           │
│    ├─ RPM Validation:                                          │
│    │   Read FFFFA55E (raw RPM), bounds check [0, 0xA00]        │
│    │   Use lookup table KV_DELAY_TIME[RPM_scaled]              │
│    │                                                           │
│    ├─ Gear Detection:                                          │
│    │   RPM_raw / FFFFA3C0 (vehicle speed proxy) = gear ratio   │
│    │   Compare against KV_GEAR_RATIO_LO per-gear thresholds    │
│    │   → Determine current gear (1, 2, 3, or 4)               │
│    │                                                           │
│    ├─ Temperature Check:                                       │
│    │   If cold (ECT < KE_COLD_TEMP_LO):                        │
│    │     Use KV_COLD_ENGINE_SPEED_LO (higher RPM floor)        │
│    │   Else:                                                    │
│    │     Use KV_ENGINE_SPEED_LO + KV_THROTTLE_LO lookup        │
│    │                                                           │
│    ├─ Throttle Check:                                          │
│    │   TPS between KV_THROTTLE_LO and KA_THROTTLE_HI_BASIC?    │
│    │   Apply hysteresis (KV_THROTTLE_HI_HYST) when off         │
│    │   Baro correction on upper throttle threshold             │
│    │                                                           │
│    ├─ MAP Check:                                               │
│    │   MAP > KV_SHIFT_MAP_THRESHOLD? (must be under load)      │
│    │                                                           │
│    ├─ Clutch Inhibit:                                          │
│    │   If clutch recently released:                            │
│    │     Wait KE_CLUTCH_TRANS_INHIBIT_TIME before enabling     │
│    │                                                           │
│    └─ Output:                                                   │
│        If KE_CONTROL_UPSHIFT_LIGHT == TRUE:                    │
│          Direct output pin (hardwired shift light)              │
│        Else:                                                    │
│          Send Class 2 message to IPC (instrument cluster)       │
│        Light duration: KE_SHIFT_DURATION (max on-time)          │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibration Parameters

| Address | CSV Label | Type | Stock | Units | Description |
|---------|-----------|------|-------|-------|-------------|
| 0x100C2 | KE_REASONABLE_ENGINE_SPEED | word | 0xFFFF | RPM | Max reasonable RPM for shift light |
| 0x100C4 | KV_SHIFT_MAP_THRESHOLD | word | 0x14FF | kPa | Disable shift light if MAP < this |
| 0x100CC | KE_TEMPERATURE_LO | word | 0 | °C | Min coolant temp for normal RPM thresholds |
| 0x100CE | KV_ENGINE_SPEED_LO | word | 0 | RPM | Normal (warm) min RPM per gear for shift indication |
| 0x100D6 | KV_THROTTLE_LO | word | 0 | Percent | Min TPS for shift indication per gear |
| 0x100DE | KA_THROTTLE_HI_BASIC | byte | 0 | Percent | Max TPS for shift indication |
| 0x10136 | KV_THROTTLE_HI_HYST | word | 0 | Percent | Hysteresis on upper TPS threshold |
| 0x1013E | KV_THROTTLE_HI_BARO_CORRECTION | byte | 0xFF | 0-16 | Barometric correction on upper TPS |
| 0x10148 | KE_SHIFT_DURATION | word | 0xFFFF | Seconds | Max time shift light stays on |
| 0x1014A | KV_GEAR_RATIO_LO | word | 0 | Input/Out | Min gear ratio per upshiftable gear |
| 0x10152 | KV_COLD_ENGINE_SPEED_LO | word | 0 | RPM | Min RPM when engine cold |
| 0x1015A | KE_COLD_TEMP_LO | word | 0 | °C | Temp below which cold RPM thresholds used |
| 0x1015C | KV_DELAY_TIME | byte | 0xFF | Seconds | Delay from good shift point to light on |
| 0x10172 | KE_CLUTCH_TRANS_INHIBIT_TIME | word | 0 | Seconds | Inhibit after clutch release |
| 0x10174 | KE_EXECUTE_UPSHIFT_LIGHT_ALGORIT | byte | 0 | Boolean | Master enable for shift light logic |
| 0x10175 | KE_CONTROL_UPSHIFT_LIGHT | byte | 0 | Boolean | Direct output (1) vs Class 2 message (0) |

---

## 5. RAM Variables

| Address | Size | Verified Via | Description |
|---------|------|-------------|-------------|
| FFFFA55E | word | sub_4A71A+12 | Scaled RPM value for shift light lookup |
| FFFFA562 | word | sub_4A71A+58 | Raw engine RPM (used for gear ratio calculation) |
| FFFFA3C0 | word | sub_4A71A+52 | Vehicle speed proxy (used for gear ratio) |

> **Note:** Full RAM variable tracing for shift light state, clutch inhibit
> timer, and shift light on/off flag requires detailed analysis of sub_4A71A.

---

## 6. Algorithm Detail

### 6.1 Main Algorithm: sub_4A71A

```
1. If KE_EXECUTE_UPSHIFT_LIGHT_ALGORIT == FALSE: exit immediately
   (Shift light feature disabled)

2. Read and validate RPM:
   - Read raw RPM from FFFFA55E
   - Clamp to range [0, 0xA00] (scaled range)
   - Scale: if < 0x60: RPM_raw × 0x50 / 3
   - If ≥ 0x60: cap at 0xA00
   - Lookup KV_DELAY_TIME[RPM_scaled] for delay

3. Determine current gear:
   - gear_ratio = FFFFA562 (RPM) / FFFFA3C0 (speed)
   - If no speed signal (FFFFA3C0 == 0): skip gear check
   - Compare against KV_GEAR_RATIO_LO thresholds:
     - If ratio < gear_ratio[0] → gear 0 (neutral or invalid)
     - If ratio < gear_ratio[1] → gear 1
     - If ratio < gear_ratio[2] → gear 2
     - If ratio < gear_ratio[3] → gear 3
     - Else → gear 4+

4. Temperature-dependent RPM threshold:
   - If ECT < KE_COLD_TEMP_LO:
     - Min RPM from KV_COLD_ENGINE_SPEED_LO (higher, to protect cold engine)
   - Else:
     - Min RPM from KV_ENGINE_SPEED_LO (gear-dependent table)
     - Throttle from KV_THROTTLE_LO (gear-dependent table)

5. Throttle window check:
   - Lower: TPS ≥ KV_THROTTLE_LO[gear]
   - Upper: TPS ≤ KA_THROTTLE_HI_BASIC + baro_correction
   - If shift light was off: apply KV_THROTTLE_HI_HYST to upper threshold
   - Baro correction: KV_THROTTLE_HI_BARO_CORRECTION × baro_factor

6. MAP threshold:
   - MAP ≥ KV_SHIFT_MAP_THRESHOLD? → must be under load
   - If MAP too low (decel, idle): disable light

7. Clutch inhibit:
   - If clutch transition detected (just released):
     - Inhibit light for KE_CLUTCH_TRANS_INHIBIT_TIME loops
   - Prevent flashing during shifts

8. Light output:
   - If all conditions met:
     - If KE_CONTROL_UPSHIFT_LIGHT: drive output pin directly
     - Else: send Class 2 message to IPC
   - Max duration: KE_SHIFT_DURATION
```

---

## 7. Integration Points

| Connected To | How |
|-------------|-----|
| DoLoop | Calls sub_4A71A periodically |
| IPC (Instrument Panel) | Class 2 serial message for shift light (when not direct output) |
| RPM | FFFFA562 and FFFFA55E — dual RPM signals |
| VSS | FFFFA3C0 — vehicle speed for gear ratio |
| Coolant Temp | Cold temperature alters RPM thresholds |
| MAP | Disables light under low load |
| Clutch Switch | Inhibits light after clutch transitions |

---

## 8. Gaps & Unresolved

1. **Exact output pin for direct shift light**: The pin number used when
   KE_CONTROL_UPSHIFT_LIGHT = TRUE has not been identified from the disassembly.

2. **Class 2 message format**: The specific CAN/J1850 message structure for
   IPC shift light control is not documented.

3. **Gear ratio thresholds per gear**: KV_GEAR_RATIO_LO is a 4-entry table
   (0x1014A, 0x1014C, 0x1014E, 0x10150) for gears 1-4. Gear 5 and 6 are not
   individually detected — gear 4+ uses the same threshold.

4. **Shift light state machine**: The exact on/off/hysteresis logic including
   KE_SHIFT_DURATION countdown requires detailed tracing of the full subroutine.

---

## 9. How To Verify

```bash
# Verify shift light disabled on Corvette M6
python3 -c "
with open('12587603-2004-Corvette-M6.bin', 'rb') as f:
    data = f.read()
print(f'KE_EXECUTE_UPSHIFT_LIGHT_ALGORIT @ 0x10174: {data[0x10174]:02X} (0=disabled)')
print(f'KE_CONTROL_UPSHIFT_LIGHT @ 0x10175: {data[0x10175]:02X} (0=Class2 msg)')
print(f'KE_TEMPERATURE_LO @ 0x100CC: {int.from_bytes(data[0x100CC:0x100CE],\"big\"):04X} (0=always warm mode)')
print(f'KV_ENGINE_SPEED_LO @ 0x100CE: {data[0x100CE]:02X} (first byte = 0)')
"
```

```bash
# Verify subroutine
grep -c "sub_4A71A" 12587603-2004-Corvette-M6.sanitized.asm
# Should show function definition + cross-references
```

---

## 10. Community Knowledge

- **Z06 shift light**: The C5 Corvette Z06 came with a functional shift light
  from the factory. The 2004 Corvette M6 likely has the code but KE_EXECUTE
  is set to 0. Enabling it would activate the upshift indicator.

- **Aftermarket tuning**: HPTuners and EFILive expose the shift light
  parameters under the "Shift Light" tab. Common adjustments include lowering
  the RPM thresholds and enabling the feature on non-Z06 models.

- **Manual transmission only**: The shift light algorithm uses gear ratio
  detection (RPM/VSS) to determine current gear. This works best with manual
  transmissions where the clutch is fully engaged. Automatic transmissions
  have torque converter slip that makes ratio detection unreliable.

- **RPM vs VSS ratio**: KV_GEAR_RATIO_LO stores the expected RPM/VSS ratio for
  each gear. These are set based on the vehicle's axle ratio and tire size.
  Changing either requires recalibration of these thresholds.
