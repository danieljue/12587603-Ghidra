# P59 OS 12587603 — Fuel-Cut RPM Limiter Analysis

> **Function**: `sub_30368` in OS3 segment (0x60000-0x7FFFF)
> **Called from**: `DoLoopB:loc_2A0D2` — the main engine control loop
> **Purpose**: Overspeed fuel cut protection with hysteresis

---

## RPM Scaling

RPM values in calibration are stored as raw units where:
```
raw_value = RPM × 5.12  (i.e., RPM × 2048 / 400)
RPM = raw_value / 5.12
```

| Parameter | Raw Value | Actual RPM |
|-----------|-----------|------------|
| PN_OVERSPEED_HIGH | 0x7C00 (31744) | 6200 |
| PN_OVERSPEED_LOW | 0x7BFB (31739) | 6199 |
| COLD_PROT_HIGH | 0x5000 (20480) | 4000 |
| COLD_PROT_LOW | 0x4FFB (20475) | 3999 |

Runtime RPM scaling (in function): `d4 = (d4 × 256) / 307`

---

## Function Logic (Pseudocode)

```c
// Called from main loop every engine cycle
void sub_30368_FuelOverspeed() {
    uint8_t fuel_cut_flag = RAM[0xFFFFA93C];
    
    if (fuel_cut_flag == 0) {
        // PATH A: Fuel is currently ENABLED — check if we need to CUT
        uint16_t rpm = RAM[0xFFFFADB6];  // Current RPM (raw)
        
        // Select HIGH overspeed threshold
        uint16_t threshold;
        if (gear >= 5) {
            threshold = KE_PN_ENGINE_OVERSPEED_HIGH;  // 6200 RPM
        } else {
            threshold = KV_ENGINE_OVERSPEED_HIGH[gear_index];
        }
        
        // Scale RPM for comparison
        rpm_scaled = (rpm << 8) / 0x133;
        
        // Cold engine: use colder limit
        uint16_t cold_limit = KV_COLD_ENG_PROT_OVERSPEED_HIGH.lookup(rpm_scaled);
        if (cold_engine_flag) {
            threshold = min(threshold, cold_limit);  // 4000 RPM when cold
        }
        
        // VSS failure: use VSS_FAIL limit
        if (VSS_malfunction) {
            threshold = KE_ENG_OVERSPEED_VSS_FAIL_HIGH;
        }
        
        // CUT FUEL if RPM exceeds threshold
        if (current_rpm_scaled > threshold) {
            RAM[0xFFFFA93C] = 1;  // SET fuel cut flag
        }
        
    } else {
        // PATH B: Fuel is currently CUT — check if we can RE-ENABLE
        uint16_t rpm = RAM[0xFFFFADB6];
        
        // Select LOW overspeed threshold (re-enable hysteresis)
        uint16_t threshold;
        if (gear >= 5) {
            threshold = KE_PN_ENGINE_OVERSPEED_LOW;  // 6199 RPM
        } else {
            threshold = KV_ENGINE_OVERSPEED_LOW[gear_index];
        }
        
        // Scale RPM
        rpm_scaled = (rpm << 8) / 0x133;
        
        // Cold engine: use colder limit
        uint16_t cold_limit = KV_COLD_ENG_PROT_OVERSPEED_LOW.lookup(rpm_scaled);
        if (cold_engine_flag) {
            threshold = min(threshold, cold_limit);  // 3999 RPM
        }
        
        // VSS failure
        if (VSS_malfunction) {
            threshold = KE_ENG_OVERSPEED_VSS_FAIL_LOW;
        }
        
        // Check if RPM has fallen below re-enable threshold
        if (threshold > current_rpm_scaled) {
            // Still above — keep fuel cut
        } else {
            // RE-ENABLE FUEL if below some other threshold
            if (threshold > RAM[0xFFFFA562]) {
                RAM[0xFFFFA93C] = 0;  // CLEAR fuel cut flag
            }
        }
    }
}
```

---

## Key RAM Addresses

| Address | Variable | Purpose |
|---------|----------|---------|
| 0xFFFFA93C | fuel_cut_flag | 0 = fuel enabled, non-zero = fuel cut |
| 0xFFFFADB6 | current_rpm | Raw RPM value |
| 0xFFFFA3AF | gear | Current transmission gear |
| 0xFFFFA3B8 | gear_index | Index into gear-based tables |
| 0xFFFFA93E | cold_engine_flag | Engine not up to temp |
| 0xFFFF8998 | VSS_flag_1 | VSS malfunction flag 1 |
| 0xFFFF899A | VSS_flag_2 | VSS malfunction flag 2 |
| 0xFFFF899C | VSS_flag_3 | VSS malfunction flag 3 |
| 0xFFFFA562 | reenable_threshold | Secondary threshold for fuel re-enable |

---

## Launch Control Strategy

To implement launch control (lower RPM limit when stopped):

**Option A: Modify calibration values at runtime**
- When VSS == 0, write launch RPM to `KE_PN_ENGINE_OVERSPEED_HIGH`
- When VSS > 0, restore original value
- Pro: Simple, no code changes
- Con: Flash writes while engine running (not good)

**Option B: Patch `sub_30368` to use launch table**
- Before threshold selection, check VSS
- If VSS == 0 AND clutch switch active → use launch RPM table
- Pro: Clean, proper implementation
- Con: Need to inject new code + new calibration table

**Option C: Inject at the threshold comparison**
- After threshold is selected, check VSS/clutch
- Override threshold if launch conditions met
- Pro: Minimal patch
- Con: Still need calibration table

### Implementation (Option B):

```asm
; Injected at 0xA0000 (OS5 free space)
; Hook: At start of sub_30368, before threshold selection

LaunchControlCheck:
    ; Check VSS
    tst.w   (VSS_RAM_ADDR).l          ; Is vehicle moving?
    bne     NormalThreshold            ; Yes → use normal threshold
    
    ; Check clutch (or use brake switch for auto trans)
    btst    #CLUTCH_BIT, (CLUTCH_RAM).l
    beq     NormalThreshold            ; Clutch not pressed → normal
    
    ; Launch mode active! Use launch RPM table
    move.w  (LAUNCH_RPM_TABLE).l(pc,d0.w*2), d3  ; Index by coolant temp
    bra     ThresholdSelected
    
NormalThreshold:
    ; Original code continues here...
    ...
ThresholdSelected:
    rts
```

---

## VSS RAM Address Discovery

Need to find the Vehicle Speed Sensor RAM address. Common GM addresses:
- P01: 0xFFFFA0xx range
- P59: search calibration CSV for VSS references

From the disassembly: `unk_FFFFA3AF` = gear, and there are VSS flags at `0xFFFF8998/9A/9C`. The actual VSS value is likely at a nearby address.

---

*Analysis based on 936,975-line disassembly from LegacyNsfw/12587603*
