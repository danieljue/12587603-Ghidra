# P59 PCM DTC Storage and MIL Control — Reverse Engineering Notes

## Overview

The P59 PCM (2004 Corvette M6, calibration 12587603) implements OBD-II compliant diagnostic
trouble code (DTC) management with a diagnostic executive that coordinates emissions testing,
fault code storage/retrieval, and Malfunction Indicator Lamp (MIL, aka SES — Service Engine Soon)
control. The system is partitioned into several cooperating subsystems:

| Subsystem | Key Functions | Address Range |
|-----------|--------------|---------------|
| **DM Executive** | Trip detection, code clear, enable conditions, odometer tracking | `sub_5EDDA`, `sub_5EE7E`, `sub_5EF12`, `sub_5EFCC` |
| **DM Types / Fault Class** | Fault type classification (A/B/C/X), light enable | `DM_TYPES_KV_DM_FAULT_TYPE`, `DM_TYPES_KV_DM_LIGHT_ENABLE` |
| **DM Data Manager** | Entry conditions (coolant temp, fuel trim), misfire conditions met | `sub_5E08A` |
| **DTC Storage (Failure Record)** | Store DTC snapshots and freeze frame data | `sub_5DE36`, `sub_5ED42` |
| **DTC Pass/Clear** | Clear individual DTCs, code-clear processing | `sub_5DFBC`, `sub_5E37E` |
| **MIL Control** | MIL illumination, flashing (misfire), steady-on | `sub_757C0` |
| **Misfire MIL Flash** | Catalyst-damaging misfire flash logic | `sub_702A6` |
| **Lamp Driver** | Hardware output — SES light pin control | `sub_1122` (device `$3E`) |
| **PID Services** | OBD-II Mode $01 PID $01 (DTC count), Mode $03/$07 DTC readout | `GetPid_0001_NumberofEmissionRelatedDTC`, `sub_40044` |

---

## 1. DTC Indexing Scheme

The P59 uses a **sequential index** (0–$104, i.e., 0–260) to identify each DTC. The index is not
the P-code directly; rather, a lookup maps index → P-code word and vice versa.

### Key Data Tables

| Table | Description | Address |
|-------|-------------|---------|
| `word_87F70` | P-code lookup: `word_87F70[index*4]` gives the 16-bit P-code value for a given index | Calibration data |
| `byte_87F72` | Group/component ID: `byte_87F72[index*4]` maps DTC to diagnostic group for enable-condition bitmaps | Calibration data |
| `byte_87F73` | Sub-component ID: `byte_87F73[index*4]` used for DTC sub-classification | Calibration data |
| `DM_TYPES_KV_DM_FAULT_TYPE` | Fault type table: one byte per DTC index. Values: 0=Type X (no reporting), 1=Type A, 2=Type B, 3=Type C | `96xxx` range |
| `DM_TYPES_KV_DM_LIGHT_ENABLE` | Per-DTC lamp enable: 1=SES lamp on, 0=no-lamp (useful for SVS-only codes) | `96xxx` range |

### P-Code ↔ Index Lookup

- **`sub_5F180` (binary search):** Given a 16-bit P-code in `d0`, returns the DTC index in `d0.w` (0 if not found).  
  Performs binary search over the sorted `word_87F70` array from index 1 to $104.
- **`sub_5F1BE`:** Iterates sequentially through DTC indices, matching status bits against criteria
  (used for OBD-II Mode $03/$07 DTC retrieval).

---

## 2. DTC Status Byte (`unk_FFFF88C0`)

Each DTC index has a **2-byte status word** at `unk_FFFF88C0[index*2]` in RAM. The low byte
(`unk_FFFF88C0`) encodes the primary DTC state:

| Bit | Name | Meaning |
|-----|------|---------|
| **0** | Test Failed This Drive Cycle | Diagnostic test has failed at least once this trip |
| **1** | Test Failed (Confirmed) | DTC is confirmed/stored (persistent across cycles) |
| **2** | Pending DTC | Test failed but not yet confirmed |
| **3** | Test Not Run Since Code Clear | Diagnostic has not completed since last clear |
| **4** | MIL Requested | Lamp driver should illuminate SES |
| **5** | Test Failed Since Code Clear | At least one failure since last code clear |
| **6** | Test Not Run This Drive Cycle | Diagnostic has not run this trip |
| **7** | Warning Indicator Requested | SES/MIL lamp output bit — set when lamp should be ON |

The high byte (`unk_FFFF88C1`) is a pass/fail **counter**:

- Incremented for each failed diagnostic test
- Decremented for each passed diagnostic test
- Compared against trip-dependent thresholds (typically 1 for Type A, 2 for Type B) for confirmation
- Clamped and used for code maturation logic

### Status Byte Operations

- **Confirm DTC:** `bset #1, unk_FFFF88C0(d6.w*2)` — sets bit 1 (sub_5DE36, line 243277)
- **Set Pending:** `bset #2` is set implicitly during confirmation
- **Set MIL Request:** `bset #7` is toggled by `sub_5EA4A` based on enable conditions
- **Set "Not Run":** `bset #3` and `bset #6` are set during DTC confirmation (sub_5DE36, line 243278-279)
- **Clear DTC (pass):** `bclr #1`, `bclr #2`, `bset #5` — marks DTC as passed (sub_5DFBC)

---

## 3. Fault Type Classification

Each DTC is classified into one of four fault types via `DM_TYPES_KV_DM_FAULT_TYPE`:

| Type | Value | Description | Trip Behavior |
|------|-------|-------------|---------------|
| **A** | 1 | Emissions-related, MIL immediately | 1 trip SES On, 3 trips SES Off |
| **B** | 2 | Emissions-related, MIL after 2nd failure | 2 trips SES On, 3 trips SES Off |
| **C** | 3 | Non-emissions (SVS instead of SES) | SVS On immediately, auto-clear |
| **X** | 0 | No reporting | No MIL, no storage |

**Tri-state MIL Logic (reflected in `unk_FFFF8ACC` bits 6-7):**
- Bit 6-7 = 0: MIL OFF (no confirmed DTCs with MIL requested)
- Bit 6-7 = 1: MIL ON but NOT flashing (steady SES)
- Bit 6-7 = 2: MIL FLASHING (active misfire causing catalyst damage risk)

**SVS (Service Vehicle Soon) logic:**
- Type C (value 3) DTCs trigger SVS rather than SES
- `sub_5EE7E` scans all indices for active Type C DTCs (bit 7 set + Fault Type = 2)
- SVS bit set via `bset #6, (unk_FFFFAAD0).w`
- Minimum SVS duration enforced by `DM_EXECUTIVE_KE_DGDM_SVS_ON_MIN_DURATION` ($320 = 800 seconds)

---

## 4. DTC Storage: Failure Records (Freeze Frame)

### Storage Function: `sub_5DE36`

When a diagnostic test fails and confirms a DTC, `sub_5DE36` stores a **failure record**
(freeze frame data). The function:

1. Checks enable conditions (coolant temp, manifold pressure rationality)
2. Validates the DTC is not Type X (`DM_TYPES_KV_DM_FAULT_TYPE != 3/0`)
3. Checks if the DTC was already confirmed (bit 1 already set, bit 6 preventing double-store)
4. Finds or allocates a storage slot (up to 5 slots managed through `unk_FFFF8ACB`)

### Failure Record Layout (per slot, $56 bytes)

Each stored failure record is accessed via offset `slot * $56` from a base address. The layout:

| Offset | Size | Field |
|--------|------|-------|
| -$7944 | word | DTC P-code stored |
| -$793C | word | Odometer at time of failure (from `word_87F70[index*4]`) |
| -$793E | byte | DTC-dependent FR list ID |
| -$7941 | byte | Clear flag (0 = not cleared) |
| -$793F | byte | Status flags |
| -$7940 | byte | Status flags |
| -$793A | word | Timestamp/cycle count |
| -$7938 | word | Additional data |
| +$C offset | 35 words ($2B each) | PID snapshot values (up to 35 PIDs from `word_89050` table) |
| +$C+$2B offset | 2 words | Additional PID values (from `word_89044` table, indexed by `DM_EXECUTIVE_KV_DGDM_DTC_DEP_FR_LIST_ID`) |

### Freeze Frame PID Data

- **Standard PID snapshot:** `word_89050` defines which PIDs to capture ($23 = 35 entries)
- **DTC-dependent PID snapshot:** `DM_EXECUTIVE_KV_DGDM_DTC_DEP_FR_LIST_ID` selects a sub-table
  from `word_89044` for DTC-specific freeze frame data
- Each PID value is fetched via `sub_5F380` which calls `sub_42E3C` (the PID read infrastructure)

### Storage Slot Management

- `unk_FFFF8ACB`: Current slot counter (1–5), wraps around
- `unk_FFFF8ACA`: Slot 0 allocation flag (used for "first DTC to fail")
- When all 5 slots are full, oldest entries are overwritten (FIFO)

---

## 5. Diagnostic Executive

### Main Loop Integration

The diagnostic executive is called from the main engine control loop:

```
DoLoopD (0x2A798 area):
  → sub_5EDDA (diagnostic executive — trip detect, code clear, manage conditions)
  
DoLoopG (0x2B364 area):
  → sub_5EF12 (odometer tracking for DGDM)
  → sub_5EE7E (MIL/SVS decision logic)
  → sub_757C0 (MIL lamp driver)
```

### Trip Detection (`sub_5EFCC`)

Called with parameter `d0 = 2` at each ignition cycle start. Responsibilities:

1. **Code Clear Processing:** Calls `sub_5E37E` which:
   - Increments pass counters for all diagnostic indices (types A/B)
   - Handles Type C DTC clearing with `byte_8A82E`/`byte_8A82F` initial values
   - Resets entry condition tracking (coolant temp buckets, fuel trim buckets)
   - Clears the warm-up cycle pass/fail state

2. **Sensor Rail Diagnostics:** Tests MAP and coolant sensor inputs for open-circuit:
   - MAP rail voltage check via `DM_EXECUTIVE_KE_DGDM_MAP_RAIL` (counts)
   - Coolant rail voltage check via `DM_EXECUTIVE_KE_DGDM_COOLANT_RAIL` ($FD counts)

3. **DTC Group Tracking:** Iterates all DTC indices (1–$104):
   - Builds `unk_FFFF8252` bitmap: bit set for each confirmed DTC group (`byte_87F72`)
   - Builds `unk_FFFFAAC8` bitmap: bit set for each confirmed+not-run DTC
   - Increments per-group confirmed-DTC counters in the `-$5538` offset area

### Entry Condition Management (`sub_5E08A`)

Monitors cooling system and fuel control stability for enabling diagnostics:

| Condition | RAM Variable | Calibration | Threshold |
|-----------|-------------|-------------|-----------|
| Coolant temp range (group A) | `unk_FFFFADB0` | `DM_DATA_MANAGER_KE_DGDM_MAX_LOW_COOLANT` ($800), `DM_DATA_MANAGER_KE_DGDM_MIN_HIGH_COOLANT` ($706) | Within window |
| Fuel trim stability | `unk_FFFFA0E2`, `unk_FFFFA562` | Various | ±$400 short term, ±$780 long term |
| Misfire conditions met | `unk_FFFFB4AE` counter | `DM_DATA_MANAGER_KE_DGDM_MISFIRE_CONDS_LIMIT` ($A = 10) | Counter ≥ threshold → `bset #2, (unk_FFFFB4AA)` |
| Fuel system conditions (group B) | `unk_FFFFB4AC` counter | `DM_DATA_MANAGER_KE_DGDM_FUEL_SYS_CONDS_LIMIT` ($A) | Counter ≥ threshold → `bset #5, (unk_FFFFB4AA)` |

### Odometer Tracking (`sub_5EF12`)

Tracks two key OBD-II mandated odometers:

1. **Odometer Since Code Clear** (`unk_FFFF8258`, reported as `unk_FFFFAACC`):
   - Accumulates vehicle distance since last diagnostic code clear
   - Scaled by `DM_EXECUTIVE_KE_DGDM_ODO_SINCE_CC_SCALE_FACT` ($DA)
   - Clamped to $FFFF0000 (65,535 km)

2. **Odometer With MIL On** (`unk_FFFF825C`, reported as `unk_FFFFAACE`):
   - Accumulates only when MIL is actively illuminated
   - Scaled by `DM_EXECUTIVE_KE_DGDM_ODO_WITH_MIL_ON_SCALE_FA` ($DA)
   - Only increments when MIL state bits (unk_FFFF8ACC bits 4-5) indicate MIL ON
   - Cleared when no confirmed, MIL-requesting DTC exists

---

## 6. MIL (SES) Illumination Logic

### Lamp Decision Function: `sub_5E1A4`

Called by `sub_5EE7E` to decide the MIL state. Sets bits 4-5 of `unk_FFFF8ACC`:

| Value | State | Condition |
|-------|-------|-----------|
| 0 | MIL OFF | No active DTCs requesting MIL |
| 1 | MIL ON (Steady) | At least one DTC with bit 4 set and Fault Type A or B, AND MIL flashing not active |
| 2 | MIL FLASHING | Misfire diagnostic has set flash request (`sub_5F2CC` checks `unk_FFFFAE61` bit 6) |

The MIL state is stored in `unk_FFFF8ACC` upper nibble (bits 4-7), and also drives the "MIL ON"
history flag in `unk_FFFFAAF2`.

### MIL Output Driver: `sub_757C0`

Called from both DoLoopD and DoLoopG at sub-loop boundaries. This function:

1. **MIL Flashing Logic:**
   - Reads current MIL state from `unk_FFFF8ACC` bits 4-5
   - If state == 2 (flashing): toggles `unk_FFFFA1E6` with period `OBD2_CONTROL_KE_MIL_TIME` ($50 = 80 units)
   - Timer management via `unk_FFFFA1E4` (flash timer) and loop rate
   
2. **Steady MIL Logic:**
   - If state == 1: sets `unk_FFFFA1E6` = 1 (MIL ON continuously)
   - If state == 0: sets `unk_FFFFA1E6` = 0 (MIL OFF)
   - Override: `unk_FFFFA1E7` can force MIL ON (bulb check / key-on test)

3. **TCM MIL Request:**
   - Monitors Allison TCM MIL request line for P0700 (transmission DTC)
   - Time-filtered via `TCM_IO_INTERFACE_KE_TCM_MIL_REQUEST_TIME`

4. **Final Output:** Calls `sub_1122` with device `$3E` — this is the hardware driver
   that toggles the actual SES lamp output pin.

### Hardware Output: `sub_1122`

Device $3E ($62 decimal) controls the SES/MIL lamp:
- Writes to bit-mapped output register at `-$40D6(device)` 
- Bit position determined by `device & 7` within the byte
- Other bits in the byte control other lamps/outputs

### MIL Flashing Stopped Conditions (`sub_702A6` misfire module)

The MIL flash is suppressed when any of these conditions are met:

- DFCO time exceeds `DG_MF_REPORTING_KE_MISF_DFCO_TIME_STOP_MIL_FLASH` ($1E seconds)
- Vehicle speed below `DG_MF_REPORTING_KE_MISF_FLASH_MIL_VEHICLE_SPEED` ($F00 = 3840)
- Engine load below `DG_MF_REPORTING_KE_MISF_FLASH_MIL_ENGINE_LOAD` ($C00 = 3072)
- Any cylinder has misfire DTC confirmed (bits 1 set in cylinder status bytes at `unk_FFFF88C6` through `unk_FFFF88D6`)
- TCC locked (bit 7 of `unk_FFFF893A` not set)

The flash is **latched** for `DG_MF_REPORTING_KE_MISF_FLASH_MIL_LATCH` duration.

---

## 7. DTC Confirmation and Clearing Flow

### DTC Confirmation (`sub_5F110` → `sub_5DE36`)

```
Diagnostic test fails
  ↓
sub_5F110(dtc_index):  "Set DTC" entry point
  → Check if already confirmed (bit 1 set) → skip if yes
  → sub_5DE36(dtc_index): Store failure record
     → Validate fault type (not Type X)
     → Check bit 6 (test not run) → prevent double-store
     → Find/allocate storage slot (unk_FFFF8ACB)
     → Store P-code, odometer, PID snapshots
     → Set DTC-specific FR list ID
     → Set bits: #1 (confirmed), #3 (not run since clear), #6 (not run this cycle)
     → sub_5EA4A: Update lamp bit and entry conditions
```

### DTC Pass/Clear (`sub_5F0BE` → `sub_5DFBC`)

```
Diagnostic test passes
  ↓
sub_5F0BE(dtc_index):  "Clear DTC" entry point
  → Check if not yet confirmed → decrement group counter
  → sub_5DFBC(dtc_index): Clear DTC status
     → bclr #1 (confirmed)
     → bclr #2 (pending)
     → bset #5 (test passed since clear)
     → sub_5EA4A: Re-evaluate lamp
```

### Code Clear at Trip Start (`sub_5E37E`)

Called at ignition-on with `d0 = 2`:
- Clears all pass/fail counters (`unk_FFFF88C1` set to initial values)
- Type C DTCs: `byte_8A82F` (0 → immediate clear)
- Type A/B DTCs: `byte_8A82E` (4 → need 4 passes to clear)
- Resets entry condition tracking
- Clears warm-up cycle flags

---

## 8. OBD-II Mode $01 PID $01 (DTC Count)

`GetPid_0001_NumberofEmissionRelatedDTC`:

1. Reads MIL status from `unk_FFFF8ACC` bits 4-5
2. Calls `sub_5F22C` with `d1=1, d0=0, d2=0` to count:
   - Confirmed DTCs (bit 1 set) with Fault Type A or B
   - Pending DTCs (bit 4 set) with Fault Type A or B
   - MIL-requested DTCs (bit 7 set) with any fault type
   - Combined total (any of above)
3. Returns byte: bit 7 = MIL status, bits 6-0 = DTC count (clamped to $7F)
4. Also checks `DM_TYPES_KV_NON_CONTINUOUS_TEST_SUPPORTED` for readiness monitor bits (bits 0-7)

---

## 9. Key RAM Variables Summary

| Address | Name | Description |
|---------|------|-------------|
| `FFFF88C0.w` (×260) | DTC status bytes | 2 bytes per DTC index: status + pass/fail counter |
| `FFFF86BC` | Current DTC view | Sliding window for PID readout of currently selected DTC |
| `FFFF8ACC` | MIL state / MIL on history | Upper nibble = MIL state (0=OFF, 1=ON, 2=FLASH), lower nibble = MIL history |
| `FFFF8ACB` | DTC storage slot | Currently active failure record slot (1-5) |
| `FFFF8252` | DTC group bitmap | Confirmed DTC groups (by `byte_87F72`) |
| `FFFFAAC8` | DTC group N/R bitmap | Confirmed but not-run DTC groups |
| `FFFFAAD0` | Diagnostic executive flags | Bit 4 = trip detection active, Bit 6 = SVS ON, Bit 7 = warm-up complete |
| `FFFF8256` | Enable-conditions-met | Set when coolant/MAP conditions allow diagnostics |
| `FFFFB4AA` | Entry conditions met | Bit 2 = misfire conditions met, Bit 4 = cooling conditions A, Bit 5 = fuel conditions B, Bit 7 = cooling conditions B |
| `FFFFA1E6` | MIL lamp output state | 1 = lamp ON (actual hardware output) |
| `FFFFA1E7` | Bulb check request | Forces MIL ON during key-on prove-out |
| `FFFFAE61` | Misfire MIL flash | Bit 6 = flash active, Bit 4/5 = misfire type |
| `FFFF8258` | DGDM Odo Since CC | Odometer since code clear (32-bit, scaled) |
| `FFFF825C` | DGDM Odo With MIL | Odometer with MIL on (32-bit, scaled) |
| `FFFFAEBC` | Vehicle speed | Used for odometer accumulation |
| `FFFFAACC` | DGDM Odo Since CC (16) | Upper 16 bits for PID readout |
| `FFFFAACE` | DGDM Odo With MIL (16) | Upper 16 bits for PID readout |
| `FFFFAAF2` | MIL on history | Previous cycle MIL state |

---

## 10. Calibration Constants Summary

| Constant | Value | Description |
|----------|-------|-------------|
| `OBD2_CONTROL_KV_DIAGNOSTIC_ENABLE` | Byte array | 42-byte Boolean flags enabling specific OBD-II diagnostics |
| `OBD2_CONTROL_KV_DIAGNOSTIC_DISABLE_FOR_PTO` | Byte array | Disable flags when PTO engaged |
| `OBD2_CONTROL_KE_MIL_TIME` | $50 (80) | MIL flash on/off period in loop counts |
| `OBD2_CONTROL_KE_MISFIRE_DIAG_RPM_LIMIT` | $C800 | Max RPM for misfire data collection |
| `DM_EXECUTIVE_KE_DGDM_COOLANT_RAIL` | $FD | Open coolant sensor rail voltage (counts) |
| `DM_EXECUTIVE_KE_DGDM_MAP_RAIL` | 2 | Open MAP sensor rail voltage (counts) |
| `DM_EXECUTIVE_KE_DGDM_ODO_SINCE_CC_SCALE_FACT` | $DA (218) | Odometer scaling factor (KPS/MPH) |
| `DM_EXECUTIVE_KE_DGDM_ODO_WITH_MIL_ON_SCALE_FA` | $DA (218) | Odometer scaling with MIL on |
| `DM_EXECUTIVE_KE_DGDM_SVS_ON_MIN_DURATION` | $320 (800) | Minimum SVS lamp duration (seconds) |
| `DM_DATA_MANAGER_KE_DGDM_MAX_LOW_COOLANT` | $800 | Upper bound of "low coolant" range |
| `DM_DATA_MANAGER_KE_DGDM_MIN_HIGH_COOLANT` | $706 | Lower bound of "high coolant" range |
| `DM_DATA_MANAGER_KE_DGDM_MISFIRE_CONDS_LIMIT` | $A (10) | Loop count for misfire conditions met |
| `DM_DATA_MANAGER_KE_DGDM_FUEL_SYS_CONDS_LIMIT` | $A (10) | Loop count for fuel system conditions met |
| `DM_TYPES_KV_NON_CONTINUOUS_TEST_SUPPORTED` | $6DFF | Bitmap of supported non-continuous monitors |
| `DM_TYPES_KV_DM_FAULT_TYPE` | Per-DTC array | One byte per DTC index: fault type classification |
| `DM_TYPES_KV_DM_LIGHT_ENABLE` | Per-DTC array | One byte per DTC index: lamp enable Boolean |
| `DM_EXECUTIVE_KV_DGDM_DTC_DEP_FR_LIST_ID` | Per-DTC array | DTC-dependent freeze frame PID list selector |
| `DG_MF_REPORTING_KE_MISF_DFCO_TIME_STOP_MIL_FLASH` | $1E (30) | DFCO time before stopping MIL flash |
| `DG_MF_REPORTING_KE_MISF_FLASH_MIL_VEHICLE_SPEED` | $F00 | Min vehicle speed for MIL flash |
| `DG_MF_REPORTING_KE_MISF_FLASH_MIL_ENGINE_LOAD` | $C00 | Min engine load for MIL flash |
| `DG_MF_REPORTING_KE_MISF_FLASH_MIL_LATCH` | $FFFF | MIL flash latch duration |
| `DG_MF_REPORTING_KE_MISF_MARSHALLING_FACTOR` | $10 | Marshall factor for emission misfire (1.0) |
| `TCM_IO_INTERFACE_KE_TCM_MIL_REQUEST_TIME` | Calibrated | TCM MIL request line filter time |

---

## 11. Call Flow Summary

### Key-On / Trip Start
```
OS Init → sub_5EFCC(d0=2)            # Trip detect, code clear processing
  → sub_5E37E(d0=2)                  # Clear warm-up state, reset counters
  → sub_5E37E(d0=4)                  # DTC pass counter advance
```

### Main Loop (each iteration)
```
DoLoopD:                             # Diagnostic loop (slower)
  → sub_5EDDA                         # Diagnostic executive
     → sub_5E9AE                      # (code clear sub-function)
     → sub_5E08A                      # Entry condition evaluation
  → sub_757C0                         # MIL lamp driver

DoLoopG:                             # General loop (faster)
  → sub_6983E                         # (misc)
  → sub_5EE7E                         # MIL/SVS decision
     → sub_5E1A4                      # MIL state determination
     → sub_5F2CC                      # Check misfire flash
  → sub_757C0                         # MIL lamp driver
  → sub_5EF12                         # Odometer tracking
     → sub_5F22C                      # DTC count
     → sub_5DFDC                      # Non-continuous test tracking
```

### Diagnostic Test (on failure detection)
```
Individual diagnostic (e.g., P0531 AC pressure test)
  → sub_5F0BE(dtc_index) or sub_5F110(dtc_index)
     → sub_5DE36(dtc_index)           # Store failure record + freeze frame
     → sub_5EA4A(dtc_index)           # Update MIL request bit + entry conditions
```

### Diagnostic Test (on pass detection)
```
Individual diagnostic
  → sub_5F0BE(dtc_index)
     → sub_5DFBC(dtc_index)           # Clear DTC confirmation
     → sub_5EA4A(dtc_index)           # Re-evaluate MIL
```

### Misfire Diagnostic (MIL Flash)
```
DoLoopF:
  → sub_702A6                         # Misfire detection + MIL flash control
     → Checks flash stop conditions
     → Sets/clears unk_FFFFAE61 bit 6 (flash request)
```

---

## 12. DTC P-Code Listing Architecture

Each diagnostic subsystem defines its own P-code thresholds and DTC associations:

| Diagnostic | P-Code Table | Description |
|-----------|-------------|-------------|
| ECT Rationality | `DI_ECTR_KV_ECTR_DTCS` (3 bytes) | P-codes for coolant temp rationality tests (P0116, P0117, P0118) |
| AC Pressure | `DG_AC_KE_AC_CLUTCH_HIGH_FAIL_THRESHOLD` → P1539 | AC clutch circuit high |
| AC Pressure | `DG_AC_KE_AC_CLUTCH_LOW_FAIL_THRESHOLD` → P1546 | AC clutch circuit low |
| AC Pressure | `DG_AC_KE_P0531_*` → P0531 | AC pressure sensor performance |
| Cruise Control | `CRUIS_MANAGE_KE_CRUISE_SWITCH_FAIL_TIME` → P0567/P0568 | Cruise switch stuck |
| TCM | `TCM_IO_INTERFACE_KE_TCM_MIL_REQUEST_TIME` → P0700 | Transmission DTC request |
| EGR | `DG_LEGR_KE_EGRP_TIME_TO_PASS_CV` → P1404 | EGR position error |

The actual P-code numeric values are stored in the `word_87F70` table (one per index),
with the fault type and lamp enable in parallel arrays. Indices above $7D (125) are
specially treated — they bypass the "enable conditions met" check in `sub_5F110`,
allowing them to be stored even when the engine hasn't fully warmed up (used for
electrical/system DTCs that don't require warm-up conditions).
