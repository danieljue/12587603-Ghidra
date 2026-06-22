# Boost OS V3.4 — Reverse Engineering Analysis

> **PRIVATE — Not for public repo**
> Analyzed by binary-diffing stock 12587603 vs Boost OS V3.4 output
> 9,267 bytes changed across 51 regions

---

## JSR Hook Points (OS Code Patches)

These are the injection points where Boost OS intercepts factory functions:

| Original Address | Patch | JSR Target | Original Code Replaced | Likely Purpose |
|-----------------|-------|-----------|----------------------|----------------|
| 0x031C9E (OS1) | `4E B9 00 0D 04 42 4E 71` | 0x0D0442 | `3C 38 A1 F8 36 38 AC AC` | Unknown subsystem hook |
| 0x031CEC (OS1) | `4E B9 00 0D 04 26 4E 71` | 0x0D0426 | `3C 38 A1 F8 4A 38 B2 EE` | Unknown subsystem hook |
| 0x034D10 (OS1) | `4E B9 00 0D 03 06` | 0x0D0306 | `31 EE FF FE A8 8E` | Unknown subsystem hook |
| **0x079B92 (OS3)** | **`4E B9 00 0D 05 58`** | **0x0D0558** | **`41 F9 00 00 84 42`** | **VE TABLE EXPANSION** (replaces `lea 0x8442, a0`) |
| **0x07A176 (OS3)** | **`4E B9 00 0D 05 58`** | **0x0D0558** | **`41 F9 00 00 84 42`** | **VE TABLE EXPANSION** (second lookup site) |
| **0x07A95E (OS3)** | **`4E B9 00 0D 05 58`** | **0x0D0558** | **`41 F9 00 00 84 42`** | **VE TABLE EXPANSION** (third lookup site) |
| 0x07ADC2 (OS3) | `60` (BRA) | — | `66` (BNE) | Branch always taken — disables a conditional check |

### Key: `41 F9 00 00 84 42` = `lea (K_MAIN_VOLUMETRIC_EFFICIENCY).l, a0`

This confirms that Boost OS intercepts the VE table address load and redirects it to custom code at 0x0D0558. The custom routine likely:
1. Modifies the VE table pointer to point to the expanded table
2. Handles the MAP axis rescaling for boost (>105 kPa)

---

## Custom Code Blobs (Free Space)

| Address | Size | Content |
|---------|------|---------|
| 0x0D0000 | 51 B | Small routine |
| 0x0D0034 | 7 B | Data/table |
| 0x0D003C | 53 B | Medium routine |
| 0x0D0072 | 662 B | **Large routine** |
| 0x0D0309 | 60 B | Routine |
| 0x0D0346 | 135 B | Routine |
| 0x0D03CE | 5 B | Data |
| 0x0D03D4 | 65 B | Routine |
| 0x0D0416 | 5 B | Data |
| 0x0D041C | 269 B | **Large routine** |
| 0x0D052A | 7 B | Data |
| 0x0D0532 | 59 B | Routine |
| 0x0D056E | 7 B | Data |
| 0x0D0576 | 25 B | Routine |
| 0x0D0590 | 7 B | Data |
| 0x0D0598 | 39 B | Routine |
| 0x0D05C0 | 7 B | Data |
| 0x0D05C8 | 102 B | Routine |
| 0x0E0000 | **7,606 B** | **MASSIVE code blob in OS7** |

**Total custom code: ~9.2 KB**

The 7,606-byte blob at 0x0E0000 is likely the main Boost OS engine — expanded VE tables, boost control PID, wideband closed loop, launch control, flat-foot shift logic, etc.

---

## Calibration/Boot Changes

| Address | Size | Change |
|---------|------|--------|
| 0x000500 | 2 B | Boot param modified |
| 0x000504 | 4 B | OSID/variant bytes changed |
| 0x000511-0x000513 | 2 B | Flash config? |
| 0x0022E9 | 3 B | Branch target modified |
| 0x080986 | 1 B | Calibration value changed (0x14→0x54) |
| 0x08098C | 1 B | Calibration value changed |

---

## JSR Target Address Map

All Boost OS custom code lives in the 0x0D0000-0x0E0000 range:

| Entry Point | Address | Called From |
|------------|---------|------------|
| Routine 1 | 0x0D0306 | 0x034D10 (OS1) |
| Routine 2 | 0x0D0426 | 0x031CEC (OS1) |
| Routine 3 | 0x0D0442 | 0x031C9E (OS1) |
| **VE Expansion** | **0x0D0558** | **0x079B92, 0x07A176, 0x07A95E (OS3)** |
| **Main engine** | **0x0E0000** | Referenced internally |

---

## What This Means for Open12587603

We now have the exact patch blueprint. To replicate Boost OS V3.4:

1. **Copy the custom code blobs** from 0x0D0000-0x0E0000 into the same locations
   - These are pre-compiled 68k routines
   - They reference each other via absolute addresses, so they must go at exact same offsets
   
2. **Apply the JSR patches** at the 6 hook points
   - Replace original instructions with JSR to custom routines
   - Add NOP padding where needed
   
3. **Apply calibration changes** in Boot/Calibration segments
   - OSID variant bytes
   - Calibration value tweaks

4. **Disassemble the custom blobs** to understand what each routine does
   - This gives us the logic to reimplement cleanly
   - Avoids copying proprietary code directly

5. **Reimplement from scratch** using our own 68k code
   - Same hook points, same functionality, clean implementation
   - Fully documented with rationale

---

*For internal use only. Use to understand the patching approach for open12587603.*
