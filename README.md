# 12587603-Ghidra

Ghidra project for GM P59 OS 12587603 — the universal donor LS1/LS2 operating system.
Forked from LegacyNsfw/12587603, ported to free open-source Ghidra.

## What This Is

A fully annotated Ghidra project for reverse engineering the GM P59 PCM running OS 12587603 (2004 Corvette, Silverado, Escalade, etc).

**This replaces the need for IDA Pro.** The original project required IDA (thousands of dollars). This fork brings everything to Ghidra (free, NSA-developed).

## What You Get

- **4,796 labeled calibration entries** — every table, scalar, and constant named with descriptions
- **11 memory segments** matching the factory layout (Boot, Param1/2, Calibration, OS1-OS7)
- **Full 68k disassembly** of the 1MB firmware
- **Cross-references** — click any label to see all code that reads/writes it
- **Decompiled C pseudocode** — understand logic without assembly
- **Documented subsystems** — RPM limiter, VPW protocol, flash kernel

## Quick Start

### Option A: Pre-built Ghidra Archive (easiest)
1. Download P59_12587603.gar from Releases
2. In Ghidra: File > Restore Project > select the .gar file
3. Open and explore

### Option B: Build from scratch
1. Install Ghidra 11+
2. Clone this repo
3. Copy Resources/12587603.csv and ghidra/Import12587603.java to Ghidra's scripts directory
4. Run:
```
analyzeHeadless <project_dir> P59_12587603 \
  -import 12587603-2004-Corvette-M6.bin \
  -processor "68000:BE:32:default" \
  -loader BinaryLoader -loader-baseAddr 0x0 \
  -postScript Import12587603.java
```

## Segment Map

| Segment | Range | Size | Purpose |
|---------|-------|------|---------|
| Boot | 0x000000-0x003FFF | 16KB | Reset vectors |
| Param1 | 0x004000-0x005FFF | 8KB | FREE |
| Param2 | 0x006000-0x007FFF | 8KB | Partially used |
| Calibration | 0x008000-0x01FFFF | 96KB | 4,796 entries |
| OS1-OS4 | 0x020000-0x08FFFF | 448KB | OS code |
| OS5-OS7 | 0x0A0000-0x0EFFFF | 192KB | FREE — custom code |

## Key Addresses

| Label | Address | Purpose |
|-------|---------|---------|
| K_MAIN_VOLUMETRIC_EFFICIENCY | 0x00008442 | Main VE table |
| KA_MAIN_OT_HIGH_OCTANE | 0x00010890 | High-octane spark |
| KV_ENGINE_SPEED_LIMIT | 0x00009A82 | RPM limiter |
| KE_PN_ENGINE_OVERSPEED_HIGH | 0x0000BAE2 | Fuel-cut limit (6200 RPM) |

## Docs

- [Fuel-Cut RPM Limiter](docs/fuel-cut-rpm-limiter.md) — Function trace + RAM addresses
- [VPW Protocol Handler](docs/vpw-protocol.md) — Diagnostic mode dispatcher
- [Flash Kernel Architecture](docs/flash-kernel.md) — PCM Hammer reference
- [Segment Map](docs/segment-map.md) — Full memory layout
- [Ghidra Analysis](docs/ghidra-analysis.md) — Initial auto-analysis results

## Credits

- **LegacyNsfw** — Original reverse engineering, IDA scripts, 4,796-entry CSV catalog
- **Anonymous hero** — Dumpster-dive calibration data
- **PCM Hammer team** — Flash kernel, VPW protocol documentation
- **turbo_v6 / bubba2533** — Boost OS V3.4 custom operating system, the inspiration
  and reference implementation for open12587603
- **Ghidra community** — Free reverse engineering for everyone

## License

MIT License — do whatever you want with this. See [LICENSE](LICENSE).
