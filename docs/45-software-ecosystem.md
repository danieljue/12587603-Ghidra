# P59 ECM Software Ecosystem — Complete Tool Catalog

> 2026-06-22 — Every piece of software that talks to, tunes, flashes, or
> analyzes the P59 PCM (OS 12587603 and family)

---

## 1. The Tool Stack (How It All Connects)

```
┌─────────────────────────────────────────────────────────────────┐
│                    P59 SOFTWARE ECOSYSTEM                       │
│                                                                 │
│  [Your PC]                                                      │
│  ├─ Universal Patcher / TunerPro  ←── Edit calibration (.bin)   │
│  ├─ PCM Hammer / LS Droid        ←── Read/Write flash          │
│  ├─ PCMLogger / EFILive Scan     ←── Datalog while driving     │
│  ├─ Ghidra / IDA Pro              ←── Reverse engineer firmware │
│  └─ Boost OS Patcher              ←── Apply custom OS          │
│                                                                 │
│  [J2534 / ELM327 / OBDX Pro]     ←── Hardware interface        │
│         │                                                       │
│  [P59 PCM on bench or in car]     ←── The actual computer       │
│                                                                 │
│  OUTPUT: .bin file (1 MB)                                       │
│    → Flashed to PCM                                             │
│    → Opened in tuning software                                  │
│    → Analyzed in Ghidra                                         │
│    → Patched for custom features                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Flashing Tools (Read/Write the PCM)

### 2.1 PCM Hammer

| Attribute | Detail |
|-----------|--------|
| Platform | Windows (.NET) |
| Cost | Free / Open Source (GPL) |
| Website | [github.com/LegacyNsfw/PcmHammer](https://github.com/LegacyNsfw/PcmHammer) |
| Interface | J2534 (OBDX Pro, VXDIAG, etc.) |
| PCMs | P01 (512KB), P59 (1MB) |
| Operations | Read entire PCM, Write OS, Write Calibration, Clone |
| Recovery | Yes — can recover bricked PCMs |
| Kernel | 68k assembly flash kernel injected at 0xFF8000 |

**What it does:**
- Full read of all 1MB flash in ~3 minutes
- Writes individual segments (OS, calibration, parameters)
- Segment-by-segment write avoids bricking if interrupted
- Uses VPW Mode $34/$36/$3D protocol (documented in our doc 12)
- Recovery mode: if PCM is bricked, PCM Hammer can force-reflash

**Status:** Mature. Release 021 as of 2026. The standard tool for open-source
P01/P59 flashing. 20,000+ users.

### 2.2 LS Droid

| Attribute | Detail |
|-----------|--------|
| Platform | Android |
| Cost | Free |
| Website | [ls-droid.com](https://ls-droid.com) |
| Interface | ELM327 Bluetooth (cheap $15 dongle) |
| PCMs | P01, P59 |
| Operations | Read, Write, Clone |
| Recovery | Partial — not as robust as PCM Hammer |

**What it does:**
- First tool to fully clone P01/P59 PCMs via ELM327
- Runs on Android phones/tablets (field-flashable)
- Slower than PCM Hammer (ELM327 bottleneck)
- Revolutionary for making tuning accessible — literally a $15 dongle

**Status:** Stable. The "gateway drug" that proved open-source flashing was possible.

### 2.3 HP Tuners MPVI

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | $299+ (hardware) + $100/vehicle (license credits) |
| Website | [hptuners.com](https://www.hptuners.com) |
| Interface | MPVI3 (USB/OBD-II) |
| PCMs | P01, P59, E38, E67, E92, T43, + hundreds more |
| Operations | Read, Write, Datalog, Custom OS |
| Recovery | Yes — good recovery tools |

**What it does:**
- The industry standard commercial tuner
- Licenses per-vehicle: 2 credits (~$100) per PCM
- Custom OS: 2-bar/3-bar Speed Density, Real-Time Tuning
- Massive parameter database — far more calibrations exposed than any XDF
- Datalogging with histograms, VCM Scanner
- VCM Suite includes Editor + Scanner

**Status:** Industry leader. Expensive but comprehensive. Most professional
tuners use HP Tuners.

### 2.4 EFILive

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | $899+ (FlashScan V3 hardware) + $125/vehicle |
| Website | [efilive.com](https://www.efilive.com) |
| Interface | FlashScan V3 (USB/OBD-II) |
| PCMs | P01, P59, E38, E67, E92, T43, Cummins, Duramax, Allison |
| Operations | Read, Write, Datalog, Custom OS, DSP5 switching |
| Recovery | Yes |

**What it does:**
- HP Tuners' main competitor
- Stronger on diesel (Duramax, Cummins)
- DSP5: 5-position switch for on-the-fly tune selection
- Real-time tuning (RoadRunner) via emulator
- COS (Custom Operating System) for boost applications
- Scripting engine for automated tuning workflows

**Status:** Mature. Preferred by many diesel tuners. More expensive hardware,
similar per-vehicle cost.

---

## 3. Calibration Editing (Tuning Software)

### 3.1 Universal Patcher

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Free / Open Source |
| Website | [github.com/joukoy/UniversalPatcher](https://github.com/joukoy/UniversalPatcher) |
| Input | .bin file |
| Requires | XDF definition file (or built-in database) |
| PCMs | P01, P59, E38, E67, and growing |

**What it does:**
- Reads .bin files and presents calibrations in human-readable form
- Built-in database of parameters (no XDF needed for many PCMs)
- Table editor with 2D/3D visualization
- Checksum correction via gm-checksum-plugins
- Scripting (Python/C#) for batch operations
- Segment swap utility
- The recommended editor for P01/P59 open-source tuning

**Status:** Active development. Rapidly replacing TunerPro in the open-source
community. Author: joukoy.

### 3.2 TunerPro

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | $39 (free version available with nag screen) |
| Website | [tunerpro.net](https://www.tunerpro.net) |
| Input | .bin file |
| Requires | XDF definition file |
| PCMs | Any (via XDF) |

**What it does:**
- The original universal tuning editor
- XDF (eXchange Definition Format) is the standard calibration description
- Table editing, 2D/3D views, comparison, history
- Checksum plugins
- Mature, stable, well-understood

**Status:** Stable but aging. UI is dated. XDF format has limitations for
complex table relationships. Being superseded by Universal Patcher.

### 3.3 TinyTuner

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Free |
| Website | pcmhacking.net forums |
| Input | .bin file |
| Requires | XDF |

**What it does:**
- Lightweight, fast tuning editor
- Written in C++ for speed
- Focused on P01/P59
- Smaller parameter set than TunerPro/Universal Patcher

**Status:** Niche. Used by some pcmhacking.net community members.

### 3.4 HP Tuners VCM Editor

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Included with MPVI hardware |
| Input | .hpt file (proprietary format) |
| PCMs | Thousands of vehicles |

**What it does:**
- Professional-grade editor with massive calibration database
- Cannot edit .bin files directly (proprietary .hpt format)
- Real-time tuning (RTT) on supported OSes
- Virtual VE table, EQ ratio error correction tools
- The reference implementation for calibration editing

### 3.5 EFILive Tune Tool

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Included with FlashScan |
| Input | .ctz file (proprietary format) |
| PCMs | Same as FlashScan |

**What it does:**
- Similar capabilities to HP Tuners Editor
- Stronger scripting/automation
- Built-in calculator for injector data, gear/tire changes

---

## 4. Datalogging / Scanning

### 4.1 PCMLogger

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Free / Open Source |
| Website | pcmhacking.net |
| Interface | J2534 / ELM327 |
| PCMs | P01, P59 |

**What it does:**
- Logs OBD-II PIDs at high rate (~40+ PIDs at 10 Hz on P59)
- Custom PID definitions
- Graph and export to CSV
- Designed for the P01/P59 VPW data rate

### 4.2 HP Tuners VCM Scanner

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Included with MPVI |
| PCMs | All HP Tuners-supported vehicles |

**What it does:**
- High-speed datalogging
- Histograms (table-format logging for VE/spark tuning)
- Wideband O2 integration
- Virtual dyno
- The standard for professional LS tuning

### 4.3 EFILive Scan Tool

| Attribute | Detail |
|-----------|--------|
| Platform | Windows |
| Cost | Included with FlashScan |

**What it does:**
- Similar to VCM Scanner
- BBL (Black Box Logging) — log without laptop
- PID groups, maps, alerts

### 4.4 Torque Pro (Android)

| Attribute | Detail |
|-----------|--------|
| Platform | Android |
| Cost | $4.95 |
| Interface | ELM327 Bluetooth |

**What it does:**
- Generic OBD-II scanner
- Custom PIDs for GM-specific parameters
- Gauges, graphs, logging
- Not fast enough for serious tuning (ELM327 bottleneck)
- Good for monitoring, not datalogging

---

## 5. Custom Operating Systems

### 5.1 Boost OS (Closed Source)

| Attribute | Detail |
|-----------|--------|
| Author | bubba2533 / turbo_v6 |
| Platform | Windows EXE patcher |
| Cost | Free (donation-supported) |
| Version | V3.4 (latest) |
| Target | P59 OS 12587603 |
| 68k Code | ~9.2 KB in OS5, ~7.6 KB data in OS7 |

**Features (from our binary diff, doc 15):**
```
- Launch Control (two-step RPM limiter)
- Flat Foot Shift (FFS)
- VE Table Expansion (2-bar, 4-bar MAP)
- Boost Spark Adder table
- Wideband Closed Loop (via EGR ADC)
- Open Loop Boost Control (via EGR solenoid)
- Lean Boostcut
- Overboost Protection
- Flex Fuel enabled (KE_FLEX_FUEL_EQUIPPED)
- Spark Cut Limiter
```

**Mechanism:** 6 JSR hooks into factory OS code. VE expansion redirects the
table pointer when MAP > 100 kPa. EGR hardware repurposed for boost control
and wideband input.

**The XDF is password-locked (RC4 encryption).** Our binary diff technique
(doc 15) extracted all changes without needing the password.

### 5.2 open12587603 (Our Project — Open Source)

| Attribute | Detail |
|-----------|--------|
| Author | danieljue (us) |
| Language | Python 3 |
| File | `F:/github/12587603-Ghidra/tools/open12587603.py` |
| License | Open source |
| Status | V1 functional, V2 rebuild planned |

**Features implemented (Phase 1-4 of plan):**
```
- Launch Control (two-step via fuel cut RPM limits)
- Expanded VE (2-bar MAP)
- Boost Spark Adder (table placement)
- Spark Cut Limiter
- Wideband CL (config scaffold)
- Lean Boostcut (config scaffold)
- Overboost Protection (config scaffold)
- Flat Foot Shift (config scaffold)
```

**Key insight:** Factory OS already has launch control (sub_3BDC4) and FFS
(sub_2FC1E). Only VE expansion requires new 68k code.

### 5.3 EFILive COS (Custom Operating System)

| Attribute | Detail |
|-----------|--------|
| Author | EFILive |
| Cost | Included with FlashScan + license |
| Target | P01, P59, E38, E67 |

**Features:**
- Valet mode
- DSP5 switchable tunes
- 2/3-bar MAP support
- Real-time tuning

### 5.4 HP Tuners Custom OS

| Attribute | Detail |
|-----------|--------|
| Author | HP Tuners |
| Cost | Additional credits |
| Target | P01, P59, E38, E67, etc. |

**Features:**
- 2/3-bar Speed Density
- Real-Time Tuning (RTT)
- Custom VE tables for boost
- Flex fuel integration

---

## 6. Reverse Engineering Tools

### 6.1 Ghidra (NSA — Free)

| Attribute | Detail |
|-----------|--------|
| Platform | Windows, macOS, Linux |
| Cost | Free / Open Source |
| Language | 68000:BE:32:default |
| PCMs | P01, P59, E38, E67 |

**What it does:**
- Disassemble raw .bin files (loader: BinaryLoader, base 0x0)
- Decompile to C pseudocode
- Cross-reference tracking (find all code that reads a calibration)
- Python/Java scripting
- Patch assembly with `patch.assemble`
- Our entire P59 project runs in Ghidra

**The standard for open-source ECU reverse engineering.**

### 6.2 IDA Pro

| Attribute | Detail |
|-----------|--------|
| Platform | Windows, macOS, Linux |
| Cost | $1,800+ (Pro), $400+ (Home) |
| Language | 68330 (CPU32) |
| PCMs | P01, P59 |

**What it does:**
- The tool LegacyNsfw used to create the 936,975-line disassembly
- The .sanitized.asm file we rely on was exported from IDA
- More mature 68k analysis than Ghidra (but paid)
- Our project replaced the need for IDA with Ghidra

### 6.3 Binary Ninja

| Attribute | Detail |
|-----------|--------|
| Platform | Windows, macOS, Linux |
| Cost | $299 (Personal), $1,499 (Commercial) |
| Language | 68k via plugin |

**What it does:**
- Modern alternative to IDA
- Good decompiler, Python API
- 68k support via community plugin
- Less mature than Ghidra for embedded firmware

### 6.4 Ghidra Headless MCP

| Attribute | Detail |
|-----------|--------|
| Author | mrphrazer |
| Cost | Free |
| Website | [github.com/mrphrazer/ghidra-headless-mcp](https://github.com/mrphrazer/ghidra-headless-mcp) |
| Tools | 212 MCP tools in 34 groups |

**What it does:**
- Bridges AI agents to Ghidra
- Allows autonomous reverse engineering: search constants, decompile functions,
  trace references, patch assembly
- Used by Hermes to automate analysis
- Installed at `F:/github/ghidra-headless-mcp/`

---

## 7. Hardware Interfaces

| Device | Cost | Protocol | Speed | Use With |
|--------|------|----------|-------|----------|
| **OBDX Pro VT** | $80 | J2534 VPW | Fast | PCM Hammer, PCMLogger |
| **OBDX Pro VX** | $130 | J2534 VPW + CAN | Fast | All J2534 tools |
| **VXDIAG VCX Nano** | $60 | J2534 | Medium | PCM Hammer (clone — quality varies) |
| **ELM327 (clone)** | $15 | ELM327 AT commands | Slow | LS Droid, Torque Pro |
| **AVT-852** | $250 | J2534 | Very fast | Professional-grade |
| **MDI2** | $500+ | J2534 + CAN FD | Fast | GM dealership tool |
| **HP Tuners MPVI3** | $299 | Proprietary | Fast | HP Tuners only |
| **EFILive FlashScan V3** | $899 | Proprietary | Fast | EFILive only |

**Recommendation for open-source work:** OBDX Pro VT ($80) + PCM Hammer +
Universal Patcher + PCMLogger. Total cost: $80. Total capability: read, write,
tune, datalog.

---

## 8. Bench Setup Tools

### 8.1 JimStim / Arduino Engine Simulator

Generates the signals a PCM needs to believe an engine is running:
- CKP: 58x crank position (0-5V square wave)
- CMP: cam position (0-5V, 1 pulse per 2 crank revs)
- TPS: variable voltage (0-5V)
- MAP: variable voltage (0-5V)
- O2: switching voltage (0-1V)
- ECT/IAT: resistor simulation (thermistor)

**Cost:** $50-100 for a pre-built JimStim, or ~$20 in parts for Arduino-based.

### 8.2 Bench Harness

- OBD-II port wired to pins 2 (VPW) and 4/5 (ground), 16 (12V)
- PCM connectors: C1 (Blue, 80-pin) and C2 (Green, 80-pin)
- 12V power supply (regulated, 3A minimum)
- Breakout board for probing signals

---

## 9. The Open-Source Workflow (Complete)

```
1. READ the PCM:
   PCM Hammer → read entire 1MB flash → stock.bin

2. EDIT the calibration:
   Universal Patcher → open stock.bin → edit tables → save → tuned.bin

3. CHECKSUM:
   Universal Patcher or gm-checksum-plugins → fix CVN in tuned.bin

4. FLASH the PCM:
   PCM Hammer → write calibration → tuned.bin → PCM

5. DATALOG:
   PCMLogger → record PIDs while driving → analyze in spreadsheet

6. ITERATE:
   Repeat steps 2-5 until tune is dialed in

7. (ADVANCED) CUSTOM OS:
   open12587603.py → patch tuned.bin with new 68k code → flash
```

**Total cost for the open-source path: $80 (OBDX Pro) + $0 (all software).**
Compare to HP Tuners: $299 (MPVI3) + $100 (credits) = $399 minimum.

---

## 10. What Each Tool Does (Quick Reference)

| Task | Free/Open Source | Commercial |
|------|-----------------|------------|
| Flash PCM | PCM Hammer, LS Droid | HP Tuners, EFILive |
| Edit calibrations | Universal Patcher, TunerPro | HP Tuners, EFILive |
| Datalog | PCMLogger, Torque Pro | VCM Scanner, EFILive Scan |
| Reverse engineer | Ghidra (free) | IDA Pro ($1,800+) |
| Patch custom code | open12587603.py, Ghidra | HP Tuners Custom OS |
| Fix checksums | Universal Patcher, gm-checkSum-plugins | Built into HP Tuners/EFILive |
| Segment swap | Universal Patcher, TunerPro | HP Tuners, EFILive |
| VIN change | PCM Hammer, Universal Patcher | HP Tuners, EFILive |
| VATS disable | Universal Patcher, TunerPro | HP Tuners, EFILive |
| DTC disable | Universal Patcher, TunerPro | HP Tuners, EFILive |
| Custom OS | open12587603.py, Boost OS Patcher | HP Tuners COS, EFILive COS |
| AI-assisted RE | Hermes + ghidra-headless-mcp | None |

---

## 11. Key Repositories

| Repo | URL | Purpose |
|------|-----|---------|
| LegacyNsfw/12587603 | github.com/LegacyNsfw/12587603 | Original reverse engineering (IDA, CSV) |
| danieljue/12587603-Ghidra | github.com/danieljue/12587603-Ghidra | **Our fork** — 44 docs + patcher |
| LegacyNsfw/PcmHammer | github.com/LegacyNsfw/PcmHammer | Flashing tool + 68k kernel |
| joukoy/UniversalPatcher | github.com/joukoy/UniversalPatcher | Calibration editor |
| joukoy/gm-checksum-plugins | github.com/joukoy/gm-checksum-plugins | Checksum DLLs |
| mrphrazer/ghidra-headless-mcp | github.com/mrphrazer/ghidra-headless-mcp | AI↔Ghidra bridge |
| BoredTruckOwner/LS_Based_Engine_Repository | github.com/BoredTruckOwner/LS_Based_Engine_Repository | Stock BIN collection |

---

## 12. Community Forums

| Forum | URL | Focus |
|-------|-----|-------|
| pcmhacking.net | pcmhacking.net/forums | Open-source flashing, P01/P59 development |
| LS1Tech | ls1tech.com/forums/pcm-diagnostics-tuning | LS tuning, HP Tuners, EFILive |
| HP Tuners Forum | forum.hptuners.com | HP Tuners support, tuning strategies |
| EFILive Forum | forum.efilive.com | EFILive support, diesel tuning |
| LS Droid (Facebook) | facebook.com/groups/LsDroid | LS Droid support, Android flashing |
| Gearhead-EFI | gearhead-efi.com | XDF files, definition sharing |
