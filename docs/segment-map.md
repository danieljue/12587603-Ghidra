# P59 OS 12587603 — Definitive Segment Map

> **Source**: `LegacyNsfw/12587603` (GitHub) — `Resources/Segments.idc`
> **Author**: LegacyNsfw (original PCM Hammer developer)
> **Verified against**: CSV calibration catalog (4,796 entries), hex density analysis

---

## Flash Segment Layout (1MB P59)

| Segment | Range | Size | Name | Status |
|---------|-------|------|------|--------|
| Boot | 0x000000-0x003FFF | 16 KB | Boot vectors | Active (reset vector at 0x000) |
| Param1 | 0x004000-0x005FFF | 8 KB | Parameter block 1 | **FREE** (verified 0% non-FF) |
| Param2 | 0x006000-0x007FFF | 8 KB | Parameter block 2 | Partially used (12% density at 0x6000) |
| **Calibration** | **0x008000-0x01FFFF** | **96 KB** | **Main calibration data** | **Active — 4,796 entries** |
| OS1 | 0x020000-0x03FFFF | 128 KB | OS code | Active |
| OS2 | 0x040000-0x05FFFF | 128 KB | OS code | Active |
| OS3 | 0x060000-0x07FFFF | 128 KB | OS code | Active |
| OS4 | 0x080000-0x08FFFF | 64 KB | OS code / OSID area | Active (OSID at 0x8A7CA) |
| _gap_ | 0x090000-0x09FFFF | 64 KB | — | **FREE** (0% non-FF) |
| **OS5** | **0x0A0000-0x0AFFFF** | **64 KB** | **OS code (EMPTY)** | **🔴 FREE** |
| **OS6** | **0x0C0000-0x0CFFFF** | **64 KB** | **OS code (EMPTY)** | **🔴 FREE** |
| **OS7** | **0x0E0000-0x0EFFFF** | **64 KB** | **OS code (EMPTY)** | **🔴 FREE** |
| _gap_ | 0x0F0000-0x0FFFFF | 64 KB | — | FREE |

### Total Free Space: ~340 KB

**Primary injection targets:**
- OS5 at 0xA0000 (64 KB) — for custom code routines
- OS6 at 0xC0000 (64 KB) — for extended calibration tables
- OS7 at 0xE0000 (64 KB) — for more calibration tables
- Param1 at 0x4000 (8 KB) — for small patches/config

---

## RAM Segments

| Segment | Range | Size | Purpose |
|---------|-------|------|---------|
| RAM_00 | 0xFF0000-0xFFFFFF | 64 KB | General purpose RAM |
| RAM_FF | 0xFFFF0000-0xFFFFFFFF | 64 KB | Peripheral registers |

### Key Memory-Mapped Registers (RAM_FF)
| Address | Register | Purpose |
|---------|----------|---------|
| 0xFFFA00 | SIM_BASE | System Integration Module |
| 0xFFFA27 | COP1 | Watchdog reset |
| 0xFFD006 | COP2 | Watchdog reset |
| 0xFFF600 | J1850_Config | VPW DLC config |
| 0xFFF60C | J1850_Command | VPW transmit control |
| 0xFFF60D | J1850_TX_FIFO | VPW transmit data |
| 0xFFF60E | J1850_Status | VPW status |
| 0xFFF60F | J1850_RX_FIFO | VPW receive data |

---

## Critical Calibration Addresses (from 4,796-entry CSV)

### Airflow / VE
| Label | Address | Units | Notes |
|-------|---------|-------|-------|
| K_MAIN_VOLUMETRIC_EFFICIENCY | **0x00008442** | gm·K/kPa | **MAIN VE TABLE** |
| KV_VOLUMETRIC_EFFICIENCY_BARO_CO | 0x000081DC | NONE 0-2 | Baro compensation |
| KA_VOLUMETRIC_EFFICIENCY_CRANK | 0x000081F0 | Percent | Cranking VE |

### Spark Advance
| Label | Address | Units | Notes |
|-------|---------|-------|-------|
| KA_MAIN_OT_HIGH_OCTANE | **0x00010890** | Degrees | **MAIN HIGH-OCTANE SPARK** |
| KA_MAIN_OT_LOW_OCTANE | **0x00010E3A** | Degrees | **MAIN LOW-OCTANE SPARK** |
| KA_MAIN_CT_DRIVE | 0x0001215A | Degrees | Closed-throttle drive spark |
| KA_MAIN_CT_PARK | 0x0001244C | Degrees | Closed-throttle park spark |

### RPM Limiter (LAUNCH CONTROL TARGET)
| Label | Address | Units | Notes |
|-------|---------|-------|-------|
| **KV_ENGINE_SPEED_LIMIT** | **0x00009A82** | RPM | **MAIN RPM LIMITER TABLE** |
| KE_ENGINE_OVERSPEED_LAMP | 0x00009A96 | RPM | Overspeed lamp threshold |
| KE_FANLOCKUPRPMLIMIT | 0x00009A9A | RPM | Fan protection RPM limit |
| KE_PN_ENGINE_OVERSPEED_LOW | 0x0000BAE2 | RPM | Park/Neutral overspeed fuel cut |
| KV_COLD_ENG_PROT_OVERSPEED_LOW | 0x0000BC1C | RPM | Cold engine protection overspeed |

### Fuel / Injectors
| Label | Address | Units | Notes |
|-------|---------|-------|-------|
| KV_STOICHIOMETRIC_FUEL_AIR | 0x0000C7D4 | Mult_0_to_1 | Stoichiometric ratio vs ethanol |
| KE_MIN_PULSE_WIDTH | 0x0000C00E | Seconds | Minimum injector pulse |
| KV_INJECTOR_OFFSET_ADJUSTMENT | 0x0000E2BE | Milliseconds | Injector dead time |

### Flex Fuel / Ethanol
| Label | Address | Units |
|-------|---------|-------|
| KE_HRP_MIN_PERCENTAGE_ETHANOL | 0x0000923C | Percent |

### MAP / Baro
| Label | Address | Units |
|-------|---------|-------|
| KE_BARO_DEFAULT_MAP_FAILED | 0x0000893C | kPa |
| KE_BARO_TPS_LIMIT | 0x0000893E | Percent |
| KE_MAX_BARO_OFFSET_FOR_UPDATE | 0x0000894A | kPa |

---

## Injection Strategy for Custom OS

### Where to place custom code:
- **OS5 (0xA0000)**: Custom 68k subroutines (64 KB)
- **OS6 (0xC0000)**: Extended calibration tables (64 KB)
- **OS7 (0xE0000)**: More tables, future expansion (64 KB)

### How to hook into the OS:
1. Find a frequently-called function in OS1-OS4
2. Replace its first instruction with `JSR 0xA0000` (6 bytes: `4E B9 00 0A 00 00`)
3. Our routine does its work, then executes the displaced original instruction
4. Returns to caller

### Checksum implications:
- Boot segment (0x0000-0x3FFF): ⚠️ Contains vectors — do not modify
- Param1/Param2 (0x4000-0x7FFF): Not checksummed
- Calibration (0x8000-0x1FFFF): Checksummed — recalculation needed after any change
- OS1-OS4 (0x20000-0x8FFFF): Checksummed — recalculation needed for JSR patches
- OS5-OS7 (0xA0000-0xEFFFF): **Not checksummed** — safe to write freely!

---

*This is the authoritative reference. Source: LegacyNsfw's 12587603 reverse engineering repository.*
