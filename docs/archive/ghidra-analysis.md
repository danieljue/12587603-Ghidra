# P59 Corvette 12587603 — Ghidra Disassembly Analysis

> Auto-analyzed by Ghidra 12.1.2, Motorola 68000:BE:32:default
> 2004 Corvette M6 Stock BIN — OS 12587603

---

## Reset Vector

| Field | Value | Meaning |
|-------|-------|---------|
| SSP (initial stack) | **0x00FFCE00** | Top of RAM — stack grows downward |
| PC (initial program counter) | **0x00000440** | Entry point — bootloader starts here |

---

## Memory Map (Refined — from hex density analysis)

| Range | Size | Density | Purpose |
|-------|------|---------|---------|
| 0x000000 - 0x0003FF | 1 KB | 97% | Boot vector table (256 vectors × 4 bytes) |
| 0x000400 - 0x0005FF | 512 B | 97% | Early boot code |
| 0x000600 - 0x003FFF | ~15 KB | 96-99% | Bootloader / HW init code |
| 0x004000 - 0x005FFF | **8 KB** | 0% | 🔴 FREE SPACE |
| 0x006000 - 0x0062FF | 768 B | 12% | Sparse — possibly parameter block |
| 0x006300 - 0x007FFF | **7.4 KB** | 0% | 🔴 FREE SPACE |
| 0x008000 - 0x08A8FF | ~530 KB | 93-99% | **MAIN OS + CALIBRATION** |
| 0x08A900 - 0x097FFF | **54 KB** | 0% | 🔴 FREE SPACE |
| 0x098000 - 0x0983FF | 1 KB | 23% | OSID area + calibration IDs |
| 0x098400 - 0x0FFEFF | **415 KB** | 0% | 🔴 MASSIVE FREE SPACE |
| 0x0FFF00 - 0x0FFFFF | 256 B | — | Possible top-of-memory vectors / unused |

### Total Free Space for Custom Code: ~484 KB

---

## Function Analysis

- **Total functions identified**: 1,481
- **Entry point**: FUN_00000440 (198 bytes) — bootloader init
- **Early boot functions** (0x440 - 0x1EFC): 43 small functions — hardware init, watchdog, flash setup
- **Main OS region** (0x20000+): ~1,438 functions — the actual engine control code

### Key Early Functions (Boot Sequence)

| Function | Address | Size | Likely Purpose |
|----------|---------|------|---------------|
| FUN_00000440 | 0x000440 | 198 | Reset handler entry |
| FUN_0000054c | 0x00054C | 50 | Early init |
| FUN_000006d2 | 0x0006D2 | 70 | Hardware setup |
| FUN_00000850 | 0x000850 | 514 | Large init routine |
| FUN_00000aa0 | 0x000AA0 | 718 | Major initialization |
| FUN_00000fc0 | 0x000FC0 | 354 | Flash or comms setup |
| FUN_0000138e | 0x00138E | 664 | Large subsystem init |
| FUN_00001958 | 0x001958 | 582 | Large subsystem init |
| FUN_00001c26 | 0x001C26 | 452 | Init (watchdog?) |
| FUN_00020000 | 0x020000 | 138 | Jump to main OS? |

---

## OSID Confirmation

Bytes at 0x600: `07 00 48 E7 FF FE 42 67 20 7C 00 02 B7 9E 60 34`

String at 0x8A7CA: **"587603"** → OS 12587603 confirmed.

---

## Strings Found

| Address | Content | Notes |
|---------|---------|-------|
| 0x08000E | "587919" | Calibration ID? |
| 0x0162DE | "586878" | Calibration ID? |
| 0x01960E | "579113" | Calibration ID? |
| 0x01D8BE | "579117" | Calibration ID? |
| 0x01E1BE | "584410" | Calibration ID? |
| 0x01F6CE | "585028" | Calibration ID? |
| 0x01FEBE | "579125" | Calibration ID? |
| 0x08A7CA | **"587603"** | OSID — 12587603 |

---

## Code Injection Targets

### Best free space for custom code:

| Region | Size | Recommendation |
|--------|------|---------------|
| **0x098400 - 0x0FFFFF** | 425 KB | 🏆 PRIMARY — huge continuous block at end of flash |
| **0x08A900 - 0x097FFF** | 55 KB | Good — right before OSID region |
| 0x004000 - 0x005FFF | 8 KB | Small, near vector table — risky |
| 0x006300 - 0x007FFF | 7.4 KB | Small, between code segments |

### How to inject (68k assembly patching):

1. Write PowerPC/68k subroutine → compile with m68k-elf-gcc
2. Place in free space (e.g., 0x098400)
3. Patch an existing function to `JSR 0x098400` (68k: `4EB9 0009 8400`)
4. Recalculate OS segment checksums
5. Flash via PCM Hammer V20+ (`Tools → Write OS, Calibration, and Boot`)

---

## Next Analysis Steps

- [ ] Decompile the entry point FUN_00000440 to understand boot sequence
- [ ] Find VE table lookup function (search for known RPM/MAP axis values from XDF)
- [ ] Find spark calculation chain
- [ ] Find RPM limiter (search for RPM limit constant)
- [ ] Identify CAN/VPW communication handler
- [ ] Map all ADC input channels
- [ ] Identify injector driver control

---

*Analysis run: 2026-06-22. Ghidra 12.1.2, 68000:BE:32:default, 112 sec auto-analysis, 1,481 functions.*
